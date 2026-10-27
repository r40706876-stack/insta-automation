"""Compose safe-area Hindi explanations over the genuine Blender animation."""
import os,json,math,subprocess
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(os.environ['STUDIO_ROOT'])
FONT=str(R/'Mukta.ttf')
meta=json.loads((R/'audio.json').read_text());motion=json.loads((R/'motion.json').read_text());starts=np.cumsum([0]+meta['seconds'][:-1]);W,H=720,1280
@lru_cache(None)
def font(n):return ImageFont.truetype(FONT,n)
def text(d,xy,s,n,c,anchor='mm'):
 d.text(xy,s,font=font(n),fill=c,anchor=anchor,stroke_width=1,stroke_fill=(8,25,38))
def arrow(d,a,b,col,width=5):
 d.line([a,b],fill=col,width=width);ang=math.atan2(b[1]-a[1],b[0]-a[0]);l=14
 d.polygon([b,(b[0]-l*math.cos(ang-.5),b[1]-l*math.sin(ang-.5)),(b[0]-l*math.cos(ang+.5),b[1]-l*math.sin(ang+.5))],fill=col)
TITLES=json.loads((R/'recipe.json').read_text())['titles']
STEPS=['दो छेद','अलग तेज़ी','अलग दबाव','मोटी नींव']
COL=(93,225,244);GOLD=(255,218,99)
def overlay(im,i):
 row=motion[i];t=row['t'];k=row['scene'];d=ImageDraw.Draw(im)
 d.rounded_rectangle((36,64,636,151),16,fill=(12,40,54),outline=(58,128,147),width=2)
 text(d,(336,89),'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',25,(244,247,237))
 text(d,(336,124),'WhatsApp: +91 89892 79637',29,GOLD)
 text(d,(40,176),'MINUTE ME GS / ANIMATION STUDIO',19,COL,anchor='lm')
 age=t-float(starts[k]);shift=int(14*(1-min(1,age/.3)))
 n=40
 while d.textlength(TITLES[k][0],font=font(n))>620:n-=1
 text(d,(340,222+shift),TITLES[k][0],n,GOLD)
 n=30
 while d.textlength(TITLES[k][1],font=font(n))>610:n-=1
 text(d,(340,269+shift),TITLES[k][1],n,(244,248,250))
 if k in (2,3):
  for key,label,color in [('upper','कम तेज़',COL),('lower','ज़्यादा तेज़',GOLD)]:
   x,y=row['pins'][key];cx=min(530,max(130,x+130));cy=y-44
   d.rounded_rectangle((cx-85,cy-23,cx+85,cy+23),12,fill=(8,32,46),outline=color,width=2)
   text(d,(cx,cy),label,28,color);arrow(d,(cx-35,cy+24),(x+12,y-5),color,3)
 if k==3:
  text(d,(345,332),'बराबर हिस्सों पर पानी का धक्का देखो',26,GOLD)
 if k>=4:
  x,y=row['pins']['dam_base'];cy=min(990,y+65)
  text(d,(390,cy),'नीचे ज़्यादा मोटा',30,GOLD);arrow(d,(370,cy-22),(x,y),GOLD,4)
 active=0 if k<2 else 1 if k==2 else 2 if k==3 else 3
 d.rounded_rectangle((36,1050,636,1160),16,fill=(10,31,44),outline=(54,100,118),width=2)
 for j,label in enumerate(STEPS):
  x=110+j*150;c=GOLD if active==j else (125,157,169)
  d.ellipse((x-13,1065,x+13,1091),fill=c);text(d,(x,1109),label,23,c)
 text(d,(336,1142),'अंदर दिखाने के लिए सामने की दीवार हटाई है',19,(169,191,200))
 d.rectangle((36,1174,636,1178),fill=(43,75,92));d.rectangle((36,1174,36+int(600*i/(len(motion)-1)),1178),fill=COL)
 return im
if __name__=='__main__':
 dec=subprocess.Popen(['ffmpeg','-v','error','-i',str(R/'silent_3d.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','24','-i','-','-i',str(R/'voice.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-shortest','-movflags','+faststart',str(R/'final.mp4')],stdin=subprocess.PIPE)
 for i in range(len(motion)):
  raw=dec.stdout.read(W*H*3)
  if len(raw)!=W*H*3:raise RuntimeError(f'Truncated 3D input frame {i}')
  im=overlay(Image.frombytes('RGB',(W,H),raw),i);enc.stdin.write(im.tobytes())
  if i%120==0:print('Composed',i,flush=True)
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0
 print('COMPOSE_DONE',flush=True)
