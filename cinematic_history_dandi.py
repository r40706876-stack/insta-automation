"""History cinematic proof: salt-tax visual, dimensional crystals, regional map and dates."""
import os,json,math,io,wave,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageOps
ROOT=Path('experiments/history_dandi_cinematic_v1');ROOT.mkdir(parents=True,exist_ok=True)
os.environ['GS_VISUAL_OUTPUT']=str(ROOT)
import auto_poster as e
e.resolve_font()
import daily_visual_gs as voices
import polished_gs as p
W,H,FPS=720,1280,24
CYAN='#49ddf5';GOLD='#ffe18a';WHITE='#f5f7fa';RED='#fc8e78'
def text(d,s,x,y,n=34,col=WHITE):
 while d.textlength(s,font=e.get_font(n))>640:n-=1
 d.text((x,y),s,font=e.get_font(n),fill=col,anchor='mm')
def tag(d,s,x,y,col=CYAN,n=28):
 wid=d.textlength(s,font=e.get_font(n))+36
 d.rounded_rectangle((x-wid/2,y-26,x+wid/2,y+26),14,fill='#102b3e',outline=col,width=2)
 text(d,s,x,y,n,col)
def crystal(im,x,y,size,t):
 # Real 3D vertex rotations, face sorting and directional light.
 verts=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
 a=t*.45;b=.4+.15*math.sin(t*.3)
 ry=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
 rx=np.array([[1,0,0],[0,math.cos(b),-math.sin(b)],[0,math.sin(b),math.cos(b)]])
 v=verts@ry.T@rx.T
 faces=[[4,5,6,7],[1,2,6,5],[3,7,6,2],[0,3,2,1],[0,4,7,3],[0,1,5,4]]
 d=ImageDraw.Draw(im)
 for face in sorted(faces,key=lambda face:np.mean(v[face,2])):
  pts=v[face];normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);normal/=np.linalg.norm(normal)
  if normal[2]<=0:continue
  strength=.55+.4*max(0,np.dot(normal,np.array([-.35,.6,.72])))
  col=tuple(int(z*strength) for z in (235,249,255))
  pp=[(x+size*q[0],y-size*q[1]) for q in pts]
  d.polygon(pp,fill=col,outline='#d0f3ff',width=2)
 # Fine specular glint on the crystal.
 r=5+3*math.sin(t*2);xx=x-size*.4;yy=y-size*.5
 d.line((xx-r,yy,xx+r,yy),fill='white',width=2)
 d.line((xx,yy-r,xx,yy+r),fill='white',width=2)
def coin(d,x,y,t):
 wid=5+23*abs(math.cos(t*2))
 d.ellipse((x-wid,y-25,x+wid,y+25),fill='#b47c31',outline='#ffe7a1',width=2)
 d.ellipse((x-wid+3,y-20,x+wid-3,y+20),outline='#f3ca70',width=2)
def paper(im,t,low=False):
 # A symbolic modern teaching prop, not a forged archival document.
 d=ImageDraw.Draw(im);x=135;y=665 if low else 435;w=450;h=260
 d.rounded_rectangle((x+12,y+16,x+w+12,y+h+16),14,fill='#04121e')
 d.polygon([(x,y+10),(x+w-12,y),(x+w,y+h-10),(x+8,y+h)],fill='#e3cda9')
 text(d,'ब्रिटिश नमक कानून',360,y+65,37,'#49392b')
 for j in range(4):d.line((x+45,y+110+j*20,x+w-45-(j%2)*35,y+110+j*20),fill='#9f896e',width=3)
 if not low:
  scale=p.c.ease(t/.45);box=Image.new('RGBA',(340,120));bd=ImageDraw.Draw(box)
  bd.rounded_rectangle((4,4,336,116),8,outline='#b94434',width=5)
  text(bd,'नमक पर कर',170,60,43,'#b94434')
  box=box.rotate(-11,resample=Image.Resampling.BICUBIC,expand=True)
  box=box.resize((max(1,round(box.width*scale)),max(1,round(box.height*scale))))
  im.paste(box,(360-box.width//2,y+180-box.height//2),box)
def plate(im,x,y,t,col):
 d=ImageDraw.Draw(im)
 d.ellipse((x-128,y-15,x+128,y+42),fill='#081524')
 for j in range(22,0,-1):
  tone=tuple(max(0,min(255,int(v*(.6+.4*j/22)))) for v in col)
  d.ellipse((x-125+j,y-37+j*.4,x+125-j,y+37-j*.4),fill=tone)
 d.ellipse((x-95,y-22,x+95,y+22),outline='#f2dab6',width=3)
 for j in range(4):
  q=(t*.35+j/4)%1
  crystal(im,x+(j-1.5)*20,y-170+150*q,8+j%2*2,t+j)
def proj(lon,lat):return(60+(lon-70.8)/3*600,410+(23.5-lat)/3.2*630)
# A public-domain geographic coastline, with a labelled schematic march corridor.
mapim=Image.new('RGB',(720,1280),'#103b54');md=ImageDraw.Draw(mapim)
for j in range(15):md.line((0,400+j*46,720,400+j*46),fill='#18435a',width=1)
mask=Image.new('L',(720,1280));draw=ImageDraw.Draw(mask)
for ring in p.c.LAND:
 pts=[proj(lon,lat) for lon,lat,*_ in ring]
 if len(pts)>2:draw.polygon(pts,fill=255)
shadow=Image.new('RGB',(720,1280),'#7b674d')
mapim.paste(shadow,(7,12),mask)
yy,xx=np.mgrid[0:1280,0:720];rng=np.random.default_rng(9);noise=rng.normal(0,1.5,(1280,720))
land=np.zeros((1280,720,3),np.uint8)
for k,base in enumerate((200,183,139)):land[:,:,k]=np.clip(base+10*np.sin(xx*.008)+noise-yy*.008,0,255)
mapim.paste(Image.fromarray(land),(0,0),mask)
route=[(72.58,23.06),(72.64,22.95),(72.87,22.69),(72.95,22.56),(72.9,22.4),(72.85,22.18),(72.96,21.85),(73.0,21.62),(73.0,21.4),(72.83,21.17),(72.8,20.89)]
points=[proj(*q) for q in route]
def history_map(im,t,dur):
 crop=mapim.crop((35,395,685,1070));im.paste(crop,(35,395))
 d=ImageDraw.Draw(im);tag(d,'गुजरात का तटीय क्षेत्र',360,405,GOLD,28)
 # Arc-length path reveal and camera-independent labels.
 lengths=[0]
 for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,b))
 progress=p.c.ease(min(1,t/max(.1,dur-1)));target=lengths[-1]*progress
 trail=[points[0]]
 for i in range(len(points)-1):
  if lengths[i+1]<=target:trail.append(points[i+1])
  else:
   q=max(0,(target-lengths[i])/max(.01,lengths[i+1]-lengths[i]))
   trail.append((points[i][0]+q*(points[i+1][0]-points[i][0]),points[i][1]+q*(points[i+1][1]-points[i][1])));break
 glow=Image.new('RGBA',(720,1280));gd=ImageDraw.Draw(glow)
 if len(trail)>1:gd.line(trail,fill=(255,193,85,210),width=15,joint='curve')
 glow=glow.filter(ImageFilter.GaussianBlur(9));im.paste(glow,(0,0),glow);d=ImageDraw.Draw(im)
 d.line(points,fill='#8f8e78',width=3)
 if len(trail)>1:d.line(trail,fill=GOLD,width=6,joint='curve')
 x,y=trail[-1];r=9+3*math.sin(t*5)
 d.ellipse((x-r,y-r,x+r,y+r),fill=WHITE,outline=GOLD,width=3)
 for j,(lon,lat) in enumerate((route[0],route[-1])):
  x,y=proj(lon,lat);d.ellipse((x-7,y-7,x+7,y+7),fill=CYAN if not j else GOLD)
 x,y=points[0];d.line((x-10,y,250,y),fill=CYAN,width=2)
 tag(d,'साबरमती आश्रम',230,y-35,CYAN,27)
 tag(d,'12 मार्च 1930',230,y+30,WHITE,25)
 x,y=points[-1];tag(d,'दांडी',x+55,y+45,GOLD,29)
 text(d,'अरब सागर',150,890,28,'#b6e7f5')
 text(d,'भौगोलिक तटरेखा • यात्रा-पथ सांकेतिक',360,1105,20,'#bccbd4')
art=ROOT/'salt_shore.jpg'
if not art.exists():
 raw=e.cf_image('Cinematic macro close-up of an elderly Indian hand in plain white homespun cotton sleeve holding a small natural lump of sea salt over a coastal salt crust at dawn, Arabian sea softly out of focus behind, 1930 historical educational reconstruction, warm gold and teal documentary lighting, dignified realistic natural skin and salt textures, no face visible, no modern objects, no text, no letters, no flags. Vertical composition, hand and salt near center.')
 if not raw:raise RuntimeError('Historical illustration generation failed; no cartoon fallback')
 Image.open(io.BytesIO(raw)).convert('RGB').save(art,quality=96)
photo=Image.open(art).convert('RGB')
lines=[
 'रोज़ के नमक पर भी टैक्स! गांधीजी ने नमक को ही आंदोलन क्यों बनाया?',
 'नमक सबकी जरूरत था। उस पर लगने वाला कर गरीबों पर भी बोझ था।',
 'बारह मार्च उन्नीस सौ तीस को गांधीजी साबरमती से दांडी के लिए पैदल निकले।',
 'छह अप्रैल को दांडी में नमक कानून तोड़ा। नमक, अंग्रेजी राज के विरोध का प्रतीक बना।']
titles=['नमक पर भी टैक्स!','नमक: सबकी जरूरत','साबरमती से दांडी','नमक बना विरोध का प्रतीक']
e.USE_GEMINI_TTS=True;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+0%';e.VOICE_PITCH='+0Hz'
e.gemini_tts_once=voices.gemini_male_once
e._TTS_STYLE[0]='Clear unhurried conversational Hindi male documentary teacher. Dates must be intelligible. Speech only, no humming, singing, music or filler.'
cached=json.loads((ROOT/'review.json').read_text()) if (ROOT/'review.json').exists() else {}
if cached.get('speech')==lines and (ROOT/'voice.wav').exists():
 ds=cached['scene_seconds'];e._CACHE['voice_used']=cached.get('voice')
else:
 vv=e.make_voices([{'segs':[(None,None,s)]} for s in lines],rot=0)
 audio=[e._compress_pauses(v[0],max_pause=.25)[0] for v in vv]
 assert all(len(a)>e.SR*.5 and np.max(np.abs(a))>.005 for a in audio)
 ds=[max(len(a)/e.SR+.55,m) for a,m in zip(audio,(5,5,6,6))]
 starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds);mix=np.zeros(math.ceil(total*e.SR),np.float32)
 for i,a in enumerate(audio):e.add_at(mix,a,starts[i]+.15)
 with wave.open(str(ROOT/'voice.wav'),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(e.SR);w.writeframes((np.clip(mix,-.98,.98)*32767).astype('<i2').tobytes())
starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds)
def brand(im):
 d=ImageDraw.Draw(im);text(d,'MINUTE ME GS • इतिहास',180,62,23,CYAN)
 d.rounded_rectangle((45,125,645,217),14,fill='#102b3e',outline=CYAN,width=2)
 text(d,'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',345,151,25,WHITE)
 text(d,'WhatsApp: +91 89892 79637',345,190,31,GOLD)
def frame(k,t):
 im=p.background(t);d=ImageDraw.Draw(im)
 if k==0:
  paper(im,t)
  halo=Image.new('RGBA',(720,1280));hd=ImageDraw.Draw(halo);hd.ellipse((125,755,595,1055),fill=(51,190,228,60))
  halo=halo.filter(ImageFilter.GaussianBlur(38));im.paste(halo,(0,0),halo)
  for j,(x,y,s) in enumerate(((305,867,72),(425,912,53),(236,960,31))):crystal(im,x,y+7*math.sin(t+j),s,t+j)
  d=ImageDraw.Draw(im)
  for j in range(3):coin(d,560,900-((t*65+j*110)%260),t+j)
  tag(d,'1930',360,395,GOLD,33)
  text(d,'नमक के साथ कर का बोझ',360,1115,31,WHITE)
 elif k==1:
  d.ellipse((48,735,672,935),fill='#102b3b')
  plate(im,190,840,t,(193,159,115));plate(im,530,840,t,(193,209,215))
  # A single common ingredient reaches both bowls. No invented tax amounts.
  crystal(im,360,530,67,t)
  d=ImageDraw.Draw(im);p.c.arrow(d,(310,615),(220,730),GOLD,5);p.c.arrow(d,(410,615),(500,730),CYAN,5)
  tag(d,'साधारण घर',190,1000,GOLD,29);tag(d,'समृद्ध घर',530,1000,CYAN,29)
  text(d,'सबकी जरूरत, गरीबों पर भी कर',360,1115,32,WHITE)
 elif k==2:history_map(im,t,ds[k])
 else:
  ph=ImageOps.fit(photo,(720,870));z=1+.07*p.c.ease(t/ds[k]);ph=ph.resize((round(720*z),round(870*z)),Image.Resampling.LANCZOS)
  ph=ImageOps.fit(ph,(720,870));im.paste(ph,(0,365))
  shade=Image.new('RGBA',(720,1280));sd=ImageDraw.Draw(shade)
  for yy in range(920,1240):sd.line((0,yy,720,yy),fill=(3,17,28,round((yy-920)/320*230)))
  im=Image.alpha_composite(im.convert('RGBA'),shade).convert('RGB');d=ImageDraw.Draw(im)
  tag(d,'6 अप्रैल 1930',360,410,GOLD,34)
  # Symbolic letters build; do not imply that the salt tax was repealed that day.
  text(d,'गांधीजी ने नमक कानून तोड़ा',360,1020,39,WHITE)
  tag(d,'अंग्रेजी राज का अहिंसक विरोध',360,1100,GOLD,28)
  text(d,'AI से बना सांकेतिक दृश्य • ऐतिहासिक फोटो नहीं',360,1165,18,WHITE)
 brand(im);p.title(im,titles[k],t,294,GOLD if k!=3 else CYAN,59)
 d=ImageDraw.Draw(im)
 if k<3:text(d,'सांकेतिक शिक्षण दृश्य • माप व आकार वास्तविक नहीं',360,1180,18,'#afc3d1')
 for j in range(4):
  xx=44+j*163;d.rounded_rectangle((xx,1230,xx+146,1236),3,fill='#28485e')
  if j<=k:d.rounded_rectangle((xx,1230,xx+146*(min(1,t/ds[k]) if j==k else 1),1236),3,fill=GOLD)
 return im
out=ROOT/'preview_notes_safe_v2.mp4'
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','18','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
for fi in range(math.ceil(total*FPS)):
 tt=fi/FPS;k=max(i for i,s in enumerate(starts) if s<=tt);proc.stdin.write(frame(k,tt-starts[k]).tobytes())
proc.stdin.close();assert proc.wait()==0
check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=.15:pix_th=.1','-f','null','-'],capture_output=True,text=True)
assert check.returncode==0 and 'black_start:' not in check.stderr
sheet=Image.new('RGB',(1440,2560))
for k in range(4):sheet.paste(frame(k,ds[k]*.6),((k%2)*720,(k//2)*1280))
sheet.thumbnail((1000,1800));sheet.save(ROOT/'review_sheet.jpg',quality=92)
review={'duration':total,'scene_seconds':ds,'voice':e._CACHE.get('voice_used'),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'speech':lines,'build_only':True,'sources':['https://rajghat.gov.in/chronology','https://www.gandhiheritageportal.org/dandi-march-details','https://www.publicationsdivision.nic.in/catalog/view/theme/default/images/new_ngm_final/timeline/pages/page14.html'],'visuals':['rotating projected 3D salt crystals','moving symbolic tax coins','two animated bowls','geographic coastal map with schematic journey line','labelled AI historical illustration'],'map_source':p.c.GEO,'map_note':'Regional geographic coastline, not a political boundary map. Journey line schematic, not a surveyed exact path.','historical_image':'AI illustration, explicitly labelled; not an archival photo','tax_note':'No claim that the salt tax was repealed on 6 April 1930'}
(ROOT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
print(json.dumps(review,ensure_ascii=False))
