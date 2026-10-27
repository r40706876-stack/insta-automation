"""GS Animation Studio: manual, topic-specific, genuine Blender scene builds."""
import os,json,sys,shutil,subprocess,time,hashlib,argparse
from pathlib import Path
REPO=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/'gs_animation_studio'))
from prepare_voice import prepare
p=argparse.ArgumentParser();p.add_argument('--topic',choices=['dam_pressure','canal_lock'],required=True);a=p.parse_args()
run_id=os.getenv('GITHUB_RUN_ID',str(int(time.time())));attempt=os.getenv('GITHUB_RUN_ATTEMPT','1')
assert run_id.isdigit() and attempt.isdigit()
folder=run_id if attempt=='1' else run_id+'-attempt-'+attempt
r=REPO/'experiments/gs_animation_studio'/a.topic/folder;r.mkdir(parents=True,exist_ok=True)
assert not (r/'final.mp4').exists(),'Existing completed export: use a new run attempt, never reuse an old MP4'
blender=os.getenv('BLENDER_BIN','/tmp/blender/blender');start=time.time();env=dict(os.environ,STUDIO_ROOT=str(r),CANAL_ROOT=str(r))
font=REPO/'experiments/canal_lock_3d/Mukta.ttf';shutil.copy(font,r/'Mukta.ttf')
if a.topic=='dam_pressure':
 src=REPO/'gs_animation_studio/dam_pressure'
 for name in ['recipe.json','scene.py','compose.py']:shutil.copy(src/name,r/name)
 prepare(r,json.loads((r/'recipe.json').read_text()))
 subprocess.run(['xvfb-run','-a',blender,'-b','-t','4','--python',str(r/'scene.py')],check=True,env=env)
 subprocess.run([sys.executable,str(r/'compose.py')],check=True,env=env)
else:
 src=REPO/'experiments/canal_lock_3d'
 for name in ['voice.flac','audio.json','canal_lock_blender.py','compose.py']:shutil.copy(src/name,r/name)
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(r/'voice.flac'),str(r/'voice.wav')],check=True)
 subprocess.run(['xvfb-run','-a',blender,'-b','-t','4','--python',str(r/'canal_lock_blender.py')],check=True,env=env)
 subprocess.run([sys.executable,str(r/'compose.py')],check=True,env=env)
 shutil.copy(r/'panama_water_lift_3d.mp4',r/'final.mp4')
 (r/'canal_lock.blend').rename(r/'scene.blend')
subprocess.run([sys.executable,str(REPO/'gs_animation_studio/verify_output.py'),str(r)],check=True)
receipt={'topic':a.topic,'run_id':run_id,'attempt':attempt,'commit':os.getenv('GITHUB_SHA'),'built_on_github':bool(os.getenv('GITHUB_ACTIONS')),'elapsed_seconds':round(time.time()-start,2),'sha256':hashlib.sha256((r/'final.mp4').read_bytes()).hexdigest(),'instagram_publish':False}
(r/'build_receipt.json').write_text(json.dumps(receipt,indent=2))
# Keep the durable review deliverables compact; never commit intermediate render frames or API responses.
for f in r.iterdir():
 if f.name not in {'final.mp4','voice.flac','audio.json','file_checks.json','scene_checks.json','build_receipt.json','recipe.json','contact_sheet.jpg','scene.blend'}:f.unlink()
subprocess.run(['xz','-f','-T2','-6',str(r/'scene.blend')],check=True)
print('STUDIO_OUTPUT='+str(r),flush=True)
with open(os.environ.get('GITHUB_OUTPUT','/tmp/studio-output'),'a') as f:f.write('output='+str(r.relative_to(REPO))+'\n')
