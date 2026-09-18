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
# 1. Environment & API Configurations
# =====================================================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()

GRAPH_API_BASE = "".join(["http", "s://", "graph.", "facebook", ".com/v19.0/"])
RUPLOAD_BASE = "https://rupload.facebook.com/ig-api-upload/v19.0/"

ASSETS_DIR = "assets/biology_master"
os.makedirs(ASSETS_DIR, exist_ok=True)

FONT_DEV_PATH = "NotoSansDevanagari-Bold.ttf"
AUDIO_OUTPUT = "page2_voice.mp3"
FINAL_VIDEO = "biology_page2_reel.mp4"
VOICE_NAME = "hi-IN-MadhurNeural"

# Cross-version Pillow Compatibility
RESAMPLE_MODE = getattr(Image, "Resampling", Image).LANCZOS

# High-Resolution Educational Assets (Page 2 Topics)
IMAGE_URLS = {
    "cork_cells": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Robert_Hooke_Micrographia_1665_cork_cells.jpg/800px-Robert_Hooke_Micrographia_1665_cork_cells.jpg",
    "living_cell": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Anabaena_sperica.jpg/800px-Anabaena_sperica.jpg",
    "nucleus_3d": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Diagram_human_cell_nucleus.svg/1024px-Diagram_human_cell_nucleus.svg.png",
    "trophy": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Golden_Trophy.svg/800px-Golden_Trophy.svg.png"
}

# =====================================================================
# 2. Font & Visual Assets Management
# =====================================================================
def ensure_font():
    if not os.path.exists(FONT_DEV_PATH):
        try:
            url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(FONT_DEV_PATH, "wb") as f:
                    f.write(r.content)
        except Exception as e:
            print(f"⚠️ Font Download Warning: {e}", flush=True)

def get_font(size):
    ensure_font()
    try:
        return ImageFont.truetype(FONT_DEV_PATH, size)
    except Exception:
        return ImageFont.load_default()

def get_verified_asset(key):
    path = os.path.join(ASSETS_DIR, f"{key}.png")
    if os.path.exists(path):
        return path

    url = IMAGE_URLS.get(key)
    if url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "image/*"
            }
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                img = Image.open(BytesIO(res.content)).convert("RGBA")
                img.save(path, "PNG")
                return path
        except Exception:
            pass

    # 100% Offline Vector Fallback
    fallback = Image.new("RGBA", (500, 500), (15, 23, 42, 255))
    fd = ImageDraw.Draw(fallback)
    if key == "cork_cells":
        for cy in range(30, 470, 55):
            for cx in range(30, 470, 55):
                fd.rectangle([cx, cy, cx + 48, cy + 48], outline="#F59E0B", width=3)
    elif key == "living_cell":
        fd.ellipse([80, 80, 420, 420], fill="#065F46", outline="#34D399", width=6)
        fd.ellipse([180, 180, 320, 320], fill="#10B981")
    elif key == "trophy":
        fd.rectangle([180, 320, 320, 420], fill="#D97706")
        fd.chord([120, 100, 380, 340], 0, 180, fill="#FBBF24")
    else:
        fd.ellipse([80, 80, 420, 420], fill="#881337", outline="#FDA4AF", width=6)
    
    fallback.save(path, "PNG")
    return path

def paste_rounded_glow_asset(canvas, img_path, target_box, glow_rgb=(56, 189, 248), corner_radius=22):
    if not os.path.exists(img_path):
        return
    try:
        x1, y1, x2, y2 = target_box
        w, h = x2 - x1, y2 - y1

        src = Image.open(img_path).convert("RGBA")
        src.thumbnail((w - 40, h - 40), RESAMPLE_MODE)

        # Smooth Rounded Corner Masking
        mask = Image.new("L", src.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), src.size], radius=corner_radius, fill=255)
        src.putalpha(mask)

        pos_x = x1 + (w - src.width) // 2
        pos_y = y1 + (h - src.height) // 2

        # Radial Ambient Glow
        glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        g_draw = ImageDraw.Draw(glow)
        g_draw.ellipse(
            [pos_x - 35, pos_y - 25, pos_x + src.width + 35, pos_y + src.height + 25],
            fill=(*glow_rgb, 125)
        )
        glow = glow.filter(ImageFilter.GaussianBlur(radius=35))
        canvas.paste(glow, (0, 0), glow)

        canvas.paste(src, (pos_x, pos_y), src)
    except Exception as e:
        print(f"⚠️ Asset Paste Warning: {e}", flush=True)

# =====================================================================
# 3. Canvas & Visual Slides Construction (PDF Page 2 Coverage)
# =====================================================================
def draw_base_scaffold(draw, slide_idx, total_slides=4):
    # Outer Border
    draw.rounded_rectangle([35, 35, 1045, 1885], radius=28, fill="#070B14", outline="#38BDF8", width=3)

    # Top Pill Header
    draw.rounded_rectangle([75, 70, 530, 135], radius=14, fill="#F59E0B")
    draw.text((95, 85), "PARMAR SSC BIOLOGY • PAGE 2", fill="#000000", font=get_font(25))
    draw.text((700, 85), "@PARMAR_BIO", fill="#64748B", font=get_font(28))

    # Top Progress Line
    bar_w = int(900 * (slide_idx / total_slides))
    draw.rounded_rectangle([90, 155, 990, 167], radius=6, fill="#1E293B")
    draw.rounded_rectangle([90, 155, 90 + bar_w, 167], radius=6, fill="#38BDF8")

    # Bottom Safe Zone CTA
    draw.rounded_rectangle([75, 1725, 1005, 1835], radius=18, fill="#E11D48")
    draw.text((150, 1755), "Page 2 Revision Pura! Save Aur Follow Karein!", fill="#FFFFFF", font=get_font(32))

def generate_all_slides():
    slide_files = []
    f_h1 = get_font(42)
    f_badge = get_font(25)
    f_body = get_font(30)
    f_label = get_font(28)

    # ----------------- SLIDE 1: Cell Definition & Hooke (1665) -----------------
    img1 = Image.new("RGB", (1080, 1920), color="#020617")
    d1 = ImageDraw.Draw(img1)
    draw_base_scaffold(d1, 1)

    d1.text((75, 195), "1. Koshika Ki Paribhasha Aur Khoj (1665)", fill="#38BDF8", font=f_h1)

    box1 = [75, 265, 1005, 830]
    d1.rounded_rectangle(box1, radius=22, fill="#0B132B", outline="#38BDF8", width=2)
    paste_rounded_glow_asset(img1, get_verified_asset("cork_cells"), box1, glow_rgb=(56, 189, 248), corner_radius=22)
    d1.rounded_rectangle([95, 285, 480, 340], radius=10, fill="#1E3A8A")
    d1.text((115, 298), "Original Cork Cells (Dead Cell)", fill="#93C5FD", font=f_badge)

    d1.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d1.text((105, 890), "Page 2 Ke Core Facts (Bilkul Aasan Bhasha):", fill="#FBBF24", font=f_label)

    txt1 = (
        "• Koshika: Jeevan ki maulik, sanrachnatmak aur karyatmak ikai hai.\n\n"
        "• Cytology: Koshika ke adhyayan ko Cytology kaha jata hai.\n\n"
        "• Latin Naam: 'Cellula' shabd se bana hai, jiska arth hai 'Small Room'.\n\n"
        "• Robert Hooke (1665): Pehli baar ped ki chhal (Cork) me dekha.\n\n"
        "• Exam Trap: Robert Hooke dwara dekhi gayi koshika Mrit (Dead) thi!"
    )
    d1.multiline_text((105, 955), txt1, fill="#F8FAFC", font=f_body, spacing=13)
    img1.save("slide_1.png")
    slide_files.append("slide_1.png")

    # ----------------- SLIDE 2: Leeuwenhoek, Brown, Purkinje -----------------
    img2 = Image.new("RGB", (1080, 1920), color="#020617")
    d2 = ImageDraw.Draw(img2)
    draw_base_scaffold(d2, 2)

    d2.text((75, 195), "2. Koshika Ki Anya Pramukh Khoj", fill="#10B981", font=f_h1)

    box2 = [75, 265, 1005, 830]
    d2.rounded_rectangle(box2, radius=22, fill="#0B132B", outline="#10B981", width=2)
    paste_rounded_glow_asset(img2, get_verified_asset("living_cell"), box2, glow_rgb=(16, 185, 129), corner_radius=22)
    d2.rounded_rectangle([95, 285, 470, 340], radius=10, fill="#064E3B")
    d2.text((115, 298), "Pehli Jeevit Koshika (Living Cell)", fill="#6EE7B7", font=f_badge)

    d2.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d2.text((105, 890), "SSC Me Baar-Baar Aane Wale 3 Vaigyanik:", fill="#10B981", font=f_label)

    txt2 = (
        "• Antonie van Leeuwenhoek (1674): Talab ke paani me pehli 'Jeevit Koshika' dekhi.\n\n"
        "• Robert Brown (1831): Koshika ke kendrak (Nucleus) ki khoj ki.\n\n"
        "• J.E. Purkinje (1839): Koshika dravya ko 'Protoplasm' (Jeev Dravya) naam diya.\n\n"
        "• Yaad Rakhne Ki Trick: Hooke = Dead, Leeuwenhoek = Living, Brown = Nucleus!"
    )
    d2.multiline_text((105, 955), txt2, fill="#F8FAFC", font=f_body, spacing=13)
    img2.save("slide_2.png")
    slide_files.append("slide_2.png")

    # ----------------- SLIDE 3: Cell Theory -----------------
    img3 = Image.new("RGB", (1080, 1920), color="#020617")
    d3 = ImageDraw.Draw(img3)
    draw_base_scaffold(d3, 3)

    d3.text((75, 195), "3. Koshika Siddhant (Cell Theory)", fill="#F43F5E", font=f_h1)

    box3 = [75, 265, 1005, 830]
    d3.rounded_rectangle(box3, radius=22, fill="#0B132B", outline="#F43F5E", width=2)
    paste_rounded_glow_asset(img3, get_verified_asset("nucleus_3d"), box3, glow_rgb=(244, 63, 94), corner_radius=22)
    d3.rounded_rectangle([95, 285, 470, 340], radius=10, fill="#881337")
    d3.text((115, 298), "Cell Control Center (Kendrak)", fill="#FDA4AF", font=f_badge)

    d3.rounded_rectangle([75, 860, 1005, 1680], radius=22, fill="#0F172A", outline="#334155", width=2)
    d3.text((105, 890), "Siddhant Ke Mukhya Niyam Aur Aavishkarak:", fill="#F43F5E", font=f_label)

    txt3 = (
        "• Schleiden & Schwann (1838-1839): Koshika Siddhant diya.\n\n"
        "• Mukhya Niyam: Sabhi paudhe aur janwar koshikaon se milkar bane hain.\n\n"
        "• Koshika jeevan ki sabse mool sanrachnatmak ikai hai.\n\n"
        "• Rudolf Virchow: Kaha ki sabhi nayi koshikaayein purani koshikaon ke vibhajan se banti hain."
    )
    d3.multiline_text((105, 955), txt3, fill="#F8FAFC", font=f_body, spacing=13)
    img3.save("slide_3.png")
    slide_files.append("slide_3.png")

    # ----------------- SLIDE 4: Interactive Quiz & Trophy Visual -----------------
    img4 = Image.new("RGB", (1080, 1920), color="#020617")
    d4 = ImageDraw.Draw(img4)
    draw_base_scaffold(d4, 4)

    d4.text((75, 195), "Page 2 Ka Live Test: Sahi Answer Dein!", fill="#FBBF24", font=f_h1)

    # Question Box
    d4.rounded_rectangle([75, 260, 1005, 540], radius=22, fill="#1E293B", outline="#FBBF24", width=3)
    d4.text((105, 290), "🎯 SSC CGL / CHSL PYQ:", fill="#FBBF24", font=f_label)
    q_text = "Talab ke paani me pehli baar 'Jeevit Koshika' (Living Cell) ki khoj kisne ki thi?"
    d4.multiline_text((105, 350), textwrap.fill(q_text, width=27), fill="#FFFFFF", font=f_body, spacing=10)

    options = ["Robert Hooke", "Antonie van Leeuwenhoek", "Robert Brown", "J.E. Purkinje"]
    qy = 575
    for idx, opt in enumerate(options):
        lbl = chr(65 + idx)
        d4.rounded_rectangle([75, qy, 1005, qy + 105], radius=16, fill="#0F172A", outline="#38BDF8", width=2)
        d4.rounded_rectangle([100, qy + 18, 170, qy + 88], radius=10, fill="#38BDF8")
        d4.text((120, qy + 30), lbl, fill="#000000", font=f_badge)
        d4.text((195, qy + 35), opt, fill="#F8FAFC", font=f_body)
        qy += 130

    # Trophy Box (Bottom Safe Balance)
    trophy_box = [75, 1120, 1005, 1680]
    d4.rounded_rectangle(trophy_box, radius=22, fill="#111827", outline="#10B981", width=2)
    paste_rounded_glow_asset(img4, get_verified_asset("trophy"), [90, 1140, 420, 1660], glow_rgb=(245, 158, 11), corner_radius=15)

    d4.text((430, 1220), "🏆 SSC TOPPER CHALLENGE", fill="#FBBF24", font=f_label)
    hint_desc = (
        "• Iska sahi uttar video me bataya gaya hai!\n\n"
        "• Comment section me A, B, C ya D likhein.\n\n"
        "• Agli reel Page 3 (Koshika Ke Bhaag) par aayegi!"
    )
    d4.multiline_text((430, 1300), hint_desc, fill="#F8FAFC", font=get_font(26), spacing=12)

    img4.save("slide_4.png")
    slide_files.append("slide_4.png")
    return slide_files

# =====================================================================
# 4. Resilient TTS & 50-55s FFmpeg Engine
# =====================================================================
async def generate_voiceover_resilient(text, out_file):
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
    print(f"🎙️ Raw Voice Duration: {total_dur:.2f}s", flush=True)

    # Strict Clamping to Guarantee 50-55 Seconds
    if total_dur < 50.0:
        clamped_audio = "voice_clamped.mp3"
        factor = round(total_dur / 51.5, 3)
        subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={factor}", clamped_audio], check=True)
        audio_file = clamped_audio
        total_dur = float(subprocess.check_output(cmd_dur).decode().strip())
        print(f"⚡ Paced audio to: {total_dur:.2f}s", flush=True)
    elif total_dur > 55.0:
        clamped_audio = "voice_clamped.mp3"
        factor = round(total_dur / 53.0, 3)
        subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-filter:a", f"atempo={factor}", clamped_audio], check=True)
        audio_file = clamped_audio
        total_dur = float(subprocess.check_output(cmd_dur).decode().strip())
        print(f"⚡ Clamped audio to: {total_dur:.2f}s", flush=True)

    weights = [1.1, 1.15, 1.15, 1.0]
    tot_w = sum(weights)
    durs = [total_dur * (w / tot_w) for w in weights]

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
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        output_file
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"🎬 100% Error-Free Video Ready: {output_file}", flush=True)

# =====================================================================
# 5. Proven Resumable Multi-Attempt Instagram Upload Engine
# =====================================================================
def post_reel_to_instagram_multipart(video_file, caption, max_container_attempts=3):
    access_token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("IG_USER_ID", "").strip()

    if not access_token or not user_id:
        print("❌ UPLOAD ABORTED: IG_ACCESS_TOKEN ya IG_USER_ID environment variables missing hain!", flush=True)
        print("👉 Run: export IG_ACCESS_TOKEN='your_token' && export IG_USER_ID='your_numeric_id'", flush=True)
        return False

    print("\n🚀 Step 4: Starting Multi-Attempt Resumable Instagram Upload...", flush=True)
    last_error = None
    for container_attempt in range(1, max_container_attempts + 1):
        print(f"   ► Attempt {container_attempt}/{max_container_attempts}...", flush=True)
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
            print(f"   ⚠️ Warning on attempt {container_attempt}: {last_error}", flush=True)

        if container_attempt < max_container_attempts:
            print("   ⏳ Retrying container initialization in 25s...", flush=True)
            time.sleep(25)

    raise RuntimeError(f"Upload failed after {max_container_attempts} attempts: {last_error}")

def _create_reel_container(video_file, caption, user_id, access_token):
    init_url = GRAPH_API_BASE + str(user_id).strip() + "/media"
    data = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(init_url, data=data, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"Container init fail: {r.text}")

    res_json = r.json()
    video_id = res_json.get("id")
    upload_url = res_json.get("uri") or (RUPLOAD_BASE + str(video_id).strip())

    time.sleep(12)  # Critical handshake buffer for Meta server

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
        raise RuntimeError(f"Upload fail: {up_r.text}")

    return video_id

def _poll_container_status(video_id, access_token, max_checks=40, wait_seconds=15):
    status_url = GRAPH_API_BASE + str(video_id).strip()
    print("   ⏳ Polling Instagram transcoding status...", flush=True)
    for check_idx in range(1, max_checks + 1):
        time.sleep(wait_seconds)
        try:
            res = requests.get(status_url, params={"fields": "status_code,status", "access_token": access_token}, timeout=30).json()
            status = res.get("status_code")
            print(f"      Status Check ({check_idx}/{max_checks}): {status}", flush=True)
            if status == "FINISHED":
                return "FINISHED"
            elif status in ["ERROR", "EXPIRED"]:
                return status
        except Exception:
            continue
    return "TIMEOUT"

def _publish_reel(video_id, user_id, access_token):
    publish_url = GRAPH_API_BASE + str(user_id).strip() + "/media_publish"
    pub_res = requests.post(publish_url, data={"creation_id": video_id, "access_token": access_token}, timeout=30).json()
    if "id" in pub_res:
        print(f"\n🎉🎉 SUCCESS! Reel Published to Instagram! Post ID: {pub_res['id']}\n", flush=True)
    else:
        raise RuntimeError(f"Publish fail: {pub_res}")

# =====================================================================
# 6. Main Execution Pipeline
# =====================================================================
if __name__ == "__main__":
    # Page 2 Exact Line-by-Line Script (125 words, ~52s natural pace)
    page2_script = (
        "SSC Biology ke notes ka Page number 2 poori bariki se samjhiye! "
        "Koshika jeevan ki maulik aur sanrachnatmak ikai hai, jiske adhyayan ko Cytology kehte hain. "
        "Iska naam Latin shabd 'Cellula' yaani 'Chhote Kamre' se liya gaya hai. "
        "Pehli baar 1665 me Robert Hooke ne ped ki chhal me mrit koshika dekhi. "
        "Lekin dhyan dein: pehli jeevit koshika 1674 me Leeuwenhoek ne paani me khoji thi! "
        "Iske baad 1831 me Robert Brown ne Kendrak yaani Nucleus ki khoj ki, "
        "aur Purkinje ne jeev dravya ko Protoplasm naam diya! "
        "Koshika Siddhant Schleiden aur Schwann ne 1838 me diya, jise Rudolf Virchow ne aage badhaya "
        "ki sabhi nayi koshikaayein purani koshikaon ke vibhajan se banti hain! "
        "To dosto, screen par diye sawal ka sahi answer abhi comments me likhein, "
        "aur Page 3 ke liye follow zaroor karein!"
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

    print("Step 1: Building Master Visual Slides...", flush=True)
    slides = generate_all_slides()

    print("Step 2: Generating Resilient Voiceover (Edge-TTS)...", flush=True)
    asyncio.run(generate_voiceover_resilient(page2_script, AUDIO_OUTPUT))

    print("Step 3: Compiling Final 52s Video with FFmpeg...", flush=True)
    compile_video_master(slides, AUDIO_OUTPUT, FINAL_VIDEO)

    print("Step 4: Executing Auto-Upload to Instagram...", flush=True)
    post_reel_to_instagram_multipart(FINAL_VIDEO, caption_text)
