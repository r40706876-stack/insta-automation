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

class EvidenceSelectionTests(unittest.TestCase):
 def test_incomplete_source_does_not_hide_available_insights(self):
  base=dict(media_id='1',topic='river',format='legacy',source='graph',published_at='2026-10-01T00:00:00Z',observed_at='2026-10-02T00:00:00Z')
  incomplete=normalize(base)
  complete=normalize(dict(base,source='metricool',observed_at='2026-10-02T00:10:00Z',views=1000,shares=3,saves=8))
  self.assertEqual(cohort([incomplete,complete])[0:] , [])
  self.assertEqual(cohort([incomplete,complete],'24h')[0]['shares_per_1000'],3)
 def test_measured_cohort_changes_priority(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.json'
   rows=[dict(media_id=str(i),topic='river',subject='Geography',format='exam_trap',source='test',published_at='2026-10-01T00:00:00Z',observed_at='2026-10-04T00:00:00Z',views=1000,shares=5,saves=10) for i in range(3)]
   ingest(rows[:2],p);self.assertEqual(evidence_score({'subject':'Geography','topic_key':'river'},p),0)
   ingest(rows,p);self.assertGreater(evidence_score({'subject':'Geography','topic_key':'river'},p),0)


class ProviderModelTests(unittest.TestCase):
 def test_retired_models_are_filtered(self):
  from unittest.mock import patch,Mock
  from gs_model_config import gemini_models
  gemini_models.cache_clear()
  response=Mock(status_code=200)
  response.json.return_value={'models':[{'name':'models/gemini-3.8-flash','supportedGenerationMethods':['generateContent']}]}
  with patch.dict('os.environ',{'GEMINI_API_KEY':'test-only'}),patch('gs_model_config.requests.get',return_value=response):
   self.assertEqual(gemini_models(),['gemini-3.8-flash'])
  gemini_models.cache_clear()

class RevisionBoundaryTests(ReleaseTests):
 def six(self,root):
  s=self.fixture(root);s['scenes']=[{'speech':'test','role':role,'label':'पुनरावृत्ति','teaches':'revision' if role=='revision' else 'causal fact','revision_card':role=='revision'} for role in ('hook','challenge','reveal','explain','transfer','revision')]
  checks=json.loads((root/'file_checks.json').read_text());checks['actual_rendered_motion_checks']={'scene_'+str(i)+'_teaching_motion':{'changed_fraction':.03} for i in range(1,6)};checks['static_revision_checks']={'scene_6':{'bounded_revision_card':True,'seconds':4}}
  (root/'file_checks.json').write_text(json.dumps(checks));(root/'audio.json').write_text(json.dumps({'speech':['test']*6,'seconds':[3]*5+[4]}));return s
 def test_short_final_revision_can_be_still(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s=self.six(root);self.assertTrue(evaluate_release(root,s)['safe_to_publish'])
 def test_long_revision_is_blocked(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s=self.six(root);audio=json.loads((root/'audio.json').read_text());audio['seconds'][-1]=8;(root/'audio.json').write_text(json.dumps(audio));self.assertFalse(evaluate_release(root,s)['safe_to_publish'])
 def test_teaching_scene_cannot_claim_revision_exception(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);s=self.six(root);s['scenes'][0]['revision_card']=True;s['scenes'][0]['role']='revision';checks=json.loads((root/'file_checks.json').read_text());checks['actual_rendered_motion_checks'].pop('scene_1_teaching_motion');(root/'file_checks.json').write_text(json.dumps(checks));self.assertFalse(evaluate_release(root,s)['safe_to_publish'])


class GroundedNarrationTests(unittest.TestCase):
 def test_visual_planner_receives_source_only_narration(self):
  from gs_storyboard import grounded_storyboard
  q={'question':'नर्मदा किस दिशा में बहती है?','options':{'a':'पश्चिम','b':'पूर्व'},'answer':'a','explanation':'नर्मदा का उद्गम अमरकंटक है। इसका प्रवाह पश्चिम की ओर है।'}
  lines=grounded_storyboard(q)
  self.assertEqual(lines[3]['speech'],'नर्मदा का उद्गम अमरकंटक है।')
  self.assertEqual(lines[4]['speech'],'इसका प्रवाह पश्चिम की ओर है।')
  self.assertLessEqual(len(lines[-1]['speech'].split()),6)
 def test_internal_topic_tag_is_not_narrated(self):
  from gs_storyboard import grounded_storyboard
  q={'question':'rainshadow-first-trial: बारिश अलग क्यों?','options':{'a':'नम हवा'},'answer':'a','explanation':'नम हवा ऊपर उठकर ठंडी होती है।'}
  self.assertNotIn('first-trial',grounded_storyboard(q)[0]['speech'])
