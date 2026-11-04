"""Route all scheduled visual explainers through the same tested Blender Studio.
The builder has no publication call. Existing account/slot/duplicate guards publish it.
"""
import datetime,hashlib,json,os,shutil,sys
from pathlib import Path
from contextlib import contextmanager
VERSION='rich_3d_v1'
SUBJECTS={'Geography':'भूगोल','History':'इतिहास','Traditional GK':'स्टैटिक जीके','Polity':'राजव्यवस्था','Economics':'अर्थशास्त्र','Science':'विज्ञान','Current Affairs':'स्टैटिक जीके'}
@contextmanager
def environment(values):
 previous={k:os.environ.get(k) for k in values}
 os.environ.update(values)
 try:yield
 finally:
  for k,v in previous.items():
   if v is None:os.environ.pop(k,None)
   else:os.environ[k]=v

def topic_priority(question):
 from gs_learning import evidence_score
 # Utility is eligibility, not a guess based on water/bank/vote keywords.
 utility=bool(question.get('explanation')) and question.get('answer') in question.get('options',{})
 import re
 # A small reading-load tie-breaker, independent of topic keywords.
 years=len(re.findall(r'(?<!\d)(?:1[5-9]|20)\d{2}(?!\d)',str(question.get('question',''))))
 return int(utility)+evidence_score(question)-.05*years-.001*max(0,len(str(question.get('question','')).split())-16)

import re as _re
_MOJIBAKE=_re.compile(r'[\u00c0-\u00ff\ufffd]|Ã|â€')
_STOP={'निम्नलिखित','में','से','कौन','सा','सी','से','है','हैं','की','का','के','को','किस','किसे','क्या','और','या','था','थी','थे','एक','भारत','भारतीय','द्वारा','लिए','शामिल','गया','गई','होता','होती'}
def clean_reference(q):
 """4 Nov: the 20:00 Static GK pick had broken PDF text ('नेटवर्कâ', 'Basilica दिँदस् Jesus')
 and an explanation about a different topic. Skip such bank rows instead of rendering them."""
 options=q.get('options') or {}
 blob=' '.join([str(q.get('question','')),str(q.get('explanation',''))]+[str(v) for v in options.values()])
 if _MOJIBAKE.search(blob):return False
 # Book answers to 'current/recent' questions go stale (e.g. 'RBI के वर्तमान गवर्नर — उर्जित पटेल').
 if _re.search(r'वर्तमान|हाल ही|हाल में|मौजूदा|अभी तक|नवीनतम|इस वर्ष|पिछले वर्ष|\bcurrent\b|\blatest\b|\brecent',str(q.get('question','')),_re.I):return False
 # Latin word glued to stray Devanagari marks is PDF damage, e.g. 'Basilica दिँदस्'.
 if _re.search(r'[A-Za-z]{3,}\s+[\u0900-\u097f]*[\u0901][\u0900-\u097f]*\u094d(?:\s|$)',blob):return False
 def words(t):return {w for w in _re.findall(r'[\u0900-\u097fA-Za-z]{3,}',t) if w not in _STOP}
 option_words=set().union(*[words(str(v)) for v in options.values()]) if options else set()
 qwords=words(str(q.get('question','')))-option_words
 ewords=words(str(q.get('explanation','')))
 answer=str(options.get(q.get('answer'),'')).strip()
 expl=str(q.get('explanation',''))
 # The explanation must actually contain the answer (e.g. 'एकता दिवस' row explained Dhyan Chand).
 tokens=[t for t in _re.findall(r'[\u0900-\u097fA-Za-z0-9]+',answer) if t not in _STOP and len(t)>=2]
 if tokens and sum(t in expl for t in tokens)/len(tokens)<.6:return False
 return True

def choose_reference(bank,subject,used):
 eligible=[]
 for q in bank:
  digest=hashlib.sha256(q.get('question','').encode()).hexdigest()
  if digest in used or q.get('answer') not in q.get('options',{}) or len(q.get('explanation',''))<11 or not clean_reference(q):continue
  if subject and q.get('subject')!=subject:continue
  eligible.append((digest,q))
 if not eligible:raise RuntimeError('No unused grounded question for subject; no old/static substitute')
 # Honor the next-question promise from the most recent published subject episode.
 plans=[]
 for base in ('experiments/scheduled_visual_gs','experiments/daily_visual_gs'):
  for path in Path(base).glob('*/script.json'):
   if not (path.parent/'published.json').exists():continue
   try:
    prior=json.loads(path.read_text())
    if prior.get('subject')==subject and prior.get('series_next_hash'):plans.append((str(path),prior['series_next_hash']))
   except (OSError,ValueError):continue
 for _,promised in sorted(plans,reverse=True):
  for candidate in eligible:
   if candidate[0]==promised:return candidate
 # Keep exact subject, grounding and duplicate filtering; rank only eligible references.
 return max(eligible,key=lambda item:topic_priority(item[1]))

def build(root,day):
 root=Path(root);root.mkdir(parents=True,exist_ok=True)
 if (root/'published.json').exists() and json.loads((root/'published.json').read_text()).get('media_id'):
  raise RuntimeError('Already published output: keep the original video and receipt; choose a future slot')
 import auto_poster as e
 bank=json.loads(os.environ['GS_REFERENCE_JSON']) if os.getenv('GS_REFERENCE_JSON') else e.load_bank()
 subject=os.getenv('GS_VISUAL_SUBJECT','')
 used=set()
 for base in ('experiments/scheduled_visual_gs','experiments/daily_visual_gs'):
  for path in Path(base).glob('*/script.json'):
   if path.parent==root:continue
   try:used.add(json.loads(path.read_text()).get('question_hash'))
   except (OSError,ValueError):continue
 if not subject:
  choices=sorted({q.get('subject') for q in bank if q.get('subject') in SUBJECTS and q.get('subject')!='Current Affairs'})
  if not choices:raise RuntimeError('No supported subject in reference bank')
  offset=datetime.date.fromisoformat(day).toordinal()%len(choices)
  choices=choices[offset:]+choices[:offset]
  chosen=None
  for item in choices:
   try:chosen=choose_reference(bank,item,used);subject=item;break
   except RuntimeError:continue
  if not chosen:raise RuntimeError('Unused source bank exhausted')
 else:chosen=choose_reference(bank,subject,used)
 digest,q=chosen
 following=None
 try:following=choose_reference(bank,subject,used|{digest})
 except RuntimeError:pass
 repo=Path(__file__).resolve().parent
 sys.path.insert(0,str(repo/'gs_animation_studio'))
 from dynamic import DynamicRecovery
 from gs_learning import experiment
 format_name=os.getenv('GS_EXPERIMENT_FORMAT') or experiment(day,subject)
 if format_name not in ('exam_trap','visual_mystery','map_pyq_challenge'):raise ValueError('Unsupported experiment format')
 objective={'exam_trap':'share','visual_mystery':'save','map_pyq_challenge':'follow' if following else 'save'}[format_name]
 from gs_storyboard import grounded_storyboard
 locked=grounded_storyboard(q,format_name)
 from gs_geography_plan import grounded_map_plan
 source_map_plan=grounded_map_plan(q,locked)
 source='Verified question-bank reference; do not add claims beyond this reference: '+json.dumps(q,ensure_ascii=False)
 values={'STUDIO_TOPIC_TEXT':q['question'],'STUDIO_SUBJECT':SUBJECTS.get(subject,'auto'),'STUDIO_REFERENCE_TEXT':source,'STUDIO_REVIEWED_RECIPE':'','STUDIO_REVIEWED_SHA256':'','STUDIO_VOICE':'auto','STUDIO_VERIFY_RECOVERY':'0','GS_SOURCE_MAP_PLAN':json.dumps(source_map_plan,ensure_ascii=False),'GS_LOCKED_STORYBOARD':json.dumps(locked,ensure_ascii=False),'GS_EXPERIMENT_FORMAT':format_name,'GS_PRIMARY_OBJECTIVE':objective,'GS_SERIES_NEXT':following[1]['question'] if following else ''}
 with environment(values):
  runner=DynamicRecovery(repo=repo)
  if not runner.run():
   detail=(runner.report.get('events') or [{}])[-1].get('detail','')
   raise RuntimeError('3D build failed: '+detail[-2500:]+'; diagnostics: '+str(runner.diag))
 out=runner.root
 recipe=json.loads((out/'recipe.json').read_text());checks=json.loads((out/'file_checks.json').read_text())
 if recipe.get('quality_version')!=VERSION:raise RuntimeError('Old visual quality version refused')
 video=out/'final.mp4';digest_video=hashlib.sha256(video.read_bytes()).hexdigest()
 if digest_video!=checks['sha256']:raise RuntimeError('3D export hash mismatch')
 shutil.copy(video,root/'reel.mp4');shutil.copy(out/'contact_sheet.jpg',root/'contact_sheet.jpg')
 for name in ('recipe.json','audio.json','sources.json','scene_checks.json','file_checks.json','build_receipt.json'):
  if (out/name).exists():shutil.copy(out/name,root/name)
 script={'ok':True,'title':recipe['title'],'subject':subject,'renderer_version':VERSION,'question_hash':digest,'reference':q,'experiment_format':format_name,'primary_objective':objective,'series_next_topic':following[1]['question'] if following else None,'series_next_hash':following[0] if following else None,'topic_policy':'evidence_cohort_v2','topic_priority':topic_priority(q),'recall':recipe.get('recall'),'share_card':recipe.get('share_card'),'share_reason':recipe.get('share_reason'),'scenes':[{'label':s['heading'],'quiz_options':s.get('quiz_options'),'speech':s['speech'],'role':s.get('role'),'revision_card':s.get('revision_card',False),'teaches':s.get('teaches'),'animation':{'type':'blender_3d','setting':s['setting'],'visible_action':s['visual_action']}} for s in recipe['scenes']]}
 (root/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2))
 (root/'validated.json').write_text(json.dumps({'renderer_version':VERSION,'date':day,'sha256':digest_video,'duration':checks['duration_seconds'],'voice':checks['voice'],'studio_output':str(out.relative_to(repo)),'built_on_github':bool(os.getenv('GITHUB_ACTIONS'))},ensure_ascii=False,indent=2))
 # Use an actual video frame for the Instagram cover.
 import subprocess
 subprocess.run(['ffmpeg','-y','-v','error','-ss','0.5','-i',str(root/'reel.mp4'),'-frames:v','1',str(root/'cover.jpg')],check=True,timeout=30)
 return script
