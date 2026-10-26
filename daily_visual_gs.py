"""Daily autonomous visual GS: source bank -> validated script -> art -> clean voice -> MP4."""
import os,json,datetime,hashlib,math,io,subprocess,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageOps,ImageFilter
import auto_poster as e
DAY=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).date().isoformat()
ROOT=Path('experiments/daily_visual_gs')/DAY
ROOT.mkdir(parents=True,exist_ok=True)
W,H,FPS=720,1280,24
COLORS=['#46e6ff','#ffe46b','#ff91ae','#95ffc1']
def save(name,obj): (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
def script():
 p=ROOT/'script.json'
 if p.exists():return json.loads(p.read_text())
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
  prompt='''Create a beautiful 25-40 second Hindi GS concept explainer from ONLY the supplied reference. No invented facts, dates, exam claims, statistics, or current affairs. Return JSON {ok:boolean,title:Hindi <=8 words,scenes:[{label:Hindi <=8 words,speech:Hindi 12-22 words,image:English detailed illustration prompt,kind:one of reveal,compare,process,quiz}]} with exactly 4 scenes. Start with a concrete visual question; explain simply in two steps; end with a recall question and its answer in speech. Each scene visually shows the specific concept, not generic books/students. Use no hmm/uh/humming/filler, no music descriptions. If source is unclear/outdated return ok:false. Reference: '''+json.dumps(q,ensure_ascii=False)
  s=e._groq(prompt) or e._gemini(prompt)
  if not s or not s.get('ok') or len(s.get('scenes',[]))!=4:continue
  if any(not 5<=len(x.get('speech','').split())<=28 or len(x.get('label',''))>65 for x in s['scenes']):continue
  audit=e._groq('Verify script against reference. Return JSON {ok:boolean}. Reject unsupported or incorrect claims. Reference:'+json.dumps(q,ensure_ascii=False)+' Script:'+json.dumps(s,ensure_ascii=False))
  if not audit or audit.get('ok') is not True:continue
  s.update(question_hash=digest,reference=q,subject=subject);save('script.json',s);return s
 raise RuntimeError('No grounded script passed validation')
def build():
 s=script();e.W=W;e.H=H;e.FPS=FPS
 e.USE_GEMINI_TTS=False;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+8%';e.VOICE_PITCH='+0Hz'
 images=[]
 for i,sc in enumerate(s['scenes']):
  p=ROOT/f'art_{i}.jpg'
  if not p.exists():
   b=e.cf_image(sc['image']+', vivid cinematic educational illustration, detailed depth and lighting, vertical composition, no text, no letters, no watermark')
   if not b:raise RuntimeError('Cloudflare image unavailable')
   Image.open(io.BytesIO(b)).convert('RGB').save(p,quality=94)
  images.append(ImageOps.fit(Image.open(p).convert('RGB'),(W,H)))
 vv=e.make_voices([{'segs':[(None,None,x['speech'])]} for x in s['scenes']],rot=0)
 audio=[]
 for v in vv:
  a=e._compress_pauses(v[0],max_pause=.22)
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
  lines=e.wrap_words(txt,e.get_font(size),640)
  for j,line in enumerate(lines):d.text((360,y+j*size*1.35),line,font=e.get_font(size),fill=col,anchor='mm',stroke_width=2,stroke_fill='#081725')
 def frame(fi):
  t=fi/FPS;k=max(i for i,x in enumerate(starts) if x<=t);lt=t-starts[k];q=lt/ds[k]
  zoom=1.03+.10*q;src=images[k].resize((int(W*zoom),int(H*zoom)))
  im=ImageOps.fit(src,(W,H),centering=(.42+.12*q,.5)).convert('RGBA')
  overlay=Image.new('RGBA',(W,H));d=ImageDraw.Draw(overlay)
  for y in range(H):
   opacity=int(180*max(0,1-y/430)+215*max(0,(y-690)/590))
   d.line((0,y,W,y),fill=(3,14,27,opacity))
  im=Image.alpha_composite(im,overlay);d=ImageDraw.Draw(im)
  d.text((36,45),'MINUTE ME GS',font=e.get_font(23),fill=COLORS[0])
  text(d,s['title'],155,48,COLORS[1]);text(d,s['scenes'][k]['label'],850,48,COLORS[k])
  words=s['scenes'][k]['speech'].split();chunks=[' '.join(words[i:i+6]) for i in range(0,len(words),6)]
  idx=min(len(chunks)-1,int(max(0,lt-.1)/max(.1,ds[k]-.35)*len(chunks)))
  text(d,chunks[idx],1040,34,'white')
  if s['scenes'][k].get('kind')=='quiz':
   d.ellipse((314,610,406,702),fill='#102b43',outline=COLORS[1],width=4)
   d.text((360,652),str(max(1,3-int(lt))),font=e.get_font(46),fill=COLORS[1],anchor='mm')
  d.rounded_rectangle((40,1197,680,1204),3,fill='#52697b');d.rounded_rectangle((40,1197,40+640*t/total,1204),3,fill=COLORS[k])
  d.text((360,1240),'AI शिक्षण चित्र • सांकेतिक दृश्य',font=e.get_font(19),fill='#cedce5',anchor='mm')
  return im.convert('RGB')
 out=ROOT/'reel.mp4'
 p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','19','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for fi in range(math.ceil(total*FPS)):p.stdin.write(frame(fi).tobytes())
 p.stdin.close();assert p.wait()==0
 check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=0.15:pix_th=0.10','-f','null','-'],capture_output=True,text=True)
 assert check.returncode==0 and 'black_start:' not in check.stderr,'Decode/black-frame validation failed'
 save('validated.json',{'duration':total,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'voice':'Edge TTS, no music/humming','date':DAY})
 frame(0).save(ROOT/'cover.jpg');return s
if __name__=='__main__':
 import sys
 if '--publish' in sys.argv:
  receipt=ROOT/'published.json'
  if receipt.exists():print(receipt.read_text());raise SystemExit()
  assert (ROOT/'validated.json').exists(),'Build must pass first'
  assert not (ROOT/'publish_started.json').exists(),'Uncertain prior attempt: inspect account before retry'
  s=json.loads((ROOT/'script.json').read_text());out=ROOT/'reel.mp4'
  assert hashlib.sha256(out.read_bytes()).hexdigest()==json.loads((ROOT/'validated.json').read_text())['sha256']
  account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();assert account.get('username','').lower()=='minuteme_gs'
  save('publish_started.json',{'date':DAY});e._with_series=lambda x:x
  caption=s['title']+'\n\n'+' '.join(x['speech'] for x in s['scenes'])+'\n\nAI शिक्षण चित्र सांकेतिक हैं। Concept practice.\n#MinuteMeGS #GS #StudyHindi #SSC #RailwayExam'
  pid=e._upload_once(str(out),caption,0)
  assert pid;save('published.json',{'media_id':pid,'date':DAY})
  obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json();save('published.json',{'media_id':pid,'permalink':obj.get('permalink'),'date':DAY})
 else:build()
