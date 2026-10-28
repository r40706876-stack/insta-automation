"""New-topic runs use the same recovery and strict export gates as reviewed lessons."""
import hashlib,json,os,shutil,sys
from recovery import Recovery,StageError
class DynamicRecovery(Recovery):
 def __init__(self,*args,**kwargs):
  super().__init__('new_topic',*args,**kwargs)
  self.snapshot={n:(self.base/n).read_bytes() for n in ('scene_dynamic.py','scene_india_drift.py','compose_dynamic.py','scene_dandi.py','dandi_map.json','dandi_map.LICENSE','rich_assets.py','world_land.json','world_land.LICENSE')}
 def prepare_inputs(self):
  self.root.mkdir(parents=True,exist_ok=True)
  if (self.root/'final.mp4').exists():raise StageError('inputs','stale_export')
  shutil.copy(self.known('Mukta.ttf'),self.root/'Mukta.ttf')
  reviewed=os.getenv('STUDIO_REVIEWED_RECIPE','')
  if reviewed:
   import re
   from planner import validate,check_quantities
   if not re.fullmatch(r'[a-z0-9_]+',reviewed):raise StageError('inputs','invalid_reviewed_recipe')
   src=self.base/'reviewed'/(reviewed+'.json');raw=src.read_bytes()
   if hashlib.sha256(raw).hexdigest()!=os.getenv('STUDIO_REVIEWED_SHA256'):raise StageError('inputs','reviewed_recipe_hash_mismatch')
   recipe=json.loads(raw);validate(recipe)
   check_quantities(recipe,[{'text':recipe['reference_text']}])
   (self.root/'recipe.json').write_bytes(raw)
   (self.root/'sources.json').write_text(json.dumps(recipe['sources'],ensure_ascii=False,indent=2))
   self.note('reviewed_recipe','passed',recipe=reviewed,sha256=hashlib.sha256(raw).hexdigest())
  else:self.call('plan_new_topic',[sys.executable,str(self.base/'planner.py'),str(self.root),str(self.repo)],timeout=720)
  self.recipe=json.loads((self.root/'recipe.json').read_text());self.plan_digest=hashlib.sha256((self.root/'recipe.json').read_bytes()).hexdigest()
  if any(o['kind'] in ('map','planet') for sc in self.recipe['scenes'] for o in sc['objects']):
   source=self.root/'sources.json';items=json.loads(source.read_text());items.append({'url':'https://www.naturalearthdata.com/downloads/110m-physical-vectors/110m-land/','publisher':'Natural Earth, public-domain physical coastline geometry','note':'Modern Gujarat outline is separately attributed in dandi_map.LICENSE; routes are schematic.'});source.write_text(json.dumps(items,ensure_ascii=False,indent=2))
  self.restore_renderer();self.note('inputs','passed',requested_topic=self.recipe['requested_topic'])
 def compatible_snapshot(self):
  if hashlib.sha256((self.root/'recipe.json').read_bytes()).hexdigest()!=self.plan_digest:raise StageError('snapshot','lesson_mismatch')
 def restore_renderer(self):
  self.compatible_snapshot()
  renderer='scene_india_drift.py' if self.recipe.get('renderer')=='india_drift_v1' else 'scene_dandi.py' if self.recipe.get('renderer')=='dandi_coast_v3' else 'scene_dynamic.py'
  for name in ('dandi_map.json','dandi_map.LICENSE','rich_assets.py','world_land.json','world_land.LICENSE'):(self.root/name).write_bytes(self.snapshot[name])
  for src,dst in [(renderer,'scene.py'),('compose_dynamic.py','compose.py')]:(self.root/dst).write_bytes(self.snapshot[src])
  self.repair('restore_reviewed_renderer',engine='data-driven-3d',same_recipe=True)
 def restore_voice(self):
  raise StageError('voice','new_topic_has_no_matching_cached_narration','Voice providers failed; an unrelated older narration is never substituted')
