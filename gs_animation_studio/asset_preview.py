"""Build-only render of the Nov 2026 physics + India-map assets. Writes contact sheets; no voice, no publication."""
import json,os,shutil,subprocess,sys
from pathlib import Path
from PIL import Image
import numpy as np
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
from planner import validate
from visual_contract import validate_visual,VERSION

def obj(id,kind,pos=(0,0,0),action='none',**extra):
 return {'id':id,'kind':kind,'pos':list(pos),'size':[1.0]*3,'color':'#e0a030','action':action,'label':''}|extra

SETS={
 'physics_a':[('प्रकाश • उत्तल लेंस','laboratory',[obj('lens','lens',variant='convex')]),
              ('प्रकाश • अवतल लेंस','laboratory',[obj('lens','lens',variant='concave')]),
              ('प्रकाश • अवतल दर्पण','laboratory',[obj('mirror','mirror',variant='concave')]),
              ('प्रकाश • उत्तल दर्पण','laboratory',[obj('mirror','mirror',variant='convex')]),
              ('प्रकाश • प्रिज़्म','laboratory',[obj('prism','prism')]),
              ('विद्युत • परिपथ','laboratory',[obj('circuit','circuit')])],
 'physics_b':[('यांत्रिकी • लोलक','laboratory',[obj('pendulum','pendulum')]),
              ('यांत्रिकी • स्प्रिंग','laboratory',[obj('spring','spring')]),
              ('यांत्रिकी • उत्तोलक','laboratory',[obj('lever','lever')]),
              ('ध्वनि • तरंग','laboratory',[obj('wave','wave')]),
              ('ध्वनि • ऊँची आवृत्ति','laboratory',[obj('wave','wave',variant='high')]),
              ('भूगोल • राज्य','neutral',[obj('map','map',map_region='india',highlight_states=['Madhya Pradesh'],size=[1.2]*3)])],
 'maps':[('भूगोल • गंगा','neutral',[obj('map','map',map_region='india',rivers=['Ganga','Yamuna'],size=[1.2]*3)]),
         ('भूगोल • नर्मदा-तापी','neutral',[obj('map','map',map_region='india',rivers=['Narmada','Tapi'],size=[1.2]*3)]),
         ('भूगोल • कर्क रेखा','neutral',[obj('map','map',map_region='india',latitude_lines=[{'lat':23.44,'label':'कर्क रेखा'}],highlight_states=['Gujarat','Rajasthan','Madhya Pradesh','Chhattisgarh','Jharkhand','West Bengal','Tripura','Mizoram'],size=[1.2]*3)]),
         ('भूगोल • दक्षिण की नदियाँ','neutral',[obj('map','map',map_region='india',rivers=['Godavari','Krishna','Kaveri'],size=[1.2]*3)]),
         ('भूगोल • तमिलनाडु','neutral',[obj('map','map',map_region='india',highlight_states=['Tamil Nadu'],rivers=['Kaveri'],size=[1.2]*3)]),
         ('भूगोल • ब्रह्मपुत्र','neutral',[obj('map','map',map_region='india',rivers=['Brahmaputra'],highlight_states=['Assam'],size=[1.2]*3)])]}

def plan(scenes):
 p={'title':'नए 3D एसेट की जाँच','subject':'QA only','quality_version':VERSION,'dynamic':True,'share_reason':'Build-only verification','recall':'Not published','scenes':[]}
 for title,setting,objects in scenes:p['scenes'].append({'heading':title,'explanation':'परीक्षण दृश्य • प्रकाशित पाठ नहीं','setting':setting,'visual_action':'The physics or map asset animates its own teaching motion','speech':'यह केवल नए एसेट की जाँच है।','teaches':'Asset render check','objects':objects})
 p.update(speech=[s['speech'] for s in p['scenes']],titles=[[s['heading'],s['explanation']] for s in p['scenes']]);validate(p);validate_visual(p);return p

def render(name,root,blender):
 root=Path(root)/name;root.mkdir(parents=True,exist_ok=True)
 (root/'recipe.json').write_text(json.dumps(plan(SETS[name]),ensure_ascii=False,indent=2));(root/'audio.json').write_text(json.dumps({'seconds':[2]*6,'voice':'NONE'}))
 for f in ('rich_assets.py','world_land.json','dandi_map.json','india_states.json','india_rivers.json'):shutil.copy(BASE/f,root/f)
 env=dict(os.environ,STUDIO_ROOT=str(root),STUDIO_PREVIEW_FRAME='12',LIBGL_ALWAYS_SOFTWARE='1');pre=['xvfb-run','-a'] if shutil.which('xvfb-run') else []
 subprocess.run(pre+[blender,'-b','-t','4','--python',str(BASE/'scene_dynamic.py')],env=env,check=True,timeout=400)
 frames=[k*48+d for k in range(6) for d in (10,40)]
 code="import bpy;from pathlib import Path;s=bpy.context.scene;s.render.image_settings.file_format='JPEG';root=Path("+repr(str(root))+");[(s.frame_set(f),setattr(s.render,'filepath',str(root/('frame_'+str(f)+'.jpg'))),bpy.ops.render.render(write_still=True)) for f in "+repr(frames)+"]"
 subprocess.run(pre+[blender,'-b',str(root/'scene.blend'),'-t','4','--python-expr',code],env=env,check=True,timeout=400)
 sheet=Image.new('RGB',(6*240,2*427),(8,25,38));motion=[]
 for k in range(6):
  a,b=[Image.open(root/f'frame_{f}.jpg').convert('RGB') for f in frames[2*k:2*k+2]]
  motion.append(float((np.abs(np.asarray(a,np.float32)-np.asarray(b,np.float32)).max(axis=2)>12).mean()))
  sheet.paste(a.resize((240,427)),(k*240,0));sheet.paste(b.resize((240,427)),(k*240,427))
 return sheet,motion

if __name__=='__main__':
 out=Path(sys.argv[1] if len(sys.argv)>1 else 'experiments/asset_preview');out.mkdir(parents=True,exist_ok=True);report={}
 for name in SETS:
  try:
   sheet,motion=render(name,'/tmp/asset-preview',os.getenv('BLENDER_BIN','/tmp/blender/blender'));sheet.save(out/f'{name}.jpg',quality=88);report[name]={'ok':True,'motion':motion}
  except Exception as exc:
   report[name]={'ok':False,'error':repr(exc)[:600]}
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
