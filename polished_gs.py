"""Vivid GS: original full-frame visual storytelling and kinetic Hindi titles."""
import cinematic_gs as c, numpy as np, math, subprocess
from PIL import Image,ImageDraw,ImageFilter,ImageOps
c.prepare();W,H=720,1280
CYAN='#42e8ff';YELLOW='#ffe567';PINK='#ff628b';WHITE='#f6fbff';GREEN='#8dffb6'
ds=[4,7,8,6,8,8];starts=[sum(ds[:i]) for i in range(6)]
rng=np.random.default_rng(42)
# A shaded globe from public-domain Natural Earth geometry, with procedural relief.
tex=Image.new('RGB',(1440,720),'#123d68');td=ImageDraw.Draw(tex)
for ring in c.LAND:
 pts=[((lon+180)*4,(90-lat)*4) for lon,lat,*_ in ring]
 if len(pts)>2:td.polygon(pts,fill='#80aa71')
T=np.array(tex,dtype=float);noise=rng.normal(0,5,T.shape[:2]);T=np.clip(T+noise[:,:,None],0,255).astype(np.uint8)
Y,X=np.mgrid[-1:1:600j,-1:1:600j];mask=X*X+Y*Y<=1;Z=np.sqrt(np.maximum(0,1-X*X-Y*Y));LAT=np.arcsin(-Y);LON=np.arctan2(X,Z);light=np.clip(.25+.75*(Z*.8-X*.45-Y*.2),.12,1)
photo=c.PHOTO

def txt(d,s,y,n=48,col=WHITE,x=360):c.text(d,s,x,y,n,col)
def pill(d,s,y,col=CYAN,n=29,x=360):
 f=c.font(n);bb=d.textbbox((0,0),s,font=f);w=bb[2]+42
 d.rounded_rectangle((x-w/2,y-29,x+w/2,y+29),18,fill='#102d44',outline=col,width=2);txt(d,s,y,n,col,x)
def title(im,s,t,y=170,col=YELLOW,n=65):
 # Scale-in typography, without distorting or clipping Hindi letters.
 layer=Image.new('RGBA',(720,190));d=ImageDraw.Draw(layer)
 size=min(n, int(650/max(1,d.textlength(s,font=c.font(n)))*n))
 d.text((363,98),s,font=c.font(size),fill='#000000',anchor='mm',stroke_width=4)
 d.text((360,94),s,font=c.font(size),fill=col,anchor='mm')
 scale=.84+.16*c.ease(t/.35);layer=layer.resize((int(720*scale),int(190*scale)),Image.Resampling.LANCZOS)
 im.paste(layer,(int((720-layer.width)/2),int(y-layer.height/2)),layer)
def background(t):
 a=np.zeros((1280,720,3),dtype=np.uint8)
 yy=np.linspace(0,1,1280)[:,None];a[:,:,0]=7;a[:,:,1]=(22+20*np.sin(yy*np.pi)).astype('uint8');a[:,:,2]=(41+28*np.sin(yy*np.pi)).astype('uint8')
 im=Image.fromarray(a);d=ImageDraw.Draw(im)
 for j in range(20):
  x=(j*137+int(t*8))%720;y=(j*211)%1280;d.ellipse((x,y,x+2,y+2),fill='#38617a')
 return im

def globe(im,t,cy=640,scale=1):
 lon0=-95+14*math.sin(t*.24);u=((LON+math.radians(lon0)+math.pi)/(2*math.pi)*1440).astype(int)%1440;v=np.clip(((math.pi/2-LAT)/math.pi*720).astype(int),0,719)
 rgb=(T[v,u]*light[:,:,None]).astype(np.uint8);rgba=np.dstack([rgb,mask.astype(np.uint8)*255]);g=Image.fromarray(rgba)
 glow=Image.new('RGBA',(720,900));gd=ImageDraw.Draw(glow);gd.ellipse((48,148,672,772),outline=(30,195,255,130),width=15);glow=glow.filter(ImageFilter.GaussianBlur(16));im.paste(glow,(0,cy-460),glow)
 g=g.resize((int(600*scale),int(600*scale)));im.paste(g,(int(360-g.width/2),int(cy-g.height/2)),g)

def landscape(im,t,stage):
 d=ImageDraw.Draw(im)
 # Full-frame sea cutaway: gradient water, sandy layers, perspective mountains.
 for y in range(290,1001):
  q=(y-290)/710;d.line((0,y,720,y),fill=(int(23+44*q),int(69+49*q),int(101+31*q)))
 for j,(base,col) in enumerate([(590,'#5e8994'),(630,'#7b9291'),(685,'#a0987b')]):
  pts=[(390,1000),(390,base)]+[(x,base-50*math.sin(x*.018+j)-28*math.sin(x*.043)) for x in range(390,721,8)]+[(720,1000)]
  d.polygon(pts,fill=col)
 for y in range(665,1001):
  q=(y-665)/335;d.line((0,y,470,y),fill=(8,int(104-64*q),int(150-67*q)))
 for j in range(34):
  y=673+j*9;x=(j*83+t*(10+j*.3))%470
  d.line((x,y,min(469,x+18+j*1.3),y),fill=(21,130-j*2,167-j*2),width=2)
 d.polygon([(450,700),(535,624),(720,645),(720,1000),(450,1000)],fill='#c39a66')
 d.polygon([(450,700),(535,624),(720,645),(680,704),(490,735)],fill='#e8c08a')
 for j in range(9):d.line((460,730+j*32,720,680+j*35),fill='#9b714e',width=2)
 for j in range(8):
  pts=[(x,665+6*math.sin(x*.035+t*2+j)) for x in range(j*60,min(470,j*60+60),4)]
  if len(pts)>1:d.line(pts,fill=CYAN,width=3)
 # warm inversion appears only when it is being explained
 if stage in (1,2):
  for y in range(440,489):d.line((30,y,690,y),fill=(115+int((y-440)*1.1),65,49))
  pill(d,'ऊपर गर्म हवा',461,PINK,28)
 for j in range(9):
  q=(t*.22+j/9)%1;x=58+j*39+math.sin(q*5+j)*7;y=650-q*(145 if stage in (1,2) else 100)
  d.ellipse((x-4,y-4,x+4,y+4),fill='#b5f4ff')
  if stage in (1,2) and q>.85:c.arrow(d,(x,506),(x+26,506),CYAN,3)
 if stage==2:
  fog=Image.new('RGBA',(720,1280));f=ImageDraw.Draw(fog)
  for j in range(13):
   x=180+j*42+18*math.sin(t*.7+j);f.ellipse((x-64,593,x+64,637),fill=(223,239,240,105))
  fog=fog.filter(ImageFilter.GaussianBlur(8));im.paste(fog,(0,0),fog)
 if stage==3:
  for x,y,sz in [(505,515,75),(690,470,90)]:
   d.polygon([(x-sz,y+265),(x,y),(x+sz,y+265)],fill='#79939c')
   d.polygon([(x,y),(x+18,y+265),(x+sz,y+265)],fill='#3e5c70')
   d.polygon([(x,y),(x-24,y+64),(x-6,y+51),(x+10,y+70),(x+26,y+57)],fill='#edf8fc')
  d.polygon([(500,640),(605,360),(720,640)],fill='#54707a');d.polygon([(605,360),(642,454),(583,420)],fill='#eff6f2');d.polygon([(605,360),(620,640),(720,640)],fill='#324c60')
  for j in range(4):
   x=80+j*85;y=360+(t*38+j*19)%160;c.arrow(d,(x,y),(x,y+70),YELLOW,5)
  pill(d,'एंडीज़ पहाड़',330,WHITE,27,x=570)
 pill(d,'ठंडा समुद्र',919,CYAN,31,x=220);pill(d,'सूखी जमीन',919,YELLOW,29,x=570)

def frame(k,t,dur):
 im=background(t);d=ImageDraw.Draw(im)
 if k==0:
  ph=ImageOps.fit(photo,(720,1280));z=1+.10*c.ease(t/dur);ph=ph.resize((int(720*z),int(1280*z)));ph=ImageOps.fit(ph,(720,1280));im=ph
  sh=Image.new('RGBA',(720,1280));sd=ImageDraw.Draw(sh)
  for y in range(1280):sd.line((0,y,720,y),fill=(2,12,22,int(160*max(0,1-y/450)+180*max(0,(y-800)/480))))
  im=Image.alpha_composite(im.convert('RGBA'),sh).convert('RGB');d=ImageDraw.Draw(im)
  title(im,'समुद्र बगल में!',t,190,CYAN,76);title(im,'फिर भी रेगिस्तान?',t-.3,298,YELLOW,66)
  pill(d,'पानी बहुत',790,CYAN,34,x=520);pill(d,'बारिश कम!',880,YELLOW,34,x=205)
  txt(d,'बारिश कहाँ गई?',1030,60,WHITE)
  txt(d,'AI से बना शिक्षण दृश्य',1180,19,WHITE)
 elif k==1:
  globe(im,t,640,1+.05*math.sin(t*.3));d=ImageDraw.Draw(im)
  title(im,'यह है अटाकामा',t,185,YELLOW)
  # Curved current beside the west coast, illustrative path.
  lon0=-95+14*math.sin(t*.24);rr=300*(1+.05*math.sin(t*.3))
  def loc(lon,lat):
   a=math.radians(lon-lon0);b=math.radians(lat);return (360+rr*math.cos(b)*math.sin(a),640-rr*math.sin(b))
  pts=[loc(-77-4*q,-43+30*q) for q in np.linspace(0,1,60)]
  px,py=loc(-70.5,-24.5);d.ellipse((px-8,py-8,px+8,py+8),fill=YELLOW);pill(d,'अटाकामा',py+50,YELLOW,23,x=px+40)
  glow=Image.new('RGBA',(720,1280));gd=ImageDraw.Draw(glow);gd.line(pts,fill=(35,218,255,170),width=19);glow=glow.filter(ImageFilter.GaussianBlur(12));im.paste(glow,(0,0),glow)
  d=ImageDraw.Draw(im);c.flowing(d,pts,t,CYAN,6)
  pill(d,'हम्बोल्ट • ठंडी धारा',995,CYAN,34)
  pill(d,'दक्षिण से उत्तर की ओर',1080,WHITE,31)
 elif k in (2,3,4):
  stage=(0 if t<2.7 else 1) if k==2 else (2 if k==3 else 3)
  landscape(im,t,stage);d=ImageDraw.Draw(im)
  if stage==0:
   title(im,'ठंडा पानी, कम भाप',t,185,CYAN,58);pill(d,'पहली वजह',260,YELLOW)
   txt(d,'कम पानी भाप बनता है',1080,42,WHITE)
  elif stage==1:
   title(im,'ऊपर जाने का रास्ता रुका',t-2.7,185,PINK,53);pill(d,'दूसरी रुकावट',260,YELLOW)
   txt(d,'नम हवा नीचे रह जाती है',1080,43,WHITE)
  elif stage==2:
   title(im,'कोहरा है… बारिश भी?',t,185,YELLOW,59)
   if t<2.2:
    pill(d,'सोचो: हाँ या नहीं?',1060,YELLOW,40)
   else:
    pill(d,'जरूरी नहीं!',1060,GREEN,47);txt(d,'कोहरा जमीन के पास भी बनता है',1140,30,WHITE)
  else:
   title(im,'सिर्फ समुद्र कारण नहीं',t,185,YELLOW,57)
   pill(d,'नीचे उतरती सूखी हवा',1070,PINK,34)
   if t>3:pill(d,'पहाड़ों की वर्षाछाया भी',1150,CYAN,31)
 else:
  globe(im,t,610,.86);d=ImageDraw.Draw(im)
  title(im,'बारिश का रास्ता याद रखो',t,185,YELLOW,53)
  for j,(s,col) in enumerate([('नम हवा ऊपर उठे',CYAN),('ऊपर जाकर ठंडी हो',WHITE),('बारिश बन सकती है',GREEN)]):
   if t>=j*.8:
    y=430+j*170;d.rounded_rectangle((65,y-60,655,y+60),22,fill='#10283d',outline=col,width=3);txt(d,s,y,43,col)
    if j<2:c.arrow(d,(360,y+72),(360,y+100),YELLOW,4)
  pill(d,'अब किसी दोस्त को समझाकर देखो',1060,YELLOW,29)
 # Persistent minimal branding and scene progress; content fills the frame.
 d=ImageDraw.Draw(im);txt(d,'MINUTE ME GS',57,22,CYAN,x=132)
 for j in range(6):
  x=42+j*107;d.rounded_rectangle((x,1230,x+95,1236),3,fill='#496073')
  if j<=k:d.rounded_rectangle((x,1230,x+95*(min(1,t/dur) if j==k else 1),1236),3,fill=YELLOW)
 if k>0:txt(d,'शिक्षण चित्र • दूरी और आकार सांकेतिक',1190,17,'#b0c3d0')
 return im
base_frame=frame
def frame(k,t,dur):
 im=base_frame(k,t,dur)
 if k>0 and t<.32:
  im=Image.blend(base_frame(k-1,ds[k-1]-.01,ds[k-1]),im,c.ease(t/.32))
 return im
if __name__=='__main__':
 import sys
 if '--preview' in sys.argv:
  sheet=Image.new('RGB',(1440,854))
  for k in range(6):
   for j,f in enumerate((.2,.7)):sheet.paste(frame(k,ds[k]*f,ds[k]).resize((240,427)),(240*k,427*j))
  sheet.save('polished_preview.jpg');sys.exit()
 p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','24','-i','-','-i','cinematic_gs_mobile.mp4','-map','0:v','-map','1:a','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','19','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart','gs_polished_animation.mp4'],stdin=subprocess.PIPE)
 for fi in range(984):
  t=fi/24;k=max(i for i,s in enumerate(starts) if s<=t);p.stdin.write(frame(k,t-starts[k],ds[k]).tobytes())
 p.stdin.close();assert p.wait()==0
