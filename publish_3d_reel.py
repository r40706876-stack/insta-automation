"""Publish a finished 3D reel from downloads/<kind>/<run folder>/ to MinuteMe_GS exactly once.
Usage: python publish_3d_reel.py downloads/body/2026-10-29_run123 body|blood_moon
Duplicate-safe: receipt (published.json) in the folder + caption-title check on the account."""
import os, sys, json, datetime, subprocess
from pathlib import Path
import auto_poster as e
import gs_publication as publication

FOLDER = Path(sys.argv[1]); KIND = sys.argv[2]
VIDEO = next(p for p in sorted(FOLDER.glob('*.mp4')))
RECEIPT, STARTED = FOLDER / 'published.json', FOLDER / 'publish_started.json'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p, o): p.write_text(json.dumps(o, ensure_ascii=False, indent=2))
def persist(msg):
    subprocess.run(['git', 'add', str(FOLDER)], check=True)
    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode:
        subprocess.run(['git', 'commit', '-m', msg + ' [skip ci]'], check=True)
        for _ in range(3):
            if subprocess.run(['git', 'pull', '--rebase', '-q']).returncode == 0 and subprocess.run(['git', 'push', '-q']).returncode == 0: break

# ---------------------------------------------------------------- caption
if KIND == 'body':
    plan = json.loads((FOLDER / 'plan.json').read_text(encoding='utf-8'))
    tags = '#मानवशरीर #HumanBody #Biology #GeneralScience #SSC #Railway #RRBGroupD #GK #MinuteMe_GS'
    credit = '3D models: Z-Anatomy (CC BY-SA 4.0), BodyParts3D/DBCLS (CC BY-SA 2.1 JP)'
else:
    plan = json.loads(Path('experiments/blood_moon_3d/timeline.json').read_text(encoding='utf-8'))
    tags = '#चंद्रग्रहण #BloodMoon #LunarEclipse #Geography #GeneralScience #SSC #Railway #GK #MinuteMe_GS'
    credit = ''
sc = plan['scenes']
TITLE = f"{sc[0]['title']} | {plan.get('topic', '')}".strip(' |')
body = [f"• {s['title']} — {s['sub']}" for s in sc[1:] if s.get('sub') and 'quiz' not in s]
quiz = next((s['quiz'] for s in sc if 'quiz' in s), None)
caption = TITLE + '\n\n' + '\n'.join(body)
if quiz: caption += f"\n\n❓ {quiz['q']}\n{quiz['a']}\n{quiz['b']}\nजवाब कमेंट में लिखो 👇"
caption += '\n\nरोज़ ऐसे 3D सवाल के लिए फ़ॉलो करो @minuteme_gs\n\n' + tags + (('\n\n' + credit) if credit else '')

# ---------------------------------------------------------------- checks
acc = e.requests.get(e.GRAPH + e.IG_USER_ID, params={'fields': 'username', 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
acc.raise_for_status(); assert acc.json().get('username', '').lower() == 'minuteme_gs', 'Wrong Instagram account'
existing = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else None
if not existing:
    r = e.requests.get(e.GRAPH + e.IG_USER_ID + '/media', params={'fields': 'id,permalink,caption', 'limit': 50, 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
    r.raise_for_status()
    for it in r.json().get('data', []):
        if (it.get('caption') or '').split('\n')[0].strip() == TITLE:
            existing = {'media_id': it['id'], 'permalink': it.get('permalink'), 'reconciled_utc': now()}; break
if existing:
    save(RECEIPT, existing); persist('Reconcile already-published 3D reel'); print('ALREADY PUBLISHED', existing); raise SystemExit(0)
assert not STARTED.exists(), 'An earlier attempt is uncertain: check the account before retrying'
save(STARTED, {'started_utc': now(), 'video': VIDEO.name}); persist('Record 3D reel publish attempt')

# ---------------------------------------------------------------- upload (video already carries the notes banner)
os.environ.pop('GS_TARGET_UTC', None)
publication.prepare_video = lambda src, font: str(src)
e._with_series = lambda v: v
pid = e._upload_once(str(VIDEO), caption, 1500)
assert pid, 'Instagram publication not confirmed'
rec = {'media_id': str(pid), 'published_utc': now(), 'title': TITLE}
r = e.requests.get(e.GRAPH + str(pid), params={'fields': 'permalink', 'access_token': e.IG_ACCESS_TOKEN}, timeout=30)
if r.ok: rec['permalink'] = r.json().get('permalink')
save(RECEIPT, rec); persist('Save 3D reel Instagram receipt')
print('PUBLISHED', json.dumps(rec, ensure_ascii=False))
