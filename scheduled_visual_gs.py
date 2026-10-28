"""Apply the visual experiment to existing subject slots, never add extra posts."""
import os,json,datetime,runpy,sys
from pathlib import Path
import auto_poster as e
hold=Path('experiments/current_affairs_hold.json')
is_current=os.environ.get('REEL_FORMAT')=='current' or os.environ.get('GS_SUBJECT')=='Current Affairs'
if os.environ.get('POST_MODE')=='publish' and is_current and hold.exists() and json.loads(hold.read_text()).get('held'):
 print('CURRENT AFFAIRS HELD: user requested no publication; other slots continue',flush=True)
 raise SystemExit(0)
target=os.environ.get('GS_TARGET_UTC')
assert target,'Explicit slot target required'
dt=datetime.datetime.fromisoformat(target.replace('Z','+00:00')).astimezone(datetime.timezone(datetime.timedelta(hours=5,minutes=30)))
subject=os.environ.get('GS_SUBJECT','')
key=dt.strftime('%Y-%m-%d_%H%M')
os.environ['GS_TARGET_DATE']=dt.date().isoformat()
os.environ['GS_VISUAL_OUTPUT']='experiments/scheduled_visual_gs/'+key
os.environ['GS_FORCE_BUILD']='1'
if os.environ.get('REEL_FORMAT')=='current':
 subject='Current Affairs'
 items=e.pick_current(e.load_progress())
 assert items,'Current affairs could not be independently checked'
 bank=[{'subject':subject,'question':x['q'],'options':{'a':x['a']},'answer':'a','explanation':x['q']+' सही उत्तर: '+x['a']} for x in items]
 os.environ['GS_REFERENCE_JSON']=json.dumps(bank,ensure_ascii=False)
elif subject=='Geography':
 # First sourced motion topic; later episodes select unused concepts from the bank.
 prior=list(Path('experiments/scheduled_visual_gs').glob('*/script.json'))
 used=any('rainshadow-first-trial' in p.read_text() for p in prior)
 if not used:
  q={'subject':subject,'question':'rainshadow-first-trial: एक पहाड़ की दो तरफ बारिश अलग क्यों?','options':{'a':'नम हवा ऊपर उठकर ठंडी होती है; दूसरी ओर उतरती हवा गर्म और अपेक्षाकृत सूखी होती है।'},'answer':'a','explanation':'नम हवा पहाड़ पर ऊपर उठती और ठंडी होती है। संघनन से बादल और वर्षा बन सकते हैं। दूसरी तरफ नीचे उतरती हवा गर्म होती है और अपेक्षाकृत कम वर्षा होती है। यह सरलीकृत वर्षाछाया का मॉडल है; बारिश पूरी तरह शून्य होना जरूरी नहीं।','sources':['https://cloudatlas.wmo.int/orographic-influences-on-the-windward-side.html','https://www.noaa.gov/jetstream/appendix/weather-glossary-r']}
  os.environ['GS_REFERENCE_JSON']=json.dumps([q],ensure_ascii=False)
assert subject in ('Geography','History','Traditional GK','Polity','Economics','Current Affairs','Science')
os.environ['GS_VISUAL_SUBJECT']=subject
root=Path(os.environ['GS_VISUAL_OUTPUT']);root.mkdir(parents=True,exist_ok=True)
if (root/'published.json').exists() and json.loads((root/'published.json').read_text()).get('media_id'):
 print('Already published slot; keep the original video and receipt',flush=True)
 raise SystemExit(0)
(root/'experiment.json').write_text(json.dumps({'slot':key,'subject':subject,'target_utc':target,'format':'everyday visual puzzle; mechanism begins immediately; transfer question','comparison':'24h and 72h; skip, watch time, shares, follows; not proof from one post'},ensure_ascii=False,indent=2))

# All supported subjects now build through gs_animation_bridge and the shared Blender engine.
sys.argv=['daily_visual_gs.py'];runpy.run_path('daily_visual_gs.py',run_name='__main__')
if os.environ.get('POST_MODE')=='publish':
 sys.argv=['daily_visual_gs.py','--publish'];runpy.run_path('daily_visual_gs.py',run_name='__main__')
