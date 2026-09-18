import os
import time
import subprocess
import asyncio
import textwrap
import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import edge_tts

# =====================================================================
# 1. Configuration & Settings
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "https://graph.facebook.com/v19.0/"
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_fixed_female_p3"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = os.path.join(ASSETS_DIR, "Mukta-Bold.ttf")
AUDIO_OUTPUT = "sync_voice.mp3"
FINAL_VIDEO = "biology_sync_reel.mp4"

# स्पष्ट और प्राकृतिक महिला आवाज़ (Female Voice)
VOICE_NAME = "hi-IN-SwaraNeural"
RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS

WHATSAPP_NUMBER = "8989971379"

IMAGE_URLS = {
    "mitochondria": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Mitochondria%2C_mammalian_lung_-_TEM.jpg/800px-Mitochondria%2C_mammalian_lung_-_TEM.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Animal_mitochondria_diagram_en.svg/1024px-Animal_mitochondria_diagram_en.svg.png"
    ],
    "ribosome": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Ribosome_mRNA_tRNA_chain.png/800px-Ribosome_mRNA_tRNA_chain.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/Ribosome_shape.png/800px-Ribosome_shape.png"
    ],
    "lysosome": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Lysosome_diagram.svg/800px-Lysosome_diagram.svg.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Cell_organelle_lysosome.png/800px-Cell_organelle_lysosome.png"
    ],
    "pdf_ebook": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Golden_Trophy.svg/800px-Golden_Trophy.svg.png"
    ]
}

# =====================================================================
# 2. Font Engine
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
# 3. 3D Biological Renderer & Downloader
# =====================================================================
def render_realistic_3d_organelle(key):
    img = Image.new("RGBA", (720, 520), (10, 15, 30, 255))
    d = ImageDraw.Draw(img)

    if key == "mitochondria":
        d.rounded_rectangle([60, 80, 660, 440], radius=180, fill="#7c2d12", outline="#ea580c", width=6)
        d.rounded_rectangle([85, 105, 635, 415], radius=155, fill="#431407", outline="#f97316", width=4)
        cristae = [
            [(160, 105), (160, 310), (200, 310), (200, 105)],
            [(250, 415), (250, 210), (290, 210), (290, 415)],
            [(340, 105), (340, 330), (380, 330), (380, 105)],
            [(430, 415), (430, 190), (470, 190), (470, 415)],
            [(520, 105), (520, 300), (560, 300), (560, 105)]
        ]
        for fold in cristae:
            d.line(fold, fill="#fdba74", width=12, joint="curve")
        for gx, gy in [(130, 350), (220, 160), (310, 360), (400, 150), (490, 350), (580, 230)]:
            d.ellipse([gx, gy, gx + 14, gy + 14], fill="#fde047")
        d.text((150, 25), "माइटोकॉन्ड्रिया: 3D आंतरिक संरचना", fill="#fed7aa", font=get_verified_font(26))

    elif key == "ribosome":
        d.ellipse([180, 80, 540, 340], fill="#047857", outline="#34d399", width=6)
        d.ellipse([240, 130, 480, 290], fill="#065f46")
        d.rounded_rectangle([130, 300, 590, 430], radius=65, fill="#0f766e", outline="#2dd4bf", width=5)
        mrna_points = [(90, 325), (190, 315), (300, 335), (420, 315), (530, 330), (630, 320)]
        for i in range(len(mrna_points) - 1):
            d.line([mrna_points[i], mrna_points[i + 1]], fill="#facc15", width=8)
        for py, px in enumerate(range(170, 70, -20)):
            d.ellipse([340 + (py % 2) * 15, px, 360 + (py % 2) * 15, px + 20], fill="#f43f5e")
        d.text((170, 25), "राइबोसोम: Subunits & Protein Chain", fill="#a7f3d0", font=get_verified_font(25))

    elif key == "lysosome":
        d.ellipse([150, 70, 570, 450], fill="#881337", outline="#f43f5e", width=7)
        d.ellipse([185, 105, 535, 415], fill="#4c0519", outline="#fb7185", width=4)
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            cx = 360 + 200 * math.cos(rad)
            cy = 260 + 180 * math.sin(rad)
            d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill="#38bdf8")
        for ex, ey in [(250, 200), (320, 170), (420, 210), (280, 300), (380, 320), (450, 280), (340, 240)]:
            d.ellipse([ex, ey, ex + 28, ey + 28], fill="#f59e0b", outline="#fde68a", width=2)
        d.text((160, 25), "लाइसोसोम: पाचक एंजाइम 3D Vesicle", fill="#fecdd3", font=get_verified_font(26))

    else:
        d.rounded_rectangle([15, 15, 705, 505], radius=16, fill="#1e1b4b", outline="#f59e0b", width=4)
        d.polygon([(260, 120), (460, 120), (420, 320), (300, 320)], fill="#f59e0b", outline="#fef08a")
        d.rectangle([340, 320, 380, 400], fill="#d97706")
        d.rectangle([270, 400, 450, 450], fill="#b45309")
        d.text((220, 25), "Exam Oriented E-Book", fill="#fef08a", font=get_verified_font(26))

    return img

def get_verified_image(key):
    path = os.path.join(ASSETS_DIR, f"{key}.png")
    if os.path.exists(path) and os.path.getsize(path) > 15000:
        return path

    urls = IMAGE_URLS.get(key, [])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://commons.wikimedia.org/",
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"
    }

    for u in urls:
        try:
            res = requests.get(u, headers=headers, timeout=12)
            if res.status_code == 200 and len(res.content) > 10000:
                img = Image.open(BytesIO(res.content)).convert("RGBA")
                img.save(path, "PNG")
                return path
        except Exception:
            continue

    fallback_art = render_realistic_3d_organelle(key)
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
        gd.ellipse([px - 35, py - 25, px + src.width + 35, py + src.height + 25], fill=(*glow_rgb, 120))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=30))
        canvas.paste(glow, (0, 0), glow)

        canvas.paste(src, (px, py), src)
    except Exception:
        pass

# =====================================================================
# 4. Slide Layouts
# =====================================================================
def draw_base_scaffold(draw, slide_idx, total=4):
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)
    
    draw.rounded_rectangle([75, 70, 600, 145], radius=14, fill="#F59E0B")
    draw.text((95, 88), "BIOLOGY EXAM REVISION", fill="#000000", font=get_verified_font(28))
    draw.text((700, 88), f"PART {slide_idx}/4", fill="#38BDF8", font=get_verified_font(30))

    bar_w = int(900 * (slide_idx / total))
    draw.rounded_rectangle([90, 165, 990, 177], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 165, 90 + bar_w, 177], radius=6, fill="#38BDF8")

    if slide_idx == 4:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#059669")
        draw.text((95, 1748), f"WhatsApp: {WHATSAPP_NUMBER}", fill="#FFFFFF", font=get_verified_font(34))
    else:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#1E293B")
        draw.text((150, 1748), "महत्वपूर्ण परीक्षा तथ्य", fill="#94A3B8", font=get_verified_font(30))

def generate_all_slides():
    slide_files = []
    f_h1 = get_verified_font(46)
    f_badge = get_verified_font(28)
    f_body = get_verified_font(34)
    f_label = get_verified_font(30)

    # SLIDE 1: Mitochondria
    img1 = Image.new("RGB", (1080, 1920), color="#020617")
    d1 = ImageDraw.Draw(img1)
    draw_base_scaffold(d1, 1)
    d1.text((75, 205), "1. माइटोकॉन्ड्रिया (Powerhouse)", fill="#38BDF8", font=f_h1)

    box1 = [75, 280, 1005, 830]
    d1.rounded_rectangle(box1, radius=22, fill="#0B132B", outline="#38BDF8", width=2)
    paste_smooth_glow_asset(img1, get_verified_image("mitochondria"), box1, glow_rgb=(234, 88, 12))
    d1.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#7c2d12")
    d1.text((115, 312), "ऊर्जा गृह (Powerhouse of Cell)", fill="#fed7aa", font=f_badge)

    d1.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d1.text((105, 885), "परीक्षा के महत्वपूर्ण बिंदु:", fill="#FBBF24", font=f_label)
    txt1 = (
        "• उपनाम: इसे कोशिका का 'पावरहाउस' कहते हैं।\n\n"
        "• कार्य: यह सेलुलर श्वसन द्वारा ATP ऊर्जा बनाता है।\n\n"
        "• खोज: अल्टमैन ने खोज की और बेंडा ने नाम दिया।\n\n"
        "• विशेषता: इसमें खुद का DNA मौजूद होता है।"
    )
    d1.multiline_text((105, 955), txt1, fill="#F8FAFC", font=f_body, spacing=16)
    img1.save("slide_1.png")
    slide_files.append("slide_1.png")

    # SLIDE 2: Ribosome
    img2 = Image.new("RGB", (1080, 1920), color="#020617")
    d2 = ImageDraw.Draw(img2)
    draw_base_scaffold(d2, 2)
    d2.text((75, 205), "2. राइबोसोम (Protein Factory)", fill="#10B981", font=f_h1)

    box2 = [75, 280, 1005, 830]
    d2.rounded_rectangle(box2, radius=22, fill="#0B132B", outline="#10B981", width=2)
    paste_smooth_glow_asset(img2, get_verified_image("ribosome"), box2, glow_rgb=(16, 185, 129))
    d2.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#064E3B")
    d2.text((115, 312), "प्रोटीन फैक्ट्री (Protein Synthesis)", fill="#6EE7B7", font=f_badge)

    d2.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d2.text((105, 885), "परीक्षा के महत्वपूर्ण बिंदु:", fill="#10B981", font=f_label)
    txt2 = (
        "• उपनाम: इसे 'प्रोटीन फैक्ट्री' कहा जाता है।\n\n"
        "• कार्य: यह शरीर में प्रोटीन संश्लेषण करता है।\n\n"
        "• खोज: जॉर्ज पैलेड ने इसकी खोज की थी।\n\n"
        "• आकार: यह सबसे छोटा कोशिका अंग है।"
    )
    d2.multiline_text((105, 955), txt2, fill="#F8FAFC", font=f_body, spacing=16)
    img2.save("slide_2.png")
    slide_files.append("slide_2.png")

    # SLIDE 3: Lysosome
    img3 = Image.new("RGB", (1080, 1920), color="#020617")
    d3 = ImageDraw.Draw(img3)
    draw_base_scaffold(d3, 3)
    d3.text((75, 205), "3. लाइसोसोम (Suicide Bag)", fill="#F43F5E", font=f_h1)

    box3 = [75, 280, 1005, 830]
    d3.rounded_rectangle(box3, radius=22, fill="#0B132B", outline="#F43F5E", width=2)
    paste_smooth_glow_asset(img3, get_verified_image("lysosome"), box3, glow_rgb=(244, 63, 94))
    d3.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#881337")
    d3.text((115, 312), "आत्महत्या की थैली (Suicide Bag)", fill="#FDA4AF", font=f_badge)

    d3.rounded_rectangle([75, 855, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d3.text((105, 885), "परीक्षा के महत्वपूर्ण बिंदु:", fill="#F43F5E", font=f_label)
    txt3 = (
        "• उपनाम: इसे 'आत्महत्या की थैली' कहते हैं।\n\n"
        "• खोज: डी डुवे ने इसकी खोज की थी।\n\n"
        "• कार्य: इसमें पाचक एंजाइम होते हैं जो मृत कोशिकाओं को साफ करते हैं।"
    )
    d3.multiline_text((105, 955), txt3, fill="#F8FAFC", font=f_body, spacing=16)
    img3.save("slide_3.png")
    slide_files.append("slide_3.png")

    # SLIDE 4: Interactive Challenge & CTA
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    draw_base_scaffold(d4, 4)
    d4.text((75, 205), "कमेंट में सही उत्तर दें!", fill="#FBBF24", font=f_h1)

    d4.rounded_rectangle([75, 270, 1005, 560], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 300), "🎯 EXAM CHALLENGE:", fill="#FBBF24", font=f_label)
    q_text = "कोशिका के किस अंग को 'आत्महत्या की थैली' (Suicide Bag) कहा जाता है?"
    d4.multiline_text((105, 365), textwrap.fill(q_text, width=26), fill="#FFFFFF", font=f_body, spacing=10)

    options = ["(A) माइटोकॉन्ड्रिया", "(B) राइबोसोम", "(C) लाइसोसोम", "(D) गॉल्जी बॉडी"]
    qy = 600
    for opt in options:
        d4.rounded_rectangle([75, qy, 1005, qy + 95], radius=14, fill="#0F172A", outline="#38BDF8", width=2)
        d4.text((110, qy + 25), opt, fill="#F8FAFC", font=f_body)
        qy += 115

    pdf_box = [75, 1140, 1005, 1680]
    d4.rounded_rectangle(pdf_box, radius=22, fill="#111827", outline="#10B981", width=2)
    paste_smooth_glow_asset(img4, get_verified_image("pdf_ebook"), [90, 1160, 420, 1660], glow_rgb=(16, 185, 129))

    d4.text((430, 1210), "📚 PDF E-BOOK & MOCK TEST", fill="#34D399", font=f_label)
    hint_desc = (
        "• सही उत्तर कमेंट में लिखें!\n\n"
        f"• WhatsApp: {WHATSAPP_NUMBER}\n\n"
        "• सम्पूर्ण नोट्स के लिए अभी मैसेज करें!"
    )
    d4.multiline_text((430, 1290), hint_desc, fill="#F8FAFC", font=get_verified_font(28), spacing=12)

    img4.save("slide_4.png")
    slide_files.append("slide_4.png")
    return slide_files

# =====================================================================
# 5. Audio-Video Sync Engine (58.5s Duration Lock)
# =====================================================================
async def make_voice(text, out_file):
    communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate="+0%")
    await communicate.save(out_file)

def compile_video(slide_files, audio_file, output_file):
    cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    total_dur = float(subprocess.check_output(cmd_dur).decode().strip())

    target_dur = 58.5
    speed_factor = round(total_dur / target_dur, 3)
    clamped_audio = "voice_clamped.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={speed_factor}", clamped_audio], check=True)
    audio_file = clamped_audio
    final_dur = float(subprocess.check_output(cmd_dur, text=True).strip())

    weights = [1.0, 1.0, 1.0, 1.15]
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
    print(f"\n🎬 58.5s Perfectly Synchronized Video Ready: {output_file}\n")

# =====================================================================
# 6. Instagram Multipart Upload Engine
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption):
    access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("IG_USER_ID", "").strip()

    if not access_token or not user_id:
        print("Notice: Token ya ID set nahi hai. Video file locally create ho chuki hai.")
        return

    print("🚀 Instagram auto-upload start ho raha hai...")
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
# 7. Execution Pipeline (Pure Devanagari Script for Female Voice)
# =====================================================================
if __name__ == "__main__":
    sync_script = (
        "दो नंबर का प्रश्न इस रील से एग्जाम में जरूर मिलेगा, चलो देखते हैं! "
        "आइए, कोशिका के सबसे महत्वपूर्ण अंगों को समझते हैं। "
        "पहली स्लाइड पर देखिए, माइटोकॉन्ड्रिया को कोशिका का पावरहाउस कहते हैं, क्योंकि यह एटीपी ऊर्जा बनाता है। "
        "दूसरी स्लाइड पर देखिए, राइबोसोम को प्रोटीन फैक्ट्री कहा जाता है, क्योंकि यह प्रोटीन संश्लेषण करता है। "
        "तीसरी स्लाइड पर देखिए, लाइसोसोम को आत्महत्या की थैली यानी सुसाइड बैग कहते हैं। "
        "अब आपके लिए एक छोटा सा सवाल। स्क्रीन पर दिए गए प्रश्न का सही उत्तर जल्दी से कमेंट सेक्शन में लिखकर बताओ! "
        "और ऐसे ही सभी चैप्टर्स के मॉक टेस्ट और पीडीएफ ई-बुक्स के लिए, स्क्रीन पर दिए गए नंबर पर व्हाट्सएप करें!"
    )

    caption_text = (
        "Biology Cell Organelles Important Notes 🧬📚\n\n"
        "• Mitochondria, Ribosome & Lysosome Complete 3D Revision.\n"
        "• Sahi uttar comment section mein zaroor likhein!\n"
        f"• WhatsApp for E-Books & Mock Tests: {WHATSAPP_NUMBER}\n\n"
        "#BiologyShorts #CellOrganelles #GovtExamPrep #MockTest"
    )

    print("Step 1: 4 detailed 3D slides banayi ja rahi hain...", flush=True)
    slides = generate_all_slides()

    print("Step 2: Realistic Devanagari female voiceover generate ho raha hai...", flush=True)
    asyncio.run(make_voice(sync_script, AUDIO_OUTPUT))

    print("Step 3: FFmpeg dwara exact 58.5s synchronization shuru...", flush=True)
    compile_video(slides, AUDIO_OUTPUT, FINAL_VIDEO)

    print("Step 4: Instagram upload chalaya ja raha hai...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
