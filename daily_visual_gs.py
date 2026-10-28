"""Daily and regular subject videos use the shared rich 3D Studio engine."""
import os,json,datetime,hashlib
from pathlib import Path
import auto_poster as e
import gs_animation_bridge as bridge
DAY=os.getenv('GS_TARGET_DATE') or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).date().isoformat()
ROOT=Path(os.getenv('GS_VISUAL_OUTPUT','experiments/daily_visual_gs/'+DAY))
ROOT.mkdir(parents=True,exist_ok=True)
def save(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
def build():return bridge.build(ROOT,DAY)
if __name__=='__main__':
 import sys
 if '--publish' in sys.argv:
  hold=ROOT/'publication_hold.json'
  assert not hold.exists(),'Publication held: user rejected this episode; rebuild and review required'
  receipt=ROOT/'published.json'
  if receipt.exists():print(receipt.read_text());raise SystemExit()
  assert (ROOT/'validated.json').exists(),'Build must pass first'
  assert json.loads((ROOT/'validated.json').read_text()).get('renderer_version')==bridge.VERSION,'Old renderer blocked: build with rich_3d_v1 first'
  assert not (ROOT/'publish_started.json').exists(),'Uncertain prior attempt: inspect account before retry'
  s=json.loads((ROOT/'script.json').read_text());out=ROOT/'reel.mp4'
  assert hashlib.sha256(out.read_bytes()).hexdigest()==json.loads((ROOT/'validated.json').read_text())['sha256']
  account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();assert account.get('username','').lower()=='minuteme_gs'
  save('publish_started.json',{'date':DAY});e._with_series=lambda x:x
  caption=s['title']+'\n\n'+' '.join(x['speech'] for x in s['scenes'])+'\n\nशिक्षण ऐनिमेशन सांकेतिक है। Concept practice.\n#MinuteMeGS #GS #StudyHindi #SSC #RailwayExam'
  pid=e._upload_once(str(out),caption,0)
  assert pid;save('published.json',{'media_id':pid,'date':DAY})
  obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();save('published.json',{'media_id':pid,'permalink':obj.get('permalink'),'date':DAY})
 else:
  if (ROOT/'published.json').exists() and json.loads((ROOT/'published.json').read_text()).get('media_id'):
   print((ROOT/'published.json').read_text());raise SystemExit(0)
  if os.getenv('GS_FORCE_BUILD')=='1' or not (ROOT/'validated.json').exists() or json.loads((ROOT/'validated.json').read_text()).get('renderer_version')!=bridge.VERSION:build()
