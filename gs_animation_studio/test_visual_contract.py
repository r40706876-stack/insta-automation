import copy,hashlib,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from planner import validate
from visual_contract import validate_visual
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import gs_animation_bridge as bridge

def fixture():
 people={'id':'person','kind':'person','role':'ordinary','pos':[-1,0,0],'to':[0,0,0],'size':[1,1,1],'color':'#35b7b1','action':'walk'}
 coin={'id':'coin','kind':'coin','pos':[1,0,0],'to':[2,0,0],'size':[.5,.5,.5],'color':'#f6bf45','action':'move'}
 scene={'setting':'neutral','visual_action':'A person moves while a coin is transferred','heading':'चलती क्रिया देखो','explanation':'दृश्य की जाँच के लिए','speech':'यह परीक्षण दृश्य है जिसमें पात्र और सिक्का चलते हुए दिखते हैं।','teaches':'Test renderer mechanics, not a published educational lesson','objects':[people,coin]}
 return {'title':'दृश्य इंजन की जाँच','share_reason':'Test only','recall':'Test only','scenes':[copy.deepcopy(scene) for _ in range(6)]}
class VisualContractTests(unittest.TestCase):
 def test_seven_subjects_use_same_supported_contract(self):
  for subject in ('इतिहास','विज्ञान','भूगोल','राजव्यवस्था','अर्थशास्त्र','स्टैटिक जीके','करंट अफेयर्स'):
   p=fixture();p['subject']=subject;validate(p);validate_visual(p)
 def test_pulse_and_zoom_cannot_replace_causal_action(self):
  p=fixture()
  for o in p['scenes'][0]['objects']:o['action']='pulse'
  with self.assertRaises(ValueError):validate_visual(p)
 def test_unimplemented_likeness_is_not_claimed(self):
  p=fixture();p['scenes'][0]['objects'][0]['role']='arbitrary_historical_portrait'
  with self.assertRaises(ValueError):validate_visual(p)
 def test_unimplemented_grasp_is_not_fake_salt(self):
  p=fixture();p['scenes'][0]['objects'][0].update(gesture='collect',interact_with='coin')
  with self.assertRaises(ValueError):validate_visual(p)
 def test_map_wrong_region_coordinates_blocked(self):
  p=fixture();p['scenes'][0]['objects'][0].update(kind='map',action='trace',map_region='gujarat',route=[[72.58,23.06],[100,20]])
  with self.assertRaises(ValueError):validate_visual(p)
 def test_map_trace_accepts_supported_sourced_region(self):
  p=fixture();p['scenes'][0]['objects'][0].update(kind='map',action='trace',map_region='gujarat',route=[[72.58,23.06],[72.80,20.89]],markers=[{'at':[72.8,20.89],'label':'दांडी'}]);validate(p);validate_visual(p)
 def test_unknown_asset_stops_before_render(self):
  p=fixture();p.update(needs_custom_assets=True,asset_requirement='A species-specific model is needed')
  with self.assertRaises(ValueError):validate_visual(p)
 def test_bridge_restores_environment_after_failure(self):
  before=os.environ.get('STUDIO_REVIEWED_RECIPE')
  with self.assertRaises(RuntimeError):
   with bridge.environment({'STUDIO_REVIEWED_RECIPE':'test'}):raise RuntimeError('fixture')
  self.assertEqual(os.environ.get('STUDIO_REVIEWED_RECIPE'),before)
 def test_bank_filter_obeys_subject_and_prevents_repeat(self):
  bank=[{'subject':'History','question':'old','options':{'a':'answer'},'answer':'a','explanation':'Grounded explanation for a source.'},{'subject':'Geography','question':'new','options':{'a':'answer'},'answer':'a','explanation':'Grounded explanation for a source.'}]
  with self.assertRaises(RuntimeError):bridge.choose_reference(bank,'History',{hashlib.sha256(b'old').hexdigest()})
  self.assertEqual(bridge.choose_reference(bank,'Geography',set())[1]['question'],'new')
 def test_regular_schedule_keeps_pyq_mega_and_hold(self):
  root=Path(__file__).resolve().parent.parent
  timer=(root/'.github/workflows/timer.yml').read_text();self.assertIn('07:00=list',timer);self.assertIn('17:00=mega',timer)
  source=(root/'scheduled_visual_gs.py').read_text();self.assertIn('current_affairs_hold.json',source)
  publisher=(root/'daily_visual_gs.py').read_text();self.assertIn("==bridge.VERSION",publisher);self.assertIn("=='minuteme_gs'",publisher);self.assertIn('publish_started.json',publisher)

class SharedBuilderTests(unittest.TestCase):
 def test_generic_recovery_stages_every_shared_asset(self):
  from dynamic import DynamicRecovery
  import hashlib
  base=Path(__file__).resolve().parent
  with tempfile.TemporaryDirectory() as tmp:
   r=DynamicRecovery(repo=tmp,base=base);r.root.mkdir(parents=True)
   raw=json.dumps(fixture()).encode();(r.root/'recipe.json').write_bytes(raw);r.recipe=json.loads(raw);r.plan_digest=hashlib.sha256(raw).hexdigest();r.restore_renderer()
   for name in ('rich_assets.py','world_land.json','dandi_map.json','world_land.LICENSE','dandi_map.LICENSE'):
    self.assertEqual((r.root/name).read_bytes(),(base/name).read_bytes())
   self.assertEqual((r.root/'scene.py').read_bytes(),(base/'scene_dynamic.py').read_bytes())
 def test_studio_safe_banner_is_not_added_twice(self):
  import gs_publication as p
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'reel.mp4';f.write_bytes(b'fixture-only')
   data={'quality_version':'rich_3d_v1','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'notes_banner':{'phone':p.PHONE,'version':'studio-notes-v1'}}
   (f.parent/'file_checks.json').write_text(json.dumps(data))
   with patch.object(p.subprocess,'run',side_effect=AssertionError('Should not re-encode verified safe banner')):
    self.assertEqual(p.prepare_video(f,None),str(f))
 def test_modified_video_cannot_skip_banner_by_stale_metadata(self):
  import gs_publication as p
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'reel.mp4';f.write_bytes(b'changed')
   (f.parent/'file_checks.json').write_text(json.dumps({'quality_version':'rich_3d_v1','sha256':'stale','notes_banner':{'phone':p.PHONE,'version':'studio-notes-v1'}}))
   with patch.object(p.subprocess,'run',side_effect=RuntimeError('Probe reached')):
    with self.assertRaisesRegex(RuntimeError,'Probe reached'):p.prepare_video(f,None)
 def test_scheduled_bridge_copies_only_verified_new_engine_output(self):
  import types,dynamic
  bank=[{'subject':'History','question':'नमक सत्याग्रह क्यों?','options':{'a':'नमक रोज की जरूरत था'},'answer':'a','explanation':'नमक रोजमर्रा की जरूरत था और नमक कानून के विरोध में लोग जुड़े।'}]
  fake=types.ModuleType('auto_poster');fake.load_bank=lambda:bank
  with tempfile.TemporaryDirectory() as tmp:
   repo=Path(tmp);(repo/'gs_animation_studio').mkdir();root=repo/'experiments/daily_visual_gs/2026-10-28'
   class Runner:
    def __init__(self,repo):
     self.root=Path(repo)/'experiments/gs_animation_studio/new_topic/1';self.diag=Path(repo)/'diag'
     assert os.environ['STUDIO_REVIEWED_RECIPE']==''
     assert os.environ['STUDIO_TOPIC_TEXT']==bank[0]['question']
    def run(self):
     self.root.mkdir(parents=True);video=b'verified fixture video';(self.root/'final.mp4').write_bytes(video);(self.root/'contact_sheet.jpg').write_bytes(b'fixture')
     plan=fixture();plan['quality_version']=bridge.VERSION
     (self.root/'recipe.json').write_text(json.dumps(plan));(self.root/'file_checks.json').write_text(json.dumps({'sha256':hashlib.sha256(video).hexdigest(),'duration_seconds':30,'voice':'test fixture'}));return True
   with patch.dict(sys.modules,{'auto_poster':fake}),patch.dict(os.environ,{'GS_VISUAL_SUBJECT':'History','STUDIO_REVIEWED_RECIPE':'dandi_v3'}),patch.object(bridge,'__file__',str(repo/'gs_animation_bridge.py')),patch.object(dynamic,'DynamicRecovery',Runner),patch('subprocess.run'):
    script=bridge.build(root,'2026-10-28');self.assertEqual(os.environ['STUDIO_REVIEWED_RECIPE'],'dandi_v3')
   self.assertEqual(script['renderer_version'],bridge.VERSION);self.assertEqual((root/'reel.mp4').read_bytes(),b'verified fixture video')
   self.assertEqual(json.loads((root/'validated.json').read_text())['sha256'],hashlib.sha256(b'verified fixture video').hexdigest())

if __name__=='__main__':unittest.main()
