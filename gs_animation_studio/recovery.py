"""Bounded, recipe-preserving recovery. Never edits main or weakens validation."""
import argparse,hashlib,json,os,py_compile,shutil,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent

def gitsha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)
def redact(s):
 for k in ('GEMINI_API_KEY','GROQ_API_KEY','GITHUB_TOKEN','GH_TOKEN'):
  if os.getenv(k):s=s.replace(os.environ[k],'***')
 return s
class StageError(RuntimeError):
 def __init__(self,stage,code,detail=''):super().__init__(stage+': '+code);self.stage=stage;self.code=code;self.detail=detail
class Recovery:
 def __init__(self,topic,repo=None,base=None):
  self.repo=Path(repo) if repo else BASE.parent;self.base=Path(base) if base else BASE;self.topic=topic
  assert topic in ('dam_pressure','canal_lock','new_topic')
  self.run_id=os.getenv('GITHUB_RUN_ID',str(time.time_ns()));self.attempt=os.getenv('GITHUB_RUN_ATTEMPT','1');assert self.run_id.isdigit() and self.attempt.isdigit()
  self.folder=self.run_id if self.attempt=='1' else self.run_id+'-attempt-'+self.attempt
  self.root=self.repo/'experiments/gs_animation_studio'/topic/self.folder
  self.diag=Path(os.getenv('STUDIO_DIAGNOSTICS',str(self.repo/'studio_diagnostics'/self.folder)));self.diag.mkdir(parents=True,exist_ok=True)
  self.report={'topic':topic,'run_id':self.run_id,'attempt':self.attempt,'status':'running','events':[],'repairs':[],'injected_failures':[],'instagram_publish':False}
  self.manifest=json.loads((self.base/'known_good/manifest.json').read_text());self.env=dict(os.environ,STUDIO_ROOT=str(self.root),CANAL_ROOT=str(self.root));self.started=time.time();self.write()
 def write(self):atomic(self.diag/'recovery_report.json',self.report)
 def note(self,stage,status,**extra):self.report['events'].append(dict(stage=stage,status=status,**extra));self.write()
 def repair(self,name,**extra):self.report['repairs'].append(dict(action=name,**extra));self.write()
 def known(self,name):
  rel='known_good/'+name;p=self.base/rel
  if rel not in self.manifest['files'] or not p.is_file() or gitsha(p.read_bytes())!=self.manifest['files'][rel]:raise StageError('snapshot','integrity_failure',rel)
  return p
 def call(self,stage,cmd,timeout=180,env=None):
  n=len(self.report['events']);log=self.diag/(str(n)+'_'+stage+'.log');self.note(stage,'started',log=log.name)
  try:
   with log.open('w') as out:
    p=subprocess.Popen(cmd,cwd=self.repo,env=env or self.env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
    try:rc=p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
     import signal
     os.killpg(p.pid,signal.SIGKILL);p.wait();raise StageError(stage,'timeout')
   text=redact(log.read_text(errors='replace'));log.write_text(text)
   if rc:raise StageError(stage,'process_failed',text[-2500:])
   self.note(stage,'passed');return
  except StageError as exc:
   if log.exists():log.write_text(redact(log.read_text(errors='replace')))
   self.note(stage,'failed',code=exc.code,detail=redact(exc.detail));raise
 def compile(self,p):
  try:py_compile.compile(str(p),doraise=True)
  except py_compile.PyCompileError as exc:raise StageError('renderer','code_error',str(exc)[-1500:])
 def prepare_inputs(self):
  self.root.mkdir(parents=True,exist_ok=True)
  if (self.root/'final.mp4').exists():raise StageError('inputs','stale_export','Existing MP4 is never reused as a new render')
  font=self.repo/'experiments/canal_lock_3d/Mukta.ttf'
  if not font.is_file() or gitsha(font.read_bytes())!=self.manifest['files']['known_good/Mukta.ttf']:
   font=self.known('Mukta.ttf');self.repair('restore_reviewed_font')
  shutil.copy(font,self.root/'Mukta.ttf')
  source=self.repo/('gs_animation_studio/dam_pressure' if self.topic=='dam_pressure' else 'experiments/canal_lock_3d')
  if self.topic=='dam_pressure':
   for name in ('recipe.json','scene.py','compose.py'):
    src=source/name
    if not src.exists():src=self.known(self.topic+'/'+name);self.repair('restore_missing_file',file=name)
    shutil.copy(src,self.root/name)
   self.recipe=json.loads((self.root/'recipe.json').read_text())
  else:
   for src,dst in [('audio.json','audio.json'),('voice.flac','voice.flac'),('canal_lock_blender.py','scene.py'),('compose.py','compose.py')]:
    p=source/src
    if not p.exists():p=self.known(self.topic+'/'+dst);self.repair('restore_missing_file',file=dst)
    shutil.copy(p,self.root/dst)
   self.recipe=None
  self.note('inputs','passed')
 def compatible_snapshot(self):
  # A rollback is allowed only for exactly the requested reviewed lesson.
  name='recipe.json' if self.recipe is not None else 'audio.json'
  current=json.loads((self.root/name).read_text());approved=json.loads(self.known(self.topic+'/'+name).read_text())
  if current!=approved:raise StageError('snapshot','lesson_mismatch','Requested lesson changed; refusing to substitute the old story')
 def restore_renderer(self):
  self.compatible_snapshot()
  for name in ('scene.py','compose.py'):shutil.copy(self.known(self.topic+'/'+name),self.root/name)
  self.repair('restore_reviewed_renderer',commit=self.manifest['approved_commit'])
 def validate_voice(self):
  m=json.loads((self.root/'audio.json').read_text())
  if self.recipe and m['speech']!=self.recipe['speech']:raise StageError('voice','script_mismatch')
  if len(m['seconds'])!=6 or any(not .5<float(x)<40 for x in m['seconds']):raise StageError('voice','bad_scene_timing')
  self.call('voice_decode',['ffmpeg','-y','-v','error','-i',str(self.root/'voice.flac'),'-ar','44100','-ac','1',str(self.root/'voice.wav')],timeout=60)
  import wave
  with wave.open(str(self.root/'voice.wav'),'rb') as w:duration=w.getnframes()/w.getframerate()
  if abs(duration-sum(m['seconds']))>.1:raise StageError('voice','duration_mismatch')
 def restore_voice(self):
  approved=json.loads(self.known(self.topic+'/audio.json').read_text())
  if self.recipe and approved['speech']!=self.recipe['speech']:raise StageError('voice','no_matching_reviewed_audio')
  if not self.recipe and approved!=json.loads((self.root/'audio.json').read_text()):raise StageError('voice','no_matching_reviewed_audio')
  for name in ('voice.flac','audio.json'):shutil.copy(self.known(self.topic+'/'+name),self.root/name)
  self.repair('restore_matching_reviewed_voice',provider=approved.get('voice'));self.validate_voice()
 def voice(self):
  if self.topic=='canal_lock':
   try:self.validate_voice();return
   except Exception:self.restore_voice();return
  for mode in (os.getenv('STUDIO_VOICE','auto'),'female_fallback'):
   try:
    env=dict(self.env,STUDIO_VOICE=mode)
    self.call('voice_generate',[sys.executable,str(self.base/'prepare_voice.py'),str(self.root)],timeout=360,env=env)
    self.validate_voice();return
   except Exception as exc:self.note('voice','retrying',reason=type(exc).__name__)
  self.restore_voice()
 def render(self,safe=False):
  self.compile(self.root/'scene.py');self.compile(self.root/'compose.py')
  env=dict(self.env)
  if safe:env.update(LIBGL_ALWAYS_SOFTWARE='1',GALLIUM_DRIVER='llvmpipe',STUDIO_RENDER_AA='FXAA')
  # Only the antialiasing setting is adapted for the safe profile. Geometry, physics and timings remain intact.
  scene=(self.root/'scene.py').read_text()
  for literal in ("s.display.render_aa='8'","s.display.render_aa='16'"):scene=scene.replace(literal,"s.display.render_aa=os.getenv('STUDIO_RENDER_AA','8')")
  (self.root/'scene.py').write_text(scene)
  for name in ('silent_3d.mp4','scene.blend','canal_lock.blend'):(self.root/name).unlink(missing_ok=True)
  self.call('render_safe' if safe else 'render',['xvfb-run','-a',os.getenv('BLENDER_BIN','/tmp/blender/blender'),'-b','-t','2' if safe else '4','--python',str(self.root/'scene.py')],timeout=1300,env=env)
  if (self.root/'canal_lock.blend').exists():(self.root/'canal_lock.blend').rename(self.root/'scene.blend')
 def compose(self):
  (self.root/'final.mp4').unlink(missing_ok=True)
  self.call('compose',[sys.executable,str(self.root/'compose.py')],timeout=300)
  if self.topic=='canal_lock':shutil.copy(self.root/'panama_water_lift_3d.mp4',self.root/'final.mp4')
 def check(self):
  self.call('validate',[sys.executable,str(self.base/'verify_output.py'),str(self.root)],timeout=150)
 def fix_audio(self):
  p=self.root/'audio_repaired.mp4'
  self.call('audio_repair',['ffmpeg','-y','-v','error','-i',str(self.root/'final.mp4'),'-i',str(self.root/'voice.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(p)],timeout=90)
  p.replace(self.root/'final.mp4');self.repair('remux_matching_voice_and_normalize_audio')
 def run(self):
  try:
   self.prepare_inputs();self.voice()
   fault=os.getenv('STUDIO_VERIFY_RECOVERY')=='1'
   if fault:
    with (self.root/'scene.py').open('a') as f:f.write('\nINJECTED_SYNTAX_ERROR !!!\n')
    self.report['injected_failures'].append('isolated_renderer_syntax_error');self.write()
   restored=False
   try:self.render()
   except Exception as exc:
    self.note('render','recovery_required',reason=type(exc).__name__,detail=redact(str(exc)));self.restore_renderer();restored=True
    self.repair('software_render_retry');self.render(safe=True)
   try:self.compose()
   except Exception:
    if not restored:self.restore_renderer();restored=True
    self.repair('composer_retry_with_reviewed_code');self.compose()
   if fault:
    p=self.root/'test_silent.mp4'
    self.call('inject_silent_audio',['ffmpeg','-y','-v','error','-i',str(self.root/'final.mp4'),'-c:v','copy','-af','volume=0','-c:a','aac',str(p)],timeout=90);p.replace(self.root/'final.mp4')
    self.report['injected_failures'].append('isolated_silent_audio');self.write()
   try:self.check()
   except Exception:
    # Repair audio first, but keep every original video/motion/science check enabled.
    try:
     self.fix_audio();self.check()
    except Exception:
     if not restored:self.restore_renderer();restored=True
     self.repair('regenerate_failed_video_with_reviewed_renderer');self.render(safe=True);self.compose();self.check()
   if fault:
    actions={x['action'] for x in self.report['repairs']}
    if not {'restore_reviewed_renderer','remux_matching_voice_and_normalize_audio'}<=actions:raise StageError('self_test','expected_recovery_not_exercised')
   receipt={'topic':self.topic,'run_id':self.run_id,'attempt':self.attempt,'commit':os.getenv('GITHUB_SHA'),'built_on_github':bool(os.getenv('GITHUB_ACTIONS')),'elapsed_seconds':round(time.time()-self.started,2),'sha256':hashlib.sha256((self.root/'final.mp4').read_bytes()).hexdigest(),'instagram_publish':False,'recovery_verified':fault}
   atomic(self.root/'build_receipt.json',receipt)
   self.report.update(status='passed',output=str(self.root.relative_to(self.repo)),sha256=receipt['sha256']);self.write()
   keep={'final.mp4','voice.flac','audio.json','file_checks.json','scene_checks.json','build_receipt.json','recipe.json','contact_sheet.jpg','scene.blend','sources.json','request.json','audit_0.json','audit_1.json','audit_2.json'}
   for p in self.root.iterdir():
    if p.is_file() and p.name not in keep:p.unlink()
   self.call('compress_scene',['xz','-f','-T2','-6',str(self.root/'scene.blend')],timeout=120)
   shutil.copy(self.diag/'recovery_report.json',self.root/'recovery_report.json')
   return True
  except Exception as exc:
   self.report.update(status='failed',failure={'type':type(exc).__name__,'message':redact(str(exc))});self.write()
   # A failed export is never labelled final or made available as a passing reel.
   if (self.root/'final.mp4').exists():(self.root/'final.mp4').rename(self.root/'rejected_final.mp4')
   return False
  finally:
   summary=os.getenv('GITHUB_STEP_SUMMARY')
   if summary:
    with open(summary,'a') as f:
     f.write('\n## GS Animation Studio — '+self.report['status']+'\n\n')
     f.write('Auto repairs: '+str(len(self.report['repairs']))+'; injected verification faults: '+str(len(self.report['injected_failures']))+'.\n\n')
     for x in self.report['repairs']:f.write('- '+x['action']+'\n')
     if self.report.get('failure'):f.write('\nUnresolved: '+self.report['failure']['message']+'\n')
     f.write('\nDetailed attempts are in recovery_report.json and the diagnostics artifact. No Instagram publication.\n')

def main():
 p=argparse.ArgumentParser();p.add_argument('--topic',choices=['dam_pressure','canal_lock','new_topic'],required=True);a=p.parse_args()
 if a.topic=='new_topic':
  from dynamic import DynamicRecovery
  r=DynamicRecovery()
 else:r=Recovery(a.topic)
 ok=r.run()
 with open(os.environ.get('GITHUB_OUTPUT','/tmp/studio-output'),'a') as f:f.write('output='+str(r.root.relative_to(r.repo))+'\n')
 raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
