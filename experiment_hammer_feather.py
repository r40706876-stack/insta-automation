"""One original science trial: modelled hammer/feather motion with and without air."""
import os,json,math,wave,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path('experiments/hammer_feather_20261027');ROOT.mkdir(parents=True,exist_ok=True)
os.environ['GS_VISUAL_OUTPUT']=str(ROOT)
import auto_poster as e
import daily_visual_gs as voices
e.resolve_font()
W,H,FPS=720,1280,30
CYAN='#49e4ff';GOLD='#ffe180';WHITE='#f2f8ff';RED='#ff987a'
def text(d,s,x,y,n=34,col=WHITE):
 while d.textlength(s,font=e.get_font(n))>620:n-=1
 d.text((x,y),s,font=e.get_font(n),fill=col,anchor='mm')
def ease(q):q=max(0,min(1,q));return q*q*(3-2*q)
def bg(t):
 yy,xx=np.mgrid[0:H,0:W];v=np.exp(-((xx-360)/500)**2-((yy-700)/650)**2)
 a=np.zeros((H,W,3),np.uint8)
 for k,(b,g) in enumerate(((5,7),(16,28),(32,37))):a[:,:,k]=b+g*v
 im=Image.fromarray(a);d=ImageDraw.Draw(im)
 for j in range(12):
  y=430+j*53;d.line((35,y,685,y),fill='#18364c',width=1)
 return im

def hammer(im,x,y,scale=1):
 d=ImageDraw.Draw(im);s=scale
 # Shaded steel head, bevel, wood handle and grip.
 d.rounded_rectangle((x-9*s,y-9*s,x+9*s,y+70*s),5*s,fill='#b47f50',outline='#efd2a4',width=2)
 for i in range(6):d.line((x-7*s,y+(28+i*6)*s,x+7*s,y+(25+i*6)*s),fill='#725038',width=2)
 d.polygon([(x-37*s,y-25*s),(x+27*s,y-25*s),(x+37*s,y-15*s),(x-27*s,y-15*s)],fill='#f0f7fc')
 d.polygon([(x+27*s,y-25*s),(x+37*s,y-15*s),(x+37*s,y+17*s),(x+27*s,y+7*s)],fill='#6b8b9e')
 d.rectangle((x-37*s,y-15*s,x+27*s,y+17*s),fill='#a4becb',outline='#e9f6ff',width=2)
 d.line((x-28*s,y-8*s,x+20*s,y-8*s),fill='white',width=2)

def feather(im,x,y,t,scale=1,flutter=False):
 # Curved vane made from 34 individually drawn barbs; central shaft remains legible.
 d=ImageDraw.Draw(im);s=scale
 sway=7*math.sin(t*4) if flutter else 0
 def pos(q):return x+sway+14*s*math.sin(q*math.pi),y+(-36+100*q)*s
 for j in range(35):
  q=j/35;cx,cy=pos(q);wid=25*s*math.sin(q*math.pi)**.65
  d.line((cx-wid,cy-15*s,cx,cy+3*s),fill='#e5f7ff',width=3)
  d.line((cx,cy+3*s,cx+wid*.8,cy-12*s),fill='#83d1ec',width=3)
 d.line([pos(q) for q in np.linspace(0,1,24)],fill='#ffffff',width=3)
 d.line((pos(1)[0],pos(1)[1],x+sway,y+82*s),fill='#fff2ca',width=3)

def tube(im,x,t,air=True,drain=0):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 d.rounded_rectangle((x-125,438,x+125,1030),45,fill=(25,91,119,45),outline=(117,220,249,175),width=3)
 for i in range(12):d.line((x-119+i,485,x-119+i,973),fill=(182,242,255,int(45*(1-i/12))),width=1)
 d.ellipse((x-125,420,x+125,476),fill=(19,54,72,255),outline=(154,227,250,220),width=3)
 d.ellipse((x-125,999,x+125,1055),fill=(14,41,57,255),outline=(129,205,230,200),width=3)
 d.line((x-90,970,x+90,970),fill=(228,229,215,240),width=5)
 if air:
  for j in range(22):
   xx=x-90+(j*47+t*10)%180;yy=495+(j*71+t*28)%455
   if j/22>=drain:d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=(80,210,255,150))
 im.paste(layer,(0,0),layer)

def glow(im,pts,col=CYAN,width=5):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);d.line(pts,fill=col,width=width*4)
 layer=layer.filter(ImageFilter.GaussianBlur(10));im.paste(layer,(0,0),layer)
 ImageDraw.Draw(im).line(pts,fill=col,width=width)

lines=['हथौड़ा या पंख? हवा हटा दें, तो पहले कौन गिरेगा? जवाब सोचो।',
 'हवा में पंख धीरे गिरता है। हवा उसे ज्यादा रोकती है।',
 'अब इस बर्तन से हवा निकाल दी। दोनों को एक ही ऊँचाई से साथ छोड़ते हैं।',
 'दोनों साथ पहुँचते हैं! हवा का विरोध न हो, तो दोनों समान तेजी से गिरते हैं। दोस्त से भी पहले अनुमान पूछो।']
titles=['हवा हटे तो पहले कौन गिरेगा?','हवा पंख को ज्यादा रोकती है','अब हवा निकालकर देखो','हवा नहीं: दोनों साथ!']
e.USE_GEMINI_TTS=True;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+0%';e.VOICE_PITCH='+0Hz'
e.gemini_tts_once=voices.gemini_male_once
e._TTS_STYLE[0]='Clear unhurried conversational Hindi male documentary teacher. Keep the question energetic and the explanation clear. Speech only, no humming, singing, music or filler.'
cached=json.loads((ROOT/'review.json').read_text()) if (ROOT/'review.json').exists() else {}
if cached.get('speech')==lines and cached.get('voice_strategy')=='per_scene_charon_v1' and (ROOT/'voice.wav').exists():
 ds=cached['scene_seconds'];e._CACHE['voice_used']=cached.get('voice')
else:
 try:
  vv=[];labels=[]
  for speech in lines:
   arr,label=voices.gemini_male_once([speech],0)
   vv.append((arr,None,speech,None));labels.append(label)
  e._CACHE['voice_used']='Gemini Charon (male), separately generated scenes: '+', '.join(sorted(set(labels)))
 except Exception as exc:
  print('Gemini per-scene voice unavailable:',str(exc)[:160])
  e.USE_GEMINI_TTS=False
  vv=e.make_voices([{'segs':[(None,None,s)]} for s in lines],rot=0)
 audio=[e._compress_pauses(v[0],max_pause=.25)[0] for v in vv]
 assert all(len(a)>e.SR*.5 and np.max(np.abs(a))>.005 for a in audio)
 ds=[max(len(a)/e.SR+.55,m) for a,m in zip(audio,(4.5,6,6,5))]
 starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds);mix=np.zeros(math.ceil(total*e.SR),np.float32)
 for i,a in enumerate(audio):e.add_at(mix,a,starts[i]+.15)
 with wave.open(str(ROOT/'voice.wav'),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(e.SR);w.writeframes((np.clip(mix,-.98,.98)*32767).astype('<i2').tobytes())
starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds)

def brand(im):
 d=ImageDraw.Draw(im);text(d,'MINUTE ME GS • विज्ञान प्रयोग',215,62,23,CYAN)
 d.rounded_rectangle((45,125,645,217),14,fill='#102b3e',outline=CYAN,width=2)
 text(d,'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',345,151,25,WHITE)
 text(d,'WhatsApp: +91 89892 79637',345,190,31,GOLD)
def frame(k,t):
 im=bg(t);d=ImageDraw.Draw(im)
 if k==0:
  # Close-up rotating light and gentle object drift, then a visible prediction timer.
  hammer(im,220,670+10*math.sin(t*1.5),1.6)
  feather(im,500,670-10*math.sin(t*1.5),t,1.6)
  text(d,'हथौड़ा',220,866,35,GOLD);text(d,'पंख',500,866,35,CYAN)
  text(d,'पहले अपना जवाब चुनो',360,990,39,WHITE)
  for j in range(3):
   x=290+j*70;r=11;d.ellipse((x-r,1060-r,x+r,1060+r),fill=GOLD if t>j*.8 else '#264758')
 elif k==1:
  tube(im,360,t,True)
  # Deliberately slow teaching model, not measured physical fall times.
  q=max(0,t-.6);h=min(1,(q/1.4)**2);f=min(1,q/5.1)
  hammer(im,285,535+361.5*h,1.05);feather(im,435,522.4+361.5*f,t,1.05,True)
  d=ImageDraw.Draw(im);text(d,'हवा मौजूद है',360,384,33,CYAN)
  if .9<t<4.5:
   for x in (400,430):
    y=535+365*f;d.line((x,y+70,x,y+25),fill=RED,width=4);d.polygon([(x,y+15),(x-7,y+30),(x+7,y+30)],fill=RED)
  text(d,'पंख को हवा का ज्यादा विरोध',360,1120,33,RED)
 elif k==2:
  q=ease(t/3);tube(im,360,t,True,q)
  hammer(im,285,535,1.05);feather(im,435,522.4,t,1.05)
  d=ImageDraw.Draw(im);text(d,'हवा निकाल रहे हैं',360,384,33,GOLD)
  # Vacuum pump, exhaust path, visibly falling gauge and escaping particles.
  d.rounded_rectangle((510,880,650,1020),18,fill='#254454',outline=CYAN,width=2)
  text(d,'पंप',580,960,24,CYAN)
  path=[(485,935),(510,935),(510,850),(580,850)]
  glow(im,path,CYAN,3);d=ImageDraw.Draw(im)
  for j in range(12):
   a=(t*.6+j/12)%1;xx=485+130*a;yy=935-100*math.sin(a*math.pi)
   if q<1:d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=CYAN)
  d.arc((120,1060,280,1190),180,360,fill='#47768a',width=8)
  a=math.pi+math.pi*(1-q);cx,cy=200,1125
  d.line((cx,cy,cx+60*math.cos(a),cy+60*math.sin(a)),fill=GOLD,width=5)
  text(d,'कम हवा',380,1135,30,CYAN)
 else:
  tube(im,360,t,False);replay=t>=4.4;local=t-4.4 if replay else t;q=max(0,local-.75);f=min(1,(q/1.7)**2)
  yy=535+361.5*f
  hammer(im,285,yy,1.05);feather(im,435,yy-12.6,t,1.05)
  d=ImageDraw.Draw(im);text(d,'हवा नहीं है • एक साथ छोड़ा',360,384,31,CYAN)
  d.line((245,yy-44,470,yy-44),fill=GOLD,width=2)
  if replay:text(d,'एक बार फिर देखो',360,1060,27,CYAN)
  if f>=1:
   for x in (285,435):
    r=8+35*min(1,max(0,q-1.7));d.ellipse((x-r,970-r,x+r,970+r),outline=GOLD,width=3)
   text(d,'दोनों एक साथ पहुँचे',360,1100,37,GOLD)
  else:text(d,'एक ऊँचाई • एक साथ शुरुआत',360,1100,29,WHITE)
  text(d,'दोस्त से पूछो: तुम्हारा अनुमान क्या था?',360,1160,28,CYAN)
 brand(im);d=ImageDraw.Draw(im)
 text(d,titles[k],360,294,49,GOLD if k<3 else CYAN)
 text(d,'शिक्षण मॉडल • आकार और समय सांकेतिक',360,1210,18,'#a8bfcb')
 for j in range(4):
  x=44+j*163;d.rounded_rectangle((x,1240,x+146,1246),3,fill='#28485e')
  if j<=k:d.rounded_rectangle((x,1240,x+146*(min(1,t/ds[k]) if j==k else 1),1246),3,fill=GOLD)
 return im
# The actual teaching area must change over time, not only a progress bar.
for k in range(4):
 a=np.asarray(frame(k,.5),float)[350:1180];b=np.asarray(frame(k,min(ds[k]-.1,3.5)),float)[350:1180]
 assert np.abs(a-b).mean()>.05,'Static teaching area'
out=ROOT/'preview_notes_safe_v2.mp4'
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
for fi in range(math.ceil(total*FPS)):
 tt=fi/FPS;k=max(i for i,s in enumerate(starts) if s<=tt);proc.stdin.write(frame(k,tt-starts[k]).tobytes())
proc.stdin.close();assert proc.wait()==0
check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=.15:pix_th=.1','-f','null','-'],capture_output=True,text=True)
assert check.returncode==0 and 'black_start:' not in check.stderr
sheet=Image.new('RGB',(1440,2560))
for k in range(4):sheet.paste(frame(k,ds[k]*.6),((k%2)*720,(k//2)*1280))
sheet.thumbnail((1000,1800));sheet.save(ROOT/'review_sheet.jpg',quality=92)
review={'voice_strategy':'per_scene_charon_v1','duration':total,'scene_seconds':ds,'voice':e._CACHE.get('voice_used'),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'speech':lines,'build_only':True,'sources':['https://science.nasa.gov/resource/the-apollo-15-hammer-feather-drop/'],'visuals':['bevelled steel and wood hammer','curved feather barbs','translucent glass chamber','air resistance arrows','animated vacuum pump and gauge','synchronised accelerating drops'],'share_hypothesis':'Ask a friend to predict before revealing the vacuum result. Not a claim of measured audience performance.','model_note':'Same height, simultaneous release, negligible air resistance. Distances and durations schematic.'}
(ROOT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2));print(json.dumps(review,ensure_ascii=False))
