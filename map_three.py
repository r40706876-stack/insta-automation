"""Independent One Map, Three Answers pilot. Region map from geographic data."""
import argparse,json,math,time,hashlib
from functools import lru_cache
from pathlib import Path
from PIL import Image,ImageDraw
import one_confusion as base

DATA=json.loads(Path('narmada_map.json').read_text())
OUT=Path('experiments/map_three_01')
SOURCE='https://sathee.iitk.ac.in/ncert-books/class-11/geography/india-physical-environment/chapter-03-drainage-system/'
SPEECH=[
 'नर्मदा का पानी किस तरफ जाएगा? अरब सागर, या बंगाल की खाड़ी? दिशा चुनो।',
 'शुरुआत यहाँ, अमरकंटक से। बस इस जगह को नक्शे में पकड़ लो।',
 'अब रास्ता देखो। नर्मदा पश्चिम बहकर अरब सागर में मिलती है।',
 'उत्तर में विंध्य, दक्षिण में सतपुड़ा। इनके बीच भ्रंश घाटी में नर्मदा बहती है।',
 'अब नाम छिपा दिए! शुरुआत कहाँ? समुद्र कौन सा? उत्तर का पर्वत? अमरकंटक, अरब सागर, विंध्य।'
]
CAPTION='''एक नक्शा, तीन जवाब — नर्मदा | Map Test 01

1. उद्गम: अमरकंटक।
2. समुद्र: अरब सागर; बहने की दिशा पश्चिम।
3. उत्तर में विंध्य, दक्षिण में सतपुड़ा। इनके बीच भ्रंश घाटी में नर्मदा बहती है।

अंत में नाम छिपेंगे: तुम्हें कितने जवाब याद रहे — 0/3 या 3/3?
अपने study partner को भेजकर उसका test लो।

स्रोत: NCERT कक्षा 11, India: Physical Environment, Drainage System (IIT Kanpur SATHEE).
https://sathee.iitk.ac.in/ncert-books/class-11/geography/india-physical-environment/chapter-03-drainage-system/
क्षेत्रीय मानचित्र सरलीकृत है। पर्वत-चिह्न, उद्गम और मुहाने के जोड़ सांकेतिक हैं। नदी का मुख्य रास्ता Natural Earth data से है।
Concept practice; किसी खास परीक्षा का verified PYQ नहीं।

#MinuteMeGS #IndianGeography #Narmada #SSC #RailwayExam'''
INK,TEAL,RED,MUTED=base.INK,base.TEAL,base.RED,base.MUTED
def text(d,s,y,n=62,fill=INK,x=540):base.txt(d,s,y,n,fill,x)
def xy(lon,lat,zoom=False):
    a,b,c,e=(72,82.7,20.5,25.5) if zoom else (68.5,89,19,28)
    return 60+(lon-a)/(b-a)*960,540+(e-lat)/(e-c)*720
def label(d,s,lon,lat,zoom=False,fill=INK,size=38):
    x,y=xy(lon,lat,zoom);f=base.font(size);bb=d.textbbox((x,y),s,font=f,anchor='mm')
    d.rounded_rectangle((bb[0]-10,bb[1]-5,bb[2]+10,bb[3]+5),radius=8,fill='#FFFFF4')
    d.text((x,y),s,font=f,fill=fill,anchor='mm')
@lru_cache(maxsize=6)
def background(zoom,hidden=False):
    im=Image.new('RGB',(1080,1920),base.BG)
    layer=Image.new('RGB',im.size,'#DCEFF4');d=ImageDraw.Draw(layer)
    fills={'Madhya Pradesh':'#FFF0B9','Gujarat':'#E4DDF6','Maharashtra':'#E4EBD5','Chhattisgarh':'#F5DFCE'}
    for f in DATA['states']:
        for r in f['rings']:
            pts=[xy(x,y,zoom) for x,y in r]
            if len(pts)>2:d.polygon(pts,fill=fills.get(f['name'],'#F3EEDC'),outline='#9BA79F',width=2)
    im.paste(layer.crop((60,540,1020,1260)),(60,540));d=ImageDraw.Draw(im)
    d.rectangle((60,540,1020,1260),outline='#9BBABD',width=3)
    if not hidden:
        label(d,'मध्य प्रदेश',78.6,25,zoom,size=35)
        label(d,'गुजरात',73 if zoom else 71.9,23 if zoom else 24.1,zoom,size=30)
        if not zoom:
            label(d,'अरब सागर',70.0,20.5,fill=TEAL,size=32)
            label(d,'बंगाल की खाड़ी',86.5,20.2,fill=TEAL,size=29)
    d.line((970,645,970,580),fill=INK,width=4);d.polygon([(958,597),(982,597),(970,575)],fill=INK)
    text(d,'उत्तर',675,28,x=970)
    return im
def river(d,p,zoom=False):
    pts=[xy(x,y,zoom) for x,y in DATA['river']];n=max(2,int(min(1,max(0,p))*len(pts)))
    d.line(pts[:n],fill='white',width=20,joint='curve');d.line(pts[:n],fill=TEAL,width=12,joint='curve')
    x,y=pts[n-1];d.ellipse((x-11,y-11,x+11,y+11),fill=TEAL,outline='white',width=3)
def arrow(d,a,b,col):
    x,y=a;xx,yy=b
    for k in range(0,20,2):
        p=k/20;q=(k+1)/20;d.line((x+(xx-x)*p,y+(yy-y)*p,x+(xx-x)*q,y+(yy-y)*q),fill=col,width=7)
    ang=math.atan2(yy-y,xx-x)
    d.polygon([(xx,yy),(xx-30*math.cos(ang-.5),yy-30*math.sin(ang-.5)),(xx-30*math.cos(ang+.5),yy-30*math.sin(ang+.5))],fill=col)
def render(k,t,dur):
    zoom=k in (1,3);im=background(zoom,k==4).copy();d=ImageDraw.Draw(im)
    base.panel(d,(70,155,1010,238),TEAL);text(d,'एक नक्शा, तीन जवाब  /  01',197,40,'white')
    titles=['नर्मदा का पानी किधर जाएगा?','पहला जवाब: शुरुआत कहाँ?','दूसरा जवाब: कौन सा समुद्र?','तीसरा जवाब: उत्तर में कौन?','अब नक्शे से जवाब दो!']
    text(d,titles[k],335,65)
    sub=['A: अरब सागर  |  B: बंगाल की खाड़ी','अमरकंटक','पश्चिम की ओर बहती है','विंध्य ऊपर  •  सतपुड़ा नीचे','उद्गम?  समुद्र?  उत्तर का पर्वत?'][k]
    text(d,sub,443,45,TEAL);src=xy(81.75,22.67,zoom)
    if k==0:
        arrow(d,src,xy(72.5,21.6),TEAL);arrow(d,src,xy(87,21),RED)
        pulse=13+5*math.sin(t*5);d.ellipse((src[0]-pulse,src[1]-pulse,src[0]+pulse,src[1]+pulse),fill=RED)
        label(d,'नर्मदा',81.8,23.9,size=38);text(d,'A या B? अपना जवाब चुनो',1390,56)
    elif k==1:
        river(d,.12,True);pulse=15+5*math.sin(t*5)
        d.ellipse((src[0]-pulse,src[1]-pulse,src[0]+pulse,src[1]+pulse),fill=RED)
        label(d,'अमरकंटक',81,21.6,True,RED,42)
        text(d,'उद्गम: अमरकंटक',1390,68);text(d,'नक्शे का यह बिंदु याद रखो',1490,46,MUTED)
    elif k==2:
        river(d,min(1,t/max(1,dur-1)));label(d,'अमरकंटक',82,23.8,size=33)
        text(d,'अमरकंटक से अरब सागर तक',1390,61);text(d,'दिशा: पश्चिम',1490,57,TEAL)
    elif k==3:
        for points,col in [([(73.8,23.1),(76,23.7),(78,24),(80,24)],'#C78D54'), ([(74.5,21.4),(76.2,21.2),(78,21.5),(80,22)],'#AA7B4A')]:
            d.line([xy(x,y,True) for x,y in points],fill=col,width=24,joint='curve')
        river(d,1,True);label(d,'विंध्य',77,24.25,True,size=48);label(d,'सतपुड़ा',77,20.95,True,size=48)
        text(d,'बीच में: नर्मदा की भ्रंश घाटी',1390,59);text(d,'उत्तर = विंध्य   |   दक्षिण = सतपुड़ा',1490,46,TEAL)
    else:
        river(d,1)
        for i,p in enumerate([(81.75,22.67),(72.6,21.6),(78,24)]):
            x,y=xy(*p);d.ellipse((x-22,y-22,x+22,y+22),fill=RED)
            d.text((x,y),str(i+1),font=base.font(30),fill='white',anchor='mm')
        if t>=dur-1.8:
            text(d,'अमरकंटक  •  अरब सागर  •  विंध्य',1400,49,TEAL);text(d,'कितने याद रहे?  0/3 से 3/3',1500,51)
        else:
            text(d,'1. शुरुआत   2. समुद्र   3. पर्वत',1390,53);text(d,'अपने study partner को जाँचो',1490,47,MUTED)
    text(d,'क्षेत्रीय मानचित्र • सरलीकृत / पर्वत सांकेतिक',1305,27,MUTED)
    d.rounded_rectangle((80,1640,1000,1649),radius=5,fill='#DDE6E1')
    d.rounded_rectangle((80,1640,80+920*min(1,(k+t/dur)/5),1649),radius=5,fill=TEAL)
    text(d,'@MinuteMe_GS  •  NCERT Geography',1710,34,MUTED)
    return im

base.OUT=OUT;base.SOURCE=SOURCE;base.SPEECH=SPEECH;base.CAPTION=CAPTION;base.render=render
def build():
    base.build();p=OUT/'manifest.json';m=json.loads(p.read_text());m['experiment']=OUT.name
    m['map_sources']=DATA['sources'];p.write_text(json.dumps(m,ensure_ascii=False,indent=2))
def publish():
    import auto_poster as e
    marker=OUT/'published.json'
    if marker.exists():print('Already published:',marker.read_text());return
    m=json.loads((OUT/'manifest.json').read_text());req=json.loads(Path('experiments/map_three_request.json').read_text())
    digest=hashlib.sha256((OUT/'reel.mp4').read_bytes()).hexdigest()
    if digest!=m['sha256'] or digest!=req.get('reviewed_sha256'):raise RuntimeError('Reviewed render hash mismatch')
    e._with_series=lambda caption:caption
    pid=e.post_reel(str(OUT/'reel.mp4'),(OUT/'caption.txt').read_text(),0)
    if not pid:raise RuntimeError('Instagram did not confirm publication')
    result={'media_id':pid,'experiment':OUT.name,'sha256':digest,'published_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    marker.write_text(json.dumps(result,indent=2))
    try:
        r=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
        result['permalink']=r.get('permalink');marker.write_text(json.dumps(result,indent=2))
    except Exception:pass
    print('PUBLISH_RESULT',json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','build','publish']);a=p.parse_args()
    {'preview':base.preview,'build':build,'publish':publish}[a.mode]()
