"""One explicitly authorized late science experiment replacement; no generation, no retry loop."""
import os,json,hashlib,datetime,subprocess
from pathlib import Path
import auto_poster as e
ROOT=Path('experiments/meerut_delhi_people_v3/publication')
ROOT.mkdir(parents=True,exist_ok=True)
SOURCE=Path('experiments/meerut_delhi_people_v3/people_story_v3_notes_safe_v2.mp4')
ARTIFACT=Path('experiments/meerut_delhi_people_v3/published.json')
SLOT=ROOT/'slot.json'
RECEIPT=ROOT/'published.json';STARTED=ROOT/'publish_started.json'
EXPECTED=os.environ['REVIEWED_SHA256']
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
title='मेरठ में विद्रोह… फिर सिपाही दिल्ली क्यों गए? | 1857'
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
 persist('Reconcile existing science experiment publication')
 print(json.dumps(existing,ensure_ascii=False));raise SystemExit(0)
assert not STARTED.exists(),'A prior attempt is uncertain: inspect account before any retry'
# The user explicitly said publish now after the original slot was missed.
# Keep the ordinary lateness checks intact; this isolated command records that authorization.
os.environ.pop('GS_TARGET_UTC',None)
save(STARTED,{'started_utc':now(),'source_sha256':EXPECTED,'authorized_late_publish':True,'user_instruction':'User requested a new experiment and immediate publication'})
persist('Record authorized one-off science experiment publication attempt before API call')
caption=title+'\n\n9 मई: मेरठ में 85 सिपाहियों को सज़ा।\n10 मई: विद्रोह और साथियों की रिहाई।\n11 मई: दिल्ली पहुँचकर बहादुर शाह ज़फ़र से नेतृत्व की माँग।\n\nज़फ़र साझा नेतृत्व के प्रतीक बने; हर मोर्चे के सेनापति नहीं।\nदोस्त से पूछो—शुरुआत कहाँ हुई और नेतृत्व किससे माँगा गया?\n\nदृश्य AI से बने सांकेतिक पुनर्निर्माण हैं, ऐतिहासिक फोटो नहीं। यात्रा-पथ सांकेतिक है।\nस्रोत: CBSE Social Science; IIT Kanpur SATHEE.\n#MinuteMeGS #History #1857 #SSC #RailwayExam #GS'
e._with_series=lambda value:value
# Exactly one upload attempt; never use post_reel's whole-upload retry loop here.
pid=e._upload_once(str(SOURCE),caption,0)
assert pid,'Instagram publication not confirmed'
receipt={'media_id':str(pid),'source_sha256':EXPECTED,'published_utc':now(),'authorized_late_publish':True,'experiment':'meerut_delhi_people_v3'}
save(RECEIPT,receipt);save(ARTIFACT,receipt)
save(SLOT,dict(receipt))
persist('Persist confirmed replacement science experiment media ID')
response=e.requests.get(e.GRAPH+str(pid),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
response.raise_for_status();receipt['permalink']=response.json().get('permalink')
assert receipt['permalink'],'Media ID confirmed; permalink lookup must be reconciled before reporting a link'
save(RECEIPT,receipt);save(ARTIFACT,receipt);save(SLOT,dict(receipt))
persist('Save actual Instagram permalink for science experiment replacement')
print(json.dumps(receipt,ensure_ascii=False))
