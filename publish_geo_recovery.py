"""One explicitly authorized late Geography replacement; no generation, no retry loop."""
import os,json,hashlib,datetime,subprocess
from pathlib import Path
import auto_poster as e
ROOT=Path('experiments/manual_geo_recovery_20261027_1000')
ROOT.mkdir(parents=True,exist_ok=True)
SOURCE=Path('experiments/cinematic_seabreeze_v4/preview_notes_safe_v2.mp4')
ARTIFACT=Path('experiments/cinematic_seabreeze_v4/published.json')
SLOT=Path('experiments/regular_schedule/2026-10-27_1000.json')
RECEIPT=ROOT/'published.json';STARTED=ROOT/'publish_started.json'
EXPECTED='c6cd42755dc018c3ab6a844c228a23fa1621859d0ab26bcb436dec4cdbf0b9da'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
def persist(message):
 subprocess.run(['git','add',str(ROOT),str(SLOT.parent),str(ARTIFACT.parent)],check=True)
 changed=subprocess.run(['git','diff','--cached','--quiet']).returncode
 if changed:
  subprocess.run(['git','commit','-m',message+' [skip ci]'],check=True)
  subprocess.run(['git','pull','--rebase','-X','theirs'],check=True)
  subprocess.run(['git','push'],check=True)
# This is the reviewed replacement, not the held/rejected rain-shadow export.
assert SOURCE.exists() and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'Reviewed video hash mismatch'
account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30)
account.raise_for_status();assert account.json().get('username','').lower()=='minuteme_gs','Wrong account'
existing=None
for path in (RECEIPT,ARTIFACT,SLOT):
 if path.exists():
  obj=json.loads(path.read_text())
  if obj.get('media_id'):existing=obj;break
title='रेत इतनी गरम, फिर समुद्र से ठंडी हवा क्यों आती है? 🌊'
# Reconcile any already-published copy before considering an upload.
if not existing:
 response=e.requests.get(e.GRAPH+e.IG_USER_ID+'/media',params={'fields':'id,permalink,caption,timestamp','limit':30,'access_token':e.IG_ACCESS_TOKEN},timeout=30)
 response.raise_for_status()
 for item in response.json().get('data',[]):
  if (item.get('caption') or '').split('\n')[0].strip()==title:
   existing={'media_id':item['id'],'permalink':item.get('permalink'),'reconciled_utc':now(),'source_sha256':EXPECTED}
   break
if existing:
 save(RECEIPT,existing);save(ARTIFACT,existing)
 persist('Reconcile existing Geography publication')
 print(json.dumps(existing,ensure_ascii=False));raise SystemExit(0)
assert not STARTED.exists(),'A prior attempt is uncertain: inspect account before any retry'
# The user explicitly said publish now after the original slot was missed.
# Keep the ordinary lateness checks intact; this isolated command records that authorization.
os.environ.pop('GS_TARGET_UTC',None)
save(STARTED,{'started_utc':now(),'source_sha256':EXPECTED,'original_slot_ist':'2026-10-27 10:00','authorized_late_publish':True,'user_instruction':'Abhi karo'})
persist('Record authorized one-off Geography publication attempt before API call')
caption=title+'\n\nदिन में जमीन जल्दी गरम होती है। उसके ऊपर की गरम हवा उठती है और समुद्र की ठंडी हवा जमीन की तरफ आती है—इसे समुद्री समीर कहते हैं।\nयह सामान्य शिक्षण मॉडल है; वास्तविक हवा मौसम के साथ बदल सकती है।\n\n#MinuteMeGS #Geography #समुद्रीसमीर #GS #SSC #RailwayExam'
e._with_series=lambda value:value
# Exactly one upload attempt; never use post_reel's whole-upload retry loop here.
pid=e._upload_once(str(SOURCE),caption,0)
assert pid,'Instagram publication not confirmed'
receipt={'media_id':str(pid),'source_sha256':EXPECTED,'published_utc':now(),'original_slot_ist':'2026-10-27 10:00','authorized_late_publish':True,'replacement_for':'held rain-shadow preview'}
save(RECEIPT,receipt);save(ARTIFACT,receipt)
save(SLOT,dict(receipt,target_utc='2026-10-27T04:30:00Z'))
persist('Persist confirmed replacement Geography media ID')
response=e.requests.get(e.GRAPH+str(pid),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
response.raise_for_status();receipt['permalink']=response.json().get('permalink')
assert receipt['permalink'],'Media ID confirmed; permalink lookup must be reconciled before reporting a link'
save(RECEIPT,receipt);save(ARTIFACT,receipt);save(SLOT,dict(receipt,target_utc='2026-10-27T04:30:00Z'))
persist('Save actual Instagram permalink for Geography replacement')
print(json.dumps(receipt,ensure_ascii=False))
