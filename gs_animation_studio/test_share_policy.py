import copy,unittest
from share_policy import validate_share

def plan():return {'share_reason':'बहुमत की उलझन सुलझाने के लिए पढ़ाई वाले साथी को भेजें','share_card':{'kind':'exam_confusion','recipient':'प्रतियोगी परीक्षा पढ़ने वाला दोस्त','benefit':'बहुमत और सबसे बड़ी पार्टी का अंतर स्पष्ट समझना','cta':'बहुमत में उलझने वाले अपने दोस्त को भेजो'}}
class SharePolicyTests(unittest.TestCase):
 def test_specific_recipient_and_value_pass(self):validate_share(plan())
 def test_missing_share_card_is_rejected(self):
  with self.assertRaises(ValueError):validate_share({'share_reason':'share karo'})
 def test_generic_share_begging_is_rejected(self):
  p=plan();p['share_card']['cta']='इस वीडियो को शेयर करो'
  with self.assertRaises(ValueError):validate_share(p)
 def test_long_cta_is_rejected(self):
  p=plan();p['share_card']['cta']='बहुत '*20
  with self.assertRaises(ValueError):validate_share(p)
 def test_empty_viewer_benefit_is_rejected(self):
  p=plan();p['share_card']['benefit']='वायरल होगा'
  with self.assertRaises(ValueError):validate_share(p)
if __name__=='__main__':unittest.main()

class ShareOverlayTests(unittest.TestCase):
 def test_invitation_only_appears_in_final_two_seconds(self):
  import importlib.util,json,os,shutil,tempfile
  from pathlib import Path
  from unittest.mock import patch
  from PIL import Image
  import numpy as np
  base=Path(__file__).resolve().parent
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);shutil.copy(base/'known_good/Mukta.ttf',root/'Mukta.ttf')
   scene={'heading':'बहुमत कैसे बनता है?','explanation':'एक आसान बात याद रखो','speech':'यह केवल टेस्ट है जिसमें शेयर करने की उपयोगी वजह दिखती है।','objects':[]}
   p=plan();p.update(titles=[['शीर्षक','उदाहरण']]*6,scenes=[scene]*6)
   (root/'recipe.json').write_text(json.dumps(p,ensure_ascii=False));(root/'audio.json').write_text(json.dumps({'seconds':[4]*6}))
   (root/'motion.json').write_text(json.dumps([{'t':0,'scene':0,'pins':{}},{'t':21,'scene':5,'pins':{}},{'t':23,'scene':5,'pins':{}}]))
   with patch.dict(os.environ,{'STUDIO_ROOT':str(root)}):
    spec=importlib.util.spec_from_file_location('share_overlay_test',base/'compose_dynamic.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    images=[np.asarray(m.overlay(Image.new('RGB',(720,1280),(8,25,38)),i))[305:365,36:636] for i in range(3)]
   self.assertTrue(np.array_equal(images[0],images[1]));self.assertGreater(float(np.abs(images[2].astype(float)-images[1]).mean()),1)
