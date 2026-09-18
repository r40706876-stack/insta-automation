import os
import time
import subprocess
import asyncio
import textwrap
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts

# =====================================================================
# 1. कॉन्फ़िगरेशन और डायरेक्टरी सेटअप
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0/"
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_final"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = "NotoSansDevanagari-Bold.ttf"
AUDIO_OUTPUT = "page2_voice.mp3"
FINAL_VIDEO = "biology_page2_master_reel.mp4"
VOICE_NAME = "hi-IN-MadhurNeural"

RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS

# असली शैक्षणिक चित्र (Page 2)
IMAGE_URLS = {
    "cork_cells": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Robert_Hooke_Micrographia_1665_cork_cells.jpg/800px-Robert_Hooke_Micrographia_1665_cork_cells.jpg",
    "living_cell": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Anabaena_sperica.jpg/800px-Anabaena_sperica.jpg",
    "nucleus_3d": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Diagram_human_cell_nucleus.svg/1024px-Diagram_human_cell_nucleus.svg.png",
    "trophy": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Golden_Trophy.svg/800px-Golden_Trophy.svg.png"
}

# =====================================================================
# 2. फ़ॉन्ट इंजन (डब्बा '□□□' कभी नहीं बनेगा)
# =====================================================================
def get_verified_font(size):
    system_paths = [
        FONT_FILE,
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
        "/usr/share/fonts/truetype/lohit-devanagari/Lohit-Devanagari.ttf"
    ]
    for p in system_paths:
        if os.path.exists(p) and os.path.getsize(p) > 50000:
            try:
                f = ImageFont.truetype(p, size)
                # हिंदी वर्ण टेस्ट
                if f.getbbox("को")[2] > 0:
                    return f
            except Exception:
                continue

    font_url = "https://raw.githubusercontent.com/googlefonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
    try:
        print("⏳ हिंदी फ़ॉन्ट डाउनलोड हो रहा है...", flush=True)
        r = requests.get(font_url, timeout=30)
        if r.status_code == 200 and len(r.content) > 50000:
            with open(FONT_FILE, "wb") as f:
                f.write(r.content)
            return ImageFont.truetype(FONT_FILE, size)
    except Exception as e:
        print(f"⚠️ फ़ॉन्ट त्रुटि: {e}", flush=True)

    raise RuntimeError("हिंदी फ़ॉन्ट नहीं मिला! चलाएं: sudo apt install -y fonts-noto-core")

# =====================================================================
# 3. इमेज हैंडलर और 3D ग्लो पेस्टिंग (असली फ़ोटो)
# =====================================================================
def get_verified_image(key):
    path = os.path.join(ASSETS_DIR, f"{key}.png")
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path

    url = IMAGE_URLS.get(key)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/*"
    }
    try:
        print(f"⏳ डाउनलोड हो रही है असली इमेज: {key}...", flush=True)
        res = requests.get(url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.content) > 5000:
            img = Image.open(BytesIO(res.content)).convert("RGBA")
            img.save(path, "PNG")
            return path
    except Exception as e:
        print(f"⚠️ इमेज डाउनलोड चेतावनी ({key}): {e}", flush=True)

    # साफ़ बैकअप पैनल (कोई वायरफ़्रेम गोला या जाली नहीं)
    fallback = Image.new("RGBA", (700, 500), (15, 23, 42, 255))
    df = ImageDraw.Draw(fallback)
    df.rounded_rectangle([10, 10, 690, 490], radius=20, fill="#1E293B", outline="#38BDF8", width=3)
    df.text((120, 220), f"{key.replace('_', ' ').title()}", fill="#FBBF24", font=get_verified_font(32))
    fallback.save(path, "PNG")
    return path

def paste_smooth_glow_asset(canvas, img_path, target_box, glow_rgb=(56, 189, 248), corner_radius=22):
    if not os.path.exists(img_path):
        return
    try:
        x1, y1, x2, y2 = target_box
        w, h = x2 - x1, y2 - y1

        src = Image.open(img_path).convert("RGBA")
        src.thumbnail((w - 40, h - 40), RESAMPLE_MODE)

        mask = Image.new("L", src.size, 0)
        md = ImageDraw.Draw(mask)
        md.rounded_rectangle([(0, 0), src.size], radius=corner_radius, fill=255)
        src.putalpha(mask)

        px = x1 + (w - src.width) // 2
        py = y1 + (h - src.height) // 2

        glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([px - 35, py - 25, px + src.width + 35, py + src.height + 25], fill=(*glow_rgb, 125))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=35))
        canvas.paste(glow, (0, 0), glow)

        canvas.paste(src, (px, py), src)
    except Exception as e:
        print(f"⚠️ इमेज पेस्ट त्रुटि: {e}", flush=True)

# =====================================================================
# 4. विजुअल स्लाइड्स निर्माण (PDF Page 2)
# =====================================================================
def draw_base_scaffold(draw, slide_idx, total=4):
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)

    # टॉप हेडर बार
    draw.rounded_rectangle([75, 70, 540, 135], radius=14, fill="#F59E0B")
    draw.text((95, 85), "PARMAR SSC BIOLOGY • PAGE 2", fill="#000000", font=get_verified_font(25))
    draw.text((710, 85), "@PARMAR_BIO", fill="#64748B", font=get_verified_font(28))

    # प्रोग्रेस लाइन
    bar_w = int(900 * (slide_idx / total))
    draw.rounded_rectangle([90, 155, 990, 167], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 155, 90 + bar_w, 167], radius=6, fill="#38BDF8")

    # निचला बैनर
    draw.rounded_rectangle([75, 1725, 1005, 1835], radius=18, fill="#E11D48")
    draw.text((150, 1755), "Page 2 Revision Pura! Save Aur Follow Karein!", fill="#FFFFFF", font=get_verified_font(32))

def generate_all_slides():
    slide_files = []
    f_h1 = get_verified_font(42)
    f_badge = get_verified_font(25)
    f_body = get_verified_font(30)
    f_label = get_verified_font(28)

    # ----------------- SLIDE 1 -----------------
    img1 = Image.new("RGB", (1080, 1920), color="#020617")
    d1 = ImageDraw.Draw(img1)
    draw_base_scaffold(d1, 1)

    d1.text((75, 195), "1. कोशिका की परिभाषा और खोज (1665)", fill="#38BDF8", font=f_h1)

    box1 = [75, 265, 1005, 830]
    d1.rounded_rectangle(box1, radius=22, fill="#0B132B", outline="#38BDF8", width=2)
    paste_smooth_glow_asset(img1, get_verified_image("cork_cells"), box1, glow_rgb=(56, 189, 248))
    d1.rounded_rectangle([95, 285, 490, 340], radius=10, fill="#1E3A8A")
    d1.text((115, 298), "रॉबर्ट हुक: कॉर्क मृत कोशिका (1665)", fill="#93C5FD", font=f_badge)

    d1.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d1.text((105, 890), "Page 2 के मुख्य परीक्षा बिंदु (Line-by-Line):", fill="#FBBF24", font=f_label)

    txt1 = (
        "• कोशिका: जीवन की मौलिक, संरचनात्मक और कार्यात्मक इकाई है।\n\n"
        "• Cytology: कोशिका के वैज्ञानिक अध्ययन को Cytology कहते हैं।\n\n"
        "• लैटिन नाम: 'Cellula' शब्द से बना है, जिसका अर्थ है 'छोटा कमरा' (Small Room)।\n\n"
        "• रॉबर्ट हुक (1665): पहली बार पेड़ की छाल (कॉर्क) में कोशिका देखी।\n\n"
        "• परीक्षा ट्रैप: रॉबर्ट हुक द्वारा देखी गई कोशिका मृत (Dead Cell) थी!"
    )
    d1.multiline_text((105, 955), txt1, fill="#F8FAFC", font=f_body, spacing=13)
    img1.save("slide_1.png")
    slide_files.append("slide_1.png")

    # ----------------- SLIDE 2 -----------------
    img2 = Image.new("RGB", (1080, 1920), color="#020617")
    d2 = ImageDraw.Draw(img2)
    draw_base_scaffold(d2, 2)

    d2.text((75, 195), "2. कोशिका की अन्य प्रमुख खोजें", fill="#10B981", font=f_h1)

    box2 = [75, 265, 1005, 830]
    d2.rounded_rectangle(box2, radius=22, fill="#0B132B", outline="#10B981", width=2)
    paste_smooth_glow_asset(img2, get_verified_image("living_cell"), box2, glow_rgb=(16, 185, 129))
    d2.rounded_rectangle([95, 285, 490, 340], radius=10, fill="#064E3B")
    d2.text((115, 298), "ल्यूवेनहॉक: पहली जीवित कोशिका (1674)", fill="#6EE7B7", font=f_badge)

    d2.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d2.text((105, 890), "बार-बार पूछे जाने वाले 3 वैज्ञानिक:", fill="#10B981", font=f_label)

    txt2 = (
        "• ल्यूवेनहॉक (1674): तालाब के जल में पहली 'जीवित कोशिका' (Living Cell) देखी।\n\n"
        "• रॉबर्ट ब्राउन (1831): कोशिका के केंद्रक (Nucleus) की खोज की।\n\n"
        "• पुरकिंजे (1839): कोशिका द्रव्य को 'प्रोटोप्लाज्म' (जीवद्रव्य) नाम दिया।\n\n"
        "• याद रखने की ट्रिक: हुक = मृत, ल्यूवेनहॉक = जीवित, ब्राउन = केंद्रक!"
    )
    d2.multiline_text((105, 955), txt2, fill="#F8FAFC", font=f_body, spacing=13)
    img2.save("slide_2.png")
    slide_files.append("slide_2.png")

    # ----------------- SLIDE 3 -----------------
    img3 = Image.new("RGB", (1080, 1920), color="#020617")
    d3 = ImageDraw.Draw(img3)
    draw_base_scaffold(d3, 3)

    d3.text((75, 195), "3. कोशिका सिद्धांत (Cell Theory)", fill="#F43F5E", font=f_h1)

    box3 = [75, 265, 1005, 830]
    d3.rounded_rectangle(box3, radius=22, fill="#0B132B", outline="#F43F5E", width=2)
    paste_smooth_glow_asset(img3, get_verified_image("nucleus_3d"), box3, glow_rgb=(244, 63, 94))
    d3.rounded_rectangle([95, 285, 490, 340], radius=10, fill="#881337")
    d3.text((115, 298), "केंद्रक संरचना एवं कोशिका नियंत्रण", fill="#FDA4AF", font=f_badge)

    d3.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d3.text((105, 890), "सिद्धांत के नियम और वैज्ञानिक योगदान:", fill="#F43F5E", font=f_label)

    txt3 = (
        "• श्लाइडेन और श्वान (1838-1839): कोशिका सिद्धांत प्रस्तुत किया।\n\n"
        "• मुख्य नियम: सभी पौधे और जंतु कोशिकाओं से मिलकर बने हैं।\n\n"
        "• कोशिका जीवन की सबसे मूल संरचनात्मक इकाई है।\n\n"
        "• रूडोल्फ विरचो (1855): कहा कि सभी नई कोशिकाएं पूर्व-मौजूद कोशिकाओं के विभाजन से बनती हैं।"
    )
    d3.multiline_text((105, 955), txt3, fill="#F8FAFC", font=f_body, spacing=13)
    img3.save("slide_3.png")
    slide_files.append("slide_3.png")

    # ----------------- SLIDE 4 -----------------
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    draw_base_scaffold(d4, 4)

    d4.text((75, 195), "Page 2 का लाइव टेस्ट: सही उत्तर दें!", fill="#FBBF24", font=f_h1)

    d4.rounded_rectangle([75, 260, 1005, 540], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 290), "🎯 SSC CGL / CHSL PYQ:", fill="#FBBF24", font=f_label)
    q_text = "तालाब के जल में पहली बार 'जीवित कोशिका' (Living Cell) की खोज किसने की थी?"
    d4.multiline_text((105, 350), textwrap.fill(q_text, width=27), fill="#FFFFFF", font=f_body, spacing=10)

    options = ["रॉबर्ट हुक", "ल्यूवेनहॉक", "रॉबर्ट ब्राउन", "पुरकिंजे"]
    qy = 575
    for idx, opt in enumerate(options):
        lbl = chr(65 + idx)
        d4.rounded_rectangle([75, qy, 1005, qy + 105], radius=16, fill="#0F172A", outline="#38BDF8", width=2)
        d4.rounded_rectangle([100, qy + 18, 170, qy + 88], radius=10, fill="#38BDF8")
        d4.text((120, qy + 30), lbl, fill="#000000", font=f_badge)
        d4.text((195, qy + 35), opt, fill="#F8FAFC", font=f_body)
        qy += 130

    trophy_box = [75, 1120, 1005, 1680]
    d4.rounded_rectangle(trophy_box, radius=22, fill="#111827", outline="#10B981", width=2)
    paste_smooth_glow_asset(img4, get_verified_image("trophy"), [90, 1140, 420, 1660], glow_rgb=(245, 158, 11))

    d4.text((430, 1220), "🏆 SSC TOPPER CHALLENGE", fill="#FBBF24", font=f_label)
    hint_desc = (
        "• सही उत्तर वीडियो में बताया गया है!\n\n"
        "• कमेंट सेक्शन में A, B, C या D लिखें।\n\n"
        "• अगली रील Page 3 (कोशिका के अंग) पर आएगी!"
    )
    d4.multiline_text((430, 1300), hint_desc, fill="#F8FAFC", font=get_verified_font(26), spacing=12)

    img4.save("slide_4.png")
    slide_files.append("slide_4.png")
    return slide_files

# =====================================================================
# 5. ऑडियो और FFmpeg (सटीक 52 सेकंड)
# =====================================================================
async def make_voice_resilient(text, out_file):
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate="+0%")
            await communicate.save(out_file)
            return
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(2)

def compile_video_master(slide_files, audio_file, output_file):
    cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    total_dur = float(subprocess.check_output(cmd_dur).decode().strip())
    print(f"🎙️ ऑडियो समय: {total_dur:.2f}s", flush=True)

    target_dur = 52.0
    speed_factor = round(total_dur / target_dur, 3)
    clamped_audio = "voice_clamped.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={speed_factor}", clamped_audio], check=True)
    audio_file = clamped_audio
    final_dur = float(subprocess.check_output(cmd_dur, text=True).strip())
    print(f"⚡ सेट किया गया समय: {final_dur:.2f}s", flush=True)

    weights = [1.1, 1.15, 1.15, 1.0]
    tot_w = sum(weights)
    durs = [final_dur * (w / tot_w) for w in weights]

    inputs = []
    filter_complex = ""
    for idx, s_path in enumerate(slide_files):
        inputs.extend(["-i", s_path])
        filter_complex += f"[{idx}:v]loop=loop=-1:size=1:start=0,trim=duration={durs[idx]},setpts=PTS-STARTPTS[v{idx}]; "

    concat_inputs = "".join([f"[v{i}]" for i in range(len(slide_files))])
    filter_complex += f"{concat_inputs}concat=n={len(slide_files)}:v=1:a=0,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p[vout]"

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-i", audio_file,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", f"{len(slide_files)}:a",
        "-t", f"{final_dur:.2f}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"🎬 वीडियो तैयार हो गई: {output_file}", flush=True)

# =====================================================================
# 6. इंस्टाग्राम ऑटो-अपलोड
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption, max_container_attempts=3):
    access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("IG_USER_ID", "").strip()

    if not access_token or not user_id:
        print("\n⚠️ इंस्टाग्राम टोकन या ID सेट नहीं है। वीडियो स्थानीय रूप से सेव हो गई है।", flush=True)
        return False

    print("\n🚀 इंस्टाग्राम पर अपलोड शुरू हो रहा है...", flush=True)
    last_error = None
    for attempt in range(1, max_container_attempts + 1):
        print(f"   ► प्रयास {attempt}/{max_container_attempts}...", flush=True)
        try:
            video_id = _create_reel_container(video_file, caption, user_id, access_token)
            status = _poll_container_status(video_id, access_token)

            if status == "FINISHED":
                _publish_reel(video_id, user_id, access_token)
                return True
            else:
                last_error = f"Status: {status}"
        except Exception as e:
            last_error = str(e)
            print(f"   ⚠️ प्रयास चेतावनी: {last_error}", flush=True)

        if attempt < max_container_attempts:
            time.sleep(25)

    raise RuntimeError(f"अपलोड विफल: {last_error}")

def _create_reel_container(video_file, caption, user_id, access_token):
    init_url = f"{GRAPH_API_BASE}{user_id}/media"
    data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(init_url, data=data, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"कंटेनर आरंभ विफल: {r.text}")

    video_id = r.json().get("id")
    upload_url = r.json().get("uri") or f"{RUPLOAD_BASE}{video_id}"

    time.sleep(12)

    file_size = os.path.getsize(video_file)
    upload_headers = {
        "Authorization": f"OAuth {access_token}",
        "offset": "0",
        "file_size": str(file_size),
        "Content-Type": "application/octet-stream"
    }

    with open(video_file, "rb") as vf:
        video_bytes = vf.read()

    up_r = requests.post(upload_url, headers=upload_headers, data=video_bytes, timeout=600)
    if up_r.status_code != 200 or not up_r.json().get("success"):
        raise RuntimeError(f"बाइनरी अपलोड विफल: {up_r.text}")

    return video_id

def _poll_container_status(video_id, access_token, max_checks=40, wait_seconds=15):
    status_url = f"{GRAPH_API_BASE}{video_id}"
    print("   ⏳ इंस्टाग्राम प्रोसेसिंग की स्थिति जांची जा रही है...", flush=True)
    for check_idx in range(1, max_checks + 1):
        time.sleep(wait_seconds)
        try:
            res = requests.get(status_url, params={"fields": "status_code,status", "access_token": access_token}, timeout=30).json()
            status = res.get("status_code")
            print(f"      जाँच ({check_idx}/{max_checks}): {status}", flush=True)
            if status == "FINISHED":
                return "FINISHED"
            elif status in ["ERROR", "EXPIRED"]:
                return status
        except Exception:
            continue
    return "TIMEOUT"

def _publish_reel(video_id, user_id, access_token):
    publish_url = f"{GRAPH_API_BASE}{user_id}/media_publish"
    pub_res = requests.post(publish_url, data={"creation_id": video_id, "access_token": access_token}, timeout=30).json()
    if "id" in pub_res:
        print(f"\n🎉 सफलता! रील इंस्टाग्राम पर पोस्ट हो गई! ID: {pub_res['id']}\n", flush=True)
    else:
        raise RuntimeError(f"पब्लिशिंग विफल: {pub_res}")

# =====================================================================
# 7. मुख्य निष्पादन (Main Execution)
# =====================================================================
if __name__ == "__main__":
    page2_script = (
        "एसएससी बायोलॉजी के नोट्स का पेज नंबर दो पूरी बारीकी से समझिए! "
        "कोशिका जीवन की मौलिक और संरचनात्मक इकाई है, जिसके अध्ययन को साइटोलॉजी कहते हैं। "
        "इसका नाम लैटिन शब्द सेल्यूला यानी छोटे कमरे से लिया गया है। "
        "पहली बार 1665 में रॉबर्ट हुक ने पेड़ की छाल में मृत कोशिका देखी। "
        "लेकिन ध्यान दें: पहली जीवित कोशिका 1674 में ल्यूवेनहॉक ने पानी में खोजी थी! "
        "इसके बाद 1831 में रॉबर्ट ब्राउन ने केंद्रक यानी न्यूक्लियस की खोज की, "
        "और पुरकिंजे ने जीवद्रव्य को प्रोटोप्लाज्म नाम दिया! "
        "कोशिका सिद्धांत श्लाइडेन और श्वान ने दिया, जिसे रूडोल्फ विरचो ने आगे बढ़ाया "
        "कि सभी नई कोशिकाएं पुरानी कोशिकाओं के विभाजन से बनती हैं! "
        "तो दोस्तों, स्क्रीन पर दिए सवाल का सही उत्तर कमेंट्स में लिखें, "
        "और पेज 3 के लिए फॉलो जरूर करें!"
    )

    caption_text = (
        "SSC Biology: कोशिका की खोज और सिद्धांत (Page 2 Complete Revision) 🧬✨\n\n"
        "• Robert Hooke (1665) — मृत कोशिका की खोज (Cork Cells)\n"
        "• Antonie van Leeuwenhoek (1674) — पहली जीवित कोशिका\n"
        "• Robert Brown (1831) — केंद्रक (Nucleus)\n"
        "• J.E. Purkinje (1839) — प्रोटोप्लाज्म (जीवद्रव्य)\n"
        "• Schleiden, Schwann & Virchow — कोशिका सिद्धांत\n\n"
        "सभी महत्वपूर्ण पेजों के ऐसे ही विजुअल नोट्स के लिए फॉलो जरूर करें! "
        "#SSCCGL #ParmarSSC #BiologyShorts #CellBiology #Cytology #GovtExamPrep"
    )

    print("चरण 1: विजुअल स्लाइड्स तैयार की जा रही हैं...", flush=True)
    slides = generate_all_slides()

    print("चरण 2: वॉयसओवर जनरेट हो रहा है...", flush=True)
    asyncio.run(make_voice_resilient(page2_script, AUDIO_OUTPUT))

    print("चरण 3: FFmpeg द्वारा वीडियो तैयार की जा रही है...", flush=True)
    compile_video_master(slides, AUDIO_OUTPUT, FINAL_VIDEO)

    print("चरण 4: इंस्टाग्राम अपलोड चलाया जा रहा है...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
