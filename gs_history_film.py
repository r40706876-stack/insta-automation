"""Cinematic history pipeline: original script, real Blender inserts and geographic storytelling."""
import os,sys,math,json,io,wave,hashlib,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps,ImageEnhance
ROOT=Path(os.environ.get('GS_FILM_ROOT','experiments/meerut_delhi_film'));ROOT.mkdir(parents=True,exist_ok=True)
W,H,FPS=720,1280,30
GOLD='#ffdb87';CYAN='#69dbdf';WHITE='#f5eedc';RED='#ff9b78'
SPEECH=[
 'बगावत मेरठ में हुई। फिर सिपाही दिल्ली क्यों पहुँचे?',
 'नौ मई, अठारह सौ सत्तावन। मेरठ में पचासी सिपाहियों को सज़ा मिली।',
 'दस मई: विद्रोह भड़का। साथियों को छुड़ाकर सिपाही दिल्ली की ओर बढ़े।',
 'ग्यारह मई: दिल्ली पहुँचकर उन्होंने बहादुर शाह ज़फ़र से नेतृत्व माँगा।',
 'ज़फ़र मुगल बादशाह थे। साझा नेतृत्व का प्रतीक। हर मोर्चे के सेनापति नहीं।',
 'याद रखो: नौ सज़ा, दस मेरठ का विद्रोह, ग्यारह दिल्ली। दोस्त से यही क्रम पूछो।']
HEAD=['मेरठ की बगावत दिल्ली क्यों गई?','9 मई 1857 • मेरठ','10 मई • कैद से विद्रोह तक','11 मई • दिल्ली पहुँचे','एक नाम, साझा नेतृत्व का प्रतीक','9 / 10 / 11 मई : कहानी याद रखो']
EARTH='https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg'
SOURCES=['https://www.cbse.gov.in/cbsenew/ebooks/ANO-SD-SW.pdf','https://sathee.iitk.ac.in/sathee-railway-exams/student-corner/general-knowledge/indian-history/revolt-1857/','https://www.pib.gov.in/newsite/erelcontent.aspx?lang=2&reg=48&relid=27529']
def download(url,path):
 import requests
 if not path.exists():
  r=requests.get(url,timeout=90);r.raise_for_status();path.write_bytes(r.content)
def prepare():
 import auto_poster as e
 import daily_visual_gs as voices
 e.resolve_font();e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+8%';e.VOICE_PITCH='+0Hz'
 e._TTS_STYLE[0]='Speak clear engaging Hindi as a male history storyteller. Speech only. No music, humming, filler or singing.'
 old=json.loads((ROOT/'audio.json').read_text()) if (ROOT/'audio.json').exists() else {}
 if old.get('speech')!=SPEECH or not (ROOT/'voice.wav').exists():
  try:
   chunks=[];labels=[]
   for line in SPEECH:
    arr,label=voices.gemini_male_once([line],0);chunks.append(arr);labels.append(label)
   label='Gemini Charon (male) per-scene: '+', '.join(sorted(set(labels)))
  except Exception as exc:
   print('Gemini unavailable:',str(exc)[:140]);e.USE_GEMINI_TTS=False
   chunks=[v[0] for v in e.make_voices([{'segs':[(None,None,x)]} for x in SPEECH],0)];label=e._CACHE.get('voice_used')
  chunks=[e._compress_pauses(a,max_pause=.22)[0] for a in chunks]
  assert all(len(a)>e.SR and np.max(np.abs(a))>.005 for a in chunks)
  ds=[max(4.5,len(a)/e.SR+.35) for a in chunks];starts=np.cumsum([0]+ds[:-1]);total=sum(ds)
  mix=np.zeros(math.ceil(total*e.SR),np.float32)
  for a,t in zip(chunks,starts):e.add_at(mix,a,float(t)+.1)
  with wave.open(str(ROOT/'voice.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(e.SR);f.writeframes((np.clip(mix,-.97,.97)*32767).astype('<i2').tobytes())
  (ROOT/'audio.json').write_text(json.dumps({'speech':SPEECH,'seconds':ds,'voice':label},ensure_ascii=False,indent=2))
 art=ROOT/'meerut_night.jpg'
 if not art.exists():
  raw=e.cf_image('Cinematic historical educational illustration, a deserted 1857 north Indian military cantonment courtyard at dusk, old brick barracks, warm oil lanterns, a dark wrought iron prison gate in the foreground, atmospheric amber light and deep blue night haze, detailed natural sandstone and old iron textures, composition with depth and visual layers, dramatic restrained documentary look, no people, no faces, no modern buildings, no electric lighting, no national flags, no readable letters, no text. Vertical 9:16 composition.')
  if not raw:raise RuntimeError('Cinematic historical background unavailable; do not substitute a blank card')
  Image.open(io.BytesIO(raw)).convert('RGB').save(art,quality=95)
 download(EARTH,ROOT/'earth5400.jpg')
 download('https://raw.githubusercontent.com/google/fonts/main/ofl/mukta/Mukta-ExtraBold.ttf',ROOT/'Mukta.ttf')
 print('PREPARED',json.loads((ROOT/'audio.json').read_text()))
if '--prepare' in sys.argv:prepare();raise SystemExit(0)
FONT=ROOT/'Mukta.ttf'
def font(n):return ImageFont.truetype(str(FONT),n)
def text(d,s,x,y,n=34,col=WHITE):
 while d.textlength(s,font=font(n))>640:n-=1
 d.text((x+2,y+3),s,font=font(n),fill='#071318',anchor='mm',stroke_width=2)
 d.text((x,y),s,font=font(n),fill=col,anchor='mm')
def ease(q):q=max(0,min(1,q));return q*q*(3-2*q)
def tag(d,s,x,y,n=29,col=GOLD):
 width=d.textlength(s,font=font(n))+36
 d.rounded_rectangle((x-width/2,y-27,x+width/2,y+27),12,fill='#162329',outline=col,width=2);text(d,s,x,y,n,col)
def flow(im,pts,t,progress=1,color=GOLD,width=5):
 progress=max(0,min(1,progress));n=max(2,round(1+(len(pts)-1)*progress));trail=pts[:n]
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);d.line(trail,fill=color,width=width*4,joint='curve');layer=layer.filter(ImageFilter.GaussianBlur(11));im.paste(layer,(0,0),layer)
 d=ImageDraw.Draw(im);d.line(trail,fill=color,width=width,joint='curve')
 for j in range(6):
  q=((t*.22+j/6)%1)*max(1,len(trail)-1);a=min(len(trail)-2,int(q));v=q-a
  x=trail[a][0]*(1-v)+trail[a+1][0]*v;y=trail[a][1]*(1-v)+trail[a+1][1]*v
  d.ellipse((x-3,y-3,x+3,y+3),fill=WHITE)
def shade(im):
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer)
 for y in range(H):
  alpha=int(210*max(0,1-y/450)+210*max(0,(y-900)/380))
  d.line((0,y,W,y),fill=(4,13,19,alpha))
 return Image.alpha_composite(im.convert('RGBA'),layer).convert('RGB')
# Maps are geographic backgrounds. No modern political borders are superimposed on 1857.
earth=Image.open(ROOT/'earth5400.jpg').convert('RGB')
def crop_geo(bounds):
 lo,la,hi,ha=bounds
 return earth.crop(((lo+180)/360*earth.width,(90-ha)/180*earth.height,(hi+180)/360*earth.width,(90-la)/180*earth.height))
wide=crop_geo((67,8,94,36));wide=ImageOps.fit(wide,(W,H));wide=ImageEnhance.Color(wide).enhance(.65);wide=ImageEnhance.Brightness(wide).enhance(.56)
# Close geographic inset retains only two precise city positions and a schematic route.
base=crop_geo((76.9,28.3,78,29.35)).resize((1000,1000),Image.Resampling.LANCZOS)
base=ImageEnhance.Color(base).enhance(.45);base=ImageEnhance.Brightness(base).enhance(.63)
rng=np.random.default_rng(1857);noise=rng.normal(0,1.7,(1000,1000,1));base=Image.fromarray(np.clip(np.asarray(base,float)+noise,0,255).astype(np.uint8))
CITY={'मेरठ':(77.7064,28.9845),'दिल्ली':(77.2373,28.6562)}
def modelpoint(lon,lat):return((lon-76.9)/1.1*1000,(29.35-lat)/1.05*1000)
def mapshot(t,progress=1,overview=False):
 im=wide.copy()
 # Perspective camera over a real raster; labels remain screen-readable.
 lean=.045*math.sin(t*.3);quad=[(-135+lean*100,410),(850+lean*100,345),(830,1160),(-90,1215)]
 src=[(0,0),(1000,0),(1000,1000),(0,1000)]
 # H maps map coordinates to screen pixels, supporting exact pin placement.
 mat=[];rhs=[]
 for (x,y),(u,v) in zip(src,quad):
  mat.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]);rhs.extend([u,v])
 h=np.append(np.linalg.solve(mat,rhs),1).reshape(3,3);inv=np.linalg.inv(h);inv/=inv[2,2]
 tile=base.transform((W,H),Image.Transform.PERSPECTIVE,inv.flatten()[:8],Image.Resampling.BICUBIC)
 im=Image.blend(im,tile,.88)
 def screen(pt):
  a=h@np.array([*pt,1]);return tuple(a[:2]/a[2])
 pins={name:screen(modelpoint(*ll)) for name,ll in CITY.items()}
 a=pins['मेरठ'];b=pins['दिल्ली']
 pts=[]
 for q in np.linspace(0,1,70):pts.append((a[0]*(1-q)+b[0]*q+26*math.sin(q*math.pi),a[1]*(1-q)+b[1]*q))
 d=ImageDraw.Draw(im);d.line(pts,fill='#78816b',width=3)
 if progress>0:flow(im,pts,t,progress)
 d=ImageDraw.Draw(im)
 for name,(x,y) in pins.items():
  rr=10+5*math.sin(t*3);d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=GOLD,width=2);d.ellipse((x-5,y-5,x+5,y+5),fill=GOLD)
  tag(d,name,x+(0 if name=='मेरठ' else 15),y-50,33)
 text(d,'उत्तर',633,420,25,CYAN)
 text(d,'भौगोलिक स्थान सही • यात्रा-पथ सांकेतिक',360,1060,20,WHITE)
 text(d,'पृष्ठभूमि: NASA Blue Marble • आधुनिक भू-दृश्य',360,1090,17,'#c7c5b7')
 return shade(im)
photo=Image.open(ROOT/'meerut_night.jpg').convert('RGB')
fort_art=Image.open(ROOT/'delhi_arrival.jpg').convert('RGB')
def arrival(t,duration):
 # Separate foreground and background camera motion, dust and light; illustration is labelled.
 ph=ImageOps.fit(fort_art,(W,H));z=1+.055*ease(t/duration)
 back=ImageOps.fit(ph.resize((round(W*z),round(H*z)),Image.Resampling.LANCZOS),(W,H))
 # Near paving moves slightly faster than the gateway, producing restrained depth parallax.
 front=ImageOps.fit(ph.resize((round(W*(z+.015)),round(H*(z+.015))),Image.Resampling.LANCZOS),(W,H))
 mask=Image.new('L',(W,H));md=ImageDraw.Draw(mask)
 for y in range(900,H):md.line((0,y,W,y),fill=round(255*(y-900)/(H-900)))
 back=Image.composite(front,back,mask)
 layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
 for j in range(24):
  x=(j*113+t*8)%W;y=600+(j*73-t*13)%530
  d.ellipse((x,y,x+2,y+2),fill=(255,212,143,105))
 return shade(Image.alpha_composite(back.convert('RGBA'),layer).convert('RGB'))
audio=json.loads((ROOT/'audio.json').read_text());ds=audio['seconds'];starts=np.cumsum([0]+ds[:-1]).tolist();total=sum(ds)
# Decode genuine rendered 3D inserts; no static-image replacement permitted.
clips={}
for shot in ('chains','fort'):
 folder=ROOT/shot
 if not list(folder.glob('frame_*.png')):
  subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/(shot+'.mp4')),str(folder/'frame_%04d.png')],check=True)
 files=sorted(folder.glob('frame_*.png'));assert len(files)>=40,shot+' incomplete 3D animation'
 clips[shot]=[Image.open(f).convert('RGB').copy() for f in files]
def shot(name,t):
 arr=clips[name];x=max(0,min(len(arr)-1,t/4*(len(arr)-1)));i=int(x);j=min(i+1,len(arr)-1)
 return Image.blend(arr[i],arr[j],x-i).resize((W,H),Image.Resampling.LANCZOS)
def brand(im,k,t):
 d=ImageDraw.Draw(im);text(d,'MINUTE ME GS • इतिहास की कहानी',244,58,22,CYAN)
 d.rounded_rectangle((44,113,645,199),12,fill='#12252c',outline='#497d81',width=2)
 text(d,'सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं',345,137,23,WHITE)
 text(d,'WhatsApp: +91 89892 79637',345,175,29,GOLD)
 title=HEAD[k];n=47
 if k==0:
  text(d,'मेरठ में बगावत…',360,271,55,GOLD);text(d,'फिर दिल्ली क्यों?',360,335,58,WHITE)
 else:text(d,title,360,282,n,GOLD)
 for j in range(6):
  x=45+j*105;d.rounded_rectangle((x,1218,x+93,1223),2,fill='#35494c')
  if j<=k:d.rounded_rectangle((x,1218,x+93*(min(1,t/ds[k]) if j==k else 1),1223),2,fill=GOLD)
def frame(k,t):
 if k==0:
  im=mapshot(t,ease(t/3));d=ImageDraw.Draw(im)
  tag(d,'1857',360,445,39,CYAN)
  text(d,'एक छावनी से मुगल दरबार तक',360,1130,34,WHITE)
 elif k==1:
  z=1+.07*ease(t/ds[k]);ph=ImageOps.fit(photo,(W,H));ph=ph.resize((round(W*z),round(H*z)),Image.Resampling.LANCZOS);im=shade(ImageOps.fit(ph,(W,H)));d=ImageDraw.Draw(im)
  # A count rises into the factual total; the scenery is clearly labelled as illustration.
  value=round(85*ease(t/.9));text(d,str(value),360,620,165,GOLD)
  text(d,'सिपाहियों को सज़ा',360,770,47,WHITE)
  for j in range(17):
   if t>j*.025:
    x=125+j*29;d.line((x,850,x,920),fill='#89abb4',width=3)
  tag(d,'मेरठ',360,1000,33,CYAN)
  text(d,'AI से बना सांकेतिक छावनी-दृश्य',360,1130,20,WHITE)
 elif k==2:
  im=shade(shot('chains',min(4,t/ds[k]*4)));d=ImageDraw.Draw(im)
  tag(d,'कैद साथियों को छुड़ाया',360,425,36,CYAN)
  if t>ds[k]*.5:text(d,'अगला कदम: दिल्ली',360,1080,40,GOLD)
  text(d,'मुक्ति का सांकेतिक 3D दृश्य',360,1150,19,WHITE)
 elif k==3:
  u=t/ds[k]
  if u<.57:im=mapshot(t,ease(u/.52));d=ImageDraw.Draw(im);tag(d,'रातभर दिल्ली की ओर',360,1125,31,CYAN)
  else:
   model=shade(shot('fort',4*ease((u-.57)/.43)))
   q=ease((u-.66)/.16);im=Image.blend(model,arrival(t,ds[k]),q);d=ImageDraw.Draw(im)
   tag(d,'बहादुर शाह ज़फ़र',360,410,35,GOLD)
   text(d,'नेतृत्व की माँग',360,1090,39,WHITE)
   text(d,'AI पुनर्निर्माण और सांकेतिक 3D मॉडल',360,1150,18,WHITE)
 elif k==4:
  im=arrival(t,ds[k]);d=ImageDraw.Draw(im)
  tag(d,'मुगल बादशाह • बहादुर शाह ज़फ़र',360,420,31,GOLD)
  for j,(s,col) in enumerate([('साझे नेतृत्व का प्रतीक',GOLD),('हर मोर्चे के सेनापति नहीं',CYAN)]):
   if t>j*1.3:
    y=940+j*105;d.rounded_rectangle((58,y-37,662,y+37),12,fill='#10252c',outline=col,width=2);text(d,s,360,y,36,col)
  text(d,'AI से बना सांकेतिक दृश्य • ऐतिहासिक फोटो नहीं',360,1155,17,WHITE)
 else:
  im=mapshot(t,1);overlay=Image.new('RGBA',(W,H),(4,15,20,135));im=Image.alpha_composite(im.convert('RGBA'),overlay).convert('RGB');d=ImageDraw.Draw(im)
  rows=[('9 मई','सज़ा • मेरठ'),('10 मई','विद्रोह • मेरठ'),('11 मई','दिल्ली • ज़फ़र से नेतृत्व की माँग')]
  for j,(date,event) in enumerate(rows):
   y=470+j*190;q=ease((t-j*.5)/.5);xx=int(45-(1-q)*90)
   d.rounded_rectangle((xx,y-50,xx+630,y+90),15,fill='#12292e',outline=GOLD if t>j*1.6 else '#5e7779',width=2)
   text(d,date,xx+315,y-10,43,GOLD);text(d,event,xx+315,y+45,32,WHITE)
   if j<2:d.line((360,y+100,360,y+128),fill=GOLD,width=4)
  text(d,'दोस्त से पूछो: किस दिन क्या हुआ?',360,1080,33,CYAN)
  text(d,'इतिहास की अगली कहानी के लिए फॉलो करो',360,1140,27,WHITE)
 brand(im,k,t)
 return im
# Shot transitions retain geographic and temporal continuity.
def finalframe(k,t):
 im=frame(k,t)
 if k>0 and t<.22:im=Image.blend(frame(k-1,ds[k-1]-.01),im,ease(t/.22))
 return im
out=ROOT/'history_story_notes_safe_v2.mp4'
if '--sheet' not in sys.argv:
 proc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r',str(FPS),'-i','-','-i',str(ROOT/'voice.wav'),'-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for f in range(math.ceil(total*FPS)):
  tt=f/FPS;k=max(i for i,x in enumerate(starts) if x<=tt);proc.stdin.write(finalframe(k,tt-starts[k]).tobytes())
 proc.stdin.close();assert proc.wait()==0
 check=subprocess.run(['ffmpeg','-hide_banner','-i',str(out),'-vf','blackdetect=d=.15:pix_th=.1','-f','null','-'],capture_output=True,text=True)
 assert check.returncode==0 and 'black_start:' not in check.stderr
sheet=Image.new('RGB',(1440,3840))
for k in range(6):sheet.paste(frame(k,ds[k]*.65),((k%2)*720,(k//2)*1280))
sheet.thumbnail((1000,2667));sheet.save(ROOT/'review_sheet.jpg',quality=93)
review={'duration':total,'scene_seconds':ds,'speech':SPEECH,'voice':audio['voice'],'renderer':'Blender 4.2 Eevee actual animated iron links and fort architecture; geographic perspective maps; original AI historical background; Pillow compositing','image_source':'Built-in imagegen historical reconstructions; no archival photo claim','source_reference':'User supplied 160.937s study reference; technique studied, no source footage or script copied','build_only':True,'sources':SOURCES,'map_source':EARTH,'map_note':'Modern physical geography for location only; no 1857 political borders. Travel path schematic.','share_hypothesis':'Retell three consecutive dates with places and event roles, then quiz a study partner. Not verified audience performance.','sha256':hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else None}
(ROOT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2));print(json.dumps(review,ensure_ascii=False))
