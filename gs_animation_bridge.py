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
 # Deterministic shortlist preference; the sourced script audit still checks meaning.
 import re
 q=str(question.get('question',''));ex=str(question.get('explanation',''))
 anchors=('पानी','बारिश','हवा','दिन','रात','सूरज','छाया','वोट','बहुमत','सरकार','कीमत','महँगाई','महंगाई','पैसा','बैंक','बचत','नमक','कर','दांडी','असहयोग','गर्मी','ब्रेक','पटरी','चाँद','वजन','नदी')
 advanced=('ऑक्सीडेटिव','समष्टि','भूराजनीति','उपधारा','एंजाइमेटिक','प्रतिरक्षात्मक')
 points=4*sum(word in q for word in anchors)+3*int('क्यों' in q or 'कैसे' in q)
 points-=8*sum(word in q for word in advanced)
 points-=3*len(re.findall(r'(?<!\d)(?:1[5-9]|20)\d{2}(?!\d)',q))
 points-=max(0,len(q.split())-16)
 # Dense source explanations are less suitable for the first, easy-concept series.
 points-=max(0,len(ex.split())-65)//10
 return points

def choose_reference(bank,subject,used):
 eligible=[]
 for q in bank:
  digest=hashlib.sha256(q.get('question','').encode()).hexdigest()
  if digest in used or q.get('answer') not in q.get('options',{}) or len(q.get('explanation',''))<11:continue
  if subject and q.get('subject')!=subject:continue
  eligible.append((digest,q))
 if not eligible:raise RuntimeError('No unused grounded question for subject; no old/static substitute')
 # Keep exact subject, grounding and duplicate filtering; rank only the eligible references.
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
 repo=Path(__file__).resolve().parent
 sys.path.insert(0,str(repo/'gs_animation_studio'))
 from dynamic import DynamicRecovery
 source='Verified question-bank reference; do not add claims beyond this reference: '+json.dumps(q,ensure_ascii=False)
 values={'STUDIO_TOPIC_TEXT':q['question'],'STUDIO_SUBJECT':SUBJECTS.get(subject,'auto'),'STUDIO_REFERENCE_TEXT':source,'STUDIO_REVIEWED_RECIPE':'','STUDIO_REVIEWED_SHA256':'','STUDIO_VOICE':'auto','STUDIO_VERIFY_RECOVERY':'0'}
 with environment(values):
  runner=DynamicRecovery(repo=repo)
  if not runner.run():raise RuntimeError('3D build failed; diagnostics: '+str(runner.diag))
 out=runner.root
 recipe=json.loads((out/'recipe.json').read_text());checks=json.loads((out/'file_checks.json').read_text())
 if recipe.get('quality_version')!=VERSION:raise RuntimeError('Old visual quality version refused')
 video=out/'final.mp4';digest_video=hashlib.sha256(video.read_bytes()).hexdigest()
 if digest_video!=checks['sha256']:raise RuntimeError('3D export hash mismatch')
 shutil.copy(video,root/'reel.mp4');shutil.copy(out/'contact_sheet.jpg',root/'contact_sheet.jpg')
 for name in ('audio.json','sources.json','scene_checks.json','file_checks.json','build_receipt.json'):
  if (out/name).exists():shutil.copy(out/name,root/name)
 script={'ok':True,'title':recipe['title'],'subject':subject,'renderer_version':VERSION,'question_hash':digest,'reference':q,'topic_policy':'easy_single_concept_v1','topic_priority':topic_priority(q),'recall':recipe.get('recall'),'share_card':recipe.get('share_card'),'share_reason':recipe.get('share_reason'),'scenes':[{'label':s['heading'],'speech':s['speech'],'animation':{'type':'blender_3d','setting':s['setting'],'visible_action':s['visual_action']}} for s in recipe['scenes']]}
 (root/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2))
 (root/'validated.json').write_text(json.dumps({'renderer_version':VERSION,'date':day,'sha256':digest_video,'duration':checks['duration_seconds'],'voice':checks['voice'],'studio_output':str(out.relative_to(repo)),'built_on_github':bool(os.getenv('GITHUB_ACTIONS'))},ensure_ascii=False,indent=2))
 # Use an actual video frame for the Instagram cover.
 import subprocess
 subprocess.run(['ffmpeg','-y','-v','error','-ss','0.5','-i',str(root/'reel.mp4'),'-frames:v','1',str(root/'cover.jpg')],check=True,timeout=30)
 return script
