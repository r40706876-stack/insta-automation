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

ASSETS_DIR = "assets/biology_clean_p3"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_FILE = os.path.join(ASSETS_DIR, "Mukta-Bold.ttf")
AUDIO_OUTPUT = "clean_voice.mp3"
FINAL_VIDEO = "biology_clean_reel.mp4"

# Realistic Male Voice
VOICE_NAME = "hi-IN-MadhurNeural"
RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS

WHATSAPP_NUMBER = "8989971379"

# Clean educational asset URLs
IMAGE_URLS = {
    "mitochondria": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Animal_mitochondria_diagram_en.svg/1024px-Animal_mitochondria_diagram_en.svg.png",
    "ribosome": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Ribosome_mRNA_tRNA_chain.png/800px-Ribosome_mRNA_tRNA_chain.png",
    "lysosome": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Lysosome_diagram.svg/800px-Lysosome_diagram.svg.png"
}

# =====================================================================
# 2. फ़ॉन्ट इंजन
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

    if key == "mitochondria":
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#2e1065", outline="#9333ea", width=4)
        d.ellipse([100, 120, 600, 400], fill="#581c87", outline="#c084fc", width=6)
        d.text((220, 25), "माइटोकॉन्ड्रिया (Powerhouse)", fill="#f3e8ff", font=get_verified_font(26))
    elif key == "ribosome":
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#062c24", outline="#059669", width=4)
        d.ellipse([150, 100, 550, 420], fill="#047857", outline="#34d399", width=6)
        d.text((230, 25), "राइबोसोम (Protein Factory)", fill="#a7f3d0", font=get_verified_font(26))
    else:
        d.rounded_rectangle([15, 15, 685, 505], radius=16, fill="#450a0a", outline="#dc2626", width=4)
        d.ellipse([150, 100, 550, 420], fill="#7f1d1d", outline="#f87171", width=6)
        d.text((210, 25), "लाइसोसोम (Suicide Bag)", fill="#fca5a5", font=get_verified_font(26))
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
# 4. 3 क्लीन स्लाइड्स (Perfect Sync Layout)
# =====================================================================
def draw_base_scaffold(draw, slide_idx, total=3):
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)
    
    draw.rounded_rectangle([75, 70, 600, 145], radius=14, fill="#F59E0B")
    draw.text((95, 88), "BIOLOGY EXAM NOTES", fill="#000000", font=get_verified_font(28))
    draw.text((700, 88), f"SLIDE {slide_idx}/3", fill="#38BDF8", font=get_verified_font(30))

    bar_w = int(900 * (slide_idx / total))
    draw.rounded_rectangle([90, 165, 990, 177], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 165, 90 + bar_w, 177], radius=6, fill="#38BDF8")

    # Sirf aakhri slide par WhatsApp CTA dikhega ya sabhi par clean footer
    if slide_idx == 3:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#059669")
        draw.text((95, 1748), f"WhatsApp: {WHATSAPP_NUMBER}", fill="#FFFFFF", font=get_verified_font(34))
    else:
        draw.rounded_rectangle([75, 1715, 1005, 1835], radius=18, fill="#1E293B")
        draw.text((150, 1748), "म्हात्वपूर्ण परीक्षा तथ्य", fill="#94A3B8", font=get_verified_font(30))

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
    paste_smooth_glow_asset(img1, get_verified_image("mitochondria"), box1, glow_rgb=(56, 189, 248))
    d1.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#1E3A8A")
    d1.text((115, 312), "ऊर्जा गृह एवं श्वसन स्थल", fill="#93C5FD", font=f_badge)

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
    d2.text((115, 312), "प्रोटीन संश्लेषण केंद्र", fill="#6EE7B7", font=f_badge)

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

    # SLIDE 3: Lysosome & WhatsApp CTA
    img3 = Image.new("RGB", (1080, 1920), color="#020617")
    d3 = ImageDraw.Draw(img3)
    draw_base_scaffold(d3, 3)
    d3.text((75, 205), "3. लाइसोसोम (Suicide Bag)", fill="#F43F5E", font=f_h1)

    box3 = [75, 280, 1005, 750]
    d3.rounded_rectangle(box3, radius=22, fill="#0B132B", outline="#F43F5E", width=2)
    paste_smooth_glow_asset(img3, get_verified_image("lysosome"), box3, glow_rgb=(244, 63, 94))
    d3.rounded_rectangle([95, 300, 550, 360], radius=10, fill="#881337")
    d3.text((115, 312), "आत्महत्या की थैली", fill="#FDA4AF", font=f_badge)

    d3.rounded_rectangle([75, 780, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d3.text((105, 810), "मॉक टेस्ट व E-Book के लिए संपर्क करें:", fill="#34D399", font=f_label)
    txt3 = (
        "• उपनाम: इसे 'आत्महत्या की थैली' कहते हैं।\n\n"
        "• खोज: डी डुवे ने इसकी खोज की थी।\n\n"
        f"• WhatsApp: {WHATSAPP_NUMBER}\n"
        "• कम्पेटिटिव नोट्स के लिए तुरंत मैसेज करें!"
    )
    d3.multiline_text((105, 880), txt3, fill="#F8FAFC", font=f_body, spacing=14)
    img3.save("slide_3.png")
    slide_files.append("slide_3.png")

    return slide_files

# =====================================================================
# 5. ऑडियो एवं वीडियो सिंक (3 Slides Perfect Weight)
# =====================================================================
async def make_voice(text, out_file):
    communicate = edge_tts.Communicate(text=text, voice=VOICE_NAME, rate="+0%")
    await communicate.save(out_file)

def compile_video(slide_files, audio_file, output_file):
    cmd_dur = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    total_dur = float(subprocess.check_output(cmd_dur).decode().strip())

    target_dur = 45.0  # 3 slides ke liye 45 seconds ekdum perfect pace hai
    speed_factor = round(total_dur / target_dur, 3)
    clamped_audio = "voice_clamped.mp3"
    subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={speed_factor}", clamped_audio], check=True)
    audio_file = clamped_audio
    final_dur = float(subprocess.check_output(cmd_dur, text=True).strip())

    # 3 slides ke liye equal distribution weights
    weights = [1.0, 1.0, 1.0]
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
    print(f"\n🎬 Clean Synchronized Video Ready: {output_file}\n")

# =====================================================================
# 6. इंस्टाग्राम ऑटो-अपलोड इंजन
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
# 7. मुख्य निष्पादन (Main Execution - Page 3 Clean Content)
# =====================================================================
if __name__ == "__main__":
    # Script perfectly matched to 3 slides with strong hook and end-only CTA
    clean_script = (
        "लिख कर ले लो, ये सवाल हर कम्पेटिटिव एग्जाम में जरूर पूछा जाता है! "
        "आइए कोशिका के सबसे महत्वपूर्ण अंगों को समझें। "
        "सबसे पहले बात करते हैं माइटोकॉन्ड्रिया की, जिसे सेल का पावरहाउस कहते हैं क्योंकि यह ऊर्जा बनाता है। "
        "दूसरी स्लाइड पर देखिए, राइबोसोम को प्रोटीन फैक्ट्री कहा जाता है क्योंकि यह प्रोटीन संश्लेषण करता है। "
        "और तीसरी स्लाइड पर देखिए, लाइसोसोम को आत्महत्या की थैली कहते हैं। "
        "ऐसे ही सभी चैप्टर के मॉक टेस्ट और पीडीएफ ई-बुक्स के लिए, स्क्रीन पर दिए नंबर पर व्हाट्सएप करें!"
    )

    caption_text = (
        "Biology Cell Organelles Notes 🧬📚\n\n"
        "• Mitochondria, Ribosome & Lysosome Important Facts.\n"
        "• Exam-oriented PDF E-Books & Mock Tests available.\n"
        f"• WhatsApp karein: {WHATSAPP_NUMBER}\n\n"
        "#BiologyShorts #CellOrganelles #GovtExamPrep #MockTest"
    )

    print("चरण 1: 3 साफ़ और सटीक स्लाइड्स तैयार की जा रही हैं...", flush=True)
    slides = generate_all_slides()

    print("चरण 2: Natural Male Voiceover generate ho raha hai...", flush=True)
    asyncio.run(make_voice(clean_script, AUDIO_OUTPUT))

    print("चरण 3: FFmpeg द्वारा वीडियो सिंक और रेंडर की जा रही है...", flush=True)
    compile_video(slides, AUDIO_OUTPUT, FINAL_VIDEO)

    print("चरण 4: इंस्टाग्राम अपलोड चलाया जा रहा है...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
