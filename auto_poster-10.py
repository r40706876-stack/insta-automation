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
GRAPH_VER = "v19.0"                     # purane auto_poster (6) me yahi chal raha tha
GRAPH = f"https://graph.facebook.com/{GRAPH_VER}/"

DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
CF_ACCOUNT_ID = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or os.getenv("CF_ACCOUNT_ID") or "").strip()
CF_API_TOKEN = (os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CF_API_TOKEN") or "").strip()
CF_IMAGE_MODELS = ["@cf/black-forest-labs/flux-1-schnell", "@cf/bytedance/stable-diffusion-xl-lightning"]
IMG_DIR = "img_cache"
# "publish" = Instagram pe seedha post | "manual" = Instagram pe NAHI, reel repo ke ready_reels/ folder me
# (Instagram ki API me "draft me save" ka koi tareeka nahi hai, isliye manual mode hi draft jaisa kaam karta hai)
POST_MODE = os.getenv("POST_MODE", "publish").strip().lower()
READY_DIR = "ready_reels"
READY_KEEP = 8

SERIES = "SCIENCE PYQ"
BRAND = "MinuteMe_GS"                       # Instagram account ka naam - har jagah branding
BRAND_HANDLE = "@MinuteMe_GS"
BRAND_SPEAK = "Minute Me G S"              # naam awaaz me ANGREZI me (Hindi lipi me galat lagta tha)
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
                              // (e.g. 'm/s2' -> 'मीटर प्रति सेकंड स्क्वायर', 'CO2' -> 'सी ओ टू', 'pH' -> 'पी एच', 'SI' -> 'एस आई').
                              // BLANKS (____): NEVER say 'खाली स्थान' - rephrase naturally as a question with 'कितने/कौन सा/क्या'
                              // e.g. '____ जन्तुओं का सबसे बड़ा समूह है' -> 'जन्तुओं का सबसे बड़ा समूह कौन सा है?'
 "speak_answer": "...",       // the correct option text as spoken Hindi (same rule)
 "why": "...",                // ONE simple Hindi line (max 18 words): the science reason why the key is correct. No book/coaching names.
 "tip": "...",                // Hindi memory trick / exam tip, max 8 words (can be a short formula like 'दाब = बल / क्षेत्रफल')
 "topic": "...",              // 1-3 word Hindi topic name (e.g. 'प्रकाश का अपवर्तन')
 "en_question": "...",        // short English translation of the question (max 20 words)
 "en_why": "...",             // English translation of 'why' (max 18 words)
 "img_hook": "...",           // ENGLISH image prompt (max 40 words): a striking, curiosity-making real-world scene about this
                              // question's topic WITHOUT showing or hinting the answer. Concrete objects, dramatic angle. No text.
 "img_why": "...",            // ENGLISH image prompt (max 40 words): a clear visual that SHOWS the science behind the correct
                              // answer (the concept in action), easy to understand at a glance. No text, no labels.
 "en_tip": "...",             // English translation of 'tip' (max 8 words)
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
    for model in ("gemini-flash-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"):
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
        out = {k: js.get(k) for k in ("why", "tip", "topic", "en_question", "en_why", "en_tip", "img_hook", "img_why")}
        out["hook"] = ""
        hk = clean_text(out.get("hook") or "")
        ans_core = clean_text(q["options"][q["answer"]])
        if (not _hi_ok(hk, 9) or (len(ans_core) >= 3 and ans_core in hk)
                or re.search(r"\d+\s*(%|प्रतिशत)|ज़्यादातर|ज्यादातर|अधिकतर लोग|लोग गलत", hk)):
            out["hook"] = ""
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
    (r"\s*/\s*", " प्रति "), (r"\s*=\s*", " बराबर "), (r"\s\+\s", " और "), (r"\s*____+\s*", " "),
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


def first_clean_sentence(exp, question="", answer=""):
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
    ans = clean_text(answer).strip(" .।")
    if len(ans) >= 2:
        hit = [c for c in cands if ans in c[1]]
        if hit:
            return hit[0][1]
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
    """Sach pe tika hook: ye sawal kitne exam-paper (shift) me aaya."""
    n = int(q.get("times_asked") or 1)
    yrs = q.get("years") or []
    y = yrs[-1] if yrs else ""
    if n >= 2:
        return [f"ये सवाल {n} पेपर में आया!", f"{n} पेपर में आया ये सवाल!",
                f"{n} बार पेपर में आ चुका!"][ep % 3]
    return [f"Railway {y} पेपर का सवाल!", f"RRB {y} पेपर में आया!",
            f"{y} के पेपर में आया!"][ep % 3].replace("  ", " ")


# ---------- Cloudflare Workers AI: topic ka sundar chitra ----------

IMG_STYLE = ("cinematic 3D render, vibrant colors, dramatic rim lighting, ultra detailed, depth of field, "
             "high-end educational science illustration, clean composition. absolutely no text, no letters, "
             "no words, no numbers, no watermark, no logo")
SUBJECT_SCENE = {"Physics": "physics laboratory with glowing light beams, magnets and electric sparks",
                 "Chemistry": "chemistry laboratory with colorful glowing flasks, bubbling liquids and molecules",
                 "Biology": "microscopic world of living cells, plants and the human body, bioluminescent"}


def cf_image(prompt):
    """Cloudflare se chitra (bytes) ya None. Quota/setup galat -> None (reel bina chitra ke banti hai)."""
    import base64
    if not (CF_ACCOUNT_ID and CF_API_TOKEN) or DRY_RUN:
        return None
    hdr = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    for model in CF_IMAGE_MODELS:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{model}"
        body = {"prompt": prompt[:1900]}
        if "flux" in model:
            body["steps"] = 8
        else:
            body.update({"width": 1024, "height": 1024})
        try:
            r = requests.post(url, headers=hdr, json=body, timeout=150)
        except requests.RequestException as exc:
            print("  Cloudflare:", str(exc)[:100])
            continue
        if r.status_code in (401, 403):
            print(f"  CLOUDFLARE SETUP GALAT ({r.status_code}): Account ID / token (Workers AI permission) jaanchiye")
            return None
        if r.status_code != 200:
            print(f"  Cloudflare {model.split('/')[-1]}: {r.status_code} {r.text[:120]}")
            continue
        if r.headers.get("content-type", "").startswith("image/"):
            return r.content
        try:
            js = r.json()
            img = (js.get("result") or {}).get("image") if isinstance(js.get("result"), dict) else js.get("image")
            if img:
                return base64.b64decode(img)
        except Exception as exc:
            print("  Cloudflare jawab samajh nahi aaya:", str(exc)[:100])
    return None


def make_images(q, ai):
    """2 chitra: hook (jigyasa, jawab chhupa) + why (concept dikhata). Path ya None."""
    import io
    os.makedirs(IMG_DIR, exist_ok=True)
    base = (ai or {}).get("en_question") or ""
    p_hook = (ai or {}).get("img_hook") or (f"{SUBJECT_SCENE.get(q['subject'], 'science laboratory')}, "
                                            f"scene inspired by: {base}" if base else SUBJECT_SCENE.get(q["subject"], ""))
    p_why = (ai or {}).get("img_why") or ""
    out = {}
    for key, prm in (("hook", p_hook), ("why", p_why)):
        if not prm:
            continue
        path = os.path.join(IMG_DIR, f"{q['id']}_{key}.jpg")
        if not os.path.exists(path):
            b = cf_image(f"{prm}. {IMG_STYLE}")
            if not b:
                continue
            try:
                Image.open(io.BytesIO(b)).convert("RGB").save(path, quality=92)
            except Exception:
                continue
        out[key] = path
    if out:
        print("  Chitra bane:", ", ".join(out))
    return out


SCIENCE_EXAMS = ["RRB NTPC", "SSC GD", "SSC CGL", "SSC CHSL", "SSC MTS", "RRB ALP", "State Police", "UPSC Prelims",
                 "CTET", "Patwari", "State PSC", "Railway Technician"]


def also_exams(q):
    """Science wale doosre exams (rotate) - chip pe 'इनके लिए भी' ke saath."""
    rnd = random.Random(q["id"] + "x")
    picks = rnd.sample(SCIENCE_EXAMS, 3)
    return ["इनमें भी Science:"] + picks


def prepare_data(q, ai, ep, next_q=None, imgs=None):
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
    why = clean_text((ai or {}).get("why") or "") or first_clean_sentence(q.get("explanation", ""), q["question"], q["options"][q["answer"]])
    if not why:
        why = f"सही उत्तर है: {correct_text.rstrip('.')}।"
    tip = clean_text((ai or {}).get("tip") or "")
    topic = clean_text((ai or {}).get("topic") or "") or short_topic(q)
    en_q = clean_text((ai or {}).get("en_question") or "")
    en_opt = {L: clean_text(((ai or {}).get("en_options") or {}).get(L.lower(), "")) for L in letters}
    if not all(en_opt.values()):
        en_opt = {}
    en_opt = {L: ("" if re.sub(r"\W", "", v) == re.sub(r"\W", "", opts[L.lower()]) else v) for L, v in en_opt.items()}
    data = {
        "id": q["id"], "seq": q["seq"], "episode": ep, "subject": q["subject"],
        "question": question, "options": options, "correct": correct, "correct_text": correct_text,
        "vs_pair": pair, "elim_order": elim, "why": why, "tip": tip, "topic": topic,
        "times_asked": int(q.get("times_asked") or 1), "exams": exam_tags(q),
        "hook": hook_line(q, ep),
        "also_exams": also_exams(q),
        "img_hook": (imgs or {}).get("hook"), "img_why": (imgs or {}).get("why"),
        "en_why": clean_text((ai or {}).get("en_why") or "") if (ai or {}).get("why") else "",
        "en_tip": clean_text((ai or {}).get("en_tip") or "") if (ai or {}).get("tip") else "", "en_question": en_q if len(en_q.split()) <= 24 else "", "en_opt": en_opt,
        "speak_q": clean_text((ai or {}).get("speak_question") or "") or to_speech(question),
        "speak_ans": clean_text((ai or {}).get("speak_answer") or "") or to_speech(correct_text),
        "teaser": clean_text(next_q["question"]) if next_q else "",
        "teaser_opts": [(L, clean_text(next_q["options"][L.lower()])) for L in "ABCD"] if next_q else [],
        "ai": bool(ai),
    }
    return data


# ============================== SCENE SPECS + AWAAZ ==============================

def build_scene_specs(data):
    """segs = [(key, screen_text, bolne_ka_text)]."""
    ans_say = f"सही जवाब, {data['correct']}! {data['speak_ans']}।"
    why_say = to_speech(data["why"]) if not data.get("ai") else data["why"]
    specs = [
        {"name": "hook", "mood": "red", "tail": 0.15, "min": 2.4,
         "segs": [("hk", data["hook"], to_speech(data["hook"])), ("q", data["question"], data["speak_q"])]},
        {"name": "question", "mood": "blue", "tail": 0.0, "min": 0,
         "segs": [("lock", "जवाब कमेंट करो!", "जवाब कमेंट करो!")]},
        {"name": "verdict", "mood": "green", "tail": 0.1, "min": 2.1, "delay": 0.9,
         "segs": [("rev", ans_say, ans_say)]},
        {"name": "why", "mood": "blue", "tail": 0.6, "min": 3.0,
         "segs": [("wx", "क्योंकि,", "क्योंकि,"), ("why", data["why"], why_say)]
                 + ([("tip", data["tip"], to_speech("याद रखो, " + data["tip"]))] if data.get("tip") else []),
         "read": [("why", data["why"])]},
        {"name": "cta", "mood": "purple", "tail": 1.6, "min": 4.2,
         "segs": [("cta", "अगला सवाल! जवाब पता है तो कमेंट करो।",
                   f"अगला सवाल स्क्रीन पर है, जवाब पता हो तो कमेंट करो! {BRAND_SPEAK} को फॉलो करो, "
                   f"और फ्री नोट्स और मॉक टेस्ट के लिए स्क्रीन पर दिए नंबर पर व्हाट्सऐप करो।")]},
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


# ---------- Gemini TTS: poori reel ki awaaz EK request me, top-3 model/awaaz baari-baari ----------

USE_GEMINI_TTS = os.getenv("USE_GEMINI_TTS", "1") != "0"
GEMINI_TTS_STYLE = "friendly, energetic Indian teacher, natural Hindi, brisk pace"
VOICE_SPEEDUP = float(os.getenv("VOICE_SPEEDUP", "1.06"))
PREBUILT_VOICES = ["Kore", "Charon", "Sulafat", "Puck", "Aoede", "Achird"]
_CACHE = {}


def _model_ver(n):
    m = re.match(r"gemini-(\d+)(?:\.(\d+))?", n or "")
    return (int(m.group(1)), int(m.group(2) or 0)) if m else (0, 0)


def _gemini_model_names():
    if "models" in _CACHE:
        return _CACHE["models"]
    names, token = [], None
    try:
        for _ in range(5):
            params = {"key": GEMINI_API_KEY, "pageSize": 200}
            if token:
                params["pageToken"] = token
            r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params=params, timeout=60)
            if r.status_code != 200:
                break
            js = r.json()
            names += [m["name"].split("/")[-1] for m in js.get("models", [])
                      if "generateContent" in (m.get("supportedGenerationMethods") or [])]
            token = js.get("nextPageToken")
            if not token:
                break
    except Exception as exc:
        print("  Gemini model list nahi mili:", str(exc)[:100])
    _CACHE["models"] = names
    return names


def gemini_tts_models():
    """Sabse behtar TTS models (top 3): naya version > pro > flash > lite."""
    names = [n for n in _gemini_model_names() if "tts" in n and n.startswith("gemini-")
             and not any(b in n for b in ("live", "native"))]
    ranked = sorted(names, key=lambda n: (_model_ver(n), "pro" in n, "lite" not in n, "preview" not in n),
                    reverse=True)
    return ranked[:3] or ["gemini-2.5-pro-preview-tts", "gemini-2.5-flash-preview-tts"]


def _new_style_tts(model):
    return _model_ver(model) >= (3, 8)


def hindi_voices():
    """Gemini voice library ki Hindi awaazein (male/female baari-baari, top 3). Na mile to standard."""
    if "voices" in _CACHE:
        return _CACHE["voices"]
    out = []
    try:
        r = requests.get("https://generativelanguage.googleapis.com/v1beta/voices", timeout=60,
                         params={"key": GEMINI_API_KEY, "language_code": "hi-IN", "page_size": 200})
        if r.status_code == 200:
            scored = []
            for v in r.json().get("voices", []) or []:
                vid = v.get("id") or v.get("name") or ""
                blob = " ".join(str(v.get(k, "")) for k in ("display_name", "displayName", "description",
                                                           "persona", "accent")).lower()
                sc = 3 * any(w in blob for w in ("education", "teacher", "narrat", "conversational", "explainer"))
                sc += 2 * any(w in blob for w in ("warm", "friendly", "natural", "clear", "engaging"))
                sc -= 6 * any(w in blob for w in ("bhojpuri", "awadhi", "haryanvi", "rajasthani", "dialect",
                                                  "whisper", "child", "robot", "assistant"))
                if vid:
                    scored.append((sc, vid, str(v.get("gender", "")).lower()))
            scored.sort(key=lambda x: -x[0])
            m = [x for x in scored if x[2].startswith("m")]
            f = [x for x in scored if x[2].startswith("f")]
            for i in range(3):
                for grp in (f, m):
                    if i < len(grp) and len(out) < 3:
                        out.append(grp[i][1])
    except Exception:
        pass
    _CACHE["voices"] = out
    return out


def _pcm_to_array(b64, mime):
    import base64
    import io
    raw = base64.b64decode(b64)
    m = re.search(r"rate=(\d+)", mime or "")
    rate = int(m.group(1)) if m else 24000
    if raw[:4] == b"RIFF":
        with wave.open(io.BytesIO(raw)) as wf:
            rate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())
    pcm = np.frombuffer(raw[: len(raw) // 2 * 2], dtype="<i2").astype(np.float32) / 32768.0
    if rate != SR and len(pcm):
        x_new = np.arange(int(len(pcm) * SR / rate)) * (rate / SR)
        pcm = np.interp(x_new, np.arange(len(pcm)), pcm).astype(np.float32)
    return pcm


def _find_audio(obj):
    if isinstance(obj, dict):
        mime = obj.get("mimeType") or obj.get("mime_type") or ""
        if isinstance(obj.get("data"), str) and len(obj["data"]) > 1000 and (not mime or "audio" in mime):
            return obj["data"], mime
        for v in obj.values():
            got = _find_audio(v)
            if got:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = _find_audio(v)
            if got:
                return got
    return None


def _tts_bodies(model, lines, voice):
    base = "https://generativelanguage.googleapis.com/v1beta"
    gen_url = f"{base}/models/{model}:generateContent"
    if _new_style_tts(model):
        script = " <long pause> ".join(lines)
        return [
            (gen_url, {"contents": [{"role": "user", "parts": [{"text": script,
                                                                 "speech_metadata": {"style": GEMINI_TTS_STYLE}}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"],
                                            "speechConfig": {"voiceConfig": {"voice": voice}}}}),
            (f"{base}/interactions", {
                "model": model,
                "input": [{"type": "user_input", "content": [{
                    "type": "text", "text": script,
                    "annotations": [{"type": "speech_metadata", "style": GEMINI_TTS_STYLE}]}]}],
                "response_format": {"type": "audio"},
                "generation_config": {"speech_config": [{"voice": voice}]}}),
        ]
    script = "\n\n".join(lines)
    return [(gen_url, {"contents": [{"parts": [{"text": script}]}],
                       "generationConfig": {"responseModalities": ["AUDIO"],
                                            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig":
                                                                             {"voiceName": voice}}}}})]


def gemini_tts_once(lines, rot):
    """Poori script EK request me. rot = reel number (top-3 model + awaaz baari-baari). -> (audio, label)."""
    models = gemini_tts_models()
    lib = hindi_voices()
    order = models[rot % len(models):] + models[:rot % len(models)]
    last = None
    for model in order:
        voice = (lib[rot % len(lib)] if (lib and _new_style_tts(model)) else PREBUILT_VOICES[rot % 3])
        for url, body in _tts_bodies(model, lines, voice):
            try:
                r = requests.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=300)
            except requests.RequestException as exc:
                last = exc
                break
            if r.status_code in (400, 404) and not url.endswith("/interactions"):
                last = RuntimeError(f"{model} {r.status_code}: {r.text[:120]}")
                continue
            if r.status_code != 200:
                last = RuntimeError(f"{model} {r.status_code}: {r.text[:120]}")
                print(f"  Gemini TTS {model}: {r.status_code} -> agla model")
                break
            got = _find_audio(r.json())
            if got:
                arr = _pcm_to_array(*got)
                if len(arr) > SR * 1.0:
                    return arr, f"{model} / {voice}"
            last = RuntimeError(f"{model}: audio nahi mila")
    raise RuntimeError(f"Gemini TTS nahi bani: {last}")


def _silence_runs(arr, min_gap, rel_db=-32.0):
    hop = int(SR * 0.01)
    n = len(arr) // hop
    if n < 3:
        return []
    fr = arr[: n * hop].reshape(n, hop)
    rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
    ref = np.percentile(rms, 95)
    if ref <= 1e-6:
        return []
    silent = rms < ref * (10 ** (rel_db / 20))
    runs, st = [], None
    for k, sflag in enumerate(silent):
        if sflag and st is None:
            st = k
        elif not sflag and st is not None:
            runs.append((st * 0.01, k * 0.01))
            st = None
    if st is not None:
        runs.append((st * 0.01, n * 0.01))
    return [(a, b) for a, b in runs if b - a >= min_gap]


def _pick_cuts(gaps, expected, total, len_w=0.15):
    n, m = len(expected), len(gaps)
    if n == 0:
        return []
    if m < n:
        return None
    mids = [(a + b) / 2 for a, b in gaps]
    lens = [b - a for a, b in gaps]
    INF = float("inf")
    cost = [[INF] * m for _ in range(n)]
    back = [[-1] * m for _ in range(n)]
    for j in range(m):
        cost[0][j] = abs(mids[j] - expected[0]) / total - len_w * min(lens[j], 1.2)
    for i in range(1, n):
        best, bk = INF, -1
        for j in range(m):
            if j - 1 >= 0 and cost[i - 1][j - 1] < best:
                best, bk = cost[i - 1][j - 1], j - 1
            if best < INF:
                cost[i][j] = best + abs(mids[j] - expected[i]) / total - len_w * min(lens[j], 1.2)
                back[i][j] = bk
    j = min(range(m), key=lambda x: cost[n - 1][x])
    if cost[n - 1][j] == INF:
        return None
    chosen = []
    for i in range(n - 1, -1, -1):
        chosen.append(j)
        j = back[i][j]
    chosen.reverse()
    return [gaps[k] for k in chosen]


def _speech_bounds(arr):
    runs = _silence_runs(arr, 0.0)
    a, b = 0.0, len(arr) / SR
    if runs and runs[0][0] <= 0.01:
        a = runs[0][1]
    if runs and runs[-1][1] >= b - 0.02:
        b = runs[-1][0]
    return max(0.0, a - 0.03), min(len(arr) / SR, b + 0.08)


def _compress_pauses(arr, max_pause=MAX_PAUSE):
    runs = _silence_runs(arr, max_pause + 0.02)
    keep, cur = [], 0.0
    for a, b in runs:
        keep.append((cur, a + max_pause / 2))
        cur = b - max_pause / 2
    keep.append((cur, len(arr) / SR))
    fade = int(0.006 * SR)
    pieces = []
    for a, b in keep:
        seg = arr[int(a * SR):int(b * SR)].copy()
        if len(seg) > 2 * fade:
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
        pieces.append(seg)

    def remap(t):
        out = 0.0
        for a, b in keep:
            if t <= a:
                break
            out += min(t, b) - a
        return out
    return (np.concatenate(pieces) if pieces else arr).astype(np.float32), remap


def _wt(text):
    return len(text.replace(" ", "")) + 4 * len(re.findall(r"[,.!?।]", text)) + 2


def _durations_ok(bounds, weights, total, lo=0.4, hi=2.5):
    wsum = float(sum(weights)) or 1.0
    for (a, b), w in zip(bounds, weights):
        exp = total * w / wsum
        if b - a < 0.3 or not (lo * exp <= (b - a) <= hi * exp):
            return False
    return True


def speed_voice(arr, f=VOICE_SPEEDUP):
    if arr is None or abs(f - 1.0) < 0.01 or len(arr) < SR * 0.2:
        return arr
    try:
        pcm = (np.clip(arr, -1, 1) * 32767).astype(np.int16).tobytes()
        cmd = ["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-",
               "-af", f"atempo={f:.3f}", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-"]
        raw = subprocess.run(cmd, input=pcm, check=True, capture_output=True).stdout
        out = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        return out if len(out) > SR * 0.1 else arr
    except Exception:
        return arr


def split_gemini_audio(full, specs):
    """Ek lambi awaaz -> scenes (scene ke beech ki chuppi se) + har scene ke andar segments ki shuruaat."""
    lead, tail = _speech_bounds(full)
    full = full[int(lead * SR):int(tail * SR)]
    total = len(full) / SR
    weights = [_wt(" ".join(t for _, _, t in sp["segs"])) for sp in specs]
    wsum = float(sum(weights))
    acc, expected = 0.0, []
    for w in weights[:-1]:
        acc += w
        expected.append(total * acc / wsum)
    chosen = _pick_cuts(_silence_runs(full, 0.35), expected, total, len_w=0.6)
    if chosen is None:
        print("  Gemini awaaz: scenes ke beech ruk nahi mile")
        return None
    edges = [0.0] + [(a + b) / 2 for a, b in chosen] + [total]
    bounds = list(zip(edges[:-1], edges[1:]))
    if not _durations_ok(bounds, weights, total):
        print("  Gemini awaaz: scenes ki lambai script se mel nahi khaati")
        return None
    out = []
    for sp, (a, b) in zip(specs, bounds):
        chunk = full[int(a * SR):int(b * SR)]
        s0, s1 = _speech_bounds(chunk)
        chunk = chunk[int(s0 * SR):int(s1 * SR)]
        segs = sp["segs"]
        starts = None
        if len(segs) > 1:
            cl = len(chunk) / SR
            sw = [_wt(t) for _, _, t in segs]
            ssum = float(sum(sw))
            acc2, exp2 = 0.0, []
            for w in sw[:-1]:
                acc2 += w
                exp2.append(cl * acc2 / ssum)
            inner = _pick_cuts(_silence_runs(chunk, 0.08), exp2, cl)
            if inner is not None:
                st = [0.0] + [g[1] for g in inner]
                if _durations_ok(list(zip(st, st[1:] + [cl])), sw, cl, 0.25, 4.0):
                    starts = st
            if starts is None:                          # anupaat se
                st, acc3 = [0.0], 0.0
                for w in sw[:-1]:
                    acc3 += w
                    st.append(cl * acc3 / ssum)
                starts = st
        else:
            starts = [0.0]
        chunk, remap = _compress_pauses(chunk)
        starts = [remap(x) for x in starts]
        out.append((chunk, starts))
    return out


def make_voices(specs, rot=0):
    """
    1) Gemini TTS: poori reel ki script EK request me (top-3 model/awaaz baari-baari), chuppi se scenes me kaati.
    2) Gadbad (quota/galat kataai) -> edge-tts, har scene alag (word-sync ke saath).
    Returns [(audio, words_or_None, speech_text, seg_starts_or_None)].
    """
    speeches = [" ".join(s for _, _, s in sp["segs"]) for sp in specs]
    if DRY_RUN:
        return [(*_fake_voice(sp_), sp_, None) for sp_ in speeches]
    if USE_GEMINI_TTS and GEMINI_API_KEY:
        try:
            full, label = gemini_tts_once(speeches, rot)
            res = split_gemini_audio(full, specs)
            if res:
                out = []
                f = VOICE_SPEEDUP
                for (chunk, starts), sp_ in zip(res, speeches):
                    arr = speed_voice(chunk, f)
                    k = len(arr) / max(1, len(chunk))
                    out.append((arr, None, sp_, [x * k for x in starts]))
                print(f"Awaaz: Gemini TTS ek baar me ({label})")
                _CACHE["voice_used"] = "Gemini " + label
                return out
            print("Gemini awaaz scenes me sahi nahi kati -> edge-tts")
        except Exception as exc:
            print(f"Gemini TTS nahi chala ({str(exc)[:160]}) -> edge-tts")
    out = []
    for i, sp_ in enumerate(speeches):
        path = f"_voice_{i}.mp3"
        words = asyncio.run(_tts_async(sp_, path))
        arr = decode_raw(path)
        os.remove(path)
        arr, words = tighten_voice(arr, words)
        out.append((arr, words, sp_, None))
    _CACHE["voice_used"] = "edge-tts " + VOICE_NAME
    return out


def marks_from_starts(sp, starts, vdur, lead):
    keys = [k for k, _, _ in sp["segs"]]
    marks, wt = {}, {}
    for i, (key, disp, _) in enumerate(sp["segs"]):
        a = starts[i] + lead
        b = (starts[i + 1] + lead) if i + 1 < len(starts) else vdur
        marks[key] = (a, b)
        ws = disp.split()
        th = word_thresholds(ws) if ws else []
        wt[key] = [a + (b - a) * x for x in th]
    return marks, wt


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
    for i, (sp, (arr, words, speech, starts)) in enumerate(zip(specs, voices)):
        lead = VOICE_LEAD + sp.get("delay", 0.0)
        vdur = len(arr) / SR + lead
        dur = max(vdur + sp["tail"], sp["min"])
        if starts is not None and len(starts) == len(sp["segs"]):
            marks, wt = marks_from_starts(sp, starts, vdur, lead)
        else:
            shifted = [(a + lead, b + lead, w) for a, b, w in (words or [])]
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
    for sc, (arr, _, _, _) in zip(timeline, voices):
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
            for i in range(4):                           # options uchhalte hain
                add_at(buf, sfx_pop(0.32), s + 0.38 + 0.12 * i)
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
TILE_W, TILE_H = 470, 240
GRID_X = [W / 2 - 250, W / 2 + 250]
GRID_Y = [1075, 1330]
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
    top = f"{SERIES}"
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
    chip = pill_sprite(lab.split("•")[0].strip(), 24, col, (14, 26, 44), col)
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
    pad, br = 30, 26
    bx, by = pad + 18 + br, pad + 18 + br
    d.ellipse((bx - br, by - br, bx + br, by + br), fill=badge + (255,))
    d.text((bx, by), letter, font=get_font(32), fill=(8, 16, 30, 255), anchor="mm")
    cx_ = pad + w / 2 + 22                         # badge se hat ke (text badge pe na chadhe)
    maxw = w - 150
    enh = 36 if en else 0
    max_lines = 3 if h >= 200 else 2
    f, s_, lines = fit_lines(text, maxw, max_lines, 54 if h >= 200 else 46, 28)
    lines = lines[:max_lines]
    lh = int(s_ * 1.18)
    y0 = pad + h / 2 + 4 - (lh * len(lines) + enh) / 2 + lh / 2
    for k, ln in enumerate(lines):
        d.text((cx_, y0 + k * lh), " ".join(ln), font=f, fill=tcol + (255,), anchor="mm")
    if en:
        fe, se, le = fit_lines(en, maxw + 20, 1, 27, 18, reg=True)
        d.text((cx_, y0 + len(lines) * lh - lh / 2 + 22), " ".join(le[0]) if le else "", font=fe,
               fill=(EN_COL if state != "wrong" else MUTED) + (255,), anchor="mm")
    if state == "wrong":
        yy = y0 + (len(lines) - 1) * lh / 2
        tw = max(text_w(" ".join(l), f) for l in lines) if lines else 0
        d.line((cx_ - tw / 2 - 10, yy, cx_ + tw / 2 + 10, yy), fill=RED + (230,), width=7)
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

# ---------- high-level FX ----------

def shockwave(cv, cx, cy, t, t0, color=YELLOW, dur=0.65, rmax=520, width=14):
    """Dhamaka-ghera: beech se phailta chamakta ring (pehle frame ki 'punch')."""
    if not (t0 <= t < t0 + dur):
        return
    p = ease_out_cubic((t - t0) / dur)
    r = 40 + rmax * p
    a = int(230 * (1 - p))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    wv = max(2, int(width * (1 - p)))
    d.ellipse((cx - r, cy - r * 0.62, cx + r, cy + r * 0.62), outline=color + (a,), width=wv)
    d.ellipse((cx - r * 0.8, cy - r * 0.5, cx + r * 0.8, cy + r * 0.5), outline=WHITE + (a // 2,), width=max(1, wv // 2))
    cv.paste(lay, (0, 0), lay)


def spark_burst(cv, cx, cy, t, t0, n=46, seed=3, cols=(YELLOW, CYAN, WHITE, ORANGE), speed=(500, 1200), dur=0.9):
    """Chingaariyan: ek pal me chaaro taraf udti roshni ki lakeerein."""
    tt = t - t0
    if not (0 <= tt < dur):
        return
    rng = random.Random(seed)
    d = ImageDraw.Draw(cv)
    fade = 1 - tt / dur
    for _ in range(n):
        ang = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(*speed)
        col = rng.choice(cols)
        dist = sp * tt * (1 - 0.45 * tt)
        x1, y1 = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist * 0.8
        tail = 28 + 40 * fade
        x0, y0 = x1 - math.cos(ang) * tail, y1 - math.sin(ang) * tail * 0.8
        d.line((x0, y0, x1, y1), fill=mix(BG_BOTTOM, col, fade), width=max(2, int(5 * fade)))


def neon_border(cv, cx, cy, w, h, t, color=CYAN, speed=0.45):
    """Card ke kinare pe daudti neon roshni (2 chamakti bindu)."""
    per = 2 * (w + h)
    for off in (0.0, 0.5):
        u = ((t * speed + off) % 1.0) * per
        if u < w:
            x, y = cx - w / 2 + u, cy - h / 2
        elif u < w + h:
            x, y = cx + w / 2, cy - h / 2 + (u - w)
        elif u < 2 * w + h:
            x, y = cx + w / 2 - (u - w - h), cy + h / 2
        else:
            x, y = cx - w / 2, cy + h / 2 - (u - 2 * w - h)
        place(cv, glow_sprite(70, color, 220), x, y)
        place(cv, glow_sprite(22, WHITE, 255), x, y)


def rgb_split(frame, amt):
    """Glitch: laal/neela parda alag khisakta hai (scene badalne pe 0.1s)."""
    if amt < 1:
        return frame
    r, g, b = frame.split()
    r = ImageChops.offset(r, int(amt), 0)
    b = ImageChops.offset(b, -int(amt), 0)
    return Image.merge("RGB", (r, g, b))


@lru_cache(maxsize=16)
def headline_sprite(text, size):
    f, s_, lines = fit_lines(text, 960, 1, size, 52)
    if len(lines) > 1:
        f, s_, lines = fit_lines(text, 960, 2, 60, 44)
    lh = int(s_ * 1.18)
    w, h = 1060, lh * len(lines) + 60
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dg, d = ImageDraw.Draw(glow), ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        y = 30 + lh * k + lh / 2
        dg.text((w / 2, y), " ".join(ln), font=f, fill=ORANGE + (255,), anchor="mm", stroke_width=16,
                stroke_fill=ORANGE + (160,))
        d.text((w / 2, y), " ".join(ln), font=f, fill=YELLOW + (255,), anchor="mm", stroke_width=7,
               stroke_fill=(20, 8, 0, 255))
    from PIL import ImageFilter
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(glow, im)
    return out


@lru_cache(maxsize=8)
def ribbon_sprite(ep):
    txt = f"{SERIES}   |   {EXAMS_LINE}"
    f = get_font(30)
    w, h = int(text_w(txt, f)) + 70, 62
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=31, fill=(150, 20, 35, 240), outline=(255, 140, 140, 255), width=3)
    d.text((w / 2, h / 2 + 1), txt, font=f, fill=WHITE + (255,), anchor="mm")
    return im


HOOK_HEAD_Y = 450
Q_CARD_Y = 845


Q_TOP = 585                      # sawal card ka upar wala kinara
Q_MAXH = GRID_Y[0] - TILE_H / 2 - 35 - Q_TOP


@lru_cache(maxsize=32)
def q_layout(question, en):
    """Sawal (Hindi) + chhoti English line card me fit: (font size, card uchai, card beech)."""
    for sz in (64, 60, 56, 52, 48, 46, 44, 42, 40, 38):
        _, s2, ql = fit_lines(question, 900, 4, sz, sz)
        if len(ql) > 4:
            continue
        hh = int(s2 * 1.26) * len(ql)
        eh = 0
        if en:
            _, se, le = fit_lines(en, 880, 2, 30, 24, reg=True)
            eh = int(se * 1.3) * min(2, len(le)) + 10
        qh = hh + eh + 64
        if qh <= Q_MAXH:
            return sz, qh, Q_TOP + Q_MAXH / 2, hh, eh
    return 38, Q_MAXH, Q_TOP + Q_MAXH / 2, Q_MAXH - 64, 0


def draw_q_card(cv, data, t, sc, karaoke=True, alpha=1.0, pop=True):
    en = data.get("en_question", "")
    sz, qh, qcy, hh, eh = q_layout(data["question"], en)
    if alpha < 0.03:
        return qcy, qh
    kq = ease_out_back(prog(t, 0.05, 0.35)) if pop else 1.0
    place(cv, card_sprite(980, int(qh), (16, 30, 58), (70, 120, 190), 3, 34), W / 2, qcy,
          scale=0.94 + 0.06 * kq, alpha=alpha)
    if alpha > 0.9:
        neon_border(cv, W / 2, qcy, 980, qh, t)
    if karaoke and "q" in sc["marks"]:
        qp, th = seg_progress(sc, "q", t)
    else:
        qp, th = 1.0, None
    col = WHITE if alpha >= 0.99 else mix(BG_BOTTOM, WHITE, alpha)
    draw_kinetic(cv, data["question"], W / 2, 900, sz, qp, max_lines=4, min_size=36, line_h=1.26,
                 center_y=qcy - eh / 2, ghost=1.0, th=th, karaoke=karaoke,
                 hl_words=q_highlights(data["question"]) if alpha > 0.9 else (), hl_color=CYAN, color=col)
    if en:
        draw_en(cv, en, qcy - eh / 2 + hh / 2 + 6, max_w=880, size=30,
                color=EN_COL if alpha >= 0.99 else mix(BG_BOTTOM, EN_COL, alpha))
    return qcy, qh


# ---------- chitra: Ken Burns panel + dhundhla backdrop ----------

@lru_cache(maxsize=4)
def _img_src(path):
    try:
        return Image.open(path).convert("RGB")
    except Exception:
        return None


@lru_cache(maxsize=16)
def _round_mask(w, h, r=36):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def img_panel(path, w, h, t, zoom=0.06, border=YELLOW):
    """Chitra card: dheema zoom + pan (Ken Burns), gol kone, chamakta kinara. RGBA sprite."""
    src = _img_src(path)
    if src is None:
        return None
    w, h = int(w), int(h)
    sc = max(w / src.width, h / src.height) * (1.0 + zoom * clamp(t / 6.0))
    cw, ch = w / sc, h / sc
    px = (src.width - cw) * (0.5 + 0.18 * math.sin(t * 0.35))
    py = (src.height - ch) * (0.5 + 0.12 * math.cos(t * 0.3))
    crop = src.crop((int(px), int(py), int(px + cw), int(py + ch))).resize((w, h), Image.BILINEAR)
    out = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.rounded_rectangle((0, 0, w + 15, h + 15), radius=42, fill=border + (255,))
    out.paste(crop, (8, 8), _round_mask(w, h))
    # neeche halki parchhayi (text padhne layak)
    grad = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(int(h * 0.6), h):
        gd.line((0, y, w, y), fill=int(170 * (y - h * 0.6) / (h * 0.4)))
    shade = Image.new("RGBA", (w, h), (5, 10, 22, 255))
    shade.putalpha(ImageChops.multiply(grad, _round_mask(w, h)))
    out.paste(shade, (8, 8), shade)
    return out


@lru_cache(maxsize=4)
def backdrop(path):
    from PIL import ImageFilter
    src = _img_src(path)
    if src is None:
        return None
    sc = max((W + 120) / src.width, (H + 120) / src.height)
    im = src.resize((int(src.width * sc), int(src.height * sc)), Image.BILINEAR)
    l, tp = (im.width - W - 120) // 2, (im.height - H - 120) // 2
    im = im.crop((l, tp, l + W + 120, tp + H + 120)).filter(ImageFilter.GaussianBlur(18))
    return Image.blend(im, Image.new("RGB", im.size, BG_TOP), 0.55)


def draw_backdrop(cv, path, t, alpha):
    bd = backdrop(path) if path else None
    if bd is None or alpha <= 0.01:
        return cv
    ox = int(60 + 40 * math.sin(t * 0.3))
    oy = int(60 + 40 * math.cos(t * 0.25))
    return Image.blend(cv, bd.crop((ox, oy, ox + W, oy + H)), clamp(alpha))


def scene_hook(cv, data, t, sc):
    """
    Pehla frame = scroll rokne wala: '{n} पेपर में आया' chamakti headline (dhamaka-ghera + chingaariyan),
    neon card me asli sawal (bolte shabd peele) + English, aur chaaron options turant (padhna shuru).
    """
    fx = {}
    place(cv, ribbon_sprite(data["episode"]), W / 2, 272)
    hy = 395
    place(cv, rays_sprite(), W / 2, hy, angle=t * 25, scale=0.8)
    hs = headline_sprite(data["hook"], 82)
    punch = 1.18 - 0.18 * ease_out_back(prog(t, 0, 0.35))
    place(cv, hs, W / 2, hy, scale=punch * (1 + 0.018 * math.sin(t * 7)))
    shockwave(cv, W / 2, hy, t, 0.0, YELLOW)
    spark_burst(cv, W / 2, hy, t, 0.02)
    if t < 0.12:
        fx["shake"] = 9
    # chips: asli paper (jisme aaya) + science wale bade exams (jinke liye ye zaroori hai)
    cy_ = hy + hs.height / 2 + 2
    real = pill_sprite("पूछा गया: " + ", ".join(data["exams"][:2]), 26, (30, 18, 0), YELLOW, ORANGE)
    others = [pill_sprite(e, 27, (10, 30, 50), CYAN, CYAN) if i == 0 else
              pill_sprite(e, 27, WHITE, (30, 45, 80), (90, 120, 180)) for i, e in enumerate(data["also_exams"])]
    rows = [[real], others]
    for r_i, row in enumerate(rows):
        tot = sum(c.width for c in row) + 12 * (len(row) - 1)
        fit = min(1.0, 1000 / max(1, tot))              # line screen se bahar na jaaye
        x = W / 2 - tot * fit / 2
        yy = cy_ + r_i * 52
        for i, c in enumerate(row):
            kc = ease_out_back(prog(t, 0.12 + 0.07 * (i + r_i * 2), 0.3))
            place(cv, c, x + c.width * fit / 2, yy, scale=max(0.05, kc) * fit)
            x += (c.width + 12) * fit
    qcy, qh = draw_q_card(cv, data, t, sc)
    # PYQ thappa: sawal card ke kone pe
    # CHITRA BEAT: hook-line bolte waqt options ki jagah bada jigyasa-chitra; sawal shuru hote hi simat ke hat-ta hai
    t_opt = 0.35
    if data.get("img_hook"):
        tq = sc["marks"]["q"][0] if "q" in sc["marks"] else 1.2
        t_opt = tq + 0.05
        ex = ease_in_out(prog(t, tq - 0.15, 0.4))
        if ex < 0.99:
            top_, bot_ = GRID_Y[0] - TILE_H / 2, GRID_Y[1] + TILE_H / 2
            pw, ph = 980 * (1 - 0.3 * ex), (bot_ - top_) * (1 - 0.3 * ex)
            kp = ease_out_back(prog(t, 0.0, 0.4))
            pan = img_panel(data["img_hook"], pw, ph, t, border=YELLOW)
            if pan is not None:
                place(cv, glow_sprite(360, YELLOW, int(70 * (1 - ex))), W / 2, (top_ + bot_) / 2)
                place(cv, pan, W / 2, (top_ + bot_) / 2, scale=max(0.05, 0.92 + 0.08 * kp), alpha=1 - ex)
                if ex < 0.5:
                    qb = pill_sprite("चित्र देखो - सवाल सोचो!", 38, (30, 20, 0), YELLOW, ORANGE)
                    place(cv, qb, W / 2, bot_ - 60, scale=1 + 0.04 * math.sin(t * 9), alpha=1 - 2 * ex)
                    place(cv, pill_sprite("?", 70, WHITE, (110, 40, 160), PURPLE), W / 2 + 400, top_ + 70,
                          scale=1 + 0.08 * math.sin(t * 7), angle=10 * math.sin(t * 3), alpha=1 - 2 * ex)
    # chaaron options: ek-ek karke uchhal ke (sawal bolte-bolte padh lo)
    for i, (l, txt) in enumerate(data["options"]):
        gx, gy = grid_pos(i)
        ti_ = t_opt + 0.12 * i
        ki = ease_out_back(prog(t, ti_, 0.35)) if t >= ti_ else 0.0
        if ki <= 0.01:
            continue
        place(cv, tile_sprite(l, txt, data["en_opt"].get(l, ""), "normal"), gx, gy + 120 * (1 - min(ki, 1)),
              scale=0.85 + 0.15 * ki, alpha=clamp(ki * 1.5))
        if t > t_opt + 0.6:
            sheen(cv, gx, gy, TILE_W, TILE_H, t, period=2.0, offset=0.25 * i, strength=40)
    kc = ease_out_back(prog(t, t_opt + 0.7, 0.3)) if t >= t_opt + 0.7 else 0.0
    if kc > 0.01:
        place(cv, pill_sprite("आपका जवाब? कमेंट करो!", 40, (30, 20, 0), YELLOW, ORANGE), W / 2, 1505,
              scale=max(0.05, kc) * (1 + 0.03 * math.sin(t * 9)))
    return fx


def scene_grid(cv, data, t, sc):
    """Wahi screen (bina cut): 3-2-1 countdown, options pe scan-roshni."""
    fx = {}
    place(cv, ribbon_sprite(data["episode"]), W / 2, 272)
    d = ImageDraw.Draw(cv)
    d.text((W / 2, 400), "अपना जवाब लॉक करो!", font=get_font(70), fill=YELLOW, anchor="mm", stroke_width=6,
           stroke_fill=(20, 8, 0))
    draw_q_card(cv, data, t, sc, karaoke=False, pop=False)
    c0 = sc["cd_start"]
    cd = COUNTDOWN_SECONDS * COUNTDOWN_STEP
    scan = min(3, int((t - c0) / (cd / 4))) if c0 <= t < c0 + cd else -1
    states = {l: ("active" if i == scan else "normal") for i, (l, _) in enumerate(data["options"])}
    draw_grid(cv, data, states)
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
            if frac < 0.35:
                place(cv, glow_sprite(260, RED, int(120 * (1 - frac / 0.35))), cx, cy)
                shockwave(cv, cx, cy, frac, 0.0, YELLOW, dur=0.35, rmax=220, width=8)
        elif tt >= cd:
            place(cv, lock_sprite(80), cx, cy)
    place(cv, pill_sprite("A / B / C / D - कमेंट करो!", 40, (30, 20, 0), YELLOW, ORANGE), W / 2, 1505,
          scale=1 + 0.03 * math.sin(t * 9))
    return fx


def scene_verdict(cv, data, t, sc):
    fx = {}
    xt = dict(zip(data["elim_order"], VERDICT_X))
    win = VERDICT_WIN
    ew = ease_in_out(prog(t, win, 0.4))
    a = 1 - clamp(ew * 3)
    if a > 0.02:
        draw_q_card(cv, data, t, sc, karaoke=False, alpha=a, pop=False)
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
    tx, ty = W / 2, 1010
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
    shockwave(cv, W / 2, ty, t, win, GREEN, dur=0.7, rmax=620, width=18)
    spark_burst(cv, W / 2, ty, t, win, n=60, seed=11, cols=(GREEN, YELLOW, WHITE, CYAN))
    if t >= win + 0.12:
        kk = ease_out_back(prog(t, win + 0.12, 0.3))
        place(cv, check_sprite(150), W / 2, 700, scale=max(0.05, kk))
        d = ImageDraw.Draw(cv)
        d.text((W / 2, 545), "सही जवाब", font=get_font(96), fill=GREEN, anchor="mm", stroke_width=5,
               stroke_fill=(3, 20, 10))
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
        d.text((W / 2, 1490), "...और सही जवाब है", font=get_font(62), fill=mix(BG_BOTTOM, YELLOW, a_), anchor="mm",
               stroke_width=5, stroke_fill=(5, 10, 22))
    if t >= win + 0.45:
        k3 = ease_out_back(prog(t, win + 0.45, 0.3))
        place(cv, pill_sprite("आपका जवाब सही था? कमेंट करो!", 38, WHITE, (37, 60, 140), CYAN, reg=False),
              W / 2, 1360, scale=max(0.05, k3))
    return fx


EXAM_BADGES = [("RAILWAY", "RRB NTPC • Group D • ALP"), ("SSC", "GD • MTS • CGL • CHSL"), ("STATE", "Police • Patwari • TET")]


def exam_tick_t(sc, k):
    m = sc["marks"]
    base = m["tip"][0] if "tip" in m else (m["why"][1] - 0.6 if "why" in m else 1.0)
    return min(sc["dur"] - 0.5, base + 0.25 + 0.2 * k)


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
    """'क्यों?' - science wajah (Hindi + English) + yaad-trick + ye topic kin exams me aata hai."""
    fx = {}
    m = sc["marks"]
    k = ease_out_back(prog(t, 0, 0.35))
    place(cv, pill_sprite(f"सही जवाब: ({data['correct']}) {data['correct_text']}", 40, (5, 30, 15), GREEN, GREEN),
          W / 2, 300, scale=max(0.05, k))
    ew_, et_ = data.get("en_why", ""), data.get("en_tip", "")
    wtxt_h = text_block_h(data["why"], 880, 64, 4, 42)
    ewh = en_block_h(ew_, 860, 34) if ew_ else 0
    wh = wtxt_h + ewh + 130
    tip_h = (text_block_h(data["tip"], 840, 56, 2, 38) + en_block_h(et_, 820, 30) + 100) if data.get("tip") else 0
    has_img = bool(data.get("img_why"))
    badges_h = 0 if has_img else 190
    block = wh + (40 + tip_h if tip_h else 0) + 40 + badges_h
    top0 = 730 if has_img else 370
    top = max(top0, top0 + (1500 - top0 - block) / 2)
    if has_img:
        pan = img_panel(data["img_why"], 1000, 330, t, border=GREEN)
        if pan is not None:
            kp = ease_out_back(prog(t, 0.05, 0.4))
            place(cv, pan, W / 2, 535, scale=max(0.05, 0.9 + 0.1 * kp), alpha=clamp(kp * 1.5))
            place(cv, pill_sprite("चित्र से समझो", 30, (5, 30, 15), GREEN, GREEN), W / 2 - 360, 380,
                  scale=max(0.05, kp))
    wc = top + wh / 2
    t_move = (m["tip"][0] - 0.45) if (data.get("tip") and "tip" in m) else exam_tick_t(sc, 0) - 0.5
    mv = 1.0                                  # poora layout pehle se (khaali screen nahi)
    wc = wc + (880 - wc) * (1 - mv)
    place(cv, glow_sprite(420, GREEN, 50), W / 2, wc)
    place(cv, card_sprite(1000, int(wh), (14, 44, 32), GREEN, 6, 44), W / 2, wc, scale=0.92 + 0.08 * k, alpha=clamp(k))
    neon_border(cv, W / 2, wc, 1000, wh, t, color=GREEN, speed=0.35)
    place(cv, pill_sprite("क्यों?  WHY?", 44, (5, 30, 15), GREEN, GREEN), W / 2, wc - wh / 2, scale=max(0.05, k))
    wp, th = seg_progress(sc, "why", t)
    yb = draw_kinetic(cv, data["why"], W / 2, 880, 64, wp, max_lines=4, min_size=42, ghost=0.18,
                      center_y=wc - ewh / 2 + 10, th=th, hl_color=GREEN)
    if ew_:
        draw_en(cv, ew_, yb + 4, max_w=860, size=34, max_lines=3, color=(170, 235, 195))
    y = wc + wh / 2 + 40
    if data.get("tip") and "tip" in m:
        ts = 0.35                                 # card pehle se, shabd bolne pe chamakte
        th_ = tip_h
        if t >= ts:
            kt = ease_out_back(prog(t, ts, 0.3))
            place(cv, glow_sprite(320, YELLOW, 60), W / 2, y + th_ / 2)
            place(cv, card_sprite(960, int(th_), (46, 38, 10), YELLOW, 5, 36), W / 2, y + th_ / 2,
                  scale=max(0.05, 0.9 + 0.1 * kt), alpha=clamp(kt * 1.5))
            place(cv, pill_sprite("याद रखो  •  REMEMBER", 32, (30, 20, 0), YELLOW, YELLOW), W / 2, y,
                  scale=max(0.05, kt))
            tp, th2 = seg_progress(sc, "tip", t)
            eth = en_block_h(et_, 820, 30) if et_ else 0
            yb2 = draw_kinetic(cv, data["tip"], W / 2, 840, 56, max(tp, 0.001), max_lines=2, min_size=38,
                               ghost=0.3, center_y=y + th_ / 2 + 8 - eth / 2, th=th2)
            if et_:
                draw_en(cv, et_, yb2 + 2, max_w=820, size=30, color=(255, 225, 150))
        y += th_ + 40
    if data.get("img_why"):
        return fx
    # exams: Railway / SSC / State - trick ke saath hi (alag se intezaar nahi)
    y += 95
    t0 = 0.5
    if t >= t0:
        ka = clamp(prog(t, t0, 0.3) * 1.5)
        ImageDraw.Draw(cv).text((W / 2, y - 92), "ऐसे सवाल इन सब exams में आते हैं", font=get_font(34),
                                fill=mix(BG_BOTTOM, (210, 220, 240), ka), anchor="mm")
        for i, (nm, sub) in enumerate(EXAM_BADGES):
            ti = exam_tick_t(sc, i)
            on = t >= ti
            kb = ease_out_back(prog(t, t0 + 0.1 * i, 0.3))
            x = W / 2 + (i - 1) * 320
            if kb > 0.01:
                place(cv, exam_badge(nm, sub, on), x, y, scale=max(0.05, 0.85 + 0.15 * kb))
                if on:
                    place(cv, check_sprite(54), x + 140, y - 52, scale=max(0.05, ease_out_back(prog(t, ti, 0.25))))
    return fx


def en_block_h(text, max_w, size, max_lines=3):
    if not text:
        return 0
    _, s_, lines = fit_lines(text, max_w, max_lines, size, 22, reg=True)
    return int(s_ * 1.3) * min(len(lines), max_lines) + 6


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


@lru_cache(maxsize=2)
def whatsapp_card():
    """FREE Notes + Mock Test: WhatsApp number (end me)."""
    top, num = "FREE Notes + Mock Test", f"WhatsApp:  {WHATSAPP_NUMBER}"
    f1, f2 = get_font(40), get_font(56)
    w = int(max(text_w(top, f1), text_w(num, f2))) + 120
    h = 160
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=34, fill=(6, 95, 70, 250), outline=(90, 230, 160, 255), width=5)
    d.text((w / 2, 46), top, font=f1, fill=(200, 255, 225, 255), anchor="mm")
    d.text((w / 2, 112), num, font=f2, fill=WHITE + (255,), anchor="mm")
    return im


def scene_cta(cv, data, t, sc):
    """Agla sawal (options ke saath) -> 'जवाब पता है? कमेंट करो' + follow. Comment = agli reel ka engagement."""
    k = ease_out_back(prog(t, 0, 0.35))
    place(cv, brand_logo(92), W / 2 - 250, 320, scale=max(0.05, k))
    wm = brand_wordmark(50)
    place(cv, wm, W / 2 + 40, 320, scale=max(0.05, k))
    teaser = data.get("teaser") or ""
    d = ImageDraw.Draw(cv)
    if teaser:
        hs = headline_sprite("अगला सवाल - जवाब दो!", 74)
        place(cv, hs, W / 2, 470, scale=1.1 - 0.1 * ease_out_back(prog(t, 0.05, 0.35)))
        _, s2, ql = fit_lines(teaser, 880, 4, 56, 38)
        qh = int(s2 * 1.28) * len(ql) + 80
        qcy = 580 + qh / 2
        kt = ease_out_cubic(prog(t, 0.15, 0.35))
        place(cv, card_sprite(980, int(qh), (30, 20, 60), PURPLE, 4, 34), W / 2, qcy, alpha=kt)
        neon_border(cv, W / 2, qcy, 980, qh, t, color=PURPLE)
        draw_kinetic(cv, teaser, W / 2, 880, 56, 1.0, max_lines=4, min_size=38, karaoke=False, center_y=qcy,
                     color=mix(BG_BOTTOM, WHITE, kt))
        y = qcy + qh / 2 + 40
        for i, (L, txt) in enumerate(data.get("teaser_opts") or []):
            ti = 0.35 + 0.1 * i
            ki = ease_out_back(prog(t, ti, 0.3)) if t >= ti else 0.0
            if ki <= 0.01:
                continue
            cx = GRID_X[i % 2]
            cy = y + 90 + (i // 2) * 200
            place(cv, tile_sprite(L, txt, "", "vs", w=470, h=180), cx, cy, scale=0.85 + 0.15 * ki,
                  alpha=clamp(ki * 1.5))
        y += 2 * 200 + 30
        kc = ease_out_back(prog(t, 0.9, 0.3)) if t >= 0.9 else 0.0
        if kc > 0.01:
            place(cv, pill_sprite("जवाब पता है? कमेंट करो: A / B / C / D", 40, (30, 20, 0), YELLOW, ORANGE), W / 2, y + 20,
                  scale=max(0.05, kc) * (1 + 0.04 * math.sin(t * 8)))
        kf = ease_out_back(prog(t, 1.3, 0.3)) if t >= 1.3 else 0.0
        if kf > 0.01:
            place(cv, pill_sprite(f"FOLLOW {BRAND_HANDLE}  •  सही जवाब अगली रील में", 32, WHITE, (200, 30, 40),
                                  (255, 140, 140)), W / 2, y + 115, scale=max(0.05, kf))
        kw = ease_out_back(prog(t, 1.7, 0.3)) if t >= 1.7 else 0.0
        if kw > 0.01 and WHATSAPP_NUMBER:
            place(cv, whatsapp_card(), W / 2, y + 245, scale=max(0.05, kw) * (1 + 0.025 * math.sin(t * 6)))
    else:
        place(cv, follow_button(), W / 2, 700, scale=max(0.05, k))
    return {}


SCENES = {"hook": scene_hook, "question": scene_grid, "verdict": scene_verdict, "why": scene_why, "cta": scene_cta}


# ============================== RENDER ==============================

# ---------- THUMBNAIL (reel ka pehla frame = Instagram cover) ----------

THUMB_HOLD = 0.25       # itni der poora thumbnail, fir 0.25s me hook me ghul jaata hai


def make_thumbnail(data):
    """Aankh pakadne wala cover: chitra + bada 'N पेपर में आया!' + sawal ki jhalak + bada '?'."""
    if data.get("_thumb") is not None:
        return data["_thumb"]
    from PIL import ImageFilter
    src = _img_src(data["img_hook"]) if data.get("img_hook") else None
    if src is not None:
        sc = max(W / src.width, H / src.height)
        bg = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
        l, tp = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((l, tp, l + W, tp + H))
        bg = Image.blend(bg, Image.new("RGB", (W, H), (8, 12, 30)), 0.35)
    else:
        bg = background("red").crop((60, 60, 60 + W, 60 + H))
    cv = bg.convert("RGB")
    # upar-neeche andhera (text saaf padhe)
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = 0
        if y < 760:
            a = int(200 * (1 - y / 760))
        elif y > 1150:
            a = int(220 * (y - 1150) / (H - 1150))
        sd.line((0, y, W, y), fill=a)
    cv.paste(Image.new("RGB", (W, H), (5, 8, 20)), (0, 0), shade)
    d = ImageDraw.Draw(cv)
    # brand
    place(cv, brand_logo(84), W / 2 - 170, 430)
    wm = brand_wordmark(52)
    place(cv, wm, W / 2 + 50, 430)
    # bada headline
    head = data["hook"].rstrip("!") + "!"
    f, s_, lines = fit_lines(head, 980, 2, 118, 70)
    lh = int(s_ * 1.12)
    y0 = 600
    for k_, ln in enumerate(lines):
        d.text((W / 2, y0 + k_ * lh), " ".join(ln), font=f, fill=YELLOW, anchor="mm", stroke_width=10,
               stroke_fill=(20, 6, 0))
    y = y0 + lh * (len(lines) - 1) + lh / 2 + 70
    # sawal ki jhalak (safed card, kaala text = sabse zyada contrast)
    q = data["question"]
    words = q.split()
    short = " ".join(words[:12]) + (" ...?" if len(words) > 12 else "")
    fq, sq, ql = fit_lines(short, 860, 3, 70, 46)
    qh = int(sq * 1.25) * len(ql) + 80
    box = Image.new("RGBA", (980, int(qh)), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, 979, int(qh) - 1), radius=40, fill=(255, 255, 255, 245),
                                          outline=YELLOW + (255,), width=8)
    place(cv, box, W / 2, y + qh / 2, angle=-1.5)
    lhq = int(sq * 1.25)
    for k_, ln in enumerate(ql):
        d.text((W / 2, y + 40 + lhq * k_ + lhq / 2), " ".join(ln), font=fq, fill=(15, 18, 30), anchor="mm")
    # bada '?' sticker
    qs = pill_sprite("?", 84, WHITE, (210, 30, 45), (255, 200, 200))
    place(cv, qs, W - 120, y - 50, angle=14)
    yb = y + qh + 90
    lab = SUBJECT_STYLE.get(data["subject"], ("SCIENCE", CYAN))
    place(cv, pill_sprite(lab[0].split("•")[0].strip() + "  •  SCIENCE PYQ", 40, (10, 20, 30), lab[1], WHITE), W / 2, yb)
    place(cv, pill_sprite("जवाब बताओ:  A / B / C / D", 50, (30, 18, 0), YELLOW, ORANGE), W / 2, yb + 110)
    place(cv, pill_sprite("RAILWAY  •  SSC  •  STATE EXAMS", 32, WHITE, (170, 25, 40), (255, 140, 140)), W / 2,
          yb + 205)
    data["_thumb"] = cv
    return cv


def render_frame(sc, data, gt, total):
    t = gt - sc["start"]
    cv = bg_frame(sc["mood"], gt)
    nm = sc["name"]
    if nm in ("hook", "question", "verdict") and data.get("img_hook"):
        a_ = 0.45
        if nm == "hook":
            tq = sc["marks"]["q"][0] if "q" in sc["marks"] else 1.2
            a_ = 0.45 * ease_in_out(prog(t, tq - 0.1, 0.5))
        cv = draw_backdrop(cv, data["img_hook"], gt, a_)
    elif nm == "why" and data.get("img_why"):
        cv = draw_backdrop(cv, data["img_why"], gt, 0.35)
    fx = SCENES[sc["name"]](cv, data, t, sc) or {}
    draw_header(cv, data, gt, total, sc["name"])
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
    place(cv, watermark(), W / 2, 1690, alpha=0.55)
    # pehla pal = thumbnail (Instagram cover), fir zoom-out ke saath hook me ghulta hai
    if sc["name"] == "hook" and t < THUMB_HOLD + 0.25:
        th = make_thumbnail(data)
        if t < THUMB_HOLD:
            cv = th.copy()
        else:
            p = ease_in_out(prog(t, THUMB_HOLD, 0.25))
            z = 1 + 0.12 * p
            big = th.resize((int(W * z), int(H * z)), Image.BILINEAR)
            ox, oy = (big.width - W) // 2, (big.height - H) // 2
            cv = Image.blend(big.crop((ox, oy, ox + W, oy + H)), cv, p)
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
    voices = make_voices(specs, int(data.get("episode") or 0))
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
           "-crf", str(VIDEO_CRF), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-r", str(FPS), "-shortest",
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
                if tt < 0.12:
                    frame = rgb_split(frame, 16 * (1 - tt / 0.12))
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
        f"🔬 {BRAND} | {SERIES} | {data['question']}",
        "",
        asked,
    ] + ([f"🇬🇧 {data['en_question']}"] if data.get("en_question") else []) + [
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

def _upload_once(video_file, caption):
    """Ek koshish: container -> (10s ruko) -> rupload -> FINISHED -> publish."""
    r = requests.post(f"{GRAPH}{IG_USER_ID}/media",
                      data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                            "thumb_offset": "0",
                            "access_token": IG_ACCESS_TOKEN}, timeout=60).json()
    cid = r.get("id")
    if not cid:
        raise RuntimeError(f"IG container nahi bana: {r}")
    print("  IG container:", cid)
    time.sleep(10)                                  # turant upload = ProcessingFailedError (container taiyar nahi)
    up_url = r.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{GRAPH_VER}/{cid}"
    size = os.path.getsize(video_file)
    with open(video_file, "rb") as vf:
        data = vf.read()
    up = None
    for k in range(3):                              # rupload kabhi-kabhi pehli baar mana karta hai
        up = requests.post(up_url, headers={"Authorization": f"OAuth {IG_ACCESS_TOKEN}", "offset": "0",
                                            "file_size": str(size), "Content-Type": "application/octet-stream"},
                           data=data, timeout=600)
        print(f"  upload try {k + 1}: HTTP {up.status_code} {up.text[:150]}")
        if up.status_code < 300:
            break
        time.sleep(15 * (k + 1))
    if up.status_code >= 300:
        raise RuntimeError(f"IG upload fail: {up.status_code} {up.text[:200]}")
    status = ""
    for _ in range(40):
        time.sleep(10)
        st = requests.get(f"{GRAPH}{cid}", params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN},
                          timeout=30).json()
        status = st.get("status_code", "")
        print("  IG processing:", status)
        if status == "FINISHED":
            break
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG processing {status}: {st}")
    if status != "FINISHED":
        raise RuntimeError("IG processing time-out")
    pub = {}
    for k in range(3):
        pub = requests.post(f"{GRAPH}{IG_USER_ID}/media_publish",
                            data={"creation_id": cid, "access_token": IG_ACCESS_TOKEN}, timeout=60).json()
        if pub.get("id"):
            break
        print("  publish dobara:", pub)
        time.sleep(20)
    if not pub.get("id"):
        raise RuntimeError(f"IG publish fail: {pub}")
    return pub["id"]


def post_reel(video_file, caption):
    """Poori upload 3 baar tak (har baar naya container). Fail = exception (progress aage nahi badhta)."""
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("IG secrets nahi - post skip (reel bani hai).")
        return None
    last = None
    for attempt in range(3):
        try:
            pid = _upload_once(video_file, caption)
            print("INSTAGRAM PE POST HO GAYA:", pid)
            return pid
        except Exception as exc:
            last = exc
            print(f"  Instagram koshish {attempt + 1} fail:", str(exc)[:300])
            time.sleep(30)
    raise RuntimeError(f"Instagram upload 3 baar fail: {last}")


# ============================== CAROUSEL (har 3 reel ke baad) ==============================

CAROUSEL_EVERY = 3
CAROUSEL_DIR = "carousels"
CAROUSEL_KEEP = 40                 # repo halka rahe: sirf aakhri itne carousel folder
CW, CH = 1080, 1350                # Instagram carousel (4:5)


def save_ready(video, caption, ep):
    """Manual mode: reel + caption repo ke ready_reels/ me (aakhri READY_KEEP hi rahti hain)."""
    import shutil
    os.makedirs(READY_DIR, exist_ok=True)
    name = f"reel_{ep:04d}"
    shutil.copy(video, os.path.join(READY_DIR, name + ".mp4"))
    thumb = os.path.join(os.path.dirname(video), "thumbnail.jpg")
    if os.path.exists(thumb):
        shutil.copy(thumb, os.path.join(READY_DIR, name + "_thumbnail.jpg"))
    Path(os.path.join(READY_DIR, name + "_caption.txt")).write_text(caption, encoding="utf-8")
    vids = sorted(x for x in os.listdir(READY_DIR) if x.endswith(".mp4"))
    for x in vids[:-READY_KEEP]:
        for f in (x, x.replace(".mp4", "_caption.txt"), x.replace(".mp4", "_thumbnail.jpg")):
            try:
                os.remove(os.path.join(READY_DIR, f))
            except OSError:
                pass
    print("MANUAL MODE: reel ready_reels/ me rakhi (Instagram pe post nahi hui):", name + ".mp4")


def carousel_item(data):
    return {k: data[k] for k in ("episode", "subject", "question", "options", "correct", "correct_text", "why",
                                 "tip", "exams", "times_asked", "topic")}


def _c_base(mood="blue"):
    bg = background(mood)
    im = bg.crop((60, 300, 60 + CW, 300 + CH)).convert("RGB")
    d = ImageDraw.Draw(im)
    place(im, brand_logo(64), 70, 70)
    wm = brand_wordmark(38)
    place(im, wm, 112 + wm.width / 2, 70)
    tag = pill_sprite("SCIENCE PYQ  |  RAILWAY • SSC • STATE", 22, WHITE, (22, 101, 52), GREEN)
    place(im, tag, CW - 50 - tag.width / 2, 70)
    d.line((50, 118, CW - 50, 118), fill=(45, 62, 90), width=2)
    return im


def _c_footer(im, i, n):
    d = ImageDraw.Draw(im)
    for k in range(n):
        x = CW / 2 + (k - (n - 1) / 2) * 30
        r = 9 if k == i else 6
        d.ellipse((x - r, CH - 60 - r, x + r, CH - 60 + r), fill=YELLOW if k == i else (80, 95, 125))
    d.text((CW - 50, CH - 60), BRAND_HANDLE, font=get_font(26), fill=(150, 165, 190), anchor="rm")
    if i < n - 1:
        d.text((50, CH - 60), "स्वाइप करो  >>", font=get_font(28), fill=YELLOW, anchor="lm")


def _c_text(im, text, cy, max_w, size, max_lines, color=WHITE, min_size=30, reg=False):
    f, s_, lines = fit_lines(text, max_w, max_lines, size, min_size, reg=reg)
    lh = int(s_ * 1.3)
    d = ImageDraw.Draw(im)
    top = cy - lh * len(lines) / 2
    for k, ln in enumerate(lines[:max_lines]):
        d.text((CW / 2, top + k * lh + lh / 2), " ".join(ln), font=f, fill=color, anchor="mm")
    return lh * len(lines)


def _c_cover(items, i, n):
    im = _c_base("red")
    d = ImageDraw.Draw(im)
    place(im, glow_sprite(320, YELLOW, 60), CW / 2, 300)
    d.text((CW / 2, 250), "3 SCIENCE PYQ", font=get_font(104), fill=YELLOW, anchor="mm", stroke_width=6,
           stroke_fill=(20, 8, 0))
    d.text((CW / 2, 360), "तीनों सही कर पाओगे?", font=get_font(64), fill=WHITE, anchor="mm")
    y = 470
    for k, it in enumerate(items):
        q = it["question"]
        short = " ".join(q.split()[:9]) + (" ..." if len(q.split()) > 9 else "")
        place(im, card_sprite(960, 150, (22, 42, 72), (90, 130, 190), 4, 30), CW / 2, y + 75)
        d.ellipse((90, y + 45, 150, y + 105), fill=CYAN)
        d.text((120, y + 76), str(k + 1), font=get_font(40), fill=(8, 16, 30), anchor="mm")
        f, s_, lines = fit_lines(short, 800, 2, 40, 28)
        lh = int(s_ * 1.25)
        for j, ln in enumerate(lines[:2]):
            d.text((180, y + 75 + (j - (min(2, len(lines)) - 1) / 2) * lh), " ".join(ln), font=f, fill=WHITE,
                   anchor="lm")
        y += 185
    place(im, pill_sprite("जवाब + वजह अगली स्लाइड में", 36, (30, 20, 0), YELLOW, ORANGE), CW / 2, y + 60)
    _c_footer(im, i, n)
    return im


def _c_question(it, k, i, n):
    im = _c_base("blue")
    d = ImageDraw.Draw(im)
    lab = SUBJECT_STYLE.get(it["subject"], ("SCIENCE", CYAN))
    chip = pill_sprite(f"PYQ {k}/3  •  {it['subject']}  •  {', '.join(it['exams'][:2])}", 26, lab[1], (14, 26, 44),
                       lab[1])
    place(im, chip, CW / 2, 175)
    qh = text_block_h(it["question"], 920, 56, 4, 36) + 70
    place(im, card_sprite(980, int(qh), (16, 30, 58), (70, 120, 190), 3, 30), CW / 2, 230 + qh / 2)
    _c_text(im, it["question"], 230 + qh / 2, 920, 56, 4, min_size=36)
    y = 230 + qh + 30
    for L, txt in it["options"]:
        ok = L == it["correct"]
        place(im, card_sprite(960, 100, (14, 60, 36) if ok else (22, 38, 62), GREEN if ok else (60, 85, 120),
                              5 if ok else 3, 26, shadow=False), CW / 2, y + 50)
        d.ellipse((78, y + 22, 134, y + 78), fill=GREEN if ok else (70, 95, 135))
        d.text((106, y + 50), L, font=get_font(34), fill=(8, 16, 30), anchor="mm")
        f, s_, ls = fit_lines(txt, 760, 1, 44, 28)
        d.text((160, y + 50), " ".join(ls[0]) if ls else txt, font=f, fill=WHITE if ok else (210, 220, 235), anchor="lm")
        if ok:
            place(im, check_sprite(60), CW - 98, y + 50)
        y += 114
    y += 14
    wh = text_block_h(it["why"], 880, 44, 4, 30) + 90
    place(im, card_sprite(980, int(wh), (14, 44, 32), GREEN, 4, 30, shadow=False), CW / 2, y + wh / 2)
    place(im, pill_sprite("क्यों?", 30, (5, 30, 15), GREEN, GREEN), CW / 2, y)
    _c_text(im, it["why"], y + wh / 2 + 8, 880, 44, 4, min_size=30)
    y += wh + 30
    if it.get("tip") and y < CH - 170:
        place(im, pill_sprite("याद रखो: " + it["tip"], 32, (30, 20, 0), YELLOW, ORANGE), CW / 2, y + 30)
    _c_footer(im, i, n)
    return im


def _c_end(items, i, n):
    im = _c_base("purple")
    d = ImageDraw.Draw(im)
    place(im, glow_sprite(220, YELLOW, 80), CW / 2, 330)
    place(im, brand_logo(230), CW / 2, 330)
    wm = brand_wordmark(76)
    place(im, wm, CW / 2, 510)
    d.text((CW / 2, 580), BRAND_TAGLINE, font=get_font(36), fill=CYAN, anchor="mm")
    d.text((CW / 2, 700), "आपके कितने सही हुए?", font=get_font(62), fill=WHITE, anchor="mm")
    place(im, pill_sprite("कमेंट करो:  3/3  या  2/3", 44, (30, 20, 0), YELLOW, ORANGE), CW / 2, 800)
    place(im, follow_button(), CW / 2, 960)
    place(im, pill_sprite("SAVE करो - Exam से पहले Revision", 34, WHITE, (37, 60, 140), CYAN), CW / 2, 1100)
    if WHATSAPP_NUMBER:
        place(im, pill_sprite(f"Free Test / Notes: WhatsApp {WHATSAPP_NUMBER}", 30, WHITE, (6, 95, 70),
                              (60, 200, 150)), CW / 2, 1180)
    _c_footer(im, i, n)
    return im


def make_carousel(items, number):
    folder = os.path.join(CAROUSEL_DIR, f"carousel_{number:03d}_{time.strftime('%Y-%m-%d')}")
    os.makedirs(folder, exist_ok=True)
    n = len(items) + 2
    slides = [_c_cover(items, 0, n)] + [_c_question(it, k + 1, k + 1, n) for k, it in enumerate(items)] \
        + [_c_end(items, n - 1, n)]
    for k, im in enumerate(slides):
        im.save(os.path.join(folder, f"slide_{k + 1}.jpg"), quality=88, optimize=True)
    cap = [f"📚 {BRAND} | 3 SCIENCE PYQ - तीनों सही कर पाओगे?", ""]
    for k, it in enumerate(items):
        cap.append(f"{k + 1}. {it['question']}  ->  ({it['correct']}) {it['correct_text']}")
    cap += ["", "🎯 Railway, SSC, State exams - जहाँ भी Science है, ऐसे सवाल आते हैं।",
            "💬 कमेंट करो आपके कितने सही हुए: 3/3?", f"🔔 Follow {BRAND_HANDLE} | 📥 Save करो", "", HASHTAGS]
    Path(os.path.join(folder, "caption.txt")).write_text("\n".join(cap), encoding="utf-8")
    # purane carousel hatao (repo halka)
    try:
        olds = sorted(x for x in os.listdir(CAROUSEL_DIR) if x.startswith("carousel_"))
        for x in olds[:-CAROUSEL_KEEP]:
            import shutil
            shutil.rmtree(os.path.join(CAROUSEL_DIR, x), ignore_errors=True)
    except Exception:
        pass
    print("CAROUSEL TAIYAR:", folder)
    return folder


def carousel_step(st, data):
    """Har post ke baad: sawal queue me; 3 ho gaye to carousel folder banao."""
    q = st.setdefault("carousel_queue", [])
    q.append(carousel_item(data))
    if len(q) >= CAROUSEL_EVERY:
        try:
            st["carousel_count"] = st.get("carousel_count", 0) + 1
            make_carousel(q[:CAROUSEL_EVERY], st["carousel_count"])
            st["carousel_queue"] = q[CAROUSEL_EVERY:]
        except Exception as exc:
            print("  Carousel nahi bana (agli baar):", str(exc)[:200])


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
    ap.add_argument("--carousel-test", action="store_true")
    args = ap.parse_args()

    bank = load_bank()
    st = load_progress()
    if args.carousel_test:          # jaanch: pehle 3 sawal se ek carousel (progress nahi badalta)
        items = [carousel_item(prepare_data(q, None, q["seq"])) for q in bank[:3]]
        make_carousel(items, 0)
        return
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
    imgs = make_images(chosen, ai)
    data = prepare_data(chosen, ai, ep, nxt, imgs)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    if args.preview:
        build_reel(data, out, preview_dir="preview")
        return
    build_reel(data, out)
    try:
        make_thumbnail(data).save(os.path.join(OUTPUT_DIR, "thumbnail.jpg"), quality=92)
    except Exception as exc:
        print("  thumbnail save nahi hua:", str(exc)[:100])
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
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    elif not post_reel(out, caption):
        save_progress(st)
        return
    st["posted"].append(chosen["id"])
    carousel_step(st, data)
    st["episode"] = ep
    st["next_seq"] = chosen["seq"] + 1
    st["last"] = {"seq": chosen["seq"], "id": chosen["id"], "time": time.strftime("%Y-%m-%d %H:%M")}
    save_progress(st)


if __name__ == "__main__":
    main()
