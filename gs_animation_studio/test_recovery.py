import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from recovery import Recovery,StageError,gitsha
BASE=Path(__file__).parent
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name)
  self.env=patch.dict(os.environ,{'GITHUB_RUN_ID':'12345','STUDIO_DIAGNOSTICS':str(self.repo/'diagnosis')});self.env.start()
  self.r=Recovery('dam_pressure',repo=self.repo,base=BASE);self.r.root.mkdir(parents=True)
 def tearDown(self):self.env.stop();self.tmp.cleanup()
 def test_snapshot_integrity(self):
  for name in self.r.manifest['files']:self.r.known(name.removeprefix('known_good/'))
 def test_corrupt_snapshot_refused(self):
  self.r.manifest['files']['known_good/dam_pressure/scene.py']='bad'
  with self.assertRaises(StageError):self.r.known('dam_pressure/scene.py')
 def test_changed_lesson_never_silently_replaced(self):
  recipe=json.loads(self.r.known('dam_pressure/recipe.json').read_text());recipe['speech'][0]='Different requested lesson'
  (self.r.root/'recipe.json').write_text(json.dumps(recipe));self.r.recipe=recipe
  with self.assertRaises(StageError):self.r.restore_renderer()
 def test_reviewed_code_recovers_staged_syntax_error(self):
  (self.r.root/'recipe.json').write_bytes(self.r.known('dam_pressure/recipe.json').read_bytes());self.r.recipe={}
  (self.r.root/'scene.py').write_text('invalid !!!')
  with self.assertRaises(StageError):self.r.compile(self.r.root/'scene.py')
  self.r.restore_renderer();self.r.compile(self.r.root/'scene.py')
 def test_timeout_is_bounded_and_reported(self):
  with self.assertRaises(StageError):self.r.call('timeout_test',[sys.executable,'-c','import time;time.sleep(60)'],timeout=.1)
  self.assertEqual(self.r.report['events'][-1]['code'],'timeout')
 def test_failed_export_is_quarantined(self):
  (self.r.root/'final.mp4').write_bytes(b'bad')
  with patch.object(self.r,'prepare_inputs',side_effect=RuntimeError('unresolved')):self.assertFalse(self.r.run())
  self.assertFalse((self.r.root/'final.mp4').exists());self.assertEqual(self.r.report['status'],'failed')
 def test_exact_offline_voice_decodes(self):
  self.r.recipe=json.loads(self.r.known('dam_pressure/recipe.json').read_text());self.r.restore_voice()
  self.assertGreater((self.r.root/'voice.wav').stat().st_size,10000)
if __name__=='__main__':unittest.main()
