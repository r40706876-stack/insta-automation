"""One explicitly authorized public Collab/notes demo from an existing reviewed reel."""
import json,hashlib,datetime
from pathlib import Path
import auto_poster as e
ROOT=Path('experiments/ar_collab_demo_20261026')
ROOT.mkdir(parents=True,exist_ok=True)
receipt=ROOT/'published.json'
started=ROOT/'publish_started.json'
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2))
if receipt.exists():
 print(receipt.read_text());raise SystemExit()
if started.exists():raise RuntimeError('Prior publication uncertain: inspect before retry')
source=Path('experiments/all_subject_trial_20261026/geography')
video=source/'reel.mp4'
assert hashlib.sha256(video.read_bytes()).hexdigest()=='362676ec756e628e6be3b63df8aac74fd26fd7fa09e99253a82af3aa564742d3'
account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
assert account.get('username','').lower()=='minuteme_gs','Wrong account'
e.resolve_font()
import gs_publication as promo
branded=promo.prepare_video(str(video),e.get_font)
caption=promo.caption((source/'caption.txt').read_text())
save(ROOT/'prepared.json',{'source':'geography','source_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'branded_sha256':hashlib.sha256(Path(branded).read_bytes()).hexdigest(),'collaborator_requested':promo.HANDLE,'phone':promo.PHONE})
save(started,{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'account':account['username']})
pid=e._upload_once(branded,caption,0)
assert pid
r={'media_id':pid,'collaborator_requested':promo.HANDLE,'notes_overlay':True,'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(receipt,r)
obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
r['permalink']=obj.get('permalink');save(receipt,r)
# Read-only diagnostic; acceptance/notification is not assumed from publication alone.
res=e.requests.get(e.GRAPH+pid+'/collaborators',params={'access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
save(ROOT/'collaborators_status.json',res)
print('DEMO_PUBLISHED',json.dumps(r))
