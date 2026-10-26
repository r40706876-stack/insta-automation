"""Build-only animated coastal breeze lesson. No Instagram publication path."""
import os,json,math,hashlib,subprocess,shutil,datetime
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('experiments/viewer_seabreeze_v1');ROOT.mkdir(parents=True,exist_ok=True)
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
def render(sc,t,duration):
 phase=sc['animation']['phase'];p=max(0,min(1,t/max(.1,duration-.2)))
 im=Image.new('RGB',(720,1280),'#f6f3ea');d=ImageDraw.Draw(im)
 if phase=='question':
  # Both directions are visible immediately, before narration explains why.
  for j,night in enumerate((0,1)):
   panel=coast(t,night);pd=ImageDraw.Draw(panel)
   stream(pd,[(90,380),(270,380),(540,380)],t,BLUE if not night else '#ffd46a',reverse=bool(night))
   label(pd,'दिन' if not night else 'रात',85,70,50,'#173f50' if not night else '#fff4c6')
   panel=panel.resize((660,325));im.paste(panel,(30,325+j*350))
  d=ImageDraw.Draw(im);label(d,'एक किनारा… हवा उलटी!',360,1052,33,TEAL)
 elif phase in ('explain','demonstrate'):
  night=0 if phase=='explain' else motion.ease(min(1,t/1.1))
  panel=coast(t,night);pd=ImageDraw.Draw(panel)
  label(pd,'दिन: जमीन जल्दी गर्म' if phase=='explain' else 'रात: जमीन जल्दी ठंडी',310,55,31,INK if phase=='explain' else '#fff3c9')
  # Strong near-surface branch, faint return branch: no implication of a fan.
  stream(pd,[(105,385),(300,385),(530,385)],t,BLUE if phase=='explain' else '#ffdb7d',reverse=phase=='demonstrate')
  if phase=='explain':
   stream(pd,[(530,360),(530,270),(500,205)],t,GOLD)
   stream(pd,[(470,180),(300,150),(120,180)],t,'#72a5b0',3)
   stream(pd,[(100,210),(90,290),(105,350)],t,'#72a5b0',3)
   thermometer(pd,610,300,.25+.65*motion.ease(p),GOLD)
   label(pd,'गर्म हवा ऊपर',405,245,29,'#995119')
   label(pd,'ठंडी हवा आती है',250,345,28,BLUE)
  else:
   stream(pd,[(105,360),(105,270),(135,205)],t,GOLD)
   stream(pd,[(160,180),(330,150),(535,180)],t,'#a6c5d2',3)
   stream(pd,[(550,210),(565,290),(540,350)],t,'#a6c5d2',3)
   thermometer(pd,610,300,.9-.65*motion.ease(p),BLUE)
   label(pd,'समुद्र अपेक्षाकृत गर्म',240,245,27,'#fff0bb')
   label(pd,'जमीन से समुद्र',330,345,30,'#fff0bb')
  im.paste(panel,(30,340));d=ImageDraw.Draw(im)
  label(d,'समुद्री समीर' if phase=='explain' else 'स्थलीय समीर',360,1032,38,BLUE if phase=='explain' else '#a56a21')
 else:
  # Final recall card carries the full useful rule, not just a request to share.
  for j,night in enumerate((0,1)):
   panel=coast(t,night,False);pd=ImageDraw.Draw(panel)
   stream(pd,[(90,365),(300,365),(540,365)],t,BLUE if not night else '#ffda6b',reverse=bool(night))
   panel=panel.resize((660,255));y=330+j*360;im.paste(panel,(30,y))
   d=ImageDraw.Draw(im)
   label(d,'दिन: समुद्र से = समुद्री समीर' if not night else 'रात: जमीन से = स्थलीय समीर',360,y+294,32,BLUE if not night else '#a56621')
  label(d,'नाम याद करो: हवा कहाँ से आई?',360,1068,30,TEAL)
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
 ('हवा ने रास्ता क्यों बदला?','समुद्र किनारे हवा दिन और रात में उलटी क्यों चल सकती है?'),
 ('दिन का रास्ता देखो','दिन में जमीन जल्दी गर्म होती है। गर्म हवा ऊपर उठे, तो समुद्र की ठंडी हवा आती है।'),
 ('रात होते ही फर्क','रात में जमीन जल्दी ठंडी होती है। हवा जमीन से समुद्र की ओर चल सकती है।'),
 ('याद रखने की आसान ट्रिक','आने की जगह से नाम याद करो: समुद्र से समुद्री समीर, जमीन से स्थलीय समीर।')]
s={'ok':True,'title':'दिन–रात हवा का रास्ता उलटा क्यों?','renderer_version':motion.VERSION,'subject':'Geography','question_hash':hashlib.sha256(b'coastal-breeze-v1').hexdigest(),'reference':reference,'scenes':[{'label':a,'speech':b,'animation':{'type':'seabreeze','phase':phase,'labels':['समुद्र','जमीन']}} for (a,b),phase in zip(lines,['question','explain','demonstrate','recall'])]}
(ROOT/'script.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
v.build();e.resolve_font()
manifest=json.loads((ROOT/'validated.json').read_text())
source=ROOT/'reel.mp4';original_duration=manifest['duration']
# Pace the entire scene and its narration together; preserve vocal pitch.
if original_duration<20:
 factor=20/original_duration;source=ROOT/'paced.mp4'
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(ROOT/'reel.mp4'),'-vf',f'setpts={factor}*PTS','-af',f'atempo={1/factor}','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-crf','19','-preset','fast','-c:a','aac','-movflags','+faststart',str(source)],check=True)
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
manifest.update(original_duration=original_duration,final_sha256=hashlib.sha256((ROOT/'preview_with_whatsapp.mp4').read_bytes()).hexdigest(),build_only=True,review_status='Needs visual editorial review; technical validation is not audience validation',whatsapp=promo.PHONE,source=reference['sources'],topic='Sea breeze and land breeze')
(ROOT/'review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
