"""Time a REAL production recipe in cinematic (Cycles) mode. Build-only, never posts."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
import asset_preview as ap
src=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
root=Path('/tmp/cine-timing')/'real';root.mkdir(parents=True,exist_ok=True)
for f in ('recipe.json','audio.json'):shutil.copy(src/f,root/f)
for f in ('rich_assets.py','world_land.json','dandi_map.json','india_states.json','india_rivers.json'):shutil.copy(BASE/f,root/f)
shutil.copy(BASE/'known_good/Mukta.ttf',root/'Mukta.ttf')
blender=os.getenv('BLENDER_BIN','/tmp/blender/blender');pre=['xvfb-run','-a'] if shutil.which('xvfb-run') else []
env=dict(os.environ,STUDIO_ROOT=str(root),STUDIO_PREVIEW_FRAME='12',LIBGL_ALWAYS_SOFTWARE='1')
t0=time.time();subprocess.run(pre+[blender,'-b','-t','0','--python',str(BASE/'scene_dynamic.py')],env=env,check=True,timeout=1800);build=time.time()-t0
t1=time.time();ap.render_video('real','/tmp/cine-timing',blender,out/'real_cinematic.mp4');total=time.time()-t1
secs=sum(json.loads((root/'audio.json').read_text())['seconds'])
rep={'reel_seconds':round(secs,1),'frames':int(secs*24),'build_s':round(build),'render_overlay_s':round(total),'s_per_frame':round(total/max(1,secs*24),2),'samples':os.getenv('STUDIO_SAMPLES')}
(out/'timing.json').write_text(json.dumps(rep,indent=2));print('TIMING',rep)
