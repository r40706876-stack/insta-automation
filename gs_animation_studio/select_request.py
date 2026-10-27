"""Keep arbitrary topic strings in environment data, never interpolate them into shell."""
import json,os
from pathlib import Path
from planner import SUBJECTS
r=json.loads(Path('experiments/gs_animation_studio_request.json').read_text());manual=os.getenv('EVENT_NAME')=='workflow_dispatch'
def value(name,default=''):
 return os.getenv('INPUT_'+name.upper(),default) if manual else r.get(name,default)
topic=value('topic','new_topic') or 'new_topic';voice=value('voice','auto') or 'auto';text=value('topic_text').strip();subject=value('subject','auto') or 'auto';source=value('reference_text')
if topic not in ('new_topic','dam_pressure','canal_lock'):raise ValueError('Unsupported mode')
if voice not in ('auto','female_fallback') or subject not in SUBJECTS:raise ValueError('Bad voice/subject')
if len(text)>350 or len(source)>14000:raise ValueError('Topic/source text too long')
# Strip no user input silently; NUL is invalid for process environments.
if '\x00' in text+source:raise ValueError('NUL in request')
test=(os.getenv('INPUT_TEST')=='true') if manual else r.get('verify_recovery',False) is True
rid=os.environ['GITHUB_RUN_ID'];attempt=os.getenv('GITHUB_RUN_ATTEMPT','1');folder=rid if attempt=='1' else rid+'-attempt-'+attempt
values={'STUDIO_TOPIC':topic,'STUDIO_VOICE':voice,'STUDIO_TOPIC_TEXT':text,'STUDIO_SUBJECT':subject,'STUDIO_REFERENCE_TEXT':source,'STUDIO_VERIFY_RECOVERY':str(int(test)),'STUDIO_DIAGNOSTICS':'studio_diagnostics/'+folder}
with open(os.environ['GITHUB_ENV'],'a') as f:
 for k,v in values.items():
  import uuid
  delim='GS_'+uuid.uuid4().hex
  f.write(k+'<<'+delim+'\n'+v+'\n'+delim+'\n')
print('Build-only request:',topic,subject,'custom topic' if text else 'fresh automatic topic')
