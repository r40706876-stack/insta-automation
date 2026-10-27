import copy,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from planner import validate,public_url,generate,normalize_layout

def plan():
 return {'title':'नमक पर कानून क्यों?','topic_key':'salt_law','share_reason':'नमक सत्याग्रह का कारण याद रहे','recall':'किस कानून को चुनौती दी?', 'scenes':[{'heading':'नमक पर कानून','explanation':'कानून तोड़ना अहिंसक विरोध था','speech':'नमक रोज की जरूरत था और उस पर अंग्रेजों का नियंत्रण था।','teaches':'नमक कानून का विरोध','objects':[{'id':'person','kind':'person','color':'#ffffff','pos':[-1,0,0],'to':[1,0,0],'size':[.6,.6,.6],'action':'walk','label':'लोग'},{'id':'salt','kind':'salt','color':'#1a80bb','pos':[2,0,0],'size':[.7,.7,.7],'action':'grow','label':'नमक'}]} for _ in range(6)]}
class NewTopicTests(unittest.TestCase):
 def test_layout_repair_preserves_facts_and_actions(self):
  p=plan();p['scenes'][0]['objects'][0]['pos']=[-10,0,-1];p['scenes'][0]['objects'][0]['size']=[.1,3,.7]
  fixed,repairs=normalize_layout(p);validate(fixed)
  self.assertTrue(repairs);self.assertEqual(p['scenes'][0]['speech'],fixed['scenes'][0]['speech']);self.assertEqual(fixed['scenes'][0]['objects'][0]['action'],'walk')
 def test_new_topic_data_passes(self):validate(plan())
 def test_static_poster_is_rejected(self):
  p=plan()
  for o in p['scenes'][0]['objects']:o['action']='none'
  with self.assertRaises(ValueError):validate(p)
 def test_code_not_supported(self):
  p=plan();p['scenes'][0]['objects'][0]['kind']='exec_python'
  with self.assertRaises(ValueError):validate(p)
 def test_unsafe_paths_and_nonfinite_coords_rejected(self):
  p=plan();p['scenes'][0]['objects'][0]['pos'][0]=float('nan')
  with self.assertRaises(ValueError):validate(p)
 def test_private_reference_blocked(self):
  for url in ['file:///etc/passwd','http://example.com','https://127.0.0.1/a','https://user:password@example.com/a']:
   with self.assertRaises(ValueError):public_url(url)
 def test_six_scene_contract(self):
  p=plan();p['scenes']=p['scenes'][:1]
  with self.assertRaises(ValueError):validate(p)
 def test_audit_failure_never_becomes_recipe(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);bad={'ok':False,'reasons':['incorrect fact'],'scene_checks':[]}
   replies=[(plan(),'test'),(bad,'test')]*3
   with patch('planner.ask',side_effect=replies):
    with self.assertRaises(RuntimeError):generate(root,root,'नमक कानून','इतिहास','Verified source text')
   self.assertFalse((root/'recipe.json').exists())
 def test_model_outage_has_no_old_topic_fallback(self):
  with tempfile.TemporaryDirectory() as tmp:
   with patch('planner.ask',side_effect=RuntimeError('service unavailable')):
    with self.assertRaises(RuntimeError):generate(tmp,tmp,'एक नया विषय','auto','Source text')
   self.assertFalse((Path(tmp)/'recipe.json').exists())
if __name__=='__main__':unittest.main()
