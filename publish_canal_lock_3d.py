"""Publish the exact user-approved Panama reel once; retain duplicate protection."""
import os,json,hashlib,datetime,subprocess
from pathlib import Path
import auto_poster as e
import gs_publication as publication
ROOT=Path('experiments/canal_lock_3d')
SOURCE=ROOT/'panama_water_lift_3d.mp4'
RECEIPT=ROOT/'published.json'
STARTED=ROOT/'publish_started.json'
EXPECTED='92924810eab107c067404ca8eba6e121417862e09242da50755ec0e3823eb3f6'
TITLE='इतना बड़ा जहाज़ ऊपर कैसे चढ़ता है? | पनामा की पानी वाली लिफ्ट'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def persist(message):
 subprocess.run(['git','add',str(ROOT)],check=True)
 if subprocess.run(['git','diff','--cached','--quiet']).returncode:
  subprocess.run(['git','commit','-m',message+' [skip ci]'],check=True)
  subprocess.run(['git','pull','--rebase'],check=True)
  subprocess.run(['git','push'],check=True)
assert SOURCE.is_file() and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED,'Reviewed file hash mismatch'
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
 save(RECEIPT,existing);persist('Reconcile existing Panama reel')
 print(json.dumps(existing,ensure_ascii=False));raise SystemExit(0)
assert not STARTED.exists(),'Prior attempt uncertain: reconcile account before retry'
os.environ.pop('GS_TARGET_UTC',None)
save(STARTED,{'started_utc':now(),'source_sha256':EXPECTED,'user_authorized_publish_now':True})
persist('Record single approved Panama publication attempt')
caption=TITLE+'\n\nजहाज़ को कोई क्रेन ऊपर नहीं खींचती। ऊँची झील का पानी नली से लॉक के खाने में आता है। पानी का स्तर बढ़ता है और तैरता जहाज़ साथ उठता है। दोनों तरफ स्तर बराबर होने पर आगे का दरवाज़ा खुलता है।\n\nयह एक लॉक का सरल 3D कट-अवे मॉडल है, पूरी नहर का वास्तविक आकार नहीं। पनामा में ऐसे कई लॉक जहाज़ को ऊपर और फिर नीचे ले जाते हैं।\n\nस्रोत: Panama Canal Authority — pancanal.com/en/design-of-the-locks/\n\nसभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं।\nWhatsApp: +91 89892 79637\nhttps://wa.me/918989279637\n#MinuteMeGS #PanamaCanal #Geography #GS #SSC #RailwayExam'
# This approved MP4 already has the safe-area notes banner. Do not add a second banner or change its bytes.
def exact_reviewed(src,font):
 assert Path(src).resolve()==SOURCE.resolve()
 assert hashlib.sha256(Path(src).read_bytes()).hexdigest()==EXPECTED
 return str(src)
publication.prepare_video=exact_reviewed
e._with_series=lambda value:value
pid=e._upload_once(str(SOURCE),caption,2000)
assert pid,'Instagram publication not confirmed'
receipt={'media_id':str(pid),'source_sha256':EXPECTED,'published_utc':now(),'experiment':'canal_lock_3d','collaborator_requested':publication.HANDLE}
save(RECEIPT,receipt);persist('Persist actual Panama Instagram media ID')
response=e.requests.get(e.GRAPH+str(pid),params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30)
response.raise_for_status();receipt['permalink']=response.json().get('permalink')
assert receipt['permalink'],'Reconcile permalink before reporting publication'
save(RECEIPT,receipt);persist('Save Panama Instagram reel permalink')
print(json.dumps(receipt,ensure_ascii=False))
