"""Hindi voiceover: ONE male voice for the whole video.
Order: Gemini Charon in one go (split at pauses) -> Gemini Charon per scene -> Edge Madhur (male) -> silent.
Writes OUT/voice/seg_<i>.wav (44.1 kHz mono) + OUT/voice/voice.json, and stretches scene seconds
in the plan so no sentence is ever cut.
Usage: python voice.py plan.json OUT_DIR"""
import os, sys, json, base64, wave, subprocess, asyncio
from pathlib import Path
import numpy as np

SR = 44100
VOICE = 'Charon'                                   # Gemini male voice
STYLE = 'Say in clear, energetic Hindi, like a friendly teacher explaining to students, at a lively pace:\n'

def scene_lines(plan):
    out = []
    for s in plan['scenes']:
        if s.get('speak'): out.append(s['speak']); continue
        if 'quiz' in s:
            q = s['quiz']
            nxt = f" अगली रील में: {plan['next']}" if plan.get('next') else ''
            out.append(f"{s.get('title', '')}। {q['q']} {q['a']}, या {q['b']}? {q['cta']}।{nxt}"); continue
        out.append(' '.join(x if x.endswith(('?', '।', '!')) else x + '।' for x in (s.get('title', ''), s.get('sub', '')) if x))
    return [l.replace('(', ', ').replace(')', ', ').replace(':', ',') for l in out]

def to_float(path):
    return np.frombuffer(subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-']), np.float32).copy()

def gemini(text, key):
    import requests
    body = {'contents': [{'parts': [{'text': text}]}],
            'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': VOICE}}}}}
    for model in ('gemini-2.5-flash-preview-tts', 'gemini-2.5-pro-preview-tts'):
        for wait in (0, 15, 45):
            import time; time.sleep(wait)
            try:
                r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                  headers={'x-goog-api-key': key}, json=body, timeout=180)
            except Exception as e:
                print('tts network', type(e).__name__); continue
            if r.status_code == 200:
                part = next(p['inlineData'] for p in r.json()['candidates'][0]['content']['parts'] if 'inlineData' in p)
                raw = np.frombuffer(base64.b64decode(part['data']), '<i2').astype(np.float32) / 32768
                n = int(len(raw) * SR / 24000)                                   # 24 kHz -> 44.1 kHz
                return np.interp(np.linspace(0, len(raw) - 1, n), np.arange(len(raw)), raw).astype(np.float32)
            print('tts', model, r.status_code)                                     # never print the body (key safety)
            if r.status_code not in (429, 500, 502, 503, 504): break
    raise RuntimeError('Gemini TTS unavailable')

def split_at_pauses(a, n, lines=None):
    """Cut one long take into n parts at the n-1 longest silences (keeps the order)."""
    win = int(.02 * SR); rms = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, 'same'))
    quiet = rms < max(.008, .06 * np.percentile(rms, 95))
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if j - i > .18 * SR: runs.append((j - i, (i + j) // 2))
            i = j
        else: i += 1
    if len(runs) < n - 1: return None
    cuts = sorted(c for _, c in sorted(runs, reverse=True)[:n - 1])
    parts = np.split(a, cuts)
    trim = []
    for p in parts:
        idx = np.where(np.abs(p) > .01)[0]
        trim.append(p[max(0, idx[0] - 800): idx[-1] + 2000] if len(idx) else p)
    if not all(len(t) > .4 * SR for t in trim): return None
    # each part must be about as long as its text (else the cut fell inside a sentence)
    if lines:
        chars = np.array([max(1, len(l)) for l in lines], float); total = sum(len(t) for t in trim)
        for t, c in zip(trim, chars):
            ratio = len(t) / (total * c / chars.sum())
            if not .6 <= ratio <= 1.6: print('split rejected, ratio', round(ratio, 2)); return None
    return trim

def edge(lines, d):
    import edge_tts
    async def go():
        for i, l in enumerate(lines): await edge_tts.Communicate(l, 'hi-IN-MadhurNeural', rate='+10%').save(str(d / f'e_{i}.mp3'))
    asyncio.run(go()); return [to_float(d / f'e_{i}.mp3') for i in range(len(lines))]

def main(plan_path, out):
    plan_path, out = Path(plan_path), Path(out); d = out / 'voice'; d.mkdir(parents=True, exist_ok=True)
    plan = json.loads(plan_path.read_text(encoding='utf-8')); lines = scene_lines(plan); key = os.getenv('GEMINI_API_KEY', '')
    segs, provider = None, None
    if key:
        try:
            take = gemini(STYLE + '\n\n'.join(lines), key)
            segs = split_at_pauses(take, len(lines), lines); provider = 'Gemini Charon (one take)' if segs else None
        except Exception as e: print('one-take failed', type(e).__name__)
        if not segs:
            try: segs = [gemini(STYLE + l, key) for l in lines]; provider = 'Gemini Charon (per scene, same voice)'
            except Exception as e: print('per-scene failed', type(e).__name__); segs = None
    if not segs:
        try: segs = edge(lines, d); provider = 'Edge Madhur (male)'
        except Exception as e: print('edge failed', type(e).__name__); segs = None
    if not segs:
        print('NO VOICE: video will have music only'); (d / 'voice.json').write_text(json.dumps({'provider': None})); return
    tempo = float(os.getenv('VOICE_TEMPO', '1.15'))          # reels feel slow at normal speed; atempo keeps the pitch
    if abs(tempo - 1) > .01:
        fast = []
        for seg in segs:
            raw = (np.clip(seg, -1, 1) * 32767).astype('<i2').tobytes()
            out_ = subprocess.run(['ffmpeg', '-v', 'error', '-f', 's16le', '-ar', str(SR), '-ac', '1', '-i', '-', '-filter:a', f'atempo={tempo}',
                                   '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-'], input=raw, capture_output=True, check=True).stdout
            fast.append(np.frombuffer(out_, np.float32).copy())
        segs = fast
    durs = []
    for i, (s, seg) in enumerate(zip(plan['scenes'], segs)):
        with wave.open(str(d / f'seg_{i}.wav'), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(seg, -.98, .98) * 32767).astype('<i2').tobytes())
        L = len(seg) / SR; durs.append(L)
        need = round(L + .45, 2)                      # 0.25 s lead-in + 0.3 s breath after the line
        if s['seconds'] < need: s['seconds'] = need
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    (d / 'voice.json').write_text(json.dumps({'provider': provider, 'lines': lines, 'seconds': durs}, ensure_ascii=False, indent=1), encoding='utf-8')
    print('VOICE', provider, [round(x, 2) for x in durs], 'scene seconds', [s['seconds'] for s in plan['scenes']])

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
