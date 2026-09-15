import os
import sys
import time
import random
import urllib.parse
import base64
import requests

# GitHub Secrets
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

def generate_and_cache_ai_image(prompt):
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded}.jpg?width=1080&height=1080&nologo=true&seed={seed}"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for attempt in range(1, 4):
        try:
            print(f"⏳ Attempt {attempt}: AI इमेज जनरेट की जा रही है...", flush=True)
            res = requests.get(pollinations_url, headers=headers, timeout=60)
            if res.status_code == 200 and len(res.content) > 5000:
                print("✅ AI इमेज सफलतापूर्वक बन गई!", flush=True)
                return res.content, pollinations_url
            else:
                print(f"⚠️ सर्वर रिस्पॉन्स: {res.status_code}, पुनः प्रयास...", flush=True)
        except Exception as e:
            print(f"⚠️ एरर: {e}", flush=True)
        time.sleep(3)
        
    raise Exception("❌ Pollinations AI सर्वर से रिस्पॉन्स नहीं मिला।")

def upload_to_imgur(image_bytes):
    try:
        print("⏳ Imgur सर्वर पर इमेज अपलोड हो रही है...", flush=True)
        headers = {"Authorization": "Client-ID 544ba50ebd5a3b2"}
        b64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        res = requests.post(
            "https://api.imgur.com/3/image",
            headers=headers,
            data={"image": b64_image, "type": "base64"},
            timeout=25
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("success"):
                link = data["data"]["link"]
                print(f"✅ Imgur Upload Success: {link}", flush=True)
                return link
        print(f"⚠️ Imgur स्टेटस: {res.status_code}", flush=True)
    except Exception as e:
        print(f"⚠️ Imgur अपलोड एरर: {e}", flush=True)
    return None

def get_best_image_url(prompt):
    image_bytes, direct_pollinations_url = generate_and_cache_ai_image(prompt)
    
    # primary host
    imgur_url = upload_to_imgur(image_bytes)
    if imgur_url:
        return imgur_url
        
    # backup host
    print("⚠️ Imgur बैकअप: Direct Pollinations URL का उपयोग किया जा रहा है...", flush=True)
    return direct_pollinations_url

def create_and_wait_for_media_container(image_url, caption):
    print("⏳ Step 2: Instagram मीडिया कंटेनर बनाया जा रहा है...", flush=True)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Instagram Container Error:", resp.text, flush=True)
        resp.raise_for_status()
        
    container_id = resp.json()["id"]
    print(f"✅ Container ID: {container_id}", flush=True)
    
    status_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{container_id}"
    params = {"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
    
    for _ in range(10):
        time.sleep(3)
        status_resp = requests.get(status_url, params=params)
        if status_resp.ok:
            status_code = status_resp.json().get("status_code")
            print(f"⏳ Processing Status: {status_code}", flush=True)
            if status_code == "FINISHED":
                print("✅ Instagram प्रोसेसिंग पूर्ण हुई!", flush=True)
                return container_id
            elif status_code == "ERROR":
                raise Exception("Instagram इमेज प्रोसेसिंग में विफल रहा।")
                
    return container_id

def publish_media(container_id):
    print("⏳ Step 3: Instagram पर पब्लिश किया जा रहा है...", flush=True)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Publish Error:", resp.text, flush=True)
        resp.raise_for_status()
    return resp.json()

def main():
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ Error: GitHub Secrets गायब हैं!", flush=True)
        sys.exit(1)

    topic_data = get_todays_topic()
    prompt = topic_data["prompt"]
    caption = topic_data["caption"]

    print(f"📌 टॉपिक: {prompt}", flush=True)
    image_url = get_best_image_url(prompt)
    print(f"🔗 Instagram Image Link: {image_url}", flush=True)

    container_id = create_and_wait_for_media_container(image_url, caption)
    result = publish_media(container_id)
    
    print("🎉 SUCCESS! Instagram पर पोस्ट सफलतापूर्वक पब्लिश हो गई!", flush=True)
    print(f"Result: {result}", flush=True)

if __name__ == "__main__":
    main()
