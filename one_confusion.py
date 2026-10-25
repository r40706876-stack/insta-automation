"""Independent, opt-in One Confusion experiment. Does not advance the normal queue."""
import argparse, hashlib, json, math, os, subprocess, sys, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path('experiments/one_confusion_01')
W,H,FPS = 1080,1920,24
INK='#153E43'; MUTED='#53696D'; TEAL='#087F80'; RED='#D34D3F'; BG='#FFF9ED'
SOURCE='https://www.ncert.nic.in/textbook/pdf/iesc109.pdf'
SPEECH=[
 'पृथ्वी पर द्रव्यमान साठ किलो। चाँद पर साठ रहेगा, या दस? अपना जवाब चुनो।',
 'साठ ही! द्रव्यमान नहीं बदलता। भार बदलता है। दोनों को एक मत समझो।',
 'वही इंसान, वही द्रव्यमान। चाँद का गुरुत्वीय खिंचाव लगभग छह गुना कम है।',
 'इसलिए पृथ्वी पर भार पाँच सौ अट्ठासी न्यूटन, तो चाँद पर लगभग अट्ठानवे न्यूटन। किलो द्रव्यमान की इकाई है।',
 'अब जाँचो! पृथ्वी पर भार एक सौ बीस न्यूटन है। चाँद पर कितना? बीस न्यूटन।'
]
CAPTION='''चाँद पर 60 kg वाला इंसान 10 kg हो जाता है? 🌍 → 🌙

द्रव्यमान और भार का यही confusion साफ करो:
• द्रव्यमान: पृथ्वी और चाँद पर समान — 60 kg.
• भार: W = mg; पृथ्वी पर लगभग 588 N, चाँद पर लगभग 98 N.
• चाँद पर भार पृथ्वी के भार का लगभग 1/6 होता है।

खुद जाँचो: पृथ्वी पर 120 N → चाँद पर लगभग 20 N.
उस study partner को भेजो जो kg और N में उलझता है।

स्रोत: NCERT कक्षा 9 विज्ञान, Gravitation: https://www.ncert.nic.in/textbook/pdf/iesc109.pdf
यह concept practice है; किसी खास परीक्षा का verified PYQ नहीं।

#MinuteMeGS #ScienceConcept #SSC #RailwayExam #GKinhindi'''

def font(n):
    return ImageFont.truetype('Mukta-ExtraBold.ttf',n)

def txt(d,s,y,n=65,fill=INK,x=540):
    d.text((x,y),s,font=font(n),fill=fill,anchor='mm')

def panel(d,box,fill='white',outline=None):
    d.rounded_rectangle(box,radius=34,fill=fill,outline=outline,width=4)

def arrow(d,x,y,length,col):
    d.line((x,y,x,y+length),fill=col,width=15)
    d.polygon([(x-24,y+length-25),(x+24,y+length-25),(x,y+length+15)],fill=col)

def globe(d,x,y,r,moon=False,t=0):
    d.ellipse((x-r,y-r,x+r,y+r),fill='#DBDBD6' if moon else '#B5E2ED',outline=INK,width=5)
    if moon:
        for dx,dy,rr in [(-.35,-.3,.17),(.35,.1,.22),(-.2,.45,.12)]:
            d.ellipse((x+dx*r-rr*r,y+dy*r-rr*r,x+dx*r+rr*r,y+dy*r+rr*r),fill='#BCBEB9')
    else:
        d.polygon([(x-r*.8,y-r*.2),(x-r*.4,y-r*.7),(x+r*.2,y-r*.5),(x+r*.1,y),(x-r*.3,y+r*.1)],fill='#57B79C')
        d.polygon([(x+r*.25,y+r*.1),(x+r*.75,y+r*.2),(x+r*.4,y+r*.75),(x+r*.1,y+r*.55)],fill='#57B79C')

def person(d,x,y,t=0):
    b=8*math.sin(t*3)
    y+=b
    d.ellipse((x-37,y-160,x+37,y-86),fill='#FFCBA9',outline=INK,width=5)
    d.rounded_rectangle((x-47,y-78,x+47,y+45),radius=22,fill=TEAL)
    for dx in (-25,25): d.line((x+dx,y+35,x+dx*1.5,y+110),fill=INK,width=19)
    d.line((x-45,y-55,x-83,y+5),fill=INK,width=15)
    d.line((x+45,y-55,x+83,y+5),fill=INK,width=15)

def render(k,t,dur):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    panel(d,(70,155,1010,238),TEAL)
    txt(d,'एक गलती साफ  /  01',197,41,'white')
    d.rounded_rectangle((80,1640,1000,1649),radius=5,fill='#DDE6E1')
    d.rounded_rectangle((80,1640,80+920*min(1,(k+t/dur)/5),1649),radius=5,fill=TEAL)
    txt(d,'@MinuteMe_GS  •  Science समझो',1710,35,MUTED)
    if k==0:
        txt(d,'चाँद पर 60 kg → 10 kg?',335,72)
        txt(d,'द्रव्यमान कितना रहेगा?',433,61,RED)
        p=min(1,t/max(1,dur-.8)); x=275+530*p
        globe(d,265,1070,155); globe(d,815,1070,155,True)
        person(d,x,800,t)
        txt(d,'पृथ्वी',1280,51,x=265); txt(d,'चाँद',1280,51,x=815)
        panel(d,(130,1410,505,1535),'#E2F2EB'); panel(d,(575,1410,950,1535),'#FFE4D8')
        txt(d,'A: 60 kg',1472,64,x=317);txt(d,'B: 10 kg',1472,64,x=762)
        txt(d,'जवाब चुनो…',590,45,MUTED)
    elif k==1:
        txt(d,'60 kg ही रहेगा!',350,90,TEAL)
        txt(d,'द्रव्यमान ≠ भार',490,80,RED)
        globe(d,270,1090,160);globe(d,810,1090,160,True)
        person(d,270,820,t);person(d,810,820,t)
        for x in (270,810):
            panel(d,(x-185,1310,x+185,1450),'#DFF0E8');txt(d,'60 kg',1380,85,TEAL,x=x)
        txt(d,'जगह बदली। द्रव्यमान नहीं।',1560,49)
    elif k==2:
        txt(d,'इंसान वही। खिंचाव अलग।',350,68)
        globe(d,270,1170,170);globe(d,810,1170,170,True)
        person(d,270,750,t);person(d,810,750,t)
        for i in range(6):arrow(d,145+i*50,915,105+10*math.sin(t*4),TEAL)
        arrow(d,810,915,65+7*math.sin(t*4),RED)
        txt(d,'पृथ्वी',1430,58,x=270);txt(d,'चाँद',1430,58,x=810)
        txt(d,'गुरुत्वीय खिंचाव ≈ 1/6',1540,56,RED)
        txt(d,'द्रव्यमान दोनों पर 60 kg',520,52,TEAL)
    elif k==3:
        txt(d,'किलो और न्यूटन का फ़र्क',345,68)
        txt(d,'भार = द्रव्यमान × g',465,64,TEAL)
        for x,moon,name,num in [(270,False,'पृथ्वी','588 N'),(810,True,'चाँद','≈ 98 N')]:
            globe(d,x,800,145,moon)
            txt(d,name,1020,54,x=x)
            panel(d,(x-210,1110,x+210,1300),'#DFF0E8' if not moon else '#FFE4D8')
            txt(d,num,1205,77,TEAL if not moon else RED,x=x)
        txt(d,'द्रव्यमान: kg   |   भार: N',1460,60)
        txt(d,'g: पृथ्वी ≈ 9.8 m/s²',1550,40,MUTED)
    else:
        txt(d,'अब बिना देखे बताओ!',345,77)
        txt(d,'पृथ्वी पर भार = 120 N',500,65)
        globe(d,540,900,180,True,t)
        txt(d,'चाँद पर भार = ?',1210,83,RED)
        if t>=dur-1.7:
            panel(d,(175,1360,905,1510),'#DFF0E8');txt(d,'120 ÷ 6 ≈ 20 N',1435,65,TEAL)
        else:
            txt(d,'120 N     /     20 N',1435,66)
        txt(d,'अपने study partner को जाँचो',1570,42,MUTED)
    return im

def preview():
    OUT.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(1080,768))
    for k in range(5):
        im=render(k,1,5);im.save(OUT/f'preview_{k}.jpg')
        sheet.paste(im.resize((216,384)),(216*k,0))
        sheet.paste(render(k,4.5,5).resize((216,384)),(216*k,384))
    sheet.save(OUT/'contact_sheet.jpg')

def build():
    import auto_poster as e
    import numpy as np
    OUT.mkdir(parents=True,exist_ok=True)
    # No text generation: one sourced, fixed concept; existing speech providers only.
    e.FPS=FPS
    voices=e.make_voices([{'segs':[(None,None,s)]} for s in SPEECH],rot=0)
    arrs=[v[0] for v in voices]
    if any(len(v)<e.SR*.5 or np.max(np.abs(v))<.001 for v in arrs):
        raise RuntimeError('Real narration required; refusing silent publication')
    durs=[max(len(v)/e.SR+.25,m) for v,m in zip(arrs,[4,3.5,4,5,5])]
    starts=[sum(durs[:i]) for i in range(5)];total=sum(durs)
    audio=e.beat_music(total,7)*.09
    for i,v in enumerate(arrs):
        e.add_at(audio,v.astype(np.float32),starts[i]+.08,1)
        if i:e.add_at(audio,e.sfx_pop(.15),starts[i])
    def frame(fi):
        t=fi/FPS;k=max(i for i,s in enumerate(starts) if s<=t)
        return render(k,t-starts[k],durs[k])
    e.encode_frames(frame,math.ceil(total*FPS),np.clip(audio,-.98,.98),str(OUT/'reel.mp4'),key=lambda fi:fi)
    (OUT/'caption.txt').write_text(CAPTION,encoding='utf-8')
    render(0,0,durs[0]).save(OUT/'cover.jpg')
    preview()
    manifest={'experiment':'one_confusion_01','source':SOURCE,'speech':SPEECH,'scene_seconds':durs,
              'duration':total,'sha256':hashlib.sha256((OUT/'reel.mp4').read_bytes()).hexdigest()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

def publish():
    import auto_poster as e
    marker=OUT/'published.json'
    if marker.exists():
        print('Already published:',marker.read_text());return
    manifest=json.loads((OUT/'manifest.json').read_text())
    if hashlib.sha256((OUT/'reel.mp4').read_bytes()).hexdigest()!=manifest['sha256']:
        raise RuntimeError('Reviewed render hash mismatch')
    # Avoid attaching an unrelated Day N / 100-days promise to this experiment.
    e._with_series=lambda caption:caption
    pid=e.post_reel(str(OUT/'reel.mp4'),(OUT/'caption.txt').read_text(),0)
    if not pid:raise RuntimeError('Instagram did not confirm publication')
    result={'media_id':pid,'published_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'experiment':'one_confusion_01','sha256':manifest['sha256']}
    marker.write_text(json.dumps(result,indent=2))
    try:
        r=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
        result['permalink']=r.get('permalink');marker.write_text(json.dumps(result,indent=2))
    except Exception:pass
    print('PUBLISH_RESULT',json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','build','publish']);a=p.parse_args()
    {'preview':preview,'build':build,'publish':publish}[a.mode]()
