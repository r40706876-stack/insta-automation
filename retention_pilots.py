"""Two sourced motion-first pilots; build, review, then explicit hash-checked publication."""
import argparse,hashlib,json,math,time
from pathlib import Path
from functools import lru_cache
from PIL import Image,ImageDraw
import one_confusion as ui

ROOT=Path('experiments/retention_pilots_v1')
IDS=['rail_gap','one_clock']
BG='#F6F3EA';INK='#172F45';BLUE='#086FA1';RED='#D94D41';GREEN='#087F78';GOLD='#E9A832'
SPEECH={
'rail_gap':[
 'पटरी का ये गैप भर दिया तो? गर्मी में क्या होगा?',
 'जोड़ वाली पटरी में यह जगह फैलाव के लिए छोड़ी जाती है।',
 'गर्मी बढ़ी, लोहा लंबा हुआ। देखो, गैप कम हो रहा है।',
 'फैलने की जगह न मिले, तो पटरी में तनाव बढ़ सकता है।',
 'अब ठंड में गैप बढ़ेगा या घटेगा? बढ़ेगा, क्योंकि लोहा सिकुड़ेगा।'
],
'one_clock':[
 'अरुणाचल में सूरज पहले, गुजरात में बाद में। फिर घड़ी एक क्यों?',
 'देश के लिए एक मानक समय चुना गया है।',
 'यह है बयासी दशमलव पाँच डिग्री पूर्व देशांतर, मिर्जापुर के पास।',
 'इसी मानक रेखा से भारतीय मानक समय तय होता है।',
 'घड़ी देशभर में एक। अब बताओ, मानक देशांतर कितना? बयासी दशमलव पाँच पूर्व।'
]}
SOURCES={
'rail_gap':['https://sathee.iitk.ac.in/sathee-neet/notes-class-11/physics/thermal-properties-of-matter/','https://rdso.indianrailways.gov.in/works/uploads/File/Handbook%20on%20maintenance%20of%20Switch%20expansion%20joint%283%29.pdf'],
'one_clock':['https://ncert.nic.in/textbook/pdf/kegy303.pdf']}
CAPTIONS={
'rail_gap':'''पटरी का गैप भर दिया तो? | रोज़ दिखता है, Science छिपी है — 01

जोड़ वाली रेलवे पटरी में expansion gap तापीय प्रसार के लिए जगह देता है।
गर्मी में रेल लंबी होने पर गैप कम हो सकता है; ठंड में सिकुड़ने पर बढ़ सकता है। फैलाव रोकने पर तापीय तनाव बढ़ता है।
चित्र में फैलाव बढ़ा-चढ़ाकर दिखाया गया है ताकि concept साफ हो। यह jointed rail का सरलीकृत उदाहरण है। आधुनिक LWR/CWR में thermal movement का प्रबंध अलग होता है; हर रेल जोड़ को यही चित्र न समझें।

खुद जाँचो: ठंड में gap बढ़ेगा या घटेगा? अपने Railway/SSC वाले study partner को भेजो।
स्रोत: IIT Kanpur SATHEE, Thermal Properties of Matter; Indian Railways RDSO, Switch Expansion Joint Handbook.
https://sathee.iitk.ac.in/sathee-neet/notes-class-11/physics/thermal-properties-of-matter/
Concept practice, verified PYQ का दावा नहीं।

#MinuteMeGS #RailwayExam #SSC #Physics #ScienceHindi''',
'one_clock':'''सूरज अलग समय पर, घड़ी एक क्यों? | रोज़ दिखता है, Geography छिपी है — 02

पूर्वी भारत में सूर्योदय पश्चिमी भारत से पहले होता है। भारत एक आधिकारिक मानक समय IST अपनाता है।
मानक देशांतर: 82°30′ E = 82.5° E, मिर्जापुर (उत्तर प्रदेश) के पास से गुजरता है। IST = UTC + 5:30.
दोनों घड़ियाँ समान क्षण का मानक समय दिखाने का illustrative उदाहरण हैं; ये शहरों के वास्तविक sunrise times नहीं हैं। नक्शा क्षेत्रीय और सरलीकृत है।

अब बिना देखे मानक देशांतर बताओ। अपने geography वाले study partner को जाँचो।
स्रोत: NCERT, Practical Work in Geography, Latitude, Longitude and Time.
https://ncert.nic.in/textbook/pdf/kegy303.pdf
Concept practice; किसी खास परीक्षा का verified PYQ नहीं।

#MinuteMeGS #IndianGeography #IST #SSC #RailwayExam'''}

def txt(d,s,y,n=65,col=INK,x=540):
    d.text((x,y),s,font=ui.font(n),fill=col,anchor='mm')
def box(d,b,fill='white',outline=None,r=24):d.rounded_rectangle(b,radius=r,fill=fill,outline=outline,width=3)
def header(d,id,k,t,dur):
    box(d,(70,155,1010,222),INK,r=18)
    txt(d,'रोज़ दिखता है, Science छिपी है' if id=='rail_gap' else 'रोज़ दिखता है, Geography छिपी है',188,35,'white')
    box(d,(80,1638,1000,1647),'#D5DEDC',r=4)
    box(d,(80,1638,80+920*min(1,(k+t/dur)/5),1647),GREEN,r=4)
    txt(d,'@MinuteMe_GS  •  SSC / Railway GS',1710,34)
def double_arrow(d,x0,x1,y,col=RED):
    d.line((x0,y,x1,y),fill=col,width=7)
    for x,sg in [(x0,1),(x1,-1)]:d.polygon([(x,y),(x+sg*18,y-12),(x+sg*18,y+12)],fill=col)
def rail(d,p,stress=False,y=890):
    # Enlarged side view, with two fixed outer ends and expansion toward the centre.
    for x in range(115,980,110):box(d,(x,y+102,x+50,y+190),'#947656',r=6)
    end=470+58*p;start=610-58*p
    for a,b in [(90,end),(start,990)]:
        box(d,(a,y,b,y+110),'#52778C',r=9)
        box(d,(a,y,b,y+26),'#AAC6D3',r=7)
        d.line((a+8,y+78,b-8,y+78),fill='#244C63',width=6)
    box(d,(end+3,y-28,start-3,y+120),'#FFE0BF',RED,r=8)
    double_arrow(d,end+5,start-5,y-58)
    txt(d,'गैप',y-115,48,RED)
    if stress:
        for x,sg in [(380,1),(700,-1)]:
            xx=x+sg*45*abs(math.sin(p*math.pi))
            d.line((x,y+55,xx,y+55),fill=RED,width=13)
            d.polygon([(xx,y+55),(xx-sg*22,y+36),(xx-sg*22,y+74)],fill=RED)
def thermometer(d,p):
    x,y=900,585;box(d,(x-22,y,x+22,y+170),'white',INK,r=20)
    d.ellipse((x-38,y+140,x+38,y+216),fill=RED)
    box(d,(x-12,y+145-125*p,x+12,y+170),RED,r=10)
def sun(d,x,y,r,t):
    for i in range(12):
        a=i*math.pi/6+t*.2
        d.line((x+(r+12)*math.cos(a),y+(r+12)*math.sin(a),x+(r+32)*math.cos(a),y+(r+32)*math.sin(a)),fill=GOLD,width=8)
    d.ellipse((x-r,y-r,x+r,y+r),fill=GOLD)
def train(d,t,y=650):
    x=-420+(t*210)%1800
    for k in range(3):
        a=x+k*200;box(d,(a,y,a+185,y+110),BLUE,r=16)
        for j in range(3):box(d,(a+15+j*53,y+22,a+53+j*53,y+62),'#CAEEFA',r=5)
        for wx in [a+38,a+146]:d.ellipse((wx-17,y+91,wx+17,y+125),fill=INK)
    d.line((65,y+130,1015,y+130),fill=INK,width=7)
def rail_frame(k,t,dur):
    im=Image.new('RGB',(1080,1920),BG);d=ImageDraw.Draw(im);p=min(1,t/max(.5,dur-.4))
    header(d,'rail_gap',k,t,dur)
    if k==0:
        txt(d,'ये गैप भर दिया तो?',330,91)
        txt(d,'गर्मी में क्या होगा?',445,68,RED)
        train(d,t);rail(d,.3+.3*math.sin(t*3),y=960)
        txt(d,'जोड़ वाली रेलवे पटरी',1330,48)
        txt(d,'खाली जगह की असली वजह देखो',1450,51,BLUE)
    elif k==1:
        txt(d,'यह जगह जानबूझकर है',330,77)
        txt(d,'फैलाव के लिए जगह',445,62,BLUE)
        rail(d,0,y=850)
        double_arrow(d,170,450,1180,BLUE);double_arrow(d,630,910,1180,BLUE)
        txt(d,'लोहा गरम होगा तो लंबा होगा',1380,59)
        txt(d,'पहले इस गैप पर ध्यान दो',1480,47,RED)
    elif k==2:
        txt(d,'गर्मी बढ़ी। पटरी फैली।',330,76)
        txt(d,'अब गैप घटता देखो',445,62,RED)
        sun(d,205,670,56,t);thermometer(d,p);rail(d,p,y=930)
        txt(d,'गैप कम',1370,87,RED)
        txt(d,'तापीय प्रसार / Thermal expansion',1480,41,BLUE)
    elif k==3:
        txt(d,'फैलने की जगह न मिले?',330,76)
        txt(d,'पटरी में तापीय तनाव बढ़ेगा',445,57,RED)
        rail(d,.9,True,y=900)
        for x in (220,860):
            box(d,(x-65,1120,x+65,1220),INK,r=12);txt(d,'रोक',1170,37,'white',x=x)
        txt(d,'प्रसार रोकना = तनाव बढ़ना',1400,61)
        txt(d,'चित्र में फैलाव बड़ा करके दिखाया है',1510,36,ui.MUTED)
    else:
        txt(d,'अब ठंड में क्या होगा?',330,80)
        txt(d,'गैप बढ़ेगा या घटेगा?',445,64,BLUE)
        if t<dur-1.8:
            rail(d,.7,y=920);txt(d,'A: बढ़ेगा     B: घटेगा',1390,62)
        else:
            rail(d,max(0,1-(t-(dur-1.8))/1.3),y=920)
            txt(d,'बढ़ेगा! लोहा सिकुड़ेगा।',1390,65,GREEN)
        txt(d,'Railway वाले दोस्त से पूछो',1510,43,ui.MUTED)
    txt(d,'जोड़ वाली पटरी का सरलीकृत उदाहरण',1585,27,ui.MUTED)
    return im

def xy(lon,lat):return 80+(lon-68)/30*920,610+(30-lat)/14*620
@lru_cache(maxsize=1)
def map_base():
    data=json.loads(Path('ist_region.json').read_text());im=Image.new('RGB',(1080,1920),BG)
    layer=Image.new('RGB',im.size,'#DCEFF4');d=ImageDraw.Draw(layer)
    for f in data['states']:
        for ring in f['rings']:
            pts=[xy(x,y) for x,y in ring]
            if len(pts)>2:d.polygon(pts,fill='#E6EDD7',outline='#D1D9C7',width=2)
    im.paste(layer.crop((80,610,1000,1230)),(80,610));d=ImageDraw.Draw(im)
    d.rectangle((80,610,1000,1230),outline='#9BBABD',width=3)
    return im
def clock(d,x,y,t=0):
    d.ellipse((x-100,y-100,x+100,y+100),fill='white',outline=INK,width=7)
    for a in range(12):
        z=a*math.pi/6;d.line((x+82*math.sin(z),y-82*math.cos(z),x+91*math.sin(z),y-91*math.cos(z)),fill=INK,width=4)
    d.line((x,y,x+58*math.sin(math.pi/3),y-58*math.cos(math.pi/3)),fill=INK,width=10)
    d.line((x,y,x,y-76),fill=BLUE,width=7)
    z=t*1.5;d.line((x,y,x+75*math.sin(z),y-75*math.cos(z)),fill=RED,width=3)
def pin(d,lon,lat,col=RED):
    x,y=xy(lon,lat);d.ellipse((x-12,y-12,x+12,y+12),fill=col,outline='white',width=3);return x,y
def meridian(d,p):
    x,_=xy(82.5,25);d.line((x,625,x,625+590*p),fill=RED,width=10)
def geo_frame(k,t,dur):
    p=min(1,t/max(.5,dur-.4));im=map_base().copy();d=ImageDraw.Draw(im)
    header(d,'one_clock',k,t,dur)
    if k==0:
        txt(d,'सूरज अलग समय पर…',305,81)
        txt(d,'फिर घड़ी एक क्यों?',410,88,RED)
        # Familiar clock comparison is visible immediately; maps ground the locations.
        clock(d,285,1400,t);clock(d,795,1400,t)
        txt(d,'गुजरात',1555,44,x=285);txt(d,'अरुणाचल',1555,44,x=795)
        a=pin(d,72.57,23.02,BLUE);b=pin(d,93.62,27.08,RED)
        sun(d,b[0],b[1]-90,34,t)
        txt(d,'सूरज पहले',b[1]+70,32,RED,x=b[0]-25)
        txt(d,'सूरज बाद में',a[1]+70,32,BLUE,x=a[0]+20)
    elif k==1:
        txt(d,'देशभर के लिए एक समय',315,77)
        txt(d,'भारतीय मानक समय / IST',435,58,BLUE)
        for pos in [(72.57,23.02),(82.5,25.15),(93.62,27.08)]:pin(d,*pos,GREEN)
        clock(d,540,1400,t);txt(d,'घड़ियाँ एक ही मानक समय पर',1555,45)
    elif k==2:
        txt(d,'इस रेखा को पकड़ लो',315,80)
        txt(d,'82.5 डिग्री पूर्व',435,78,RED)
        meridian(d,p);x,y=pin(d,82.5,25.15)
        box(d,(x+20,y-45,x+240,y+30),'white');txt(d,'मिर्जापुर',y-8,39,INK,x=x+130)
        txt(d,'उत्तर प्रदेश के मिर्जापुर के पास',1400,57)
        txt(d,'मानक देशांतर',1510,54,RED)
    elif k==3:
        txt(d,'यही है मानक देशांतर',315,76)
        txt(d,'82.5 डिग्री पूर्व',435,78,RED);meridian(d,1)
        x,y=pin(d,82.5,25.15);txt(d,'मिर्जापुर',y+55,36,INK,x=x+125)
        clock(d,290,1400,t);clock(d,790,1400,t)
        txt(d,'दो जगह। घड़ी का समय समान।',1555,48,GREEN)
    else:
        txt(d,'बिना देखे जवाब दो!',315,82)
        txt(d,'मानक देशांतर कितना?',435,68,BLUE);meridian(d,1)
        if t<dur-1.8:
            txt(d,'82.5 पूर्व  या  90 पूर्व?',1390,64)
        else:
            box(d,(110,1320,970,1460),'#DDEFE5');txt(d,'82.5 डिग्री पूर्व',1390,74,GREEN)
        txt(d,'घड़ी देखकर geography याद करो',1530,45)
    txt(d,'भारत का क्षेत्रीय मानचित्र • सरलीकृत',1270,27,ui.MUTED)
    return im
def render(id,k,t,dur):return (rail_frame if id=='rail_gap' else geo_frame)(k,t,dur)
def preview(id):
    out=ROOT/id;out.mkdir(parents=True,exist_ok=True);sheet=Image.new('RGB',(1080,768))
    for k in range(5):
        sheet.paste(render(id,k,.4,4).resize((216,384)),(k*216,0))
        sheet.paste(render(id,k,3.7,4).resize((216,384)),(k*216,384))
    sheet.save(out/'contact_sheet.jpg');render(id,0,0,4).save(out/'cover.jpg')
def build(id):
    import auto_poster as e
    import numpy as np
    out=ROOT/id;out.mkdir(parents=True,exist_ok=True);e.FPS=24
    vs=e.make_voices([{'segs':[(None,None,s)]} for s in SPEECH[id]],rot=1 if id=='one_clock' else 0)
    arrs=[x[0] for x in vs]
    if any(len(a)<e.SR*.5 or np.max(np.abs(a))<.001 for a in arrs):raise RuntimeError('Real narration required')
    mins=[2.7,2.7,3.2,3,4.8];durs=[max(len(a)/e.SR+.2,m) for a,m in zip(arrs,mins)]
    starts=[sum(durs[:i]) for i in range(5)];total=sum(durs);audio=e.beat_music(total,9)*.07
    for i,a in enumerate(arrs):
        e.add_at(audio,a.astype(np.float32),starts[i]+.06,1)
        if i:e.add_at(audio,e.sfx_pop(.13),starts[i])
    def frame(fi):
        t=fi/24;k=max(i for i,s in enumerate(starts) if s<=t);return render(id,k,t-starts[k],durs[k])
    e.encode_frames(frame,math.ceil(total*24),np.clip(audio,-.98,.98),str(out/'reel.mp4'),key=lambda fi:fi)
    (out/'caption.txt').write_text(CAPTIONS[id],encoding='utf-8');preview(id)
    m={'experiment':id,'duration':total,'scene_seconds':durs,'speech':SPEECH[id],'sources':SOURCES[id],
       'sha256':hashlib.sha256((out/'reel.mp4').read_bytes()).hexdigest(),
       'research':['https://creators.instagram.com/blog/helping-creators-of-all-sizes-break-through','https://creators.instagram.com/faq'],
       'hypothesis':'Immediate moving visual + specific question; no intro; explanation before CTA. Not a promised skip rate.'}
    (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print('BUILT',id,total)
def publish(id):
    import auto_poster as e
    out=ROOT/id;marker=out/'published.json'
    if marker.exists():print('Already published',id,marker.read_text());return
    req=json.loads(Path('experiments/retention_pilots_request.json').read_text());m=json.loads((out/'manifest.json').read_text())
    digest=hashlib.sha256((out/'reel.mp4').read_bytes()).hexdigest()
    if digest!=m['sha256'] or digest!=req.get('reviewed_sha256',{}).get(id):raise RuntimeError('Reviewed render mismatch')
    e._with_series=lambda c:c
    pid=e.post_reel(str(out/'reel.mp4'),(out/'caption.txt').read_text(),0)
    if not pid:raise RuntimeError('Instagram publication unconfirmed')
    result={'experiment':id,'media_id':pid,'sha256':digest,'published_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    marker.write_text(json.dumps(result,indent=2))
    try:
        r=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
        result['permalink']=r.get('permalink');marker.write_text(json.dumps(result,indent=2))
    except Exception:pass
    print('PUBLISH_RESULT',json.dumps(result))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['preview','build','publish']);ap.add_argument('--id',choices=IDS);a=ap.parse_args()
    for id in ([a.id] if a.id else IDS):{'preview':preview,'build':build,'publish':publish}[a.mode](id)
