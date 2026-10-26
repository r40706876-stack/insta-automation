"""Semantic motion graphics: timelines, comparisons, causal flows and location reveals."""
import math
from PIL import Image,ImageDraw,ImageFilter
import auto_poster as e
VERSION=2
C=['#46e6ff','#ffe46b','#ff91ae','#95ffc1']
def ease(x):
 x=max(0,min(1,x));return 1-(1-x)**3
def label(d,s,x,y,size=31,col='white',width=290):
 while size>20 and any(e.text_w(' '.join(l),e.get_font(size))>width for l in e.wrap_words(s,e.get_font(size),width)):size-=2
 lines=e.wrap_words(s,e.get_font(size),width)[:3]
 for j,line in enumerate(lines):d.text((x,y+(j-(len(lines)-1)/2)*size*1.25),' '.join(line),font=e.get_font(size),fill=col,anchor='mm')
def arrow(d,a,b,col,p=1):
 x,y=a;xx,yy=b;xx=x+(xx-x)*p;yy=y+(yy-y)*p;d.line((x,y,xx,yy),fill=col,width=5)
 ang=math.atan2(yy-y,xx-x)
 d.polygon([(xx,yy),(xx-17*math.cos(ang-.5),yy-17*math.sin(ang-.5)),(xx-17*math.cos(ang+.5),yy-17*math.sin(ang+.5))],fill=col)
def book(d,x,y,t,col):
 opening=ease(t/.7);w=70*opening
 d.polygon([(x,y+12),(x-w,y-8),(x-w,y+74),(x,y+94)],fill='#eaf3f4',outline=col,width=3)
 d.polygon([(x,y+12),(x+w,y-8),(x+w,y+74),(x,y+94)],fill='#fff9df',outline=col,width=3)
 for j in range(4):
  d.line((x-w+10,y+12+j*13,x-10,y+30+j*13),fill='#8095a3',width=2)
  d.line((x+10,y+30+j*13,x+w-10,y+12+j*13),fill='#8095a3',width=2)
def render(im,plan,t,dur):
 """Every scene contains a paced explanatory graphic, not just a camera move."""
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 d.rounded_rectangle((34,390,686,825),30,fill=(5,23,39,225),outline=(92,178,200,130),width=2)
 nodes=plan.get('nodes',[])[:3];typ=plan.get('type','flow')
 if typ=='timeline':
  d.line((110,620,610,620),fill='#456273',width=5)
  d.line((110,620,110+500*ease(t/max(1,dur-.8)),620),fill=C[1],width=6)
  for j,n in enumerate(nodes):
   p=ease((t-j*.8)/.5);x=120+j*240
   d.ellipse((x-11*p,620-11*p,x+11*p,620+11*p),fill=C[j])
   if p>.1:label(d,n,x,520 if j%2==0 else 715,30,C[j],185)
 elif typ=='compare':
  for j,n in enumerate(nodes[:2]):
   p=ease((t-j*.7)/.5);x=190+j*340;yy=600+(1-p)*70
   d.rounded_rectangle((x-140,yy-125,x+140,yy+125),20,fill=(20,51,68,255),outline=C[j],width=3)
   label(d,n,x,yy,34,C[j],240)
  if t>1.2:arrow(d,(340,600),(380,600),C[1],ease((t-1.2)/.5))
 elif typ=='location':
  # Locator rings deliberately indicate a named place, not a fabricated map.
  x,y=360,540
  for j in range(3):
   r=30+((t*30+j*35)%110);d.ellipse((x-r,y-r,x+r,y+r),outline=(*[70,220,255],max(0,int(200*(1-r/150)))),width=3)
  d.line((360,535,360,660),fill=C[0],width=4);d.ellipse((346,521,374,549),fill=C[1])
  if nodes:label(d,nodes[0],360,700,43,C[1],560)
  if len(nodes)>1:label(d,nodes[1],360,770,28,'white',560)
 else:
  for j,n in enumerate(nodes):
   p=ease((t-j*.7)/.5);y=465+j*143+(1-p)*25
   if p<=0:continue
   d.rounded_rectangle((110,y-43,610,y+43),18,fill=(18,49,66,255),outline=C[j],width=3)
   label(d,n,360,y,33,C[j],450)
   if j<min(2,len(nodes)-1):arrow(d,(360,y+49),(360,y+87),C[j],ease((t-j*.7-.3)/.4))
 if plan.get('icon')=='book':book(d,605,294,t,C[1])
 im.alpha_composite(layer)
 return im
