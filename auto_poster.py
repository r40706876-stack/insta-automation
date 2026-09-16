import os
import sys
import json
import time
import asyncio
import subprocess
import requests
import textwrap
from pypdf import PdfReader
from PIL import Image, ImageDraw, ImageFont
from groq import Groq
import edge_tts

PDF_PATH = "notes.pdf"
PROGRESS_FILE = "progress.json"
FRAME_IMG = "frame.png"
AUDIO_OUTPUT = "voiceover.mp3"
OUTPUT_VIDEO = "reel_output.mp4"

GRAPH_API_BASE = "".join(["http", "s://", "graph.", "facebook", ".com/v19.0/"])

VOICE_NAME = "hi-IN-SwaraNeural"
WHATSAPP_NUMBER = "+91 8989971379"

def get_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("last_page", 0)
        except Exception:
            return 0
    return 0

def save_progress(page_num):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_page": page_num}, f, indent=4)

def extract_pdf_topic():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"'{PDF_PATH}' file nahi mili!")
    
    reader = PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    if total_pages == 0:
        raise ValueError("PDF file khali hai!")
        
    last_page = get_progress()
    current_page = last_page % total_pages
    text = reader.pages[current_page].extract_text() or ""
    
    save_progress(current_page + 1)
    return text, current_page + 1, total_pages

def generate_exam_script(raw_text):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY GitHub Secrets me set nahi hai!")

    client = Groq(api_key=api_key)
    model_name = "openai/gpt-oss-120b"
    print(f"Using Groq Model: {model_name}")

    prompt = f"""
    You are an expert Indian competitive exam educator creating a high-retention 40-second Instagram reel.
    Extract ONE important topic from the PDF text.

    CRITICAL RULES:
    1. "spoken_script" MUST BE WRITTEN ENTIRELY IN NATURAL DEVANAGARI HINDI (हिंदी लिपि).
       - Never write English spelling or Roman script for spoken_script.
       - Pronounce chemical compounds and names properly in Hindi (e.g. write "सोडियम कार्बोनेट", "धोने का सोडा", "क्रिस्टलीकरण").
       - After asking the question, add ellipsis (...) to create a clear 1.5-second thinking pause.
       - End the spoken_script EXACTLY with this calm closing:
         "अपना जवाब कमेंट बॉक्स में लिखिए... और सभी एग्जाम्स के कम्पलीट मॉक टेस्ट्स के लिए... स्क्रीन पर दिए गए नंबर पर व्हाट्सएप करिए।"
    2. "hook_title" and "bullet_points" MUST be in clean ENGLISH for visual display on screen.
       - Keep bullet point lines clean and under 36 characters each so formulas fit comfortably.
    3. "bullet_points" MUST have exactly 3 items:
       - Item 1: Core rule or chemical reaction
       - Item 2: Important exam application or fact
       - Item 3: "❓ Q: [Clear question testing the student]"

    Return ONLY a valid JSON object without markdown fences:
    {{
      "hook_title": "WASHING SODA FORMULA",
      "spoken_script": "दोस्तों, सोडियम कार्बोनेट को दस जल अणुओं के साथ क्रिस्टलीकरण कर धोने का सोडा बनाते हैं... यह कपड़ों की धुलाई और जल की कठोरता हटाने में उपयोगी है। अब एक प्रश्न: सोडियम कार्बोनेट का कौन सा रूप वाशिंग सोडा कहलाता है?... अपना जवाब कमेंट बॉक्स में लिखिए... और सभी एग्जाम्स के कम्पलीट मॉक टेस्ट्स के लिए... स्क्रीन पर दिए गए नंबर पर व्हाट्सएप करिए।",
      "bullet_points": [
        "Na2CO3 + 10H2O → Na2CO3·10H2O",
        "Used in laundry & water softening",
        "❓ Q: Which form is washing soda?"
      ],
      "caption": "Can you solve this exam question? Drop your answer below! #chemistry #upsc #ssc #study"
    }}

    PDF Text:
    {raw_text[:2000]}
    """

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content or "{}"
    clean_text = content.strip()
    if clean_text.startswith("```"):
        clean_text = clean_text.strip("`")
        if clean_text.startswith("json"):
            clean_text = clean_text[4:].strip()

    return json.loads(clean_text)

async def create_voiceover(text):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE_NAME,
        rate="-2%"
    )
    await communicate.save(AUDIO_OUTPUT)

def get_font(size):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def create_graphic_frame(reel_data):
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    title_font = get_font(44)
    body_font = get_font(34)
    promo_title_font = get_font(36)
    promo_num_font = get_font(44)

    # 1. Top Header Box
    draw.rounded_rectangle([(50, 180), (1030, 360)], radius=20, fill=(30, 41, 59), outline=(250, 204, 21), width=4)
    title = reel_data.get("hook_title", "EXAM CAPSULE").upper()
    if len(title) > 28:
        title = title[:28] + "..."
    draw.text((80, 245), f"🔥 {title}", fill=(250, 204, 21), font=title_font)

    # 2. Content Boxes
    y_offset = 430
    for pt in reel_data.get("bullet_points", []):
        wrapped_lines = textwrap.wrap(pt, width=38)
        box_height = max(135, len(wrapped_lines) * 48 + 42)

        draw.rounded_rectangle([(50, y_offset), (1030, y_offset + box_height)], radius=18, fill=(30, 41, 59))
        
        text_y = y_offset + 24
        for idx, line in enumerate(wrapped_lines):
            prefix = "✔ " if (idx == 0 and not line.startswith("❓")) else ("" if line.startswith("❓") else "   ")
            text_color = (250, 204, 21) if "❓" in line else (255, 255, 255)
            draw.text((80, text_y), f"{prefix}{line}", fill=text_color, font=body_font)
            text_y += 48

        y_offset += box_height + 30

    # 3. WhatsApp Promo Banner
    promo_top = 1520
    promo_bottom = 1750
    draw.rounded_rectangle([(50, promo_top), (1030, promo_bottom)], radius=24, fill=(17, 24, 39), outline=(34, 197, 94), width=4)
    
    promo_text1 = "📚 COMPLETE MOCK TESTS & E-BOOKS"
    draw.text((90, promo_top + 35), promo_text1, fill=(250, 204, 21), font=promo_title_font)
    
    promo_text2 = f"📲 WhatsApp: {WHATSAPP_NUMBER}"
    draw.text((90, promo_top + 105), promo_text2, fill=(34, 197, 94), font=promo_num_font)

    img.save(FRAME_IMG)

# Smooth Slow-Motion Zoom (Ken Burns Effect) via FFmpeg
def render_video():
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", FRAME_IMG,
        "-i", AUDIO_OUTPUT,
        "-filter_complex",
        "zoompan=z='min(zoom+0.0003,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1500:s=1080x1920:fps=30",
        "-c:v", "libx264",
        "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-t", "50",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd, check=True)

def post_reel_to_instagram_direct(video_file, caption):
    access_token = os.environ.get("IG_ACCESS_TOKEN")
    user_id = os.environ.get("IG_USER_ID")
    
    if not access_token or not user_id:
        raise ValueError("IG_ACCESS_TOKEN ya IG_USER_ID secrets me missing hai!")

    file_size = os.path.getsize(video_file)
    print(f"Video size: {file_size} bytes. Initializing upload container...")

    init_url = GRAPH_API_BASE + str(user_id).strip() + "/media"
    init_params = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": caption,
        "length": file_size,
        "access_token": access_token
    }
    r = requests.post(init_url, data=init_params)
    init_data = r.json()
    video_id = init_data.get("id")
    upload_url = init_data.get("upload_url") or init_data.get("uri")

    if not video_id or not upload_url:
        raise RuntimeError(f"Upload init fail hua: {init_data}")

    print("Uploading video binary data directly to Instagram...")
    with open(video_file, "rb") as vf:
        video_bytes = vf.read()

    headers = {
        "Authorization": f"OAuth {access_token}",
        "Offset": "0",
        "Content-Length": str(file_size),
        "X-Entity-Length": str(file_size),
        "Content-Type": "application/octet-stream"
    }
    upload_res = requests.post(upload_url, headers=headers, data=video_bytes)
    if upload_res.status_code not in [200, 201]:
        raise RuntimeError(f"Video binary upload fail hua: {upload_res.text}")

    print("Waiting for Instagram video processing...")
    status_url = GRAPH_API_BASE + str(video_id).strip()
    for _ in range(25):
        time.sleep(6)
        status_res = requests.get(status_url, params={"fields": "status_code", "access_token": access_token}).json()
        status = status_res.get("status_code")
        print(f"Status: {status}...")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            raise RuntimeError(f"Instagram processing error: {status_res}")

    print("Publishing Reel...")
    publish_url = GRAPH_API_BASE + str(user_id).strip() + "/media_publish"
    pub_res = requests.post(publish_url, data={"creation_id": video_id, "access_token": access_token}).json()

    if "id" in pub_res:
        print(f"🎉 Reel successfully published on Instagram! Post ID: {pub_res['id']}")
    else:
        raise RuntimeError(f"Publish fail hua: {pub_res}")

def main():
    print("🚀 [Step 1] Reading topic from notes.pdf...")
    raw_text, page_num, total = extract_pdf_topic()
    print(f"Loaded Page {page_num} of {total}")

    print("🤖 [Step 2] Generating Devanagari Voice & Visuals with Groq...")
    reel_data = generate_exam_script(raw_text)
    print(f"Topic: {reel_data.get('hook_title')}")

    print(f"🎙️ [Step 3] Generating Voiceover ({VOICE_NAME})...")
    asyncio.run(create_voiceover(reel_data.get("spoken_script")))

    print("🖼️ [Step 4] Creating Poster Frame...")
    create_graphic_frame(reel_data)

    print("🎬 [Step 5] Rendering Dynamic Zoom Video (FFmpeg)...")
    render_video()

    caption_base = reel_data.get("caption", "")
    promo_caption = (
        f"\n\n💬 Drop your answer in the COMMENTS below!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Complete Mock Tests & E-Books for all Competitive Exams (Banking, SSC, Railway, State PCS)!\n"
        f"📲 Send 'NOTES' on WhatsApp to get instant access: {WHATSAPP_NUMBER}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    final_caption = f"{caption_base}\n{promo_caption}"

    print("📲 [Step 6] Uploading directly to Instagram...")
    post_reel_to_instagram_direct(OUTPUT_VIDEO, final_caption)

    print("\n✅ Entire workflow completed successfully!")

if __name__ == "__main__":
    main()
