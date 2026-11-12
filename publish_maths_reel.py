"""Ek bani hui Maths reel ko MinuteMe_GS par sirf EK baar post karna (apne cover ke saath).
Usage: python publish_maths_reel.py downloads/maths_demo/maths_demo_2.mp4 maths_reel/demo_bells.json [cover.jpg]
Duplicate-safe: video ke paas <video>.published.json receipt + account par caption ki pehli line check."""
import os, sys, json, datetime
from pathlib import Path
import auto_poster as e
import gs_publication as publication

VIDEO, SPEC = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
COVER = Path(sys.argv[3]) if len(sys.argv) > 3 else None
RECEIPT = VIDEO.with_suffix('.published.json')
now = lambda: datetime.datetime.now(datetime.timezone.utc).isoformat()

TITLE = ' '.join(SPEC['hook']) + ' 🔔 | RRB NTPC 2025 PYQ'
L = 'ABCD'
caption = TITLE + '\n\n' + SPEC['question_hi'] + '\n\n' + '\n'.join(f"{L[i]}) {o}" for i, o in enumerate(SPEC['options']))
caption += '\n\nपहले खुद सोचो, फिर वीडियो में हल देखो 👆 जवाब कमेंट में लिखो 👇'
caption += '\n\n📌 याद रखो\n' + '\n'.join('• ' + t for t in SPEC.get('trick', []))
caption += '\n\n📤 उस दोस्त को भेजो जो NTPC / Group D / SSC की तैयारी कर रहा है'
caption += '\n\nरोज़ 1 PYQ + शॉर्टकट — फ़ॉलो करो @minuteme_gs\n\n#Maths #LCM #MathsTricks #RRBNTPC #NTPC #RRBGroupD #SSC #Railway #MathsShortcut #MinuteMe_GS'

acc = e.requests.get(e.GRAPH + e.IG_USER_ID, params={'fields': 'username', 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
acc.raise_for_status(); assert acc.json().get('username', '').lower() == 'minuteme_gs', 'Wrong Instagram account'
if RECEIPT.exists():
    print('ALREADY PUBLISHED', RECEIPT.read_text()); raise SystemExit(0)
r = e.requests.get(e.GRAPH + e.IG_USER_ID + '/media', params={'fields': 'id,permalink,caption', 'limit': 50, 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
r.raise_for_status()
for it in r.json().get('data', []):
    if (it.get('caption') or '').split('\n')[0].strip() == TITLE:
        RECEIPT.write_text(json.dumps({'media_id': it['id'], 'permalink': it.get('permalink'), 'reconciled_utc': now()}))
        print('ALREADY PUBLISHED', it.get('permalink')); raise SystemExit(0)

os.environ.pop('GS_TARGET_UTC', None)
publication.prepare_video = lambda src, font: str(src)   # video jaisi bani waisi hi jaaye
e._with_series = lambda v: v
cover_url = e._public_url(str(COVER)) if COVER and COVER.exists() else None
print('cover:', 'ok' if cover_url else 'nahi (video ka frame cover banega)')
def via_url():
    """Repo public hai: video GitHub raw link se Instagram khud utha le (resumable upload ki jagah)."""
    import time
    repo = os.environ.get('GITHUB_REPOSITORY', 'r40706876-stack/insta-automation')
    url = f"https://raw.githubusercontent.com/{repo}/main/{VIDEO.as_posix()}"
    body = {'media_type': 'REELS', 'video_url': url, 'caption': caption, 'share_to_feed': 'true', 'access_token': e.IG_ACCESS_TOKEN}
    if cover_url: body['cover_url'] = cover_url
    publication.container_policy(body)
    c = e.requests.post(f"{e.GRAPH}{e.IG_USER_ID}/media", data=body, timeout=60).json()
    cid = c.get('id'); print('  url-container:', cid or c)
    if not cid: return None
    for _ in range(60):
        time.sleep(10)
        st = e.requests.get(f"{e.GRAPH}{cid}", params={'fields': 'status_code,status', 'access_token': e.IG_ACCESS_TOKEN}, timeout=30).json()
        print('  IG processing:', st.get('status_code'), st.get('status', ''))
        if st.get('status_code') == 'FINISHED': break
        if st.get('status_code') in ('ERROR', 'EXPIRED'): print('  IG ka kaaran:', st); return None
    else:
        return None
    pub = e.requests.post(f"{e.GRAPH}{e.IG_USER_ID}/media_publish", data={'creation_id': cid, 'access_token': e.IG_ACCESS_TOKEN}, timeout=60).json()
    print('  publish:', pub)
    return pub.get('id')


pid = via_url()
if not pid:
    print('video link se nahi hua -> purana resumable upload')
    pid = e.post_reel(str(VIDEO), caption, 0, cover_url)
assert pid, 'Instagram publication not confirmed'
rec = {'media_id': str(pid), 'published_utc': now(), 'title': TITLE}
r = e.requests.get(e.GRAPH + str(pid), params={'fields': 'permalink', 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
if r.ok: rec['permalink'] = r.json().get('permalink')
RECEIPT.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
print('PUBLISHED', json.dumps(rec, ensure_ascii=False))
