"""Original animated geography demo. Build only: no publication capability."""
import math,json,hashlib,io,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
OUT=Path('experiments/cinematic_coast_v1'); W,H,FPS=720,1280,24
BG='#07182b'; WHITE='#f2f8ff'; BLUE='#49daff'; GOLD='#ffcb72'
SPEECH=[
'समुद्र बगल में, फिर भी रेगिस्तान! बारिश कहाँ गई?',
'दक्षिण अमेरिका का अटाकामा देखो। इसके तट पर ठंडी हम्बोल्ट धारा उत्तर की ओर बहती है।',
'ठंडा समुद्र, कम वाष्पीकरण। ऊपर गर्म हवा की परत, नीचे की नम हवा को ऊपर उठने से रोकती है।',
'नमी से तट पर कोहरा बन सकता है। लेकिन कोहरा होना, बारिश होना नहीं है।',
'नीचे उतरती सूखी हवा और एंडीज़ की वर्षाछाया भी सूखे में योगदान देती हैं। सिर्फ धारा कारण नहीं।',
'याद रखो। समुद्र पास होना काफी नहीं। बारिश के लिए नम हवा का ऊपर उठकर ठंडा होना भी जरूरी है।']
HEAD=['समुद्र है… बारिश क्यों नहीं?','अटाकामा • दक्षिण अमेरिका','बारिश बनने की राह में रुकावट','कोहरा ≠ बारिश','एक कारण नहीं • तीन की टीम','नमी + ऊपर उठना + ठंडा होना']
SUB=['एक जगह। दो बिल्कुल अलग दुनिया।','नीला रास्ता: ठंडी हम्बोल्ट धारा','ठंडा पानी + स्थिर हवा की परत','नमी जमीन के पास अटक सकती है','ठंडी धारा  •  उतरती हवा  •  वर्षाछाया','समझ आया? किसी study partner को समझाओ।']
GEO='https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson'
SOURCES=['https://prod-01-asg-www-climate.woc.noaa.gov/news-features/event-tracker/flooding-chile%E2%80%99s-atacama-desert-after-years%E2%80%99-worth-rain-one-day','https://pubs.usgs.gov/gip/deserts/types/','https://science.nasa.gov/earth/earth-observatory/cloudy-earth-85843/']
PHOTO=None; LAND=[]
def font(n):return ImageFont.truetype('Mukta-ExtraBold.ttf',n)
def text(d,s,x,y,n=30,c=WHITE,anchor='mm'):d.text((x,y),s,font=font(n),fill=c,anchor=anchor)
def tag(d,s,x,y,c=BLUE,n=24):
 b=d.textbbox((0,0),s,font=font(n));w=b[2]+28
 d.rounded_rectangle((x-w/2,y-24,x+w/2,y+24),14,fill='#102a41',outline=c,width=2);text(d,s,x,y,n,c)
def ease(v):v=max(0,min(1,v));return v*v*(3-2*v)
def arrow(d,a,b,col=BLUE,width=5):
 d.line([a,b],fill=col,width=width);ang=math.atan2(b[1]-a[1],b[0]-a[0]);s=width*3
 d.polygon([b,(b[0]-s*math.cos(ang-.5),b[1]-s*math.sin(ang-.5)),(b[0]-s*math.cos(ang+.5),b[1]-s*math.sin(ang+.5))],fill=col)
def flowing(d,pts,t,col=BLUE,width=5):
 d.line(pts,fill=col,width=width,joint='curve')
 for j in range(7):
  v=((t*.24+j/7)%1)*(len(pts)-1);i=min(len(pts)-2,int(v));f=v-i
  a=pts[i];b=pts[i+1];x=a[0]+(b[0]-a[0])*f;y=a[1]+(b[1]-a[1])*f
  d.ellipse((x-4,y-4,x+4,y+4),fill='white')
 arrow(d,pts[-2],pts[-1],col,width)
def base(k,t,dur):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 for y in range(100,1100):
  f=math.sin((y-100)/1000*math.pi);d.line((0,y,W,y),fill=(7,int(24+9*f),int(43+13*f)))
 text(d,'MINUTE ME GS',48,62,25,BLUE,'lm');text(d,'VISUAL EXPLAINER',674,62,17,'#a9bdcd','rm')
 d.line((48,99,672,99),fill='#234257',width=2)
 text(d,HEAD[k],360,174,35,GOLD)
 text(d,SUB[k],360,1040,25,WHITE)
 text(d,'शिक्षण दृश्य • आकार व दूरी सांकेतिक',360,1100,17,'#92a9bb')
 for i in range(6):
  d.rounded_rectangle((48+i*105,1160,143+i*105,1165),2,fill=BLUE if i<k else '#294356')
  if i==k:d.rounded_rectangle((48+i*105,1160,48+i*105+95*min(1,t/dur),1165),2,fill=BLUE)
 text(d,'@MinuteMe_GS',360,1210,23,'#a9bdcd');return im,d

def project(lon,lat,rot=-80,r=300,cx=360,cy=600):
 a=math.radians(lon-rot);b=math.radians(lat);z=math.cos(b)*math.cos(a)
 return (cx+r*math.cos(b)*math.sin(a),cy-r*math.sin(b),z)
def globe(d,t):
 r=300;cy=605;rot=-105+22*ease(t/5)
 for rr in range(r,0,-3):
  q=rr/r;d.ellipse((360-rr,cy-rr,360+rr,cy+rr),fill=(9,int(40+30*(1-q)),int(72+42*(1-q))))
 for lat in range(-60,90,30):
  pts=[]
  for lon in range(-180,181,3):
   x,y,z=project(lon,lat,rot,r,360,cy)
   if z>0:pts.append((x,y))
   elif len(pts)>1:d.line(pts,fill='#31526b',width=1);pts=[]
  if len(pts)>1:d.line(pts,fill='#31526b')
 for ring in LAND:
  ps=[project(a,b,rot,r,360,cy) for a,b,*_ in ring]
  if all(z>0 for x,y,z in ps):d.polygon([(x,y) for x,y,z in ps],fill='#638878',outline='#9cba91')
 d.ellipse((59,cy-301,661,cy+301),outline=BLUE,width=2)
 x,y,z=project(-70.5,-24.5,rot,r,360,cy)
 for rr in (12,22+9*math.sin(t*3)):d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=GOLD,width=3)
 tag(d,'ATACAMA',x+50,y+65,GOLD)
def coast(d,t):
 # Regional geographic overview, west on left, north at top.
 def p(lon,lat):return(85+(lon+90)*14,285+(-lat)*12)
 d.rounded_rectangle((45,260,675,960),25,fill='#103b5b')
 for ring in LAND:
  ps=[p(a,b) for a,b,*_ in ring if -91<a<-40 and -57<b<1]
  if len(ps)>3:d.polygon(ps,fill='#7f9872',outline='#b6c79b')
 pts=[p(-76,-45),p(-77,-36),p(-76,-28),p(-79,-20),p(-82,-12)]
 flowing(d,pts,t,BLUE,8)
 x,y=p(-70.5,-24.5);d.ellipse((x-12,y-12,x+12,y+12),fill=GOLD)
 tag(d,'अटाकामा',x+80,y,GOLD);tag(d,'हम्बोल्ट धारा',210,865,BLUE)
 text(d,'प्रशांत महासागर',175,385,23,'#b2e9ff');text(d,'N ↑',615,310,24)

def cutaway(d,t,fog=False,mountains=False):
 d.rounded_rectangle((45,290,675,945),24,fill='#17425b')
 # air, ocean, land and subsurface as separately animated layers
 d.rectangle((46,555,420,944),fill='#0a557b');d.rectangle((46,750,420,944),fill='#123958')
 d.polygon([(420,610),(470,565),(515,545),(675,565),(675,945),(420,945)],fill='#b88b58')
 for j in range(6):
  x=60+j*58; yy=555+5*math.sin(t*2+j);d.arc((x,yy-8,x+55,yy+8),0,180,fill=BLUE,width=3)
 for j in range(4):
  x=105+j*80;v=(t*.22+j*.25)%1;y=700-v*125
  arrow(d,(x,y+18),(x,y),BLUE,3)
 tag(d,'ठंडा समुद्र',220,830,BLUE);tag(d,'सूखा तट',545,830,GOLD)
 if mountains:
  d.polygon([(490,570),(570,370),(620,570)],fill='#777e80');d.polygon([(550,420),(570,370),(590,420)],fill='#dae6eb')
  tag(d,'एंडीज़',570,330)
  for j in range(3):arrow(d,(120+j*90,340),(120+j*90,470),GOLD,4)
  text(d,'नीचे उतरती हवा',255,305,23,GOLD)
 else:
  d.rounded_rectangle((75,395,640,440),15,fill='#7f5a41');text(d,'ऊपर गर्म हवा • स्थिर परत',355,418,23,GOLD)
  for j in range(3):
   x=140+j*105;arrow(d,(x,535),(x,455),BLUE,4)
   d.line((x-12,450,x+12,450),fill='#ff8d7d',width=5)
 if fog:
  for j in range(7):
   x=270+j*48+7*math.sin(t+j);y=520+9*math.sin(t*1.4+j)
   d.ellipse((x-42,y-17,x+42,y+17),fill='#a4bac1')
  tag(d,'कोहरा • नीचे की नमी',375,670,WHITE)
 else:tag(d,'कम वाष्पीकरण',230,675)

def render(k,t,dur):
 im,d=base(k,t,dur)
 if k==0:
  if PHOTO:
   ph=ImageOps.fit(PHOTO,(624,650));z=1+.045*ease(t/dur);ph=ph.resize((int(624*z),int(650*z)));ph=ImageOps.fit(ph,(624,650));im.paste(ph,(48,290));d=ImageDraw.Draw(im)
   tag(d,'समुद्र',185,875,BLUE);tag(d,'रेगिस्तान',520,875,GOLD)
   text(d,'AI कल्पना • वास्तविक स्थान का फोटो नहीं',360,970,16,'#a9bdcd')
  else:cutaway(d,t,False)
  tag(d,'इतना पानी… फिर भी सूखा?',360,350,GOLD,27)
 elif k==1:
  if t<2.7:globe(d,t)
  else:coast(d,t)
 elif k==2:cutaway(d,t)
 elif k==3:cutaway(d,t,True)
 elif k==4:cutaway(d,t,False,True)
 else:
  globe(d,t)
  for j,(s,col) in enumerate([('01  ठंडी धारा',BLUE),('02  स्थिर / उतरती हवा',GOLD),('03  एंडीज़ की वर्षाछाया',WHITE)]):
   if t>j*.55:tag(d,s,360,430+j*130,col,29)
 return im

def prepare():
 OUT.mkdir(parents=True,exist_ok=True)
 f=OUT/'land.geojson'
 if not f.exists():
  import requests
  r=requests.get(GEO,timeout=45);r.raise_for_status();f.write_text(r.text)
 global LAND,PHOTO
 for feat in json.loads(f.read_text())['features']:
  g=feat['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
  LAND.extend(p[0] for p in polys)
 p=OUT/'coast_ai.jpg'
 if p.exists():PHOTO=Image.open(p).convert('RGB')

def build():
 import auto_poster as e
 OUT.mkdir(parents=True,exist_ok=True)
 if not (OUT/'coast_ai.jpg').exists():
  if not(e.CF_ACCOUNT_ID and e.CF_API_TOKEN):raise RuntimeError('Cloudflare credentials unavailable; no claim of AI-generated visuals')
  b=e.cf_image('Cinematic aerial oblique view of a barren coastal desert meeting deep blue Pacific ocean, dramatic contrast between immense ocean and extremely dry rocky ochre land, realistic educational illustration, sophisticated natural lighting, no text, no labels, no arrows, no buildings, vertical composition')
  if not b:raise RuntimeError('Cloudflare did not return an image; preserve diagnostic and stop')
  Image.open(io.BytesIO(b)).convert('RGB').save(OUT/'coast_ai.jpg',quality=95)
 prepare();e.FPS=FPS;e.W=W;e.H=H
 voices=e.make_voices([{'segs':[(None,None,s)]} for s in SPEECH],rot=0)
 arr=[v[0] for v in voices]
 if any(len(a)<e.SR*.5 or np.max(np.abs(a))<.001 for a in arr):raise RuntimeError('Narration missing')
 durs=[max(len(a)/e.SR+.4,m) for a,m in zip(arr,[4,7,8,6,8,8])];starts=np.cumsum([0]+durs[:-1]).tolist();total=sum(durs)
 audio=e.beat_music(total,17)*.055
 for i,a in enumerate(arr):
  e.add_at(audio,a.astype(np.float32),starts[i]+.12,1)
  if i:e.add_at(audio,e.sfx_pop(.12),starts[i],.35)
 def frame(fi):
  t=fi/FPS;k=max(i for i,s in enumerate(starts) if s<=t);return render(k,t-starts[k],durs[k])
 e.encode_frames(frame,math.ceil(total*FPS),np.clip(audio,-.98,.98),str(OUT/'demo.mp4'),key=lambda fi:fi)
 sheet=Image.new('RGB',(6*240,2*427))
 for k in range(6):
  for j,f in enumerate((.25,.75)):sheet.paste(render(k,durs[k]*f,durs[k]).resize((240,427)),(k*240,j*427))
 sheet.save(OUT/'contact_sheet.jpg',quality=92)
 (OUT/'manifest.json').write_text(json.dumps({'duration':total,'scene_seconds':durs,'speech':SPEECH,'sources':SOURCES,'map_source':GEO,'map_license':'Natural Earth public domain','cloudflare_image':True,'synthetic_photo_label':True,'publication':'demo only','sha256':hashlib.sha256((OUT/'demo.mp4').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
if __name__=='__main__':build()
