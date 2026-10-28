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
COL=(93,225,244);GOLD=(255,218,99)
plan=json.loads((R/'recipe.json').read_text())
def fit(d,xy,s,n,c,maxw):
 while n>17 and d.textlength(s,font=font(n))>maxw:n-=1
 text(d,xy,s,n,c)
def overlay(im,i):
 row=motion[i];t=row['t'];k=row['scene'];sc=plan['scenes'][k];age=t-float(starts[k]);q=age/meta['seconds'][k];d=ImageDraw.Draw(im)
 d.rounded_rectangle((36,64,636,151),16,fill=(12,40,54),outline=(58,128,147),width=2)
 text(d,(336,89),'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',25,(244,247,237))
 text(d,(336,124),'WhatsApp: +91 89892 79637',29,GOLD)
 text(d,(40,176),'MINUTE ME GS / ANIMATION STUDIO',19,COL,anchor='lm')
 fit(d,(336,222+int(12*(1-min(1,age/.3)))),sc['heading'],40,GOLD,600)
 fit(d,(336,273),sc['explanation'],30,(244,248,250),600)
 occupied=[]
 for obj in sc['objects']:
  if not obj.get('label'):continue
  ax,ay=row['pins'][obj['id']];x,y=ax,ay;x=max(115,min(550,x));y=max(355,min(950,y-30))
  while any(abs(x-a)<170 and abs(y-b)<55 for a,b in occupied):y+=58
  y=min(1010,y);occupied.append((x,y));label=obj['label'];n=26
  while n>18 and d.textlength(label,font=font(n))>200:n-=1
  w=max(65,d.textlength(label,font=font(n))/2+12)
  if abs(x-ax)+abs(y-ay)>45:arrow(d,(x,y+23),(ax,ay),COL,2)
  d.rounded_rectangle((x-w,y-23,x+w,y+23),10,fill=(9,35,47),outline=COL,width=2);text(d,(x,y),label,n,(244,248,250))
 # Dedicated scene labels are projected from the actual 3D scene, not guessed object names.
 for item in row.get('annotations',[]):
  ax,ay=item['anchor'];x=max(135,min(535,ax));y=max(350,min(997,ay));label=item['text'];n=25
  while n>18 and d.textlength(label,font=font(n))>370:n-=1
  w=d.textlength(label,font=font(n))/2+12
  if abs(x-ax)+abs(y-ay)>50:arrow(d,(x,y+20),(ax,ay),COL,2)
  d.rounded_rectangle((x-w,y-22,x+w,y+22),10,fill=(9,35,47),outline=COL,width=2);text(d,(x,y),label,n,(244,248,250))
 if row.get('map_disclaimer'):
  fit(d,(336,1018),'दिशा सांकेतिक • हर पड़ाव का सटीक मार्ग नहीं',21,(224,237,240),590)
 # Phrase timing is approximate for Gemini; it is not falsely labelled word-aligned.
 words=sc['speech'].split();groups=[' '.join(words[j:j+5]) for j in range(0,len(words),5)]
 phrase=groups[min(len(groups)-1,int(max(0,q)*len(groups)))]
 d.rounded_rectangle((36,1050,636,1123),14,fill=(13,40,53),outline=(57,126,143),width=2)
 fit(d,(336,1086),phrase,32,GOLD,560)
 for j in range(6):
  x=236+j*40;d.ellipse((x-7,1137,x+7,1151),fill=GOLD if j==k else (76,114,130))
 fit(d,(336,1170),'समझाने के लिए सांकेतिक 3D दृश्य',20,(174,197,206),580)
 d.rectangle((36,1192,636,1196),fill=(43,75,92));d.rectangle((36,1192,36+int(600*i/(len(motion)-1)),1196),fill=COL)
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
