"""Build-only animated coastal breeze lesson. No Instagram publication path."""
import os,json,math,hashlib,subprocess,shutil,datetime
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('experiments/viewer_seabreeze_story_v3');ROOT.mkdir(parents=True,exist_ok=True)
os.environ['GS_VISUAL_OUTPUT']=str(ROOT)
os.environ['GS_FORCE_BUILD']='1'
os.environ['GS_TARGET_DATE']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30))).date().isoformat()
import daily_visual_gs as v
import gs_scene_stage as motion
import gs_publication as promo
import auto_poster as e
INK='#183b50';BLUE='#087fba';GOLD='#e99830';TEAL='#058d96'
def font(n):return ImageFont.truetype('Mukta-ExtraBold.ttf',n)
def label(d,s,x,y,n=30,c=INK):d.text((x,y),s,font=font(n),fill=c,anchor='mm')
def blend(a,b,p):return tuple(round(x+(y-x)*p) for x,y in zip(a,b))
def scene_sky(night):
 im=Image.new('RGB',(660,650));d=ImageDraw.Draw(im)
 top=blend((132,210,237),(26,48,87),night);bottom=blend((232,247,246),(100,130,155),night)
 for y in range(650):d.line((0,y,660,y),fill=blend(top,bottom,y/650))
 return im
def sunmoon(d,night,t):
 if night<.85:
  x,y,r=580,80+70*night,30
  for j in range(10):
   a=j*math.tau/10+t*.12
   d.line((x+39*math.cos(a),y+39*math.sin(a),x+49*math.cos(a),y+49*math.sin(a)),fill='#ffe798',width=4)
  d.ellipse((x-r,y-r,x+r,y+r),fill='#ffdb6e')
 if night>.4:
  for j in range(15):
   x=35+(j*113)%570;y=32+(j*71)%200;r=1+(j%2)
   d.ellipse((x-r,y-r,x+r,y+r),fill='#e7f3fa')
  d.ellipse((548,45,608,105),fill='#fff1c1')
  d.ellipse((565,40,616,91),fill='#233c62')
def person(d,x,y,wind,t):
 d.ellipse((x-10,y-80,x+10,y-60),fill='#e9b287',outline=INK,width=2)
 d.line((x,y-59,x,y-30),fill='#ed6963',width=13)
 d.line((x,y-33,x-13,y,x+2,y-29,x+15,y),fill=INK,width=5)
 # A scarf follows the surface wind; it is not a decorative unrelated motion.
 pts=[(x+wind*j*9,y-53+3*math.sin(t*5+j)) for j in range(6)]
 d.line(pts,fill='#ffca45',width=6)
 d.line((x,y-52,x+14,y-40),fill=INK,width=5)
def coast(t,night=0,detail=True):
 im=scene_sky(night);d=ImageDraw.Draw(im);sunmoon(d,night,t)
 sea=blend((39,157,195),(28,88,128),night)
 d.rectangle((0,425,660,650),fill=sea)
 d.polygon([(330,425),(440,405),(660,420),(660,650),(330,650),(295,550)],fill=blend((237,202,135),(145,150,159),night))
 d.polygon([(330,425),(347,428),(312,550),(348,650),(330,650),(295,550)],fill='#d3eff0')
 for j in range(7):
  yy=445+j*29
  pts=[(xx,yy+3*math.sin(xx*.05+t*2+j)) for xx in range(0,290,5)]
  d.line(pts,fill='#92d7e3' if night<.5 else '#68a9bc',width=2)
 # A boat rocks on waves without suggesting that it measures the wind.
 bx=100+5*math.sin(t*.7);by=535+4*math.sin(t*2)
 d.polygon([(bx-45,by),(bx+40,by),(bx+24,by+22),(bx-27,by+22)],fill='#fff1ce')
 d.line((bx,by,bx,by-55),fill=INK,width=3)
 d.polygon([(bx+3,by-53),(bx+3,by-4),(bx+35,by-4)],fill='#ef7667')
 # Village silhouette and palm bending gently; all stay inside the stage.
 d.rounded_rectangle((535,505,615,565),4,fill='#fff0ce',outline=INK,width=2)
 d.polygon([(522,505),(574,466),(627,505)],fill='#d77760')
 d.rectangle((566,535,585,565),fill='#45646d')
 d.line((475,572,480,485,490,454),fill='#8a6b42',width=9)
 for j in range(5):
  a=-math.pi+j*.66+.08*math.sin(t*2)
  d.line((490,454,490+55*math.cos(a),454+28*math.sin(a)),fill='#21866f',width=8)
 if detail:person(d,418,569,-1 if night>.5 else 1,t)
 label(d,'समुद्र',145,610,30,'#e2f8ff')
 label(d,'जमीन',505,610,30,INK if night<.5 else '#f6f6e8')
 return im
def stream(d,points,t,c,width=6,reverse=False):
 if reverse:points=points[::-1]
 d.line(points,fill=c,width=width,joint='curve')
 motion.arrow(d,points[-3],points[-1],c)
 # Arc-length interpolation keeps direction and speed consistent on turns.
 lengths=[0]
 for a,b in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(a,b))
 for j in range(7):
  at=((t*.22+j/7)%1)*lengths[-1]
  k=next((i for i in range(len(points)-1) if lengths[i+1]>=at),len(points)-2)
  p=(at-lengths[k])/max(.01,lengths[k+1]-lengths[k]);a,b=points[k],points[k+1]
  x=a[0]+(b[0]-a[0])*p;y=a[1]+(b[1]-a[1])*p
  d.ellipse((x-5,y-5,x+5,y+5),fill='white',outline=c,width=2)
def thermometer(d,x,y,amount,c):
 d.rounded_rectangle((x-9,y-75,x+9,y+35),9,fill='#fff9e8',outline=INK,width=2)
 d.rectangle((x-4,y+25-90*amount,x+4,y+35),fill=c)
 d.ellipse((x-14,y+24,x+14,y+52),fill=c,outline=INK,width=2)
def hero(d,x,feet,t,hop=False,cool=False,scale=1):
 # Articulated limbs and facial reaction, rather than a moving stick figure.
 lift=(max(0,math.sin(t*7))*38 if hop else 0)*scale
 y=feet-lift;head=y-210*scale;skin='#eeb48e';shirt='#f06a5b'
 def pt(dx,dy):return(x+dx*scale,y+dy*scale)
 # Shadow stays on the sand as the body rises.
 d.ellipse((x-43*scale,feet-8,x+43*scale,feet+9),fill='#c19a62')
 knee=math.sin(t*7)*24 if hop else 0
 d.line([pt(-13,-65),pt(-26,-30-knee*.5),pt(-43,-3-knee)],fill='#25475a',width=max(3,int(17*scale)))
 d.line([pt(15,-65),pt(33,-31+knee*.3),pt(45,0+knee*.5)],fill='#25475a',width=max(3,int(17*scale)))
 for dx,dy in [(-43,-3-knee),(45,knee*.5)]:
  xx,yy=pt(dx,dy);d.ellipse((xx-14*scale,yy-6*scale,xx+16*scale,yy+8*scale),fill=skin,outline='#a56c51',width=2)
 d.rounded_rectangle((*pt(-33,-157),*pt(33,-62)),int(14*scale),fill=shirt,outline='#b8433c',width=max(2,int(2*scale)))
 for sign in (-1,1):
  end=-174 if hop else -93
  d.line([pt(sign*30,-144),pt(sign*58,-124 if not hop else -160),pt(sign*72,end)],fill=skin,width=max(3,int(12*scale)))
 d.ellipse((x-29*scale,head-35*scale,x+29*scale,head+30*scale),fill=skin,outline='#795c4d',width=2)
 d.pieslice((x-32*scale,head-42*scale,x+32*scale,head+6*scale),180,355,fill='#263d49')
 for sign in (-1,1):
  xx=x+sign*11*scale
  if cool:d.arc((xx-5*scale,head-4*scale,xx+5*scale,head+6*scale),185,350,fill=INK,width=2)
  else:d.ellipse((xx-3*scale,head-3*scale,xx+3*scale,head+4*scale),fill=INK)
 if hop:
  d.ellipse((x-6*scale,head+10*scale,x+6*scale,head+23*scale),fill='#963f36')
 else:d.arc((x-12*scale,head+5*scale,x+12*scale,head+23*scale),0,180,fill='#963f36',width=3)
 # Large, readable scarf streams in the onshore wind.
 pts=[pt(9+j*13,-163+7*math.sin(t*6+j*.65)) for j in range(7)]
 if cool:d.line(pts,fill='#ffd55b',width=max(4,int(12*scale)),joint='curve')
 else:d.line([pt(5,-164),pt(15,-129),pt(9,-113)],fill='#ffd55b',width=max(4,int(10*scale)))
def camera(panel,factor,center):
 cw,ch=round(660/factor),round(650/factor)
 cx,cy=center;left=max(0,min(660-cw,round(cx-cw/2)));top=max(0,min(650-ch,round(cy-ch/2)))
 return panel.crop((left,top,left+cw,top+ch)).resize((660,650),Image.Resampling.LANCZOS)
def render(sc,t,duration):
 phase=sc['animation']['phase'];p=max(0,min(1,t/max(.1,duration-.2)))
 im=Image.new('RGB',(720,1280),'#f6f3ea')
 panel=coast(t,0,False);pd=ImageDraw.Draw(panel)
 # One coherent coastal location with different camera shots.
 if phase=='question':
  hot=t<duration*.58
  hero(pd,414,600,t,hop=hot,cool=not hot,scale=.9)
  if hot:
   for j in range(4):
    xx=365+j*31;yy=595-((t*65+j*19)%58)
    pd.arc((xx,yy,xx+19,yy+25),210,340,fill='#df693d',width=3)
  else:
   for j in range(4):
    xx=180+((t*150+j*67)%220);yy=380+j*24
    pd.arc((xx,yy,xx+85,yy+15),180,345,fill=BLUE,width=4)
  label(pd,'आह! गरम रेत!' if hot else 'अरे… ठंडी हवा!',300,140,38,'#a94b27' if hot else BLUE)
  panel=camera(panel,1.12+.08*math.sin(p*math.pi),(390,370))
 elif phase=='explain':
  # A close view, then follow the warming air upward. No unrelated icons.
  pd.polygon([(345,425),(440,405),(655,420),(655,458),(345,458)],fill='#ef9369')
  for j in range(16):
   xx=370+(j*37)%245;yy=410-((t*80+j*29)%240)
   pd.ellipse((xx-6,yy-6,xx+6,yy+6),fill='#ed9b4b')
  stream(pd,[(510,398),(510,295),(510,180)],t,GOLD,10)
  label(pd,'धूप से जमीन गरम',350,85,38,'#a95127')
  label(pd,'गरम हवा ऊपर उठी',340,145,36,'#a95127')
  panel=camera(panel,1.18,(405,325-35*p))
 elif phase=='demonstrate':
  hero(pd,430,600,t,cool=True,scale=.95)
  for j in range(6):
   xx=20+((t*155+j*88)%380);yy=340+j*22
   pd.arc((xx,yy,xx+86,yy+18),185,350,fill='#eefaff',width=5)
  stream(pd,[(70,360),(240,360),(395,360)],t,BLUE,9)
  label(pd,'समुद्र की ठंडी हवा आई',330,125,37,BLUE)
  panel=camera(panel,1.08+.13*motion.ease(p),(365+40*p,365))
 else:
  hero(pd,430,600,t,cool=True,scale=.85)
  stream(pd,[(535,395),(535,285),(535,205)],t,GOLD,8)
  stream(pd,[(70,365),(250,365),(395,365)],t,BLUE,8)
  label(pd,'गरम हवा ऊपर',350,125,37,'#a95127')
  label(pd,'ठंडी हवा हमारी तरफ',310,305,35,BLUE)
 im.paste(panel,(30,340));d=ImageDraw.Draw(im)
 label(d,'समुद्र से आने वाली हवा: समुद्री समीर' if phase=='recall' else 'दिन का दृश्य',360,1036,28,TEAL)
 return im
original_validate=motion.validate
def validate(sc):
 m=sc.get('animation',{})
 if m.get('type')!='seabreeze':return original_validate(sc)
 assert m.get('phase') in ('question','explain','demonstrate','recall')
 assert len(m.get('labels',[]))==2
 return m
motion.validate=validate;motion.render=render
reference={'question':'Why can coastal surface wind reverse between day and night?','explanation':'Idealized local circulation: land generally warms and cools faster than nearby water. Daytime sea breeze flows inland at the surface, with rising air over warm land and return flow aloft. With cooler land at night a land breeze can flow offshore, with return flow aloft. Larger-scale winds can prevent or modify this pattern; it is not guaranteed every night.','sources':['https://www.noaa.gov/jetstream/ocean/sea-breeze']}
lines=[
 ('पैर गरम… हवा ठंडी?','अरे! रेत इतनी गरम, फिर ये हवा ठंडी कैसे?'),
 ('जमीन से शुरू होती है बात','धूप में जमीन जल्दी गरम होती है। ऊपर की हवा भी गरम होकर उठती है।'),
 ('अब हवा का रास्ता देखो','तब समुद्र की ठंडी हवा जमीन की तरफ आती है। यही हवा हमें ठंडक देती है।'),
 ('एक बार में याद रखो','गरम हवा ऊपर, समुद्र की हवा हमारी तरफ। यही समुद्री समीर है।')]
s={'ok':True,'title':'पैर जल रहे… हवा ठंडी कैसे?','renderer_version':motion.VERSION,'subject':'Geography','question_hash':hashlib.sha256(b'coastal-breeze-story-v3').hexdigest(),'reference':reference,'scenes':[{'label':a,'speech':b,'animation':{'type':'seabreeze','phase':phase,'labels':['समुद्र','जमीन']}} for (a,b),phase in zip(lines,['question','explain','demonstrate','recall'])]}
(ROOT/'script.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
# Capture the actual compressed scene timings for sound effects.
scene_lengths=[]
base_make_voices=e.make_voices
def timed_voices(*args,**kwargs):
 vv=base_make_voices(*args,**kwargs)
 scene_lengths[:]=[len(e._compress_pauses(q[0],max_pause=.22)[0])/e.SR+.35 for q in vv]
 return vv
e.make_voices=timed_voices
v.build();e.resolve_font()
# Quiet sand taps and a short wind texture. No humming or music.
import numpy as np,wave
with wave.open(str(ROOT/'voice.wav'),'rb') as w:
 rate=w.getframerate();n=w.getnframes()
fx=np.zeros(n,dtype=np.float32);rng=np.random.default_rng(27)
def sound(at,length,gain,wind=False):
 start=int(at*rate);count=min(int(length*rate),n-start)
 if count<=0:return
 noise=rng.standard_normal(count).astype(np.float32)
 noise=np.convolve(noise,np.ones(24 if wind else 5)/(24 if wind else 5),mode='same')
 env=np.sin(np.linspace(0,math.pi,count))**2 if wind else np.exp(-np.linspace(0,7,count))
 fx[start:start+count]+=noise*env*gain
sound(.24,.14,.12);sound(.7,.14,.1)
sound(sum(scene_lengths[:2])+.15,min(2.5,scene_lengths[2]-.3),.045,True)
with wave.open(str(ROOT/'effects.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((np.clip(fx,-.8,.8)*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'reel.mp4'),'-i',str(ROOT/'effects.wav'),'-filter_complex','[0:a][1:a]amix=inputs=2:duration=first:normalize=0:dropout_transition=0[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-movflags','+faststart',str(ROOT/'story_sound.mp4')],check=True)
manifest=json.loads((ROOT/'validated.json').read_text())
source=ROOT/'story_sound.mp4';original_duration=manifest['duration']
# Pace the entire scene and its narration together; preserve vocal pitch.
if original_duration<20:
 factor=20/original_duration;source=ROOT/'paced.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'story_sound.mp4'),'-vf',f'setpts={factor}*PTS','-af',f'atempo={1/factor}','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','19','-preset','fast','-c:a','aac','-movflags','+faststart',str(source)],check=True)
 manifest['duration']=20
final=promo.prepare_video(source,e.get_font)
shutil.copyfile(final,ROOT/'preview_with_whatsapp.mp4')
duration=manifest['duration']
check=subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/'preview_with_whatsapp.mp4'),'-f','null','-'],capture_output=True,text=True)
assert check.returncode==0,'Final branded video must decode'
sheet=Image.new('RGB',(1440,2560),'white')
for i,frac in enumerate((.12,.38,.64,.9)):
 jpg=ROOT/f'frame_{i}.jpg'
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(duration*frac),'-i',str(ROOT/'preview_with_whatsapp.mp4'),'-frames:v','1',str(jpg)],check=True)
 sheet.paste(Image.open(jpg).convert('RGB'),((i%2)*720,(i//2)*1280))
sheet.thumbnail((1000,1800));sheet.save(ROOT/'review_sheet.jpg',quality=88)
manifest.update(original_duration=original_duration,final_sha256=hashlib.sha256((ROOT/'preview_with_whatsapp.mp4').read_bytes()).hexdigest(),build_only=True,review_status='Needs visual editorial review; technical validation is not audience validation',whatsapp=promo.PHONE,source=reference['sources'],topic='Hot sand / cool wind: acted story, close-up, air mechanism')
(ROOT/'review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
