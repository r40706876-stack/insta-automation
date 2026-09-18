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
# 1. कॉन्फ़िगरेशन एवं API सेटिंग्स
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0/"
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_pro_p2"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = os.path.join(ASSETS_DIR, "Mukta-Bold.ttf")
AUDIO_OUTPUT = "pro_voice.mp3"
FINAL_VIDEO = "biology_pro_reel.mp4"

# प्रोफेशनल महिला आवाज़ (Female Voice)
VOICE_NAME = "hi-IN-SwaraNeural"
RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS

WHATSAPP_NUMBER = "8989971379"

IMAGE_URLS = {
    "cork_cells": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Robert_Hooke_Micrographia_1665_cork_cells.jpg/800px-Robert_Hooke_Micrographia_1665_cork_cells.jpg",
    "living_cell": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Anabaena_sperica.jpg/800px-Anabaena_sperica.jpg",
    "nucleus_3d": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Diagram_human_cell_nucleus.svg/1024px-Diagram_human_cell_nucleus.svg.png",
    "pdf_ebook": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Golden_Trophy.svg/800px-Golden_Trophy.svg.png"
}

# =====================================================================
# 2. फ़ॉन्ट इंजन (बड़े और स्पष्ट अक्षर)
# =====================================================================
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

# =====================================================================
# 3. 3D विजुअल और इमेज हैंडलर
# =====================================================================
def generate_artistic_fallback(key):
    img = Image.new("RGBA", (700, 520), (11, 19, 43, 255))
    d = ImageDraw.Draw(img)

    if key == "cork_cells":
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#1c1917", outline="#78350f", width=4)
        for row in range(50, 480, 55):
            offset = 25 if (row // 55) % 2 == 1 else 0
            for col in range(40 + offset, 650, 60):
                d.rounded_rectangle([col, row, col + 48, row + 45], radius=8, fill="#292524", outline="#d97706", width=3)
                d.ellipse([col + 15, row + 14, col + 33, row + 31], fill="#451a03")
        d.text((180, 25), "रॉबर्ट हुक कॉर्क कोशिकाएं (1665)", fill="#fde68a", font=get_verified_font(26))
    elif key == "living_cell":
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#062c24", outline="#059669", width=4)
        d.ellipse([100, 80, 600, 440], fill="#047857", outline="#34d399", width=6)
        d.ellipse([270, 180, 430, 340], fill="#0f766e", outline="#5eead4", width=4)
        d.text((160, 25), "ल्यूवेनहॉक जीवित कोशिका (1674)", fill="#a7f3d0", font=get_verified_font(26))
    elif key == "nucleus_3d":
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#2e1065", outline="#9333ea", width=4)
        d.ellipse([140, 60, 560, 460], fill="#581c87", outline="#c084fc", width=8)
        d.ellipse([300, 210, 400, 310], fill="#a855f7", outline="#f3e8ff", width=4)
        d.text((180, 25), "कोशिका केंद्रक (Nucleus - 1831)", fill="#f3e8ff", font=get_verified_font(26))
    else:
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#1e1b4b", outline="#f59e0b", width=4)
        d.polygon([(250, 120), (450, 120), (410, 320), (290, 320)], fill="#f59e0b", outline="#fef08a")
        d.rectangle([330, 320, 370, 400], fill="#d97706")
        d.rectangle([260, 400, 440, 450], fill="#b45309")
    return img

def get_verified_image(key):
    path = os.path.join(ASSETS_DIR, f"{key}.png")
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        return path

    url = IMAGE_URLS.get(key)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://en.wikipedia.org/",
        "Accept": "image/*"
    }

    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200 and len(res.content) > 5000:
            img = Image.open(BytesIO(res.content)).convert("RGBA")
            img.save(path, "PNG")
            return path
    except Exception:
        pass

    fallback_art = generate_artistic_fallback(key)
    fallback_art.save(path, "PNG")
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
    except Exception:
        pass

# =====================================================================
# 4. प्रोफेशनली डिजाइन स्लाइड्स (बड़े फॉन्ट और अंत में WhatsApp)
# =====================================================================
def draw_base_scaffold(draw, slide_idx, total=4):
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)
    
    draw.rounded_rectangle([75, 70, 600, 145], radius=14, fill="#F59E0B")
    draw.text((95, 88), "EXAM ORIENTED BIOLOGY NOTES", fill="#000000", font=get_verified_font(28))
    draw.text((700, 88), "PDF E-BOOK", fill="#38BDF8", font=get_verified_font(30))

    bar_w = int(900 * (slide_idx / total))
    draw.rounded_rectangle([90, 165, 990, 177], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 165, 90 + bar_w, 177], radius=6, fill="#38BDF8")

    draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#059669")
    draw.text((95, 1748), f"📲 WhatsApp करें: {WHATSAPP_NUMBER}", fill="#FFFFFF", font=get_verified_font(34))

def generate_all_slides():
    slide_files = []
    f_h1 = get_verified_font(46)
    f_badge = get_verified_font(28)
    f_body = get_verified_font(34)
    f_label = get_verified_font(30)

    # SLIDE 1
    img1 = Image.new("RGB", (1080, 1920), color="#020617")
    d1 = ImageDraw.Draw(img1)
    draw_base_scaffold(d1, 1)
    d1.text((75, 205), "1. कोशिका की परिभाषा और खोज (1665)", fill="#38BDF8", font=f_h1)

    box1 = [75, 280, 1005, 830]
    d1.rounded_rectangle(box1, radius=22, fill="#0B132B", outline="#38BDF8", width=2)
    paste_smooth_glow_asset(img1, get_verified_image("cork_cells"), box1, glow_rgb=(56, 189, 248))
    d1.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#1E3A8A")
    d1.text((115, 312), "रॉबर्ट हुक: कॉर्क मृत कोशिका (1665)", fill="#93C5FD", font=f_badge)

    d1.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d1.text((105, 885), "परीक्षा के लिए अति महत्वपूर्ण बिंदु:", fill="#FBBF24", font=f_label)
    txt1 = (
        "• कोशिका: जीवन की मौलिक व संरचनात्मक इकाई है।\n\n"
        "• साइटोलॉजी (Cytology): कोशिका का वैज्ञानिक अध्ययन।\n\n"
        "• लैटिन नाम: 'Cellula' यानी छोटा कमरा (Small Room)।\n\n"
        "• रॉबर्ट हुक (1665): पेड़ की छाल में मृत कोशिका खोजी।\n\n"
        "• विशेष ध्यान दें: यह पहली मृत कोशिका थी!"
    )
    d1.multiline_text((105, 955), txt1, fill="#F8FAFC", font=f_body, spacing=16)
    img1.save("slide_1.png")
    slide_files.append("slide_1.png")

    # SLIDE 2
    img2 = Image.new("RGB", (1080, 1920), color="#020617")
    d2 = ImageDraw.Draw(img2)
    draw_base_scaffold(d2, 2)
    d2.text((75, 205), "2. कोशिका की अन्य प्रमुख खोजें", fill="#10B981", font=f_h1)

    box2 = [75, 280, 1005, 830]
    d2.rounded_rectangle(box2, radius=22, fill="#0B132B", outline="#10B981", width=2)
    paste_smooth_glow_asset(img2, get_verified_image("living_cell"), box2, glow_rgb=(16, 185, 129))
    d2.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#064E3B")
    d2.text((115, 312), "ल्यूवेनहॉक: पहली जीवित कोशिका (1674)", fill="#6EE7B7", font=f_badge)

    d2.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d2.text((105, 885), "शीर्ष 3 महत्वपूर्ण वैज्ञानिक:", fill="#10B981", font=f_label)
    txt2 = (
        "• ल्यूवेनहॉक (1674): तालाब के जल में पहली जीवित कोशिका।\n\n"
        "• रॉबर्ट ब्राउन (1831): केंद्रक (Nucleus) की खोज की।\n\n"
        "• पुरकिंजे (1839): जीवद्रव्य को 'प्रोटोप्लाज्म' नाम दिया।\n\n"
        "• ट्रिक: हुक = मृत, ल्यूवेनहॉक = जीवित, ब्राउन = केंद्रक।"
    )
    d2.multiline_text((105, 955), txt2, fill="#F8FAFC", font=f_body, spacing=16)
    img2.save("slide_2.png")
    slide_files.append("slide_2.png")

    # SLIDE 3
    img3 = Image.new("RGB", (1080, 1920), color="#020617")
    d3 = ImageDraw.Draw(img3)
    draw_base_scaffold(d3, 3)
    d3.text((75, 205), "3. कोशिका सिद्धांत (Cell Theory)", fill="#F43F5E", font=f_h1)

    box3 = [75, 280, 1005, 830]
    d3.rounded_rectangle(box3, radius=22, fill="#0B132B", outline="#F43F5E", width=2)
    paste_smooth_glow_asset(img3, get_verified_image("nucleus_3d"), box3, glow_rgb=(244, 63, 94))
    d3.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#881337")
    d3.text((115, 312), "केंद्रक संरचना एवं नियंत्रण केंद्र", fill="#FDA4AF", font=f_badge)

    d3.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d3.text((105, 885), "सिद्धार्थ के मुख्य नियम:", fill="#F43F5E", font=f_label)
    txt3 = (
        "• श्लाइडेन व श्वान (1838-39): कोशिका सिद्धांत दिया।\n\n"
        "• मुख्य नियम: सभी पौधे व जंतु कोशिकाओं से बने हैं।\n\n"
        "• मूल इकाई: कोशिका जीवन की मौलिक इकाई है।\n\n"
        "• रूडोल्फ विरचो (1855): नई कोशिकाएं पुरानी से बनती हैं।"
    )
    d3.multiline_text((105, 955), txt3, fill="#F8FAFC", font=f_body, spacing=16)
    img3.save("slide_3.png")
    slide_files.append("slide_3.png")

    # SLIDE 4
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    draw_base_scaffold(d4, 4)
    d4.text((75, 205), "परीक्षा उपयोगी महत्वपूर्ण प्रश्न", fill="#FBBF24", font=f_h1)

    d4.rounded_rectangle([75, 280, 1005, 550], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 310), "🎯 SSC CGL / CHSL PYQ:", fill="#FBBF24", font=f_label)
    q_text = "तालाब के जल में पहली बार 'जीवित कोशिका' की खोज किसने की थी?"
    d4.multiline_text((105, 375), textwrap.fill(q_text, width=26), fill="#FFFFFF", font=f_body, spacing=12)

    options = ["रॉबर्ट हुक", "ल्यूवेनहॉक", "रॉबर्ट ब्राउन", "पुरकिंजे"]
    qy = 590
    for idx, opt in enumerate(options):
        lbl = chr(65 + idx)
        d4.rounded_rectangle([75, qy, 1005, qy + 105], radius=16, fill="#0F172A", outline="#38BDF8", width=2)
        d4.rounded_rectangle([100, qy + 18, 170, qy + 88], radius=10, fill="#38BDF8")
        d4.text((122, qy + 28), lbl, fill="#000000", font=f_badge)
        d4.text((195, qy + 32), opt, fill="#F8FAFC", font=f_body)
        qy += 125

    pdf_box = [75, 1110, 1005, 1680]
    d4.rounded_rectangle(pdf_box, radius=22, fill="#111827", outline="#10B981", width=2)
    paste_smooth_glow_asset(img4, get_verified_image("pdf_ebook"), [90, 1130, 420, 1660], glow_rgb=(16, 185, 129))

    d4.text((430, 1200), "📚 PDF E-BOOK ORDER", fill="#34D399", font=f_label)
    hint_desc = (
        "• सम्पूर्ण बायोलॉजी नोट्स!\n\n"
        f"• WhatsApp: {WHATSAPP_NUMBER}\n\n"
        "• तुरंत मैसेज करें!"
    )
    d4.multiline_text((430, 1280), hint_desc, fill="#F8FAFC", font=get_verified_font(28), spacing=14)

    img4.save("slide_4.png")
    slide_files.append("slide_4.png")
    return slide_files

# =====================================================================
# 5. ऑडियो (फीमेल वॉइस) एवं वीडियो सिंक
# =====================================================================
async def make_voice(text, out_file):
    communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate="+0%")
    await communicate.save(out_file)

def compile_video(slide_files, audio_file, output_file):
    cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    total_dur = float(subprocess.check_output(cmd_dur).decode().strip())

    target_dur = 52.0
    speed_factor = round(total_dur / target_dur, 3)
    clamped_audio = "voice_clamped.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={speed_factor}", clamped_audio], check=True)
    audio_file = clamped_audio
    final_dur = float(subprocess.check_output(cmd_dur, text=True).strip())

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
        "-shortest",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"\n🎬 Pro Video Ready: {output_file}\n")

# =====================================================================
# 6. इंस्टाग्राम ऑटो-अपलोड इंजन
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption):
    access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("IG_USER_ID", "").strip()

    if not access_token or not user_id:
        print("Notice: Token ya ID set nahi hai. Video file locally create ho chuki hai.")
        return

    print("🚀 Instagram auto-upload start ho raha है...")
    init_url = f"{GRAPH_API_BASE}{user_id}/media"
    data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(init_url, data=data, timeout=60).json()
    video_id = r.get("id")
    upload_url = r.get("uri") or f"{RUPLOAD_BASE}{video_id}"

    time.sleep(10)
    file_size = os.path.getsize(video_file)
    headers = {
        "Authorization": f"OAuth {access_token}",
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
        res = requests.get(status_url, params={"fields": "status_code", "access_token": access_token}).json()
        if res.get("status_code") == "FINISHED":
            break

    pub_url = f"{GRAPH_API_BASE}{user_id}/media_publish"
    pub_res = requests.post(pub_url, data={"creation_id": video_id, "access_token": access_token}).json()
    if "id" in pub_res:
        print(f"🎉 SUCCESS! Reel Live on Instagram! ID: {pub_res['id']}")

# =====================================================================
# 7. मुख्य निष्पादन (Main Execution)
# =====================================================================
if __name__ == "__main__":
    # शुरुआत पूरी तरह पढ़ाई से, और WhatsApp ऑर्डर की बात बिल्कुल अंत में
    pro_script = (
        "आइए एसएससी बायोलॉजी के कोशिका चैप्टर के सबसे महत्वपूर्ण तथ्यों को समझें। "
        "कोशिका जीवन की मौलिक और संरचनात्मक इकाई है, जिसके अध्ययन को साइटोलॉजी कहते हैं। "
        "पहली बार 1665 में रॉबर्ट हुक ने मृत कोशिका देखी थी, "
        "जबकि 1674 में ल्यूवेनहॉक ने पहली जीवित कोशिका की खोज की। "
        "रॉबर्ट ब्राउन ने केंद्रक यानी न्यूक्लियस खोजा और पुरकिंजे ने जीवद्रव्य को प्रोटोप्लाज्म नाम दिया। "
        "अब परीक्षा में पक्की सफलता के लिए, एक्जाम ओरिएंटेड पीडीएफ ई-बुक प्राप्त करने के लिए "
        f"आज ही हमारे व्हाट्सएप नंबर {WHATSAPP_NUMBER} पर मैसेज करें!"
    )

    caption_text = (
        "SSC Biology Exam-Oriented Notes 🧬📚\n\n"
        "• सम्पूर्ण पाठ्यक्रम आधारित PDF E-Book उपलब्ध!\n"
        "• बेहतरीन ट्रिक्स और परीक्षा उपयोगी प्रश्न।\n"
        f"• E-Book मंगवाने के लिए तुरंत WhatsApp करें: {WHATSAPP_NUMBER}\n\n"
        "#SSCCGL #ParmarSSC #BiologyPDF #CellBiology #GovtExamPrep"
    )

    print("चरण 1: बड़े फॉन्ट और स्पष्ट स्लाइड्स तैयार की जा रही हैं...", flush=True)
    slides = generate_all_slides()

    print("चरण 2: प्रोफेशनल फीमेल वॉयसओवर जनरेट हो रहा है...", flush=True)
    asyncio.run(make_voice(pro_script, AUDIO_OUTPUT))

    print("चरण 3: FFmpeg द्वारा वीडियो रेंडर की जा रही है...", flush=True)
    compile_video(slides, AUDIO_OUTPUT, FINAL_VIDEO)

    print("चरण 4: इंस्टाग्राम अपलोड चलाया जा रहा है...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
