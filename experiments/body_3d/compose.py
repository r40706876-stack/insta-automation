"""Hindi overlays + synthesized sound on top of the Blender frames -> final reel MP4.
Deterministic: same frames in -> same video out. Needs Pillow (with raqm), numpy, ffmpeg."""
import os, json, math, subprocess, hashlib, wave
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = Path(os.environ.get('BODY_ROOT', Path(__file__).parent))
OUT = Path(os.environ.get('OUT', R / 'out'))
TL = json.loads(Path(os.environ['TOPIC']).read_text(encoding='utf-8'))
PINS = json.loads((OUT / 'pins.json').read_text())
IDX = json.loads((R / 'organ_index.json').read_text(encoding='utf-8'))
FPS = TL['fps']; W, H = 720, 1280
LEN = [round(s['seconds'] * FPS) for s in TL['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]
N = sum(LEN)
GOLD = (255, 214, 92); WHITE = (246, 248, 250); CYAN = (110, 220, 255); RED = (255, 110, 70); BLUE = (120, 175, 255); INK = (6, 14, 24)

@lru_cache(None)
def font(n): return ImageFont.truetype(str(R / 'Mukta.ttf'), n)

def scene_of(f):
    for i in range(len(START) - 1, -1, -1):
        if f >= START[i]: return i, f - START[i]
def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3

def fit(s, n, maxw=660):            # shrink long Hindi lines so they never leave the frame
    while n > 18 and font(n).getlength(s) > maxw: n -= 1
    return n
def text(d, xy, s, n, c, anchor='mm', stroke=3):
    d.text(xy, s, font=font(n), fill=c, anchor=anchor, stroke_width=stroke, stroke_fill=INK)

def chip(d, xy, s, c, n=26, anchor_pt=None):
    x, y = xy; w = d.textlength(s, font=font(n)) + 30; h = n + 18
    box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    if anchor_pt:
        d.line([(x, y + h / 2 if anchor_pt[1] > y else y - h / 2), anchor_pt], fill=c, width=3)
        d.ellipse((anchor_pt[0] - 6, anchor_pt[1] - 6, anchor_pt[0] + 6, anchor_pt[1] + 6), fill=c)
    d.rounded_rectangle(box, radius=h / 2, fill=(8, 20, 32, 215), outline=c, width=2)
    d.text((x, y + 1), s, font=font(n), fill=c, anchor='mm')

def overlay(f):
    k, age = scene_of(f); sc = TL['scenes'][k]; p = PINS[f]; t = age / FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # top shade + bottom shade keep text readable over bright space objects
    for i in range(330):
        d.line([(0, i), (W, i)], fill=(0, 0, 0, int(150 * (1 - i / 330) ** 1.6)))
    for i in range(260):
        d.line([(0, H - i), (W, H - i)], fill=(0, 0, 0, int(170 * (1 - i / 260) ** 1.4)))
    # repo-standard notes banner (kept clear of Instagram's top bar)
    if f >= 2 * FPS:          # first 2 s: only the question + visual (hook), banner fades in after
        ba = int(225 * min(1, (f - 2 * FPS) / 8)); tb = int(255 * min(1, (f - 2 * FPS) / 8))
        d.rounded_rectangle((36, 60, 684, 140), radius=16, fill=(10, 34, 48, ba), outline=(70, 140, 160, tb), width=2)
        text(d, (360, 84), 'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं', 24, WHITE + (tb,), stroke=0)
        text(d, (360, 117), 'WhatsApp: +91 89892 79637', 28, GOLD + (tb,), stroke=0)
    if f >= 2 * FPS:          # series badge: same look on every 3D reel = recognisable page identity
        badge = 'MinuteMe 3D  ·  ' + TL.get('brand', 'GS') + (f"  ·  Day {TL['day']}" if TL.get('day') else '')
        bw = font(21).getlength(badge) + 30
        d.rounded_rectangle((36, 150, 36 + bw, 182), radius=16, fill=(255, 196, 60, 235))
        d.text((36 + bw / 2, 166), badge, font=font(21), fill=(20, 24, 30), anchor='mm')
    # title pops in, subtitle slides in 0.25s later
    fast = sc['id'] == 'hook'
    a = ease(t / (.12 if fast else .35)); b = ease((t - (.1 if fast else .25)) / .3)
    trap = sc.get('trap')
    if trap:
        k_ = ease(t / .25); d.rounded_rectangle((210, 258, 510, 294), radius=18, fill=(150, 20, 20, int(235 * k_)))
        text(d, (360, 276), 'परीक्षा की आम गलती', 24, (255, 235, 230) + (int(255 * k_),), stroke=0)
    if sc['title']:
        tcol = (255, 105, 90) if trap else GOLD
        size = int(48 + 8 * (1 - a)) if not fast else int(54 + 10 * (1 - a))
        text(d, (360, 222 - int(18 * (1 - a))), sc['title'], fit(sc['title'], size), tcol + (int(255 * a),), stroke=4)
    if sc['sub']:
        text(d, (360 - int(40 * (1 - b)), 276 + (56 if trap else 0)), sc['sub'], fit(sc['sub'], 32 if trap else 30), ((120, 235, 140) if trap else WHITE) + (int(255 * b),))
    sid = sc['id']
    # labels pinned to organs (positions exported by Blender), stacked so they never overlap
    placed = []
    for j, lab in enumerate(sc.get('labels', [])):
        key = lab if isinstance(lab, str) else lab['key']; txt = IDX.get(key, {}).get('hi', key) if isinstance(lab, str) else lab['text']
        if key not in p or t < .5 + .45 * j: continue
        x, y, z = p[key]
        if z <= 0 or not (20 < x < 700 and 300 < y < 1030): continue
        side = -1 if x > 360 else 1
        cx = 360 + side * 190; cy = min(max(y, 340), 1000)
        while any(abs(cy - q) < 62 for q in placed): cy += 64
        placed.append(cy)
        c = (GOLD, CYAN, WHITE)[j % 3]
        chip(d, (cx, cy), txt, c, n=27, anchor_pt=(x, y))
    if '__ball' in p and p['__ball'][2] > 0 and p.get('__ballt'):
        bx, by, _ = p['__ball']
        if 20 < bx < 700 and 300 < by < 1030:
            side = -1 if bx > 360 else 1
            chip(d, (min(max(bx + side * 120, 90), 630), max(by - 70, 330)), p['__ballt'], (255, 170, 60), n=26, anchor_pt=(bx, by))
    if sid == 'hook' and sc.get('hook_line', 'अंत तक देखो, कभी नहीं भूलोगे'):
        q = 1 + .06 * math.sin(t * 7)
        text(d, (360, 980), sc.get('hook_line', 'अंत तक देखो, कभी नहीं भूलोगे'), int(30 * q), CYAN)
    if 'quiz' in sc:
        qz = sc['quiz']; c = ease((t - .2) / .4)
        y0 = 330 + int(30 * (1 - c)); al = int(235 * c)
        d.rounded_rectangle((60, y0, 660, y0 + 250), radius=22, fill=(10, 24, 38, al), outline=GOLD + (al,), width=3)
        text(d, (360, y0 + 48), qz['q'], fit(qz['q'], 33, 560), WHITE + (al,), stroke=0)
        pulse = int(6 * math.sin(t * 6))
        for j, opt in enumerate((qz['a'], qz['b'])):
            yy = y0 + 112 + j * 64
            d.rounded_rectangle((110, yy - 25, 610, yy + 25), radius=14, fill=(22, 46, 64, al), outline=CYAN + (al,), width=2)
            text(d, (360, yy), opt, 30, CYAN + (al,), stroke=0)
        end = LEN[k] / FPS - t < 1.8                      # last 1.8 s: follow promise end card
        if end:
            e_ = ease((1.8 - (LEN[k] / FPS - t)) / .3)
            d.rounded_rectangle((50, 640, 670, 1010), radius=26, fill=(8, 18, 30, int(240 * e_)), outline=(255, 196, 60, int(255 * e_)), width=4)
            text(d, (360, 690), 'कल 13:00 बजे', 34, (255, 196, 60, int(255 * e_)), stroke=0)
            if TL.get('next'): text(d, (360, 770), TL['next'], fit(TL['next'], 46, 580), (255, 255, 255, int(255 * e_)))
            text(d, (360, 860), 'फ़ॉलो करो — रोज़ एक 3D सवाल', fit('फ़ॉलो करो — रोज़ एक 3D सवाल', 34, 580), CYAN + (int(255 * e_),), stroke=0)
            text(d, (360, 940), '@minuteme_gs', 30, (200, 210, 220, int(255 * e_)), stroke=0)
        elif t > 1.2: text(d, (360, 1000 + pulse), qz['cta'], 38, GOLD)
        if TL.get('next') and t > 1.6 and not end:
            chip(d, (360, 940), 'अगली रील: ' + TL['next'], CYAN, n=26)
    # step tracker + progress (above Instagram's caption area)
    st = sc['step']
    if st >= 0:
        d.rounded_rectangle((36, 1040, 684, 1150), radius=16, fill=(8, 24, 36, 210), outline=(54, 100, 118), width=2)
        for j, lab in enumerate(TL['steps']):
            x = 117 + j * 162; on_ = j == st; c = GOLD if on_ else (120, 150, 165) if j > st else CYAN
            r = 13 + (3 * math.sin(t * 6) if on_ else 0)
            d.ellipse((x - r, 1072 - r, x + r, 1072 + r), fill=c)
            if j < 3: d.line([(x + 18, 1072), (x + 144, 1072)], fill=CYAN if j < st else (60, 90, 105), width=3)
            d.text((x, 1112), lab, font=font(23), fill=c, anchor='mm')
    d.text((360, 1184), TL.get('credit', '3D: Z-Anatomy, BodyParts3D (CC BY-SA)'), font=font(15), fill=(150, 170, 182), anchor='mm')
    d.rectangle((36, 1164, 684, 1168), fill=(40, 70, 88)); d.rectangle((36, 1164, 36 + int(648 * f / (N - 1)), 1168), fill=CYAN)
    return im

# ---------------------------------------------------------------- sound design (no external audio)
def make_audio(path):
    """Phone-audible mix: male voiceover on top, soft music ducked under it, heartbeat/whoosh/chime effects."""
    sr = 44100; total = N / FPS; n = int(total * sr); tt = np.arange(n) / sr; rng = np.random.default_rng(3)
    music = np.zeros(n)
    for fr, amp in ((220, .10), (261.6, .08), (329.6, .07), (440, .035)):            # warm A-minor pad, mid range
        music += amp * np.sin(2 * np.pi * fr * tt + rng.random() * 6) * (.75 + .25 * np.sin(2 * np.pi * .2 * tt + fr))
    notes = (440, 523.3, 659.3, 880, 659.3, 523.3)                                    # gentle pluck arpeggio
    for k, t0 in enumerate(np.arange(.4, total - .4, .5)):
        i0 = int(t0 * sr); m = min(int(.45 * sr), n - i0); x = np.arange(m) / sr; fr = notes[k % len(notes)]
        music[i0:i0 + m] += .09 * (np.sin(2 * np.pi * fr * x) + .3 * np.sin(4 * np.pi * fr * x)) * np.exp(-x * 7)
    music *= np.clip(tt / 1.0, 0, 1) * np.clip((total - tt) / 1.2, 0, 1)
    fx = np.zeros(n)
    def burst(t0, dur, lo, hi, amp):
        i0 = max(0, int(t0 * sr)); m = min(int(dur * sr), n - i0)
        if m <= 0: return
        w = rng.standard_normal(m); spec = np.fft.rfft(w); fq = np.fft.rfftfreq(m, 1 / sr); spec[(fq < lo) | (fq > hi)] = 0
        x = np.fft.irfft(spec, m); fx[i0:i0 + m] += amp * x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
    for s0 in START[1:]: burst(s0 / FPS - .3, .6, 500, 6000, .22)                      # whoosh at every cut
    for i, scn in enumerate(TL['scenes']):
        t0 = START[i] / FPS; dur = LEN[i] / FPS
        if 'quiz' in scn:
            for k, fr in ((t0 + .2, 880), (t0 + .38, 1318.5)):
                i0 = int(k * sr); m = min(int(1.2 * sr), n - i0); x = np.arange(m) / sr
                fx[i0:i0 + m] += .25 * np.sin(2 * np.pi * fr * x) * np.exp(-x * 5)
        if 'beat' in scn.get('effects', []):                                          # lub-dub, audible on phone speakers
            beat = 0
            while (bt := beat / 1.2) < t0 + dur:
                for off, amp in ((.1 / 1.2, .55), (.32 / 1.2, .35)):
                    t1 = bt + off
                    if t0 <= t1 < t0 + dur:
                        i0 = int(t1 * sr); m = min(int(.14 * sr), n - i0); x = np.arange(m) / sr
                        fx[i0:i0 + m] += amp * (np.sin(2 * np.pi * 75 * x) + .6 * np.sin(2 * np.pi * 150 * x) + .35 * np.sin(2 * np.pi * 300 * x)) * np.exp(-x * 28)
                beat += 1
    voice = np.zeros(n); vj = OUT / 'voice' / 'voice.json'
    if vj.exists() and json.loads(vj.read_text()).get('provider'):
        for i in range(len(TL['scenes'])):
            p = OUT / 'voice' / f'seg_{i}.wav'
            if not p.exists(): continue
            with wave.open(str(p)) as w: v = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
            i0 = int((START[i] / FPS + .25) * sr); m = min(len(v), n - i0)
            if m > 0: voice[i0:i0 + m] += v[:m]
        if np.abs(voice).max() > 0: voice *= .9 / np.abs(voice).max()
    env = np.convolve(np.abs(voice), np.ones(int(.12 * sr)) / int(.12 * sr), 'same'); env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
    mix = voice + (music * (1 - .7 * env)) * 1.0 + fx * (1 - .5 * env)
    mix *= .95 / (np.abs(mix).max() + 1e-9)
    with wave.open(str(path), 'wb') as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((mix * 32767).astype(np.int16).tobytes())


def carousel():
    """Save-worthy revision card from the reel's own 3D frames: cover, 3 key scenes, exam trap, quiz + answer."""
    out = OUT / 'carousel'; out.mkdir(exist_ok=True)
    for old in out.glob('*.jpg'): old.unlink()
    CW, CH = 1080, 1350
    def big(n): return ImageFont.truetype(str(R / 'Mukta.ttf'), n)
    def fitc(s, n, w=980):
        while n > 26 and big(n).getlength(s) > w: n -= 2
        return n
    def frame_of(i):
        f = START[i] + int(LEN[i] * .6)
        im = Image.open(OUT / 'frames' / f'{f:04d}.png').convert('RGB')
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        return im.crop((0, 200, 720, 1100)).resize((CW, CH), Image.LANCZOS)
    def card(bg, top, title, sub, col, idx, note=''):
        im = bg.convert('RGBA'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        for y in range(420): d.line([(0, CH - y), (CW, CH - y)], fill=(4, 10, 18, int(235 * (1 - y / 420) ** .6)))
        for y in range(220): d.line([(0, y), (CW, y)], fill=(4, 10, 18, int(200 * (1 - y / 220))))
        d.rounded_rectangle((50, 46, 50 + big(30).getlength(top) + 44, 100), radius=26, fill=(255, 196, 60, 240))
        d.text((72, 73), top, font=big(30), fill=(20, 24, 30), anchor='lm')
        d.text((CW - 60, 73), f'{idx}/6', font=big(30), fill=(220, 230, 240), anchor='rm')
        d.text((CW / 2, CH - 300), title, font=big(fitc(title, 62)), fill=col, anchor='mm', stroke_width=3, stroke_fill=INK)
        if sub: d.text((CW / 2, CH - 200), sub, font=big(fitc(sub, 40)), fill=WHITE, anchor='mm', stroke_width=2, stroke_fill=INK)
        d.text((CW / 2, CH - 70), note or '@minuteme_gs  ·  सेव करो, परीक्षा से पहले दोहराओ', font=big(28), fill=(170, 190, 205), anchor='mm')
        return Image.alpha_composite(im, ov).convert('RGB')
    sc = TL['scenes']; top = 'MinuteMe 3D' + (f"  ·  Day {TL['day']}" if TL.get('day') else '')
    body = [i for i, s in enumerate(sc) if s['id'] not in ('hook', 'quiz', 'trap')][:3]
    pages = [card(frame_of(0), top, sc[0]['title'], TL.get('topic', ''), GOLD, 1, 'स्वाइप करो →')]
    for n, i in enumerate(body): pages.append(card(frame_of(i), top, sc[i]['title'], sc[i].get('sub', ''), GOLD, n + 2))
    trap = next((i for i, s in enumerate(sc) if s.get('trap')), None)
    if trap is not None:
        bg = Image.new('RGB', (CW, CH), (10, 16, 26)); d = ImageDraw.Draw(bg)
        d.rounded_rectangle((70, 300, CW - 70, 600), radius=30, fill=(70, 18, 18)); d.rounded_rectangle((70, 680, CW - 70, 980), radius=30, fill=(14, 60, 30))
        d.text((CW / 2, 360), 'गलत', font=big(40), fill=(255, 150, 140), anchor='mm')
        w_ = sc[trap]['title'].replace('गलती: ', ''); r_ = sc[trap]['sub'].replace('सही: ', '')
        d.text((CW / 2, 480), w_, font=big(fitc(w_, 54, 900)), fill=(255, 225, 220), anchor='mm')
        d.text((CW / 2, 740), 'सही', font=big(40), fill=(150, 240, 170), anchor='mm')
        d.text((CW / 2, 860), r_, font=big(fitc(r_, 54, 900)), fill=(225, 255, 230), anchor='mm')
        pages.append(card(bg, top, 'परीक्षा की आम गलती', '', (255, 120, 100), 5))
    qz = sc[-1].get('quiz')
    if qz:
        bg = Image.new('RGB', (CW, CH), (10, 16, 26)); d = ImageDraw.Draw(bg)
        d.text((CW / 2, 330), qz['q'], font=big(fitc(qz['q'], 50, 960)), fill=WHITE, anchor='mm')
        for j, key in enumerate(('a', 'b')):
            y = 470 + j * 150; ok = qz.get('ans') == key
            d.rounded_rectangle((120, y, CW - 120, y + 110), radius=24, fill=(20, 90, 50) if ok else (28, 40, 56), outline=(120, 240, 150) if ok else (90, 110, 130), width=4)
            d.text((CW / 2, y + 55), qz[key] + ('  ✔' if False else ''), font=big(fitc(qz[key], 46, 760)), fill=WHITE, anchor='mm')
        if qz.get('ans'): d.text((CW / 2, 820), 'सही जवाब: ' + qz[qz['ans']], font=big(44), fill=(150, 240, 170), anchor='mm')
        nxt = ('कल 13:00: ' + TL['next']) if TL.get('next') else 'रोज़ एक 3D सवाल'
        pages.append(card(bg, top, 'फ़ॉलो करो @minuteme_gs', nxt, CYAN, 6))
    for n, im in enumerate(pages, 1):
        d = ImageDraw.Draw(im); d.rectangle((CW - 150, 46, CW - 50, 100), fill=(4, 10, 18)); d.text((CW - 60, 73), f'{n}/{len(pages)}', font=big(30), fill=(220, 230, 240), anchor='rm')
        im.save(out / f'{n:02d}.jpg', quality=90)
    print('CAROUSEL', len(pages), 'pages')

if __name__ == '__main__':
    wav = OUT / 'soundtrack.wav'; make_audio(wav)
    out = OUT / 'reel.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', str(wav), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(out)], stdin=subprocess.PIPE)
    sheet = []
    for f in range(N):
        base = Image.open(OUT / 'frames' / f'{f:04d}.png').convert('RGBA')
        if base.size != (W, H): base = base.resize((W, H), Image.LANCZOS)   # preview renders at lower %
        fr = Image.alpha_composite(base, overlay(f)).convert('RGB')
        ff.stdin.write(fr.tobytes())
        if f in [START[i] + LEN[i] * 2 // 3 for i in range(len(LEN))] + [10]: sheet.append(fr.resize((270, 480)))
    ff.stdin.close(); assert ff.wait() == 0
    cs = Image.new('RGB', (270 * 4, 480 * 2), (5, 10, 16))
    for i, im in enumerate(sorted(sheet, key=lambda x: 0)[:8]): cs.paste(im, ((i % 4) * 270, (i // 4) * 480))
    cs.save(OUT / 'contact_sheet.jpg', quality=88)
    info = {'video': out.name, 'frames': N, 'seconds': N / FPS, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'bytes': out.stat().st_size}
    carousel()
    (OUT / 'file_checks.json').write_text(json.dumps(info, indent=2, ensure_ascii=False)); print(info)
