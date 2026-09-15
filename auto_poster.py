import os
import sys
import json
import asyncio
import subprocess
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

    print("Generating script with Groq (Fast & Stable)...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

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

def main():
    print("🚀 [Step 1] Reading topic from notes.pdf...")
    raw_text, page_num, total = extract_pdf_topic()
    print(f"Loaded Page {page_num} of {total}")

    print("🤖 [Step 2] Processing exam script...")
    reel_data = generate_exam_script(raw_text)
    print(f"Topic: {reel_data.get('hook_title')}")

    print("🎙️ [Step 3] Generating Hindi Audio (Edge-TTS)...")
    asyncio.run(create_voiceover(reel_data.get("spoken_script")))

    print("🖼️ [Step 4] Creating Poster Frame...")
    create_graphic_frame(reel_data)

    print("🎬 [Step 5] Merging to 9:16 Video (FFmpeg)...")
    render_video()

    print("\n✅ Reel Video Ready: reel_output.mp4")
    print(f"📝 Caption:\n{reel_data.get('caption')}")

if __name__ == "__main__":
    main()
