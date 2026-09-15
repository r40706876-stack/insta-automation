import os
import sys
import json
import time
import re
import textwrap
import asyncio
import requests
from pypdf import PdfReader
from google import genai
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# Secrets
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GRAPH_API_VERSION = "v21.0"

def get_pdf_text(pdf_path="notes.pdf"):
    if not os.path.exists(pdf_path):
        raise Exception(f"❌ {pdf_path} फाइल नहीं मिली!")
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

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

    client = genai.Client(api_key=GEMINI_API_KEY)

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

    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=prompt
    )

    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
    clean_json = json_match.group(0) if json_match else response.text.replace("```json", "").replace("```", "").strip()

    content = json.loads(clean_json)

    with open(progress_file, "w") as f:
        json.dump({"last_topic_index": topic_index + 1}, f)

    return content

async def create_voiceover(text, output_audio="voice.mp3"):
    print("⏳ Voiceover AI जनरेट हो रहा है...", flush=True)
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(output_audio)
    print("✅ Voiceover तैयार हो गया!", flush=True)

def create_slide_image(title, body_text, slide_num, output_path):
    img = Image.new('RGB', (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.load_default(size=44)
        font_body = ImageFont.load_default(size=36)
        font_sub = ImageFont.load_default(size=28)
    except TypeError:
        font_title = font_body = font_sub = ImageFont.load_default()

    # Title Banner
    draw.rectangle([50, 80, 1030, 200], fill=(30, 41, 59))
    draw.text((80, 115), f"📌 {title.upper()[:25]}", fill=(56, 189, 248), font=font_title)
    draw.text((920, 125), f"[{slide_num}/3]", fill=(148, 163, 184), font=font_sub)

    # Content Box
    draw.rectangle([50, 240, 1030, 1720], fill=(30, 41, 59))
    
    raw_lines = body_text.split('\n')
    y_pos = 300
    for line in raw_lines:
        wrapped_lines = textwrap.wrap(line.strip(), width=36)
        for w_line in wrapped_lines:
            draw.text((90, y_pos), w_line, fill=(241, 245, 249), font=font_body)
            y_pos += 60
        y_pos += 20

    # Footer
    draw.text((380, 1780), "⚡ Exam Prep Shorts", fill=(148, 163, 184), font=font_sub)
    img.save(output_path)

def render_reel_video(content):
    print("⏳ Reel वीडियो रेंडर हो रही है...", flush=True)
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
    
    print("✅ Reel Video (.mp4) तैयार है!", flush=True)
    return output_video

def upload_file_temp(file_path):
    print("⏳ Video को टेंपरेरी सर्वर पर होस्ट किया जा रहा है...", flush=True)
    with open(file_path, 'rb') as f:
        res = requests.post('https://catbox.moe/user/api.php', data={'reqtype': 'fileupload'}, files={'fileToUpload': f})
        if res.status_code == 200 and res.text.startswith("http"):
            url = res.text.strip()
            print(f"✅ Video Hosted Link: {url}", flush=True)
            return url
    raise Exception("❌ Video फाइल होस्ट नहीं हो पाई!")

def publish_instagram_reel(video_url, caption):
    print("⏳ Instagram Reels API पर वीडियो भेजा जा रहा है...", flush=True)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Reel Container Error:", resp.text, flush=True)
        resp.raise_for_status()
        
    container_id = resp.json()["id"]
    status_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{container_id}"
    params = {"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
    
    for _ in range(20):
        time.sleep(5)
        status_resp = requests.get(status_url, params=params)
        if status_resp.ok:
            status_code = status_resp.json().get("status_code")
            print(f"⏳ Processing Status: {status_code}", flush=True)
            if status_code == "FINISHED":
                break
            elif status_code == "ERROR":
                raise Exception("Instagram Reels प्रोसेसिंग फेल हो गई!")

    pub_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    pub_payload = {"creation_id": container_id, "access_token": IG_ACCESS_TOKEN}
    pub_resp = requests.post(pub_url, data=pub_payload)
    if not pub_resp.ok:
        print("❌ Reel Publish Error:", pub_resp.text, flush=True)
        pub_resp.raise_for_status()
    
    print("🎉 SUCCESS! Reel इंस्टाग्राम पर सफलतापूर्वक पोस्ट हो गई!", flush=True)

def main():
    print("🚀 Auto Reel Generator Started...", flush=True)
    content = generate_reel_content()
    print(f"📌 Topic: {content['topic_title']}", flush=True)
    
    video_file = render_reel_video(content)
    hosted_video_url = upload_file_temp(video_file)
    
    publish_instagram_reel(hosted_video_url, content["caption"])

if __name__ == "__main__":
    main()
