import json
import tempfile
import unittest
from pathlib import Path
from gs_learning import normalize,ingest,cohort,report,evidence_score,experiment
from gs_release import evaluate_release
class LearningTests(unittest.TestCase):
 def row(self,**extra):
  return dict(media_id='1',topic='river',subject='Geography',format='exam_trap',source='verified export',published_at='2026-10-01T00:00:00Z',observed_at='2026-10-02T00:00:00Z',views=1000,shares=3,saves=8,**extra)
 def test_missing_is_not_zero_or_retention(self):
  r=normalize(self.row(three_second_rate=72));self.assertIsNone(r['retention']);self.assertIsNone(r['net_followers']);self.assertEqual(r['shares_per_1000'],3)
 def test_age_windows_and_dedup(self):
  r=self.row();r['observed_at']='2026-10-08T00:00:00Z'
  self.assertEqual(normalize(r)['window'],'7d');self.assertFalse(cohort([normalize(r)],'24h'))
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.json';ingest([self.row(),self.row()],p);self.assertEqual(len(json.loads(p.read_text())),1)
 def test_invalid_observation(self):
  for key,value in [('views',-1),('three_second_rate',120),('views',float('nan')),('observed_at','2026-09-30T00:00:00Z')]:
   r=self.row();r[key]=value
   with self.assertRaises(ValueError):normalize(r)
 def test_small_sample_never_scales(self):
  r=report([normalize(self.row())])['windows']['24h'][0]
  self.assertFalse(r['automatic_scale']);self.assertEqual(r['decision'],'collect_more')
 def test_missing_review_blocks(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertFalse(evaluate_release(t,{'scenes':[{'speech':'test'}]})['safe_to_publish'])
 def test_balanced_rotation(self):
  self.assertEqual(len({experiment('2026-11-0'+str(d),'Geography') for d in (1,2,3)}),3)
if __name__=='__main__':unittest.main()

class ReleaseTests(unittest.TestCase):
 def fixture(self,root):
  import hashlib
  from gs_release import REVIEW_CHECKS
  (root/'reel.mp4').write_bytes(b'test-video')
  digest=hashlib.sha256(b'test-video').hexdigest()
  script={'scenes':[{'speech':'test'}]}
  data={'sha256':digest,'decoded_without_errors':True,'black_intervals':0,'dimensions':[720,1280],'audio_mean_db':-18,'actual_rendered_motion_checks':{'scene_1':{'changed_fraction':.03}}}
  (root/'file_checks.json').write_text(json.dumps(data))
  (root/'audio.json').write_text(json.dumps({'seconds':[3],'speech':['test']}))
  review=dict(sha256=digest,reviewer='test fixture only',reviewed_at='2026-11-01T00:00:00Z',**{k:True for k in REVIEW_CHECKS})
  (root/'release_review.json').write_text(json.dumps(review))
  return script
 def test_review_bound_to_video_hash(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s=self.fixture(root);self.assertTrue(evaluate_release(root,s)['safe_to_publish'])
   (root/'reel.mp4').write_bytes(b'changed');self.assertFalse(evaluate_release(root,s)['safe_to_publish'])
 def test_audio_mismatch_blocks(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s=self.fixture(root);s['scenes'][0]['speech']='other';self.assertFalse(evaluate_release(root,s)['safe_to_publish'])
