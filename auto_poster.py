import os
import sys
import time
import random
import urllib.parse
import requests

# CONFIG
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
GRAPH_API_VERSION = "v21.0"

TOPICS = [
    {
        "prompt": "Clean flat educational science illustration, Litmus paper test, blue and red strips in beakers, bright laboratory background",
        "caption": "pH paper का रंग बदलने का साइंस! 🧪 #ScienceFacts #Learning #Chemistry"
    },
    {
        "prompt": "Clean flat educational science illustration, pH scale chart 0 to 14, colorful gradient, lemon and soap icons",
        "caption": "pH Scale समझे 30 सेकंड में! 0-6 Acidic, 7 Neutral, 8-14 Basic #Science #Study"
    },
    {
        "prompt": "Clean flat educational science illustration, baking soda and vinegar reaction with bubbles, kitchen lab setup",
        "caption": "Baking Soda सिर्फ खाने में ही नहीं, Chemistry में भी काम आता है! 💥 #Chemistry #ScienceFacts"
    }
]

def get_todays_topic():
    hour = int(time.strftime("%H"))
    return TOPICS[hour % len(TOPICS)]

def generate_and_upload_image(prompt):
    encoded = urllib.parse.quote(prompt)
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&nologo=true&seed={random.randint(1,10000)}"
    
    print("Generating AI image...")
    res = requests.get(pollinations_url)
    if res.status_code != 200:
        raise Exception("Failed to generate image from Pollinations")
        
    print("Uploading image to direct JPG host...")
    upload_res = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": ("image.jpg", res.content, "image/jpeg")}
    )
    
    direct_url = upload_res.text.strip()
    print(f"Direct Image URL: {direct_url}")
    return direct_url

def create_media_container(image_url, caption):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Instagram rejected request:", resp.text)
        resp.raise_for_status()
    return resp.json()["id"]

def publish_media(creation_id):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Instagram publish failed:", resp.text)
        resp.raise_for_status()
    return resp.json()

def main():
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("Error: Missing IG_ACCESS_TOKEN or IG_USER_ID secret!")
        sys.exit(1)

    topic_data = get_todays_topic()
    prompt = topic_data["prompt"]
    caption = topic_data["caption"]

    print(f"Topic Prompt: {prompt}")
    image_url = generate_and_upload_image(prompt)

    print("Creating media container on Instagram...")
    creation_id = create_media_container(image_url, caption)

    print("Publishing to Instagram...")
    publish_result = publish_media(creation_id)
    print("✅ Success! Published to Instagram:", publish_result)

if __name__ == "__main__":
    main()
