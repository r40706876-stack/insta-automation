"""One explicitly authorized late science experiment replacement; no generation, no retry loop."""
import os,json,hashlib,datetime,subprocess
from pathlib import Path
import auto_poster as e
ROOT=Path('experiments/hammer_feather_20261027/publication')
ROOT.mkdir(parents=True,exist_ok=True)
SOURCE=Path('experiments/hammer_feather_20261027/preview_notes_safe_v2.mp4')
ARTIFACT=Path('experiments/hammer_feather_20261027/published.json')
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
title='हथौड़ा या पंख? हवा हटा दें तो पहले कौन गिरेगा? 🪶🔨'
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
caption=title+'\n\nपहले अपना अनुमान चुनो: हथौड़ा, पंख या दोनों साथ?\nहवा का विरोध पंख को ज्यादा रोकता है। हवा हटाने पर, एक ही ऊँचाई से साथ छोड़े गए दोनों समान त्वरण से गिरते हैं और साथ पहुँचते हैं।\n\nदोस्त को भेजकर जवाब दिखाने से पहले उसका अनुमान पूछो। आगे ऐसे आसान visual GS प्रयोग के लिए @minuteme_gs को फॉलो करो।\n\nयह शिक्षण एनिमेशन है; आकार और समय सांकेतिक हैं। तथ्य: NASA Apollo 15 Hammer–Feather demonstration.\n#MinuteMeGS #Science #GS #Gravity #SSC #RailwayExam'
e._with_series=lambda value:value
# Exactly one upload attempt; never use post_reel's whole-upload retry loop here.
pid=e._upload_once(str(SOURCE),caption,0)
assert pid,'Instagram publication not confirmed'
receipt={'media_id':str(pid),'source_sha256':EXPECTED,'published_utc':now(),'authorized_late_publish':True,'experiment':'hammer_feather_20261027'}
save(RECEIPT,receipt);save(ARTIFACT,receipt)
save(SLOT,dict(receipt))
persist('Persist confirmed replacement science experiment media ID')
response=e.requests.get(e.GRAPH+str(pid),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
response.raise_for_status();receipt['permalink']=response.json().get('permalink')
assert receipt['permalink'],'Media ID confirmed; permalink lookup must be reconciled before reporting a link'
save(RECEIPT,receipt);save(ARTIFACT,receipt);save(SLOT,dict(receipt))
persist('Save actual Instagram permalink for science experiment replacement')
print(json.dumps(receipt,ensure_ascii=False))
