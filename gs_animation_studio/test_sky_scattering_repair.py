"""Regression against the actual 2026-11-02 sky scattering AV failure."""
import unittest
from planner import repair_sky_scattering, normalize_layout, validate_sky_scattering

class SkyScatteringRepairTests(unittest.TestCase):
 def test_air_and_colored_rays_replace_water_village(self):
  roles=('hook','challenge','reveal','explain','transfer','revision')
  p={'scenes':[{'role':r,'setting':'village','objects':[{'kind':'water','action':'flow','label':'पानी'}]} for r in roles]}
  p=repair_sky_scattering(p,'आकाश नीला क्यों दिखाई देता है?')
  p,_=normalize_layout(p)
  validate_sky_scattering(p,'आकाश नीला क्यों दिखाई देता है?')
  self.assertEqual(p['scenes'][0]['setting'],'space')
  self.assertNotIn('नीला',' '.join(o['label'] for o in p['scenes'][0]['objects']))
  for scene in p['scenes'][3:5]:
   self.assertEqual(scene['setting'],'laboratory')
   self.assertFalse(any(o['kind']=='water' for o in scene['objects']))
  blue=next(o for o in p['scenes'][4]['objects'] if 'नीला' in o['label'])
  red=next(o for o in p['scenes'][4]['objects'] if 'लाल' in o['label'])
  self.assertEqual(blue['color'],'#2563eb')
  self.assertEqual(red['color'],'#ef4444')
  self.assertGreater(blue['to'][2],blue['pos'][2])
  self.assertGreater(red['to'][0],red['pos'][0])

 def test_other_topics_unchanged(self):
  p={'scenes':[{'objects':[{'kind':'water'}]}]}
  self.assertIs(repair_sky_scattering(p,'गंगा नदी कहाँ बहती है?'),p)

if __name__=='__main__':unittest.main()
