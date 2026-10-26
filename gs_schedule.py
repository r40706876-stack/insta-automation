"""Persistent schedule checks; no secret values in logs or receipts."""
import os,json,time,datetime,hashlib
from pathlib import Path
UTC=datetime.timezone.utc
class Slot:
 def __init__(self,video):
  raw=os.getenv('GS_TARGET_UTC','')
  self.enabled=bool(raw);self.cached=None
  if not raw:return
  self.target=datetime.datetime.fromisoformat(raw.replace('Z','+00:00'))
  if self.target.tzinfo is None:raise RuntimeError('Explicit UTC target required')
  now=datetime.datetime.now(UTC)
  if (self.target-now).total_seconds()>7200:raise RuntimeError('Target too far ahead')
  if (now-self.target).total_seconds()>900:raise RuntimeError('Slot over 15 minutes late; do not bunch posts')
  ist=self.target.astimezone(datetime.timezone(datetime.timedelta(hours=5,minutes=30)))
  self.path=Path('experiments/regular_schedule')/(ist.strftime('%Y-%m-%d_%H%M')+'.json')
  self.path.parent.mkdir(parents=True,exist_ok=True)
  digest=hashlib.sha256(Path(video).read_bytes()).hexdigest()
  self.data=json.loads(self.path.read_text()) if self.path.exists() else {'target_utc':raw,'source_sha256':digest}
  if self.data.get('media_id'):self.cached=self.data['media_id'];return
  if self.data.get('publish_started_utc'):raise RuntimeError('Publication uncertain: check Instagram before retry')
  if self.data['source_sha256']!=digest:raise RuntimeError('Different video for the same slot blocked')
  self.data['prepared_utc']=now.isoformat();self.save()
  print('SCHEDULE: video ready; target',raw,flush=True)
 def save(self):self.path.write_text(json.dumps(self.data,indent=2))
 def before_publish(self):
  if not self.enabled:return
  warned=False
  while True:
   left=(self.target-datetime.datetime.now(UTC)).total_seconds()
   if left<=0:break
   if left<=600 and not warned:
    print('REMINDER: reel ready, publication due within 10 minutes:',self.data['target_utc'],flush=True);warned=True
   time.sleep(min(30,left))
  if (datetime.datetime.now(UTC)-self.target).total_seconds()>900:raise RuntimeError('Slot expired during processing')
  self.data['publish_started_utc']=datetime.datetime.now(UTC).isoformat();self.save()
 def complete(self,pid):
  if self.enabled:
   self.data.update(media_id=pid,published_utc=datetime.datetime.now(UTC).isoformat());self.save()
