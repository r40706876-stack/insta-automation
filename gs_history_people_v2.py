"""Human-centred 1857 explanation: visual events, animated walk cycle and cause-to-outcome recall."""
import os,json,math,hashlib,subprocess
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
ROOT=Path(os.environ.get('GS_PEOPLE_ROOT','experiments/meerut_delhi_people_v2'))
A=ROOT/'assets';W,H,FPS=720,1280,30
meta=json.loads((A/'audio.json').read_text());ds=meta['seconds'];starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds)
GOLD='#ffdf8d';CYAN='#75e7e5';WHITE='#fff5e5';NAVY='#0b1d29'
@lru_cache(None)
def font(n):return ImageFont.truetype(str(A/'Mukta.ttf'),n)
def text(d,s,x,y,n=38,col=WHITE,maxwidth=630):
 while d.textlength(s,font=font(n))>maxwidth:n-=1
 d.text((x+2,y+3),s,font=font(n),fill='#071217',anchor='mm',stroke_width=2)
 d.text((x,y),s,font=font(n),fill=col,anchor='mm')
def ease(q):q=max(0,min(1,q));return q*q*(3-2*q)
def tag(d,s,x,y,n=32,col=GOLD):
 width=min(645,d.textlength(s,font=font(n))+38)
 d.rounded_rectangle((x-width/2,y-29,x+width/2,y+29),12,fill='#112b34',outline=col,width=2)
 text(d,s,x,y,n,col,maxwidth=width-24)
def arrow(d,a,b,col=GOLD,w=5):
 d.line((a,b),fill=col,width=w);ang=math.atan2(b[1]-a[1],b[0]-a[0]);r=16
 d.polygon([b,(b[0]-r*math.cos(ang-.5),b[1]-r*math.sin(ang-.5)),(b[0]-r*math.cos(ang+.5),b[1]-r*math.sin(ang+.5))],fill=col)
photos={n:Image.open(A/(n+'.png')).convert('RGB') for n in ('punishment','release','court')}
# Four separately generated gait poses, normalized within equal cells for stable foot placement.
sheet=Image.open(A/'walk.png').convert('RGBA');walk=[]
for j in range(4):
 cw,ch=sheet.width//2,sheet.height//2;cell=sheet.crop(((j%2)*cw,(j//2)*ch,(j%2+1)*cw,(j//2+1)*ch))
 bb=cell.getchannel('A').getbbox();assert bb,'Sprite transparency missing'
 spr=cell.crop(bb);spr.thumbnail((235,390),Image.Resampling.LANCZOS)
 tile=Image.new('RGBA',(260,420));tile.alpha_composite(spr,((260-spr.width)//2,410-spr.height));walk.append(tile)
def actor(im,x,y,t,height=270,flip=False,phase=0):
 spr=walk[(int(t*6)+phase)%4];spr=spr.resize((round(260*height/420),height),Image.Resampling.LANCZOS)
 if flip:spr=ImageOps.mirror(spr)
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);d.ellipse((x-42,y-6,x+45,y+9),fill=(2,7,10,90))
 layer.alpha_composite(spr,(round(x-spr.width/2),round(y-spr.height-2*math.sin(t*9))))
 im.paste(layer,(0,0),layer)
# Reusable gentle camera motion. The paintings are never described as real historical footage.
@lru_cache(None)
def fitted(name):return ImageOps.fit(photos[name],(820,1458),centering=(.5,.5))
def photo(name,t,duration,focus=.5):
 ph=fitted(name);q=ease(t/max(.1,duration));left=round(45+34*(q-.5));top=round(85+28*math.sin(q*math.pi))
 im=ph.crop((left,top,left+720,top+1280)).copy()
 # Independent atmospheric particles, plus a softer foreground/sky motion cue.
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 for j in range(18):
  x=(j*123+t*9)%W;y=420+(j*83-t*17)%710
  d.ellipse((x,y,x+2,y+2),fill=(255,212,149,85))
 im=Image.alpha_composite(im.convert('RGBA'),layer)
 shade=Image.new('RGBA',(W,H));d=ImageDraw.Draw(shade)
 for yy in range(H):
  a=int(170*max(0,1-yy/420)+170*max(0,(yy-1030)/250))
  d.line((0,yy,W,yy),fill=(3,13,20,a))
 return Image.alpha_composite(im,shade).convert('RGB')
def map_scene(t,duration):
 yy,xx=np.mgrid[:H,:W];q=np.clip(1-((xx-360)/700)**2-((yy-760)/1100)**2,0,1)
 arr=np.zeros((H,W,3),np.uint8)
 for k,(base,delta) in enumerate(((8,16),(28,25),(40,23))):arr[:,:,k]=base+q*delta
 im=Image.fromarray(arr);d=ImageDraw.Draw(im)
 # Clean route inset, explicitly schematic: north at top, Meerut north-east of Delhi.
 for x in range(45,710,70):d.line((x,370,x,1070),fill='#2c4d56',width=1)
 for y in range(390,1090,70):d.line((35,y,685,y),fill='#2c4d56',width=1)
 a=(520,480);b=(225,840);pts=[]
 for q in np.linspace(0,1,80):pts.append((a[0]*(1-q)+b[0]*q+25*math.sin(q*math.pi),a[1]*(1-q)+b[1]*q))
 d.line(pts,fill='#52716c',width=4)
 p=ease(min(1,t/max(1,duration*.72)));n=max(2,round(1+p*79));layer=Image.new('RGBA',(W,H));ld=ImageDraw.Draw(layer)
 ld.line(pts[:n],fill=(255,200,80,190),width=20);layer=layer.filter(ImageFilter.GaussianBlur(10));im.paste(layer,(0,0),layer);d=ImageDraw.Draw(im);d.line(pts[:n],fill=GOLD,width=6)
 for name,(x,y),date in [('मेरठ',a,'10 मई'),('दिल्ली',b,'11 मई')]:
  rr=12+4*math.sin(t*3);d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=GOLD,width=3)
  tag(d,name,x,y-53,38);text(d,date,x,y+40,29,CYAN)
 i=min(78,max(0,n-2));x,y=pts[i];actor(im,x,y,t,145,True)
 d=ImageDraw.Draw(im);text(d,'रातभर दिल्ली की ओर',360,1010,39,GOLD)
 text(d,'उत्तर ऊपर • स्थानों की दिशा सही • मार्ग सांकेतिक',360,1080,20,WHITE)
 return im
HEAD=['साथी छुड़ाए… फिर दिल्ली क्यों?','9 मई 1857 • मेरठ','10 मई • साथियों की रिहाई','11 मई • दिल्ली में नेतृत्व की माँग','दिल्ली क्यों? एक साझा नेता चाहिए था','तीन दिनों की कहानी, तीन तस्वीरों में']
def brand(im,k,t):
 d=ImageDraw.Draw(im);text(d,'MINUTE ME GS • इतिहास समझो',211,54,22,CYAN)
 d.rounded_rectangle((43,111,645,199),13,fill='#122a33',outline='#4d9094',width=2)
 text(d,'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',345,137,23,WHITE)
 text(d,'WhatsApp: +91 89892 79637',345,175,29,GOLD)
 text(d,HEAD[k],360,282,44,GOLD)
 for j in range(6):
  x=45+j*105;d.rounded_rectangle((x,1220,x+93,1225),2,fill='#41606a')
  if j<=k:d.rounded_rectangle((x,1220,x+93*(min(1,t/ds[k]) if j==k else 1),1225),2,fill=GOLD)
 text(d,'AI से बने सांकेतिक दृश्य • ऐतिहासिक फोटो नहीं',360,1175,17,'#ded8c9')
def frame(k,t):
 if k==0:
  im=photo('release',t,ds[k]);d=ImageDraw.Draw(im)
  tag(d,'1857 • मेरठ',360,375,35,CYAN)
  # Human action is visible from frame one, before any date memorisation.
  if t<1.5:tag(d,'कैद साथियों को बाहर निकाला',360,1020,34,GOLD)
  else:
   tag(d,'फिर दिल्ली क्यों गए?',360,1010,46,GOLD)
   actor(im,110+110*ease((t-1.5)/3),1130,t,240,False)
 elif k==1:
  im=photo('punishment',t,ds[k]);d=ImageDraw.Draw(im)
  count=85;tag(d,str(count)+' सिपाहियों को सज़ा',360,380,43,GOLD)
  if t>2.3:tag(d,'बाकी साथी यह देख रहे थे',360,1020,34,CYAN)
 elif k==2:
  if t<ds[k]*.67:
   im=photo('release',t,ds[k]);d=ImageDraw.Draw(im);tag(d,'जेल खुली • साथी छुड़ाए गए',360,385,37,CYAN)
  else:
   im=map_scene((t-ds[k]*.67)*2,ds[k]*.66);d=ImageDraw.Draw(im)
   tag(d,'अब दिल्ली की ओर',360,375,38,CYAN)
 elif k==3:
  if t<1.5:
   im=map_scene(t+2,3.5)
  else:
   im=photo('court',t,ds[k]);d=ImageDraw.Draw(im)
   tag(d,'सिपाहियों ने नेतृत्व माँगा',360,385,36,CYAN)
   # Two screen-readable labels explain the relationship, without invented direct quotes.
   tag(d,'सिपाही',165,540,28,WHITE);tag(d,'बहादुर शाह ज़फ़र',500,590,28,GOLD)
   if t>2.4:arrow(d,(265,555),(432,590),GOLD,4)
 elif k==4:
  im=photo('court',t,ds[k]);d=ImageDraw.Draw(im)
  tag(d,'मुगल बादशाह का नाम',360,380,35,GOLD)
  if t>1.0:tag(d,'एकजुटता के लिए साझा नेतृत्व',360,990,33,CYAN)
  if t>3.1:tag(d,'हर मोर्चे के सेनापति नहीं',360,1080,34,WHITE)
 else:
  im=photo('court',t,ds[k]);im=Image.blend(im,Image.new('RGB',(W,H),NAVY),.77);d=ImageDraw.Draw(im)
  rows=[('punishment','9 मई','सज़ा'),('release','10 मई','विद्रोह / रिहाई'),('court','11 मई','नेतृत्व की माँग')]
  for j,(name,date,act) in enumerate(rows):
   x=38+j*226;y=450
   tile=ImageOps.fit(photos[name],(200,350),centering=(.5,.63));im.paste(tile,(x,y))
   d=ImageDraw.Draw(im);active=(0 if t<1.8 else 1 if t<3.2 else 2)==j
   d.rounded_rectangle((x-3,y-3,x+203,y+353),9,outline=GOLD if active else '#75878a',width=4 if active else 1)
   text(d,date,x+100,y-43,37,GOLD,maxwidth=200);text(d,act,x+100,y+396,27,WHITE,maxwidth=210)
   if j<2:arrow(d,(x+205,y+180),(x+220,y+180),CYAN,3)
  tag(d,'शुरुआत मेरठ • साझा नेतृत्व दिल्ली',360,985,33,CYAN)
  text(d,'अब दोस्त से तस्वीर देखकर क्रम पूछो',360,1080,31,WHITE)
 brand(im,k,t);return im
# Cross-shot joins are short, preserving the event progression.
def finalframe(k,t):
 im=frame(k,t)
 if k>0 and t<.16:im=Image.blend(frame(k-1,ds[k-1]-.02),im,ease(t/.16))
 return im
if '--sheet' not in os.sys.argv:
 out=ROOT/'people_story_notes_safe_v2.mp4';p=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(A/'voice.wav'),'-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','19','-af','volume=2dB','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for i in range(math.ceil(total*FPS)):
  tt=i/FPS;k=max(j for j,v in enumerate(starts) if v<=tt);p.stdin.write(finalframe(k,tt-starts[k]).tobytes())
 p.stdin.close();assert p.wait()==0
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)
 review={'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'duration':total,'voice':meta['voice'],'speech':meta['speech'],'scene_seconds':ds,'build_only':True,'changes':['People and visible event relationships replace symbolic lock-only scene','Four-frame walking sepoy sprite animation','Clean schematic journey inset','Soldiers-to-emperor explanation with labels','Three-event illustrated recall instead of text-only cards'],'image_note':'AI historical reconstructions, not archival photos; uniforms and exact staging are illustrative','map_note':'North up, Meerut north-east of Delhi; route schematic','sources':['https://www.cbse.gov.in/cbsenew/ebooks/ANO-SD-SW.pdf','https://sathee.iitk.ac.in/sathee-railway-exams/student-corner/general-knowledge/indian-history/revolt-1857/'],'performance':'No measured engagement claim'}
 (ROOT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2));print(json.dumps(review,ensure_ascii=False))
sheetout=Image.new('RGB',(1440,3840))
for k in range(6):sheetout.paste(frame(k,ds[k]*.65),((k%2)*720,(k//2)*1280))
sheetout.thumbnail((900,2400));sheetout.save(ROOT/'review_sheet.jpg',quality=92)
