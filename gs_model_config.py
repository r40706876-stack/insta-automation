"""Configurable, discovered provider models; never log credential-bearing errors."""
import os
from functools import lru_cache
import requests
@lru_cache(maxsize=1)
def gemini_models():
    configured=os.getenv('GS_GEMINI_MODELS','').strip()
    preferred=[x.strip() for x in configured.split(',') if x.strip()] if configured else ['gemini-3.8-flash','gemini-3.6-flash','gemini-3.5-flash-lite','gemini-2.5-flash']
    try:
        r=requests.get('https://generativelanguage.googleapis.com/v1beta/models',headers={'x-goog-api-key':os.environ['GEMINI_API_KEY']},timeout=(10,20))
        if r.status_code==200:
            active={m['name'].removeprefix('models/') for m in r.json().get('models',[]) if 'generateContent' in m.get('supportedGenerationMethods',[])}
            return [name for name in preferred if name in active]
    except (requests.RequestException,KeyError,ValueError):pass
    return preferred
