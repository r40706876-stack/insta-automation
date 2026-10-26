import cinematic_gs as c, math, subprocess
from PIL import ImageDraw
c.prepare()
c.HEAD=['इतना पानी… फिर भी रेगिस्तान?','पहले जगह पहचानो','बारिश क्यों नहीं बनती?','कोहरा और बारिश अलग हैं','पहाड़ और हवा भी असर डालते हैं','बस यह बात याद रखो']
c.SUB=['समुद्र पास है। लेकिन बारिश बहुत कम।','नीले तीर ठंडे पानी की दिशा बताते हैं।','तीर और बिंदु हवा की चाल समझाते हैं।','कोहरा जमीन के पास रह सकता है।','इस सूखे की वजह सिर्फ ठंडा समुद्र नहीं।','समुद्र पास होना ही काफी नहीं।']
old=c.render

def frame(k,t,dur):
 if k not in (2,3,5):return old(k,t,dur)
 im,d=c.base(k,t,dur)
 if k==5:
  for j,(s,col) in enumerate([('नम हवा ऊपर उठती है',c.BLUE),('ऊपर जाकर ठंडी होती है',c.WHITE),('बादल और बारिश बन सकते हैं',c.GOLD)]):
   y=420+j*190
   if t>=j*1.3:
    d.rounded_rectangle((65,y-60,655,y+60),22,fill='#14354d',outline=col,width=2)
    c.text(d,s,360,y,33,col)
    if j<2:c.arrow(d,(360,y+80),(360,y+115),c.BLUE,5)
  return im
 # Water and sky deliberately separated; moisture particles are above the surface.
 d.rounded_rectangle((45,290,675,960),25,fill='#27536b')
 d.rectangle((46,680,430,959),fill='#12668b')
 d.polygon([(430,705),(485,650),(675,650),(675,959),(430,959)],fill='#bf945c')
 for j in range(7):
  x=48+j*54;y=680+4*math.sin(t*2+j);d.arc((x,y-7,x+52,y+7),0,180,fill=c.BLUE,width=3)
 c.tag(d,'ठंडा समुद्र',230,865,c.BLUE,30);c.tag(d,'सूखी जमीन',550,865,c.GOLD,27)
 stage=0 if t<2.6 else 1
 if k==3:stage=2
 msg=['1. ठंडा पानी → कम भाप','2. नम हवा ऊपर नहीं उठ पाती','3. नीचे कोहरा… पर बारिश नहीं'][stage]
 c.text(d,msg,360,350,32,c.GOLD)
 if stage>=1:
  d.rounded_rectangle((75,455,640,500),16,fill='#956743')
  c.text(d,'ऊपर गर्म हवा की परत',357,478,29,c.WHITE)
 for j in range(9):
  phase=(t*.19+j*.11)%1;x=105+j*33;y=660-phase*(140 if stage>=1 else 100)
  r=3 if j%3 else 5;d.ellipse((x-r,y-r,x+r,y+r),fill='#bdedff')
  if stage>=1 and phase>.8:
   c.arrow(d,(x,520),(x+25,520),c.BLUE,3)
 if stage==0:c.tag(d,'कम पानी भाप बनता है',260,570,c.WHITE,27)
 elif stage==1:c.tag(d,'हवा ऊपर उठने में रुकावट',350,750,c.WHITE,27)
 else:
  for j in range(8):
   x=230+j*42+8*math.sin(t+j);d.ellipse((x-36,615,x+36,640),fill='#b5c9cf')
  c.tag(d,'कोहरा: जमीन के पास',390,750,c.WHITE,28)
 return im

if __name__=='__main__':
 ds=[4,7,8,6,8,8];starts=[sum(ds[:i]) for i in range(6)]
 p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','720x1280','-r','24','-i','-','-i','cinematic_gs_mobile.mp4','-map','0:v','-map','1:a','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','20','-c:a','copy','-shortest','-movflags','+faststart','gs_easy_explanation.mp4'],stdin=subprocess.PIPE)
 for fi in range(984):
  t=fi/24;k=max(i for i,s in enumerate(starts) if s<=t);p.stdin.write(frame(k,t-starts[k],ds[k]).tobytes())
 p.stdin.close();assert p.wait()==0
