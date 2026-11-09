"""Hindi titles + sound effects over the rendered optics frames -> MP4 (demo only, never posted)."""
import sys, os, glob, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]
FPS = 24
font = lambda n: ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'known_good', 'Mukta.ttf'), n)
frames = sorted(glob.glob(os.path.join(src, 'f_*.png')))
TITLES = [('सफ़ेद रोशनी में छिपे हैं 7 रंग!', 'प्रिज़्म • प्रकाश का विक्षेपण'), ('उत्तल लेंस: किरणें F पर मिलती हैं', 'अभिसारी लेंस • फोकस बिंदु')]
os.makedirs(src + '/txt', exist_ok=True)
for i, f in enumerate(frames):
    im = Image.open(f).convert('RGB'); d = ImageDraw.Draw(im); shot = 0 if i < len(frames) // 2 else 1
    q = (i % (len(frames) // 2)) / (len(frames) // 2)
    a = min(1, q * 6)
    t1, t2 = TITLES[shot]
    for txt, y, n, col in ((t1, 170, 46, (255, 214, 90)), (t2, 232, 30, (225, 240, 248))):
        w = d.textlength(txt, font=font(n))
        d.text((360 - w / 2, y - 30 * (1 - a)), txt, font=font(n), fill=col, stroke_width=3, stroke_fill=(5, 15, 25))
    if shot == 1 and q > .62:
        d.rounded_rectangle((250, 1060, 470, 1120), 14, fill=(200, 40, 30)); d.text((300, 1068), 'फोकस F', font=font(34), fill=(255, 255, 255))
    d.text((24, 1240), '@MinuteMe_GS', font=font(24), fill=(150, 200, 220))
    im.save(f'{src}/txt/{i:04d}.png')
SR = 44100; T = len(frames) / FPS; t = np.arange(int(SR * T)) / SR
audio = .05 * np.sin(2 * np.pi * 110 * t) * (1 + .5 * np.sin(2 * np.pi * .5 * t))
def add(at, sig):
    s = int(at * SR); audio[s:s + len(sig)] += sig[:len(audio) - s]
k = np.arange(int(SR * .7)) / SR
whoosh = np.random.default_rng(1).normal(0, 1, len(k)) * np.exp(-((k - .3) / .15) ** 2) * .25
chime = sum(np.sin(2 * np.pi * f0 * k) for f0 in (880, 1320, 1760)) * np.exp(-k * 5) * .12
add(1.6, whoosh); add(1.75, chime); add(4.0, whoosh * .7); add(4 + 2.3, chime)
audio = np.clip(audio, -1, 1)
with wave.open(src + '/a.wav', 'w') as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((audio * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', src + '/txt/%04d.png', '-i', src + '/a.wav', '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-shortest', '-movflags', '+faststart', out], check=True)
print('ASSEMBLED', out)
