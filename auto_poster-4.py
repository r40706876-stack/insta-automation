"""
SCIENCE PYQ REEL ENGINE  (Railway | SSC | State exams)
=======================================================
Har run = 1 animated reel: ek asli previous-year Science sawal (Physics / Chemistry / Biology).

Source: science_pyq_bank.json  (book PDF se ek baar convert kiya hua - 3000+ PYQ, jawab ke saath).
        Reel / caption me kisi book / notes ka naam KABHI nahi aata - sirf exam ka naam (RRB Group D + saal).

Reel flow (~25s):
  HOOK      : "SCIENCE PYQ | RAILWAY • SSC • STATE" + exam/saal + kitni baar poochha + asli sawal + 2 jawab taraazu pe
  SAWAL     : 2x2 options + 3-2-1 countdown ("jawab comment karo")
  JAWAB     : galat options ✗ palat ke girte hain, sahi beech me (confetti)
  KYUN?     : 1 line science wajah + yaad-trick + "ye sawal kis-kis exam me" (Railway / SSC / State)
  AGLA      : agle PYQ ka teaser + follow / save

Commands:
  python auto_poster.py                 -> agla sawal: reel banao + Instagram pe daalo (secrets ho to)
  python auto_poster.py --no-post       -> sirf reel banao
  python auto_poster.py --seq 25        -> bank ka sawal no. 25 (progress nahi badalta)
  python auto_poster.py --preview       -> sirf kuch frame PNG (preview/) - jaldi jaanch
  DRY_RUN=1 python auto_poster.py       -> bina internet (awaaz andaze se, silent) - test

Env / GitHub secrets: IG_ACCESS_TOKEN, IG_USER_ID, GEMINI_API_KEY (optional), GROQ_API_KEY (optional)
"""

import os
import re
import sys
import json
import math
import time
import wave
import random
import asyncio
import hashlib
import argparse
import subprocess
import importlib
from pathlib import Path
from functools import lru_cache


def _ensure_packages():
    needed = {"numpy": "numpy", "PIL": "pillow", "requests": "requests", "edge_tts": "edge-tts"}
    missing = []
    for module, pip_name in needed.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pip_name)
    if not missing:
        return
    print("Missing packages install ho rahe hain:", ", ".join(missing))
    base = [sys.executable, "-m", "pip", "install", "--quiet", *missing]
    for cmd in (base, base + ["--break-system-packages"], base + ["--user"]):
        if subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            importlib.invalidate_caches()
            return


_ensure_packages()
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageChops, features


# ============================== CONFIG ==============================

BANK_FILE = os.getenv("PYQ_BANK", "science_pyq_bank.json")
PROGRESS_FILE = "progress.json"
OUTPUT_DIR = "generated_reels"
FINAL_VIDEO = "science_pyq_reel.mp4"

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
GRAPH = "https://graph.facebook.com/v21.0/"

DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

SERIES = "SCIENCE PYQ"
BRAND = "MinuteMe_GS"                       # Instagram account ka naam - har jagah branding
BRAND_HANDLE = "@MinuteMe_GS"
BRAND_SPEAK = "मिनटमी जी एस"                 # awaaz me naam aise bola jaata hai
BRAND_TAGLINE = "1 मिनट  •  1 सवाल  •  पक्का GS"
EXAMS_LINE = "RAILWAY  •  SSC  •  STATE EXAMS"
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "8989971379")
HASHTAGS = "#MinuteMe_GS #sciencepyq #rrbgroupd #ssc #railwayexam"   # Instagram: max 5

VOICE_NAME = os.getenv("VOICE_NAME", "hi-IN-SwaraNeural")
VOICE_RATE = "+8%"
VOICE_PITCH = "+2Hz"

W, H = 1080, 1920
FPS = 30
SR = 44100
VIDEO_CRF = 23
COUNTDOWN_SECONDS = 3
COUNTDOWN_STEP = 0.55
MAX_PAUSE = 0.14          # awaaz ke andar koi chuppi isse lambi nahi
VOICE_LEAD = 0.06
EYE_LEAD = 0.10
READ_WPS = 3.3            # mobile pe Hindi padhne ki speed (shabd/sec)
TRANSITION = 0.30
LOOP_BLEND = 0.35
MAX_TRIES_PER_RUN = 6     # sawal jaanch me fail ho to agla (ek run me itne tak)

FONT_FILE = "Mukta-ExtraBold.ttf"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-ExtraBold.ttf"
FONT_REG_FILE = "Mukta-Medium.ttf"
FONT_REG_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-Medium.ttf"
FALLBACK_FONTS = ["/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
                  "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf",
                  "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                  "C:/Windows/Fonts/Nirmala.ttf"]

# Palette (main reel jaisa dark navy + neon)
BG_TOP = (10, 18, 38)
BG_BOTTOM = (20, 36, 66)
CARD = (14, 27, 45)
CARD_2 = (19, 38, 61)
WHITE = (248, 250, 252)
MUTED = (159, 176, 194)
RED = (239, 68, 68)
GREEN = (34, 197, 94)
YELLOW = (250, 204, 21)
ORANGE = (245, 158, 11)
CYAN = (56, 189, 248)
BLUE = (37, 99, 235)
PURPLE = (139, 92, 246)
EN_COL = (150, 200, 245)
MOODS = {"red": (190, 30, 45), "blue": (30, 90, 200), "yellow": (200, 140, 10),
         "green": (20, 150, 80), "purple": (110, 60, 200)}
SUBJECT_STYLE = {   # subject -> (label, rang)
    "Physics": ("PHYSICS  •  भौतिक विज्ञान", CYAN),
    "Chemistry": ("CHEMISTRY  •  रसायन विज्ञान", ORANGE),
    "Biology": ("BIOLOGY  •  जीव विज्ञान", GREEN),
}


# ============================== TEXT ==============================

_ALLOWED = re.compile(r"[^\u0900-\u097F\u0020-\u007E\u00A0-\u00FF\u2010-\u2027\u20B9\u2126\u03A9\u03B1-\u03C9"
                      r"\u00D7\u00F7\u2192\u2212\u221A\u2248\u2264\u2265\u200C\u200D]")


_SUP = {"1": "", "2": "²", "3": "³"}


def _unit_pow(m):
    pre, unit, n = m.group(1), m.group(2), m.group(3)
    pre = pre.replace("Kg", "kg")
    return (pre or "1") + "/" + unit + _SUP[n]


def clean_text(text):
    if not text:
        return ""
    t = str(text)
    # ms–2 -> m/s², Nm–2 -> N/m², kgm–3 -> kg/m³ (book me ghaat aise likha hota hai)
    t = re.sub(r"(?<![A-Za-z])([A-Za-z]{0,3}?)\s?(s|m|K|g)\s?[–\-−]\s?([123])(?![\d.])", _unit_pow, t)
    t = re.sub(r"[_]{2,}|[–\-]{3,}|\.{4,}|…{2,}|(?:\.\s?){4,}", " ____ ", t)
    t = t.replace("…", "...").replace("—", "-").replace("–", "-").replace("\u2212", "-")
    t = (t.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"'))
    t = re.sub(r"ः\s*([–\-]?)\s*$", ":", t)
    t = _ALLOWED.sub("", t)
    t = re.sub(r"\s+([,।?!:])", r"\1", t)
    t = re.sub(r"(____\s*){2,}", "____ ", t)
    return " ".join(t.split()).strip()


# ============================== FONTS ==============================

_font_path = []
_reg_path = []


def _download(url, path):
    if DRY_RUN:
        return False
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 50000:
            Path(path).write_bytes(r.content)
            return True
    except Exception:
        pass
    return False


def resolve_font():
    if _font_path:
        return _font_path[0]
    p = None
    if os.path.exists(FONT_FILE) and os.path.getsize(FONT_FILE) > 50000:
        p = FONT_FILE
    elif _download(FONT_URL, FONT_FILE):
        p = FONT_FILE
    else:
        for f in ["Mukta-Bold.ttf", os.path.join("assets", "biology_production", "Mukta-Bold.ttf")] + FALLBACK_FONTS:
            if os.path.exists(f) and os.path.getsize(f) > 50000:
                p = f
                break
    if not p:
        raise RuntimeError("Devanagari font nahi mila (Mukta-ExtraBold.ttf repo me rakhiye).")
    _font_path.append(p)
    return p


def resolve_reg_font():
    if _reg_path:
        return _reg_path[0]
    p = None
    if os.path.exists(FONT_REG_FILE) and os.path.getsize(FONT_REG_FILE) > 50000:
        p = FONT_REG_FILE
    elif _download(FONT_REG_URL, FONT_REG_FILE):
        p = FONT_REG_FILE
    _reg_path.append(p or resolve_font())
    return _reg_path[0]


def _tt(path, size):
    if features.check("raqm"):
        return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=256)
def get_font(size):
    return _tt(resolve_font(), int(size))


@lru_cache(maxsize=128)
def get_font_reg(size):
    return _tt(resolve_reg_font(), int(size))


def text_w(text, font):
    return font.getlength(text)


def wrap_words(text, font, max_w):
    lines, cur = [], []
    for w in text.split():
        if cur and text_w(" ".join(cur + [w]), font) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines


@lru_cache(maxsize=512)
def _fit(text, max_w, max_lines, size, min_size, reg=False):
    getf = get_font_reg if reg else get_font
    s = size
    while s >= min_size:
        f = getf(s)
        lines = wrap_words(text, f, max_w)
        if len(lines) <= max_lines and all(text_w(" ".join(l), f) <= max_w for l in lines):
            return s, tuple(tuple(l) for l in lines)
        s -= 2
    f = getf(min_size)
    return min_size, tuple(tuple(l) for l in wrap_words(text, f, max_w))


def fit_lines(text, max_w, max_lines, size, min_size=26, reg=False):
    s, lines = _fit(text, int(max_w), max_lines, int(size), int(min_size), reg)
    return (get_font_reg(s) if reg else get_font(s)), s, [list(l) for l in lines]


# ============================== EASING ==============================

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return clamp((t - start) / dur)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.70158):
    x = x - 1
    return x * x * ((s + 1) * x + s) + 1


def with_alpha(c, a):
    return (c[0], c[1], c[2], int(255 * clamp(a)))


def mix(c1, c2, k):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))


# ============================== SPRITES ==============================

def place(canvas, sprite, cx, cy, scale=1.0, alpha=1.0, angle=0.0):
    if sprite is None or alpha <= 0.01 or scale <= 0.01:
        return
    sp = sprite
    if abs(scale - 1.0) > 0.005:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(angle) > 0.05:
        sp = sp.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.99:
        sp = sp.copy()
        sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)), sp)


def place_flip(canvas, front, back, cx, cy, p, scale=1.0):
    p = clamp(p)
    sp = front if p < 0.5 else back
    sx = abs(math.cos(math.pi * p))
    if sx < 0.03:
        return
    sp = sp.resize((max(1, int(sp.width * sx * scale)), max(1, int(sp.height * scale * (1 + 0.06 * (1 - sx))))),
                   Image.BILINEAR)
    canvas.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)), sp)


@lru_cache(maxsize=64)
def glow_sprite(radius, color, strength=110):
    size = radius * 2
    y, x = np.ogrid[:size, :size]
    d = np.sqrt((x - radius) ** 2 + (y - radius) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * strength
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = color
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


@lru_cache(maxsize=96)
def card_sprite(w, h, fill=CARD_2, outline=(42, 64, 88), width=4, radius=32, shadow=True):
    pad = 30 if shadow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        for i in range(6, 0, -1):
            d.rounded_rectangle((pad - i * 3, pad - i * 3 + 10, pad + w + i * 3, pad + h + i * 3 + 10),
                                radius=radius + i * 3, fill=(0, 0, 0, 12))
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=radius, fill=fill + (255,),
                        outline=outline + (255,), width=width)
    arr = np.array(im).astype(np.float32)
    ramp = np.clip(1 - (np.arange(im.height) - pad) / max(1, h * 0.6), 0, 1)[:, None] * 16
    inside = arr[..., 3] > 250
    for c in range(3):
        arr[..., c] = np.where(inside, np.clip(arr[..., c] + ramp, 0, 255), arr[..., c])
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


@lru_cache(maxsize=64)
def pill_sprite(text, size, fg, bg, outline, reg=False):
    f = get_font_reg(size) if reg else get_font(size)
    w = int(text_w(text, f)) + size * 2
    h = int(size * 1.9)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 2, h - 2), radius=h // 2, fill=bg + (235,), outline=outline + (255,), width=3)
    d.text((w / 2, h / 2), text, font=f, fill=fg + (255,), anchor="mm")
    return im


@lru_cache(maxsize=8)
def x_mark_sprite(size=96):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=RED + (255,))
    m = size * 0.3
    d.line((m, m, size - m, size - m), fill=WHITE + (255,), width=size // 9)
    d.line((size - m, m, m, size - m), fill=WHITE + (255,), width=size // 9)
    return im


@lru_cache(maxsize=8)
def check_sprite(size=140):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, size - 1, size - 1), fill=GREEN + (255,))
    s = size
    d.line((s * 0.27, s * 0.52, s * 0.43, s * 0.68), fill=WHITE + (255,), width=s // 10)
    d.line((s * 0.43, s * 0.68, s * 0.74, s * 0.34), fill=WHITE + (255,), width=s // 10)
    return im


@lru_cache(maxsize=8)
def stamp_sprite(text="PYQ", sub="PREVIOUS YEAR"):
    f, f2 = get_font(86), get_font(28)
    tw = int(max(text_w(text, f), text_w(sub, f2)))
    w, h = tw + 90, 170
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, w - 6, h - 6), radius=22, outline=RED + (255,), width=10, fill=(60, 8, 14, 215))
    d.rounded_rectangle((22, 22, w - 22, h - 22), radius=14, outline=RED + (170,), width=3)
    d.text((w / 2, h / 2 - 14), text, font=f, fill=RED + (255,), anchor="mm")
    d.text((w / 2, h - 40), sub, font=f2, fill=(255, 150, 150, 255), anchor="mm")
    rng = random.Random(7)
    arr = np.array(im)
    for _ in range(300):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        r = rng.randint(1, 3)
        arr[max(0, y - r):y + r, max(0, x - r):x + r, 3] = (arr[max(0, y - r):y + r, max(0, x - r):x + r, 3] * 0.25).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


@lru_cache(maxsize=4)
def lock_sprite(size=80):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(6, size // 10)
    d.arc((size * 0.25, size * 0.05, size * 0.75, size * 0.6), 180, 360, fill=YELLOW + (255,), width=lw)
    d.line((size * 0.25, size * 0.32, size * 0.25, size * 0.5), fill=YELLOW + (255,), width=lw)
    d.line((size * 0.75, size * 0.32, size * 0.75, size * 0.5), fill=YELLOW + (255,), width=lw)
    d.rounded_rectangle((size * 0.12, size * 0.45, size * 0.88, size * 0.95), radius=size // 9, fill=YELLOW + (255,))
    d.ellipse((size * 0.44, size * 0.6, size * 0.56, size * 0.72), fill=(40, 30, 0, 255))
    return im


@lru_cache(maxsize=4)
def rays_sprite(size=1000):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(16):
        a0, a1 = math.radians(i * 22.5), math.radians(i * 22.5 + 9)
        d.polygon([(c, c), (c + math.cos(a0) * c, c + math.sin(a0) * c),
                   (c + math.cos(a1) * c, c + math.sin(a1) * c)], fill=GREEN + (60,))
    mask = np.array(glow_sprite(size // 2, (255, 255, 255), 255).getchannel("A"), dtype=np.float32)
    a = np.array(im.getchannel("A"), dtype=np.float32) * mask / 255.0
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


@lru_cache(maxsize=8)
def atom_sprite(size=200, col=CYAN):
    """Science pehchaan: chhota atom (3 orbit + nucleus) - code se bana."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    big = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    S = size * 2
    for ang in (0, 60, 120):
        lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(lay).ellipse((S * 0.08, S * 0.36, S * 0.92, S * 0.64), outline=col + (230,), width=S // 50)
        big = Image.alpha_composite(big, lay.rotate(ang, resample=Image.BICUBIC))
    d = ImageDraw.Draw(big)
    r = S * 0.08
    d.ellipse((S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r), fill=YELLOW + (255,))
    im = big.resize((size, size), Image.LANCZOS)
    return im


def sheen(canvas, cx, cy, w, h, t, period=2.2, offset=0.0, strength=60):
    ph = ((t + offset) % period) / 0.55
    if ph > 1:
        return
    lay = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lx = -160 + (w + 320) * ph
    d.polygon([(lx, 0), (lx + 70, 0), (lx + 20, h), (lx - 50, h)], fill=(255, 255, 255, strength))
    mask = Image.new("L", (int(w), int(h)), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=34, fill=255)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mask))
    canvas.paste(lay, (int(cx - w / 2), int(cy - h / 2)), lay)


# ============================== BACKGROUND ==============================

@lru_cache(maxsize=8)
def background(mood):
    bw, bh = W + 120, H + 120
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    ty = yy / bh
    base = np.zeros((bh, bw, 3), dtype=np.float32)
    for i in range(3):
        base[..., i] = BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * ty
    col = MOODS[mood]
    for (gx, gy, gr, k) in [(0.2, 0.18, 0.55, 0.55), (0.9, 0.75, 0.6, 0.35)]:
        d = np.sqrt((xx - gx * bw) ** 2 + (yy - gy * bh) ** 2) / (gr * bw)
        g = np.clip(1 - d, 0, 1) ** 2 * k
        for i in range(3):
            base[..., i] += col[i] * g * 0.55
    # science lab-notebook grid (graph paper)
    base += (((xx % 60) < 1.5) | ((yy % 60) < 1.5)).astype(np.float32)[..., None] * 5
    base += (((xx % 12) < 1) | ((yy % 12) < 1)).astype(np.float32)[..., None] * 1.2
    d = np.sqrt(((xx - bw / 2) / (bw / 2)) ** 2 + ((yy - bh / 2) / (bh / 2)) ** 2)
    base *= np.clip(1.15 - 0.35 * d, 0.62, 1)[..., None]
    base += np.random.default_rng(3).normal(0, 4.0, (bh, bw, 1))
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")


_PARTS = [(random.Random(k).random(), random.Random(k + 99).random(), 0.4 + random.Random(k + 7).random())
          for k in range(30)]
_SYMBOLS = ["H2O", "CO2", "F=ma", "pH", "DNA", "NaCl", "V=IR", "O2", "ATP", "g=9.8", "E=mc2", "Fe"]


def bg_frame(mood, gt):
    im = background(mood)
    ox = int(60 + 40 * math.sin(gt * 0.45))
    oy = int(60 + 40 * math.cos(gt * 0.33))
    im = im.crop((ox, oy, ox + W, oy + H))
    d = ImageDraw.Draw(im)
    col = mix((40, 60, 95), MOODS[mood], 0.35)
    for k, (px, py, sp) in enumerate(_PARTS):            # tairti roshni + halke science chinh
        y = (py * H - gt * 38 * sp) % H
        x = px * W + 18 * math.sin(gt * 0.8 + py * 9)
        if k % 5 == 0:
            d.text((x, y), _SYMBOLS[k % len(_SYMBOLS)], font=get_font_reg(26), fill=mix(BG_BOTTOM, col, 0.55),
                   anchor="mm")
        else:
            r = 2 + 3 * sp
            d.ellipse((x - r, y - r, x + r, y + r), fill=col)
    return im


# ============================== KINETIC TEXT ==============================

def word_thresholds(words):
    weights = [len(w) + (3 if re.search(r"[,.!?।]$", w) else 0) + 1 for w in words]
    total = float(sum(weights)) or 1.0
    out, acc = [], 0.0
    for w in weights:
        out.append(acc / total)
        acc += w
    return out


def text_block_h(text, max_w, size, max_lines=4, min_size=30, line_h=1.34):
    _, s, lines = fit_lines(text, max_w, max_lines, size, min_size)
    return int(s * line_h) * len(lines)


def draw_kinetic(canvas, text, cx, max_w, size, p, max_lines=4, color=WHITE, hl_words=(), hl_color=YELLOW,
                 karaoke=True, ghost=0.0, min_size=30, line_h=1.34, center_y=0, th=None, stroke=0):
    """Awaaz ke saath shabd-dar-shabd text; bolta shabd peela. Returns neeche ka y."""
    font, s, lines = fit_lines(text, max_w, max_lines, size, min_size)
    lh = int(s * line_h)
    top = center_y - lh * len(lines) / 2
    words = [w for ln in lines for w in ln]
    if not words:
        return top
    if th is None or len(th) != len(words):
        th = word_thresholds(words)
    n = len(words)
    space = text_w(" ", font)
    layer = Image.new("RGBA", (int(max_w) + 80, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hl = set(hl_words)
    idx = 0
    for li, ln in enumerate(lines):
        line_w = sum(text_w(w, font) for w in ln) + space * (len(ln) - 1)
        x = (layer.width - line_w) / 2
        y = 20 + li * lh + lh / 2
        for w in ln:
            start = th[idx]
            nxt = th[idx + 1] if idx + 1 < n else 1.0
            a = clamp((p - start) / 0.06 + (0.4 if (idx == 0 and p > 0) else 0.0))
            e = ease_out_cubic(a)
            alpha, dy = (ghost, 0) if a <= 0 else (max(ghost, e), (1 - e) * 22)
            key = re.sub(r"[,.!?।:()]", "", w)
            col = hl_color if (key in hl and a > 0) else color
            if karaoke and p > 0 and start <= p < nxt and p < 0.999:
                col = YELLOW
            if alpha > 0.01:
                kw = {"stroke_width": stroke, "stroke_fill": (5, 10, 22, int(255 * alpha))} if stroke else {}
                d.text((x, y + dy), w, font=font, fill=with_alpha(col, alpha), anchor="lm", **kw)
            x += text_w(w, font) + space
            idx += 1
    canvas.paste(layer, (int(cx - layer.width / 2), int(top - 20)), layer)
    return top + lh * len(lines)


def draw_en(cv, text, y_top, max_w=900, size=34, max_lines=2, color=EN_COL, alpha=1.0):
    if not text or alpha <= 0.02:
        return y_top
    f, s_, lines = fit_lines(text, max_w, max_lines, size, 24, reg=True)
    lh = int(s_ * 1.3)
    d = ImageDraw.Draw(cv)
    for k, ln in enumerate(lines[:max_lines]):
        d.text((W / 2, y_top + k * lh + lh / 2), " ".join(ln), font=f, fill=color, anchor="mm")
    return y_top + lh * min(len(lines), max_lines)


QWORDS = ("क्या", "कौन", "कौनसा", "कौन-सा", "कौनसी", "कौन-सी", "कितने", "कितनी", "कितना", "कब", "कहाँ", "किसके",
          "किसकी", "किसका", "किसे", "किस", "कैसे", "क्यों", "नहीं", "सबसे", "अधिकतम", "न्यूनतम", "SI", "____")


def q_highlights(text):
    out = []
    for w in text.split():
        core = re.sub(r"[,.!?।:()]", "", w)
        if core in QWORDS or re.search(r"\d", core):
            out.append(core)
    return tuple(out)


# ============================== BANK + PROGRESS ==============================

def load_bank():
    if not os.path.exists(BANK_FILE):
        raise RuntimeError(f"{BANK_FILE} nahi mila - ise repo me upload kijiye.")
    with open(BANK_FILE, encoding="utf-8") as f:
        return json.load(f)["questions"]


def load_progress():
    st = {}
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                st = json.load(f) or {}
        except Exception:
            st = {}
    if "next_seq" not in st:          # purana (page wala) format -> naya shuru
        st = {"next_seq": 1, "episode": 0, "posted": [], "skipped": {}}
    st.setdefault("episode", 0)
    st.setdefault("posted", [])
    st.setdefault("skipped", {})
    return st


def save_progress(st):
    st["posted"] = st["posted"][-4000:]
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


# ============================== AI: SAFAI + WAJAH (optional) ==============================

ENRICH_PROMPT = """You prepare ONE previous-year Science MCQ (Indian govt exams: Railway RRB Group D, SSC, State exams) for a
short Hindi Instagram reel. The Hindi text was auto-converted from an old font and MAY contain small spelling errors.

QUESTION (Hindi): {q}
OPTIONS: (a) {a} | (b) {b} | (c) {c} | (d) {d}
OFFICIAL ANSWER KEY: ({ans}) {ans_text}
REFERENCE EXPLANATION (may be noisy): {exp}

Tasks - return ONLY JSON:
{{
 "ok": true/false,            // false if the answer key is scientifically WRONG, or the question needs a figure/table, or is unclear
 "problem": "",               // short reason if ok=false
 "question": "...",           // same question, Hindi, ONLY fix spelling/spacing (do NOT change meaning, numbers or units). Use ____ for blanks.
 "options": {{"a":"..","b":"..","c":"..","d":".."}},   // same 4 options, same order, only spelling fixed, keep numbers/units/formulas exactly
 "speak_question": "...",     // the question as it should be SPOKEN in Hindi (Devanagari): spell symbols/units/formulas in words
                              // (e.g. 'm/s2' -> 'मीटर प्रति सेकंड स्क्वायर', 'CO2' -> 'सी ओ टू', 'pH' -> 'पी एच', 'SI' -> 'एस आई'), blanks -> 'खाली स्थान'
 "speak_answer": "...",       // the correct option text as spoken Hindi (same rule)
 "why": "...",                // ONE simple Hindi line (max 18 words): the science reason why the key is correct. No book/coaching names.
 "tip": "...",                // Hindi memory trick / exam tip, max 8 words (can be a short formula like 'दाब = बल / क्षेत्रफल')
 "topic": "...",              // 1-3 word Hindi topic name (e.g. 'प्रकाश का अपवर्तन')
 "en_question": "...",        // short English translation of the question (max 20 words)
 "en_options": {{"a":"..","b":"..","c":"..","d":".."}}
}}"""


def _parse_json(raw):
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        try:
            return json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0)))
        except Exception:
            return None


def _gemini(prompt):
    if not GEMINI_API_KEY:
        return None
    for model in ("gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"):
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": GEMINI_API_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}},
                timeout=90)
            if r.status_code != 200:
                print(f"  Gemini {model}: HTTP {r.status_code}")
                continue
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            js = _parse_json(txt)
            if js:
                return js
        except Exception as exc:
            print(f"  Gemini {model} fail:", str(exc)[:120])
    return None


def _groq(prompt):
    if not GROQ_API_KEY:
        return None
    for model in ("llama-3.3-70b-versatile", "openai/gpt-oss-120b", "llama-3.1-8b-instant"):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                              json={"model": model, "temperature": 0.2,
                                    "response_format": {"type": "json_object"},
                                    "messages": [{"role": "user", "content": prompt}]}, timeout=90)
            if r.status_code != 200:
                print(f"  Groq {model}: HTTP {r.status_code}")
                continue
            js = _parse_json(r.json()["choices"][0]["message"]["content"])
            if js:
                return js
        except Exception as exc:
            print(f"  Groq {model} fail:", str(exc)[:120])
    return None


def _nums(s):
    return sorted(re.findall(r"\d+(?:\.\d+)?", s or ""))


def _hi_ok(s, max_words):
    s = clean_text(s)
    return bool(s) and len(s.split()) <= max_words and not re.search(r"[A-Za-z]{14,}", s)


def ai_enrich(q):
    """AI se: spelling safai + bolne layak text + 1 line wajah + trick + English. Fail -> None."""
    if DRY_RUN or not (GEMINI_API_KEY or GROQ_API_KEY):
        return None
    exp = re.sub(r"\s+", " ", q.get("explanation", ""))[:700]
    prompt = ENRICH_PROMPT.format(q=q["question"], a=q["options"]["a"], b=q["options"]["b"], c=q["options"]["c"],
                                  d=q["options"]["d"], ans=q["answer"], ans_text=q["options"][q["answer"]], exp=exp)
    for fn in (_gemini, _groq):
        js = fn(prompt)
        if not js:
            continue
        if js.get("ok") is False:
            return {"reject": str(js.get("problem") or "AI: answer/sawal galat ya chitra wala")[:160]}
        if not _hi_ok(js.get("why", ""), 26):
            print("  AI wajah kharab -> agla provider")
            continue
        # har hissa alag jaancho: sankhya/lambai badli to us hisse ke liye book ka text
        out = {k: js.get(k) for k in ("why", "tip", "topic", "en_question")}
        if not _hi_ok(out.get("tip") or "", 10):
            out["tip"] = ""
        if not _hi_ok(out.get("topic") or "", 4):
            out["topic"] = ""
        q_ok = _hi_ok(js.get("question", ""), 40) and _nums(js["question"]) == _nums(q["question"])
        if q_ok:
            out["question"] = js["question"]
            out["speak_question"] = js.get("speak_question") or ""
        opts = js.get("options") or {}
        out["options"] = {k: opts[k] for k in "abcd"
                          if isinstance(opts.get(k), str) and opts[k].strip()
                          and _nums(opts[k]) == _nums(q["options"][k]) and len(opts[k].split()) <= 10}
        if q["answer"] in out["options"]:
            out["speak_answer"] = js.get("speak_answer") or ""
        eo = js.get("en_options") or {}
        if all(isinstance(eo.get(k), str) and eo[k].strip() for k in "abcd"):
            out["en_options"] = eo
        return out
    return None


# ============================== BOLNE LAYAK TEXT (fallback) ==============================

_LETTER_HI = {"A": "ए", "B": "बी", "C": "सी", "D": "डी", "E": "ई", "F": "एफ", "G": "जी", "H": "एच", "I": "आई",
              "J": "जे", "K": "के", "L": "एल", "M": "एम", "N": "एन", "O": "ओ", "P": "पी", "Q": "क्यू", "R": "आर",
              "S": "एस", "T": "टी", "U": "यू", "V": "वी", "W": "डब्ल्यू", "X": "एक्स", "Y": "वाई", "Z": "ज़ेड"}
_NUM_HI = {"2": "टू", "3": "थ्री", "4": "फोर", "5": "फाइव", "6": "सिक्स", "7": "सेवन", "8": "एट", "1": "वन", "0": "ज़ीरो",
           "9": "नाइन"}
_SPEAK_SUB = [
    (r"m\s*/\s*s\s*2|ms\s*[-–]\s*2|m\s*s\s*[-–]\s*2", "मीटर प्रति सेकंड स्क्वायर"),
    (r"\bS\.\s?I\.?(?=\s|$|\))|\bSI\b", "एस आई"), (r"\bpH\b", "पी एच"), (r"\bkWh\b|\bKWh\b", "किलोवाट घंटा"),
    (r"\bHz\b", "हर्ट्ज़"), (r"\bkHz\b", "किलोहर्ट्ज़"), (r"Ω|\bohm\b", "ओम"), (r"°\s?C\b", "डिग्री सेल्सियस"),
    (r"\bkg\b", "किलोग्राम"), (r"\bcm\b", "सेंटीमीटर"), (r"\bmm\b", "मिलीमीटर"), (r"\bkm\b", "किलोमीटर"),
    (r"\bDNA\b", "डी एन ए"), (r"\bRNA\b", "आर एन ए"), (r"\bATP\b", "ए टी पी"), (r"\bHIV\b", "एच आई वी"),
    (r"\bAIDS\b", "एड्स"), (r"\bLPG\b", "एल पी जी"), (r"\bCNG\b", "सी एन जी"), (r"\bRBC\b", "आर बी सी"),
    (r"\bWBC\b", "डब्ल्यू बी सी"), (r"%", " प्रतिशत"), (r"×", " गुणा "), (r"(?<=\d)\s*/\s*(?=\d)", " बटा "),
    (r"\s*/\s*", " प्रति "), (r"\s*=\s*", " बराबर "), (r"\s\+\s", " और "), (r"____+", " खाली स्थान "),
    (r"[()\[\]'\"‘’“”]", " "), (r"\s[-–]\s", ", "), (r"\.\.\.+", ", "),
]


def _spell_formula(tok):
    out = []
    for el, num in re.findall(r"([A-Z][a-z]?)(\d*)", tok):
        out.append(" ".join(_LETTER_HI.get(ch.upper(), ch) for ch in el))
        if num:
            out.append(" ".join(_NUM_HI.get(c, c) for c in num))
    return " ".join(out)


def to_speech(text):
    t = " " + clean_text(text) + " "
    # Hindi ke baad bracket me English gloss (Magnification) / (SI) - bolna nahi
    t = re.sub(r"(?<=[\u0900-\u097F.])\s*\(([A-Za-z][A-Za-z .,/\-']*)\)", " ", t)
    t = re.sub(r"\.\s*।", "।", t)
    for pat, rep in _SPEAK_SUB:
        t = re.sub(pat, rep, t)
    # chemical formula / akele angrezi akshar -> naam se
    t = re.sub(r"(?<![A-Za-z])((?:[A-Z][a-z]?\d*){1,5})(?![A-Za-z])",
               lambda m: _spell_formula(m.group(1)) if (re.search(r"\d", m.group(1)) or len(m.group(1)) <= 3)
               else m.group(1), t)
    t = t.replace("!", "।")
    return " ".join(t.split())


# ============================== SAWAL -> REEL DATA ==============================

_BAD_EXP = ("व्याख्या देखें", "उपर्युक्त", "प्रश्नानुसार", "हम जानते")


def first_clean_sentence(exp, question=""):
    """Book ki vyakhya se ek saaf line - jo sawal ko hi na dohraye (naya gyaan de)."""
    qw = set(re.findall(r"[\u0900-\u097F]{2,}", question))
    cands = []
    for s in re.split(r"(?<=[।?])\s+", exp or ""):
        s = clean_text(s)
        if (8 <= len(s.split()) <= 26 and not any(b in s for b in _BAD_EXP) and not re.search(r"[=×→⇒∴]", s)
                and len(re.findall(r"[\u0900-\u097F]", s)) > 0.6 * len(s.replace(" ", ""))):
            sw = re.findall(r"[\u0900-\u097F]{2,}", s)
            overlap = sum(1 for w in sw if w in qw) / max(1, len(sw))
            cands.append((overlap, s.rstrip("।") + "।"))
    for ov, s in cands:
        if ov < 0.55:
            return s
    return cands[0][1] if cands else ""


def short_topic(q):
    return SUBJECT_STYLE.get(q["subject"], ("SCIENCE",))[0].split("•")[-1].strip()


def exam_tags(q):
    yrs = q.get("years") or []
    return [f"RRB Group D {y}" for y in yrs] or ["RRB Group D"]


def hook_line(q, ep):
    n = int(q.get("times_asked") or 1)
    yrs = q.get("years") or []
    y = yrs[-1] if yrs else ""
    if n >= 2:
        return f"ये सवाल {n} बार पूछा जा चुका है!"
    lines = [
        f"Railway {y} में पूछा गया सवाल!".replace("  ", " "),
        "Science PYQ: 3 सेकंड में बताओ!",
        "SSC, Railway, State: सबमें आता है ऐसा सवाल!",
        "सिर्फ एक सही है, आप कौन चुनोगे?",
    ]
    return lines[ep % len(lines)]


def prepare_data(q, ai, ep, next_q=None):
    rnd = random.Random(q["id"])
    opts = {k: clean_text((ai or {}).get("options", {}).get(k) or q["options"][k]) for k in "abcd"}
    question = clean_text((ai or {}).get("question") or q["question"])
    correct = q["answer"].upper()
    letters = ["A", "B", "C", "D"]
    options = [(L, opts[L.lower()]) for L in letters]
    correct_text = opts[q["answer"]]
    wrong = [L for L in letters if L != correct]
    decoy = rnd.choice(wrong)
    pair = [correct_text, opts[decoy.lower()]]
    rnd.shuffle(pair)
    elim = wrong[:]
    rnd.shuffle(elim)
    elim.remove(decoy)
    elim.append(decoy)              # jo VS me tha wo sabse aakhir me katega (suspense)
    why = clean_text((ai or {}).get("why") or "") or first_clean_sentence(q.get("explanation", ""), q["question"])
    if not why:
        why = f"सही उत्तर है: {correct_text.rstrip('.')}।"
    tip = clean_text((ai or {}).get("tip") or "")
    topic = clean_text((ai or {}).get("topic") or "") or short_topic(q)
    en_q = clean_text((ai or {}).get("en_question") or "")
    en_opt = {L: clean_text(((ai or {}).get("en_options") or {}).get(L.lower(), "")) for L in letters}
    if not all(en_opt.values()):
        en_opt = {}
    data = {
        "id": q["id"], "seq": q["seq"], "episode": ep, "subject": q["subject"],
        "question": question, "options": options, "correct": correct, "correct_text": correct_text,
        "vs_pair": pair, "elim_order": elim, "why": why, "tip": tip, "topic": topic,
        "times_asked": int(q.get("times_asked") or 1), "exams": exam_tags(q),
        "hook": hook_line(q, ep), "en_question": en_q if len(en_q.split()) <= 24 else "", "en_opt": en_opt,
        "speak_q": clean_text((ai or {}).get("speak_question") or "") or to_speech(question),
        "speak_ans": clean_text((ai or {}).get("speak_answer") or "") or to_speech(correct_text),
        "teaser": clean_text(next_q["question"]) if next_q else "",
        "ai": bool(ai),
    }
    return data


# ============================== SCENE SPECS + AWAAZ ==============================

def build_scene_specs(data):
    """segs = [(key, screen_text, bolne_ka_text)]."""
    ans_say = f"सही जवाब, {data['correct']}! {data['speak_ans']}।"
    why_say = to_speech(data["why"]) if not data.get("ai") else data["why"]
    specs = [
        {"name": "hook", "mood": "red", "tail": 0.25, "min": 2.6,
         "segs": [("hk", data["hook"], to_speech(data["hook"])), ("q", data["question"], data["speak_q"])]},
        {"name": "question", "mood": "blue", "tail": 0.0, "min": 0,
         "segs": [("lock", "जवाब कमेंट करो!", "जवाब कमेंट करो!")]},
        {"name": "verdict", "mood": "green", "tail": 0.45, "min": 2.4, "delay": 0.95,
         "segs": [("rev", ans_say, ans_say)]},
        {"name": "why", "mood": "blue", "tail": 0.5, "min": 3.2,
         "segs": [("wx", "क्योंकि,", "क्योंकि,"), ("why", data["why"], why_say)]
                 + ([("tip", data["tip"], to_speech("याद रखो, " + data["tip"]))] if data.get("tip") else []),
         "read": [("why", data["why"])]},
        {"name": "cta", "mood": "purple", "tail": 1.2, "min": 3.2,
         "segs": [("cta", f"ऐसे Science PYQ रोज़! {BRAND} को फॉलो करो!",
                   f"ऐसे ही साइंस के PYQ रोज़ आएंगे, {BRAND_SPEAK} को फॉलो और सेव कर लो!")]},
    ]
    return specs


async def _tts_async(text, path):
    import edge_tts
    last = None
    for attempt in range(4):
        try:
            try:
                com = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate=VOICE_RATE, pitch=VOICE_PITCH,
                                           boundary="WordBoundary")
            except TypeError:
                com = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate=VOICE_RATE, pitch=VOICE_PITCH)
            words = []
            with open(path, "wb") as f:
                async for chunk in com.stream():
                    if chunk.get("type") == "audio":
                        f.write(chunk["data"])
                    elif chunk.get("type") == "WordBoundary":
                        st = chunk["offset"] / 1e7
                        words.append((st, st + chunk["duration"] / 1e7, chunk.get("text", "")))
            if os.path.getsize(path) > 1000:
                return words
        except Exception as exc:
            last = exc
        await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TTS fail: {last}")


def decode_raw(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if len(arr) < SR * 0.2:
        raise RuntimeError("Voice file khali")
    return arr


def tighten_voice(arr, words, max_pause=MAX_PAUSE):
    """Lambi chuppi kaat do (TTS full-stop pe 0.5s rukta hai) aur word timing usi hisaab se."""
    if not words:
        return arr, words
    words = sorted(words)
    keep, new_words, out_t = [], [], 0.0
    cur = max(0.0, words[0][0] - 0.03)
    for i, (ws, we, wt) in enumerate(words):
        if i > 0:
            prev_end = max(words[i - 1][1], cur)
            if ws - prev_end > max_pause:
                keep.append((cur, prev_end + max_pause / 2))
                out_t += prev_end + max_pause / 2 - cur
                cur = ws - max_pause / 2
        new_words.append((out_t + (ws - cur), out_t + (we - cur), wt))
    keep.append((cur, min(len(arr) / SR, words[-1][1] + 0.12)))
    fade = int(0.006 * SR)
    pieces = []
    for a, b in keep:
        seg = arr[int(a * SR):int(b * SR)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
        pieces.append(seg)
    return (np.concatenate(pieces) if pieces else arr).astype(np.float32), new_words


def _fake_voice(text):
    """DRY_RUN: internet nahi -> andaze se lambai (silent) + word timing."""
    words = text.split()
    dur = 0.25 + len(words) / 2.9
    th = word_thresholds(words)
    wl = [(dur * a, dur * a + 0.2, w) for a, w in zip(th, words)]
    return np.zeros(int(dur * SR), dtype=np.float32), wl


def make_voices(specs):
    out = []
    for i, sp in enumerate(specs):
        speech = " ".join(s for _, _, s in sp["segs"])
        if DRY_RUN:
            arr, words = _fake_voice(speech)
        else:
            path = f"_voice_{i}.mp3"
            words = asyncio.run(_tts_async(speech, path))
            arr = decode_raw(path)
            os.remove(path)
            arr, words = tighten_voice(arr, words)
        out.append((arr, words, speech))
    return out


def seg_word_times(sp, words, speech, vdur):
    """
    Har seg ke screen-shabdon ka samay. Bolne ka text screen text se alag ho sakta hai -> seg ke andar
    anupaat se baanto (shabd-sankhya barabar ho to seedha).
    """
    spans, pos = [], 0
    for key, _disp, say in sp["segs"]:
        a = speech.find(say, pos)
        a = pos if a < 0 else a
        spans.append((key, a, a + len(say)))
        pos = a + len(say)
    # har boundary ka char-position
    bpos, ptr = [], 0
    for st, en, wtxt in words or []:
        wtxt = (wtxt or "").strip()
        if not wtxt:
            continue
        k = speech.find(wtxt, ptr)
        if k < 0:
            continue
        ptr = k + len(wtxt)
        bpos.append((k, st, en))
    marks, wt = {}, {}
    for (key, a, b), (_, disp, say) in zip(spans, sp["segs"]):
        inside = [(st, en) for k, st, en in bpos if a <= k < b]
        if inside:
            s0, s1 = inside[0][0], inside[-1][1]
        else:
            s0, s1 = None, None
        marks[key] = [s0, s1, inside]
    # khaali seg: padosi se andaza
    keys = [k for k, _, _ in sp["segs"]]
    for i, k in enumerate(keys):
        if marks[k][0] is None:
            prev_end = next((marks[keys[j]][1] for j in range(i - 1, -1, -1) if marks[keys[j]][1] is not None), 0.0)
            nxt = next((marks[keys[j]][0] for j in range(i + 1, len(keys)) if marks[keys[j]][0] is not None), vdur)
            marks[k][0], marks[k][1] = prev_end, nxt
    out_marks = {}
    for i, k in enumerate(keys):
        s0, s1, inside = marks[k]
        nxt = marks[keys[i + 1]][0] if i + 1 < len(keys) else max(vdur, s1)
        out_marks[k] = (s0, max(s1, nxt if nxt is not None else s1))
        disp = sp["segs"][i][1].split()
        if inside and len(inside) == len(disp):
            wt[k] = [x for x, _ in inside]
        else:
            th = word_thresholds(disp) if disp else []
            wt[k] = [s0 + (s1 - s0) * x for x in th]
    return out_marks, wt


def seg_progress(sc, key, t):
    s0, s1 = sc["marks"][key]
    span = max(0.1, s1 - s0)
    th = [clamp((w - EYE_LEAD - s0) / span) for w in sc["wt"][key]]
    return clamp((t - s0 + EYE_LEAD) / span), th


VERDICT_X = [0.12, 0.42, 0.72]      # galat options kab katenge (verdict scene me)
VERDICT_WIN = 1.0                   # sahi kab chamkega


def build_timeline(specs, voices, data):
    timeline, cur = [], 0.0
    for i, (sp, (arr, words, speech)) in enumerate(zip(specs, voices)):
        lead = VOICE_LEAD + sp.get("delay", 0.0)
        vdur = len(arr) / SR + lead
        dur = max(vdur + sp["tail"], sp["min"])
        shifted = [(a + lead, b + lead, w) for a, b, w in words]
        marks, wt = seg_word_times(sp, shifted, speech, vdur)
        for key, text in sp.get("read", []):
            need = marks[key][0] + len(text.split()) / READ_WPS + 0.4
            dur = max(dur, min(need, vdur + 1.0))
        sc = {"index": i, "name": sp["name"], "mood": sp["mood"], "start": cur, "dur": dur, "vdur": vdur,
              "marks": marks, "wt": wt, "lead": lead}
        if sp["name"] == "question":
            sc["cd_start"] = 0.45
            sc["dur"] = dur = max(dur, sc["cd_start"] + COUNTDOWN_SECONDS * COUNTDOWN_STEP + 0.25)
        timeline.append(sc)
        cur += dur
    return timeline, cur


# ============================== AUDIO: SFX + MUSIC (code se bana, copyright-free) ==============================

def _t(d):
    return np.arange(int(d * SR)) / SR


def sfx_whoosh(d=0.35, amp=0.35):
    rng = np.random.default_rng(1)
    n = rng.normal(0, 1, int(d * SR)).astype(np.float32)
    k = 0.02 + 0.25 * np.sin(np.pi * np.arange(len(n)) / len(n))
    out = np.zeros_like(n)
    y = 0.0
    for i in range(len(n)):
        y += k[i] * (n[i] - y)
        out[i] = y
    return out * np.sin(np.linspace(0, math.pi, len(n))) ** 2 * amp * 2.2


def sfx_pop(amp=0.4):
    t = _t(0.09)
    return np.sin(2 * math.pi * np.cumsum(900 - 5000 * t) / SR) * np.exp(-t * 40) * amp


def sfx_tick(amp=0.35):
    t = _t(0.04)
    return np.sin(2 * math.pi * 2200 * t) * np.exp(-t * 120) * amp


def sfx_buzz(amp=0.3):
    t = _t(0.28)
    return (np.sign(np.sin(2 * math.pi * 110 * t)) * 0.6 + np.sin(2 * math.pi * 55 * t) * 0.4) * np.exp(-t * 6) * amp


def sfx_ding(amp=0.4):
    t = _t(1.1)
    s = np.sin(2 * math.pi * 1318.5 * t) + 0.6 * np.sin(2 * math.pi * 1975.5 * t) + 0.3 * np.sin(2 * math.pi * 2637 * t)
    return s * np.exp(-t * 4.5) * amp / 1.9


def sfx_thud(amp=0.7):
    t = _t(0.45)
    s = np.sin(2 * math.pi * np.cumsum(90 - 60 * t) / SR) * np.exp(-t * 9)
    s[:600] += np.random.default_rng(2).normal(0, 0.5, 600) * np.exp(-np.arange(600) / 120)
    return s * amp


def sfx_riser(d=0.9, amp=0.18):
    t = _t(d)
    s = np.sin(2 * math.pi * np.cumsum(200 + 700 * (t / d) ** 2) / SR) * 0.6 + np.random.default_rng(4).normal(0, 0.25, len(t))
    return s * (t / d) ** 2 * amp


def sfx_heartbeat(amp=0.45):
    b = sfx_thud(amp)
    out = np.zeros(int(0.5 * SR))
    out[:len(b)] += b[:len(out)]
    s = int(0.18 * SR)
    n2 = min(len(b), len(out) - s)
    out[s:s + n2] += b[:n2] * 0.7
    return out


def music_bed(total):
    t = np.arange(int(total * SR)) / SR
    chord = [110.0, 164.81, 220.0, 261.63]
    pad = sum(np.sin(2 * math.pi * f * t + i) for i, f in enumerate(chord)) / len(chord)
    lfo = 0.6 + 0.4 * np.sin(2 * math.pi * 0.25 * t)
    pulse = np.sin(2 * math.pi * 55 * t) * np.exp(-((t % 0.5) * 14))
    return (pad * lfo * 0.05 + pulse * 0.05).astype(np.float32)


def add_at(buf, clip, t_sec, gain=1.0):
    s = int(t_sec * SR)
    if s >= len(buf) or s < 0:
        return
    e = min(len(buf), s + len(clip))
    buf[s:e] += (np.asarray(clip[:e - s]) * gain).astype(np.float32)


def build_audio(voices, timeline, total, out_path):
    n = int(total * SR) + SR
    buf = np.zeros(n, dtype=np.float32)
    vt = np.zeros(n, dtype=np.float32)
    for sc, (arr, _, _) in zip(timeline, voices):
        add_at(vt, arr, sc["start"] + sc["lead"])
    env = np.convolve(np.abs(vt), np.ones(int(0.15 * SR), dtype=np.float32) / int(0.15 * SR), mode="same")
    duck = 1.0 - np.clip(env * 6, 0, 0.6)
    bed = music_bed(n / SR)
    m = min(len(bed), n)
    buf[:m] += bed[:m] * duck[:m]
    for sc in timeline:
        s, name = sc["start"], sc["name"]
        if sc["index"] > 0 and name not in SEAMLESS:
            add_at(buf, sfx_whoosh(), max(0.0, s - 0.14), 0.9)
        if name == "hook":
            add_at(buf, sfx_thud(0.8), s)
            add_at(buf, sfx_pop(0.45), s + 0.08)
            add_at(buf, sfx_thud(0.7), s + STAMP_T)
        elif name == "question":
            add_at(buf, sfx_whoosh(0.25, 0.3), s)
            for k in range(COUNTDOWN_SECONDS):
                add_at(buf, sfx_tick(0.5), s + sc["cd_start"] + k * COUNTDOWN_STEP)
                add_at(buf, sfx_heartbeat(0.45), s + sc["cd_start"] + k * COUNTDOWN_STEP)
        elif name == "verdict":
            add_at(buf, sfx_riser(0.9, 0.2), s)
            for xt in VERDICT_X:
                add_at(buf, sfx_buzz(0.33), s + xt)
            add_at(buf, sfx_ding(0.5), s + VERDICT_WIN)
            add_at(buf, sfx_thud(0.6), s + VERDICT_WIN)
        elif name == "why":
            add_at(buf, sfx_pop(0.35), s + 0.05)
            if "tip" in sc["marks"]:
                add_at(buf, sfx_ding(0.3), s + sc["marks"]["tip"][0])
            for k in range(3):
                add_at(buf, sfx_pop(0.3), s + exam_tick_t(sc, k))
        elif name == "cta":
            add_at(buf, sfx_pop(0.4), s + 0.05)
            add_at(buf, sfx_pop(0.45), s + 0.7)
    buf += vt
    buf = buf[:int(total * SR)]
    peak = float(np.max(np.abs(buf))) if len(buf) else 1.0
    if peak > 0.95:
        buf = buf / peak * 0.95
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())


# ============================== OVERLAYS ==============================

STEPS = ["सवाल", "जवाब", "क्यों", "याद"]
STEPPER_Y = 1560
TILE_W, TILE_H = 470, 230
GRID_X = [W / 2 - 250, W / 2 + 250]
GRID_Y = [790, 1050]
VS_Y = 1185
STAMP_T = 0.3
SEAMLESS = ("question", "verdict")


@lru_cache(maxsize=8)
def brand_logo(size=120):
    """MinuteMe_GS logo: stopwatch (1 minute) ke andar 'M' + chalti minute ki sui."""
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = S / 2, S * 0.40
    cy = c + S * 0.05
    d.rounded_rectangle((c - S * 0.07, cy - r - S * 0.12, c + S * 0.07, cy - r + S * 0.02), radius=S // 40,
                        fill=YELLOW + (255,))
    d.line((c + r * 0.72, cy - r * 0.72, c + r * 0.86, cy - r * 0.86), fill=YELLOW + (255,), width=S // 22)
    d.ellipse((c - r, cy - r, c + r, cy + r), fill=(12, 22, 44, 255), outline=YELLOW + (255,), width=S // 20)
    d.arc((c - r * 0.82, cy - r * 0.82, c + r * 0.82, cy + r * 0.82), -90, 30, fill=CYAN + (255,), width=S // 26)
    for k in range(12):
        a = math.radians(k * 30)
        r1, r2 = r * 0.86, r * (0.74 if k % 3 == 0 else 0.80)
        d.line((c + math.cos(a) * r1, cy + math.sin(a) * r1, c + math.cos(a) * r2, cy + math.sin(a) * r2),
               fill=(160, 180, 210, 255), width=S // 60)
    d.text((c, cy + S * 0.02), "M", font=get_font(int(S * 0.42)), fill=WHITE + (255,), anchor="mm")
    return im.resize((size, size), Image.LANCZOS)


@lru_cache(maxsize=4)
def brand_wordmark(size=34):
    f = get_font(size)
    a, b = "MinuteMe", "_GS"
    w = int(text_w(a, f) + text_w(b, f)) + 4
    im = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, im.height / 2), a, font=f, fill=WHITE + (255,), anchor="lm")
    d.text((text_w(a, f) + 2, im.height / 2), b, font=f, fill=YELLOW + (255,), anchor="lm")
    return im


@lru_cache(maxsize=32)
def series_banner(ep):
    top = f"{SERIES}  ·  EP {ep}"
    f1, f2 = get_font(50), get_font(32)   # brand header me (logo + MinuteMe_GS) hamesha upar
    w = int(max(text_w(top, f1), text_w(EXAMS_LINE, f2))) + 110
    h = 160
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 96), radius=24, fill=RED + (255,), outline=(255, 150, 150, 255), width=3)
    d.text((w / 2, 50), top, font=f1, fill=WHITE + (255,), anchor="mm")
    d.rounded_rectangle((30, 104, w - 31, h - 1), radius=26, fill=(40, 32, 8, 240), outline=YELLOW + (255,), width=2)
    d.text((w / 2, 132), EXAMS_LINE, font=f2, fill=YELLOW + (255,), anchor="mm")
    return im


def draw_header(cv, data, gt, total, name):
    d = ImageDraw.Draw(cv)
    hy = 150                                    # Instagram ka upar wala UI ~150px dhakta hai
    place(cv, brand_logo(58), 60 + 29, hy)
    wm = brand_wordmark(32)
    place(cv, wm, 60 + 66 + wm.width / 2, hy)
    d = ImageDraw.Draw(cv)
    bx = 60 + 66 + wm.width + 14
    ft = get_font(24)
    tag = "SCIENCE PYQ"
    tw_ = text_w(tag, ft) + 28
    d.rounded_rectangle((bx, hy - 19, bx + tw_, hy + 19), radius=19, fill=(22, 101, 52), outline=GREEN, width=2)
    d.text((bx + tw_ / 2, hy + 1), tag, font=ft, fill=WHITE, anchor="mm")
    lab, col = SUBJECT_STYLE.get(data["subject"], ("SCIENCE", CYAN))
    chip = pill_sprite(lab.split("•")[0].strip() + f"  |  EP {data['episode']}", 24, col, (14, 26, 44), col)
    place(cv, chip, W - 130 - chip.width / 2, hy)
    x0, x1, y = 60, W - 60, hy + 48
    d.rounded_rectangle((x0, y, x1, y + 10), radius=5, fill=(27, 42, 58))
    cur = x0 + (x1 - x0) * clamp(gt / total)
    d.rounded_rectangle((x0, y, max(x0 + 10, cur), y + 10), radius=5, fill=CYAN)
    place(cv, glow_sprite(22, CYAN, 200), cur, y + 5)


def step_of(name):
    return {"hook": 0, "question": 0, "verdict": 1, "why": 2, "cta": 3}.get(name, -1)


def draw_stepper(cv, step, t):
    if step < 0:
        return
    n = len(STEPS)
    x0, x1 = 120, W - 120
    xs = [x0 + (x1 - x0) * k / (n - 1) for k in range(n)]
    d = ImageDraw.Draw(cv)
    d.line((x0, STEPPER_Y, x1, STEPPER_Y), fill=(45, 60, 85), width=4)
    d.line((x0, STEPPER_Y, xs[step], STEPPER_Y), fill=GREEN, width=4)
    f = get_font(26)
    for k, x in enumerate(xs):
        if k < step:
            col, r, tcol = GREEN, 16, (150, 220, 170)
        elif k == step:
            col, r, tcol = YELLOW, 22 + 3 * math.sin(t * 8), YELLOW
        else:
            col, r, tcol = (70, 90, 120), 14, (120, 135, 160)
        d.ellipse((x - r, STEPPER_Y - r, x + r, STEPPER_Y + r), fill=col)
        d.text((x, STEPPER_Y + 48), STEPS[k], font=f, fill=tcol, anchor="mm")


@lru_cache(maxsize=96)
def tile_sprite(letter, text, en, state, w=TILE_W, h=TILE_H):
    styles = {
        "normal": ((22, 42, 72), (70, 110, 160), 4, CYAN, WHITE),
        "active": ((28, 58, 96), CYAN, 7, CYAN, WHITE),
        "vs": ((26, 48, 84), (110, 150, 205), 5, YELLOW, WHITE),
        "wrong": ((40, 18, 26), RED, 5, RED, MUTED),
        "correct": ((14, 60, 36), GREEN, 8, GREEN, WHITE),
    }
    fill, outline, width, badge, tcol = styles[state]
    im = card_sprite(w, h, fill, outline, width, 34).copy()
    d = ImageDraw.Draw(im)
    pad, br = 30, 30
    bx, by = pad + 22 + br, pad + 22 + br
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=badge + (255,))
    d.text((bx, by), letter, font=get_font(36), fill=(8, 16, 30, 255), anchor="mm")
    maxw = w - 110
    f, s_, lines = fit_lines(text, maxw, 3, 58, 30)
    lines = lines[:3]
    lh = int(s_ * 1.18)
    enh = 38 if en else 0
    y0 = pad + h / 2 + 16 - (lh * len(lines) + enh) / 2 + lh / 2
    for k, ln in enumerate(lines):
        d.text((pad + w / 2, y0 + k * lh), " ".join(ln), font=f, fill=tcol + (255,), anchor="mm")
    if en:
        fe, se, le = fit_lines(en, maxw, 1, 28, 18, reg=True)
        d.text((pad + w / 2, y0 + len(lines) * lh - lh / 2 + 22), " ".join(le[0]) if le else "", font=fe,
               fill=(EN_COL if state != "wrong" else MUTED) + (255,), anchor="mm")
    if state == "wrong":
        yy = y0 + (len(lines) - 1) * lh / 2
        tw = max(text_w(" ".join(l), f) for l in lines) if lines else 0
        d.line((pad + w / 2 - tw / 2 - 10, yy, pad + w / 2 + tw / 2 + 10, yy), fill=RED + (230,), width=7)
    return im


def grid_pos(i):
    return GRID_X[i % 2], GRID_Y[i // 2]


def draw_grid(cv, data, states, offs=None, scl=None, alp=None):
    offs, scl, alp = offs or {}, scl or {}, alp or {}
    for i, (l, txt) in enumerate(data["options"]):
        st = states.get(l)
        if not st:
            continue
        x, y = grid_pos(i)
        dx, dy = offs.get(l, (0, 0))
        place(cv, tile_sprite(l, txt, data["en_opt"].get(l, ""), st), x + dx, y + dy, scale=scl.get(l, 1.0),
              alpha=alp.get(l, 1.0))


def q_size(question, cap=64):
    for sz in (64, 60, 56, 52, 48, 46, 44):
        if sz > cap:
            continue
        _, s2, ls = fit_lines(question, 960, 4, sz, sz)
        if len(ls) <= 4 and int(s2 * 1.28) * len(ls) <= 330:
            return sz
    return 42


# ============================== SCENES ==============================

def scene_hook(cv, data, t, sc):
    """Frame 0: SCIENCE PYQ (Railway•SSC•State) + kab poochha + asli sawal + 2 jawab taraazu pe."""
    fx = {}
    place(cv, series_banner(data["episode"]), W / 2, 300, scale=0.86 + 0.06 * ease_out_back(prog(t, 0, 0.3)))
    # hook line (peeli, badi)
    hl = data["hook"]
    f, s_, lines = fit_lines(hl, 960, 2, 66, 44)
    lh = int(s_ * 1.22)
    lay = Image.new("RGBA", (1000, lh * len(lines) + 30), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    for k, ln in enumerate(lines):
        dl.text((500, 15 + lh * k + lh / 2), " ".join(ln), font=f, fill=YELLOW + (255,), anchor="mm",
                stroke_width=6, stroke_fill=(5, 10, 22, 255))
    hy = 455 + lh * (len(lines) - 1) / 2
    place(cv, lay, W / 2, hy, scale=1 + 0.02 * math.sin(t * 8))
    # exam chips: RRB Group D 2018 / 2022 (+ kitni baar)
    chips = [pill_sprite(e, 28, WHITE, (30, 45, 80), (90, 120, 180)) for e in data["exams"][:2]]
    if data.get("ai") and data.get("topic") and len(data["topic"]) <= 22:
        chips.insert(0, pill_sprite(data["topic"], 28, (10, 30, 50), CYAN, CYAN))
    if data["times_asked"] >= 2:
        chips.append(pill_sprite(f"{data['times_asked']} बार पूछा गया", 28, (30, 18, 0), YELLOW, ORANGE))
    cy_ = hy + lh * len(lines) / 2 + 42
    tot = sum(c.width for c in chips) + 16 * (len(chips) - 1)
    x = W / 2 - tot / 2
    for i, c in enumerate(chips):
        kc = ease_out_back(prog(t, 0.1 + 0.08 * i, 0.3))
        place(cv, c, x + c.width / 2, cy_, scale=max(0.05, kc))
        x += c.width + 16
    # sawal (awaaz ke saath)
    sz = q_size(data["question"])
    qp, th = seg_progress(sc, "q", t)
    qc = 600 + (1185 - TILE_H / 2 - 600) / 2 + 20
    yb = draw_kinetic(cv, data["question"], W / 2, 960, sz, qp, max_lines=4, min_size=40, line_h=1.28,
                      center_y=qc, ghost=1.0, th=th, hl_words=q_highlights(data["question"]), hl_color=CYAN)
    # PYQ stamp
    if t >= STAMP_T:
        kk = prog(t, STAMP_T, 0.16)
        place(cv, stamp_sprite(), W - 150, VS_Y - TILE_H / 2 - 30, scale=(1.9 - 0.9 * ease_out_cubic(kk)) * 0.48, angle=-11,
              alpha=clamp(kk * 3))
        if t < STAMP_T + 0.3:
            fx["shake"] = 10 * (1 - prog(t, STAMP_T + 0.04, 0.26))
    # 2 jawab taraazu pe (jhoolte) + beech me palatta sikka
    pair = data["vs_pair"]
    letter = {txt: l for l, txt in data["options"]}
    ang = 7.0 * math.sin(t * 3.3) * (1 - 0.25 * math.exp(-t * 2))
    rad = math.radians(ang)
    half = (GRID_X[1] - GRID_X[0]) / 2
    piv_y = VS_Y + TILE_H / 2 + 46
    heavy = 0 if ang > 0 else 1
    d = ImageDraw.Draw(cv)
    L = half * 1.18
    d.line((W / 2 - L * math.cos(rad), piv_y + L * math.sin(rad), W / 2 + L * math.cos(rad), piv_y - L * math.sin(rad)),
           fill=(255, 205, 60), width=12)
    d.polygon([(W / 2, piv_y - 6), (W / 2 - 46, piv_y + 70), (W / 2 + 46, piv_y + 70)], fill=(200, 150, 30))
    for side, txt in enumerate(pair):
        l = letter.get(txt, "?")
        sgn = -1 if side == 0 else 1
        x = W / 2 + sgn * half * math.cos(rad)
        y = VS_Y - sgn * half * math.sin(rad)
        is_heavy = side == heavy and abs(ang) > 2.5
        place(cv, tile_sprite(l, txt, data["en_opt"].get(l, ""), "active" if is_heavy else "vs"), x, y,
              scale=1.04 if is_heavy else 0.98, angle=ang * 0.6)
        sheen(cv, x, y, TILE_W, TILE_H, t, period=1.6, offset=0.35 * side)
    faces = [pill_sprite("?", 54, WHITE, (70, 40, 140), PURPLE),
             pill_sprite(letter.get(pair[0], "?"), 54, (30, 18, 0), YELLOW, ORANGE),
             pill_sprite("?", 54, WHITE, (70, 40, 140), PURPLE),
             pill_sprite(letter.get(pair[1], "?"), 54, (30, 18, 0), YELLOW, ORANGE)]
    cyc = t / 0.42
    i_ = int(cyc) % 4
    place(cv, glow_sprite(110, YELLOW, 150), W / 2, piv_y + 36)
    place_flip(cv, faces[i_], faces[(i_ + 1) % 4], W / 2, piv_y + 36, cyc - int(cyc))
    kc = ease_out_back(prog(t, 0.7, 0.3)) if t >= 0.7 else 0.0
    if kc > 0.01:
        place(cv, pill_sprite("आपका जवाब? कमेंट करो!", 40, (30, 20, 0), YELLOW, ORANGE), W / 2, 1470,
              scale=max(0.05, kc) * (1 + 0.03 * math.sin(t * 9)))
    return fx


def scene_grid(cv, data, t, sc):
    """VS ke 2 card apni jagah, baaki 2 girte hain -> 2x2 + 3-2-1."""
    fx = {}
    pair = data["vs_pair"]
    e = ease_in_out(prog(t, 0.0, 0.35))
    big = q_size(data["question"])
    qc0 = 600 + (1185 - TILE_H / 2 - 600) / 2 + 20
    draw_kinetic(cv, data["question"], W / 2, 960 - 40 * e, int(big + (min(big, 50) - big) * e), 1.0, max_lines=4,
                 min_size=36, karaoke=False, line_h=1.26, center_y=qc0 + (470 - qc0) * e,
                 hl_words=q_highlights(data["question"]), hl_color=CYAN)
    if data.get("en_question") and e > 0.95:
        _, s_, ls = fit_lines(data["question"], 920, 4, min(big, 50), 36)
        draw_en(cv, data["en_question"], 470 + int(s_ * 1.26) * len(ls) / 2 + 6, max_w=900, size=30)
    offs, scl, alp, states = {}, {}, {}, {}
    c0 = sc["cd_start"]
    cd = COUNTDOWN_SECONDS * COUNTDOWN_STEP
    scan = min(3, int((t - c0) / (cd / 4))) if c0 <= t < c0 + cd else -1
    for i, (l, txt) in enumerate(data["options"]):
        gx, gy = grid_pos(i)
        states[l] = "active" if i == scan else "normal"
        if txt in pair:
            side = pair.index(txt)
            offs[l] = ((GRID_X[side] - gx) * (1 - e), (VS_Y - gy) * (1 - e))
        else:
            kd = ease_out_back(prog(t, 0.1 + 0.08 * i, 0.3))
            offs[l] = (0, -140 * (1 - kd))
            alp[l] = clamp(kd * 1.6)
            scl[l] = 0.85 + 0.15 * min(kd, 1.0)
    draw_grid(cv, data, states, offs, scl, alp)
    if t > 0.5:
        for i in range(4):
            gx_, gy_ = grid_pos(i)
            sheen(cv, gx_, gy_, TILE_W, TILE_H, t, period=1.8, offset=0.22 * i, strength=40)
    cx, cy = W / 2, (GRID_Y[0] + GRID_Y[1]) / 2
    if t >= c0 - 0.2:
        kin_ = ease_out_back(prog(t, c0 - 0.2, 0.25))
        r = 74 * max(0.05, kin_)
        place(cv, glow_sprite(170, PURPLE, 150), cx, cy)
        d = ImageDraw.Draw(cv)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(20, 16, 44), outline=(90, 80, 150), width=8)
        tt = t - c0
        if 0 <= tt < cd:
            d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * clamp(1 - tt / cd), fill=YELLOW, width=9)
            num = max(1, COUNTDOWN_SECONDS - int(tt / COUNTDOWN_STEP))
            frac = tt / COUNTDOWN_STEP - int(tt / COUNTDOWN_STEP)
            d.text((cx, cy), str(num), font=get_font(int(80 * (1.3 - 0.3 * ease_out_cubic(clamp(frac * 3))))),
                   fill=YELLOW, anchor="mm")
            if frac < 0.08 and tt > 0.05:
                fx["shake"] = 4
        elif tt >= cd:
            place(cv, lock_sprite(80), cx, cy)
    kc = ease_out_back(prog(t, 0.3, 0.3)) if t >= 0.3 else 0.0
    if kc > 0.01:
        place(cv, pill_sprite("अपना जवाब लॉक करो: A / B / C / D", 38, (30, 20, 0), YELLOW, ORANGE), W / 2, 1330,
              scale=max(0.05, kc))
    return fx


def scene_verdict(cv, data, t, sc):
    fx = {}
    xt = dict(zip(data["elim_order"], VERDICT_X))
    win = VERDICT_WIN
    ew = ease_in_out(prog(t, win, 0.4))
    a = 1 - clamp(ew * 3)
    if a > 0.02:
        draw_kinetic(cv, data["question"], W / 2, 920, min(q_size(data["question"]), 50), 1.0, max_lines=4,
                     min_size=36, karaoke=False, line_h=1.26, center_y=470, color=mix(BG_BOTTOM, WHITE, a))
    ci = next(i for i, (l, _) in enumerate(data["options"]) if l == data["correct"])
    gx, gy = grid_pos(ci)
    for i, (l, txt) in enumerate(data["options"]):
        if l == data["correct"]:
            continue
        x, y = grid_pos(i)
        eo = data["en_opt"].get(l, "")
        if t < xt[l]:
            place(cv, tile_sprite(l, txt, eo, "normal"), x, y)
            continue
        pf = prog(t, xt[l], 0.28)
        if pf < 1:
            place_flip(cv, tile_sprite(l, txt, eo, "normal"), tile_sprite(l, txt, eo, "wrong"), x, y, pf)
        else:
            al = (1 - 0.35 * prog(t, xt[l], 0.2)) * (1 - ew)
            place(cv, tile_sprite(l, txt, eo, "wrong"), x, y + 40 * ew, scale=0.94 - 0.2 * ew, alpha=al)
        if t - xt[l] < 0.08:
            fx["shake"] = 7
        if t >= xt[l] + 0.28 and ew < 0.9:
            kx = prog(t, xt[l] + 0.28, 0.2)
            place(cv, x_mark_sprite(90), x + TILE_W / 2 - 40, y - TILE_H / 2 + 40 + 40 * ew,
                  scale=max(0.05, 1.7 - 0.7 * ease_out_back(kx)), alpha=1 - ew)
    tx, ty = W / 2, 930
    x = gx + (tx - gx) * ew
    y = gy + (ty - gy) * ew
    if ew > 0.05:
        place(cv, rays_sprite(), x, y, angle=t * 30, scale=1.1 * ew)
        place(cv, glow_sprite(360, GREEN, int(150 * ew)), x, y)
    eo = data["en_opt"].get(data["correct"], "")
    st = "correct" if t >= win else ("active" if t >= VERDICT_X[-1] + 0.15 else "normal")
    hb = 1 + (0.04 * math.sin(t * 20) if VERDICT_X[-1] + 0.15 <= t < win else 0)
    if win <= t < win + 0.26:
        place_flip(cv, tile_sprite(data["correct"], data["correct_text"], eo, "active"),
                   tile_sprite(data["correct"], data["correct_text"], eo, "correct"), x, y, prog(t, win, 0.26),
                   scale=1 + 0.45 * ew)
    else:
        place(cv, tile_sprite(data["correct"], data["correct_text"], eo, st), x, y, scale=(1 + 0.45 * ew) * hb)
    if t >= win + 0.12:
        kk = ease_out_back(prog(t, win + 0.12, 0.3))
        place(cv, check_sprite(140), W / 2, 600, scale=max(0.05, kk))
        d = ImageDraw.Draw(cv)
        d.text((W / 2, 455), "सही जवाब", font=get_font(84), fill=GREEN, anchor="mm")
        if t < win + 0.1:
            fx["flash"] = 0.3 * (1 - (t - win) / 0.1)
        rng = random.Random(9)
        tt = t - win
        for _ in range(70):
            ang = rng.uniform(0, 2 * math.pi)
            sp = rng.uniform(500, 1300)
            col = rng.choice([GREEN, YELLOW, CYAN, WHITE, ORANGE])
            szz = rng.randint(10, 18)
            px = W / 2 + math.cos(ang) * sp * tt * 0.9
            py = ty + math.sin(ang) * sp * tt * 0.9 + 900 * tt * tt
            if 0 < px < W and 0 < py < H and tt < 1.6:
                d.rectangle((px, py, px + szz, py + szz * 0.6), fill=col)
    if VERDICT_X[-1] + 0.12 <= t < win:
        d = ImageDraw.Draw(cv)
        a_ = 0.6 + 0.4 * math.sin(t * 16)
        d.text((W / 2, 1300), "...और सही जवाब है", font=get_font(62), fill=mix(BG_BOTTOM, YELLOW, a_), anchor="mm",
               stroke_width=5, stroke_fill=(5, 10, 22))
    if t >= win + 0.45:
        k3 = ease_out_back(prog(t, win + 0.45, 0.3))
        place(cv, pill_sprite("आपका जवाब सही था? कमेंट करो!", 38, WHITE, (37, 60, 140), CYAN, reg=False),
              W / 2, 1300, scale=max(0.05, k3))
    return fx


EXAM_BADGES = [("RAILWAY", "RRB NTPC • Group D • ALP"), ("SSC", "GD • MTS • CGL • CHSL"), ("STATE", "Police • Patwari • TET")]


def exam_tick_t(sc, k):
    base = sc["marks"]["why"][1] if "why" in sc["marks"] else 1.0
    return min(sc["dur"] - 0.6, base + 0.15 + 0.22 * k)


@lru_cache(maxsize=8)
def exam_badge(name, sub, on):
    w, h = 300, 120
    im = card_sprite(w, h, (16, 52, 34) if on else (24, 34, 54), GREEN if on else (70, 90, 120), 4, 26).copy()
    d = ImageDraw.Draw(im)
    d.text((30 + w / 2, 30 + 44), ("✓ " if False else "") + name, font=get_font(40), fill=(WHITE if on else MUTED) + (255,),
           anchor="mm")
    d.text((30 + w / 2, 30 + 90), sub, font=get_font_reg(20), fill=((170, 230, 190) if on else (110, 125, 150)) + (255,),
           anchor="mm")
    return im


def scene_why(cv, data, t, sc):
    """'क्यों?' - science wajah (awaaz ke saath) + yaad-trick + ye topic kin exams me aata hai."""
    fx = {}
    m = sc["marks"]
    k = ease_out_back(prog(t, 0, 0.35))
    # upar: sahi jawab chhota recap
    place(cv, pill_sprite(f"सही जवाब: ({data['correct']}) {data['correct_text']}", 34, (5, 30, 15), GREEN, GREEN),
          W / 2, 300, scale=max(0.05, k))
    # wajah card (poora block screen ke beech: wajah + trick + exams)
    wh = text_block_h(data["why"], 860, 60, 4, 40) + 130
    tip_h = (text_block_h(data["tip"], 820, 52, 2, 36) + 90 + 40) if data.get("tip") else 0
    block = wh + 40 + tip_h + 230
    top = max(370, 370 + (1470 - 370 - block) / 2)
    wc = top + wh / 2
    place(cv, card_sprite(980, int(wh), (14, 44, 32), GREEN, 6, 44), W / 2, wc, scale=0.92 + 0.08 * k, alpha=clamp(k))
    place(cv, pill_sprite("क्यों?", 44, (5, 30, 15), GREEN, GREEN), W / 2, wc - wh / 2, scale=max(0.05, k))
    wp, th = seg_progress(sc, "why", t)
    draw_kinetic(cv, data["why"], W / 2, 860, 60, wp, max_lines=4, min_size=40, ghost=0.18, center_y=wc + 12, th=th,
                 hl_color=GREEN)
    y = wc + wh / 2 + 40
    # yaad-trick
    if data.get("tip") and "tip" in m:
        ts = m["tip"][0] - 0.1
        if t >= ts:
            kt = ease_out_back(prog(t, ts, 0.3))
            th_ = text_block_h(data["tip"], 820, 52, 2, 36) + 90
            place(cv, glow_sprite(300, YELLOW, 50), W / 2, y + th_ / 2)
            place(cv, card_sprite(940, int(th_), (46, 38, 10), YELLOW, 5, 36), W / 2, y + th_ / 2,
                  scale=max(0.05, 0.9 + 0.1 * kt), alpha=clamp(kt * 1.5))
            place(cv, pill_sprite("याद रखो", 34, (30, 20, 0), YELLOW, YELLOW), W / 2, y, scale=max(0.05, kt))
            tp, th2 = seg_progress(sc, "tip", t)
            draw_kinetic(cv, data["tip"], W / 2, 820, 52, max(tp, 0.001), max_lines=2, min_size=36, ghost=0.3,
                         center_y=y + th_ / 2 + 10, th=th2)
        y += text_block_h(data["tip"], 820, 52, 2, 36) + 90 + 40
    # exam badges (Railway / SSC / State) - ek-ek karke ✓
    y = y + 120
    d = ImageDraw.Draw(cv)
    t0 = exam_tick_t(sc, 0) - 0.3
    if t >= t0:
        ka = clamp(prog(t, t0, 0.3) * 1.5)
        d.text((W / 2, y - 92), "Science का ये टॉपिक इन सब exams में आता है", font=get_font(34),
               fill=mix(BG_BOTTOM, (210, 220, 240), ka), anchor="mm")
        for i, (nm, sub) in enumerate(EXAM_BADGES):
            ti = exam_tick_t(sc, i)
            on = t >= ti
            kb = ease_out_back(prog(t, ti - 0.25, 0.3)) if t >= ti - 0.25 else 0.0
            x = W / 2 + (i - 1) * 320
            if kb > 0.01:
                place(cv, exam_badge(nm, sub, on), x, y, scale=max(0.05, 0.85 + 0.15 * kb))
                if on:
                    kk = ease_out_back(prog(t, ti, 0.25))
                    place(cv, check_sprite(54), x + 140, y - 52, scale=max(0.05, kk))
    return fx


@lru_cache(maxsize=2)
def follow_button():
    top, bot = f"FOLLOW {BRAND_HANDLE}", "रोज़ नए Science PYQ"
    f1, f2 = get_font(54), get_font(36)
    w = int(max(text_w(top, f1), text_w(bot, f2))) + 140
    h = 180
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=36, fill=(220, 38, 38, 255), outline=(255, 200, 200, 255), width=5)
    d.text((w / 2, 62), top, font=f1, fill=WHITE + (255,), anchor="mm")
    d.rounded_rectangle((40, 104, w - 40, 162), radius=24, fill=(255, 196, 0, 255))
    d.text((w / 2, 133), bot, font=f2, fill=(40, 20, 0, 255), anchor="mm")
    return im


def scene_cta(cv, data, t, sc):
    k = ease_out_back(prog(t, 0, 0.35))
    # brand: logo + naam + tagline
    place(cv, glow_sprite(190, YELLOW, 80), W / 2, 400)
    place(cv, brand_logo(190), W / 2, 400 + 6 * math.sin(t * 3), scale=max(0.05, k), angle=3 * math.sin(t * 2))
    wm = brand_wordmark(64)
    place(cv, wm, W / 2, 540, scale=max(0.05, k))
    d = ImageDraw.Draw(cv)
    d.text((W / 2, 600), BRAND_TAGLINE, font=get_font(32), fill=mix(BG_BOTTOM, CYAN, clamp(k)), anchor="mm")
    teaser = data.get("teaser") or ""
    y = 660
    if teaser:
        kt = ease_out_cubic(prog(t, 0.15, 0.35))
        box_h = text_block_h(teaser, 840, 44, 3, 32) + 120
        place(cv, glow_sprite(280, PURPLE, int(60 + 40 * math.sin(t * 5))), W / 2, y + box_h / 2)
        place(cv, card_sprite(960, int(box_h), CARD, PURPLE, 4, 30), W / 2, y + box_h / 2, alpha=kt,
              scale=1 + 0.015 * math.sin(t * 5))
        d = ImageDraw.Draw(cv)
        d.text((W / 2, y + 40), "अगला PYQ (अगली रील में):", font=get_font(36), fill=YELLOW, anchor="mm")
        draw_kinetic(cv, teaser, W / 2, 840, 44, 1.0, max_lines=3, min_size=32, karaoke=False,
                     center_y=y + box_h / 2 + 22, color=mix(BG_BOTTOM, WHITE, kt))
        y += box_h + 60
    else:
        y += 160
    kf = ease_out_back(prog(t, 0.6, 0.3)) if t >= 0.6 else 0.0
    if kf > 0.01:
        place(cv, glow_sprite(300, RED, 90), W / 2, y + 90)
        place(cv, follow_button(), W / 2, y + 90, scale=max(0.05, kf) * (1 + 0.04 * math.sin(t * 8)))
    ks = ease_out_back(prog(t, 1.0, 0.3)) if t >= 1.0 else 0.0
    if ks > 0.01:
        place(cv, pill_sprite("सेव करो: Exam से पहले Revision", 36, WHITE, (37, 60, 140), CYAN), W / 2, y + 250,
              scale=max(0.05, ks))
        if WHATSAPP_NUMBER:
            place(cv, pill_sprite(f"Free Test / Notes: WhatsApp {WHATSAPP_NUMBER}", 32, WHITE, (6, 95, 70),
                                  (60, 200, 150)), W / 2, y + 345, scale=max(0.05, ks))
    return {}


SCENES = {"hook": scene_hook, "question": scene_grid, "verdict": scene_verdict, "why": scene_why, "cta": scene_cta}


# ============================== RENDER ==============================

def render_frame(sc, data, gt, total):
    t = gt - sc["start"]
    cv = bg_frame(sc["mood"], gt)
    fx = SCENES[sc["name"]](cv, data, t, sc) or {}
    draw_header(cv, data, gt, total, sc["name"])
    draw_stepper(cv, step_of(sc["name"]), t)
    z = 1.0
    if t < 0.2 and sc["name"] in ("why", "cta"):
        z *= 1 + 0.07 * (1 - ease_out_cubic(t / 0.2))
    if sc["name"] == "hook":
        z *= 1 + 0.03 * clamp(t / max(sc["dur"], 0.1))
    if sc["name"] == "why":
        z *= 1 + 0.02 * clamp(t / max(sc["dur"], 0.1))
    if z > 1.0005:
        nw, nh = int(W * z), int(H * z)
        big = cv.resize((nw, nh), Image.BILINEAR)
        ox, oy = (nw - W) // 2, (nh - H) // 2
        cv = big.crop((ox, oy, ox + W, oy + H))
    shake = fx.get("shake", 0) or 0
    if shake > 0.5:
        rng = random.Random(int(gt * 1000))
        s = int(shake)
        base = Image.new("RGB", (W, H), BG_TOP)
        base.paste(cv, (rng.randint(-s, s), rng.randint(-s, s)))
        cv = base
    flash = fx.get("flash", 0) or 0
    if flash > 0.01:
        cv = Image.blend(cv, Image.new("RGB", (W, H), (255, 255, 255)), clamp(flash))
    # watermark: video download/repost ho to bhi naam dikhe
    place(cv, watermark(), W / 2, 1652, alpha=0.55)
    return cv


@lru_cache(maxsize=1)
def watermark():
    lg = brand_logo(40)
    f = get_font(28)
    w = int(lg.width + 10 + text_w(BRAND_HANDLE, f)) + 4
    im = Image.new("RGBA", (w, 46), (0, 0, 0, 0))
    im.paste(lg, (0, 3), lg)
    ImageDraw.Draw(im).text((lg.width + 10, 23), BRAND_HANDLE, font=f, fill=WHITE + (255,), anchor="lm")
    return im


def iris(prev, cur, p, cx=W / 2, cy=H * 0.45):
    e = ease_in_out(clamp(p))
    r = (math.hypot(max(cx, W - cx), max(cy, H - cy)) + 20) * e
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)
    out = Image.blend(prev, Image.new("RGB", (W, H), BG_BOTTOM), 0.35 * e) if e < 1 else prev.copy()
    out.paste(cur, (0, 0), mask)
    if 0.02 < e < 0.98:
        d = ImageDraw.Draw(out)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=CYAN, width=6)
    return out


def build_reel(data, output_video, preview_dir=None):
    os.makedirs(os.path.dirname(output_video) or ".", exist_ok=True)
    resolve_font()
    specs = build_scene_specs(data)
    print("Awaaz ban rahi hai...")
    voices = make_voices(specs)
    timeline, total = build_timeline(specs, voices, data)
    print("  scene | shuru | lambai | awaaz")
    for sc in timeline:
        print(f"  {sc['name']:<9} {sc['start']:5.2f}s  {sc['dur']:4.2f}s  {sc['vdur']:4.2f}s")
    print(f"  KUL: {total:.1f}s")
    if preview_dir:
        os.makedirs(preview_dir, exist_ok=True)
        for sc in timeline:
            for frac in (0.15, 0.55, 0.95):
                gt = sc["start"] + sc["dur"] * frac
                render_frame(sc, data, gt, total).save(os.path.join(preview_dir, f"{sc['index']}_{sc['name']}_{int(frac*100)}.png"))
        print("Preview frames:", preview_dir)
        return total
    audio_path = "_master_audio.wav"
    build_audio(voices, timeline, total, audio_path)
    n_frames = int(math.ceil(total * FPS))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio_path, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium",
           "-crf", str(VIDEO_CRF), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
           "-movflags", "+faststart", output_video]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        si, cache = 0, {}
        for fi in range(n_frames):
            gt = fi / FPS
            while si + 1 < len(timeline) and gt >= timeline[si + 1]["start"]:
                si += 1
            sc = timeline[si]
            frame = render_frame(sc, data, gt, total)
            tt = gt - sc["start"]
            if si > 0 and tt < TRANSITION and sc["name"] not in SEAMLESS:
                if si not in cache:
                    cache = {k: v for k, v in cache.items() if k == "first"}
                    cache[si] = render_frame(timeline[si - 1], data, sc["start"] - 1.0 / FPS, total)
                frame = iris(cache[si], frame, tt / TRANSITION)
            if gt > total - LOOP_BLEND:                 # ant pehle frame me ghule -> Instagram loop seamless
                if "first" not in cache:
                    cache["first"] = render_frame(timeline[0], data, 0.0, total)
                q_ = clamp((gt - (total - LOOP_BLEND)) / LOOP_BLEND)
                dark = Image.new("RGB", (W, H), BG_BOTTOM)
                frame = Image.blend(frame, dark, q_ * 2) if q_ < 0.5 else Image.blend(dark, cache["first"], (q_ - 0.5) * 2)
            proc.stdin.write(frame.tobytes())
            if fi % 150 == 0:
                print(f"  frame {fi}/{n_frames}")
        proc.stdin.close()
    except BrokenPipeError:
        pass
    ret = proc.wait()
    if os.path.exists(audio_path):
        os.remove(audio_path)
    if ret != 0:
        raise RuntimeError("ffmpeg encoding fail")
    print(f"REEL TAIYAR: {output_video} ({total:.1f}s)")
    return total


# ============================== CAPTION ==============================

def make_caption(data):
    sub = data["subject"]
    yrs = ", ".join(data["exams"])
    asked = (f"📌 {yrs} में {data['times_asked']} बार पूछा गया ({sub})" if data["times_asked"] >= 2
             else f"📌 {yrs} में पूछा गया ({sub})")
    lines = [
        f"🔬 {BRAND} | {SERIES} EP {data['episode']} | {data['question']}",
        "",
        asked,
        "🎯 Railway (NTPC / Group D / ALP), SSC (GD / MTS / CGL / CHSL) और State exams - जहाँ भी Science है, ऐसे सवाल आते हैं।",
        "👀 सही जवाब और उसकी वजह रील में। अपना जवाब A / B / C / D कमेंट करो!",
        "📥 सेव कर लो - exam से पहले revision में काम आएगा।",
        f"🔔 Follow {BRAND_HANDLE} - रोज़ 1 मिनट में पक्का GS (Science PYQ)",
    ] + ([f"📲 Free test / notes: WhatsApp {WHATSAPP_NUMBER}"] if WHATSAPP_NUMBER else []) + [
        "",
        HASHTAGS,
    ]
    return "\n".join(lines)


# ============================== INSTAGRAM ==============================

def post_reel(video_file, caption):
    """Resumable upload -> status FINISHED -> publish. Fail = exception (progress aage nahi badhta)."""
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("IG secrets nahi - post skip (reel bani hai).")
        return None
    r = requests.post(f"{GRAPH}{IG_USER_ID}/media",
                      data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                            "share_to_feed": "true", "access_token": IG_ACCESS_TOKEN}, timeout=60).json()
    cid = r.get("id")
    if not cid:
        raise RuntimeError(f"IG container nahi bana: {r}")
    up_url = r.get("uri") or f"https://rupload.facebook.com/ig-api-upload/v21.0/{cid}"
    size = os.path.getsize(video_file)
    with open(video_file, "rb") as vf:
        up = requests.post(up_url, headers={"Authorization": f"OAuth {IG_ACCESS_TOKEN}", "offset": "0",
                                            "file_size": str(size), "Content-Type": "application/octet-stream"},
                           data=vf.read(), timeout=600)
    if up.status_code >= 300:
        raise RuntimeError(f"IG upload fail: {up.status_code} {up.text[:200]}")
    status = ""
    for _ in range(40):
        time.sleep(10)
        st = requests.get(f"{GRAPH}{cid}", params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN},
                          timeout=30).json()
        status = st.get("status_code", "")
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG processing {status}: {st}")
    if status != "FINISHED":
        raise RuntimeError("IG processing time-out")
    pub = requests.post(f"{GRAPH}{IG_USER_ID}/media_publish",
                        data={"creation_id": cid, "access_token": IG_ACCESS_TOKEN}, timeout=60).json()
    if not pub.get("id"):
        raise RuntimeError(f"IG publish fail: {pub}")
    print("INSTAGRAM PE POST HO GAYA:", pub["id"])
    return pub["id"]


# ============================== MAIN ==============================

def pick_question(bank, st, seq=None):
    by_seq = {q["seq"]: q for q in bank}
    if seq:
        return [by_seq[seq]]
    done = set(st["posted"]) | set(st["skipped"])
    n = len(bank)
    start = st.get("next_seq", 1)
    out = []
    for k in range(n):
        q = by_seq.get(((start - 1 + k) % n) + 1)
        if q and q["id"] not in done:
            out.append(q)
        if len(out) >= MAX_TRIES_PER_RUN + 1:
            break
    if not out:                     # poora bank ho gaya -> naya chakra (revision round)
        st["posted"], st["skipped"] = [], {}
        return pick_question(bank, st)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-post", action="store_true")
    ap.add_argument("--seq", type=int)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    bank = load_bank()
    st = load_progress()
    cands = pick_question(bank, st, args.seq)
    ep = st["episode"] + 1
    chosen, ai, data = None, None, None
    for i, q in enumerate(cands[:MAX_TRIES_PER_RUN]):
        print(f"\nSawal #{q['seq']} ({q['subject']}, {q['times_asked']} baar): {q['question'][:80]}")
        ai = ai_enrich(q)
        if ai and ai.get("reject"):
            print("  CHHODA:", ai["reject"])
            if not args.seq:
                st["skipped"][q["id"]] = ai["reject"]
            continue
        chosen = q
        break
    if not chosen:
        save_progress(st)
        raise SystemExit("Is run me koi sahi sawal nahi mila (sab jaanch me fail).")
    nxt = next((c for c in cands if c is not chosen and c["id"] not in st["skipped"] and c["seq"] > chosen["seq"]), None)
    print("  AI safai:", "haan" if ai else "nahi (book text + wajah)")
    data = prepare_data(chosen, ai, ep, nxt)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    if args.preview:
        build_reel(data, out, preview_dir="preview")
        return
    build_reel(data, out)
    caption = make_caption(data)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.seq:
        print("--seq mode: progress nahi badla.")
        if not args.no_post:
            post_reel(out, caption)
        return
    if args.no_post or DRY_RUN:
        save_progress(st)
        return
    if not post_reel(out, caption):
        save_progress(st)
        return
    st["posted"].append(chosen["id"])
    st["episode"] = ep
    st["next_seq"] = chosen["seq"] + 1
    st["last"] = {"seq": chosen["seq"], "id": chosen["id"], "time": time.strftime("%Y-%m-%d %H:%M")}
    save_progress(st)


if __name__ == "__main__":
    main()
