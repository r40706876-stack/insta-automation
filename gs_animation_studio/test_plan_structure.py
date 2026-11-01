import unittest
from planner import normalize_layout,validate
from test_topics import plan
class TechnicalIDTests(unittest.TestCase):
 def test_invalid_technical_id_does_not_change_lesson(self):
  source=plan();source['scenes'][0]['objects'][0]['id']='person-1'
  fixed,_=normalize_layout(source);validate(fixed)
  self.assertEqual(fixed['scenes'][0]['speech'],source['scenes'][0]['speech'])
  self.assertNotEqual(fixed['scenes'][0]['objects'][0]['id'],'person-1')
 def test_ambiguous_interaction_target_is_not_guessed(self):
  source=plan();source['scenes'][0]['objects'][1]['id']='person';source['scenes'][0]['objects'][0]['interact_with']='person'
  with self.assertRaises(ValueError):normalize_layout(source)
