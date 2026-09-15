import os
import sys
import json
import asyncio
from pypdf import PdfReader
from google import genai
import edge_tts
from moviepy.editor import (
    TextClip,
    ColorClip,
    CompositeVideoClip,
    AudioFileClip
)

PDF_PATH = "notes.pdf"
PROGRESS_FILE = "progress.json"
OUTPUT_VIDEO = "reel_output.mp4"
AUDIO_OUTPUT = "voiceover.mp3"

def get_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f).get("last_page", 0)
        except Exception:
            return 0
    return 0

def save_progress(page_num):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_page": page_num}, f, indent=4)

def extract_pdf_topic():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"'{PDF_PATH}' file nahi mili repository me!")
    
    reader = PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    last_page = get_progress()
    
    current_page = last_page % total_pages
    text = reader.pages[current_page].extract_text() or ""
    
    # Save next page for the next run
    save_progress(current_page + 1)
    return text, current_page + 1, total_pages

def get_best_active_model(client):
    """Dynamically detects active models on your Google project to avoid 404 errors."""
    try:
        models = [m.name for m in client.models.list()]
        # Preference order of stable production models
        for preferred in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"]:
            for m in models:
                if preferred in m:
                    return m
        # Fallback to the first available content generation model
        for m in models:
            if "gemini" in m.lower() and "embed" not in m.lower():
                return m
    except Exception as e:
        print(f"Warning: Could not list models ({e}). Using default 'gemini-2.5-flash'.")
    return "gemini-2.5-flash"

def generate_exam_reel_script(raw_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable set nahi hai!")

    client = genai.Client(api_key=api_key)
    selected_model = get_best_active_model(client)
    print(f"Using Active Google Model: {selected_model}")

    prompt = f"""
    Tum ek expert competitive exam educator ho.
    Neeche diye gaye PDF text me se ek SINGLE high-yield exam topic chun kar 30-35 second ki Hindi Reel script banao.

    Strictly return ONLY a valid JSON object without any backticks, markdown, or commentary:
    {{
      "hook_title": "Attractive 3-4 words topic title",
      "spoken_script": "30-35 seconds spoken Hindi voiceover script (exam trick or high-value concept). Crisp and engaging.",
      "bullet_points": ["Key Point 1", "Key Point 2", "Key Point 3"],
      "caption": "Instagram reel caption with exam hashtags"
    }}

    PDF Text:
    {raw_text[:2500]}
    """

    response = client.models.generate_content(
        model=selected_model,
        contents=prompt
    )

    res_text = response.text.strip()
    if res_text.startswith("```"):
        res_text = res_text.strip("`")
        if res_text.startswith("json"):
            res_text = res_text[4:].strip()

    return json.loads(res_text)

async def create_voiceover(text):
    # Free natural Hindi voice
    communicate = edge_tts.Communicate(text, voice="hi-IN-MadhurNeural")
    await communicate.save(AUDIO_OUTPUT)

def render_reel_video(reel_data):
    audio_clip = AudioFileClip(AUDIO_OUTPUT)
    duration = audio_clip.duration

    # 9:16 vertical canvas (1080x1920)
    bg_clip = ColorClip(size=(1080, 1920), color=(18, 24, 38), duration=duration)

    # Title Banner
    title_text = f"🔥 {reel_data.get('hook_title', 'EXAM CAPSULE')}"
    title_clip = (
        TextClip(title_text, fontsize=56, color="#FACC15", font="Arial-Bold", size=(950, None), method="caption")
        .set_position(("center", 250))
        .set_duration(duration)
    )

    # Bullet Points on screen
    bullet_text = "\n\n".join([f"✔ {pt}" for pt in reel_data.get("bullet_points", [])])
    points_clip = (
        TextClip(bullet_text, fontsize=42, color="#FFFFFF", font="Arial", size=(900, None), method="caption")
        .set_position(("center", 600))
        .set_duration(duration)
    )

    video = CompositeVideoClip([bg_clip, title_clip, points_clip])
    video = video.set_audio(audio_clip)

    video.write_videofile(
        OUTPUT_VIDEO,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )
    return OUTPUT_VIDEO

def main():
    print("🚀 [Step 1] Reading topic from notes.pdf...")
    raw_text, page_num, total = extract_pdf_topic()
    print(f"Loaded Page {page_num} of {total}")

    print("🤖 [Step 2] Processing exam points with Gemini...")
    reel_data = generate_exam_reel_script(raw_text)
    print(f"Hook Title: {reel_data.get('hook_title')}")

    print("🎙️ [Step 3] Generating Hindi Voiceover (Edge-TTS)...")
    asyncio.run(create_voiceover(reel_data.get("spoken_script")))

    print("🎬 [Step 4] Rendering 9:16 Video Reel...")
    render_reel_video(reel_data)

    print("\n✅ Reel Video Ready: reel_output.mp4")
    print(f"📝 Caption:\n{reel_data.get('caption')}")

if __name__ == "__main__":
    main()
