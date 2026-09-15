import os
import sys
import json
import time
import asyncio
import subprocess
import requests
from pypdf import PdfReader
from PIL import Image, ImageDraw
from groq import Groq
import edge_tts

PDF_PATH = "notes.pdf"
PROGRESS_FILE = "progress.json"
FRAME_IMG = "frame.png"
AUDIO_OUTPUT = "voiceover.mp3"
OUTPUT_VIDEO = "reel_output.mp4"

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
    Tum ek expert competitive exam educator ho.
    Neeche diye gaye PDF text me se ek SINGLE important topic chun kar 30 second ki Hindi Reel script banao.
    
    Strictly return ONLY a valid JSON object without backticks, markdown, or extra words:
    {{
      "hook_title": "Attractive 3-4 words topic title",
      "spoken_script": "30 seconds Hindi voiceover script (exam trick or core concept). Clear and direct.",
      "bullet_points": ["Point 1", "Point 2", "Point 3"],
      "caption": "Instagram reel caption with hashtags"
    }}

    PDF Text:
    {raw_text[:2500]}
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
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(AUDIO_OUTPUT)

def create_graphic_frame(reel_data):
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Header Box
    draw.rectangle([(80, 200), (1000, 360)], fill=(30, 41, 59))
    title = reel_data.get("hook_title", "EXAM CAPSULE")
    draw.text((120, 240), f"🔥 {title}", fill=(250, 204, 21))

    # Bullets
    y_offset = 550
    for pt in reel_data.get("bullet_points", []):
        draw.rectangle([(80, y_offset), (1000, y_offset + 140)], fill=(30, 41, 59))
        draw.text((120, y_offset + 40), f"✔ {pt}", fill=(255, 255, 255))
        y_offset += 200

    img.save(FRAME_IMG)

def render_video():
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", FRAME_IMG,
        "-i", AUDIO_OUTPUT,
        "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(cmd, check=True)

def upload_video_to_temp_host(file_path):
    """Instagram ke download karne ke liye temporary public link banata hai."""
    print("🌐 Uploading video for Instagram download link...")
    with open(file_path, "rb") as f:
        res = requests.post(
            "[https://catbox.moe/user/api.php](https://catbox.moe/user/api.php)",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": f}
        )
    if res.status_code == 200 and res.text.startswith("http"):
        return res.text.strip()
    raise RuntimeError(f"Temporary video link nahi bana: {res.text}")

def post_reel_to_instagram(video_url, caption):
    access_token = os.environ.get("IG_ACCESS_TOKEN")
    user_id = os.environ.get("IG_USER_ID")
    
    if not access_token or not user_id:
        raise ValueError("IG_ACCESS_TOKEN ya IG_USER_ID GitHub Secrets me missing hai!")

    print("📲 Step 1: Instagram container create ho raha hai...")
    container_url = f"[https://graph.facebook.com/v19.0/](https://graph.facebook.com/v19.0/){user_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": access_token
    }
    r = requests.post(container_url, data=payload)
    res_data = r.json()
    creation_id = res_data.get("id")
    
    if not creation_id:
        raise RuntimeError(f"Instagram Container Error: {res_data}")

    # Instagram server processing wait
    print("⏳ Step 2: Instagram par video ready hone ka wait ho raha hai...")
    status_url = f"[https://graph.facebook.com/v19.0/](https://graph.facebook.com/v19.0/){creation_id}"
    for _ in range(15):
        time.sleep(10)
        status_res = requests.get(status_url, params={"fields": "status_code", "access_token": access_token}).json()
        status = status_res.get("status_code")
        print(f"Status: {status}...")
        if status == "FINISHED":
            break
        elif status == "ERROR":
            raise RuntimeError(f"Instagram video processing fail hui: {status_res}")

    print("🚀 Step 3: Reel publish ho rahi hai...")
    publish_url = f"[https://graph.facebook.com/v19.0/](https://graph.facebook.com/v19.0/){user_id}/media_publish"
    publish_res = requests.post(publish_url, data={"creation_id": creation_id, "access_token": access_token}).json()
    
    if "id" in publish_res:
        print(f"🎉 Reel successfully Instagram par post ho gayi! Post ID: {publish_res['id']}")
    else:
        raise RuntimeError(f"Publish failed: {publish_res}")

def main():
    print("🚀 [Step 1] Reading topic from notes.pdf...")
    raw_text, page_num, total = extract_pdf_topic()
    print(f"Loaded Page {page_num} of {total}")

    print("🤖 [Step 2] Processing exam script with Groq...")
    reel_data = generate_exam_script(raw_text)
    print(f"Topic: {reel_data.get('hook_title')}")

    print("🎙️ [Step 3] Generating Hindi Audio (Edge-TTS)...")
    asyncio.run(create_voiceover(reel_data.get("spoken_script")))

    print("🖼️ [Step 4] Creating Poster Frame...")
    create_graphic_frame(reel_data)

    print("🎬 [Step 5] Merging to 9:16 Video (FFmpeg)...")
    render_video()

    print("🌐 [Step 6] Posting Reel to Instagram...")
    public_video_url = upload_video_to_temp_host(OUTPUT_VIDEO)
    post_reel_to_instagram(public_video_url, reel_data.get("caption", ""))

    print("\n✅ All steps completed successfully!")

if __name__ == "__main__":
    main()
