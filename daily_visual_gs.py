"""Daily autonomous visual GS: source bank -> validated script -> art -> clean voice -> MP4."""
import os,json,datetime,hashlib,math,io,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps,ImageFilter
import auto_poster as e
import gs_scene_stage as motion
DAY=os.getenv('GS_TARGET_DATE') or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).date().isoformat()
ROOT=Path('experiments/daily_visual_gs')/DAY
ROOT.mkdir(parents=True,exist_ok=True)
W,H,FPS=720,1280,24
COLORS=['#46e6ff','#ffe46b','#ff91ae','#95ffc1']
def save(name,obj): (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def script():
 p=ROOT/'script.json'
 if p.exists():
  cached=json.loads(p.read_text())
  if cached.get('renderer_version')==motion.VERSION:return cached
  # A different visual contract must be re-authored, never relabelled as upgraded.
 used=set()
 for f in ROOT.parent.glob('*/script.json'):
  used.add(json.loads(f.read_text()).get('question_hash'))
 bank=e.load_bank();eligible=[]
 for q in bank:
  digest=hashlib.sha256(q.get('question','').encode()).hexdigest()
  if digest not in used and q.get('answer') in q.get('options',{}) and len(q.get('explanation',''))>50:eligible.append((digest,q))
 # Rotate across every subject present in the source bank.
 subjects=sorted(set(str(q.get('subject','GS')) for _,q in eligible))
 assert subjects,'Source bank exhausted'
 subject=subjects[datetime.date.fromisoformat(DAY).toordinal()%len(subjects)]
 pool=[x for x in eligible if str(x[1].get('subject','GS'))==subject]
 for digest,q in pool[:15]:
  prompt='''Create a Hindi GS motion explainer ONLY from the reference. Return JSON {ok:boolean,title:Hindi <=8 words,scenes:[{label:Hindi <=7 words,speech:Hindi 12-22 words,animation:{type:rail|sunrise|river|gravity|quantity|timeline|process|inertia|water,phase:question|explain|demonstrate|recall,labels:[2-3 short Hindi labels, each <=26 characters],amounts:[integer,integer],years:[integer,integer]}}]}. Exactly four scenes. Every scene must show the same narrated concept with a matching physical or logical transformation. Concrete question, two explanation steps, recall. Simple conversational Hindi; no humming/filler. Supported scenes have STRICT semantics: rail = jointed railway thermal expansion only, heating makes the gap narrower; sunrise = India IST 82.5 E only with real map and synchronized clocks; river = Narmada westward to Arabian Sea only; gravity = same mass on Earth/Moon with weaker lunar pull only; quantity = compare two counts 1..12, supply unequal amounts grounded in reference, no invented numbers; timeline = 2-3 distinct sorted exact years and matching events; inertia = braking bus, feet stop with floor, upper body continues only; water = evaporation rising and rain falling only; process = animate 2-3 named institutional/causal steps in the order explicitly supported by reference. Do not use process as a generic fallback for a physical concept. Do not select animations for merely related keywords. No invented facts, dates or unverified causal claims. No answer in question/recall labels until reveal. If no mechanism fits, return ok:false. Reference: '''+json.dumps(q,ensure_ascii=False)
  s=e._groq(prompt) or e._gemini(prompt)
  if not s or not s.get('ok') or len(s.get('scenes',[]))!=4:continue
  try:
   for sc in s['scenes']:motion.validate(sc)
  except (AssertionError,TypeError,ValueError,KeyError):continue
  if any(not 5<=len(x.get('speech','').split())<=28 or len(x.get('label',''))>65 for x in s['scenes']):continue
  audit=e._groq('Verify script AND full-scene animation semantics against reference. Rail always heats and narrows its gap; river is ONLY Narmada; sunrise is ONLY India IST; gravity is ONLY Earth/Moon mass; inertia is ONLY bus braking; water is evaporation/rain. Reject any other topic using those renderers. Verify quantities and timeline years exactly. Process labels must describe an actual ordered process, not three unrelated facts. Reject mismatched animations, misleading demonstrations, formal/awkward Hindi, weak generic opening, filler or answer leaks in quiz imagery. Do not merely trust the source explanation if it contains a contradictory date/title. Return JSON {ok:boolean}. Reject unsupported or incorrect claims. Reference:'+json.dumps(q,ensure_ascii=False)+' Script:'+json.dumps(s,ensure_ascii=False))
  if not audit or audit.get('ok') is not True:continue
  s.update(renderer_version=motion.VERSION,question_hash=digest,reference=q,subject=subject);save('script.json',s);return s
 raise RuntimeError('No grounded script passed validation')
def gemini_male_once(lines,rot):
 last='Gemini key unavailable'
 if not e.GEMINI_API_KEY:raise RuntimeError(last)
 for model in ('gemini-2.5-flash-preview-tts','gemini-2.5-pro-preview-tts'):
  for url,body in e._tts_bodies(model,lines,'Charon'):
   try:
    r=e.requests.post(url,params={'key':e.GEMINI_API_KEY},json=body,timeout=60)
    if r.status_code!=200:
     last=f'{model}: HTTP {r.status_code}';continue
    got=e._find_audio(r.json())
    if got:
     arr=e._pcm_to_array(*got)
     if len(arr)>e.SR:return arr,model+' / Charon (male)'
   except e.requests.RequestException:last='Gemini network failure'
 raise RuntimeError(last)

def build():
 s=script();e.W=W;e.H=H;e.FPS=FPS
 e.resolve_font()
 # Reject static stages before paying for voice/encoding. Compare the actual teaching area.
 for sc in s['scenes']:
  motion.validate(sc)
  a=np.asarray(motion.render(sc,.2,4),dtype=np.float32)[300:1050]
  b=np.asarray(motion.render(sc,3.5,4),dtype=np.float32)[300:1050]
  assert np.abs(a-b).mean()>.05,'Static educational stage rejected'

 e.USE_GEMINI_TTS=True;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+8%';e.VOICE_PITCH='+0Hz'
 e.gemini_tts_once=gemini_male_once
 e._TTS_STYLE[0]='Clear conversational Hindi, friendly male teacher. Speech only. No humming, singing, music or filler sounds.'
 vv=e.make_voices([{'segs':[(None,None,x['speech'])]} for x in s['scenes']],rot=0)
 audio=[];word_times=[]
 for v in vv:
  a,remap=e._compress_pauses(v[0],max_pause=.22)
  word_times.append([(remap(a),remap(b),w) for a,b,w in (v[1] or [])])
  if len(a)<e.SR*.6 or np.max(np.abs(a))<.005:raise RuntimeError('Missing real narration')
  audio.append(a)
 ds=[len(a)/e.SR+.35 for a in audio];starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds)
 mix=np.zeros(math.ceil(total*e.SR),dtype=np.float32)
 for i,a in enumerate(audio):e.add_at(mix,a,starts[i]+.1)
 # No music or synthesized humming; narration only.
 with wave.open(str(ROOT/'voice.wav'),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(e.SR);f.writeframes((np.clip(mix,-.98,.98)*32767).astype('<i2').tobytes())
 e.resolve_font()
 def text(d,txt,y,size,col):
  lines=[' '.join(x) for x in e.wrap_words(txt,e.get_font(size),640)]
  for j,line in enumerate(lines):d.text((360,y+j*size*1.35),line,font=e.get_font(size),fill=col,anchor='mm',stroke_width=0)
 def coloured_caption(d,group,active,y):
  words=[w for a,b,w in group];f=e.get_font(32);gap=d.textlength(' ',font=f)
  widths=[d.textlength(w,font=f) for w in words];x=(720-sum(widths)-gap*(len(words)-1))/2
  for j,(w,width) in enumerate(zip(words,widths)):
   if j==active:d.rounded_rectangle((x-5,y-23,x+width+5,y+25),7,fill='#ffd86a')
   d.text((x,y),w,font=f,fill='#a83830' if j==active else '#172f45',anchor='lm');x+=width+gap
 def frame(fi):
  t=fi/FPS;k=max(i for i,x in enumerate(starts) if x<=t);lt=t-starts[k];q=lt/ds[k]
  im=motion.render(s['scenes'][k],lt,ds[k]);d=ImageDraw.Draw(im)
  d.text((36,45),'MINUTE ME GS',font=e.get_font(23),fill='#087f80')
  text(d,s['title'],145,44,'#a83830');text(d,s['scenes'][k]['label'],245,32,'#087f80')
  words=s['scenes'][k]['speech'].split();chunks=[' '.join(words[i:i+6]) for i in range(0,len(words),6)]
  idx=min(len(chunks)-1,int(max(0,lt-.1)/max(.1,ds[k]-.35)*len(chunks)))
  timed=word_times[k]
  if timed:
   wi=max([i for i,(a,b,w) in enumerate(timed) if a<=max(0,lt-.1)] or [0]);group=timed[(wi//5)*5:(wi//5)*5+5]
   line=' '.join(w for a,b,w in group)
   coloured_caption(d,group,wi%5,1140)

  else:
   # Gemini has no word timestamps: phrase highlight only.
   d.rounded_rectangle((35,1108,685,1186),16,fill='#ffe8b3')
   text(d,chunks[idx],1140,32,'#a83830')
  d.rounded_rectangle((40,1197,680,1204),3,fill='#52697b');d.rounded_rectangle((40,1197,40+640*t/total,1204),3,fill=COLORS[k])
  d.text((360,1240),'चलता शिक्षण मॉडल • सांकेतिक',font=e.get_font(19),fill='#53696d',anchor='mm')
  return im.convert('RGB')
 out=ROOT/'reel.mp4'
 p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','19','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for fi in range(math.ceil(total*FPS)):p.stdin.write(frame(fi).tobytes())
 p.stdin.close();assert p.wait()==0
 check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=0.15:pix_th=0.10','-f','null','-'],capture_output=True,text=True)
 assert check.returncode==0 and 'black_start:' not in check.stderr,'Decode/black-frame validation failed'
 save('scene_manifest.json',{'renderer_version':motion.VERSION,'scenes':[x['animation'] for x in s['scenes']],'no_photo_fallback':True})
 save('validated.json',{'duration':total,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'voice':e._CACHE.get('voice_used','unknown'),'date':DAY,'renderer_version':motion.VERSION})
 frame(0).save(ROOT/'cover.jpg');return s
if __name__=='__main__':
 import sys
 if '--publish' in sys.argv:
  hold=ROOT/'publication_hold.json'
  assert not hold.exists(),'Publication held: user rejected this episode; rebuild and review required'
  receipt=ROOT/'published.json'
  if receipt.exists():print(receipt.read_text());raise SystemExit()
  assert (ROOT/'validated.json').exists(),'Build must pass first'
  assert json.loads((ROOT/'validated.json').read_text()).get('renderer_version')==motion.VERSION,'Old photo-only renderer blocked'
  assert not (ROOT/'publish_started.json').exists(),'Uncertain prior attempt: inspect account before retry'
  s=json.loads((ROOT/'script.json').read_text());out=ROOT/'reel.mp4'
  assert hashlib.sha256(out.read_bytes()).hexdigest()==json.loads((ROOT/'validated.json').read_text())['sha256']
  account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();assert account.get('username','').lower()=='minuteme_gs'
  save('publish_started.json',{'date':DAY});e._with_series=lambda x:x
  caption=s['title']+'\n\n'+' '.join(x['speech'] for x in s['scenes'])+'\n\nशिक्षण ऐनिमेशन सांकेतिक है। Concept practice.\n#MinuteMeGS #GS #StudyHindi #SSC #RailwayExam'
  pid=e._upload_once(str(out),caption,0)
  assert pid;save('published.json',{'media_id':pid,'date':DAY})
  obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();save('published.json',{'media_id':pid,'permalink':obj.get('permalink'),'date':DAY})
 else:
  if os.getenv('GS_FORCE_BUILD')=='1' or not (ROOT/'validated.json').exists() or json.loads((ROOT/'validated.json').read_text()).get('renderer_version')!=motion.VERSION:build()
