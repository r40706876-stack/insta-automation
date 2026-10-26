"""Semantic motion graphics: timelines, comparisons, causal flows and location reveals."""
import math
from PIL import Image,ImageDraw,ImageFilter
import auto_poster as e
VERSION=4
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
 x+=8*math.sin(t*.9)
 opening=ease(t/.7);w=70*opening
 d.polygon([(x,y+12),(x-w,y-8),(x-w,y+74),(x,y+94)],fill='#eaf3f4',outline=col,width=3)
 d.polygon([(x,y+12),(x+w,y-8),(x+w,y+74),(x,y+94)],fill='#fff9df',outline=col,width=3)
 for j in range(4):
  d.line((x-w+10,y+12+j*13,x-10,y+30+j*13),fill='#8095a3',width=2)
  d.line((x+10,y+30+j*13,x+w-10,y+12+j*13),fill='#8095a3',width=2)
# Pages lift and turn independently of the background camera.
def turning_page(d,x,y,t):
 a=(t*.7)%1;w=100*math.cos(a*math.pi)
 d.polygon([(x,y),(x+w,y-30*math.sin(a*math.pi)),(x+w,y+85),(x,y+105)],fill='#fff8d9',outline='#53ddeb',width=2)

def building(d,x,y,t,col):
 # Walls rise, the roof settles, then arches and windows are revealed.
 p=ease(t/.9);top=y-170*p
 d.rectangle((x-150,top,x+150,y),fill='#e3bd81',outline='#fff2ca',width=3)
 if t>.35:
  q=ease((t-.35)/.65);roof=top-45*q
  d.polygon([(x-170,top),(x,roof),(x+170,top)],fill='#f8dba1',outline=col,width=3)
 if t>.8:
  for j in range(5):
   xx=x-115+j*57;q=ease((t-.8-j*.12)/.4)
   d.rounded_rectangle((xx-16,y-105*q,xx+16,y),16,fill='#335c70',outline='#fff0c8',width=2)
 for j in range(9):
  if t>1.2:
   xx=x-130+j*32;d.ellipse((xx,y+14,xx+4,y+18),fill=col)
 label(d,'सांकेतिक शिक्षण चित्र',x,y+45,21,'#eaf4f6',400)

def concept(d,kind,t):
 # State changes are visible in the objects, independent of camera movement.
 if kind=='motion':
  x=170+min(t,2)*100
  d.line((70,570,650,570),fill='#e6f8ff',width=5)
  d.rounded_rectangle((x-60,470,x+60,550),15,fill=C[0],outline='white',width=3)
  for xx in (x-38,x+38):d.ellipse((xx-13,537,xx+13,563),fill='#18364a',outline='white',width=3)
  if t<2:arrow(d,(x-110,510),(x-70,510),C[1])
  else:
   bx=x+min(100,(t-2)*65);d.ellipse((bx-15,410,bx+15,440),fill=C[2]);d.line((x,515,bx,450),fill=C[2],width=9)
 elif kind=='balance':
  a=.25*math.sin(t*1.8);cx,cy=360,460
  d.polygon([(340,590),(380,590),(360,470)],fill=C[1])
  left=(cx-160,cy+160*a);right=(cx+160,cy-160*a)
  d.line((*left,*right),fill='white',width=7)
  for x,y in (left,right):
   d.line((x,y,x,y+70),fill=C[0],width=3);d.arc((x-55,y+30,x+55,y+110),0,180,fill=C[0],width=5)
 elif kind=='quantity':
  for side in range(2):
   count=8 if side==0 else max(4,8-int(t*2))
   x=180+side*350
   for j in range(count):
    yy=570-j*18;d.ellipse((x-55,yy-10,x+55,yy+10),fill=C[side],outline='#795d22',width=2)
 elif kind=='water':
  d.rectangle((110,520,610,580),fill='#17619b')
  for j in range(10):
   q=(t*.22+j*.1)%1;x=150+j*42;y=510-q*160
   d.ellipse((x-4,y-7,x+4,y+7),fill=C[0])
  d.rounded_rectangle((190,330,530,385),28,fill='#dff7ff')
 elif kind=='orbit':
  d.ellipse((240,360,480,600),outline=C[0],width=3)
  d.ellipse((325,445,395,515),fill=C[1])
  x=360+120*math.cos(t*1.4);y=480+120*math.sin(t*1.4)
  d.ellipse((x-16,y-16,x+16,y+16),fill=C[2])

def render(im,plan,t,dur):
 """Every scene contains a paced explanatory graphic, not just a camera move."""
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 d.rounded_rectangle((34,630,686,825),24,fill=(5,23,39,180),outline=(92,178,200,110),width=2)
 # The illustration itself animates above the compact explanation.
 if plan.get('icon') in ('motion','balance','quantity','water','orbit'):concept(d,plan['icon'],t)
 elif plan.get('icon')=='building':building(d,360,590,t,C[1])
 elif plan.get('icon')=='book':
  book(d,360,415,t,C[1]);turning_page(d,360,425,t)
 nodes=plan.get('nodes',[])[:3];typ=plan.get('type','flow')
 if typ=='timeline':
  d.line((110,740,610,740),fill='#456273',width=5)
  d.line((110,740,110+500*ease(t/max(1,dur-.8)),740),fill=C[1],width=6)
  for j,n in enumerate(nodes):
   p=ease((t-j*.8)/.5);x=120+j*240
   d.ellipse((x-11*p,740-11*p,x+11*p,740+11*p),fill=C[j])
   if p>.1:label(d,n,x,680 if j%2==0 else 790,30,C[j],185)
 elif typ=='compare':
  for j,n in enumerate(nodes[:2]):
   p=ease((t-j*.7)/.5);x=190+j*340;yy=725+(1-p)*30
   d.rounded_rectangle((x-140,yy-65,x+140,yy+65),20,fill=(20,51,68,255),outline=C[j],width=3)
   label(d,n,x,yy,34,C[j],240)
  if t>1.2:arrow(d,(340,725),(380,725),C[1],ease((t-1.2)/.5))
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
   p=ease((t-j*.7)/.5);y=670+j*63+(1-p)*25
   if p<=0:continue
   d.rounded_rectangle((110,y-25,610,y+25),18,fill=(18,49,66,255),outline=C[j],width=3)
   label(d,n,360,y,29,C[j],450)
   if j<min(2,len(nodes)-1):arrow(d,(360,y+27),(360,y+36),C[j],ease((t-j*.7-.3)/.4))
 
 im.alpha_composite(layer)
 return im
