import os
import sys
import time
import random
import urllib.parse
import requests

# GitHub Secrets से टोकन और आईडी पाना
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

def generate_ai_image(prompt):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1080&nologo=true&seed={random.randint(1, 999999)}"
    print("⏳ Step 1: AI इमेज जनरेट हो रही है...")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=60)
    
    if res.status_code == 200 and len(res.content) > 5000:
        print("✅ AI इमेज सफलतापूर्वक बन गई!")
        return res.content
    else:
        raise Exception(f"Failed to generate image. Status: {res.status_code}")

def upload_to_telegra_ph(image_bytes):
    try:
        print("⏳ Server 1 (Telegraph) पर अपलोड हो रहा है...")
        res = requests.post(
            "https://telegra.ph/upload",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            timeout=15
        )
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0 and "src" in data[0]:
                direct_url = "https://telegra.ph" + data[0]["src"]
                print(f"✅ Server 1 Success: {direct_url}")
                return direct_url
    except Exception as e:
        print(f"⚠️ Server 1 Failed: {e}")
    return None

def upload_to_tmpfiles(image_bytes):
    try:
        print("⏳ Server 2 (Tmpfiles) पर अपलोड हो रहा है...")
        res = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            timeout=15
        )
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                raw_url = data["data"]["url"]
                direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                print(f"✅ Server 2 Success: {direct_url}")
                return direct_url
    except Exception as e:
        print(f"⚠️ Server 2 Failed: {e}")
    return None

def upload_to_litterbox(image_bytes):
    try:
        print("⏳ Server 3 (Litterbox) पर अपलोड हो रहा है...")
        res = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data={"reqtype": "fileupload", "time": "1h"},
            files={"fileToUpload": ("image.jpg", image_bytes, "image/jpeg")},
            timeout=15
        )
        if res.status_code == 200 and res.text.startswith("http"):
            direct_url = res.text.strip()
            print(f"✅ Server 3 Success: {direct_url}")
            return direct_url
    except Exception as e:
        print(f"⚠️ Server 3 Failed: {e}")
    return None

def get_public_image_url(prompt):
    image_bytes = generate_ai_image(prompt)
    
    # Try 1: Telegraph
    url = upload_to_telegra_ph(image_bytes)
    if url: return url
        
    # Try 2: Tmpfiles
    url = upload_to_tmpfiles(image_bytes)
    if url: return url
        
    # Try 3: Litterbox
    url = upload_to_litterbox(image_bytes)
    if url: return url
        
    raise Exception("❌ सारे इमेज सर्वर फेल हो गए!")

def create_and_wait_for_media_container(image_url, caption):
    print("⏳ Step 2: Instagram कंटेनर तैयार किया जा रहा है...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Instagram Container Error:", resp.text)
        resp.raise_for_status()
        
    container_id = resp.json()["id"]
    print(f"✅ Container Created! ID: {container_id}")
    
    # Wait for Instagram processing
    status_url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{container_id}"
    params = {"fields": "status_code", "access_token": IG_ACCESS_TOKEN}
    
    for _ in range(10):
        time.sleep(3)
        status_resp = requests.get(status_url, params=params)
        if status_resp.ok:
            status_code = status_resp.json().get("status_code")
            print(f"⏳ Instagram Processing Status: {status_code}")
            if status_code == "FINISHED":
                print("✅ Instagram इमेज रेडी हो चुकी है!")
                return container_id
            elif status_code == "ERROR":
                raise Exception("Instagram Image Processing Failed!")
                
    return container_id

def publish_media(container_id):
    print("⏳ Step 3: Instagram पर पब्लिश किया जा रहा है...")
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN
    }
    resp = requests.post(url, data=payload)
    if not resp.ok:
        print("❌ Publish Error:", resp.text)
        resp.raise_for_status()
    return resp.json()

def main():
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ Error: Secrets (IG_ACCESS_TOKEN / IG_USER_ID) मिसिंग हैं!")
        sys.exit(1)

    topic_data = get_todays_topic()
    prompt = topic_data["prompt"]
    caption = topic_data["caption"]

    print(f"📌 Topic: {prompt}")
    image_url = get_public_image_url(prompt)

    container_id = create_and_wait_for_media_container(image_url, caption)
    result = publish_media(container_id)
    
    print("🎉 🎉 SUCCESS! आपकी पोस्ट सफलतापूर्वक Instagram पर अपलोड हो गई है! 🎉 🎉")
    print(f"Post Result: {result}")

if __name__ == "__main__":
    main()
