"""Compose safe-area Hindi explanations over the genuine Blender animation."""
import os,json,math,subprocess
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(os.environ.get('CANAL_ROOT','/mnt/data/canal_3d'))
FONT=os.environ.get('CANAL_FONT',str(R/'Mukta.ttf'))
meta=json.loads((R/'audio.json').read_text());motion=json.loads((R/'motion.json').read_text());starts=np.cumsum([0]+meta['seconds'][:-1]);W,H=720,1280
@lru_cache(None)
def font(n):return ImageFont.truetype(FONT,n)
def text(d,xy,s,n,c,anchor='mm'):
 d.text(xy,s,font=font(n),fill=c,anchor=anchor,stroke_width=1,stroke_fill=(8,25,38))
def arrow(d,a,b,col,width=5):
 d.line([a,b],fill=col,width=width);ang=math.atan2(b[1]-a[1],b[0]-a[0]);l=14
 d.polygon([b,(b[0]-l*math.cos(ang-.5),b[1]-l*math.sin(ang-.5)),(b[0]-l*math.cos(ang+.5),b[1]-l*math.sin(ang+.5))],fill=col)
TITLES=[('इतना बड़ा जहाज़…','ऊपर कैसे चढ़ेगा?'),('ये है पानी की लिफ्ट','पहले जहाज़ अंदर आया'),('पीछे का दरवाज़ा बंद','अब नली से पानी भरता है'),('पानी ऊपर, जहाज़ ऊपर','उठाने वाली कोई क्रेन नहीं'),('दोनों तरफ पानी बराबर','तभी आगे का दरवाज़ा खुला'),('याद रखने की ट्रिक','जहाज़ की लिफ्ट = पानी')]
STEPS=['जहाज़ अंदर','दरवाज़ा बंद','पानी भरता है','जहाज़ बाहर']
COL=(93,225,244);GOLD=(255,218,99)
def overlay(im,i):
 row=motion[i];t=row['t'];k=row['scene'];d=ImageDraw.Draw(im)
 # Upper notes banner is clear of Instagram username/caption and right-hand controls.
 d.rounded_rectangle((36,64,636,151),radius=16,fill=(12,40,54),outline=(58,128,147),width=2)
 text(d,(336,89),'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',25,(244,247,237))
 text(d,(336,124),'WhatsApp: +91 89892 79637',29,GOLD)
 text(d,(40,176),'MINUTE ME GS  /  पनामा नहर',19,COL,anchor='lm')
 # Two short lines, no paragraphs over the mechanism.
 age=t-float(starts[k]);shift=int(14*(1-min(1,age/.3)))
 text(d,(340,222+shift),TITLES[k][0],40,GOLD)
 text(d,(340,269+shift),TITLES[k][1],31,(244,248,250))
 pins=row['pins']
 if k==0:
  p=pins['ship'];arrow(d,(p[0]+105,p[1]-80),(p[0]+12,p[1]-15),GOLD)
  d.rounded_rectangle((max(35,p[0]+40),p[1]-134,max(35,p[0]+40)+150,p[1]-93),12,fill=(10,39,55));text(d,(max(35,p[0]+40)+75,p[1]-114),'जहाज़',29,GOLD)
 if k in (2,3) and t>starts[2]+2.05:
  # Fixed meter makes the physical rise measurable even on a small phone.
  x,y=64,410;h=175;p=(row['level']-1)/1.6
  d.rounded_rectangle((x,y,x+38,y+h),12,fill=(7,25,37),outline=COL,width=2)
  d.rectangle((x+5,y+h-8-int(p*(h-16)),x+33,y+h-7),fill=COL)
  text(d,(90,610),'पानी का स्तर',23,(241,245,246))
  arrow(d,(119,571),(119,425),COL,4)
  q=pins['water'];d.ellipse((q[0]-7,q[1]-7,q[0]+7,q[1]+7),fill=GOLD)
  if k==2:
   q=pins['valve'];arrow(d,(q[0]-70,q[1]+70),q,COL)
 if k==4:
  text(d,(340,340),'स्तर बराबर  =  रास्ता खुला',28,COL)
 if k==5:
  text(d,(340,335),'कई खाने: ऊपर, फिर नीचे',28,COL)
 # Explanatory strip above the bottom UI, with an animated active step.
 active=0 if k<2 else 1 if t<starts[2]+2.05 else 2 if k<4 else 3
 d.rounded_rectangle((36,1050,636,1160),16,fill=(10,31,44),outline=(54,100,118),width=2)
 for j,label in enumerate(STEPS):
  x=110+j*150;c=GOLD if active==j else (125,157,169)
  d.ellipse((x-13,1065,x+13,1091),fill=c)
  text(d,(x,1109),label,23,c)
 text(d,(336,1142),'एक लॉक का सरल 3D मॉडल • वास्तविक आकार नहीं',18,(169,191,200))
 d.rectangle((36,1174,636,1178),fill=(43,75,92));d.rectangle((36,1174,36+int(600*i/(len(motion)-1)),1178),fill=COL)
 return im
if __name__=='__main__':
 dec=subprocess.Popen(['ffmpeg','-v','error','-i',str(R/'silent_3d.mp4'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 enc=subprocess.Popen(['ffmpeg','-y','-v','warning','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','24','-i','-','-i',str(R/'voice.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-shortest','-movflags','+faststart',str(R/'panama_water_lift_3d.mp4')],stdin=subprocess.PIPE)
 for i in range(len(motion)):
  raw=dec.stdout.read(W*H*3)
  if len(raw)!=W*H*3:raise RuntimeError(f'Truncated 3D input frame {i}')
  im=overlay(Image.frombytes('RGB',(W,H),raw),i);enc.stdin.write(im.tobytes())
  if i%120==0:print('Composed',i,flush=True)
 enc.stdin.close();assert enc.wait()==0;assert dec.wait()==0
 print('COMPOSE_DONE',flush=True)
