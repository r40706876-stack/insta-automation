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
import re as _re
@lru_cache(None)
def phrases(text,limit=7):
 """4 Nov: subtitles used fixed 5-word slices ('नहीं किया जाएगा।', 'की ओर।').
 Split at sentence/comma breaks; long parts split evenly; never leave a 1-2 word tail."""
 if len(text.split())<=limit+1:return (text,)
 parts=[p.strip() for p in _re.split(r'(?<=[।?!,:])\s+',text) if p.strip()]
 out=[]
 joins={'या','और','लेकिन','क्योंकि','तो','जबकि','पर'}
 for p in parts:
  w=p.split()
  while len(w)>limit:
   mid=len(w)//2
   # Prefer breaking just before a conjunction near the middle ("… बहती है | या पश्चिम …").
   cut=min((j for j in range(2,len(w)-1) if w[j] in joins),key=lambda j:abs(j-mid),default=None)
   if cut is None or abs(cut-mid)>3:cut=-(-len(w)//(-(-len(w)//limit)))
   out.append(' '.join(w[:cut]));w=w[cut:]
  out.append(' '.join(w))
 merged=[]
 for p in out:
  if merged and (len(p.split())<=2 or len(merged[-1].split())<=2) and len((merged[-1]+' '+p).split())<=limit+2:merged[-1]+=' '+p
  else:merged.append(p)
 return tuple(merged) or (text,)
def rgb(value,default):
 try:return tuple(int(value[j:j+2],16) for j in (1,3,5)) if isinstance(value,str) and len(value)==7 and value[0]=='#' else default
 except ValueError:return default
def wrap(d,s,size,maxw):
 words=s.split();lines=[];cur=''
 for w in words:
  t=(cur+' '+w).strip()
  if d.textlength(t,font=font(size))<=maxw or not cur:cur=t
  else:lines.append(cur);cur=w
 if cur:lines.append(cur)
 return lines
def ease_out(x):x=max(0.,min(1.,x));return 1-(1-x)**3
def hook_poster(im,age,sc,total_hook):
 """4 Nov: frame 0 must stop the thumb. Poster card like हथौड़ा-पंख: one bold question,
 two big coloured answer tiles face to face, a MinuteMe stopwatch counting down, and
 movement from the very first frames. The 3D scene stays visible but dimmed behind it."""
 W_,H_=im.size
 bg=Image.new('RGB',(W_,H_),(10,22,40));g=ImageDraw.Draw(bg)
 for y in range(H_):
  f=y/H_;g.line([(0,y),(W_,y)],fill=(int(14+30*f),int(24+10*f),int(52-14*f)))
 im=Image.blend(im,bg,.86);d=ImageDraw.Draw(im)
 a=ease_out(age/.35)
 # top chip
 chip='परीक्षा में पूछा गया सवाल'
 cw=d.textlength(chip,font=font(26))+44
 d.rounded_rectangle((360-cw/2,92,360+cw/2,140),24,fill=(255,196,61))
 d.text((360,116),chip,font=font(26),fill=(25,25,30),anchor='mm')
 # question: slams in (slight scale/drop) and stays big
 q=sc['hook_question'];size=54
 lines=wrap(d,q,size,640)
 while len(lines)>4 and size>36:size-=3;lines=wrap(d,q,size,640)
 y=200-int(26*(1-a))
 for line in lines[:4]:
  d.text((360,y),line,font=font(size),fill=(255,255,255),anchor='mm',stroke_width=4,stroke_fill=(8,14,30));y+=size+16
 # two answer tiles slide in from left/right, then pulse gently
 opts=[str(o).split(':',1)[-1].strip() for o in (sc.get('quiz_options') or [])][:2]
 top=max(y+30,470);th=300
 cols=[(255,122,61),(61,165,255)];letters=['A','B']
 pulse=1+.025*math.sin(max(0,age-.6)*6.0)
 for j,opt in enumerate(opts):
  sl=ease_out((age+.14-.06*j)/.32);off=int((1-sl)*(-420 if j==0 else 420))
  cx=190+340*j+off;w=150*pulse;h=th/2*pulse;cy=top+th/2
  d.rounded_rectangle((cx-w+6,cy-h+8,cx+w+6,cy+h+8),28,fill=(4,8,18))
  d.rounded_rectangle((cx-w,cy-h,cx+w,cy+h),28,fill=cols[j],outline=(255,255,255),width=4)
  d.ellipse((cx-44,cy-h+22,cx+44,cy-h+110),fill=(255,255,255))
  d.text((cx,cy-h+66),letters[j],font=font(64),fill=cols[j],anchor='mm')
  n=36;ol=wrap(d,opt,n,270)
  while len(ol)>3 and n>24:n-=2;ol=wrap(d,opt,n,270)
  oy=cy+26-((len(ol[:3])-1)*(n+8))/2
  for line in ol[:3]:
   d.text((cx,oy),line,font=font(n),fill=(255,255,255),anchor='mm',stroke_width=3,stroke_fill=(20,20,30));oy+=n+8
 if len(opts)==2:
  vs=ease_out((age-.45)/.25);r=int(34*vs)
  if r>2:
   d.ellipse((360-r,top+th/2-r,360+r,top+th/2+r),fill=(255,255,255),outline=(20,20,30),width=3)
   d.text((360,top+th/2),'या',font=font(max(10,int(30*vs))),fill=(20,20,30),anchor='mm')
 # MinuteMe stopwatch countdown (brand identity + reason to stay)
 cy=top+th+120;R=62
 left=max(0.,1-age/max(1.,total_hook))
 d.ellipse((360-R-8,cy-R-8,360+R+8,cy+R+8),fill=(255,196,61))
 d.rectangle((360-12,cy-R-30,360+12,cy-R-6),fill=(255,196,61))
 d.ellipse((360-R,cy-R,360+R,cy+R),fill=(14,26,44))
 d.pieslice((360-R+6,cy-R+6,360+R-6,cy+R-6),-90,-90+360*left,fill=(255,92,72))
 d.ellipse((360-R+20,cy-R+20,360+R-20,cy+R-20),fill=(14,26,44))
 secs=max(1,math.ceil(left*min(5,total_hook)))
 d.text((360,cy),str(secs),font=font(46),fill=(255,255,255),anchor='mm')
 d.text((360,cy+R+42),'जवाब आने से पहले कमेंट करो: A या B?',font=font(30),fill=(255,214,92),anchor='mm',stroke_width=3,stroke_fill=(8,14,30))
 d.text((360,1236),'@MinuteMe_GS',font=font(24),fill=(190,210,230),anchor='mm')
 return im

def overlay(im,i):
 row=motion[i];t=row['t'];k=row['scene'];sc=plan['scenes'][k];age=t-float(starts[k]);q=age/meta['seconds'][k];d=ImageDraw.Draw(im);accent=rgb(sc.get('text_color'),GOLD);secondary=rgb(sc.get('explanation_color'),(244,248,250))
 if sc.get('hook_question') and sc.get('role','hook')=='hook':
  im=hook_poster(im,age,sc,meta['seconds'][k])
  d=ImageDraw.Draw(im);d.rectangle((36,1192,636,1196),fill=(43,75,92));d.rectangle((36,1192,36+int(600*i/(len(motion)-1)),1196),fill=COL)
  return im
 # Notes/WhatsApp banner only in the last 3 seconds (end card): top-of-frame space is
 # reserved for the question, which decides the 3-second hold.
 total=float(sum(meta['seconds']))
 if t>=total-3:
  d.rounded_rectangle((36,64,636,151),16,fill=(12,40,54),outline=(58,128,147),width=2)
  text(d,(336,89),'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',25,(244,247,237))
  text(d,(336,124),'WhatsApp: +91 89892 79637',29,GOLD)
 hook_q=sc.get('hook_question')
 options=sc.get('quiz_options') or []
 label_floor=430 if options else 355
 if hook_q:
  # Frame 0 = full question in big letters + both options (pattern of the top 5 reels).
  size=46
  while True:
   words=hook_q.split();lines=[];cur=''
   for w in words:
    trial=(cur+' '+w).strip()
    if d.textlength(trial,font=font(size))<=610 or not cur:cur=trial
    else:lines.append(cur);cur=w
   if cur:lines.append(cur)
   if len(lines)<=3 or size<=32:break
   size-=2
  y=128
  for line in lines[:3]:
   fit(d,(336,y),line,size,accent,620);y+=size+14
  if options:
   top=y+6;box_h=26+48*min(2,len(options))
   d.rounded_rectangle((46,top,626,top+box_h),14,fill=(12,39,52),outline=COL,width=3)
   for option_index,option in enumerate(options[:2]):fit(d,(336,top+37+option_index*48),str(option),32,(244,248,250),550)
   y=top+box_h+14
  fit(d,(336,y+18),sc['explanation'],26,secondary,600)
  label_floor=y+60
  options=[]
 else:
  text(d,(40,176),'MINUTE ME GS',19,COL,anchor='lm')
  fit(d,(336,222+int(12*(1-min(1,age/.3)))),sc['heading'],40,accent,600)
  fit(d,(336,273),sc['explanation'],30,secondary,600)
 # Optional question/reveal card stays above the mechanism and below the title.
 card_spec=sc.get('quiz_card')
 if card_spec and not hook_q:
  reveal=age>=float(card_spec.get('reveal_after',2))
  color=rgb(card_spec.get('answer_color'),(96,238,167)) if reveal else accent
  message=card_spec.get('answer','') if reveal else card_spec.get('question','')
  d.rounded_rectangle((46,310,626,376),12,fill=(12,39,52),outline=color,width=2)
  fit(d,(336,342),message,29,color,550)
 if options:
  d.rounded_rectangle((46,304,626,402),12,fill=(12,39,52),outline=COL,width=2)
  for option_index,option in enumerate(options[:2]):fit(d,(336,330+option_index*44),str(option),29,(244,248,250),550)
 occupied=[]
 for obj in sc['objects']:
  if not obj.get('label'):continue
  ax,ay=row['pins'][obj['id']];x,y=ax,ay;x=max(115,min(550,x));y=max(label_floor,min(950,y-30))
  while any(abs(x-a)<170 and abs(y-b)<55 for a,b in occupied):y+=58
  y=min(1010,y);occupied.append((x,y));label=obj['label'];n=26
  while n>18 and d.textlength(label,font=font(n))>200:n-=1
  w=max(65,d.textlength(label,font=font(n))/2+12)
  if abs(x-ax)+abs(y-ay)>45:arrow(d,(x,y+23),(ax,ay),COL,2)
  d.rounded_rectangle((x-w,y-23,x+w,y+23),10,fill=(9,35,47),outline=COL,width=2);text(d,(x,y),label,n,rgb(obj.get('label_color'),(244,248,250)))
 # Dedicated scene labels are projected from the actual 3D scene, not guessed object names.
 for item in [a for a in row.get('annotations',[]) if a.get('style')!='context']:
  ax,ay=item['anchor'];x=max(135,min(535,ax));y=max(max(350,label_floor-80),min(997,ay));label=item['text'];n=25
  while n>18 and d.textlength(label,font=font(n))>370:n-=1
  while any(abs(x-a)<210 and abs(y-b)<54 for a,b in occupied):y+=58
  y=min(997,y);occupied.append((x,y))
  w=d.textlength(label,font=font(n))/2+12
  if abs(x-ax)+abs(y-ay)>50:arrow(d,(x,y+20),(ax,ay),COL,2)
  d.rounded_rectangle((x-w,y-22,x+w,y+22),10,fill=(9,35,47),outline=COL,width=2);text(d,(x,y),label,n,(244,248,250))
 # Map context names (seas, route states) are printed on the map itself, like Map Test 01.
 for item in [a for a in row.get('annotations',[]) if a.get('style')=='context']:
  ax,ay=item['anchor'];label=item['text'];n=24
  if not (40<ax<680 and label_floor-40<ay<1030):continue
  if any(abs(ax-a)<150 and abs(ay-b)<40 for a,b in occupied):continue
  d.text((ax,ay),label,font=font(n),fill=(22,52,66),anchor='mm',stroke_width=3,stroke_fill=(250,250,244));occupied.append((ax,ay))
 if row.get('map_disclaimer') and plan['scenes'][k].get('role')=='reveal':
  fit(d,(336,1018),'दिशा सांकेतिक • हर पड़ाव का सटीक मार्ग नहीं',19,(224,237,240),590)
 # A specific useful share invitation appears only after the explanation, for two seconds.
 card=plan.get('share_card') or {}
 objective=plan.get('primary_objective','share')
 if objective=='save':card={'cta':'रिवीजन के लिए सेव करें'}
 elif objective=='follow':card={'cta':'अगला सवाल: '+str(plan.get('series_next_topic') or '')}
 if k==len(plan['scenes'])-1 and age>=max(0,meta['seconds'][k]-2) and card.get('cta'):
  d.rounded_rectangle((36,305,636,365),12,fill=(17,63,65),outline=GOLD,width=2)
  fit(d,(336,335),card['cta'],26,GOLD,570)
 # Phrase timing is approximate for Gemini; it is not falsely labelled word-aligned.
 groups=phrases(sc['speech'])
 # Time each phrase by its share of words, not equal slices.
 sizes=[len(g.split()) for g in groups];total_w=sum(sizes);acc=0;phrase=groups[-1]
 for g,n in zip(groups,sizes):
  acc+=n
  if max(0,q)*total_w<acc:phrase=g;break
 d.rounded_rectangle((36,1050,636,1123),14,fill=(13,40,53),outline=(57,126,143),width=2)
 fit(d,(336,1086),phrase,32,accent,560)
 # 4 Nov: less clutter. Scene dots removed (the progress bar already shows progress);
 # the 'symbolic 3D' note only on the final revision scene.
 if k==len(plan['scenes'])-1:fit(d,(336,1160),'समझाने के लिए सांकेतिक 3D दृश्य',19,(150,175,186),580)
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
