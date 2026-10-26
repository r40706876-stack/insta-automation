"""Full-scene educational motion. Normalized keyframes, no photo fallback."""
import math
from PIL import Image, ImageDraw, ImageFont
import one_confusion as legacy
import retention_pilots as pilots
VERSION=6
KINDS={'rail','sunrise','river','gravity','quantity','timeline','process','inertia','water'}
BG='#f6f3ea'; INK='#172f45'; BLUE='#087fa4'; RED='#d94d41'; GOLD='#edb649'
def font(n): return ImageFont.truetype('Mukta-ExtraBold.ttf',n)
def label(d,s,x,y,n=30,c=INK):
 d.text((x,y),s,font=font(n),fill=c,anchor='mm')
def ease(q):
 q=max(0,min(1,q));return q*q*(3-2*q)
def arrow(d,a,b,c=BLUE):
 d.line((a,b),fill=c,width=6);z=math.atan2(b[1]-a[1],b[0]-a[0])
 d.polygon([b,(b[0]-20*math.cos(z-.5),b[1]-20*math.sin(z-.5)),(b[0]-20*math.cos(z+.5),b[1]-20*math.sin(z+.5))],fill=c)
def validate(sc):
 m=sc.get('animation',{});assert m.get('type') in KINDS,'Unsupported mechanism: author a scene, never use photo fallback'
 assert m.get('phase') in ('question','explain','demonstrate','recall')
 ns=m.get('labels',[]);assert 2<=len(ns)<=3 and all(isinstance(s,str) and 0<len(s)<=26 for s in ns)
 if m['type']=='quantity':
  a,b=m.get('amounts',[0,0]);assert 1<=a<=12 and 1<=b<=12 and a!=b
 if m['type']=='timeline':
  years=m.get('years',[]);assert len(years)==len(ns) and years==sorted(years) and len(set(years))==len(years)
 return m

def render(sc,t,duration):
 m=validate(sc);kind=m['type'];p=ease(t/max(.5,duration-.3));ns=m['labels'];reveal=m['phase'] not in ('question','recall') or t>=duration-1.6
 im=Image.new('RGB',(720,1280),BG);d=ImageDraw.Draw(im)
 # Main stage occupies 720 x 750 pixels. Text is outside the moving objects.
 if kind=='rail':
  layer=Image.new('RGB',(1080,1100),BG);ld=ImageDraw.Draw(layer)
  pilots.train(ld,t,y=110);pilots.rail(ld,p if reveal else .15,y=500)
  pilots.sun(ld,200,360,60,t);pilots.thermometer(ld,p)
  im.paste(layer.resize((680,690)),(20,280));d=ImageDraw.Draw(im)
 elif kind=='sunrise':
  # Reuse the actual geographic state geometry and synchronized clock renderer.
  layer=pilots.geo_frame(2 if reveal else 0,t,duration)
  im.paste(layer.crop((60,570,1020,1260)).resize((680,480)),(20,320))
  pilots.clock(d,210,900,t);pilots.clock(d,510,900,t)
 elif kind=='river':
  import map_three as river
  layer=river.background(False,not reveal).copy();ld=ImageDraw.Draw(layer)
  river.river(ld,p,False)
  im.paste(layer.crop((40,520,1040,1300)).resize((700,600)),(10,330))
 elif kind=='gravity':
  legacy.globe(d,170,760,130);legacy.globe(d,550,760,130,True)
  # Same person crosses both worlds without changing size.
  x=170+380*p;legacy.person(d,x,480,t*.15)
  for j in range(6):arrow(d,(90+j*30,940),(90+j*30,1000),BLUE)
  arrow(d,(550,940),(550,980),RED)
 elif kind=='inertia':
  q=ease(min(1,t/2));shift=80*q;lean=65*ease((t-2)/1.2)
  d.rounded_rectangle((25,910,695,990),18,fill='#d9e3e4')
  travel=160*min(t,2)
  for j in range(6):
   x=(j*155-travel)%850-80;d.rectangle((x,945,x+70,953),fill='white')
  for j in range(3):
   x=(j*260-travel*.3)%850-80;d.rounded_rectangle((x,330,x+100,415),8,fill='#d8e8e6')
  d.rounded_rectangle((50+shift,450,580+shift,850),35,fill='#2d9fbc',outline=INK,width=5)
  d.rounded_rectangle((85+shift,485,545+shift,715),20,fill='#d6f1f3')
  for x in (150+shift,490+shift):
   d.ellipse((x-50,800,x+50,900),fill=INK)
   z=min(t,2)*5;d.line((x-35*math.cos(z),850-35*math.sin(z),x+35*math.cos(z),850+35*math.sin(z)),fill='white',width=7)
  feet=330+shift;head=feet+lean
  d.line((feet,790,feet,685,head,600),fill=INK,width=20)
  d.line((feet,700,feet-28,790,feet-55,790),fill=INK,width=14)
  d.line((feet,700,feet+25,790,feet+48,790),fill=INK,width=14)
  d.line((head-10,620,head+40,665,head+75,640),fill=BLUE,width=13)
  if m['phase']=='explain':
   r=22+8*math.sin(t*4)
   for fx in (feet-40,feet+35):d.ellipse((fx-r,790-r,fx+r,790+r),outline=GOLD,width=5)
  d.ellipse((head-30,535,head+30,595),fill='#efb18c',outline=INK,width=3)
  if t>1.8:
   arrow(d,(feet,630),(head+100,630),RED)
   for j in range(3):
    x=feet+((t*90+j*35)%120);d.ellipse((x-4,622,x+4,630),fill=GOLD)
  d.rounded_rectangle((52+shift,700,68+shift,770),5,fill=RED if t>=2 else '#9fc2c4')
  label(d,'ब्रेक',590,400,34,RED)
 elif kind=='quantity':
  a,b=m['amounts'];n=a+(b-a)*p
  for side,count in enumerate((a,n)):
   x=190+340*side;d.rounded_rectangle((x-125,390,x+125,900),22,fill='#e7b858',outline=INK,width=4)
   for j in range(math.ceil(count)):
    opacity=min(1,max(0,count-j));y=850-j*35
    d.rectangle((x-90,y,x-90+180*opacity,y+22),fill='#fff6d7')
   label(d,str(a if side==0 else round(n)),x,960,56)
 elif kind=='timeline':
  years=m['years'];lo,hi=years[0],years[-1]
  d.line((120,420,120,950),fill='#cad9d9',width=10)
  d.line((120,420,120,420+530*p),fill=BLUE,width=10)
  for i,(year,s) in enumerate(zip(years,ns)):
   frac=(year-lo)/(hi-lo);y=420+530*frac
   d.ellipse((103,y-17,137,y+17),fill=BLUE if p>=frac else '#a5bcbc')
   label(d,str(year),230,y,42,RED)
   if p>=frac and reveal:label(d,s,475,y,30)
 elif kind=='water':
  d.rectangle((30,870,690,1010),fill='#359bc3')
  for j in range(16):
   x=70+j*38;y=850-((t*90+j*37)%370)
   d.ellipse((x-5,y-10,x+5,y+10),fill=BLUE)
  for j in range(5):d.ellipse((180+j*55,350+(j%2)*20,340+j*55,480+(j%2)*20),fill='#b8d9e5')
  if reveal:
   for j in range(8):
    x=230+j*37;y=500+(t*160+j*41)%330;d.line((x,y,x-8,y+22),fill=BLUE,width=5)
 else: # Explicit concept process: the narrated steps travel and connect in order.
  for i,s in enumerate(ns):
   y=400+i*230;progress=ease(p*len(ns)-i)
   if i:arrow(d,(360,y-140),(360,y-70),BLUE)
   x=360-500*(1-progress)
   d.rounded_rectangle((x-270,y-70,x+270,y+70),24,fill=('#d2ece8','#ffe5b0','#dbe8f7')[i],outline=BLUE,width=4)
   label(d,s if reveal else '?',x,y,40)
 if kind not in ('timeline','process'):
  if reveal:
   for i,s in enumerate(ns[:2]):
    x=190+340*i;col=BLUE if i==0 else RED
    d.rounded_rectangle((x-150,1020,x+150,1090),16,fill='#e0efeb' if i==0 else '#ffe0d1')
    label(d,s,x,1055,29,col)
  else:label(d,'देखो… फिर जवाब दो',360,1055,32,BLUE)
 return im
