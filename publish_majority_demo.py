"""Publish one explicitly authorized, reviewed majority demo; never regenerate or loop uploads."""
import os,json,hashlib,datetime,subprocess
from pathlib import Path
import auto_poster as e
import gs_publication as publication
ROOT=Path('experiments/majority_share_demo_20261028')
SOURCE=Path('experiments/gs_animation_studio/new_topic/40660412849/final.mp4')
RECEIPT=ROOT/'published.json'
STARTED=ROOT/'publish_started.json'
EXPECTED='314a7b829e2f1a599a8257def7cfa3ca7907720c420fe58088b9be93e530eec0'
TITLE='3 सबसे ज्यादा, फिर भी बहुमत नहीं?'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def persist(message):
 subprocess.run(['git','add',str(ROOT)],check=True)
 if subprocess.run(['git','diff','--cached','--quiet']).returncode:
  subprocess.run(['git','commit','-m',message+' [skip ci]'],check=True)
  subprocess.run(['git','pull','--rebase'],check=True)
  subprocess.run(['git','push'],check=True)
assert SOURCE.is_file() and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'Reviewed file hash mismatch'
checks=json.loads((SOURCE.parent/'file_checks.json').read_text())
assert checks['sha256']==EXPECTED and checks['decoded_without_errors'] and checks['black_intervals']==0,'Reviewed video validation missing'
assert checks.get('notes_banner',{}).get('phone')=='+91 89892 79637','Required safe-area WhatsApp banner missing'
recipe=json.loads((SOURCE.parent/'recipe.json').read_text())
assert recipe['title']==TITLE and recipe.get('share_card',{}).get('cta'),'Wrong or incomplete demo lesson'
account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30)
account.raise_for_status()
assert account.json().get('username','').lower()=='minuteme_gs','Wrong Instagram account'
existing=json.loads(RECEIPT.read_text()) if RECEIPT.exists() else None
if not existing or not existing.get('media_id'):
 response=e.requests.get(e.GRAPH+e.IG_USER_ID+'/media',params={'fields':'id,permalink,caption,timestamp','limit':50,'access_token':e.IG_ACCESS_TOKEN},timeout=30)
 response.raise_for_status()
 for item in response.json().get('data',[]):
  if (item.get('caption') or '').split('\n')[0].strip()==TITLE:
   existing={'media_id':item['id'],'permalink':item.get('permalink'),'source_sha256':EXPECTED,'reconciled_utc':now()}
   break
if existing and existing.get('media_id'):
 if not existing.get('permalink'):
  response=e.requests.get(e.GRAPH+str(existing['media_id']),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
  response.raise_for_status();existing['permalink']=response.json().get('permalink')
 save(RECEIPT,existing);persist('Reconcile existing majority demo reel')
 print(json.dumps(existing,ensure_ascii=False));raise SystemExit(0)
assert not STARTED.exists(),'Prior attempt uncertain: reconcile account before retry'
os.environ.pop('GS_TARGET_UTC',None)
save(STARTED,{'started_utc':now(),'source_sha256':EXPECTED,'user_authorized_publish_now':True})
persist('Record single authorized majority demo publication attempt')
caption=TITLE+'\n\nसबसे ज्यादा और आधे से ज्यादा—यही फर्क याद रखो।\n\nसात काल्पनिक सदस्यों का उदाहरण: नीले 3, पीले 2 और बैंगनी 2। नीला अकेला सबसे बड़ा दल है, लेकिन सात में आधे से ज्यादा होने के लिए 4 चाहिए। पीले और बैंगनी साथ हों तो 2 + 2 = 4।\n\nसबसे बड़ा दल और बहुमत में उलझने वाले दोस्त को भेजो।\n\nयह गिनती समझाने वाला काल्पनिक 3D उदाहरण है; वास्तविक दलों या चुनाव परिणामों का चित्रण नहीं।\nस्रोत: NCERT, Working of Institutions — https://www.ncert.nic.in/textbook/pdf/iess404.pdf\n\nसभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं।\nWhatsApp: +91 89892 79637\nhttps://wa.me/918989279637\n#MinuteMeGS #Polity #GS #SSC #RailwayExam'
# This approved MP4 already has the safe-area notes banner. Do not add a second banner or change its bytes.
def exact_reviewed(src,font):
 assert Path(src).resolve()==SOURCE.resolve()
 assert hashlib.sha256(Path(src).read_bytes()).hexdigest()==EXPECTED
 return str(src)
publication.prepare_video=exact_reviewed
e._with_series=lambda value:value
pid=e._upload_once(str(SOURCE),caption,2000)
assert pid,'Instagram publication not confirmed'
receipt={'media_id':str(pid),'source_sha256':EXPECTED,'published_utc':now(),'experiment':'majority_share_demo_20261028','collaborator_requested':publication.HANDLE}
save(RECEIPT,receipt);persist('Persist actual majority demo Instagram media ID')
response=e.requests.get(e.GRAPH+str(pid),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
response.raise_for_status();receipt['permalink']=response.json().get('permalink')
assert receipt['permalink'],'Reconcile permalink before reporting publication'
save(RECEIPT,receipt);persist('Save majority demo Instagram reel permalink')
print(json.dumps(receipt,ensure_ascii=False))
