"""Cinematic coastal breeze proof: shaded globe, large layered coast, no cartoons."""
import os,json,math,hashlib,subprocess,io,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps,ImageFont
ROOT=Path('experiments/cinematic_seabreeze_v4');ROOT.mkdir(parents=True,exist_ok=True)
os.environ['GS_VISUAL_OUTPUT']=str(ROOT)
import auto_poster as e
e.resolve_font()
import daily_visual_gs as voice_engine
import polished_gs as p
CYAN='#42e8ff';GOLD='#ffe567';WHITE='#f6fbff';RED='#ff9472'
FPS=24;W,H=720,1280
def txt(d,s,x,y,n=38,col=WHITE):
 size=n
 while d.textlength(s,font=e.get_font(size))>650:size-=1
 d.text((x,y),s,font=e.get_font(size),fill=col,anchor='mm',stroke_width=0)
def pill(d,s,x,y,col=CYAN,n=28):
 font=e.get_font(n);width=d.textlength(s,font=font)+38
 d.rounded_rectangle((x-width/2,y-26,x+width/2,y+26),16,fill='#0b263c',outline=col,width=2)
 txt(d,s,x,y,n,col)
# Reuse the shaded, geometrically projected globe from the user's reference.
def earth(im,t):
 size=640;cx,cy=360,740;lon0=57+18*p.c.ease(t/5)
 u=((p.LON+math.radians(lon0)+math.pi)/(2*math.pi)*1440).astype(int)%1440
 v=np.clip(((math.pi/2-p.LAT)/math.pi*720).astype(int),0,719)
 rgb=(p.T[v,u]*p.light[:,:,None]).astype(np.uint8)
 globe=Image.fromarray(np.dstack([rgb,p.mask.astype(np.uint8)*255])).resize((size,size),Image.Resampling.LANCZOS)
 halo=Image.new('RGBA',(720,1280));hd=ImageDraw.Draw(halo)
 hd.ellipse((cx-325,cy-325,cx+325,cy+325),outline=(40,208,255,170),width=17)
 halo=halo.filter(ImageFilter.GaussianBlur(15));im.paste(halo,(0,0),halo)
 im.paste(globe,(40,cy-size//2),globe)
 def loc(lon,lat):
  a=math.radians(lon-lon0);b=math.radians(lat)
  return(cx+size/2*math.cos(b)*math.sin(a),cy-size/2*math.sin(b))
 x,y=loc(72.8,19.1);d=ImageDraw.Draw(im)
 rr=15+7*math.sin(t*3);d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=GOLD,width=3)
 d.ellipse((x-5,y-5,x+5,y+5),fill=GOLD)
 pill(d,'भारत का पश्चिमी तट',360,1080,GOLD,30)
 pts=[loc(lon,18.8) for lon in np.linspace(64.5,71.2,35)]
 p.c.flowing(d,pts,t,CYAN,5)
 pill(d,'दिन में समुद्र से आने वाली हवा',360,385,CYAN,27)
def coastal(im,t,warm=False,cold=False):
 d=ImageDraw.Draw(im)
 # Deep sky, remote coast and foreground cliff have separate lit planes.
 for y in range(380,1090):
  q=(y-380)/710
  d.line((0,y,720,y),fill=(int(16+26*q),int(49+58*q),int(78+55*q)))
 d.ellipse((569,400,632,463),fill='#ffe7a2')
 for j,(base,col) in enumerate(((675,'#456d79'),(710,'#65848a'))):
  points=[(390,1100),(390,base)]+[(x,base-35*math.sin(x*.02+j)-20*math.sin(x*.041)) for x in range(390,721,6)]+[(720,1100)]
  d.polygon(points,fill=col)
 # Ocean depth is a visible volume, not a flat blue rectangle.
 for y in range(730,1090):
  q=(y-730)/360
  d.line((0,y,450,y),fill=(7,int(105-67*q),int(152-70*q)))
 for j in range(32):
  yy=742+j*10;xx=(j*83+t*(13+j*.3))%450
  d.line((xx,yy,min(449,xx+25+j),yy),fill=(20,max(50,153-j*2),max(90,196-j*2)),width=2)
 d.polygon([(425,764),(535,665),(720,695),(720,1090),(425,1090)],fill='#ab7749')
 d.polygon([(425,764),(535,665),(720,695),(682,752),(467,801)],fill='#f2c98b' if not warm else '#eeae72')
 d.polygon([(425,764),(467,801),(467,1090),(425,1090)],fill='#75523a')
 for j in range(10):
  d.line((469,824+j*26,720,778+j*30),fill='#825933',width=2)
 for j in range(7):
  points=[(x,728+6*math.sin(x*.035+t*2+j)) for x in range(j*65,min(449,j*65+65),4)]
  if len(points)>1:d.line(points,fill=CYAN,width=3)
 if warm:
  glow=Image.new('RGBA',(720,1280));gd=ImageDraw.Draw(glow)
  for j in range(6):
   xx=500+j*32
   points=[(xx+9*math.sin(k*.3+t*2+j),738-k*5) for k in range(47)]
   gd.line(points,fill=(255,128,72,95),width=18)
  glow=glow.filter(ImageFilter.GaussianBlur(12));im.paste(glow,(0,0),glow);d=ImageDraw.Draw(im)
  for j in range(16):
   q=(t*.2+j/16)%1;x=490+(j*41)%170+7*math.sin(q*5+j);y=740-q*235
   d.ellipse((x-4,y-4,x+4,y+4),fill='#ffbc7b')
  p.c.flowing(d,[(595,730),(599,660),(590,575),(596,500)],t,RED,6)
  pill(d,'गरम हवा ऊपर उठी',360,420,RED,34)
 if cold:
  pts=[(30+520*q,665-35*math.sin(q*math.pi)) for q in np.linspace(0,1,65)]
  glow=Image.new('RGBA',(720,1280));gd=ImageDraw.Draw(glow);gd.line(pts,fill=(40,218,255,160),width=21)
  glow=glow.filter(ImageFilter.GaussianBlur(12));im.paste(glow,(0,0),glow);d=ImageDraw.Draw(im)
  p.c.flowing(d,pts,t,CYAN,7)
  pill(d,'समुद्र की ठंडी हवा आई',360,420,CYAN,33)
 pill(d,'समुद्र',175,1000,CYAN,31);pill(d,'गरम जमीन',570,1000,GOLD,30)
# Generate a new coast illustration, never reuse the Atacama desert for this lesson.
art=ROOT/'coast.jpg'
if not art.exists():
 raw=e.cf_image('Premium cinematic aerial oblique view of a tropical Indian coastal beach in afternoon sunlight. Ocean on LEFT and wide warm golden sandy beach on RIGHT, palms very far in background, turquoise waves with fine foam, realistic water depth, atmospheric perspective, rich navy and cyan shadows, warm sunlit sand, no people, no text, no arrows, no desert, no labels, composition made for a vertical educational film, exceptionally detailed natural textures.')
 if not raw:raise RuntimeError('Fresh cinematic coast asset unavailable; stop rather than substitute basic cartoons')
 Image.open(io.BytesIO(raw)).convert('RGB').save(art,quality=96)
photo=Image.open(art).convert('RGB')
lines=[
 'रेत इतनी गरम, फिर समुद्र से ठंडी हवा क्यों आती है?',
 'भारत के समुद्री तट पर दिन का ये आसान मॉडल देखो।',
 'धूप से जमीन जल्दी गरम होती है। ऊपर की हवा भी गरम होकर उठती है।',
 'तब समुद्र की ठंडी हवा जमीन की तरफ आती है। इसे समुद्री समीर कहते हैं।']
titles=['गरम रेत… ठंडी हवा कैसे?','समुद्र से जमीन की ओर','पहले जमीन गरम होती है','फिर ठंडी हवा आती है']
e.USE_GEMINI_TTS=True;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+0%';e.VOICE_PITCH='+0Hz'
e.gemini_tts_once=voice_engine.gemini_male_once
e._TTS_STYLE[0]='Clear calm conversational Hindi male teacher. Unhurried, easy to understand. Speech only, no humming, filler, singing or music.'
cached=json.loads((ROOT/'review.json').read_text()) if (ROOT/'review.json').exists() else {}
if cached.get('speech')==lines and (ROOT/'voice.wav').exists():
 ds=cached['scene_seconds'];starts=np.cumsum([0]+ds[:-1]).tolist();duration=sum(ds)
 e._CACHE['voice_used']=cached.get('voice')
else:
 vv=e.make_voices([{'segs':[(None,None,s)]} for s in lines],rot=0)
 audio=[e._compress_pauses(x[0],max_pause=.25)[0] for x in vv]
 assert all(len(a)>e.SR*.5 and np.max(np.abs(a))>.005 for a in audio)
 ds=[max(len(a)/e.SR+.4,m) for a,m in zip(audio,(4.5,4.5,6,6))]
 starts=np.cumsum([0]+ds[:-1]).tolist();duration=sum(ds)
 mix=np.zeros(math.ceil(duration*e.SR),dtype=np.float32)
 for i,a in enumerate(audio):e.add_at(mix,a,starts[i]+.15)
 with wave.open(str(ROOT/'voice.wav'),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(e.SR);w.writeframes((np.clip(mix,-.97,.97)*32767).astype('<i2').tobytes())
 
# Built-in safe-area notes banner: preserve the full-frame cinematic background.
def brand(im):
 d=ImageDraw.Draw(im);txt(d,'MINUTE ME GS',145,62,23,CYAN)
 d.rounded_rectangle((45,125,645,217),14,fill='#102c40',outline='#40c6d2',width=2)
 txt(d,'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',345,151,25,WHITE)
 txt(d,'WhatsApp: +91 89892 79637',345,190,31,GOLD)
def frame(k,t):
 im=p.background(t)
 if k==0:
  ph=ImageOps.fit(photo,(720,930))
  z=1+.08*p.c.ease(t/ds[0]);ph=ph.resize((round(720*z),round(930*z)),Image.Resampling.LANCZOS)
  ph=ImageOps.fit(ph,(720,930));im.paste(ph,(0,350))
  # Animated air stream, plus moving camera; not a static photo-only scene.
  layer=Image.new('RGBA',(720,1280));ld=ImageDraw.Draw(layer)
  for j in range(6):
   x=(t*90+j*120)%750-100;y=620+j*34
   ld.arc((x,y,x+110,y+25),190,345,fill=(172,238,255,150),width=3)
  im=Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
 elif k==1:earth(im,t)
 else:coastal(im,t,warm=True,cold=k==3)
 brand(im);p.title(im,titles[k],t,y=294,col=GOLD if k<3 else CYAN,n=59)
 d=ImageDraw.Draw(im)
 if k==0:
  pill(d,'रेत गरम',565,650,GOLD,32)
  pill(d,'हवा ठंडी?',180,910,CYAN,32)
  txt(d,'AI से बना तटीय शिक्षण दृश्य',360,1130,19,WHITE)
 elif k==2:txt(d,'गरम होकर हवा ऊपर जाती है',360,1125,31,WHITE)
 elif k==3:txt(d,'समुद्र से आने वाली हवा = समुद्री समीर',360,1125,29,WHITE)
 else:txt(d,'नक्शा और दिशा: शिक्षण मॉडल',360,1130,20,'#b0c3d0')
 txt(d,'दिन का सामान्य मॉडल • मौसम से हवा बदल सकती है',360,1183,18,'#aac0ce')
 for j in range(4):
  x=44+j*163;d.rounded_rectangle((x,1230,x+146,1236),3,fill='#28485e')
  if j<=k:d.rounded_rectangle((x,1230,x+146*(min(1,t/ds[k]) if j==k else 1),1236),3,fill=CYAN)
 return im
out=ROOT/'preview_notes_safe_v2.mp4'
cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','18','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for fi in range(math.ceil(duration*FPS)):
 t=fi/FPS;k=max(i for i,x in enumerate(starts) if x<=t);proc.stdin.write(frame(k,t-starts[k]).tobytes())
proc.stdin.close();assert proc.wait()==0
check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=0.15:pix_th=0.10','-f','null','-'],capture_output=True,text=True)
assert check.returncode==0 and 'black_start:' not in check.stderr
sheet=Image.new('RGB',(1440,2560))
for k in range(4):sheet.paste(frame(k,ds[k]*.55),((k%2)*720,(k//2)*1280))
sheet.thumbnail((1000,1800));sheet.save(ROOT/'review_sheet.jpg',quality=92)
manifest={'duration':duration,'scene_seconds':ds,'voice':e._CACHE.get('voice_used'),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'build_only':True,'renderer':'reference polished shaded globe + custom full-frame coast layers','reference_code':'polished_gs.py','new_cloudflare_asset':True,'speech':lines,'sources':['https://www.noaa.gov/jetstream/ocean/sea-breeze'],'editorial_review':'Required; renderer success does not establish shares or retention'}
(ROOT/'review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
