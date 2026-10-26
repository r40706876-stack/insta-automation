"""Build-only rain-shadow retry: four distinct explanatory scenes, branded export."""
import os,json,math,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path('experiments/viewer_retry_rainshadow_v2')
ROOT.mkdir(parents=True,exist_ok=True)
os.environ['GS_VISUAL_OUTPUT']=str(ROOT)
os.environ['GS_FORCE_BUILD']='1'
os.environ['GS_TARGET_DATE']='2026-10-27'
import daily_visual_gs as v
import gs_scene_stage as motion
import gs_publication as promo
import auto_poster as e
BG='#edf7fa';INK='#183b50';TEAL='#058d96';BLUE='#278fc7';GOLD='#ffbd4b'
def f(n):return ImageFont.truetype('Mukta-ExtraBold.ttf',n)
def txt(d,s,x,y,n=30,c=INK):
 d.text((x,y),s,font=f(n),fill=c,anchor='mm')
def cloud(d,x,y,r=1,c='#ffffff'):
 for a,b,z in [(-35,6,30),(0,-8,38),(36,6,29)]:
  d.ellipse((x+(a-z)*r,y+(b-z)*r,x+(a+z)*r,y+(b+z)*r),fill=c)
 d.rounded_rectangle((x-60*r,y,x+61*r,y+30*r),12,fill=c)
def rain(d,x,y,t,w=130,h=210):
 for j in range(18):
  xx=x+(j*29)%w;yy=y+(j*47+t*210)%h
  d.line((xx,yy,xx-7,yy+17),fill=BLUE,width=4)
def tree(d,x,y,scale=1,dry=False):
 d.line((x,y,x,y-52*scale),fill='#79583c',width=max(2,int(8*scale)))
 if dry:
  for z in (-1,1):d.line((x,y-30*scale,x+z*22*scale,y-55*scale),fill='#79583c',width=4)
 else:
  for yy,rr in [(30,25),(49,20),(65,13)]:
   d.ellipse((x-rr*scale,y-(yy+rr)*scale,x+rr*scale,y-(yy-rr)*scale),fill='#239b75')
def home(d,x,y,c):
 d.rounded_rectangle((x-30,y-42,x+30,y),3,fill='#fff5d9',outline=INK,width=2)
 d.polygon([(x-40,y-42),(x,y-75),(x+40,y-42)],fill=c)
 d.rectangle((x-7,y-23,x+7,y),fill=INK)
def person(d,x,y,umbrella=False):
 d.ellipse((x-10,y-74,x+10,y-54),fill='#edb28c',outline=INK,width=2)
 d.line((x,y-54,x,y-23),fill=TEAL,width=12)
 for a in (-1,1):
  d.line((x,y-24,x+a*12,y),fill=INK,width=5)
  d.line((x,y-45,x+a*15,y-30),fill=INK,width=5)
 if umbrella:
  d.line((x+23,y-31,x+23,y-110),fill=INK,width=3)
  d.pieslice((x-22,y-140,x+68,y-70),180,360,fill='#ee5b66',outline=INK,width=2)
def air(d,x,y,t,wet=True,r=36):
 col=BLUE if wet else GOLD
 d.ellipse((x-r,y-r,x+r,y+r),fill='#dbf3fc' if wet else '#ffe9bc',outline=col,width=4)
 for j in range(6):
  a=j*math.tau/6+t
  xx=x+r*.58*math.cos(a);yy=y+r*.58*math.sin(a)
  d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=col)
def landscape(d,t,reverse=False):
 d.rounded_rectangle((25,320,695,1000),28,fill='#dff1f7')
 d.ellipse((548,350,620,422),fill='#ffd15b')
 for j in range(3):cloud(d,100+j*235+8*math.sin(t+j),385+j%2*25,.65,'#ffffff')
 d.polygon([(25,760),(200,660),(390,725),(695,675),(695,1000),(25,1000)],fill='#a6ceaa')
 d.polygon([(25,900),(300,490),(470,745),(695,870),(695,1000),(25,1000)],fill='#73aa9b')
 d.polygon([(300,490),(470,745),(695,870),(695,1000),(375,1000)],fill='#d9bd83')
 d.polygon([(300,490),(264,546),(320,535)],fill='#f5f5dd')
 d.polygon([(25,900),(200,770),(300,735),(400,810),(695,910),(695,1000),(25,1000)],fill='#61b58a')
 d.polygon([(365,790),(695,910),(695,1000),(420,1000)],fill='#eacb8c')
 d.polygon([(25,905),(98,903),(120,1000),(25,1000)],fill='#55bdd9')
 for j in range(5):
  y=917+j*17
  d.line((30+6*math.sin(t*2+j),y,85+6*math.sin(t*2+j),y),fill='#c7f5ff',width=3)
 for x,y in [(120,910),(170,875),(210,920)]:tree(d,x,y,.75)
 for x,y in [(510,920),(590,950)]:tree(d,x,y,.75,True)
 home(d,175,965,'#ee6c5e');home(d,585,965,'#b37b53')
 txt(d,'समुद्र',65,1038,27,BLUE)
 txt(d,'पहाड़',315,1038,27,TEAL)
 txt(d,'भीतरी इलाका',580,1038,27,'#a76b20')
def render(sc,t,duration):
 p=max(0,min(1,t/max(.1,duration-.4)));phase=sc['animation']['phase']
 im=Image.new('RGB',(720,1280),'#f6f3ea');d=ImageDraw.Draw(im)
 if phase=='question':
  # Two people, the same mountain crossing: the puzzle is visible without audio.
  landscape(d,t)
  cloud(d,166,590,1.05,'#789cb5');rain(d,95,630,t,140,240)
  person(d,150,885,True);person(d,570,895,False)
  d.rounded_rectangle((60,420,245,478),14,fill='#d6efff')
  txt(d,'यहाँ छाता!',152,450,32,BLUE)
  d.rounded_rectangle((455,460,658,518),14,fill='#ffe6ab')
  txt(d,'उधर सूखा?',555,490,32,'#a36916')
  # A bus travels the connecting road, rather than a static icon.
  x=200+360*p;y=850-65*math.sin(math.pi*p)
  d.line((190,870,330,790,580,885),fill='#eee5cc',width=22)
  d.rounded_rectangle((x-35,y-32,x+35,y),7,fill='#f9b63d',outline=INK,width=2)
  for j in (-1,0,1):d.rectangle((x+j*18-6,y-25,x+j*18+6,y-11),fill='#a2e4ee')
  for j in (-22,22):d.ellipse((x+j-7,y-7,x+j+7,y+7),fill=INK)
 elif phase=='explain':
  # Close view follows one moist parcel; cloud is assembled as it rises.
  d.rounded_rectangle((25,320,695,1000),28,fill='#dff1f7')
  d.polygon([(25,1000),(470,425),(695,1000)],fill='#79b298')
  d.polygon([(470,425),(695,1000),(555,1000)],fill='#548c86')
  d.rectangle((25,920,145,1000),fill='#41b2d5')
  q=min(1,p*1.7);x=100+290*q;y=875-350*q
  points=[(100+290*i/40,875-350*i/40) for i in range(41)]
  d.line(points,fill='#ffffff',width=10)
  motion.arrow(d,points[-5],points[-1],BLUE)
  air(d,x,y,t,True,r=54-18*q)
  # Thermometer visibly falls without fabricated temperatures.
  d.rounded_rectangle((565,520,593,775),13,fill='white',outline=INK,width=3)
  d.rectangle((574,750-185*(1-q),584,775),fill=BLUE)
  d.ellipse((558,760,600,802),fill=BLUE)
  txt(d,'ठंडी',580,486,28,BLUE)
  if p>.3:
   z=motion.ease((p-.3)/.35)
   cloud(d,330,520,z,'#789cb5')
   if p>.55:rain(d,245,565,t,140,265)
  txt(d,'नम हवा ऊपर चढ़ी',258,365,34,TEAL)
  txt(d,'ठंडी हुई → बादल बने',310,870,31,BLUE)
  txt(d,'पर्याप्त नमी हो तो बारिश',350,1040,28,BLUE)
 elif phase=='demonstrate':
  # Follow the parcel on the other slope; warm expansion is visible.
  landscape(d,t)
  cloud(d,180,585,.8,'#789cb5');rain(d,125,625,t,100,180)
  q=motion.ease(p);x=340+260*q;y=550+300*q
  d.line([(340,550),(420,640),(500,745),(600,850)],fill='#fff6ce',width=10)
  motion.arrow(d,(550,800),(600,850),GOLD)
  air(d,x,y,t,False,32+28*q)
  # Fewer cloud fragments fade as descending air warms.
  for j in range(3):
   if p<.65-j*.13:cloud(d,420+j*65,600+j*70,.5-j*.08,'#d4e1de')
  txt(d,'नीचे उतरते हुए गर्म',385,365,34,'#b96b19')
  txt(d,'बादल बनना मुश्किल',500,420,29,'#b96b19')
  d.rounded_rectangle((370,920,665,982),14,fill='#fff0c5')
  txt(d,'अक्सर बारिश कम',518,950,31,'#a76818')
 else:
  # Transfer test: reverse the wind, so recalling the picture is insufficient.
  landscape(d,t,True)
  motion.arrow(d,(640,465),(435,465),BLUE)
  txt(d,'अब हवा उलटी चले तो?',350,365,35,TEAL)
  for j in range(12):
   u=(t*.18+j/12)%1
   x=650-570*u;y=850-310*math.sin(math.pi*u)
   d.ellipse((x-4,y-4,x+4,y+4),fill=BLUE if u<.6 else GOLD)
  for x,s in [(170,'A'),(580,'B')]:
   d.ellipse((x-25,675,x+25,725),fill='white',outline=INK,width=3)
   txt(d,s,x,700,32)
  if t>=duration-1.6:
   cloud(d,525,580,.85,'#789cb5');rain(d,470,630,t,115,210)
   d.rounded_rectangle((350,920,660,982),14,fill='#d3f2e2')
   txt(d,'B: ऊपर चढ़ती नम हवा',505,950,27,TEAL)
  else:txt(d,'बारिश वाली तरफ: A या B?',360,1038,30,BLUE)
 return im
motion.render=render
reference={'question':'Rain shadow: moist air rises over mountains, may condense and rain; descending leeward air warms.','explanation':'Simplified orographic model. Sufficient moisture is necessary; leeward rainfall is lower, not necessarily zero. Reversed-wind question assumes sufficient moisture arrives from the right.','sources':['https://cloudatlas.wmo.int/orographic-influences-on-the-windward-side.html','https://www.noaa.gov/jetstream/appendix/weather-glossary-r']}
lines=[
 ('एक पहाड़, दो अलग नज़ारे!','इधर छाता चाहिए, पहाड़ के उस पार सूखा! बारिश का ये फर्क क्यों?'),
 ('बादल ऐसे बनते हैं','नम हवा पहाड़ पर चढ़कर ठंडी होती है। बादल बनते हैं, फिर बारिश हो सकती है।'),
 ('सूखी तरफ का राज़','दूसरी तरफ उतरती हवा गर्म होती है। इसलिए वहाँ अक्सर बारिश कम होती है।'),
 ('दोस्त का छोटा टेस्ट','अब नम हवा उलटी तरफ से आए, तो बारिश कहाँ होगी? दोस्त को पूछो!')]
script={'ok':True,'title':'पहाड़ बदला… बारिश गायब?','renderer_version':motion.VERSION,'question_hash':hashlib.sha256(b'viewer-retry-v2').hexdigest(),'reference':reference,'subject':'Geography','scenes':[{'label':label,'speech':speech,'animation':{'type':'rainshadow','phase':phase,'labels':['नम हवा ऊपर','गर्म हवा नीचे']}} for (label,speech),phase in zip(lines,['question','explain','demonstrate','recall'])]}
(ROOT/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2))
v.build()
e.resolve_font()
final=promo.prepare_video(ROOT/'reel.mp4',e.get_font)
# A stable filename lets the user open the complete final export.
import shutil
shutil.copyfile(final,ROOT/'preview_with_whatsapp.mp4')
manifest=json.loads((ROOT/'validated.json').read_text())
dur=manifest['duration']
sheet=Image.new('RGB',(720*2,1280*2),'white')
for i,frac in enumerate((.11,.38,.64,.94)):
 jpg=ROOT/f'frame_{i}.jpg'
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(dur*frac),'-i',str(ROOT/'preview_with_whatsapp.mp4'),'-frames:v','1',str(jpg)],check=True)
 sheet.paste(Image.open(jpg).convert('RGB'),((i%2)*720,(i//2)*1280))
sheet.thumbnail((1000,1800));sheet.save(ROOT/'review_sheet.jpg',quality=88)
manifest.update(final_sha256=hashlib.sha256((ROOT/'preview_with_whatsapp.mp4').read_bytes()).hexdigest(),build_only=True,review_status='awaiting human visual review; not automatically rated',whatsapp=promo.PHONE)
(ROOT/'review.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(manifest,ensure_ascii=False))
