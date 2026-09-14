"""
Instagram Auto-Poster — generates an AI image and publishes it automatically.
================================================================================
Runs every hour via GitHub Actions (free, no server needed).

HOW IT WORKS
------------
1. Picks a topic from TOPICS (rotates based on current hour so it doesn't
   repeat the same one back to back).
2. Builds a free AI image via Pollinations.ai (public URL, no upload needed —
   Instagram's API can fetch the image directly from that URL).
3. Calls the Instagram Graph API in two steps:
   a. POST /{ig-user-id}/media       -> creates a media container
   b. POST /{ig-user-id}/media_publish -> publishes it live

CREDENTIALS
-----------
This script reads credentials from environment variables — it NEVER hardcodes
them. Set these as GitHub repository secrets (Settings > Secrets and
variables > Actions):
  - IG_ACCESS_TOKEN   -> your Page access token
  - IG_USER_ID        -> your Instagram Business Account ID
"""

import os
import sys
import time
import random
import urllib.parse

import requests

# ============ CONFIG ============
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")
GRAPH_API_VERSION = "v21.0"

# Rotate through these — add/edit topics anytime. Each has an image prompt
# and a caption. Feel free to swap this list for your study-material topics.
TOPICS = [
    {
        "prompt": "clean flat educational science illustration, litmus paper test, blue and red strips in beakers, bright colors, minimalist, vertical composition, no text",
        "caption": "क्या तुम्हें पता है Acid और Base को बिना चखे कैसे पहचानते हैं? 🧪\nनीला लिटमस लाल हो जाए = Acid\nलाल लिटमस नीला हो जाए = Base\n#Science #Class10 #Chemistry #StudyTips",
    },
    {
        "prompt": "clean flat educational science illustration, pH scale chart 0 to 14, colorful gradient, lemon and soap on opposite ends, minimalist vertical composition",
        "caption": "pH Scale समझो 30 सेकंड में! 0-6 Acidic, 7 Neutral, 8-14 Basic 📊\n#pH #Science #Class10Science #NCERT",
    },
    {
        "prompt": "clean flat educational science illustration, baking soda and vinegar reaction with bubbles, kitchen chemistry, bright colors, minimalist vertical composition",
        "caption": "Baking Soda सिर्फ खाने में नहीं, Chemistry में भी काम आता है! 🍞\n#Chemistry #DidYouKnow #ScienceFacts",
    },
]


def get_todays_topic():
    """Rotate topics by hour so consecutive runs don't repeat."""
    hour = int(time.strftime("%H"))
    return TOPICS[hour % len(TOPICS)]


def build_image_url(prompt):
    """Pollinations.ai gives back a public, directly-fetchable image URL —
    perfect for Instagram's API, which needs a public image_url."""
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1350&nologo=true&seed={random.randint(1, 999999)}"


def create_media_container(image_url, caption):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media"
    resp = requests.post(url, data={
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()["id"]


def publish_media(creation_id):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{IG_USER_ID}/media_publish"
    resp = requests.post(url, data={
        "creation_id": creation_id,
        "access_token": IG_ACCESS_TOKEN,
    }, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    if not IG_ACCESS_TOKEN or not IG_USER_ID:
        print("❌ IG_ACCESS_TOKEN or IG_USER_ID not set. Check GitHub secrets.")
        sys.exit(1)

    topic = get_todays_topic()
    print(f"📝 Topic selected: {topic['caption'][:50]}...")

    image_url = build_image_url(topic["prompt"])
    print(f"🎨 Image URL: {image_url}")

    # Give Pollinations a moment to actually generate the image before
    # Instagram tries to fetch it.
    print("⏳ Waiting for image to render...")
    time.sleep(10)

    print("📤 Creating media container on Instagram...")
    creation_id = create_media_container(image_url, topic["caption"])
    print(f"   → creation_id: {creation_id}")

    # Instagram needs a few seconds to finish downloading/processing the image
    # before it can be published.
    time.sleep(5)

    print("🚀 Publishing...")
    result = publish_media(creation_id)
    print(f"✅ Published! Media ID: {result.get('id')}")


if __name__ == "__main__":
    main()
