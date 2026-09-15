import os
import sys
import json
import time
import re
import textwrap
import asyncio
import requests
from pypdf import PdfReader
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# Environment Variables
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GRAPH_API_VERSION = "v21.0"
FONT_PATH = "NotoSansDevanagari.ttf"

def ensure_hindi_font(size):
    """
    Downloads and loads NotoSansDevanagari font to ensure Hindi text renders correctly 
    without rendering tofu boxes (□□□□).
    """
    if not os.path.exists(FONT_PATH):
        print("⏳ Downloading Hindi Devanagari Font...", flush=True)
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwght%5D.ttf"
        try:
            res = requests.get(font_url, timeout=30)
            if res.status_code == 200:
                with open(FONT_PATH, "wb") as f:
                    f.write(res.content)
                print("✅ Devanagari font downloaded successfully!", flush=True)
            else:
                raise Exception(f"Failed to download font. HTTP {res.status_code}")
        except Exception as e:
            print(f"⚠️ Font Download Error: {e}", flush=True)
            return ImageFont.load_default()
            
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception as e:
        print(f"⚠️ Error loading downloaded font: {e}", flush=True)
        return ImageFont.load_default()

def get_pdf_text(pdf_path="notes.pdf"):
    if not os.path.exists(pdf_path):
        raise Exception(f"❌ {pdf_path} file not found!")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def call_gemini_rest_api(prompt):
    """
    Direct REST API call with fallback endpoints & active models.
    """
    targets_to_try = [
        ("v1", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-pro"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1beta", "gemini-2.0-flash-exp")
    ]
    
    last_error = ""

    for api_ver, model_name in targets_to_try:
        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        try:
            print(f"Connecting to Gemini REST API: {api_ver} - {model_name}", flush=True)
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_data = response.json()
                text_output = res_data['candidates'][0]['content']['parts'][0]['text']
                print(f"Success! Response received from {api_ver} - {model_name}", flush=True)
                return text_output
            else:
                print(f"Error ({response.status_code}): {response.text}", flush=True)
                last_error = response.text
        except Exception as e:
            print(f"Exception: {e}", flush=True)
            last_error = str(e)

    raise Exception(f"All Gemini REST API endpoints failed! Last Error: {last_error}")

def generate_reel_content():
    pdf_text = get_pdf_text()
    progress_file = "progress.json"
    topic_index = 0
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r") as f:
                data = json.load(f)
                topic_index = data.get("last_topic_index", 0)
        except Exception:
            topic_index = 0

    prompt = f"""
    You are an expert educational content creator for Instagram Reels.
    Below is text from study material:
    ---
    {pdf_text[:15000]}
    ---
    Pick Topic Index #{topic_index + 1} sequentially.
    Create a 30-40 second exam-oriented short script for students.
    Output strictly in valid JSON format with NO markdown code block wrappers:
    {{
      "topic_title": "Short Topic Title (Max 5 words)",
      "voiceover_script": "Hindi/Hinglish Voiceover text (70 to 90 words total). Clear and educational.",
      "slide1_text": "Heading 1 \\n Bullet point summary",
      "slide2_text": "Heading 2 \\n Key exam highlight point",
      "slide3_text": "Heading 3 \\n Quick conclusion / memory trick",
      "caption": "Instagram Reel Caption with Hashtags"
    }}
    """

    raw_response_text = call_gemini_rest_api(prompt)

    json_match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
    clean_json = json_match.group(0) if json_match else raw_response_text.replace("```json", "").replace("```", "").strip()

    content = json.loads(clean_json)

    with open(progress_file, "w") as f:
        json.dump({"last_topic_index": topic_index + 1}, f)

    return content

async def create_voiceover(text, output_audio="voice.mp3"):
    print("⏳ Generating AI Voiceover...", flush=True)
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(output_audio)
    print("✅ Voiceover generated successfully!", flush=True)

def create_slide_image(title, body_text, slide_num, output_path):
    img = Image.new('RGB', (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    font_title = ensure_hindi_font(44)
    font_body = ensure_hindi_font(36)
    font_sub = ensure_hindi_font(28)

    # Header Box
    draw.rectangle([50, 80, 1030, 200], fill=(30, 41, 59))
    draw.text((80, 115), f"📌 {title[:25]}", fill=(56, 189, 248), font=font_title)
    draw.text((920, 125), f"[{slide_num}/3]", fill=(148, 163, 184), font=font_sub)

    # Content Box
    draw.rectangle([50, 240, 1030, 1720], fill=(30, 41, 59))
    
    raw_lines = body_text.split('\n')
    y_pos = 300
    for line in raw_lines:
        wrapped_lines = textwrap.wrap(line.strip(), width=32)
        for w_line in wrapped_lines:
            draw.text((90, y_pos), w_line, fill=(241, 245, 249), font=font_body)
            y_pos += 60
        y_pos += 20

    # Footer
    draw.text((380, 1780), "⚡ Exam Prep Shorts", fill=(148, 163, 184), font=font_sub)
    img.save(output_path)

def render_reel_video(content):
    print("⏳ Rendering Reel Video...", flush=True)
    asyncio.run(create_voiceover(content["voiceover_script"]))

    audio_clip = AudioFileClip("voice.mp3")
    total_duration = audio_clip.duration
    slide_duration = max(total_duration / 3.0, 3.0)

    slides_data = [content["slide1_text"], content["slide2_text"], content["slide3_text"]]
    clips = []

    for idx, text in enumerate(slides_data, start=1):
        img_filename = f"slide_{idx}.png"
        create_slide_image(content["topic_title"], text, idx, img_filename)
        clip = ImageClip(img_filename).set_duration(slide_duration)
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.set_audio(audio_clip)
    
    output_video = "final_reel.mp4"
    final_video.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")
    
    audio_clip.close()
    final_video.close()
    
    print("✅ Video Rendering Complete (.mp4)", flush=True)
    return output_video

def upload_file_temp(file_path):
    print("⏳ Hosting video on temporary storage...", flush=True)
    with open(file_path, 'rb') as f:
        res = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f}, timeout=120)
        if res.status_code == 200 and res.text.startswith("http"):
            url = res.text.strip()
            print(f"✅ Video Hosted Link: {url}", flush=True)
            return url
    raise Exception("❌ Failed to upload video file!")

def publish_instagram_reel(video_url, caption):
    print("⏳ Sending media container to Instagram Graph API...", flush=True)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload, timeout=60)
    if not resp.ok:
        print("❌ Reel Container Error:", resp.text, flush=True)
        resp.raise_for_status()
        
    container_id = resp.json()["id"]
    status_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{container_id}"
    params = {"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
    
    for _ in range(20):
        time.sleep(5)
        status_resp = requests.get(status_url, params=params, timeout=30)
        if status_resp.ok:
            status_code = status_resp.json().get("status_code")
            print(f"⏳ Processing Status: {status_code}", flush=True)
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                raise Exception("Instagram Reels Video Processing Failed!")

    pub_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    pub_payload = {"creation_id": container_id, "access_token": IG_ACCESS_TOKEN}
    pub_resp = requests.post(pub_url, data=pub_payload, timeout=60)
    if not pub_resp.ok:
        print("❌ Reel Publish Error:", pub_resp.text, flush=True)
        pub_resp.raise_for_status()
    
    print("🎉 SUCCESS! Reel has been published to Instagram!", flush=True)

def main():
    print("🚀 Auto Reel Generator Started...", flush=True)
    content = generate_reel_content()
    print(f"📌 Topic: {content['topic_title']}", flush=True)
    
    video_file = render_reel_video(content)
    hosted_video_url = upload_file_temp(video_file)
    
    publish_instagram_reel(hosted_video_url, content["caption"])

if __name__ == "__main__":
    main()
