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
BRAND_TAGLINE = "एक मिनट, एक PYQ - पक्का!"        # naam (Minute) se juda signature line, har jagah
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
    "History": ("HISTORY  •  इतिहास", (230, 150, 70)),
    "Polity": ("POLITY  •  राजव्यवस्था", (130, 160, 255)),
    "Geography": ("GEOGRAPHY  •  भूगोल", (60, 200, 170)),
    "Economics": ("ECONOMICS  •  अर्थशास्त्र", (250, 200, 60)),
    "Environment": ("ENVIRONMENT  •  पर्यावरण", (120, 210, 90)),
    "Traditional GK": ("GK  •  सामान्य ज्ञान", (240, 120, 160)),
    "Computer": ("COMPUTER  •  कंप्यूटर", (120, 200, 255)),
}
SCIENCE_SUBJ = ("Physics", "Chemistry", "Biology")


def series_of(subject):
    """Ribbon/header ka naam: Science ke liye 'SCIENCE PYQ', baaki 'HISTORY PYQ' jaisa."""
    if subject in SCIENCE_SUBJ:
        return SERIES
    return SUBJECT_STYLE.get(subject, ("GK",))[0].split("•")[0].strip() + " PYQ"


def subj_word(subject):
    """Chhota Hindi/English shabd (chips/caption me): Science / इतिहास / GK ..."""
    if subject in SCIENCE_SUBJ:
        return "Science"
    return {"Traditional GK": "GK", "Computer": "Computer"}.get(subject, SUBJECT_STYLE.get(subject, ("", ))[0].split("•")[-1].strip())


# ============================== TEXT ==============================

_ALLOWED = re.compile(r"[^\u0900-\u097F\u0020-\u007E\u00A0-\u00FF\u2010-\u2027\u20B9\u2126\u03A9\u03B1-\u03C9"
                      r"\u00D7\u00F7\u2192\u2212\u221A\u2248\u2264\u2265\u200C\u200D\u2070\u2074-\u2079]")


_SUP = {"1": "", "2": "²", "3": "³"}
_SUPD = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
_UNSUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


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
    # book me ghaat chhoot gaya: 6 × 1024 kg -> 6 × 10²⁴ kg, 3 × 108 m/s -> 3 × 10⁸ m/s
    t = re.sub(r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*×\s*10([1-9]\d?)(?![\d.])",
               lambda m: f"{m.group(1)} × 10" + m.group(2).translate(_SUPD), t)
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
    st["posted"] = st["posted"][-8000:]
    if COMMENT_LOG:
        st["comment_log"] = dict(COMMENT_LOG)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


# ============================== AI: SAFAI + WAJAH (optional) ==============================

ENRICH_PROMPT = """You prepare ONE previous-year General Studies MCQ (Science / History / Polity / Geography / Economics / GK) (Indian govt exams: Railway RRB Group D, SSC, State exams) for a
short Hindi Instagram reel. The Hindi text was auto-converted from an old font and MAY contain small spelling errors.

QUESTION (Hindi): {q}
OPTIONS: (a) {a} | (b) {b} | (c) {c} | (d) {d}
OFFICIAL ANSWER KEY: ({ans}) {ans_text}
REFERENCE EXPLANATION (may be noisy): {exp}

Tasks - return ONLY JSON:
{{
 "ok": true/false,            // false if the answer key is WRONG, OUTDATED today (e.g. counts/records/officials that changed),
                              // the text has broken math (lost superscripts like '1024' for 10^24), needs a figure/table, or is unclear
 "problem": "",               // short reason if ok=false
 "question": "...",           // same question, Hindi, ONLY fix spelling/spacing (do NOT change meaning, numbers or units). Use ____ for blanks.
 "options": {{"a":"..","b":"..","c":"..","d":".."}},   // same 4 options, same order, only spelling fixed, keep numbers/units/formulas exactly
 "speak_question": "...",     // the question as it should be SPOKEN in Hindi (Devanagari): spell symbols/units/formulas in words
                              // (e.g. 'm/s2' -> 'मीटर प्रति सेकंड स्क्वायर', 'CO2' -> 'सी ओ टू', 'pH' -> 'पी एच', 'SI' -> 'एस आई').
                              // BLANKS (____): NEVER say 'खाली स्थान' - rephrase naturally as a question with 'कितने/कौन सा/क्या'
                              // e.g. '____ जन्तुओं का सबसे बड़ा समूह है' -> 'जन्तुओं का सबसे बड़ा समूह कौन सा है?'
 "speak_answer": "...",       // the correct option text as spoken Hindi (same rule)
 "why": "...",                // ONE simple Hindi line (max 18 words): the reason / fact why the key is correct. No book/coaching names.
 "level": "easy|medium|hard", // how hard this is for an average RRB Group D aspirant
 "visual_options": true/false, // true ONLY if all 4 options are concrete things (plants, animals, objects, foods, places, body parts) that a picture can show without any text; false for numbers, years, laws/articles, people, abstract terms
 "img_options": {{"a":"..","b":"..","c":"..","d":".."}}, // if visual_options: ENGLISH prompt (max 15 words) for a simple clear picture of that option alone
 "trap": "...",               // Hindi, max 16 words: which WRONG option looks tempting and why it is wrong (e.g. '(C) तिल भी फसल है, पर फलीदार नहीं')
 "tip": "...",                // Hindi memory trick / exam tip, max 8 words (can be a short formula like 'दाब = बल / क्षेत्रफल')
 "topic": "...",              // 1-3 word Hindi topic name (e.g. 'प्रकाश का अपवर्तन')
 "en_question": "...",        // short English translation of the question (max 20 words)
 "en_why": "...",             // English translation of 'why' (max 18 words)
 "img_hook": "...",           // ENGLISH image prompt (max 40 words): a striking, curiosity-making real-world scene about this
                              // question's topic WITHOUT showing or hinting the answer. Concrete objects, dramatic angle. No text.
 "img_why": "...",            // ENGLISH image prompt (max 40 words): a clear visual that SHOWS the idea/fact behind the correct
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
        out = {k: js.get(k) for k in ("why", "tip", "topic", "en_question", "en_why", "en_tip", "img_hook", "img_why", "level", "trap", "visual_options", "img_options")}
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
    (r"\bm\s*/\s*s²", "मीटर प्रति सेकंड स्क्वायर"), (r"\bm²", "मीटर स्क्वायर"), (r"\bm³", "मीटर क्यूब"),
    (r"\bcm²", "सेंटीमीटर स्क्वायर"), (r"\bcm³", "सेंटीमीटर क्यूब"),
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
    t = re.sub(r"10([⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: " 10 की घात " + m.group(1).translate(_UNSUP) + " ", t)
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
    # 1 baar wala: sirf "paper me aaya" kamzor hook tha -> chunauti (sach hi, koi nakli % nahi)
    return [f"RRB {y} का सवाल - 3 सेकंड में बताओ!", f"Railway {y} में आया - आप कर पाओगे?",
            f"Exam में पूछा गया - जवाब दो!"][ep % 3].replace("  ", " ")


# ---------- Cloudflare Workers AI: topic ka sundar chitra ----------

IMG_STYLE = ("cinematic 3D render, vibrant colors, dramatic rim lighting, ultra detailed, depth of field, "
             "high-end educational science illustration, clean composition. absolutely no text, no letters, "
             "no words, no numbers, no watermark, no logo")
SUBJECT_SCENE = {"Physics": "physics laboratory with glowing light beams, magnets and electric sparks",
                 "Chemistry": "chemistry laboratory with colorful glowing flasks, bubbling liquids and molecules",
                 "Biology": "microscopic world of living cells, plants and the human body, bioluminescent",
                 "History": "ancient Indian fort, old manuscripts and historic monuments at golden hour",
                 "Polity": "Indian Parliament building, constitution book and scales of justice, dramatic light",
                 "Geography": "planet earth from space, mountains, rivers and a glowing world map",
                 "Economics": "Indian rupee coins, bank building and rising graph arrows, cinematic",
                 "Environment": "lush forest, wildlife and clean river under blue sky, nature conservation",
                 "Traditional GK": "colorful Indian festival, culture, dance and heritage symbols",
                 "Computer": "glowing computer chip, keyboard and digital network lines"}


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


SCIENCE_EXAMS = ["RRB NTPC", "SSC GD", "SSC CGL", "SSC CHSL", "SSC MTS", "RRB ALP", "State Police", "Patwari",
                 "State PSC"]


def also_exams(q):
    """GS wale doosre exams (rotate) - hook me EK chhoti line (pehle 2 line ki chips bheed karti thi)."""
    rnd = random.Random(q["id"] + "x")
    return rnd.sample(SCIENCE_EXAMS, 2)


# reel ke liye bahut lamba sawal/option = pehle 2 sec me padha nahi jaata -> reel me nahi (bank me rehta hai)
REEL_MAX_Q_WORDS = 22
REEL_MAX_OPT_WORDS = 6


def reel_friendly(q):
    if len(q["question"].split()) > REEL_MAX_Q_WORDS:
        return False
    return all(len(str(o).split()) <= REEL_MAX_OPT_WORDS for o in q["options"].values())


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
        "exam_raw": today_exam(q) or ((q.get("exams") or [""])[0] if isinstance(q.get("exams"), list) else ""),
        "today_exam": today_exam(q),
        "level": str((ai or {}).get("level") or "").lower(),
        "trap": clean_text((ai or {}).get("trap") or "") if _hi_ok((ai or {}).get("trap") or "", 20) else "",
        "audience": audience_of(ep),
        "toppers": [],
        "also_exams": also_exams(q),
        "series": series_of(q["subject"]),
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
        {"name": "verdict", "mood": "green", "tail": 0.1, "min": 1.9, "delay": 0.5,
         "segs": [("rev", ans_say, ans_say)]},
        {"name": "why", "mood": "blue", "tail": 0.4, "min": 2.6,
         "segs": [("why", data["why"], why_say)]
                 + ([("tip", data["tip"], to_speech("याद रखो, " + data["tip"]))] if data.get("tip") else []),
         "read": [("why", data["why"])]},
        # ant chhota: lamba follow + WhatsApp wala bolna watch-% girata tha (WhatsApp ab caption me)
        {"name": "cta", "mood": "purple", "tail": 1.0, "min": 3.0,
         "segs": [("cta", "अगला सवाल! जवाब पता है तो कमेंट करो।",
                   "अगले सवाल का जवाब पता है? कमेंट करो!")]},
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


POSTER_TAIL = 0.4                   # reel ke ant me poster/cover kitni der
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
    # sabse aakhir me poster (cover) ke kuch frame: Instagram cover thumb_offset se yahi uthata hai.
    # Pehle poster video ke SHURU me tha -> feed me reel 'photo/ad' lagti thi aur log 1 sec me skip karte the.
    timeline.append({"index": len(timeline), "name": "poster", "mood": "blue", "start": cur, "dur": POSTER_TAIL,
                     "vdur": 0.0, "marks": {}, "wt": {}, "lead": 0.0})
    data["_timer_end"] = next((s["start"] for s in timeline if s["name"] == "verdict"), 6.0)
    cur += POSTER_TAIL
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
SEAMLESS = ("question", "verdict", "poster")


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
    tag = data.get("series", SERIES)
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
    txt = f"{ep}   |   {EXAMS_LINE}"
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


def draw_timer(cv, data, gt):
    """Neeche khaali hoti 'टाइम' patti: frame 1 se chalti hai -> rukne ki wajah (jawab aane tak)."""
    end = float(data.get("_timer_end") or 6.0)
    if gt >= end:
        return
    p = clamp(1 - gt / max(0.5, end))
    x0, x1, y = 150, W - 90, 1585
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle((x0, y - 13, x1, y + 13), radius=13, fill=(30, 40, 62))
    col = GREEN if p > 0.5 else (YELLOW if p > 0.25 else RED)
    cur = x0 + (x1 - x0) * p
    d.rounded_rectangle((x0, y - 13, max(x0 + 26, cur), y + 13), radius=13, fill=col)
    place(cv, glow_sprite(26, col, 220), cur, y)
    d.text((95, y), "टाइम", font=get_font(30), fill=col, anchor="mm")


def scene_hook(cv, data, t, sc):
    """
    Pehla frame hi poora sawal: chamakti hook-line + bada sawal + chaaron options 0.25s me uchhal ke,
    neeche khaali hoti time-patti. (Pehle: poster -> chips ki 2 line -> chitra -> options ~1.5s baad aate the.)
    """
    fx = {}
    hy = 300
    place(cv, rays_sprite(), W / 2, hy, angle=t * 25, scale=0.7)
    hs = headline_sprite(data["hook"], 82)
    punch = 1.08 - 0.08 * ease_out_back(prog(t, 0, 0.3))
    shockwave(cv, W / 2, hy, t, 0.0, YELLOW)            # dhamaka headline ke PEECHE (shabd na dhake)
    spark_burst(cv, W / 2, hy, t, 0.0)
    place(cv, hs, W / 2, hy, scale=punch * (1 + 0.018 * math.sin(t * 7)))
    if t < 0.12:
        fx["shake"] = 9
    # EK chhoti line: asli paper + 2 bade exam (sawal ki ahmiyat), baaki bheed hata di
    real = data["exams"][0] if data.get("exams") else "RRB Group D"
    row = [pill_sprite("पूछा गया: " + real, 28, (30, 18, 0), YELLOW, ORANGE)] + \
          [pill_sprite(e, 28, WHITE, (30, 45, 80), (90, 120, 180)) for e in data.get("also_exams", [])[:2]]
    tot = sum(c.width for c in row) + 12 * (len(row) - 1)
    fit = min(1.0, 1000 / max(1, tot))
    x = W / 2 - tot * fit / 2
    yy = hy + hs.height / 2 + 30
    for i, c in enumerate(row):
        kc = ease_out_back(prog(t, 0.1 + 0.06 * i, 0.25))
        place(cv, c, x + c.width * fit / 2, yy, scale=max(0.05, kc) * fit)
        x += (c.width + 12) * fit
    draw_q_card(cv, data, t, sc)
    # chaaron options TURANT (0.08s se): scroll karne wala pehle second me hi sochne lage
    t_opt = 0.08
    for i, (l, txt) in enumerate(data["options"]):
        gx, gy = grid_pos(i)
        ti_ = t_opt + 0.08 * i
        ki = ease_out_back(prog(t, ti_, 0.3)) if t >= ti_ else 0.0
        if ki <= 0.01:
            continue
        place(cv, tile_sprite(l, txt, data["en_opt"].get(l, ""), "normal"), gx, gy + 120 * (1 - min(ki, 1)),
              scale=0.85 + 0.15 * ki, alpha=clamp(ki * 1.5))
        if t > t_opt + 0.6:
            sheen(cv, gx, gy, TILE_W, TILE_H, t, period=2.0, offset=0.25 * i, strength=40)
    kc = ease_out_back(prog(t, 0.9, 0.3)) if t >= 0.9 else 0.0
    if kc > 0.01:
        place(cv, pill_sprite("आपका जवाब? कमेंट करो!", 40, (30, 20, 0), YELLOW, ORANGE), W / 2, 1505,
              scale=max(0.05, kc) * (1 + 0.03 * math.sin(t * 9)))
    draw_timer(cv, data, sc["start"] + t)
    return fx


def scene_grid(cv, data, t, sc):
    """Wahi screen (bina cut): 3-2-1 countdown, options pe scan-roshni."""
    fx = {}
    d = ImageDraw.Draw(cv)
    d.text((W / 2, 330), "अपना जवाब लॉक करो!", font=get_font(76), fill=YELLOW, anchor="mm", stroke_width=6,
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
    draw_timer(cv, data, sc["start"] + t)
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
    top, bot = f"FOLLOW {BRAND_HANDLE}", "रोज़ नए PYQ"
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
    else:
        place(cv, follow_button(), W / 2, 700, scale=max(0.05, k))
    return {}


SCENES = {"hook": scene_hook, "question": scene_grid, "verdict": scene_verdict, "why": scene_why, "cta": scene_cta}


# ============================== RENDER ==============================

# ---------- THUMBNAIL (reel ke AAKHRI frame = Instagram cover, thumb_offset se) ----------



# ---- thumbnail ke design-tukde (poster style: brush patti, chaunka emoji, starburst sticker) ----

def brush_band(w, h, color, seed=1, tilt=-2.0):
    """Paint-brush jaisi patti: khurdure kinare + halki dhaariyaan."""
    rng = random.Random(seed)
    W2, H2 = w + 60, h + 60
    m = Image.new("L", (W2, H2), 0)
    d = ImageDraw.Draw(m)
    top, bot = [], []
    for k in range(0, w + 1, 18):
        top.append((30 + k, 30 + rng.uniform(-10, 12)))
        bot.append((30 + k, 30 + h + rng.uniform(-12, 10)))
    left = [(30 + rng.uniform(-28, 6), 30 + y) for y in range(h, -1, -max(8, h // 6))]
    right = [(30 + w + rng.uniform(-6, 28), 30 + y) for y in range(0, h + 1, max(8, h // 6))]
    d.polygon(top + right + bot[::-1] + left, fill=255)
    for _ in range(14):                                   # bahar nikle brush ke reshe
        y = rng.uniform(40, 20 + h)
        x0 = rng.choice([rng.uniform(0, 40), rng.uniform(w, w + 50)])
        d.line((x0, y, x0 + rng.uniform(-60, 60), y + rng.uniform(-3, 3)), fill=255, width=rng.randint(2, 6))
    band = Image.new("RGBA", (W2, H2), color + (255,))
    arr = np.array(band).astype(np.int16)
    yy = np.arange(H2)[:, None]
    streak = (np.sin(yy * 0.9 + rng.uniform(0, 6)) * 9 + np.random.default_rng(seed).normal(0, 7, (H2, W2)))
    for c in range(3):
        arr[..., c] = np.clip(arr[..., c] + streak, 0, 255)
    band = Image.fromarray(arr.astype(np.uint8), "RGBA")
    band.putalpha(m)
    return band.rotate(tilt, resample=Image.BICUBIC, expand=True)


def shock_emoji(size=230):
    """Chaunka hua emoji (code se bana): khule muh, badi aankhen, laal gaal."""
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(S // 2, 0, -2):                        # gol chehra, upar roshni
        k = r / (S / 2)
        col = mix((255, 236, 120), (245, 170, 20), k)
        d.ellipse((S / 2 - r, S / 2 - r + (1 - k) * -S * 0.06, S / 2 + r, S / 2 + r), fill=col + (255,))
    d.ellipse((S * 0.12, S * 0.56, S * 0.30, S * 0.68), fill=(255, 120, 110, 150))
    d.ellipse((S * 0.70, S * 0.56, S * 0.88, S * 0.68), fill=(255, 120, 110, 150))
    for ex in (0.33, 0.67):
        d.ellipse((S * (ex - 0.11), S * 0.24, S * (ex + 0.11), S * 0.50), fill=WHITE + (255,), outline=(60, 30, 0, 255),
                  width=S // 80)
        d.ellipse((S * (ex - 0.05), S * 0.32, S * (ex + 0.05), S * 0.44), fill=(25, 15, 10, 255))
        d.ellipse((S * (ex - 0.02), S * 0.33, S * (ex + 0.01), S * 0.36), fill=WHITE + (255,))
        d.arc((S * (ex - 0.13), S * 0.10, S * (ex + 0.13), S * 0.28), 200, 340, fill=(90, 45, 0, 255), width=S // 40)
    d.ellipse((S * 0.38, S * 0.60, S * 0.62, S * 0.88), fill=(120, 20, 25, 255), outline=(70, 10, 10, 255), width=S // 90)
    d.ellipse((S * 0.43, S * 0.75, S * 0.57, S * 0.86), fill=(230, 80, 90, 255))
    return im.resize((size, size), Image.LANCZOS)


def starburst(text, size=230, fill=(220, 30, 40), fg=WHITE, spikes=14, angle=-12):
    S = size
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    pts = []
    for i in range(spikes * 2):
        r = c * (0.98 if i % 2 == 0 else 0.78)
        a = math.pi * i / spikes
        pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
    d.polygon(pts, fill=fill + (255,), outline=(255, 230, 120, 255))
    lines = text.split("\n")
    f = get_font(int(S * 0.2))
    for k, ln in enumerate(lines):
        d.text((c, c + (k - (len(lines) - 1) / 2) * S * 0.22), ln, font=f, fill=fg + (255,), anchor="mm",
               stroke_width=3, stroke_fill=(90, 0, 0, 255))
    return im.rotate(angle, resample=Image.BICUBIC, expand=True)


def stamp_box(text, size=96, col=RED):
    f = get_font(size)
    w, h = int(text_w(text, f)) + 60, int(size * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=WHITE + (255,), outline=col + (255,), width=10)
    d.rectangle((14, 14, w - 15, h - 15), outline=col + (255,), width=3)
    d.text((w / 2, h / 2 + 4), text, font=f, fill=col + (255,), anchor="mm")
    return im.rotate(-6, resample=Image.BICUBIC, expand=True)


def _rich_lines(draw, text, cx, cy, max_w, size, max_lines, base, key, min_size=50, stroke=None):
    """Text ko lines me, sawal-shabd/ank laal (ya key rang) - poster jaisa."""
    f, s_, lines = fit_lines(text, max_w, max_lines, size, min_size)
    lh = int(s_ * 1.18)
    keys = set(q_highlights(text))
    top = cy - lh * len(lines) / 2
    sp = text_w(" ", f)
    for k, ln in enumerate(lines):
        lw = sum(text_w(w_, f) for w_ in ln) + sp * (len(ln) - 1)
        x = cx - lw / 2
        for w_ in ln:
            col = key if re.sub(r"[,.!?।:()]", "", w_) in keys else base
            kw = {"stroke_width": stroke[0], "stroke_fill": stroke[1]} if stroke else {}
            draw.text((x, top + k * lh + lh / 2), w_, font=f, fill=col, anchor="lm", **kw)
            x += text_w(w_, f) + sp
    return lh * len(lines)


def _shadow_text(cv, xy, text, font, fill, anchor="mm", blur=10, off=(0, 6), alpha=170):
    from PIL import ImageFilter
    lay = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((xy[0] + off[0], xy[1] + off[1]), text, font=font, fill=(0, 0, 0, alpha), anchor=anchor)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    cv.paste(lay, (0, 0), lay)
    ImageDraw.Draw(cv).text(xy, text, font=font, fill=fill, anchor=anchor)


def _soft_shadow(cv, box, radius=34, blur=22, alpha=150, off=10):
    from PIL import ImageFilter
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = blur * 2
    lay = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((pad, pad + off, pad + x1 - x0, pad + y1 - y0 + off), radius=radius,
                                          fill=(0, 0, 0, alpha))
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    cv.paste(lay, (x0 - pad, y0 - pad), lay)


def make_thumbnail(data):
    """
    COVER (pehla frame) - poster style (v10): chaunka emoji + laal brush patti '{n} पेपर में आया!' + 'PYQ!' stamp,
    peeli brush patti me sawal, '{Subject} PYQ Trick', topic-chitra card ('कौन सही? कमेंट करो!' + laal '?'),
    2 jawab teer ke saath 'या', laal patti 'EXAM TRAP | जवाब + वजह रील में!', 'ज़रूर देखें!' sticker, brand footer.
    Har text apni jagah me fit (koi overlap nahi). Jawab nahi dikhaya.
    """
    if data.get("_thumb") is not None:
        return data["_thumb"]
    from PIL import ImageFilter
    NAVY = (14, 22, 48)
    INK = (18, 18, 26)
    BRED = (212, 30, 42)
    BYEL = (255, 214, 10)
    KRED = (200, 20, 30)
    lab, scol = SUBJECT_STYLE.get(data["subject"], ("SCIENCE", CYAN))
    sub_en = lab.split("•")[0].strip().title().replace("Gk", "GK")
    img = _img_src(data["img_hook"]) if data.get("img_hook") else None
    # 1) peeche: topic-chitra dhundhla + gehra (ya subject gradient)
    if img is not None:
        sc_ = max(W / img.width, H / img.height)
        bg = img.resize((int(img.width * sc_) + 1, int(img.height * sc_) + 1), Image.LANCZOS)
        l, tp = (bg.width - W) // 2, (bg.height - H) // 2
        bg = bg.crop((l, tp, l + W, tp + H)).filter(ImageFilter.GaussianBlur(28))
        cv = Image.blend(bg, Image.new("RGB", (W, H), NAVY), 0.55)
    else:
        cv = background("blue").crop((60, 60, 60 + W, 60 + H))
    d = ImageDraw.Draw(cv)

    def text_center(dr, cx, cy, words, font, base, keyc, keys):
        sp = text_w(" ", font)
        lw = sum(text_w(w_, font) for w_ in words) + sp * (len(words) - 1)
        x = cx - lw / 2
        for w_ in words:
            core = re.sub(r"[,.!?।:()-]", "", w_)
            col = keyc if (core in keys or "____" in w_) else base
            dr.text((x, cy), w_, font=font, fill=col, anchor="lm")
            x += text_w(w_, font) + sp

    # 2) laal brush patti: '{n} पेपर में आया!' (emoji ke baad wali jagah me hi fit)
    band = brush_band(800, 150, BRED, seed=3, tilt=1.5)
    place(cv, band, 650, 300)
    hook = data["hook"].rstrip("!") + "!"
    fh, sh, lh_ = fit_lines(hook, 640, 1, 76, 40)
    dh = ImageDraw.Draw(cv)
    text_center(dh, 655, 300, lh_[0] if lh_ else hook.split(), fh, WHITE, BYEL,
                {w_ for w_ in hook.split() if re.search(r"\d", w_)})
    # chaunka emoji + kirne
    ex, ey = 150, 285
    for k_ in range(5):
        ang = math.radians(200 + k_ * 35)
        d.line((ex + math.cos(ang) * 150, ey + math.sin(ang) * 150, ex + math.cos(ang) * 190,
                ey + math.sin(ang) * 190), fill=BYEL, width=9)
    place(cv, shock_emoji(230), ex, ey)
    place(cv, stamp_box("PYQ!", 64, col=BRED), 945, 165)
    # 3) peeli brush patti me sawal (kaala, khaali jagah/ank laal)
    words = data["question"].split()
    short = " ".join(words[:22]) + (" ...?" if len(words) > 22 else "")
    fq, sq, ql = fit_lines(short, 900, 3, 66, 40)
    lhq = int(sq * 1.25)
    qbh = max(220, lhq * len(ql) + 70)
    place(cv, brush_band(1000, qbh, BYEL, seed=7, tilt=-1.0), W / 2, 420 + qbh / 2)
    dq = ImageDraw.Draw(cv)
    keys = set(q_highlights(short))
    for k_, ln in enumerate(ql):
        text_center(dq, W / 2, 420 + qbh / 2 + (k_ - (len(ql) - 1) / 2) * lhq, ln, fq, INK, KRED, keys)
    # 4) '{Subject} PYQ Trick' chhoti laal patti
    yt = 420 + qbh + 75
    ft = get_font(42)
    tw_ = int(text_w(f"{sub_en} PYQ Trick", ft)) + 90
    place(cv, brush_band(tw_, 74, BRED, seed=11, tilt=1.0), W / 2, yt)
    ImageDraw.Draw(cv).text((W / 2, yt + 2), f"{sub_en} PYQ Trick", font=ft, fill=BYEL, anchor="mm")
    # 5) chitra card
    cy0, cy1 = yt + 65, 1445
    cx0, cx1 = 35, W - 35
    cw, ch = cx1 - cx0, cy1 - cy0
    inner = Image.new("RGB", (cw, ch), (16, 26, 56))
    if img is not None:
        sc_ = max(cw / img.width, ch / img.height)
        im2 = img.resize((int(img.width * sc_) + 1, int(img.height * sc_) + 1), Image.LANCZOS)
        l, tp = (im2.width - cw) // 2, (im2.height - ch) // 2
        inner = im2.crop((l, tp, l + cw, tp + ch))
    else:
        gi = background("blue").crop((200, 600, 200 + cw, 600 + ch))
        inner.paste(gi, (0, 0))
    m = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), radius=34, fill=255)
    _soft_shadow(cv, (cx0, cy0, cx1, cy1), radius=34, blur=18, alpha=150, off=8)
    cv.paste(inner, (cx0, cy0), m)
    d = ImageDraw.Draw(cv)
    d.rounded_rectangle((cx0, cy0, cx1, cy1), radius=34, outline=WHITE, width=7)
    if img is None:                                   # chitra nahi: beech me subject ka nishaan
        mid = (cy0 + 95 + cy1 - 200) / 2
        place(cv, glow_sprite(200, scol, 110), W / 2, mid)
        if data["subject"] in SCIENCE_SUBJ:
            place(cv, atom_sprite(min(300, int(ch - 330)), scol), W / 2, mid)
        else:
            pl = pill_sprite(subj_word(data["subject"]), 80, (10, 14, 30), scol, WHITE)
            place(cv, pl, W / 2, mid, scale=min(1.0, 600 / pl.width), angle=-4)
    # 'कौन सही? कमेंट करो!' pill + laal '?' gola
    pc = pill_sprite("कौन सही?  कमेंट करो!", 40, WHITE, BRED, WHITE)
    place(cv, pc, W / 2 - 40, cy0 + 75)
    blob = Image.new("RGBA", (250, 230), (0, 0, 0, 0))
    bd_ = ImageDraw.Draw(blob)
    bd_.ellipse((8, 8, 242, 222), fill=(200, 30, 45, 255), outline=WHITE + (255,), width=6)
    bd_.text((125, 115), "?", font=get_font(110), fill=WHITE + (255,), anchor="mm")
    place(cv, blob, 935, cy0 + 70, angle=-8)
    # 6) do jawab + 'या' + laal teer
    pair = data["vs_pair"]
    letter = {txt: l for l, txt in data["options"]}
    oy0, oy1 = cy1 - 180, cy1 - 30
    for side, txt in enumerate(pair):
        bx0, bx1 = (55, 485) if side == 0 else (595, 1025)
        box = Image.new("RGBA", (bx1 - bx0, oy1 - oy0), (0, 0, 0, 0))
        bdr = ImageDraw.Draw(box)
        bdr.rounded_rectangle((0, 0, box.width - 1, box.height - 1), radius=26, fill=(22, 34, 66, 245),
                              outline=(150, 170, 220, 255), width=4)
        fo, so, lo = fit_lines(txt, box.width - 100, 2, 46, 26)       # gola (A/B) aur kinare se door
        lho = int(so * 1.18)
        for k_, ln in enumerate(lo[:2]):
            bdr.text((72 + (box.width - 92) / 2, box.height / 2 + (k_ - (min(2, len(lo)) - 1) / 2) * lho), " ".join(ln),
                     font=fo, fill=WHITE + (255,), anchor="mm")
        bdr.ellipse((14, 14, 62, 62), fill=BYEL + (255,))
        bdr.text((38, 39), letter.get(txt, "?"), font=get_font(30), fill=INK + (255,), anchor="mm")
        place(cv, box, (bx0 + bx1) / 2, (oy0 + oy1) / 2, angle=(1.5 if side == 0 else -1.5))
        # teer: upar se box ki taraf
        tx_ = (bx0 + bx1) / 2 + (-40 if side == 0 else 40)
        ax0, ay0, ax1, ay1 = tx_ - (40 if side == 0 else -40) * -1, oy0 - 150, tx_, oy0 - 20
        dd = ImageDraw.Draw(cv)
        dd.line((ax0, ay0, ax1, ay1), fill=(230, 50, 50), width=10)
        ang = math.atan2(ay1 - ay0, ax1 - ax0)
        for da in (2.6, -2.6):
            dd.line((ax1, ay1, ax1 + 42 * math.cos(ang + da), ay1 + 42 * math.sin(ang + da)), fill=(230, 50, 50),
                    width=10)
    ya = pill_sprite("या", 46, INK, BYEL, BYEL)
    place(cv, ya, W / 2, (oy0 + oy1) / 2)
    # 7) neeche laal patti: EXAM TRAP | जवाब + वजह रील में!
    place(cv, brush_band(1060, 130, BRED, seed=19, tilt=0.8), W / 2, 1515)
    et = pill_sprite("EXAM TRAP", 38, INK, BYEL, BYEL)
    place(cv, et, 70 + et.width / 2, 1508)
    fj = get_font(44)
    rt = "जवाब + वजह रील में!"
    rx1 = W - 50
    rx0 = 70 + et.width + 30
    while text_w(rt, fj) > rx1 - rx0 and fj.size > 30:
        fj = get_font(fj.size - 2)
    ImageDraw.Draw(cv).text((rx1, 1505), rt, font=fj, fill=WHITE, anchor="rm")
    # 8) footer: logo + brand + exams ; 'ज़रूर देखें!' sticker
    d = ImageDraw.Draw(cv)
    d.rectangle((0, 1590, W, 1745), fill=(10, 16, 36))
    place(cv, brand_logo(66), 75, 1668)
    wm = brand_wordmark(40)
    place(cv, wm, 125 + wm.width / 2, 1668)
    fe = get_font(36)
    ex_t = "|  RRB  |  SSC  |  NTPC  |  STATE"
    xe = 125 + wm.width + 22
    while xe + text_w(ex_t, fe) > 830 and fe.size > 24:
        fe = get_font(fe.size - 2)
    d.text((xe, 1668), ex_t, font=fe, fill=WHITE, anchor="lm")
    place(cv, starburst("ज़रूर\nदेखें!", 210, fill=(205, 25, 40), angle=-12), 955, 1640)
    data["_thumb"] = cv
    return cv


def render_frame(sc, data, gt, total):
    t = gt - sc["start"]
    nm = sc["name"]
    if nm == "poster":                          # ant ke frame = Instagram cover (thumb_offset)
        return make_thumbnail(data).copy()
    cv = bg_frame(sc["mood"], gt)
    if nm in ("hook", "question", "verdict") and data.get("img_hook"):
        cv = draw_backdrop(cv, data["img_hook"], gt, 0.45)   # chitra pehle frame se peeche (khaali intezaar nahi)
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
                    cache = {}
                    cache[si] = render_frame(timeline[si - 1], data, sc["start"] - 1.0 / FPS, total)
                frame = iris(cache[si], frame, tt / TRANSITION)
                if tt < 0.12:
                    frame = rgb_split(frame, 16 * (1 - tt / 0.12))
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

SUBJ_TAGS = {"Physics": "#physics", "Chemistry": "#chemistry", "Biology": "#biology", "History": "#history",
             "Polity": "#polity", "Geography": "#geography", "Economics": "#economics", "Environment": "#environment",
             "Traditional GK": "#gk", "Computer": "#computer"}


def make_caption(data):
    """
    Pehli line = sawal + search shabd (Instagram ab caption ke shabdon se search/explore me dikhata hai).
    Hashtag: 5, subject ke hisaab se. WhatsApp sirf yahan (reel me nahi).
    """
    sub = data["subject"]
    sw = subj_word(sub)
    yrs = ", ".join(data["exams"][:2])
    asked = (f"📌 {yrs} में {data['times_asked']} बार पूछा गया" if data["times_asked"] >= 2
             else f"📌 {yrs} में पूछा गया")
    lines = [
        f"❓ {data['question']}",
        f"{sw} GK Question | RRB NTPC, Group D, SSC GD, State Exam PYQ 2026",
        "",
        asked,
    ] + ([f"🇬🇧 {data['en_question']}"] if data.get("en_question") else []) + [
        "💬 अपना जवाब A / B / C / D कमेंट करो - सही जवाब + वजह रील में।",
        "📥 Save करो - exam से पहले revision में काम आएगा।",
        f"🔔 Follow {BRAND_HANDLE} - रोज़ नए PYQ",
    ] + ([f"📲 Free test / notes: WhatsApp {WHATSAPP_NUMBER}"] if WHATSAPP_NUMBER else []) + [
        "",
        f"#gkquiz #rrbntpc #sscgd #gkpyq {SUBJ_TAGS.get(sub, '#gk')}",
    ]
    return "\n".join(lines)


# ============================== INSTAGRAM ==============================

def _upload_once(video_file, caption, thumb_ms=0):
    """Ek koshish: container -> (10s ruko) -> rupload -> FINISHED -> publish."""
    r = requests.post(f"{GRAPH}{IG_USER_ID}/media",
                      data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                            "thumb_offset": str(int(thumb_ms)),      # cover = ant wala poster frame
                            "share_to_feed": "true",
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


def post_reel(video_file, caption, thumb_ms=0):
    """Poori upload 3 baar tak (har baar naya container). Fail = exception (progress aage nahi badhta)."""
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("IG secrets nahi - post skip (reel bani hai).")
        return None
    last = None
    for attempt in range(3):
        try:
            pid = _upload_once(video_file, caption, thumb_ms)
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
    tag = pill_sprite("PYQ  |  RAILWAY • SSC • STATE", 22, WHITE, (22, 101, 52), GREEN)
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
    d.text((CW / 2, 250), "3 PYQ CHALLENGE", font=get_font(104), fill=YELLOW, anchor="mm", stroke_width=6,
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
    cap = [f"📚 {BRAND} | 3 PYQ - तीनों सही कर पाओगे?", ""]
    for k, it in enumerate(items):
        cap.append(f"{k + 1}. {it['question']}  ->  ({it['correct']}) {it['correct_text']}")
    cap += ["", "🎯 Railway, SSC, State exams - ऐसे सवाल हर exam में आते हैं।",
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


# ============================== NAYE FORMAT: LOOP SAWAL + 7 PYQ LIST ==============================
# vidIQ jaanch (Oct 2026): is niche ki viral reels 4-10 sec ki, sirf music, ek static padhne layak screen.
#  - @__quiztech05: 1 PYQ, 4s, jawab nahi -> 4 lakh   - @kalanauriya_nvnguran: 'IAS me poochha', 5s -> 9.4 lakh
#  - @aman._comman_generalknowledge: 7 sawal+jawab ek page, 10s -> 44 lakh
# Reel itni chhoti ki padhte-padhte 2-3 baar loop ho jaaye -> watch time 100%+ -> Instagram aage dikhata hai.

REEL_FORMAT = os.getenv("REEL_FORMAT", "auto").strip().lower()     # auto | loop | list | classic
LOOP_DUR = 8.0                      # 120 BPM ke 4 bar -> music aur visual dono bilkul seamless loop
LIST_DUR = 10.0
LIST_N = 7
LIST_MAX_Q_WORDS = 14
LIST_MAX_A_WORDS = 4
INK = (22, 24, 34)
PAPER = (252, 250, 242)
PEN_BLUE = (24, 70, 190)
PEN_RED = (200, 30, 40)


def pick_format(ep):
    if REEL_FORMAT in ("loop", "list", "classic", "triple", "quiz", "galti", "mega"):
        return REEL_FORMAT
    # din ki 3 reel samay ke hisaab se (IST): subah 7 PYQ list, dopahar quiz notebook, raat MEGA revision
    # (MEGA = sabse zyada save wali reel -> raat 8 baje ke sabse bade peak pe)
    h = time.gmtime(time.time() + 19800).tm_hour
    return "list" if h < 11 else ("quiz" if h < 17 else "mega")


# ---------- HAR EXAM KI AUDIENCE: GS sab me aata hai -> har reel alag exam waalon ko bulaye ----------
AUDIENCES = [
    ("Railway NTPC / Group D", "#rrbntpc #rrbgroupd"),
    ("SSC GD / MTS / CGL", "#sscgd #ssccgl"),
    ("Police भर्ती", "#policebharti #upsi"),
    ("Patwari / Lekhpal", "#patwari #lekhpal"),
    ("Army / Agniveer", "#agniveer #armygk"),
    ("State PSC / UPSC Pre", "#uppsc #bpsc"),
]


def audience_of(ep):
    return AUDIENCES[ep % len(AUDIENCES)]


# ---------- music: code se bana (copyright-free), 120 BPM, LOOP_DUR me poora seamless ----------

def beat_music(dur, seed=0):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t, dtype=np.float32)
    beat = 0.5
    rng = np.random.default_rng(seed)
    roots = [[110.0, 130.81, 164.81], [98.0, 123.47, 146.83], [87.31, 110.0, 130.81], [98.0, 123.47, 146.83]]
    n_beats = int(round(dur / beat))
    kick_t = _t(0.25)
    kick = np.sin(2 * math.pi * np.cumsum(55 + 110 * np.exp(-kick_t * 30)) / SR) * np.exp(-kick_t * 9)
    hat_t = _t(0.05)
    hat = rng.normal(0, 1, len(hat_t)) * np.exp(-hat_t * 90)
    clap_t = _t(0.18)
    clap = rng.normal(0, 1, len(clap_t)) * np.exp(-clap_t * 22)
    for b in range(n_beats):
        s = b * beat
        add_at(out, kick, s, 0.55)
        add_at(out, hat, s + beat / 2, 0.10)
        add_at(out, hat, s + beat * 0.75, 0.05)
        if b % 2 == 1:
            add_at(out, clap, s, 0.16)
    # chord pad + bass (har bar = 2s ek chord)
    bar = 4 * beat
    for k in range(int(round(dur / bar))):
        ch = roots[k % 4]
        st, n = int(k * bar * SR), int(bar * SR)
        tt = np.arange(n) / SR
        env = np.minimum(1, tt / 0.05) * np.minimum(1, (bar - tt) / 0.08)
        pad = sum(np.sin(2 * math.pi * f * 2 * tt) for f in ch) / len(ch)
        bass = np.sin(2 * math.pi * ch[0] / 2 * tt) * (0.6 + 0.4 * np.sign(np.sin(2 * math.pi * 2 * tt)))
        seg = (pad * 0.07 + bass * 0.10) * env
        e = min(len(out), st + n)
        out[st:e] += seg[:e - st].astype(np.float32)
    # pluck melody (har aadha beat)
    notes = [440.0, 523.25, 659.25, 587.33, 523.25, 440.0, 392.0, 440.0]
    pl_t = _t(0.22)
    for i in range(int(round(dur / (beat / 2)))):
        if i % 8 in (1, 5):
            continue
        f = notes[i % 8]
        add_at(out, np.sin(2 * math.pi * f * pl_t) * np.exp(-pl_t * 14), i * beat / 2, 0.07)
    out = out[:int(dur * SR)]
    pk = float(np.max(np.abs(out))) or 1.0
    return (out / pk * 0.8).astype(np.float32)


def encode_frames(render, n_frames, audio, out_path, key=lambda fi: fi):
    """render(fi)->PIL frame; key(fi) same ho to pichhla frame dobara (static hisse tez)."""
    wav = out_path + ".wav"
    with wave.open(wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264", "-preset", "medium",
           "-crf", str(VIDEO_CRF), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last_k, last_b = None, None
    try:
        for fi in range(n_frames):
            k = key(fi)
            if k != last_k:
                last_b, last_k = render(fi).tobytes(), k
            proc.stdin.write(last_b)
        proc.stdin.close()
    except BrokenPipeError:
        pass
    ret = proc.wait()
    os.remove(wav)
    if ret != 0:
        raise RuntimeError("ffmpeg encoding fail")



# ---------- MinuteMe pehchan: stopwatch, repeat-thappa, aaj ki tareekh, toppers ----------

def stopwatch_sprite(size, frac):
    """Brand ki ghadi: peela stopwatch, sui frac (0-1) par. Logo bhi yahi, reel me chalti hai."""
    S = size * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = S / 2, S * 0.40
    cy = c + S * 0.05
    d.rounded_rectangle((c - S * 0.08, cy - r - S * 0.13, c + S * 0.08, cy - r + S * 0.02), radius=S // 40,
                        fill=YELLOW + (255,))
    d.ellipse((c - r, cy - r, c + r, cy + r), fill=(12, 22, 44, 255), outline=YELLOW + (255,), width=S // 18)
    if frac > 0:
        d.pieslice((c - r * 0.8, cy - r * 0.8, c + r * 0.8, cy + r * 0.8), -90, -90 + 360 * frac,
                   fill=(250, 204, 21, 90))
    for k in range(12):
        a = math.radians(k * 30)
        d.line((c + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86, c + math.cos(a) * r * 0.74,
                cy + math.sin(a) * r * 0.74), fill=(200, 210, 230, 255), width=S // 50)
    a = math.radians(-90 + 360 * frac)
    d.line((c, cy, c + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78), fill=RED + (255,), width=S // 22)
    d.ellipse((c - S * 0.04, cy - S * 0.04, c + S * 0.04, cy + S * 0.04), fill=WHITE + (255,))
    return im.resize((size, size), Image.LANCZOS)


@lru_cache(maxsize=8)
def repeat_stamp(n):
    """'रिपीट PYQ xn' laal thappa - bank ka asli data, koi aur page nahi dikhata."""
    f1, f2 = get_font(34), get_font(24)
    top, bot = f"रिपीट PYQ  x{n}", f"{n} शिफ्ट में पूछा गया"
    w = int(max(text_w(top, f1), text_w(bot, f2))) + 50
    h = 96
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=16, fill=(200, 25, 40, 245), outline=WHITE + (255,), width=4)
    d.text((w / 2, 34), top, font=f1, fill=WHITE + (255,), anchor="mm")
    d.text((w / 2, 72), bot, font=f2, fill=(255, 230, 120, 255), anchor="mm")
    return im


def today_dm():
    """IST aaj: ('DD-MM', saal). Jaanch ke liye TODAY_DM=03-10 env."""
    ist = time.gmtime(time.time() + 19800)
    return (os.getenv("TODAY_DM") or f"{ist.tm_mday:02d}-{ist.tm_mon:02d}"), ist.tm_year


def today_exam(q):
    dm, _ = today_dm()
    for e in q.get("exams") or []:
        if re.search(r"(?<!\d)" + re.escape(dm) + r"-20\d\d", str(e)):
            return str(e)
    return None


def years_ago(exam):
    m = re.search(r"\d\d-\d\d-(20\d\d)", exam or "")
    return today_dm()[1] - int(m.group(1)) if m else 0


def fetch_toppers(st):
    """Pichhli loop reel ke comments: jinhone sirf sahi akshar likha, unke naam (max 3). Permission na ho -> []."""
    ll = st.get("last_loop") or {}
    mid, cor = ll.get("media"), ll.get("correct")
    if not (mid and cor and IG_ACCESS_TOKEN) or DRY_RUN:
        return []
    try:
        r = requests.get(f"{GRAPH}{mid}/comments", params={"fields": "username,text", "limit": 100,
                                                          "access_token": IG_ACCESS_TOKEN}, timeout=30).json()
    except Exception as exc:
        print("  toppers nahi mile:", str(exc)[:120])
        return []
    if "error" in r:
        print("  toppers: comment padhne ki permission nahi ->", str(r["error"].get("message", ""))[:120])
        return []
    names = []
    for c in r.get("data", []):
        u = (c.get("username") or "").strip()
        letters = set(re.findall(r"(?<![A-Z])([ABCD])(?![A-Z])", (c.get("text") or "").upper()))
        if u and u.lower() != BRAND.lower() and letters == {cor} and u not in names:
            names.append(u)
    print("  Kal ke toppers:", names[:3])
    return names[:3]


# ---------- LOOP SAWAL (8s, jawab reel me nahi -> pehle comment me) ----------

def loop_hook(data):
    return exam_hook(data)


def _old_loop_hook(data):
    if data.get("today_exam"):
        y = years_ago(data["today_exam"])
        return f"{y} साल पहले आज ही पूछा गया!" if y > 0 else "आज ही के दिन पूछा गया!"
    n = data["times_asked"]
    if n >= 2:
        return f"ये सवाल {n} बार पेपर में आया!"
    return ["Railway में पूछा गया सवाल!", "RRB पेपर का असली सवाल!", "Exam में पूछा गया - बताओ!"][data["episode"] % 3]


def _ink_words(d, words, cx, cy, font, base, key_col, keys):
    sp = text_w(" ", font)
    lw = sum(text_w(w_, font) for w_ in words) + sp * (len(words) - 1)
    x = cx - lw / 2
    for w_ in words:
        core = re.sub(r"[,.!?।:()]", "", w_)
        d.text((x, cy), w_, font=font, fill=key_col if (core in keys or "____" in w_) else base, anchor="lm")
        x += text_w(w_, font) + sp


@lru_cache(maxsize=2)
def _loop_bg(img_path):
    if img_path:
        bd = backdrop(img_path)
        if bd is not None:
            im = bd.crop((60, 60, 60 + W, 60 + H))
            return Image.blend(im, Image.new("RGB", (W, H), (8, 12, 28)), 0.35)
    return background("blue").crop((60, 60, 60 + W, 60 + H))


def loop_layout(data, limit=1450):
    """Sawal card (safed kaagaz, kaali syahi) + 4 poori-chaudai options. Sab 230..1560 me fit."""
    q = data["question"]
    opt_n = len(data["options"])
    for qs, os_, oh in ((72, 60, 150), (66, 56, 140), (60, 52, 130), (54, 48, 122), (48, 44, 114), (44, 40, 106)):
        fq, sq, ql = fit_lines(q, 920, 4, qs, qs)
        if len(ql) > 4:
            continue
        lh = int(sq * 1.28)
        qh = lh * len(ql) + 70
        top = 550 if (data["times_asked"] >= 2 or data.get("level") in ("hard", "medium")) else 520
        total = qh + 36 + opt_n * oh + (opt_n - 1) * 22
        if top + total <= limit:
            return {"fq": fq, "ql": ql, "lh": lh, "qh": qh, "q_top": top, "os": os_, "oh": oh,
                    "o_top": top + qh + 36}
    fq, sq, ql = fit_lines(q, 920, 5, 40, 34)
    lh = int(sq * 1.28)
    qh = lh * len(ql) + 60
    return {"fq": fq, "ql": ql, "lh": lh, "qh": qh, "q_top": 500, "os": 38, "oh": 100, "o_top": 500 + qh + 30}


@lru_cache(maxsize=24)
def _opt_row(letter, text, active, w=1000, h=150, size=60):
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fill = (30, 58, 110, 250) if active else (16, 28, 58, 240)
    out = YELLOW if active else (110, 140, 200)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=30, fill=fill, outline=out + (255,), width=6 if active else 4)
    r = h * 0.30
    cx, cy = 20 + 30 + r, 20 + h / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=YELLOW + (255,))
    d.text((cx, cy + 2), letter, font=get_font(int(r * 1.15)), fill=INK + (255,), anchor="mm")
    f, s_, lines = fit_lines(text, w - 2 * r - 110, 2, size, 30)
    lh_ = int(s_ * 1.15)
    x0 = cx + r + 34
    for k, ln in enumerate(lines[:2]):
        d.text((x0, cy + (k - (min(2, len(lines)) - 1) / 2) * lh_), " ".join(ln), font=f, fill=WHITE + (255,),
               anchor="lm")
    return im


@lru_cache(maxsize=8)
def poster_band(text):
    """Purane poster wali pehchan: laal brush patti, safed akshar, ank peele (pehla frame = cover)."""
    band = brush_band(820, 150, (212, 30, 42), seed=3, tilt=1.2)
    d = ImageDraw.Draw(band)
    f, s_, ls = fit_lines(text, 760, 1, 72, 40)
    words = ls[0] if ls else text.split()
    sp = text_w(" ", f)
    lw = sum(text_w(w_, f) for w_ in words) + sp * (len(words) - 1)
    x, cy = band.width / 2 - lw / 2, band.height / 2
    for w_ in words:
        col = (255, 214, 10) if re.search(r"\d", w_) else WHITE
        d.text((x, cy), w_, font=f, fill=col + (255,), anchor="lm", stroke_width=3, stroke_fill=(90, 0, 10, 255))
        x += text_w(w_, f) + sp
    return band


# ---------- MinuteMe MASCOT (stopwatch character) + PEN ----------

def lerp(a, b, k):
    return a + (b - a) * k


def mascot(size, look=(0.0, 0.0), mood="think", sweat=0.0, pose="chin", frac=0.0, blink=False, bob=0.0):
    S = size * 2
    im = Image.new("RGBA", (S, int(S * 1.25)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = S / 2, S * 0.55 + bob, S * 0.36
    ink = (40, 26, 10, 255)
    lw = max(3, S // 60)
    # legs + shoes
    for sx in (-1, 1):
        x = cx + sx * r * 0.38
        d.line((x, cy + r * 0.85, x + sx * 6, cy + r * 1.28), fill=ink, width=lw * 2)
        d.ellipse((x + sx * 6 - S * 0.07, cy + r * 1.22, x + sx * 6 + S * 0.07, cy + r * 1.38), fill=(220, 40, 50, 255),
                  outline=ink, width=lw)
    # crown + side button
    d.rounded_rectangle((cx - S * 0.07, cy - r - S * 0.11, cx + S * 0.07, cy - r + S * 0.02), radius=S // 50,
                        fill=(250, 204, 21, 255), outline=ink, width=lw)
    d.rounded_rectangle((cx - S * 0.12, cy - r - S * 0.15, cx + S * 0.12, cy - r - S * 0.09), radius=S // 60,
                        fill=(250, 204, 21, 255), outline=ink, width=lw)
    # body
    d.ellipse((cx - r - S * 0.035, cy - r - S * 0.035, cx + r + S * 0.035, cy + r + S * 0.035),
              fill=(250, 204, 21, 255), outline=ink, width=lw)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 246, 214, 255), outline=ink, width=lw)
    for k in range(12):
        a = math.radians(k * 30)
        d.line((cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92, cx + math.cos(a) * r * 0.82,
                cy + math.sin(a) * r * 0.82), fill=(150, 140, 120, 255), width=lw)
    # chalti laal 'sui' kinare par (8s me ek chakkar)
    a = math.radians(-90 + 360 * frac)
    sw = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sw).pieslice((cx - r * 0.98, cy - r * 0.98, cx + r * 0.98, cy + r * 0.98), -90, -90 + 360 * frac,
                                fill=(255, 140, 140, 55))
    im.alpha_composite(sw)
    d = ImageDraw.Draw(im)
    px, py = cx + math.cos(a) * r * 0.87, cy + math.sin(a) * r * 0.87
    d.ellipse((px - S * 0.03, py - S * 0.03, px + S * 0.03, py + S * 0.03), fill=(220, 30, 40, 255))
    # gaal
    for sx in (-1, 1):
        d.ellipse((cx + sx * r * 0.55 - S * 0.06, cy + r * 0.12, cx + sx * r * 0.55 + S * 0.06, cy + r * 0.28),
                  fill=(255, 150, 150, 150))
    # aankhen
    ex, ey, erx, ery = r * 0.32, cy - r * 0.12, S * 0.085, S * 0.105
    for sx in (-1, 1):
        x = cx + sx * ex
        if blink:
            d.line((x - erx, ey, x + erx, ey), fill=ink, width=lw * 2)
        else:
            d.ellipse((x - erx, ey - ery, x + erx, ey + ery), fill=(255, 255, 255, 255), outline=ink, width=lw)
            px_, py_ = x + look[0] * erx * 0.45, ey + look[1] * ery * 0.45
            d.ellipse((px_ - erx * 0.48, py_ - erx * 0.48, px_ + erx * 0.48, py_ + erx * 0.48), fill=(20, 20, 30, 255))
            d.ellipse((px_ - erx * 0.2, py_ - erx * 0.32, px_, py_ - erx * 0.12), fill=(255, 255, 255, 255))
        # bhaunh
        tilt = {"think": (0.0, 0.35), "worried": (0.45, -0.1), "shock": (0.0, -0.1), "happy": (0.0, 0.0)}[mood]
        y0 = ey - ery - S * 0.05
        d.line((x - erx, y0 + sx * tilt[0] * S * 0.05 * (-1) + (S * 0.03 if sx < 0 else 0) * tilt[1],
                x + erx, y0 + sx * tilt[0] * S * 0.05 + (S * 0.03 if sx > 0 else 0) * tilt[1]), fill=ink, width=lw * 2)
    # muh
    my = cy + r * 0.40
    if mood == "think":
        d.line((cx - S * 0.05, my, cx + S * 0.04, my - S * 0.015), fill=ink, width=lw * 2)
    elif mood == "worried":
        pts = [(cx - S * 0.08 + i * S * 0.02, my + (S * 0.012 if i % 2 else -S * 0.012)) for i in range(9)]
        d.line(pts, fill=ink, width=lw * 2)
    elif mood == "shock":
        d.ellipse((cx - S * 0.045, my - S * 0.05, cx + S * 0.045, my + S * 0.05), fill=(120, 20, 25, 255), outline=ink,
                  width=lw)
    else:
        d.arc((cx - S * 0.09, my - S * 0.07, cx + S * 0.09, my + S * 0.05), 20, 160, fill=ink, width=lw * 2)
    # haath
    glove = (255, 255, 255, 255)
    # baaya haath: kamar par
    lx0, ly0 = cx - r * 0.95, cy + r * 0.1
    d.line((lx0, ly0, lx0 - S * 0.08, ly0 + S * 0.12), fill=ink, width=lw * 2)
    d.ellipse((lx0 - S * 0.13, ly0 + S * 0.08, lx0 - S * 0.03, ly0 + S * 0.18), fill=glove, outline=ink, width=lw)
    rx0, ry0 = cx + r * 0.95, cy + r * 0.05
    if pose == "chin":                         # thodi par haath (soch)
        hx, hy = cx + r * 0.25, cy + r * 0.62
        d.line((rx0, ry0, rx0 + S * 0.05, ry0 + S * 0.22), fill=ink, width=lw * 2)
        d.line((rx0 + S * 0.05, ry0 + S * 0.22, hx + S * 0.04, hy + S * 0.02), fill=ink, width=lw * 2)
        d.ellipse((hx - S * 0.06, hy - S * 0.05, hx + S * 0.06, hy + S * 0.07), fill=glove, outline=ink, width=lw)
    else:                                      # neeche ishaara (comment ki taraf)
        hx, hy = rx0 + S * 0.10, ry0 + S * 0.30
        d.line((rx0, ry0, hx, hy), fill=ink, width=lw * 2)
        d.ellipse((hx - S * 0.06, hy - S * 0.06, hx + S * 0.06, hy + S * 0.06), fill=glove, outline=ink, width=lw)
        d.line((hx, hy + S * 0.04, hx + S * 0.01, hy + S * 0.13), fill=ink, width=lw * 2)
    # pasina
    if sweat > 0.02:
        sx_, sy_ = cx + r * 0.78, cy - r * 0.55 + sweat * S * 0.12
        a_ = int(255 * min(1, sweat * 2))
        d.polygon([(sx_, sy_ - S * 0.06), (sx_ - S * 0.035, sy_ + S * 0.01), (sx_ + S * 0.035, sy_ + S * 0.01)],
                  fill=(80, 170, 255, a_))
        d.ellipse((sx_ - S * 0.035, sy_ - S * 0.02, sx_ + S * 0.035, sy_ + S * 0.05), fill=(80, 170, 255, a_))
    return im.resize((size, int(size * 1.25)), Image.LANCZOS)


@lru_cache(maxsize=2)
def pen_sprite(size=120):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(10, size - 10), (26, size - 44), (44, size - 26)], fill=(240, 220, 180, 255), outline=(60, 40, 20, 255))
    d.polygon([(10, size - 10), (16, size - 24), (24, size - 16)], fill=(200, 30, 40, 255))
    d.polygon([(26, size - 44), (44, size - 26), (size - 8, 30), (size - 30, 8)], fill=(220, 40, 50, 255),
              outline=(90, 10, 20, 255))
    return im


# ---------- HEADLINE: "aane wale exam me aa sakta hai" (user ki manzoor ki hui lines) ----------
AUD_SHORT = ["NTPC", "SSC GD", "Police भर्ती", "Patwari", "Agniveer", "State PSC"]   # AUDIENCES ke kram me


def upcoming_year():
    ist = time.gmtime(time.time() + 19800)
    return ist.tm_year if ist.tm_mon < 7 else ist.tm_year + 1


def exam_hook(data):
    n, ep = data["times_asked"], data["episode"]
    if n >= 2:
        return [f"{n} बार आ चुका - फिर आ सकता है!", "बार-बार पूछा जाने वाला सवाल!",
                "Repeat सवाल - इस बार मत छोड़ना!"][ep % 3]
    aud = AUD_SHORT[ep % len(AUD_SHORT)]
    pool = [f"{aud} {upcoming_year()} में आ सकता है!", f"{aud} की तैयारी है? ये ज़रूर देखो!",
            "Exam से पहले ये ज़रूर देखो!", "ये गलत किया तो नंबर कटेंगे!", "Selection वाले इसे नहीं छोड़ते!",
            "10 सेकंड दो - 1 नंबर पक्का!", "अगले Exam का Important सवाल!"]
    return pool[ep % len(pool)]


# ---------- chitron wale options (Cloudflare) ----------
OPT_TW, OPT_TH, OPT_IMG_H = 495, 292, 188


def make_option_images(q, ai):
    """AI kahe 'chaaron options chitra me dikh sakte hain' to har option ka chitra. Ek bhi fail -> {} (lambi rows)."""
    ai = ai or {}
    prm = ai.get("img_options") or {}
    if not ai.get("visual_options") or not all(isinstance(prm.get(k), str) and prm[k].strip() for k in "abcd"):
        return {}
    import io
    os.makedirs(IMG_DIR, exist_ok=True)
    out = {}
    for k in "abcd":
        path = os.path.join(IMG_DIR, f"{q['id']}_opt_{k}.jpg")
        if not os.path.exists(path):
            b = cf_image(f"{prm[k]}. single subject in the center, simple soft plain background. {IMG_STYLE}")
            if not b:
                print("  option chitra nahi bana -> lambi rows")
                return {}
            try:
                Image.open(io.BytesIO(b)).convert("RGB").save(path, quality=90)
            except Exception:
                return {}
        out[k.upper()] = path
    print("  Option chitra bane: 4")
    return out


@lru_cache(maxsize=16)
def pic_tile(L, txt, path, active):
    TW, TH, IH = OPT_TW, OPT_TH, OPT_IMG_H
    im = Image.new("RGBA", (TW + 30, TH + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((15, 15, 15 + TW, 15 + TH), radius=28, fill=(16, 28, 58, 245),
                        outline=(YELLOW if active else (110, 140, 200)) + (255,), width=7 if active else 4)
    src = _img_src(path)
    if src is not None:
        w, h = TW - 24, IH
        sc = max(w / src.width, h / src.height)
        cw, ch = w / sc, h / sc
        crop = src.crop((int((src.width - cw) / 2), int((src.height - ch) / 2), int((src.width + cw) / 2),
                         int((src.height + ch) / 2))).resize((w, h), Image.LANCZOS)
        im.paste(crop, (27, 27), _round_mask(w, h, 22))
    r = 30
    d.ellipse((30, 30, 30 + 2 * r, 30 + 2 * r), fill=YELLOW + (255,), outline=(40, 26, 10, 255), width=3)
    d.text((30 + r, 30 + r + 2), L, font=get_font(38), fill=(20, 20, 30, 255), anchor="mm")
    f, s_, ls = fit_lines(txt, TW - 40, 1, 52, 28)
    d.text((15 + TW / 2, 27 + IH + (TH - IH - 12) / 2), " ".join(ls[0]) if ls else txt, font=f,
           fill=(255, 255, 255, 255), anchor="mm")
    return im


def loop_layout2(data, limit=1420):
    """Sawal card + options. Chaaron chitra hon aur jagah ho -> 2x2 chitra-dabbe, warna lambi rows."""
    q = data["question"]
    top = 600
    if data.get("opt_imgs") and len(data["opt_imgs"]) == 4:
        grid = 2 * OPT_TH + 22
        for qs in (64, 58, 52, 48, 44):
            fq, sq, ql = fit_lines(q, 920, 3, qs, qs)
            if len(ql) > 3:
                continue
            lh = int(sq * 1.26)
            qh = lh * len(ql) + 64
            g0 = top + qh + 40
            if g0 + grid <= limit:
                xs = (W / 2 - OPT_TW / 2 - 12, W / 2 + OPT_TW / 2 + 12)
                ys = (g0 + OPT_TH / 2, g0 + OPT_TH * 1.5 + 22)
                boxes = [(xs[i % 2], ys[i // 2], OPT_TW, OPT_TH) for i in range(4)]
                return {"mode": "pic", "fq": fq, "ql": ql, "lh": lh, "qh": qh, "q_top": top, "boxes": boxes}
    n = len(data["options"])
    for qs, os_, oh in ((68, 58, 140), (62, 54, 130), (56, 50, 122), (50, 46, 114), (46, 42, 106), (42, 38, 98)):
        fq, sq, ql = fit_lines(q, 920, 4, qs, qs)
        if len(ql) > 4:
            continue
        lh = int(sq * 1.28)
        qh = lh * len(ql) + 64
        o_top = top + qh + 34
        if o_top + n * oh + (n - 1) * 20 <= limit:
            break
    boxes = [(W / 2, o_top + oh / 2 + i * (oh + 20), 1000, oh) for i in range(n)]
    return {"mode": "rows", "fq": fq, "ql": ql, "lh": lh, "qh": qh, "q_top": top, "os": os_, "oh": oh,
            "boxes": boxes}


@lru_cache(maxsize=4)
def head_band(text):
    """Laal brush patti (mascot ke liye baayein jagah chhod ke), ank peele."""
    band = brush_band(690, 140, (212, 30, 42), seed=3, tilt=1.2)
    d = ImageDraw.Draw(band)
    f, s_, ls = fit_lines(text, 640, 1, 66, 34)
    if len(ls) > 1:
        f, s_, ls = fit_lines(text, 640, 2, 46, 30)
    lh = int(s_ * 1.12)
    for j, words in enumerate(ls[:2]):
        sp = text_w(" ", f)
        lw = sum(text_w(w_, f) for w_ in words) + sp * (len(words) - 1)
        x = band.width / 2 - lw / 2
        cy = band.height / 2 + (j - (min(2, len(ls)) - 1) / 2) * lh
        for w_ in words:
            col = (255, 214, 10) if re.search(r"\d", w_) else WHITE
            d.text((x, cy), w_, font=f, fill=col + (255,), anchor="lm", stroke_width=3, stroke_fill=(90, 0, 10, 255))
            x += text_w(w_, f) + sp
    return band


def draw_pen(cv, box, pt, seg):
    """Laal pen active option ke charon taraf ghera banata hai, fir '?'."""
    x, y, bw, bh = box
    k = clamp((pt - 0.08 * seg) / (0.45 * seg))
    if k <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    rx, ry = bw / 2 + 18, bh / 2 + 18
    pts = [(x + math.cos(math.radians(-100 + 380 * j / 80)) * rx * (1 + 0.02 * math.sin(j)),
            y + math.sin(math.radians(-100 + 380 * j / 80)) * ry) for j in range(int(80 * k) + 1)]
    if len(pts) > 1:
        ld.line(pts, fill=(230, 30, 45, 235), width=9, joint="curve")
    cv.paste(lay, (0, 0), lay)
    if k < 1:
        place(cv, pen_sprite(), pts[-1][0] + 45, pts[-1][1] - 45)
    elif pt > 0.6 * seg:
        place(cv, pill_sprite("?", 46, WHITE, RED, WHITE), x + bw / 2 - 10, y - bh / 2 + 10,
              scale=min(1.0, (pt - 0.6 * seg) / (0.08 * seg)))


def render_loop_frame(data, lay, t):
    dur = data.get("_dur", LOOP_DUR)
    rel = t / dur
    act = int(rel * 4) % 4
    cv = _loop_bg(data.get("img_hook")).copy()
    d = ImageDraw.Draw(cv)
    # header: chalti stopwatch + naam + tagline | subject + audience
    place(cv, stopwatch_sprite(84, int(t * 15) % int(dur * 15) / (dur * 15)), 92, 150)
    wm = brand_wordmark(34)
    place(cv, wm, 150 + wm.width / 2, 136)
    d.text((150, 172), BRAND_TAGLINE, font=get_font(24), fill=(255, 225, 120), anchor="lm")
    aud = (data.get("audience") or AUDIENCES[0])[0]
    lab, col = SUBJECT_STYLE.get(data["subject"], ("GK", CYAN))
    c1 = pill_sprite(lab.split("•")[0].strip() + " PYQ", 24, col, (14, 26, 44), col)
    c2 = pill_sprite(aud + " के लिए भी", 24, WHITE, (120, 30, 60), (255, 150, 170))
    place(cv, c1, W - 70 - c1.width / 2, 128)
    place(cv, c2, W - 70 - c2.width / 2, 172)
    # asli paper (bharosa)
    src = data.get("exam_raw") or (data["exams"][0] if data.get("exams") else "RRB Group-D")
    place(cv, pill_sprite("पूछा गया:  " + src, 32, (30, 18, 0), YELLOW, ORANGE), W / 2 + 120, 262)
    # headline patti + MASCOT
    place(cv, head_band(data.get("_hook") or exam_hook(data)), W / 2 + 150, 410,
          scale=1 + 0.015 * math.sin(2 * math.pi * t / 2.0))
    if lay["mode"] == "pic":
        look = [(-0.9, 0.9), (0.9, 0.9), (-0.9, 1.0), (0.9, 1.0)][act]
    else:
        look = (0.7, 0.2 + 0.25 * act)
    mood = "think" if rel < 0.5 else ("worried" if rel < 0.75 else "shock")
    m = mascot(270, look, mood, clamp((rel - 0.5) / 0.15) if rel >= 0.5 else 0.0,
               "point" if rel >= 0.75 else "chin", rel, (0.17 < rel < 0.185) or (0.63 < rel < 0.645),
               6 * math.sin(2 * math.pi * t / 1.0))
    place(cv, m, 150, 400)
    # sawal card + thappe
    qt, qh = lay["q_top"], lay["qh"]
    place(cv, card_sprite(1000, qh, PAPER, (255, 255, 255), 3, 30), W / 2, qt + qh / 2)
    keys = set(q_highlights(data["question"]))
    for k, ln in enumerate(lay["ql"]):
        _ink_words(d, ln, W / 2, qt + 32 + lay["lh"] / 2 + k * lay["lh"], lay["fq"], INK, PEN_RED, keys)
    lv = {"hard": ("LEVEL: कठिन", RED), "medium": ("LEVEL: मध्यम", ORANGE)}.get(data.get("level", ""))
    if lv:
        place(cv, pill_sprite(lv[0], 28, WHITE, lv[1], WHITE), W / 2 + 20, qt - 6)
    if data["times_asked"] >= 2:
        place(cv, repeat_stamp(data["times_asked"]), W - 200, qt - 30, angle=5)
    # options (chitra-dabbe ya rows), active pe peeli roshni
    for i, (L, txt) in enumerate(data["options"]):
        bx, by, bw, bh = lay["boxes"][i]
        if lay["mode"] == "pic":
            place(cv, pic_tile(L, txt, data["opt_imgs"][L], i == act), bx, by, scale=1.03 if i == act else 1.0)
        else:
            place(cv, _opt_row(L, txt, i == act, 1000, lay["oh"], lay["os"]), bx, by)
    draw_pen(cv, lay["boxes"][act], t - act * dur / 4, dur / 4)
    # toppers
    if data.get("toppers"):
        tp = "कल सही बताने वाले:  " + "   ".join("@" + u for u in data["toppers"])
        place(cv, pill_sprite(tp, 30, WHITE, (14, 90, 50), GREEN), W / 2, 1418)
    # CTA + jawab ka bada patta (mascot ishaara kare tab tez dhadkan)
    cta = data.get("_cta") or "8 सेकंड में बताओ:  A / B / C / D ?"
    if rel >= 0.5:
        cta = data.get("_sub") or "उस दोस्त को भेजो जो ये गलत करेगा"
    place(cv, pill_sprite(cta, 40, (30, 20, 0), YELLOW, ORANGE), W / 2, 1490,
          scale=1 + 0.03 * math.sin(2 * math.pi * t / 1.0))
    fast = rel >= 0.75
    place(cv, answer_banner(data.get("_ans_text") or "सही जवाब कमेंट में है"), W / 2, 1592,
          scale=1 + (0.06 if fast else 0.025) * math.sin(2 * math.pi * t / (0.5 if fast else 1.0)))
    return cv


@lru_cache(maxsize=4)
def answer_banner(text):
    """Bada laal-safed patta + neeche ki taraf teer: 'सही जवाब कमेंट में है'."""
    f = get_font(60)
    tw = int(text_w(text, f))
    w, h = tw + 220, 112
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=26, fill=(220, 30, 45, 255), outline=WHITE + (255,), width=5)
    d.text((w / 2, h / 2 + 2), text, font=f, fill=WHITE + (255,), anchor="mm")
    for ax in (55, w - 55):                                  # dono taraf neeche teer (comment ki taraf)
        d.polygon([(ax - 26, 38), (ax + 26, 38), (ax, 80)], fill=(255, 214, 10, 255))
        d.rectangle((ax - 10, 18, ax + 10, 42), fill=(255, 214, 10, 255))
    return im


def build_loop_reel(data, out):
    resolve_font()
    lay = loop_layout2(data, 1345 if data.get("toppers") else 1420)
    n = int(LOOP_DUR * FPS)
    music = beat_music(LOOP_DUR, seed=data["episode"]) * 0.85
    # AWAAZ KI PEHCHAN: shuru me stopwatch 'tick-tick-DING' + har second halki tick (MinuteMe = ghadi)
    add_at(music, sfx_tick(0.55), 0.0)
    add_at(music, sfx_tick(0.55), 0.14)
    add_at(music, sfx_ding(0.42), 0.30)
    for k in range(1, int(LOOP_DUR)):
        add_at(music, sfx_tick(0.22), float(k))
    for ph in range(4):                                     # pen ki 'scribble'
        add_at(music, sfx_whoosh(0.5, 0.12), ph * LOOP_DUR / 4 + 0.15)
    add_at(music, sfx_pop(0.4), LOOP_DUR * 0.75)            # mascot chaunka
    music = np.clip(music, -0.98, 0.98)
    step = max(1, FPS // 15)                      # 15 alag frame/sec kaafi (halki halchal)
    encode_frames(lambda fi: render_loop_frame(data, lay, fi / FPS), n, music, out, key=lambda fi: fi // step)
    print(f"LOOP REEL TAIYAR: {out} ({LOOP_DUR:.0f}s)")
    return LOOP_DUR


def loop_caption(data):
    opts = "\n".join(f"({L}) {t}" for L, t in data["options"])
    src = data.get("exam_raw") or ", ".join(data["exams"][:1])
    return "\n".join([
        f"❓ {data['question']}",
        opts,
        "",
        f"📌 {src} में पूछा गया" + (f" ({data['times_asked']} बार)" if data["times_asked"] >= 2 else ""),
        "💬 8 सेकंड में जवाब कमेंट करो - सही जवाब + वजह पहले कमेंट में।",
        "📤 उस दोस्त को भेजो जो Railway / SSC / Police की तैयारी कर रहा है।",
        f"{subj_word(data['subject'])} GK Question | RRB NTPC, Group D, SSC GD, State Exam PYQ",
        f"⏱ {BRAND} - {BRAND_TAGLINE}",
        "",
        f"🎯 {(data.get('audience') or AUDIENCES[0])[0]} + हर GS exam के लिए",
        "",
        f"#gkquiz #gkpyq {(data.get('audience') or AUDIENCES[0])[1]} {SUBJ_TAGS.get(data['subject'], '#gk')}",
    ])


def answer_comment(data):
    lines = [f"✅ सही जवाब: ({data['correct']}) {data['correct_text']}"]
    if data.get("why"):
        lines.append(f"💡 वजह: {data['why']}")
    if data.get("trap"):
        lines.append(f"⚠️ Trap: {data['trap']}")
    if data.get("tip"):
        lines.append(f"📝 याद रखो: {data['tip']}")
    lines.append("🏆 सही बताने वालों के नाम अगली रील में!")
    lines.append(f"⏱ {BRAND_TAGLINE}  Follow {BRAND_HANDLE}")
    if WHATSAPP_NUMBER:
        lines.append(f"📲 Free test / notes: WhatsApp {WHATSAPP_NUMBER}")
    return "\n".join(lines)


COMMENT_LOG = {}


def post_comment(media_id, text):
    """Reel pe pehla comment (jawab). 4 koshish (reel taiyar hone me der lagti hai); nateeja progress.json me
    'comment_log' me save (GitHub log na khule tab bhi wajah dikhe). Fail ho to bhi reel post ho chuki hai."""
    if not media_id or not IG_ACCESS_TOKEN:
        return None
    last = None
    for attempt in range(4):
        time.sleep(15 if attempt == 0 else 25)
        try:
            r = requests.post(f"{GRAPH}{media_id}/comments", data={"message": text, "access_token": IG_ACCESS_TOKEN},
                              timeout=60).json()
        except Exception as exc:
            r = {"error": {"message": str(exc)[:200]}}
        last = r
        if r.get("id"):
            print("  Jawab comment ho gaya:", r["id"])
            COMMENT_LOG.update({"media": media_id, "ok": True, "comment_id": r["id"], "tries": attempt + 1,
                                "time": time.strftime("%Y-%m-%d %H:%M")})
            return r["id"]
        print(f"  Jawab comment koshish {attempt + 1} fail:", str(r)[:300])
        err = (r.get("error") or {})
        if err.get("code") in (10, 200, 190) or "permission" in str(err.get("message", "")).lower():
            break                                   # permission/token ki dikkat: dobara koshish bekaar
    COMMENT_LOG.update({"media": media_id, "ok": False, "error": str((last or {}).get("error") or last)[:400],
                        "time": time.strftime("%Y-%m-%d %H:%M")})
    return None


# ---------- 7 PYQ LIST (10s, notebook page, sawal + jawab -> SAVE) ----------

def list_ok(q):
    if len(q["question"].split()) > LIST_MAX_Q_WORDS:
        return False
    if len(str(q["options"][q["answer"]]).split()) > LIST_MAX_A_WORDS:
        return False
    qc = clean_text(q["question"])
    txt = qc + str(q["options"][q["answer"]])
    if re.search(r"[^ऀ-ॿ -~‐-‧]", txt) or "__" in qc:
        return False
    # bina options ke list me ye sawal ulte/adhoore lagte hain
    # 'वर्तमान/मौजूदा' = jawab badal chuka ho sakta hai (list me AI ke alawa ye doosri suraksha)
    return not re.search(r"नहीं|असत्य|गलत|निम्न|इनमें से|इनमे से|सही कथन|पता लगाया|वर्तमान|मौजूदा|हाल ही|अभी", qc)


def pick_list_items(bank, st):
    """Agle sawal ka subject; usi subject ke chhote, bina-post sawal (AI se jaanch ke) 7 tak."""
    done = set(st["posted"]) | set(st["skipped"])
    pending = [q for q in sorted(bank, key=lambda x: int(x["seq"])) if q["id"] not in done]
    if not pending:
        return None, []
    today = []                                  # 'aaj ke din' wala title band: hamesha ek subject ("जीव विज्ञान के 7 PYQ")
    subject = next((q["subject"] for q in pending if list_ok(q)), pending[0]["subject"])
    items = []
    for q in (today if subject == "TODAY" else pending):
        if subject != "TODAY" and (q["subject"] != subject or not list_ok(q)):
            continue
        ai = ai_enrich(q)
        if ai and ai.get("reject"):
            st["skipped"][q["id"]] = ai["reject"]
            continue
        qq = clean_text((ai or {}).get("question") or q["question"])
        aa = clean_text(((ai or {}).get("options") or {}).get(q["answer"]) or q["options"][q["answer"]])
        items.append({"id": q["id"], "seq": q["seq"], "q": qq, "a": aa})
        if len(items) >= LIST_N:
            break
    return subject, items


@lru_cache(maxsize=2)
def _paper_bg():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    for y in range(200, 1700, 56):
        d.line((0, y, W, y), fill=(200, 215, 240), width=2)
    d.line((110, 0, 110, H), fill=(240, 150, 150), width=3)
    return im


def list_title(subject):
    if subject == "TODAY":
        return "आज ही के दिन पूछे गए PYQ"
    if subject == "WEEK":
        return f"इस हफ्ते के {LIST_N} PYQ - Revision"
    hi = SUBJECT_STYLE.get(subject, ("GK",))[0].split("•")[-1].strip()
    return f"{hi} के {LIST_N} PYQ"


def render_list_frame(subject, items):
    cv = _paper_bg().copy()
    d = ImageDraw.Draw(cv)
    d.text((W / 2, 245), list_title(subject), font=get_font(84), fill=PEN_BLUE, anchor="mm")
    d.line((200, 300, W - 200, 300), fill=PEN_BLUE, width=5)
    sub = {"TODAY": f"आज की तारीख ({today_dm()[0]}) के पुराने पेपर  •  SAVE करो",
           "WEEK": "हफ्ते भर में पूछे गए - कितने याद हैं?  •  SAVE करो"}.get(subject, "पिछले पेपरों में पूछे गए  •  SAVE करो")
    d.text((W / 2, 335), sub, font=get_font(34), fill=PEN_RED, anchor="mm")
    ex = "RRB • SSC • Police • Patwari • Army • State Exams"
    fe = next(get_font(z) for z in (32, 30, 28, 26, 24) if text_w(ex, get_font(z)) + 40 <= W - 260)
    we = text_w(ex, fe) + 40
    d.rounded_rectangle((W / 2 - we / 2, 357, W / 2 + we / 2, 397), radius=20, fill=(18, 32, 72))
    d.text((W / 2, 377), ex, font=fe, fill=(255, 225, 90), anchor="mm")
    top, bottom = 420, 1580
    for size in (42, 40, 38, 36, 34, 32):                 # sab 7 aaram se fit (koi line upar na chadhe)
        blocks = []
        for k, it in enumerate(items):
            f, s_, lines = fit_lines(f"{k + 1}. {it['q']}", 900, 2, size, size)
            blocks.append((f, int(s_ * 1.22), lines[:2], it["a"]))
        need = sum(lh * len(ls) + int(size * 1.35) for _, lh, ls, _ in blocks)
        if need + 14 * (len(items) - 1) <= bottom - top:
            break
    gap = max(0, (bottom - top - need) / max(1, len(items) - 1))
    y = top
    fa = get_font(size + 2)
    for f, lh, lines, ans in blocks:
        for j, ln in enumerate(lines):
            d.text((140, y + j * lh), " ".join(ln), font=f, fill=INK, anchor="la")
        y += lh * len(lines) + 2
        d.text((175, y), "Ans :  ", font=fa, fill=PEN_BLUE, anchor="la")
        d.text((175 + text_w("Ans :  ", fa), y), ans, font=fa, fill=PEN_BLUE, anchor="la")
        y += int(size * 1.35) + gap
    sw = stopwatch_sprite(70, 0.0)
    cv.paste(sw, (150, 1597), sw)
    d.text((235, 1618), BRAND_HANDLE, font=get_font(36), fill=INK, anchor="lm")
    d.text((235, 1660), f"कितने पहले से आते थे?  कमेंट करो __/{len(items)}   •   दोस्तों को भेजो",
           font=get_font(30), fill=PEN_RED, anchor="lm")
    return cv


def build_list_reel(subject, items, out):
    resolve_font()
    frame = render_list_frame(subject, items)
    music = beat_music(LIST_DUR, seed=len(items))
    encode_frames(lambda fi: frame, int(LIST_DUR * FPS), music, out, key=lambda fi: 0)
    frame.save(os.path.join(os.path.dirname(out) or ".", "thumbnail.jpg"), quality=92)
    print(f"LIST REEL TAIYAR: {out} ({LIST_DUR:.0f}s)")
    return LIST_DUR


def list_caption(subject, items):
    lines = [f"📚 {list_title(subject)} - RRB, SSC, Police, Patwari, Army, State Exams के लिए (Save करो)", ""]
    lines += [f"{k + 1}. {it['q']} → {it['a']}" for k, it in enumerate(items)]
    lines += ["", "💬 कितने पहले से आते थे? कमेंट करो: 7/7?",
              "📤 Save करो + उस दोस्त को भेजो जो exam की तैयारी कर रहा है।",
              f"{'GK' if subject in ('TODAY', 'WEEK') else subj_word(subject)} GK Questions | RRB NTPC, Group D, SSC GD, State Exam PYQ",
              f"⏱ {BRAND} - {BRAND_TAGLINE}"]
    if WHATSAPP_NUMBER:
        lines.append(f"📲 Free test / notes: WhatsApp {WHATSAPP_NUMBER}")
    lines += ["", f"#gkquiz #rrbntpc #sscgd #gkpyq {SUBJ_TAGS.get(subject, '#gk')}"]
    return "\n".join(lines)


def run_list(bank, st, ep, args):
    revision = is_sunday() and len(st.get("recent", [])) >= 5
    if revision:                                       # Sunday: hafte ke PYQ ka revision (wapas aane ki aadat)
        subject, items = "WEEK", [it for it in st["recent"] if list_ok_text(it["q"], it["a"])][-LIST_N:]
    else:
        subject, items = pick_list_items(bank, st)
    if len(items) < 4:
        print("List ke liye kaafi chhote sawal nahi -> loop format")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    build_list_reel(subject, items, out)
    caption = list_caption(subject, items)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.no_post or DRY_RUN:
        save_progress(st)
        return True
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    elif not post_reel(out, caption, 0):
        save_progress(st)
        return True
    if not revision:
        st["posted"] += [it["id"] for it in items]
    st["episode"] = ep
    st["last"] = {"seq": items[-1]["seq"], "id": items[-1]["id"], "time": time.strftime("%Y-%m-%d %H:%M"),
                  "format": "list"}
    save_progress(st)
    return True


# ---------- QUIZ NOTEBOOK: 7 PYQ wala page, par jawab KHAALI -> 7s countdown -> pen se jawab likhe jaate ----------
# Winner (7 PYQ list) ka look + quiz ka maza: dekhne wala khud sochta hai, score comment karta hai, dobara dekhta hai.

QUIZ_THINK = 7.0                    # itne second sirf sawal (jawab ki jagah ____ ?)
QUIZ_STEP = 0.7                     # har jawab ke beech ka samay
QUIZ_WRITE = 0.45                   # ek jawab "likhne" ka samay (bayen se dayen)
QUIZ_DUR = 14.0                     # 120 BPM ke 7 bar


def quiz_title(subject):
    if subject == "TODAY":
        return "आज के दिन पूछे गए PYQ"
    hi = SUBJECT_STYLE.get(subject, ("GK",))[0].split("•")[-1].strip()
    return f"{hi} के {LIST_N} PYQ"


def quiz_layout(items, top=430, bottom=1570, sizes=(42, 40, 38, 36, 34, 32)):
    for size in sizes:
        blocks = []
        for k, it in enumerate(items):
            f, s_, lines = fit_lines(f"{k + 1}. {it['q']}", 900, 2, size, size)
            blocks.append((f, int(s_ * 1.22), lines[:2], it["a"]))
        need = sum(lh * len(ls) + int(size * 1.35) for _, lh, ls, _ in blocks)
        if need + 14 * (len(items) - 1) <= bottom - top:
            break
    gap = max(0, (bottom - top - need) / max(1, len(items) - 1))
    fa = get_font(size + 2)
    lab = "उत्तर :  "
    rows, y = [], top
    for f, lh, lines, ans in blocks:
        rows.append({"f": f, "lh": lh, "lines": lines, "y": y})
        y += lh * len(lines) + 2
        rows[-1]["ay"] = y
        y += int(size * 1.35) + gap
    return {"rows": rows, "fa": fa, "lab": lab, "ax": 175 + text_w(lab, fa), "size": size}


def _tick_mark(d, x, y, s, col=PEN_RED):
    d.line((x, y, x + s * 0.35, y + s * 0.4), fill=col, width=max(4, int(s / 7)))
    d.line((x + s * 0.35, y + s * 0.4, x + s, y - s * 0.45), fill=col, width=max(4, int(s / 7)))


@lru_cache(maxsize=2)
def _quiz_base(subject, key):
    items, lay = _QUIZ_CACHE[key]
    cv = _paper_bg().copy()
    d = ImageDraw.Draw(cv)
    title = quiz_title(subject)
    msg = f"सभी {len(items)} जवाब इसी स्क्रीन पर आएँगे  -  अंत तक देखो"
    fb = get_font(38)
    w = text_w(msg, fb) + 60
    d.rounded_rectangle((W / 2 - w / 2, 128, W / 2 + w / 2, 186), radius=29, fill=(18, 32, 72))
    d.text((W / 2, 157), msg, font=fb, fill=(255, 225, 90), anchor="mm")
    d.text((W / 2, 250), title, font=get_font(80), fill=PEN_BLUE, anchor="mm")
    d.line((170, 302, W - 170, 302), fill=PEN_BLUE, width=5)
    for k, r in enumerate(lay["rows"]):
        for j, ln in enumerate(r["lines"]):
            d.text((140, r["y"] + j * r["lh"]), " ".join(ln), font=r["f"], fill=INK, anchor="la")
        d.text((175, r["ay"]), lay["lab"], font=lay["fa"], fill=PEN_BLUE, anchor="la")
    sw = stopwatch_sprite(70, 0.0)
    cv.paste(sw, (150, 1597), sw)
    d.text((235, 1618), BRAND_HANDLE, font=get_font(36), fill=INK, anchor="lm")
    d.text((235, 1660), BRAND_TAGLINE + "   •   दोस्तों को भेजो", font=get_font(28), fill=PEN_RED, anchor="lm")
    return cv


_QUIZ_CACHE = {}


@lru_cache(maxsize=16)
def _ans_sprite(text, size):
    f = get_font(size)
    w, h = int(text_w(text, f)) + 12, int(size * 1.45)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2, 0), text, font=f, fill=PEN_BLUE + (255,), anchor="la")
    return im


@lru_cache(maxsize=64)
def _count_sprite(n, frac_q):
    """Bada laal countdown gola: number + ghatti hui ring."""
    S = 170
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, S - 6, S - 6), fill=(200, 25, 40, 255), outline=(255, 225, 90, 255), width=8)
    if frac_q < 20:
        d.arc((18, 18, S - 18, S - 18), -90, -90 + 360 * (1 - frac_q / 20), fill=WHITE + (255,), width=7)
    d.text((S / 2, S / 2 + 4), str(n), font=get_font(92), fill=WHITE + (255,), anchor="mm")
    return im


def render_quiz_frame(subject, key, t):
    items, lay = _QUIZ_CACHE[key]
    cv = _quiz_base(subject, key).copy()
    d = ImageDraw.Draw(cv)
    fa = lay["fa"]
    size = lay["size"] + 2
    if t < QUIZ_THINK:                                   # sochne ka samay: countdown + khaali jawab
        left = int(math.ceil(QUIZ_THINK - t))
        if QUIZ_THINK - t > 2.0:
            sub, col = f"चैलेंज: {len(items)} में से कितने आते हैं?", PEN_RED
        else:                                            # aakhri 2 sec: "aa rahe hain" chamakta hai
            sub, col = "जवाब आ रहे हैं...  तैयार?", (PEN_RED if int(t * 6) % 2 else PEN_BLUE)
        d.text((W / 2 - 60, 350), sub, font=get_font(44), fill=col, anchor="mm")
        frac = t / QUIZ_THINK
        d.rounded_rectangle((150, 392, W - 230, 404), radius=6, fill=(235, 225, 225))
        d.rounded_rectangle((150, 392, 150 + (W - 380) * (1 - frac), 404), radius=6, fill=PEN_RED)
        within = t - math.floor(t)                       # har second number "pop" hota hai
        sc = 0.75 + 0.25 * ease_out_back(clamp(within / 0.35))
        cs = _count_sprite(left, int(within * 20))
        cs = cs.resize((int(cs.width * sc), int(cs.height * sc)), Image.LANCZOS)
        cv.paste(cs, (int(W - 120 - cs.width / 2), int(350 - cs.height / 2)), cs)
    else:
        if t < QUIZ_THINK + QUIZ_STEP * len(items) + 0.3:
            d.text((W / 2, 350), "अब मिलाओ - कितने सही?", font=get_font(44), fill=PEN_RED, anchor="mm")
        else:                                            # ant: score maango (comment)
            msg = f"{len(items)}/{len(items)} = टॉपर!  तुम्हारे कितने?  कमेंट करो"
            fb = get_font(46)
            w = text_w(msg, fb) + 60
            d.rounded_rectangle((W / 2 - w / 2, 318, W / 2 + w / 2, 384), radius=14, fill=PEN_RED)
            d.text((W / 2, 351), msg, font=fb, fill=WHITE, anchor="mm")
    for k, r in enumerate(lay["rows"]):
        t0 = QUIZ_THINK + k * QUIZ_STEP
        x, y = lay["ax"], r["ay"]
        if t < t0:                                       # khaali line + laal ?
            d.line((x, y + size * 1.05, x + 260, y + size * 1.05), fill=(150, 160, 190), width=3)
            pul = 1.0 + 0.18 * abs(math.sin(math.pi * (t * 2 + k * 0.3)))
            d.text((x + 290, y + size * 0.6), "?", font=get_font(int(size * 1.15 * pul)), fill=PEN_RED,
                   anchor="mm")
            continue
        sp = _ans_sprite(items[k]["a"], size)
        p = clamp((t - t0) / QUIZ_WRITE)
        cw = max(1, int(sp.width * ease_out_cubic(p)))
        part = sp.crop((0, 0, cw, sp.height))
        cv.paste(part, (int(x), int(y)), part)
        if p >= 1:
            _tick_mark(d, x + sp.width + 22, y + size * 0.55, size * 0.75)
    return cv


def build_quiz_reel(subject, items, out):
    resolve_font()
    key = "|".join(it["id"] for it in items)
    _QUIZ_CACHE[key] = (items, quiz_layout(items, top=445))
    music = beat_music(QUIZ_DUR, seed=len(items) + 3) * 0.8
    for k in range(int(QUIZ_THINK)):
        add_at(music, sfx_tick(0.5), float(k))
        if k >= QUIZ_THINK - 3:
            add_at(music, sfx_heartbeat(0.5), float(k))
    add_at(music, sfx_riser(1.0, 0.22), QUIZ_THINK - 1.0)
    add_at(music, sfx_ding(0.5), QUIZ_THINK)
    for k in range(len(items)):
        add_at(music, sfx_pop(0.45), QUIZ_THINK + k * QUIZ_STEP)
    add_at(music, sfx_ding(0.45), QUIZ_THINK + QUIZ_STEP * len(items) + 0.3)
    music = np.clip(music, -0.98, 0.98)
    step = max(1, FPS // 15)
    encode_frames(lambda fi: render_quiz_frame(subject, key, fi / FPS), int(QUIZ_DUR * FPS), music, out,
                  key=lambda fi: fi // step)
    render_quiz_frame(subject, key, 0.0).save(os.path.join(os.path.dirname(out) or ".", "thumbnail.jpg"),
                                              quality=92)
    print(f"QUIZ REEL TAIYAR: {out} ({QUIZ_DUR:.0f}s)")


def quiz_caption(subject, items, ep):
    aud = audience_of(ep)
    lines = [f"🧠 {quiz_title(subject)} - 7 सेकंड में कितने बता पाओगे?", ""]
    lines += [f"{k + 1}. {it['q']}" for k, it in enumerate(items)]
    lines += ["", f"💬 स्कोर कमेंट करो: {len(items)}/{len(items)} वाले जीनियस! (जवाब reel में + पहले कमेंट में)",
              "📤 दोस्त को भेजो - देखो उसके कितने सही होते हैं!",
              f"🎯 {aud[0]} + हर GS exam के लिए",
              f"⏱ {BRAND} - {BRAND_TAGLINE}", "",
              f"#gkquiz #gkpyq {aud[1]} {SUBJ_TAGS.get(subject, '#gk')}"]
    return "\n".join(lines)


def quiz_comment(items):
    lines = ["✅ सही जवाब:"] + [f"{k + 1}) {it['a']}" for k, it in enumerate(items)]
    lines += ["", f"🏆 {len(items)}/{len(items)} वाले कमेंट में हाथ उठाओ!", f"⏱ Follow {BRAND_HANDLE}"]
    return "\n".join(lines)


def run_quiz(bank, st, ep, args):
    subject, items = pick_list_items(bank, st)
    if len(items) < 5:
        print("Quiz ke liye kaafi chhote sawal nahi -> list format")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    build_quiz_reel(subject, items, out)
    caption = quiz_caption(subject, items, ep)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.no_post or DRY_RUN:
        save_progress(st)
        return True
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    else:
        pid = post_reel(out, caption, 0)                 # pehla frame (khaali jawab) = cover
        if not pid:
            save_progress(st)
            return True
        post_comment(pid, quiz_comment(items))
    st["posted"] += [it["id"] for it in items]
    remember_recent(st, items)
    st["episode"] = ep
    st["last"] = {"seq": items[-1]["seq"], "id": items[-1]["id"], "time": time.strftime("%Y-%m-%d %H:%M"),
                  "format": "quiz"}
    save_progress(st)
    return True


# ---------- GALTI PAKDO: "टॉपर की कॉपी" - 7 sawal-jawab, 1 jawab jaan-boojhkar galat ----------
# vidIQ: viral = 1 static padhne layak page + music + 8-10s loop; jawab chhupa -> comment, 7 jawab -> save.
# Yahan dono: poora page padhna padta hai (loop/watch time) + galti ka number comment (engagement).
# Sahi jawab pehle comment me (galat jaankari aage na jaaye).

GALTI_DUR = 4.0                     # bahut chhoti: galti dhoondhte-dhoondhte reel 3-4 baar loop
GALTI_N = 6                         # kam sawal = bada font, jaldi padh ke galti pakad sake

GALTI_PROMPT = """Ye Indian govt exam (RRB/SSC) ke PYQ hain, har ek: id | sawal | sahi jawab.
{rows}

Kaam:
1) Inme se sabse AASAN 10 chuno - jinka jawab aam 10vi pass student ko turant pata ho (rozmarra / bahut prasiddh GK).
   Mushkil, aankde wale, ya kam-jaane tathya wale mat chuno. Jawab bilkul sahi hona chahiye, warna chhod do.
2) Har chune hue ke liye ek GALAT jawab do (Hindi, 1-3 shabd) jo usi type ka ho par aam student turant pakad le
   ki ye galat hai (jaise sahi 'दिल्ली' -> galat 'मुंबई'; sahi 'आँख' -> galat 'कान'). Kabhi sahi ya aadha-sahi jawab mat do.
Sirf JSON: {{"easy": [{{"id": "...", "wrong": "..."}}, ...]}}  (sabse aasan pehle)"""


def _galti_cands(bank, st):
    done = set(st["posted"]) | set(st["skipped"])
    out = []
    for q in sorted(bank, key=lambda x: int(x["seq"])):
        if q["id"] in done or not list_ok(q) or len(q["question"].split()) > 12:
            continue
        a = clean_text(str(q["options"][q["answer"]]))
        if len(a.split()) > 3 or len(re.findall(r"\d", a)) > 4:
            continue
        out.append(q)
        if len(out) >= 40:
            break
    return out


def _galti_ai_easy(cands):
    rows = "\n".join(f"{q['id']} | {clean_text(q['question'])} | {clean_text(str(q['options'][q['answer']]))}"
                     for q in cands)
    prompt = GALTI_PROMPT.format(rows=rows)
    for fn in (_gemini, _groq):
        js = fn(prompt) if not DRY_RUN else None
        if js and isinstance(js.get("easy"), list):
            return [(e.get("id"), clean_text(str(e.get("wrong") or ""))) for e in js["easy"] if isinstance(e, dict)]
    return None


def _galti_wrong(q, ans):
    """Asli sawal ke galat options me se ek chhota, saaf, bharosemand galat jawab."""
    for k in ("a", "b", "c", "d"):
        if k == q["answer"]:
            continue
        w = clean_text(str(q["options"].get(k, "")))
        same = set(w.replace(",", " ").split()) & set(ans.replace(",", " ").split())
        if same:                                   # '22 अप्रैल 1973' vs '01 अप्रैल 1973' jaisi baal ki khaal nahi
            continue
        if (w and w != ans and len(w.split()) <= LIST_MAX_A_WORDS
                and not re.search(r"सभी|कोई नहीं|इनमें|उपर्युक्त|दोनों|[^ऀ-ॿ -~‐-‧]", w)):
            return w
    return None


def pick_galti(bank, st, ep):
    """AASAN sawal (taaki zyada log galti pakad ke comment karein): AI se chune, warna sabse zyada baar poochhe gaye."""
    cands = _galti_cands(bank, st)
    by_id = {q["id"]: q for q in cands}
    easy = _galti_ai_easy(cands) or []
    easy = [(i, w) for i, w in easy if i in by_id]
    if len(easy) < GALTI_N:                           # AI nahi: zyada baar poochha + chhota = aam taur par aasan
        have = {i for i, _ in easy}
        rest = sorted((q for q in cands if q["id"] not in have),
                      key=lambda q: (-int(q.get("times_asked") or 1), len(q["question"].split())))
        easy += [(q["id"], "") for q in rest]
    items, wrongs = [], {}
    for qid, w in easy:
        q = by_id[qid]
        ai = ai_enrich(q)
        if ai and ai.get("reject"):
            st["skipped"][q["id"]] = ai["reject"]
            continue
        qq = clean_text((ai or {}).get("question") or q["question"])
        aa = clean_text(((ai or {}).get("options") or {}).get(q["answer"]) or q["options"][q["answer"]])
        items.append({"id": q["id"], "seq": q["seq"], "q": qq, "a": aa})
        ok_w = (w and w != aa and len(w.split()) <= 3 and not (set(w.split()) & set(aa.split()))
                and not re.search(r"[^ऀ-ॿ -~‐-‧]", w))
        wrongs[q["id"]] = w if ok_w else _galti_wrong(q, aa)
        if len(items) >= GALTI_N:
            break
    if len(items) < 5:
        return "MIX", items, None
    order = list(range(1, len(items) - 1)) + [0, len(items) - 1]      # beech wala pehle (seedha na dikhe)
    rot = ep % max(1, len(items) - 2)
    order = order[rot:] + order[:rot]
    for k in order:
        if wrongs.get(items[k]["id"]):
            items[k] = dict(items[k], wrong=wrongs[items[k]["id"]])
            return "MIX", items, k
    return "MIX", items, None


def galti_title(subject):
    return "टॉपर की कॉपी चेक करो"


@lru_cache(maxsize=2)
def _galti_base(key):
    subject, items, bad = _GALTI_CACHE[key]
    cv = _paper_bg().copy()
    d = ImageDraw.Draw(cv)
    f, sz, lines = fit_lines(galti_title(subject), 900, 1, 80, 56)
    d.text((W / 2, 228), " ".join(lines[0]), font=f, fill=PEN_BLUE, anchor="mm")
    d.line((170, 282, W - 170, 282), fill=PEN_BLUE, width=5)
    msg = "इसमें 1 जवाब गलत है!"
    fb = get_font(52)
    w = text_w(msg, fb) + 64
    d.rounded_rectangle((W / 2 - w / 2, 305, W / 2 + w / 2, 382), radius=16, fill=PEN_RED)
    d.text((W / 2, 342), msg, font=fb, fill=WHITE, anchor="mm")
    d.text((W / 2, 412), "आसान सवाल हैं - फिर भी पकड़ पाओगे?", font=get_font(36), fill=INK, anchor="mm")
    lay = quiz_layout(items, top=485, bottom=1520, sizes=(52, 50, 48, 46, 44, 42, 40, 38, 36))
    fa = lay["fa"]
    for k, r in enumerate(lay["rows"]):
        for j, ln in enumerate(r["lines"]):
            d.text((140, r["y"] + j * r["lh"]), " ".join(ln), font=r["f"], fill=INK, anchor="la")
        ans = items[k].get("wrong") or items[k]["a"]
        d.text((175, r["ay"]), "Ans :  " + ans, font=fa, fill=PEN_BLUE, anchor="la")
    d.text((W / 2, 1560), f"गलत वाला नंबर कमेंट करो  (1-{len(items)})", font=get_font(46), fill=PEN_RED,
           anchor="mm")
    sw = stopwatch_sprite(70, 0.0)
    cv.paste(sw, (150, 1597), sw)
    d.text((235, 1618), BRAND_HANDLE, font=get_font(36), fill=INK, anchor="lm")
    d.text((235, 1660), BRAND_TAGLINE + "   •   दोस्त को चैलेंज करो", font=get_font(28), fill=PEN_RED,
           anchor="lm")
    return cv, lay


_GALTI_CACHE = {}


@lru_cache(maxsize=1)
def _lens_sprite(size=120):
    S = size
    im = Image.new("RGBA", (S + 70, S + 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, S, S), fill=(255, 240, 150, 55), outline=(40, 40, 50, 255), width=10)
    d.line((S - 18, S - 18, S + 60, S + 60), fill=(90, 50, 20, 255), width=22)
    d.line((S - 18, S - 18, S + 60, S + 60), fill=(140, 85, 35, 255), width=12)
    return im


def render_galti_frame(key, t):
    base, lay = _galti_base(key)
    cv = base.copy()
    rows = lay["rows"]
    # lens upar se neeche aur wapas (seamless loop): sab jawabon par ghoomta hai
    ph = (t % GALTI_DUR) / GALTI_DUR
    u = 1 - abs(1 - 2 * ph)                               # 0 -> 1 -> 0
    k = int(round(u * (len(rows) - 1)))                  # sirf jawab ki line par rukta hai (sawal nahi dhakta)
    y = rows[k]["ay"] + lay["size"] * 0.6
    x = 560 + 90 * math.sin(2 * math.pi * ph * 2)
    lens = _lens_sprite()
    cv.paste(lens, (int(x - 63), int(y - 63)), lens)
    d = ImageDraw.Draw(cv)                                # 10 sec ka timer (loop me phir bharta hai)
    d.rounded_rectangle((200, 446, W - 200, 454), radius=4, fill=(235, 225, 225))
    d.rounded_rectangle((200, 446, 200 + (W - 400) * (1 - ph), 454), radius=4, fill=PEN_RED)
    return cv


def build_galti_reel(subject, items, bad, out):
    resolve_font()
    key = "|".join(it["id"] for it in items)
    _GALTI_CACHE[key] = (subject, items, bad)
    music = beat_music(GALTI_DUR, seed=len(items) + 7) * 0.85
    add_at(music, sfx_buzz(0.35), 0.05)
    music = np.clip(music, -0.98, 0.98)
    step = max(1, FPS // 15)
    encode_frames(lambda fi: render_galti_frame(key, fi / FPS), int(GALTI_DUR * FPS), music, out,
                  key=lambda fi: fi // step)
    _galti_base(key)[0].save(os.path.join(os.path.dirname(out) or ".", "thumbnail.jpg"), quality=92)
    print(f"GALTI REEL TAIYAR: {out} ({GALTI_DUR:.0f}s)  galat = #{bad + 1}")


def galti_caption(subject, items, ep):
    aud = audience_of(ep)
    lines = [f"🔍 {galti_title(subject)}: इसमें 1 जवाब गलत है - पकड़ पाओगे?", "",
             f"💬 गलत जवाब का नंबर कमेंट करो (1-{len(items)}) - सही जवाब पहले कमेंट में।",
             "📤 दोस्त को भेजो - देखें वो पकड़ पाता है या नहीं!",
             f"🎯 {aud[0]} + हर GS exam के लिए",
             f"⏱ {BRAND} - {BRAND_TAGLINE}", "",
             f"#gkquiz #gkpyq {aud[1]} {SUBJ_TAGS.get(subject, '#gk')}"]
    return "\n".join(lines)


def galti_comment(items, bad):
    it = items[bad]
    lines = [f"✅ गलती नंबर {bad + 1} में थी!",
             f"सवाल: {it['q']}",
             f"❌ {it['wrong']}   →   ✔️ सही जवाब: {it['a']}",
             "", f"बाकी {len(items) - 1} जवाब सही हैं - Save कर लो।", f"⏱ Follow {BRAND_HANDLE}"]
    return "\n".join(lines)


def run_galti(bank, st, ep, args):
    subject, items, bad = pick_galti(bank, st, ep)
    if bad is None:
        print("Galti format ke liye sahi sawal/galat option nahi -> list format")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    build_galti_reel(subject, items, bad, out)
    caption = galti_caption(subject, items, ep)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    Path(os.path.join(OUTPUT_DIR, "comment.txt")).write_text(galti_comment(items, bad), encoding="utf-8")
    print("\nCAPTION:\n" + caption + "\n\nCOMMENT:\n" + galti_comment(items, bad))
    if args.no_post or DRY_RUN:
        save_progress(st)
        return True
    if POST_MODE == "manual":
        save_ready(out, caption + "\n\n" + galti_comment(items, bad), ep)
    else:
        pid = post_reel(out, caption, 0)
        if not pid:
            save_progress(st)
            return True
        post_comment(pid, galti_comment(items, bad))
    st["posted"] += [it["id"] for it in items]
    remember_recent(st, [{k: v for k, v in it.items() if k != "wrong"} for it in items])
    st["episode"] = ep
    st["last"] = {"seq": items[-1]["seq"], "id": items[-1]["id"], "time": time.strftime("%Y-%m-%d %H:%M"),
                  "format": "galti"}
    save_progress(st)
    return True


# ---------- MEGA REVISION: "सभी सरकारी परीक्षाओं के लिए - Physics के 100 सबसे महत्वपूर्ण प्रश्न" ----------
# Viral reel (@sscprepfocus, Oct 2026): 7 page x 30 sawal-jawab, har page ~3s. Itna ek baar me padhna mumkin
# nahi -> log PAUSE karte hain, SAVE karte hain, baar-baar dekhte hain (watch time + save sabse zyada).
# Shuru me AI awaaz: "SSC, Railway... is reel ko skip karne ki galti mat karna".

MEGA_PER_PAGE = 20                  # 1080 chaudai pe 20 line padhne layak (reference 30 thi, par chhota font)
MEGA_PAGES = 5                      # 100 sawal
MEGA_PAGE_DUR = 3.0
MEGA_SLIDE = 0.22                   # page badalne ki slide
MEGA_END = 1.3                      # aakhir me 'SAVE + Follow' patta
MEGA_MIN_FONT = 30
MEGA_SUBJ = ["Physics", "Chemistry", "Biology", "History", "Polity", "Geography", "Economics", "Traditional GK",
             "Environment", "Computer"]
_MEGA_JUNK = re.compile(r"[\[\]@÷{}|\\^~`◌µÀ-ÿ]|ृ\?$|=\s*$|औरीं|भ्ण्|ण्ह|फ्ह|न्न्|ज्ञ्|ष्टण्|उश्|स्/|घ्(?=\s|$)|[क-ह]्(?=[\d,.)\-–]|$)")
# bina options/sandarbh ke adhoore lagne wale sawal (sawal-ganit, 'yadi...', 'ek vastu...')
_MEGA_VAGUE = re.compile(r"^(\d|यदि|अगर|किसी|एक |दिए|दी गई|उपरोक्त|निम्न)|=|तो |इसलिए|गणना|ज्ञात कर")


def subj_names(subject):
    lab = SUBJECT_STYLE.get(subject, ("GK  •  सामान्य ज्ञान",))[0]
    en, _, hi = lab.partition("•")
    return hi.strip() or "सामान्य ज्ञान", en.strip().title() if en.strip() != "GK" else "GK"


def _mega_row_text(q, a):
    q = re.sub(r"\s*(निम्नलिखित|निम्न)\s+में\s+से\s*", " ", q)            # bina options ke 'nimn me se' bekaar
    q = re.sub(r"[-\s]*-[-\s]*-[-\s]*", " ____ ", q).strip()
    q = " ".join(q.split()).rstrip(" ?।:-") + "?"
    return q, a.strip(" .।")


def _mega_fits(q, a, size=MEGA_MIN_FONT):
    f = get_font(size)
    return text_w(f"100. {q}  {a}", f) <= MEGA_TEXT_W


MEGA_TEXT_W = 900
MEGA_ROW0, MEGA_ROW_H = 332, 61


def pick_mega(bank, st):
    """Agla subject (baari-baari) + uske sabse zyada baar poochhe gaye chhote sawal (1 line me fit)."""
    used = set(st.get("mega_used", []))
    n0 = st.get("mega_n", 0)
    for k in range(len(MEGA_SUBJ)):
        subject = MEGA_SUBJ[(n0 + k) % len(MEGA_SUBJ)]
        pool, seen = [], set()
        for q in bank:
            if q["subject"] != subject or q["id"] in used:
                continue
            qq, aa = _mega_row_text(clean_text(q["question"]), clean_text(q["options"][q["answer"]]))
            if (len(qq.split()) > 16 or len(aa.split()) > 5 or "__" in qq
                    or re.search(r"नहीं|असत्य|गलत|इनमें से|इनमे से|सही कथन|कथन|वर्तमान|मौजूदा|हाल ही|अभी|उपर्युक्त", qq)):
                continue
            if (not qq or not aa or _MEGA_JUNK.search(qq + " " + aa) or _MEGA_VAGUE.search(qq) or qq in seen
                    or re.fullmatch(r"\d+[A-Za-z]", aa)):
                continue
            seen.add(qq)
            pool.append({"id": q["id"], "seq": q["seq"], "q": qq, "a": aa, "n": int(q.get("times_asked") or 1),
                         "fit": _mega_fits(qq, aa)})
        pool.sort(key=lambda x: (-x["n"], not x["fit"], int(x["seq"])))   # sabse zyada repeat = 'sabse mahatvapurn'
        # AI lambe sawal chhote karke 1 line me la sakta hai; AI na chale to sirf jo already fit hain
        checked = _mega_ai_check(pool[:MEGA_PAGES * MEGA_PER_PAGE + 60])
        pool = checked if checked is not None else [x for x in pool if x["fit"]]
        pages = min(MEGA_PAGES, len(pool) // MEGA_PER_PAGE)
        if pages >= 2:
            return subject, pool[:pages * MEGA_PER_PAGE], (n0 + k) % len(MEGA_SUBJ)
    return None, [], n0


MEGA_PROMPT = """Ye Indian govt exam (RRB/SSC) ke PYQ hain, har line: id | sawal | sahi jawab.
Ye ek revision page pe BINA options ke ek line me chhapenge.
{rows}

Sirf wo id rakho jinme: sawal akela padhkar poora samajh aaye (adhoora / options pe tika / ganit wala NAHI),
jawab bilkul sahi aur aaj bhi sahi ho, aur text me koi toota/ajeeb akshar na ho.
Har rakhe gaye sawal ko CHHOTA likho: sawal 9 shabd tak, jawab 4 shabd tak (matlab bilkul mat badlo,
spelling theek karo). Udaharan: 'द्रव्यमान और वेग का गुणनफल क्या कहलाता है?' -> 'द्रव्यमान × वेग = ?' nahi,
balki 'द्रव्यमान और वेग का गुणनफल?' (Hindi hi rakho).
Sirf JSON: {{"ok": [{{"id": "...", "q": "...", "a": "..."}}, ...]}}  (diye gaye kram me)"""


def _mega_ai_check(pool):
    """Ek hi AI call me 100+ line ki jaanch + chhota karna. AI na chale -> None."""
    rows = "\n".join(f"{x['id']} | {x['q']} | {x['a']}" for x in pool)
    for fn in (_gemini, _groq):
        js = fn(MEGA_PROMPT.format(rows=rows)) if not DRY_RUN else None
        if js and isinstance(js.get("ok"), list):
            by = {x["id"]: x for x in pool}
            out = []
            for e in js["ok"]:
                x = by.get(str(e.get("id"))) if isinstance(e, dict) else None
                if not x:
                    continue
                q2, a2 = _mega_row_text(clean_text(e.get("q") or x["q"]), clean_text(e.get("a") or x["a"]))
                if q2 and a2 and _mega_fits(q2, a2) and not _MEGA_JUNK.search(q2 + " " + a2):
                    out.append(dict(x, q=q2, a=a2))
                elif x["fit"]:
                    out.append(x)
            print(f"  Mega AI jaanch: {len(pool)} me se {len(out)} sahi")
            if len(out) >= 2 * MEGA_PER_PAGE:
                return out
    return None


def mega_title(subject, n):
    hi, en = subj_names(subject)
    return f'"{hi} ({en})" के {n} सबसे महत्वपूर्ण प्रश्न' if en != "GK" else f'"सामान्य ज्ञान" के {n} सबसे महत्वपूर्ण प्रश्न'


@lru_cache(maxsize=4)
def _mega_paper(subject):
    col = SUBJECT_STYLE.get(subject, ("", CYAN))[1]
    im = Image.new("RGB", (W, H), (234, 230, 250))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((26, 26, W - 26, H - 26), radius=46, fill=PAPER, outline=mix(col, (60, 40, 140), 0.55),
                        width=7)
    d.rounded_rectangle((40, 40, W - 40, H - 40), radius=38, outline=mix(col, (255, 255, 255), 0.45), width=3)
    for i in range(MEGA_PER_PAGE):
        y = MEGA_ROW0 + i * MEGA_ROW_H + 31
        d.line((60, y, W - 60, y), fill=(222, 228, 242), width=2)
    return im


def render_mega_page(subject, rows, start, page, pages, total):
    cv = _mega_paper(subject).copy()
    d = ImageDraw.Draw(cv)
    # sabse upar: kis-kis ke liye (bharosa + 'mere exam ka hai')
    t1 = "सभी सरकारी परीक्षाओं के लिए"
    f1 = get_font(50)
    w1 = text_w(t1, f1) + 80
    d.rounded_rectangle((W / 2 - w1 / 2, 70, W / 2 + w1 / 2, 150), radius=40, fill=(255, 255, 255),
                        outline=(40, 40, 70), width=4)
    d.text((W / 2, 110), t1, font=f1, fill=INK, anchor="mm")
    place(cv, stopwatch_sprite(78, (page + 1) / pages), 100, 110)
    pg = pill_sprite(f"पेज {page + 1}/{pages}", 26, WHITE, PEN_RED, WHITE)
    place(cv, pg, W - 70 - pg.width / 2, 110)
    # title: "भौतिक विज्ञान (Physics)" के 100 सबसे महत्वपूर्ण प्रश्न  (ank laal)
    title = mega_title(subject, total)
    ft = next(get_font(z) for z in (50, 46, 42, 40, 38, 36) if text_w(title, get_font(z)) <= W - 120)
    sp = text_w(" ", ft)
    words = title.split()
    x = W / 2 - (sum(text_w(w_, ft) for w_ in words) + sp * (len(words) - 1)) / 2
    for w_ in words:
        d.text((x, 205), w_, font=ft, fill=PEN_RED if w_.isdigit() else (60, 30, 150), anchor="lm")
        x += text_w(w_, ft) + sp
    d.text((W / 2, 262), "SSC  •  Railway  •  Police  •  Patwari  •  Army  •  State Exams",
           font=get_font(28), fill=PEN_RED, anchor="mm")
    d.line((140, 292, W - 140, 292), fill=(60, 30, 150), width=4)
    # 20 line: (n) sawal?  jawab
    size = next(z for z in (38, 36, 34, 32, MEGA_MIN_FONT)
                if all(text_w(f"{start + len(rows)}. {r['q']}  {r['a']}", get_font(z)) <= MEGA_TEXT_W for r in rows))
    f = get_font(size)
    fn = get_font(24)
    for i, r in enumerate(rows):
        y = MEGA_ROW0 + i * MEGA_ROW_H
        n = start + i + 1
        d.ellipse((58, y - 21, 100, y + 21), outline=(60, 30, 150), width=3, fill=(255, 255, 255))
        d.text((79, y + 1), str(n), font=fn, fill=(60, 30, 150), anchor="mm")
        d.text((116, y), r["q"], font=f, fill=INK, anchor="lm")
        d.text((116 + text_w(r["q"] + "  ", f), y), r["a"], font=f, fill=PEN_BLUE, anchor="lm")
    # neeche: SAVE patta + brand
    t3 = "SAVE करो  -  Exam से पहले 1 बार ज़रूर देखना!"
    f3 = get_font(38)
    w3 = text_w(t3, f3) + 70
    d.rounded_rectangle((W / 2 - w3 / 2, 1645, W / 2 + w3 / 2, 1715), radius=35, fill=(255, 255, 255),
                        outline=(40, 40, 70), width=4)
    d.text((W / 2, 1680), t3, font=f3, fill=PEN_RED, anchor="mm")
    d.text((W / 2, 1772), BRAND_HANDLE + "   •   " + BRAND_TAGLINE, font=get_font(30), fill=(60, 30, 150),
           anchor="mm")
    return cv


@lru_cache(maxsize=2)
def _skip_stamp():
    """Pehle page pe tircha laal thappa (bina awaaz dekhne walon ke liye wahi baat)."""
    f = get_font(40)
    t = "Skip करने की गलती मत करना!"
    w, h = int(text_w(t, f)) + 60, 80
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=22, fill=(220, 30, 45, 245), outline=WHITE + (255,), width=5)
    d.text((w / 2, h / 2 + 2), t, font=f, fill=WHITE + (255,), anchor="mm")
    return im


def mega_end_card(last):
    im = Image.blend(last.convert("RGB"), Image.new("RGB", (W, H), (10, 12, 24)), 0.72)
    place(im, stopwatch_sprite(220, 0.75), W / 2, 760)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 960), BRAND_HANDLE, font=get_font(70), fill=WHITE, anchor="mm")
    d.text((W / 2, 1050), "SAVE करो  •  दोस्तों को भेजो  •  Follow करो", font=get_font(42), fill=YELLOW, anchor="mm")
    return im


def mega_voice(subject, n, rot):
    """Shuru ki AI awaaz. Gemini na chale -> None (sirf music)."""
    if not GEMINI_API_KEY:
        return None
    hi, _ = subj_names(subject)
    line = (f"SSC, Railway, Police... सभी सरकारी exams के लिए, {hi} के {n} सबसे important सवाल! "
            f"इस reel को skip करने की गलती मत करना... अभी Save कर लो!")
    try:
        arr, label = gemini_tts_once([line], rot)
        print("  Mega awaaz:", label)
    except Exception as exc:
        print("  Mega awaaz nahi bani (sirf music):", str(exc)[:150])
        return None
    arr = np.asarray(arr, dtype=np.float32)
    loud = np.where(np.abs(arr) > 0.02 * (np.max(np.abs(arr)) or 1))[0]
    if len(loud):
        arr = arr[max(0, loud[0] - int(0.05 * SR)): loud[-1] + int(0.15 * SR)]
    try:
        arr = speed_voice(arr)
    except Exception:
        pass
    return arr


def build_mega_reel(subject, items, out, rot=0):
    resolve_font()
    pages = len(items) // MEGA_PER_PAGE
    imgs = [render_mega_page(subject, items[p * MEGA_PER_PAGE:(p + 1) * MEGA_PER_PAGE], p * MEGA_PER_PAGE, p,
                             pages, len(items)) for p in range(pages)]
    voice = mega_voice(subject, len(items), rot)
    vdur = len(voice) / SR if voice is not None else 0.0
    first = max(MEGA_PAGE_DUR + 0.6, vdur + 0.6)              # awaaz pehle page pe hi khatam ho
    starts = [0.0]
    for p in range(1, pages):
        starts.append(first + (p - 1) * MEGA_PAGE_DUR)
    end_t = starts[-1] + MEGA_PAGE_DUR
    total = end_t + MEGA_END
    stamp = _skip_stamp()
    first_img = imgs[0].copy()
    place(first_img, stamp, W / 2, 1590, angle=-3)
    end_img = mega_end_card(imgs[-1])

    def page_at(t):
        return max(i for i, s0 in enumerate(starts) if t >= s0)

    def render(fi):
        t = fi / FPS
        if t >= end_t:
            return end_img
        p = page_at(t)
        cur = first_img if p == 0 and t < first - 0.4 else imgs[p]
        k = (t - starts[p]) / MEGA_SLIDE if p > 0 else 1.0
        if k >= 1:
            return cur
        e = ease_out_cubic(clamp(k))                         # naya page daayen se aata hai
        cv = imgs[p - 1].copy()
        cv.paste(cur, (int(W * (1 - e)), 0))
        return cv

    def key(fi):
        t = fi / FPS
        if t >= end_t:
            return "end"
        p = page_at(t)
        if p > 0 and t - starts[p] < MEGA_SLIDE:
            return fi
        return ("p", p, p == 0 and t < first - 0.4)

    music = beat_music(total, seed=len(items)) * 0.32
    if voice is not None:
        add_at(music, voice, 0.15, 1.0)
    for s0 in starts[1:]:
        add_at(music, sfx_whoosh(0.3, 0.4), s0 - 0.05)
    add_at(music, sfx_ding(0.4), end_t)
    music = np.clip(music, -0.98, 0.98)
    encode_frames(render, int(total * FPS), music, out, key=key)
    first_img.save(os.path.join(os.path.dirname(out) or ".", "thumbnail.jpg"), quality=92)
    print(f"MEGA REEL TAIYAR: {out} ({total:.1f}s, {pages} page, {len(items)} sawal)")
    return total


def mega_caption(subject, items):
    hi, en = subj_names(subject)
    return "\n".join([
        f"📚 {mega_title(subject, len(items))} - सभी सरकारी परीक्षाओं के लिए",
        "",
        "⏸️ हर पेज पर रोककर पढ़ो (स्क्रीन दबाकर रखो)",
        "📌 अभी SAVE करो - exam से पहले 1 बार ज़रूर revise करना",
        "📤 उस दोस्त को भेजो जो SSC / Railway / Police की तैयारी कर रहा है",
        "💬 कितने पहले से आते थे? कमेंट करो!",
        "",
        f"{hi} ({en}) GK | RRB NTPC, Group D, SSC GD, CGL, MTS, Police, Patwari, State Exam PYQ",
        f"⏱ {BRAND} - {BRAND_TAGLINE}",
        "",
        f"#gk #gkquiz #gkpyq #sscgd #rrbntpc #rrbgroupd #policebharti {SUBJ_TAGS.get(subject, '#gk')}",
    ])


def run_mega(bank, st, ep, args):
    subject, items, idx = pick_mega(bank, st)
    if not items:
        print("Mega ke liye kaafi chhote sawal nahi -> list format")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    build_mega_reel(subject, items, out, rot=ep)
    caption = mega_caption(subject, items)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.no_post or DRY_RUN:
        return True
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    elif not post_reel(out, caption, 0):
        save_progress(st)
        return True
    st["mega_used"] = (st.get("mega_used", []) + [it["id"] for it in items])[-3000:]
    st["mega_n"] = idx + 1                                   # agli baar agla subject
    st["episode"] = ep
    st["last"] = {"seq": items[-1]["seq"], "id": items[-1]["id"], "time": time.strftime("%Y-%m-%d %H:%M"),
                  "format": "mega"}
    save_progress(st)
    return True


# ---------- TRIPLE: "3 सवाल, 16 सेकंड" challenge (score comment + dost ko challenge = share) ----------

TRI_DUR = 16.0                      # 120 BPM ke 8 bar; 3 sawal x 5.33s
TRI_N = 3
RECENT_KEEP = 21


def is_sunday():
    return time.gmtime(time.time() + 19800).tm_wday == 6


def list_ok_text(q, a):
    q, a = clean_text(q), clean_text(a)
    if len(q.split()) > LIST_MAX_Q_WORDS + 4 or len(a.split()) > LIST_MAX_A_WORDS + 1 or "__" in q:
        return False
    return not re.search(r"नहीं|असत्य|गलत|निम्न|इनमें से|इनमे से|सही कथन|वर्तमान|मौजूदा", q)


def remember_recent(st, items):
    """Hafte ka revision (Sunday list) ke liye aakhri post hue sawal-jawab."""
    rec = st.setdefault("recent", [])
    have = {x["id"] for x in rec}
    rec += [it for it in items if it["id"] not in have]
    st["recent"] = rec[-RECENT_KEEP:]


def pick_triple(bank, st, ep):
    """Alag-alag subject ke 3 sawal (GS ka mix = har exam wala jude), AI jaanch ke saath."""
    done = set(st["posted"]) | set(st["skipped"])
    pending = [q for q in sorted(bank, key=lambda x: int(x["seq"])) if q["id"] not in done and reel_friendly(q)]
    chosen, subs = [], set()
    for q in pending:
        if q["subject"] in subs or len(q["question"].split()) > 18:
            continue
        ai = ai_enrich(q)
        if ai and ai.get("reject"):
            st["skipped"][q["id"]] = ai["reject"]
            continue
        d_ = prepare_data(q, ai, ep, None, {})
        d_["opt_imgs"] = make_option_images(q, ai)
        chosen.append(d_)
        subs.add(q["subject"])
        if len(chosen) >= TRI_N:
            break
    return chosen


def build_triple_reel(datas, out):
    resolve_font()
    seg = TRI_DUR / len(datas)
    lays = []
    for k, d_ in enumerate(datas):
        d_["_dur"] = seg
        d_["_hook"] = f"सवाल {k + 1}/{len(datas)}  -  {len(datas)}/{len(datas)} सही = जीनियस!"
        d_["_cta"] = "5 सेकंड!  जवाब याद रखो..." if k < len(datas) - 1 else "कितने सही?  कमेंट करो: 3/3 ?"
        d_["_sub"] = "दोस्त को भेजो: देखें उसके कितने सही होते हैं"
        d_["_ans_text"] = "तीनों के जवाब कमेंट में हैं"
        d_["toppers"] = []
        lays.append(loop_layout2(d_, 1420))
    music = beat_music(TRI_DUR, seed=datas[0]["episode"]) * 0.85
    add_at(music, sfx_tick(0.55), 0.0)
    add_at(music, sfx_tick(0.55), 0.14)
    add_at(music, sfx_ding(0.42), 0.30)
    for k in range(1, len(datas)):
        add_at(music, sfx_whoosh(0.3, 0.45), k * seg - 0.12)
        add_at(music, sfx_pop(0.5), k * seg)
    for k in range(1, int(TRI_DUR)):
        add_at(music, sfx_tick(0.2), float(k))
    music = np.clip(music, -0.98, 0.98)

    def render(fi):
        t = fi / FPS
        k = min(len(datas) - 1, int(t / seg))
        return render_loop_frame(datas[k], lays[k], t - k * seg)

    step = max(1, FPS // 15)
    encode_frames(render, int(TRI_DUR * FPS), music, out, key=lambda fi: fi // step)
    print(f"TRIPLE REEL TAIYAR: {out} ({TRI_DUR:.0f}s)")


def triple_caption(datas, ep):
    aud = audience_of(ep)
    lines = [f"🧠 {len(datas)} PYQ, {int(TRI_DUR)} सेकंड - कितने सही कर पाओगे?", ""]
    for k, d_ in enumerate(datas):
        lines.append(f"{k + 1}. {d_['question']}")
        lines.append("    " + "  ".join(f"({L}) {t}" for L, t in d_["options"]))
    lines += ["", "💬 स्कोर कमेंट करो: 3/3, 2/3 या 1/3 - सही जवाब पहले कमेंट में।",
              "📤 दोस्त को भेजो - देखो किसके ज़्यादा सही होते हैं!",
              f"🎯 {aud[0]} + हर GS exam के लिए",
              f"⏱ {BRAND} - {BRAND_TAGLINE}", "",
              f"#gkquiz #gkpyq {aud[1]} #gk"]
    return "\n".join(lines)


def triple_comment(datas):
    lines = ["✅ सही जवाब:"]
    for k, d_ in enumerate(datas):
        lines.append(f"{k + 1}) ({d_['correct']}) {d_['correct_text']}")
    lines += ["", "🏆 3/3 वाले जीनियस हो - कमेंट में बताओ!", f"⏱ {BRAND_TAGLINE}  Follow {BRAND_HANDLE}"]
    return "\n".join(lines)


def run_triple(bank, st, ep, args):
    datas = pick_triple(bank, st, ep)
    if len(datas) < TRI_N:
        print("Triple ke liye 3 sahi sawal nahi mile -> loop format")
        return False
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, FINAL_VIDEO)
    build_triple_reel(datas, out)
    caption = triple_caption(datas, ep)
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.no_post or DRY_RUN:
        save_progress(st)
        return True
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    else:
        pid = post_reel(out, caption, 0)
        if not pid:
            save_progress(st)
            return True
        post_comment(pid, triple_comment(datas))
    st["posted"] += [d_["id"] for d_ in datas]
    remember_recent(st, [{"id": d_["id"], "seq": d_["seq"], "q": d_["question"], "a": d_["correct_text"]}
                         for d_ in datas])
    st["episode"] = ep
    st["last"] = {"seq": datas[-1]["seq"], "id": datas[-1]["id"], "time": time.strftime("%Y-%m-%d %H:%M"),
                  "format": "triple"}
    save_progress(st)
    return True


# ============================== MAIN ==============================

def pick_question(bank, st, seq=None):
    by_seq = {q["seq"]: q for q in bank}
    if seq:
        return [by_seq[seq]]
    done = set(st["posted"]) | set(st["skipped"])
    n = len(bank)
    start = 1                       # kram me pehla bina-post sawal (bank ka kram badle to bhi sahi)
    out = []
    for k in range(n):
        q = by_seq.get(((start - 1 + k) % n) + 1)
        if q and q["id"] not in done and reel_friendly(q):
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
    ep = st["episode"] + 1
    fmt = "classic" if args.preview else pick_format(ep)
    if args.seq and fmt in ("list", "triple", "quiz", "galti", "mega"):
        fmt = "loop"
    print(f"FORMAT: {fmt}")
    if fmt == "mega":
        if run_mega(bank, st, ep, args):
            return
        fmt = "list"
    if fmt == "galti":
        if run_galti(bank, st, ep, args):
            return
        fmt = "list"
    if fmt == "quiz":
        if run_quiz(bank, st, ep, args):
            return
        fmt = "list"
    if fmt == "list":
        if run_list(bank, st, ep, args):
            return
        fmt = "loop"
    if fmt == "triple":
        if run_triple(bank, st, ep, args):
            return
        fmt = "loop"
    cands = pick_question(bank, st, args.seq)
    if not args.seq and fmt == "loop":              # aaj ki tareekh wale PYQ pehle (sirf hamara data)
        done = set(st["posted"]) | set(st["skipped"])
        tod = [q for q in bank if q["id"] not in done and reel_friendly(q) and today_exam(q)]
        if tod:
            print(f"  Aaj ki tareekh ke {len(tod)} PYQ baaki")
            cands = tod[:3] + [c for c in cands if c not in tod[:3]]
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
    if fmt == "loop":
        data["opt_imgs"] = make_option_images(chosen, ai)
        if not args.seq:
            data["toppers"] = fetch_toppers(st)
        build_loop_reel(data, out)
        thumb_ms = 0                                        # pehla frame hi poora sawal = cover
        caption = loop_caption(data)
    else:
        total = build_reel(data, out)
        thumb_ms = int((total - POSTER_TAIL / 2) * 1000)   # poster (cover) ant me hai
        caption = make_caption(data)
    try:
        make_thumbnail(data).save(os.path.join(OUTPUT_DIR, "thumbnail.jpg"), quality=92)
    except Exception as exc:
        print("  thumbnail save nahi hua:", str(exc)[:100])
    Path(os.path.join(OUTPUT_DIR, "caption.txt")).write_text(caption, encoding="utf-8")
    print("\nCAPTION:\n" + caption)
    if args.seq:
        print("--seq mode: progress nahi badla.")
        if not args.no_post:
            pid = post_reel(out, caption, thumb_ms)
            if fmt == "loop":
                post_comment(pid, answer_comment(data))
        return
    if args.no_post or DRY_RUN:
        save_progress(st)
        return
    if POST_MODE == "manual":
        save_ready(out, caption, ep)
    else:
        pid = post_reel(out, caption, thumb_ms)
        if not pid:
            save_progress(st)
            return
        if fmt == "loop":
            post_comment(pid, answer_comment(data))
            st["last_loop"] = {"media": pid, "correct": data["correct"]}
        remember_recent(st, [{"id": data["id"], "seq": data["seq"], "q": data["question"],
                              "a": data["correct_text"]}])
    st["posted"].append(chosen["id"])
    carousel_step(st, data)
    st["episode"] = ep
    st["next_seq"] = chosen["seq"] + 1
    st["last"] = {"seq": chosen["seq"], "id": chosen["id"], "time": time.strftime("%Y-%m-%d %H:%M")}
    save_progress(st)


if __name__ == "__main__":
    main()
