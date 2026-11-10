"""Daily and regular subject videos use the shared rich 3D Studio engine."""
import os,json,datetime,hashlib
from pathlib import Path
import auto_poster as e
from gs_growth_quality import evaluate, caption_addendum
from gs_release import evaluate_release, compact_caption
import gs_animation_bridge as bridge
DAY=os.getenv('GS_TARGET_DATE') or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).date().isoformat()
ROOT=Path(os.getenv('GS_VISUAL_OUTPUT','experiments/daily_visual_gs/'+DAY))
ROOT.mkdir(parents=True,exist_ok=True)
def save(name,value):(ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2))
def build():
 script=bridge.build(ROOT,DAY)
 from gs_review_render import review
 review(ROOT)
 release=evaluate_release(ROOT,script)
 save('release_quality.json',release)
 if not release['safe_to_publish']:raise RuntimeError('Rendered AV review blocked: '+', '.join(release['blocking_reasons']))
 return script
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
  quality=evaluate(s)
  save('growth_quality.json',quality)
  if not quality['safe_to_publish']:
   raise RuntimeError('Growth quality gate failed: '+', '.join(quality['blocking_reasons']))
  release=evaluate_release(ROOT,s)
  save('release_quality.json',release)
  if not release['safe_to_publish']:raise RuntimeError('Rendered QA blocked: '+', '.join(release['blocking_reasons']))
  assert hashlib.sha256(out.read_bytes()).hexdigest()==json.loads((ROOT/'validated.json').read_text())['sha256']
  account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();assert account.get('username','').lower()=='minuteme_gs'
  save('publish_started.json',{'date':DAY});e._with_series=lambda x:x
  caption=compact_caption(s)
  pid=e._upload_once(str(out),caption,0)
  assert pid;save('published.json',{'media_id':pid,'date':DAY})
  obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();save('published.json',{'media_id':pid,'permalink':obj.get('permalink'),'date':DAY})
 else:
  if (ROOT/'published.json').exists() and json.loads((ROOT/'published.json').read_text()).get('media_id'):
   print((ROOT/'published.json').read_text());raise SystemExit(0)
  if os.getenv('GS_REVIEW_ONLY')=='1' and (ROOT/'reel.mp4').exists() and (ROOT/'validated.json').exists() and (ROOT/'script.json').exists():
   # bani hui reel ka sirf Gemini AV review dobara (503/429 ke baad), dobara render nahi
   from gs_review_render import review
   review(ROOT);release=evaluate_release(ROOT,json.loads((ROOT/'script.json').read_text()));save('release_quality.json',release)
   if not release['safe_to_publish']:raise RuntimeError('Rendered AV review blocked: '+', '.join(release['blocking_reasons']))
  elif not (ROOT/'release_review.json').exists() or os.getenv('GS_FORCE_BUILD')=='1' or not (ROOT/'validated.json').exists() or json.loads((ROOT/'validated.json').read_text()).get('renderer_version')!=bridge.VERSION:build()
