import copy,unittest
from quality_smoke import test_plan
from planner import validate
from visual_contract import validate_visual
class MotionReadabilityTests(unittest.TestCase):
 def test_new_geology_assets_are_valid(self):
  p=test_plan();validate(p);validate_visual(p)
  self.assertEqual(p['scenes'][2]['objects'][0]['kind'],'rock_layers')
 def test_cause_can_precede_effect(self):
  p=test_plan();p['scenes'][2]['objects'][0]['animation_window']=[.4,1];validate_visual(p)
 def test_too_fast_or_invalid_window_is_rejected(self):
  for window in ([.8,1],[1,0],[float('nan'),1],[False,1],[0,2]):
   p=test_plan();p['scenes'][2]['objects'][0]['animation_window']=window
   with self.assertRaises(ValueError):validate_visual(p)
 def test_fake_country_box_is_rejected(self):
  p=test_plan();p['scenes'][0]['objects'][0].update(kind='box',id='india_land',gesture='',label='भारत')
  with self.assertRaises(ValueError):validate_visual(p)
 def test_compression_cannot_be_assigned_to_unimplemented_model(self):
  p=test_plan();p['scenes'][2]['objects'][0]['kind']='mountain'
  with self.assertRaises(ValueError):validate_visual(p)
 def test_unknown_camera_is_rejected(self):
  p=test_plan();p['scenes'][0]['camera_view']='random_spin'
  with self.assertRaises(ValueError):validate_visual(p)
