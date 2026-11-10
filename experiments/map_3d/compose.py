"""Hindi overlays + sound on top of the 3D map frames -> reel.mp4 (deterministic).
Env: TOPIC=plan.json OUT=dir MAP_ROOT=folder.  Needs Pillow with raqm, numpy, ffmpeg."""
import os, json, math, subprocess, hashlib, wave
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R = Path(os.environ.get('MAP_ROOT', Path(__file__).parent))
OUT = Path(os.environ.get('OUT', R / 'out'))
TL = json.loads(Path(os.environ['TOPIC']).read_text(encoding='utf-8'))
PINS = json.loads((OUT / 'pins.json').read_text())
FPS = TL['fps']; W, H = 720, 1280
LEN = [round(s['seconds'] * FPS) for s in TL['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]
N = sum(LEN)
GOLD = (255, 205, 70); WHITE = (246, 248, 250); CYAN = (110, 220, 255); GREEN = (90, 225, 130); INK = (6, 14, 24)
LET = 'ABCD'


def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
OPT_COL = [rgb(r['color']) for r in TL.get('rivers', [])] or [rgb(c) for c in ('#ff7a45', '#4ade80', '#c084fc', '#38bdf8')]
while len(OPT_COL) < 4: OPT_COL.append((180, 190, 200))


@lru_cache(None)
def font(n): return ImageFont.truetype(str(R / 'Mukta.ttf'), n)
def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3
def scene_of(f):
    for i in range(len(START) - 1, -1, -1):
        if f >= START[i]: return i, f - START[i]


def fit(s, n, maxw=640):
    while n > 18 and font(n).getlength(s) > maxw: n -= 1
    return n


def wrap(s, n, maxw):
    words, lines, cur = s.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if font(n).getlength(t) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def text(d, xy, s, n, c, anchor='mm', stroke=3):
    d.text(xy, s, font=font(n), fill=c, anchor=anchor, stroke_width=stroke, stroke_fill=INK)


def chip(d, xy, s, c, n=26, anchor_pt=None, alpha=255):
    x, y = xy; w = d.textlength(s, font=font(n)) + 30; h = n + 18
    x = min(max(x, w / 2 + 14), W - w / 2 - 14)
    if anchor_pt:
        d.line([(x, y + h / 2 if anchor_pt[1] > y else y - h / 2), anchor_pt], fill=c + (alpha,), width=3)
        d.ellipse((anchor_pt[0] - 6, anchor_pt[1] - 6, anchor_pt[0] + 6, anchor_pt[1] + 6), fill=c + (alpha,))
    d.rounded_rectangle((x - w / 2, y - h / 2, x + w / 2, y + h / 2), radius=h / 2, fill=(8, 20, 32, int(220 * alpha / 255)), outline=c + (alpha,), width=2)
    d.text((x, y + 1), s, font=font(n), fill=c + (alpha,), anchor='mm')


VOICE = {}
vj = OUT / 'voice' / 'voice.json'
if vj.exists(): VOICE = json.loads(vj.read_text(encoding='utf-8'))


def tick(d, x, y, r, c):
    d.line([(x - r * .9, y), (x - r * .25, y + r * .7), (x + r, y - r * .8)], fill=c, width=max(4, int(r / 3)), joint='curve')


def title_block(d, s, t, fast=False, col=GOLD):
    a = ease(t / (.15 if fast else .3)); lines = wrap(s, 44, 640)
    n = 44 if len(lines) <= 2 else 38; lines = wrap(s, n, 640)[:3]
    y0 = 205 - (len(lines) - 1) * 26 - int(14 * (1 - a))
    for i, ln in enumerate(lines): text(d, (360, y0 + i * (n + 10)), ln, n, col + (int(255 * a),), stroke=4)
    return y0 + len(lines) * (n + 10)


def overlay(f):
    k, age = scene_of(f); sc = TL['scenes'][k]; p = PINS[f]; t = age / FPS; dur = LEN[k] / FPS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(360): d.line([(0, i), (W, i)], fill=(2, 8, 18, int(200 * (1 - i / 360) ** 1.5)))
    for i in range(330): d.line([(0, H - i), (W, H - i)], fill=(2, 8, 18, int(215 * (1 - i / 330) ** 1.3)))
    badge = TL.get('badge', 'MinuteMe 3D नक्शा') + '  ·  PYQ ' + TL.get('exam_short', '')
    bw = font(21).getlength(badge) + 30
    d.rounded_rectangle((36, 92, 36 + bw, 124), radius=16, fill=(255, 196, 60, 235))
    d.text((36 + bw / 2, 108), badge, font=font(21), fill=(20, 24, 30), anchor='mm')
    sid = sc['id']
    # ---- title area
    if sid in ('hook', 'options'):
        title_block(d, TL['question'], t if sid == 'hook' else 1, fast=sid == 'hook', col=WHITE if sid == 'options' else GOLD)
    elif sid == 'reveal':
        a = ease(t / .25); s_ = 1 + .25 * (1 - a)
        d.rounded_rectangle((70, 150, 650, 250), radius=26, fill=(16, 120, 60, int(235 * a)), outline=(150, 255, 180, int(255 * a)), width=3)
        n_ = fit(sc['title'], int(46 * s_), 500); tw = font(n_).getlength(sc['title'])
        tick(d, 360 - tw / 2 - 30, 200, 20, (255, 255, 255, int(255 * a)))
        text(d, (360 + 22, 200), sc['title'], n_, (255, 255, 255, int(255 * a)), stroke=0)
        b = ease((t - .5) / .4); text(d, (360, 290), sc['sub'], fit(sc['sub'], 32), WHITE + (int(255 * b),))
    else:
        a = ease(t / .3); text(d, (360, 190), sc['title'], fit(sc['title'], 50), GOLD + (int(255 * a),), stroke=4)
    # ---- labels pinned to the 3D map
    placed = []
    for li, lab in enumerate(sc.get('labels', [])):
        key = f'{k}:{li}'
        if key not in p or t < lab.get('t', 0): continue
        x, y, z = p[key]
        if z <= 0 or not (10 < x < 710 and 320 < y < 1000): continue
        al = int(255 * ease((t - lab.get('t', 0)) / .25))
        if sid == 'reveal' and lab.get('kind') == 'river' or lab.get('kind') == 'pin' and sid in ('reveal', 'end'): c = rgb(lab['color'])
        else: c = rgb(lab['color'])
        if lab.get('kind') == 'letter':
            c = rgb(lab['color']); r_ = 24
            d.ellipse((x - 34 - r_, y - r_, x - 34 + r_, y + r_), fill=c + (al,), outline=(255, 255, 255, al), width=2)
            d.text((x - 34, y), lab['text'], font=font(30), fill=(10, 16, 24, al), anchor='mm'); continue
        if lab.get('kind') == 'anchor':
            w_ = font(26).getlength(lab['text']) + 30
            chip(d, (min(x + 14 + w_ / 2, W - w_ / 2 - 14), y), lab['text'], rgb(lab['color']), n=26, alpha=al); continue
        if lab.get('kind') == 'pin':
            cx, cy = x, y - 58
        else:
            side = -1 if x > 360 else 1; cx, cy = x + side * 110, y - 46
        while any(abs(cy - q[1]) < 44 and abs(cx - q[0]) < 220 for q in placed): cy -= 46
        placed.append((cx, cy))
        chip(d, (cx, cy), lab['text'], c, n=27 if lab.get('kind') != 'point' else 24, anchor_pt=(x, y), alpha=al)
    # ---- option cards + countdown
    if sid == 'options' or sid == 'hook' and t > dur - .6:
        a = ease((t - (0 if sid == 'options' else dur - .6)) / .35)
        reveal_at = TL['answer']
        for i, opt in enumerate(TL['options']):
            col, row = i % 2, i // 2
            x0 = 44 + col * 322; y0 = 1010 + row * 74 + int(30 * (1 - a))
            show = a if sid == 'hook' else ease((t - .55 * i) / .3)
            if show <= 0: continue
            d.rounded_rectangle((x0, y0, x0 + 310, y0 + 62), radius=16, fill=(10, 22, 36, int(235 * show)), outline=OPT_COL[i] + (int(255 * show),), width=3)
            d.ellipse((x0 + 10, y0 + 10, x0 + 52, y0 + 52), fill=OPT_COL[i] + (int(255 * show),))
            d.text((x0 + 31, y0 + 31), LET[i], font=font(28), fill=(10, 16, 24, int(255 * show)), anchor='mm')
            d.text((x0 + 66, y0 + 32), opt, font=font(fit(opt, 30, 230)), fill=WHITE + (int(255 * show),), anchor='lm')
        if sid == 'options' and t >= 1.0:
            text(d, (360, 975), 'कमेंट में अपना जवाब लिखो!', 30, CYAN)
        if sid == 'options' and sc.get('countdown'):
            cd0 = dur - 2.4
            if t >= cd0:
                n_ = 3 - int((t - cd0) / .8); ph = ((t - cd0) % .8) / .8
                if n_ >= 1:
                    r_ = 42 + 10 * (1 - ease(ph * 3)); cx_, cy_ = 630, 340
                    d.ellipse((cx_ - r_, cy_ - r_, cx_ + r_, cy_ + r_), fill=(255, 196, 60, 235))
                    d.arc((cx_ - r_ - 7, cy_ - r_ - 7, cx_ + r_ + 7, cy_ + r_ + 7), -90, -90 + 360 * (1 - ph), fill=(255, 255, 255, 255), width=6)
                    text(d, (cx_, cy_ - 3), str(n_), 56, (20, 24, 30), stroke=0)
    # ---- answer card stays visible after reveal
    if sid == 'reveal':
        i = TL['answer']; a = ease((t - .2) / .3)
        d.rounded_rectangle((150, 1020, 570, 1090), radius=18, fill=(14, 90, 48, int(235 * a)), outline=(150, 255, 180, int(255 * a)), width=3)
        text(d, (360, 1055), f'{LET[i]}  {TL["options"][i]}', 38, (255, 255, 255, int(255 * a)), stroke=0)
    # ---- journey facts
    if sid == 'path':
        rows = [sc.get('sub'), sc.get('sub2'), sc.get('sub3')]
        times = [.3, 1.6, dur - 1.6]
        for j, (row, t0) in enumerate(zip(rows, times)):
            if not row or t < t0: continue
            a = ease((t - t0) / .3); y = 990 + j * 60
            head, _, rest = row.partition(': ')
            d.rounded_rectangle((40, y - 26, 680, y + 26), radius=14, fill=(8, 22, 36, int(225 * a)), outline=(70, 130, 160, int(255 * a)), width=2)
            d.text((60, y), head, font=font(26), fill=GOLD + (int(255 * a),), anchor='lm')
            hw = font(26).getlength(head) + 76
            d.text((hw, y), rest, font=font(fit(rest, 27, 680 - hw - 20)), fill=WHITE + (int(255 * a),), anchor='lm')
    if sid in ('fact', 'trick'):
        a = ease((t - .3) / .4)
        if sc.get('sub'):
            lines = wrap(sc['sub'], 30, 600)[:3]; y0 = 1150 - 42 * len(lines) - 20
            d.rounded_rectangle((40, y0 - 18, 680, 1140), radius=18, fill=(8, 22, 36, int(225 * a)), outline=(70, 130, 160, int(255 * a)), width=2)
            for j, ln in enumerate(lines): d.text((360, y0 + 20 + j * 42), ln, font=font(30), fill=WHITE + (int(255 * a),), anchor='mm')
        else: y0 = 1150
        for j, row in enumerate([sc.get('sub2'), sc.get('sub3')]):
            if not row: continue
            b = ease((t - 1.2 - .5 * j) / .3); head, _, rest = row.partition(': ')
            yy = y0 - 60 - j * 58
            d.rounded_rectangle((40, yy - 25, 680, yy + 25), radius=14, fill=(8, 22, 36, int(225 * b)), outline=(70, 130, 160, int(255 * b)), width=2)
            d.text((60, yy), head, font=font(26), fill=GOLD + (int(255 * b),), anchor='lm')
            hw = font(26).getlength(head) + 76
            d.text((hw, yy), rest, font=font(fit(rest, 28, 680 - hw - 20)), fill=WHITE + (int(255 * b),), anchor='lm')
    # ---- end card
    if sc.get('end'):
        a = ease((t - .2) / .4)
        d.rounded_rectangle((60, 300, 660, 420), radius=24, fill=(10, 24, 38, int(235 * a)), outline=GOLD + (int(255 * a),), width=3)
        text(d, (360, 360), sc['sub'], fit(sc['sub'], 52, 560), GOLD + (int(255 * a),), stroke=0)
        b = ease((t - 1.0) / .4)
        d.rounded_rectangle((60, 990, 660, 1120), radius=24, fill=(8, 18, 30, int(240 * b)), outline=(255, 196, 60, int(255 * b)), width=3)
        text(d, (360, 1030), 'सही था? कमेंट में "सही" लिखो', 34, WHITE + (int(255 * b),), stroke=0)
        text(d, (360, 1080), TL.get('follow', 'फ़ॉलो करो — रोज़ 3D में एक PYQ'), 30, CYAN + (int(255 * b),), stroke=0)
    d.text((360, 1196), TL.get('credit', ''), font=font(15), fill=(150, 170, 182), anchor='mm')
    d.rectangle((36, 1172, 684, 1176), fill=(40, 70, 88)); d.rectangle((36, 1172, 36 + int(648 * f / (N - 1)), 1176), fill=CYAN)
    return im


def make_audio(path):
    sr = 44100; total = N / FPS; n = int(total * sr); tt = np.arange(n) / sr; rng = np.random.default_rng(5)
    music = np.zeros(n)
    for fr, amp in ((110, .07), (164.8, .05), (220, .05), (329.6, .03)):
        music += amp * np.sin(2 * np.pi * fr * tt + rng.random() * 6) * (.7 + .3 * np.sin(2 * np.pi * .25 * tt + fr))
    beat = 60 / 112
    for k_, t0 in enumerate(np.arange(.2, total - .3, beat / 2)):
        i0 = int(t0 * sr); m = min(int(.12 * sr), n - i0); x = np.arange(m) / sr
        music[i0:i0 + m] += (.10 if k_ % 2 == 0 else .05) * np.sin(2 * np.pi * (660 if k_ % 4 else 880) * x) * np.exp(-x * 30)
    music *= np.clip(tt / .8, 0, 1) * np.clip((total - tt) / 1.0, 0, 1)
    fx = np.zeros(n)

    def tone(t0, fr, dur, amp, decay=6):
        i0 = int(t0 * sr); m = min(int(dur * sr), n - i0)
        if m > 0: x = np.arange(m) / sr; fx[i0:i0 + m] += amp * np.sin(2 * np.pi * fr * x) * np.exp(-x * decay)

    def burst(t0, dur, lo, hi, amp):
        i0 = max(0, int(t0 * sr)); m = min(int(dur * sr), n - i0)
        if m <= 0: return
        w_ = rng.standard_normal(m); spec = np.fft.rfft(w_); fq = np.fft.rfftfreq(m, 1 / sr); spec[(fq < lo) | (fq > hi)] = 0
        x = np.fft.irfft(spec, m); fx[i0:i0 + m] += amp * x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * np.linspace(0, 1, m)) ** 2
    for s0 in START[1:]: burst(s0 / FPS - .25, .5, 400, 5000, .18)
    for i, s in enumerate(TL['scenes']):
        t0 = START[i] / FPS; dur = LEN[i] / FPS
        for a in s.get('actions', []):
            if a['type'] == 'pin': tone(t0 + a['t'] + .37, 520, .25, .35, 14); burst(t0 + a['t'] + .3, .2, 60, 400, .3)
        if s.get('countdown'):
            for j in range(3): tone(t0 + dur - 2.4 + .8 * j, 1000, .12, .3, 25)
        if s['id'] == 'reveal':
            for dt, fr in ((.05, 784), (.17, 988), (.29, 1318.5)): tone(t0 + dt, fr, 1.0, .25, 5)
    voice = np.zeros(n)
    if VOICE.get('provider'):
        for i in range(len(TL['scenes'])):
            p = OUT / 'voice' / f'seg_{i}.wav'
            if not p.exists(): continue
            with wave.open(str(p)) as w_: v = np.frombuffer(w_.readframes(w_.getnframes()), '<i2').astype(np.float32) / 32768
            i0 = int((START[i] / FPS + .25) * sr); m = min(len(v), n - i0)
            if m > 0: voice[i0:i0 + m] += v[:m]
        if np.abs(voice).max() > 0: voice *= .9 / np.abs(voice).max()
    env = np.convolve(np.abs(voice), np.ones(int(.12 * sr)) / int(.12 * sr), 'same'); env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
    mix = voice + music * (1 - .65 * env) + fx * (1 - .4 * env)
    mix *= .95 / (np.abs(mix).max() + 1e-9)
    with wave.open(str(path), 'wb') as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((mix * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    wav = OUT / 'soundtrack.wav'; make_audio(wav)
    out = OUT / 'reel.mp4'
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', str(wav), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', str(out)], stdin=subprocess.PIPE)
    marks = [START[i] + LEN[i] * 2 // 3 for i in range(len(LEN))]; sheet = []
    for f in range(N):
        base = Image.open(OUT / 'frames' / f'{f:04d}.png').convert('RGBA')
        if base.size != (W, H): base = base.resize((W, H), Image.LANCZOS)
        fr = Image.alpha_composite(base, overlay(f)).convert('RGB'); ff.stdin.write(fr.tobytes())
        if f in marks: sheet.append(fr.resize((270, 480)))
    ff.stdin.close(); assert ff.wait() == 0
    cs = Image.new('RGB', (270 * len(sheet), 480), (5, 10, 16))
    for i, im in enumerate(sheet): cs.paste(im, (i * 270, 0))
    cs.save(OUT / 'contact_sheet.jpg', quality=88)
    info = {'video': out.name, 'frames': N, 'seconds': N / FPS, 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(), 'voice': VOICE.get('provider')}
    (OUT / 'file_checks.json').write_text(json.dumps(info, indent=2, ensure_ascii=False)); print(info)
