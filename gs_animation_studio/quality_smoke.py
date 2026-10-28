"""Build-only six-scene Blender integration check. No voices, secrets or publication."""
import argparse,copy,json,os,shutil,subprocess,sys
from pathlib import Path
from planner import validate
from visual_contract import validate_visual,VERSION
BASE=Path(__file__).resolve().parent

def obj(id,kind,pos,action='none',to=None,**extra):
 d={'id':id,'kind':kind,'pos':pos,'size':[.8]*3,'color':'#35b7b1','action':action,'label':''}
 if to is not None:d['to']=to
 return d|extra

def test_plan():
 scenes=[
  ('इतिहास • पात्र','coast',[obj('gandhi','person',[-1.5,0,0],'walk',[-.5,0,0],role='gandhi',gesture='collect',interact_with='salt'),obj('salt','salt',[.5,-.8,0],'grow')]),
  ('अर्थशास्त्र • लेनदेन','institution',[obj('citizen','person',[-1.5,0,0],'walk',[-.5,0,0]),obj('coin','coin',[.1,0,.5],'move',[1.2,0,.5])]),
  ('विज्ञान • मशीन','laboratory',[obj('gear','gear',[-1,0,0],'spin'),obj('piston','piston',[1,0,0],'rise',[1,0,.9])]),
  ('राजव्यवस्था • मतदान','institution',[obj('citizen','person',[-1.4,0,0],'walk',[-.4,0,0]),obj('ballot','ballot',[1,0,0],'pulse')]),
  ('भूगोल • नक्शा','neutral',[obj('map','map',[0,0,0],'trace',map_region='gujarat',route=[[72.5802,23.0608],[72.8014,20.8867]],markers=[{'at':[72.58,23.06],'label':'साबरमती'},{'at':[72.80,20.89],'label':'दांडी'}],size=[1.2]*3),obj('arrow','arrow',[-1.8,-.4,0],'move',[-1,-.4,0],size=[.3]*3)]),
  ('अंतरिक्ष • तटरेखा','space',[obj('earth','planet',[-1.1,0,0],'spin'),obj('moon','moon',[1.2,0,0],'orbit')])]
 result={'title':'3D इंजन का तकनीकी परीक्षण','subject':'QA only','quality_version':VERSION,'dynamic':True,'share_reason':'Build-only verification','recall':'Not a published lesson','scenes':[]}
 for title,setting,objects in scenes:result['scenes'].append({'heading':title,'explanation':'परीक्षण दृश्य • प्रकाशित पाठ नहीं','setting':setting,'visual_action':'The articulated object demonstrates its supported operation with visible motion','speech':'यह केवल वीडियो इंजन की जाँच है और इसे पब्लिश नहीं किया जाएगा।','teaches':'Exercise assets, do not assert educational physics from this test fixture','objects':objects})
 result.update(speech=[s['speech'] for s in result['scenes']],titles=[[s['heading'],s['explanation']] for s in result['scenes']]);validate(result);validate_visual(result);return result

def render(root,blender):
 from PIL import Image,ImageDraw
 import numpy as np
 root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
 (root/'recipe.json').write_text(json.dumps(test_plan(),ensure_ascii=False,indent=2));(root/'audio.json').write_text(json.dumps({'seconds':[2]*6,'voice':'NONE: build-only QA fixture'}))
 for name in ('rich_assets.py','world_land.json','dandi_map.json','world_land.LICENSE','dandi_map.LICENSE'):shutil.copy(BASE/name,root/name)
 shutil.copy(BASE/'known_good/Mukta.ttf',root/'Mukta.ttf')
 env=dict(os.environ,STUDIO_ROOT=str(root),STUDIO_PREVIEW_FRAME='12',LIBGL_ALWAYS_SOFTWARE='1')
 prefix=['xvfb-run','-a'] if shutil.which('xvfb-run') else []
 subprocess.run(prefix+[blender,'-b','-t','4','--python',str(BASE/'scene_dynamic.py')],env=env,check=True,timeout=240)
 # Render both phases of each real 3D set, not title/zoom-only placeholders.
 frames=[k*48+d for k in range(6) for d in (12,35)]
 code="import bpy;from pathlib import Path;s=bpy.context.scene;s.render.image_settings.file_format='JPEG';root=Path("+repr(str(root))+");[(s.frame_set(f),setattr(s.render,'filepath',str(root/('frame_'+str(f)+'.jpg'))),bpy.ops.render.render(write_still=True)) for f in "+repr(frames)+"]"
 subprocess.run(prefix+[blender,'-b',str(root/'scene.blend'),'-t','4','--python-expr',code],env=env,check=True,timeout=240)
 sheet=Image.new('RGB',(1080,1280),(8,25,38));checks=[]
 import importlib.util
 spec=importlib.util.spec_from_file_location('compose_quality_preview',BASE/'compose_dynamic.py');module=importlib.util.module_from_spec(spec);os.environ['STUDIO_ROOT']=str(root);spec.loader.exec_module(module)
 for k in range(6):
  a,b=(np.asarray(Image.open(root/f'frame_{f}.jpg').convert('RGB'),dtype=np.float32)[420:1000,75:620] for f in frames[k*2:k*2+2]);fraction=float((np.abs(a-b).max(axis=2)>12).mean());assert fraction>.001,(k,fraction)
  checks.append({'scene':k+1,'changed_fraction':fraction})
  f=frames[k*2+1];im=module.overlay(Image.open(root/f'frame_{f}.jpg').convert('RGB'),f-1);im.save(root/f'scene_{k+1}.jpg');sheet.paste(im.resize((360,640)),((k%3)*360,(k//3)*640))
 sheet.save(root/'contact_sheet.jpg');(root/'quality_smoke.json').write_text(json.dumps({'passed':True,'quality_version':VERSION,'no_publication':True,'actual_rendered_motion':checks},indent=2));print('RICH_3D_SMOKE_PASSED',checks,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--root',default='/tmp/gs-quality-preview');args=p.parse_args()
 if args.render:render(args.root,os.getenv('BLENDER_BIN','/tmp/blender/blender'))
 else:test_plan();print('RICH_PLAN_PASSED')
