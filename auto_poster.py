import os
import sys
import json
import requests

def call_gemini_rest_api(prompt: str) -> str:
    """Calls Gemini REST API using the active gemini-2.5-flash model."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    # Only working model for new API accounts
    model = "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Gemini API Error ({response.status_code}): {response.text}")

    try:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise Exception(f"Failed to parse API response: {response.text}") from e

def generate_reel_content():
    """Generates prompt and reels topic."""
    prompt = (
        "Generate a short, viral, engaging Hindi-English (Hinglish) Instagram Reel script "
        "and caption about an interesting fact, motivation, or tech tip. Keep it crisp."
    )
    print("Calling Gemini API...")
    return call_gemini_rest_api(prompt)

def main():
    print("🚀 Auto Reel Generator Started...")
    try:
        content = generate_reel_content()
        print("Generated Reel Content:")
        print(content)
        
        # Reel save / post logic runs here
        print("Done successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
