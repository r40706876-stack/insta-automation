import os
import json
import time
import re
import subprocess
import asyncio
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts
import fitz  # PyMuPDF

# =====================================================================
# 1. Configuration & Global Variables
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0/"
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_production"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = os.path.join(ASSETS_DIR, "Mukta-Bold.ttf")
FINAL_VIDEO = "biology_auto_reel.mp4"
PROGRESS_FILE = "progress.json"
PDF_FILE = "Parmar Biology (1).pdf"

MALE_VOICE = "hi-IN-MadhurNeural"
FEMALE_VOICE = "hi-IN-SwaraNeural"

RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS
WHATSAPP_NUMBER = "8989971379"

# =====================================================================
# 2. Competitive Exam & Number-Based Hooks (1 to 7 Rotation)
# =====================================================================
HOOKS_LIST = [
    "Sirf 1 number se selection ruk jata hai? Yeh galti dobara mat karna!",
    "90 percent students is sawal mein phas jaate hain, kya aapko sahi jawab pata hai?",
    "Agar paper mein 2 number pakke karne hain, toh yeh 30 sekund ki reel poori dekh lo!",
    "Ek-ek number ki laadai hai! Yeh concept miss kiya toh rank peeche ho jayegi.",
    "Competition mein aage nikalna hai? Toh yeh number game aaj hi samajh lo.",
    "Sirf 3 minute do, aur exam ke 5 marks pakke karo!",
    "Ye ek number aapki poori mehnat palat sakta hai, dhyan se dekh lo!"
]

# =====================================================================
# 3. Universal Phonetic Engine (Text Sanitization)
# =====================================================================
class UniversalPhoneticEngine:
    NUM_MAP = {
        "0": "शून्य", "1": "एक", "2": "दो", "3": "तीन", "4": "चार",
        "5": "पांच", "6": "छह", "7": "सात", "8": "आठ", "9": "नौ",
        "10": "दस", "11": "ग्यारह", "12": "बारह", "13": "तेरह",
        "14": "चौदह", "15": "पंद्रह", "16": "सोलह", "17": "सत्रह",
        "18": "अठारह", "19": "उन्नीस", "20": "बीस", "95%": "पचानवे प्रतिशत", "90%": "नब्बे प्रतिशत"
    }

    SUBSTITUTIONS = {
        r"\bप्रश्न\b": "सवाल",
        r"\bप्रश्नों\b": "सवालों",
        r"\bद्विगुणन\b": "कॉपी बनने",
        r"\bकोशिकांगों\b": "कोशिका अंगों",
        r"\bकोशिकांग\b": "कोशिका अंग",
        r"\bसमसूत्री\b": "सम सूत्री",
        r"\bअर्धसूत्री\b": "अर्ध सूत्री",
        r"\bगुणसूत्रों\b": "गुण सूत्रों",
        r"\bगुणसूत्र\b": "गुण सूत्र",
        r"\bकायिक\b": "शारीरिक",
        r"\bअगुणित\b": "हाफ",
        r"\bDNA\b": "डीएनए",
        r"\bRNA\b": "आरएनए",
        r"\bATP\b": "एटीपी",
        r"\bHCl\b": "हाइड्रोक्लोरिक एसिड",
        r"\bS-Phase\b": "एस फेज",
        r"\bरील\b": "वीडियो",
        r"\bReel\b": "वीडियो"
    }

    @classmethod
    def sanitize(cls, text):
        for num, word in cls.NUM_MAP.items():
            text = re.sub(rf"\b{re.escape(num)}\b", word, text)

        nukta_map = {"ज़": "ज", "फ़": "फ", "क़": "क", "ख़": "ख", "ग़": "ग", "ड़": "ड", "ढ़": "ढ"}
        for k, v in nukta_map.items():
            text = text.replace(k, v)

        for pattern, replacement in cls.SUBSTITUTIONS.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        text = text.replace("ज्ञ", "ग्य")
        text = text.replace("क्ष", "छ")
        text = text.replace("!", "।")
        text = text.replace("-", " ")
        text = text.replace("/", " या ")
        text = re.sub(r"[()\[\]]", ", ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

# =====================================================================
# 4. Continuous Sequential Page & Hook Tracker (Safe Bounds)
# =====================================================================
def get_continuous_pdf_chunk_with_hook():
    doc = fitz.open(PDF_FILE)
    total_pages = len(doc)
    
    start_page = 4  
    chunk_size = 3  
    hook_index = 0
    
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
                start_page = data.get("next_start_page", 4)
                hook_index = data.get("next_hook_index", 0)
        except Exception:
            start_page = 4
            hook_index = 0

    if start_page >= total_pages - 1:
        start_page = 4

    current_hook = HOOKS_LIST[hook_index % len(HOOKS_LIST)]

    next_start_page = start_page + chunk_size
    if next_start_page >= total_pages:
        next_start_page = 4 

    next_hook_index = (hook_index + 1) % len(HOOKS_LIST)
    
    with open(PROGRESS_FILE, "w") as f:
        json.dump({
            "next_start_page": next_start_page,
            "next_hook_index": next_hook_index,
            "current_batch": f"Pages {start_page} to {min(start_page + chunk_size - 1, total_pages - 1)}",
            "active_hook": current_hook
        }, f, indent=4)

    actual_count = min(chunk_size, total_pages - start_page)
    return start_page, actual_count, current_hook

def get_verified_font(size):
    if not os.path.exists(FONT_FILE) or os.path.getsize(FONT_FILE) < 50000:
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-Bold.ttf"
        try:
            r = requests.get(font_url, timeout=30)
            if r.status_code == 200:
                with open(FONT_FILE, "wb") as f:
                    f.write(r.content)
        except Exception:
            pass
    try:
        return ImageFont.truetype(FONT_FILE, size)
    except Exception:
        return ImageFont.load_default()

def extract_page_summary(page):
    text = page.get_text("text")
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 4]
    clean_lines = [l for l in lines if "PARMAR" not in l.upper() and "SSC" not in l.upper()]
    if clean_lines:
        return ", ".join(clean_lines[:2])
    return "महत्वपूर्ण प्रतियोगी परीक्षा बिंदु"

def extract_continuous_slides(start_pg, count):
    slide_files = []
    doc = fitz.open(PDF_FILE)
    extracted_texts = []

    for i in range(count):
        pg_idx = start_pg + i
        page = doc.load_page(pg_idx)
        
        page_summary = extract_page_summary(page)
        extracted_texts.append(page_summary)

        pix = page.get_pixmap(dpi=300)
        img = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        
        w, h = img.size
        header_crop_height = int(h * 0.12)
        
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w, header_crop_height], fill="#020617")
        
        target_img = Image.new("RGB", (1080, 1920), color="#020617")
        img.thumbnail((1040, 1700), RESAMPLE_MODE)
        
        px = (1080 - img.width) // 2
        py = 180 + (1700 - img.height) // 2
        target_img.paste(img, (px, py))
        
        d_target = ImageDraw.Draw(target_img)
        d_target.rounded_rectangle([35, 35, 1045, 150], radius=18, fill="#F59E0B")
        d_target.text((60, 65), f"BIOLOGY REVISION - PAGE {pg_idx+1}", fill="#000000", font=get_verified_font(32))
        
        s_path = f"slide_{i+1}.png"
        target_img.save(s_path)
        slide_files.append(s_path)

    # Slide 4: Interactive Quiz & Call To Action (Safe Layout Coordinates)
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    d4.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)
    
    d4.rounded_rectangle([75, 70, 1005, 160], radius=14, fill="#F59E0B")
    d4.text((95, 95), "EXAM CHALLENGE & REVISION", fill="#000000", font=get_verified_font(32))
    d4.text((75, 205), "कमेंट में सही उत्तर दें!", fill="#FBBF24", font=get_verified_font(46))

    d4.rounded_rectangle([75, 290, 1005, 580], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 315), "🎯 IMPORTANT QUESTION:", fill="#FBBF24", font=get_verified_font(30))
    d4.multiline_text((105, 385), textwrap.fill("इन पृष्ठों के सभी महत्वपूर्ण बिंदु परीक्षा की दृष्टि से अत्यंत आवश्यक हैं। सही विकल्प चुनें:", width=26), fill="#FFFFFF", font=get_verified_font(32), spacing=10)

    options = ["(A) सभी तथ्य पूर्णतः सत्य हैं", "(B) मुख्य बिंदु परीक्षा उपयोगी", "(C) नोट्स आधारित रिवीज़न", "(D) इनमें से कोई नहीं"]
    qy = 600
    for opt in options:
        d4.rounded_rectangle([75, qy, 1005, qy + 85], radius=14, fill="#0F172A", outline="#38BDF8", width=2)
        d4.text((110, qy + 20), opt, fill="#F8FAFC", font=get_verified_font(32))
        qy += 105

    d4.rounded_rectangle([75, 1050, 1005, 1650], radius=22, fill="#111827", outline="#10B981", width=2)
    d4.text((120, 1080), "📚 COMPLETE NOTES", fill="#34D399", font=get_verified_font(30))
    hint_desc = (
        "• सही उत्तर कमेंट में लिखें!\n\n"
        f"• WhatsApp: {WHATSAPP_NUMBER}\n\n"
        "• सम्पूर्ण नोट्स और टेस्ट के लिए मैसेज करें!"
    )
    d4.multiline_text((120, 1160), hint_desc, fill="#F8FAFC", font=get_verified_font(28), spacing=12)

    d4.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#059669")
    d4.text((95, 1748), f"WhatsApp: {WHATSAPP_NUMBER}", fill="#FFFFFF", font=get_verified_font(34))

    s4_path = "slide_4.png"
    img4.save(s4_path)
    slide_files.append(s4_path)

    return slide_files, extracted_texts

# =====================================================================
# 5. Audio & Video Compilation Engine (Safe Length Handling)
# =====================================================================
async def generate_audio_clip(text, voice, filename):
    clean_text = UniversalPhoneticEngine.sanitize(text) if voice == MALE_VOICE else text
    rate = "-4%" if voice == MALE_VOICE else "+0%"
    comm = edge_tts.Communicate(text=clean_text, voice=voice, rate=rate, pitch="+2Hz" if voice == MALE_VOICE else "+0Hz")
    await comm.save(filename)

async def make_all_voice_clips(extracted_texts, current_hook):
    while len(extracted_texts) < 3:
        extracted_texts.append("महत्वपूर्ण प्रतियोगी परीक्षा तथ्य")

    scripts = [
        f"{current_hook} Pehli slide par diye gaye in binduon ko dekhiye: {extracted_texts[0]}",
        f"Agli slide par yeh mukhya bindu samjhein: {extracted_texts[1]}",
        f"Teesri slide ke in tathyon ko yaad rakhein: {extracted_texts[2]}",
        "अब स्क्रीन पर दिख रहे इस सवाल का सही उत्तर जल्दी से कमेंट में लिखकर बताओ। और पूरे सिलेबस के सटीक नोट्स के लिए स्क्रीन पर दिए गए नंबर पर अभी व्हाट्सएप करें।"
    ]
    
    audio_files = []
    for i, sc in enumerate(scripts):
        voice = MALE_VOICE if i % 2 == 0 else FEMALE_VOICE
        fn = f"voice_part_{i+1}.mp3"
        await generate_audio_clip(sc, voice, fn)
        audio_files.append(fn)
    return audio_files

def compile_alternate_video(slide_files, audio_files, output_file):
    durations = []
    for af in audio_files:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", af]
        dur = float(subprocess.check_output(cmd).decode().strip())
        durations.append(dur)

    total_dur = sum(durations)
    target_dur = 58.5
    speed_factor = round(total_dur / target_dur, 3)
    
    if speed_factor < 0.5:
        speed_factor = 0.5
    elif speed_factor > 2.0:
        speed_factor = 2.0

    balanced_audios = []
    balanced_durations = []
    for i, af in enumerate(audio_files):
        out_af = f"balanced_{af}"
        subprocess.run(["ffmpeg", "-y", "-i", af, "-filter:a", f"atempo={speed_factor}", out_af], check=True)
        balanced_audios.append(out_af)
        b_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", out_af]).decode().strip())
        balanced_durations.append(b_dur)

    with open("audio_list.txt", "w") as f:
        for b_af in balanced_audios:
            f.write(f"file '{b_af}'\n")

    combined_audio = "combined_voice.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "audio_list.txt", "-c", "copy", combined_audio], check=True)
    final_audio_dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", combined_audio]).decode().strip())

    inputs = []
    filter_complex = ""
    for idx, s_path in enumerate(slide_files):
        inputs.extend(["-i", s_path])
        filter_complex += f"[{idx}:v]loop=loop=-1:size=1:start=0,trim=duration={balanced_durations[idx]},setpts=PTS-STARTPTS[v{idx}]; "

    concat_inputs = "".join([f"[v{i}]" for i in range(len(slide_files))])
    filter_complex += f"{concat_inputs}concat=n={len(slide_files)}:v=1:a=0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p[vout]"

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", combined_audio,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{len(slide_files)}:a",
        "-t", f"{final_audio_dur:.2f}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)

# =====================================================================
# 6. Instagram Upload Engine
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption):
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        return

    init_url = f"{GRAPH_API_BASE}{IG_USER_ID}/media"
    data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    r = requests.post(init_url, data=data, timeout=60).json()
    video_id = r.get("id")
    upload_url = r.get("uri") or f"{RUPLOAD_BASE}{video_id}"

    time.sleep(10)
    file_size = os.path.getsize(video_file)
    headers = {
        "Authorization": f"OAuth {IG_ACCESS_TOKEN}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Type": "application/octet-stream"
    }

    with open(video_file, "rb") as vf:
        video_bytes = vf.read()

    requests.post(upload_url, headers=headers, data=video_bytes, timeout=600)

    status_url = f"{GRAPH_API_BASE}{video_id}"
    for _ in range(35):
        time.sleep(12)
        res = requests.get(status_url, params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN}).json()
        if res.get("status_code") == "FINISHED":
            break

    pub_url = f"{GRAPH_API_BASE}{IG_USER_ID}/media_publish"
    requests.post(pub_url, data={"creation_id": video_id, "access_token": IG_ACCESS_TOKEN})

# =====================================================================
# 7. Main Execution Pipeline
# =====================================================================
if __name__ == "__main__":
    start_page, page_count, selected_hook = get_continuous_pdf_chunk_with_hook()
    print(f"\n🎯 Active Hook: {selected_hook}", flush=True)
    print(f"🎯 Processing PDF sequentially starting from page {start_page} (Count: {page_count})\n", flush=True)

    slides, extracted_texts = extract_continuous_slides(start_page, page_count)
    audio_clips = asyncio.run(make_all_voice_clips(extracted_texts, selected_hook))
    compile_alternate_video(slides, audio_clips, FINAL_VIDEO)
    
    caption_text = f"Complete Biology Revision Notes 🧬📚\n\n• {selected_hook}\n• Sahi uttar comment me zaroor likhein!\n• WhatsApp: 8989971379\n\n#BiologyShorts #ExamPrep #GovtExamPrep"
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
