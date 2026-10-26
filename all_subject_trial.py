"""Seven comparable 20-second GS pilots. Publishing is separately authorized by reviewed hashes."""
import argparse,hashlib,json,math,time,datetime
from pathlib import Path
from PIL import Image,ImageDraw
import one_confusion as ui
import retention_pilots as art

ROOT=Path('experiments/all_subject_trial_20261026')
PLAN=Path('experiments/all_subject_trial_plan.json')
DURS=[3.6,3.8,4.4,3.8,4.4]
INK=art.INK;BLUE=art.BLUE;RED=art.RED;GREEN=art.GREEN;BG=art.BG
TOPICS={
'history':{'subject':'इतिहास','title':'प्लासी या बक्सर: पहले कौन?',
 'speech':['प्लासी पहले हुई या बक्सर? दोनों का क्रम चुनो।','पहले प्लासी की लड़ाई, सत्रह सौ सत्तावन में।','फिर बक्सर की लड़ाई, सत्रह सौ चौंसठ में।','बीच में सात साल। क्रम है, प्लासी फिर बक्सर।','अब बताओ, सत्रह सौ चौंसठ वाली लड़ाई? बक्सर।'],
 'facts':'प्लासी 1757; बक्सर 1764; अंतर 7 वर्ष।',
 'source':'https://ncert.nic.in/textbook/pdf/hess202.pdf'},
'economics':{'subject':'अर्थशास्त्र','title':'कीमत वही। सामान कम?',
 'speech':['दस रुपये का पैकेट छोटा हुआ। महँगा हुआ या नहीं?','पहले सौ ग्राम के दस रुपये थे।','अब अस्सी ग्राम के भी दस रुपये हैं।','सौ ग्राम के हिसाब से कीमत साढ़े बारह रुपये हुई।','सामान कम, कीमत वही। इस तरीके को श्रिंकफ्लेशन कहते हैं।'],
 'facts':'काल्पनिक उदाहरण: 100 g / Rs 10 से 80 g / Rs 10. प्रति 100 g कीमत Rs 10 से Rs 12.50: 25% वृद्धि। यह किसी ब्रांड पर आरोप नहीं।',
 'source':'https://www.ons.gov.uk/economy/inflationandpriceindices/articles/theimpactofshrinkflationoncpihuk/howmanyofourproductsaregettingsmaller'},
'science':{'subject':'विज्ञान','title':'बस रुकी, शरीर आगे क्यों?',
 'speech':['बस ने ब्रेक लगाया। शरीर आगे क्यों झुका?','बस धीमी हुई, पैर फर्श के साथ रुकने लगे।','ऊपरी शरीर अपनी चाल बनाए रखना चाहता है। यही जड़त्व है।','न्यूटन का पहला नियम, अवस्था बदलने का विरोध।','अब बस अचानक चले तो झटका किधर? पीछे।'],
 'facts':'अचानक ब्रेक पर शरीर आगे झुकता है: गति का जड़त्व। अचानक चलने पर पीछे झुकना: विराम का जड़त्व। चित्र सापेक्ष गति का सरलीकृत प्रदर्शन है।',
 'source':'https://sathee.iitk.ac.in/ncert-books/ncert-books-theory/class-11/nbt-phy-11/phy-11-chapter-4-laws-of-motion/'},
'polity':{'subject':'राजव्यवस्था','title':'संविधान: 1949 या 1950?',
 'speech':['संविधान उन्नीस सौ उनचास का, या पचास का? फर्क देखो।','छब्बीस नवंबर उनचास: संविधान अपनाया गया।','छब्बीस जनवरी पचास: मुख्य प्रावधान लागू हुए।','याद रखो, नवंबर अपनाया। जनवरी लागू।','अब संविधान दिवस कब? छब्बीस नवंबर।'],
 'facts':'26 नवंबर 1949 को संविधान अपनाया गया। अनुच्छेद 394 के अनुसार कुछ प्रावधान तत्काल लागू हुए; शेष 26 जनवरी 1950 को। संविधान दिवस 26 नवंबर।',
 'source':'https://lddashboard.legislative.gov.in/sites/default/files/coi/COI_2024.pdf'},
'geography':{'subject':'भूगोल','title':'कर्क रेखा: UP या MP?',
 'speech':['कर्क रेखा उत्तर प्रदेश से गुजरती है या मध्य प्रदेश से?','यह लगभग साढ़े तेईस डिग्री उत्तरी अक्षांश है।','नक्शे में देखो, रेखा मध्य प्रदेश को काट रही है।','उत्तर प्रदेश इस रेखा के उत्तर में है।','अब चुनो, यू पी या एम पी? सही, मध्य प्रदेश।'],
 'facts':'कर्क रेखा लगभग 23.5° N है। भारत में गुजरात, राजस्थान, मध्य प्रदेश, छत्तीसगढ़, झारखंड, पश्चिम बंगाल, त्रिपुरा और मिजोरम से गुजरती है; उत्तर प्रदेश से नहीं। क्षेत्रीय मानचित्र सरलीकृत है।',
 'source':'https://ncert.nic.in/textbook/pdf/iess101.pdf'},
'current':{'subject':'करंट अफेयर्स','title':'शांति नोबेल 2026 किसे?',
 'speech':['दो हजार छब्बीस का शांति नोबेल किसे मिला? नाम पहचानो।','नवी पिल्लै को दो हजार छब्बीस का शांति नोबेल मिला।','वह दक्षिण अफ्रीका से हैं।','सम्मान शांति और अंतरराष्ट्रीय कानून के प्रयासों के लिए।','नाम फिर याद करो। नवी पिल्लै, दक्षिण अफ्रीका।'],
 'facts':'2026 Nobel Peace Prize: Navanethem (Navi) Pillay; दक्षिण अफ्रीका। घोषणा: 9 अक्टूबर 2026. विषय चयन/तथ्य जाँच: 26 अक्टूबर 2026; कोई AI portrait उपयोग नहीं।',
 'source':'https://www.nobelprize.org/prizes/peace/2026/summary/'},
'static_gk':{'subject':'सामान्य ज्ञान','title':'चक्र में 12 या 24 तीलियाँ?',
 'speech':['तिरंगे के चक्र में बारह तीलियाँ हैं या चौबीस?','पहला चौथाई देखो, छह तीलियाँ गिनो।','ऐसे चार हिस्से। हर हिस्से में छह।','छह गुना चार, यानी चौबीस तीलियाँ।','अब बिना गिने बताओ, कितनी? चौबीस।'],
 'facts':'राष्ट्रीय ध्वज के अशोक चक्र में 24 तीलियाँ होती हैं। गिनने का बड़ा चक्र अलग शिक्षण-रेखाचित्र है; तिरंगे के चित्र में हर समय 24 तीलियाँ हैं।',
 'source':'https://knowindia.india.gov.in/my-india-my-pride/indian-tricolor.php'}
}
def txt(d,s,y,n=62,col=INK,x=540):art.txt(d,s,y,n,col,x)
def box(d,b,fill='white',outline=None):art.box(d,b,fill,outline)
def title(d,id,k,t,dur):
    box(d,(70,155,1010,222),INK);txt(d,'20 सेकंड में GS  |  '+TOPICS[id]['subject'],188,36,'white')
    txt(d,TOPICS[id]['title'],330,71)
    box(d,(80,1640,1000,1649),'#D5DEDC');box(d,(80,1640,80+920*min(1,(k+t/dur)/5),1649),GREEN)
    txt(d,'@MinuteMe_GS  •  SSC / Railway GS',1710,34)
def card(d,x,y,label,year,col):
    box(d,(x-205,y-150,x+205,y+150),'white',col)
    txt(d,label,y-60,52,col,x=x);txt(d,year,y+65,76,INK,x=x)
def timeline(d,t,k,polity=False):
    d.line((160,1150,920,1150),fill='#B6C8C6',width=9)
    x=160+(760*(t/4)%760);d.ellipse((x-13,1137,x+13,1163),fill=BLUE)
    if polity:
        card(d,290,850,'अपनाया','1949' if k>=1 else '?',BLUE)
        card(d,790,850,'लागू','1950' if k>=2 else '?',GREEN)
        txt(d,'26 नवंबर' if k>=1 else 'नवंबर?',1200,44,BLUE,x=290)
        txt(d,'26 जनवरी' if k>=2 else 'जनवरी?',1200,44,GREEN,x=790)
    else:
        card(d,290,850,'प्लासी','1757' if k>=1 else '?',BLUE)
        card(d,790,850,'बक्सर','1764' if k>=2 else '?',GREEN)
        if k>=3:txt(d,'1764 - 1757 = 7 वर्ष',1260,62,RED)
def packet(d,x,grams,t):
    h=grams*3.5;top=1150-h
    box(d,(x-155,top,x+155,1160),'#E7B65F',INK)
    for yy in (top+12,1140):d.line((x-140,yy,x+140,yy),fill='#B37D2D',width=7)
    txt(d,str(grams)+' g',(top+1160)/2,78,x=x)
    txt(d,'Rs 10',1260,61,BLUE,x=x)
def passenger(d,x,y,lean=0):
    headx=x+lean;d.ellipse((headx-30,y-145,headx+30,y-85),fill='#F4C29E',outline=INK,width=3)
    d.line((headx,y-80,x,y+15),fill=GREEN,width=30)
    for dx in (-22,22):d.line((x,y+10,x+dx,y+95),fill=INK,width=15)
def bus(d,k,t):
    # Bus-relative frame: feet remain on floor while upper body leans.
    box(d,(100,650,980,1120),'#BDE0E8',INK)
    d.line((100,1050,980,1050),fill=INK,width=9)
    for x in (235,845):d.ellipse((x-50,1080,x+50,1180),fill=INK)
    stop=k in (0,1,2,3);lean=(1 if stop else -1)*min(85,85*(.5+.5*math.sin(t*2)))
    passenger(d,500,955,lean)
    for i in range(4):
        x=160+(i*220-t*130)%760;d.line((x,1230,x+95,1230),fill='#9BA9A7',width=9)
    if stop:txt(d,'ब्रेक!',570,68,RED)
    else:txt(d,'बस चल पड़ी!',570,63,BLUE)
def wheel(d,x,y,r,highlight=0):
    d.ellipse((x-r,y-r,x+r,y+r),outline='#15285D',width=max(5,int(r*.035)))
    for i in range(24):
        a=i*math.pi/12-math.pi/2
        col=RED if i<highlight else '#15285D'
        d.line((x,y,x+(r-4)*math.cos(a),y+(r-4)*math.sin(a)),fill=col,width=max(3,int(r*.023)))
    d.ellipse((x-r*.09,y-r*.09,x+r*.09,y+r*.09),fill='#15285D')
def flag(d):
    x,y,w,h=180,660,720,480
    for i,c in enumerate(('#FF9933','white','#138808')):d.rectangle((x,y+i*h/3,x+w,y+(i+1)*h/3),fill=c)
    wheel(d,540,y+h/2,69)
def geo(d,k,t,dur):
    data=json.loads(Path('ist_region.json').read_text())
    def xy(lon,lat):return 75+(lon-70)/19*930,600+(30-lat)/10*650
    layer=Image.new('RGB',(1080,1920),'#DCEFF4');ld=ImageDraw.Draw(layer)
    for f in data['states']:
        for ring in f['rings']:
            p=[xy(x,y) for x,y in ring]
            if len(p)>2:ld.polygon(p,fill='#FFE9B9' if f['name']=='Madhya Pradesh' else '#DFE8D9',outline='#A6B4A7',width=2)
    d._image.paste(layer.crop((75,600,1005,1250)),(75,600))
    y=xy(75,23.5)[1];end=1000 if k!=1 else 80+920*min(1,t/max(.2,dur-.3))
    d.line((80,y,end,y),fill=RED,width=10)
    txt(d,'मध्य प्रदेश',xy(78,24.2)[1],38,INK,x=xy(78,24.2)[0])
    txt(d,'उत्तर प्रदेश',xy(80.4,27.3)[1],36,INK,x=xy(80.4,27.3)[0])
    txt(d,'कर्क रेखा',y+55,39,RED,x=700)
    txt(d,'क्षेत्रीय मानचित्र • सरलीकृत',1300,27,ui.MUTED)
def medal(d,t):
    d.polygon([(390,590),(500,810),(580,810),(500,590)],fill=BLUE)
    d.polygon([(580,590),(500,810),(580,810),(690,590)],fill=RED)
    r=155+3*math.sin(t*3);d.ellipse((540-r,900-r,540+r,900+r),fill='#E5B84F',outline='#986C16',width=9)
    txt(d,'2026',900,84,col='#71521B')
def frame(id,k,t,dur):
    im=Image.new('RGB',(1080,1920),BG);d=ImageDraw.Draw(im);title(d,id,k,t,dur)
    if id=='history':
        timeline(d,t,k)
        lines=['अपना क्रम चुनो','पहले प्लासी: 1757','फिर बक्सर: 1764','प्लासी, फिर बक्सर','1764 की लड़ाई कौन सी?']
        txt(d,lines[k],480,62,BLUE)
        txt(d,'बक्सर!' if k==4 and t>dur-1.5 else ('दो घटनाएँ, सात साल का फ़र्क' if k>=2 else 'पहले कौन?'),1450,62,GREEN)
    elif id=='polity':
        timeline(d,t,k,True)
        lines=['दो तारीखें, दो अलग काम','26 नवंबर 1949: अपनाया','26 जनवरी 1950: मुख्यतः लागू','नवंबर अपनाया, जनवरी लागू','संविधान दिवस कब?']
        txt(d,lines[k],480,56,BLUE)
        txt(d,'26 नवंबर' if k==4 and t>dur-1.5 else ('1949  /  1950' if k<3 else 'अपनाना और लागू होना अलग'),1450,58,GREEN)
    elif id=='economics':
        left=100;right=100 if k<=1 else (100-int(20*min(1,t/(dur*.65))) if k==2 else 80)
        packet(d,285,left,t);packet(d,795,right,t)
        txt(d,['महँगा हुआ या नहीं?','पहले: 100 g = Rs 10','अब: 80 g = Rs 10','100 g की कीमत: Rs 12.50','इसका नाम क्या है?'][k],480,58,BLUE)
        txt(d,'Shrinkflation' if k==4 and t>dur-1.5 else ('प्रति मात्रा कीमत बढ़ी' if k>=3 else 'पैसे वही, सामान कम'),1450,62,GREEN)
    elif id=='science':
        bus(d,k,t)
        txt(d,['आगे का झटका क्यों?','पैर फर्श के साथ रुकते हैं','शरीर गति बनाए रखता है','जड़त्व / Newton का पहला नियम','चलने पर झटका किधर?'][k],440,55,BLUE)
        txt(d,'पीछे!' if k==4 and t>dur-1.5 else ('गति का जड़त्व' if k>=2 else 'ब्रेक और शरीर की चाल'),1440,69,GREEN)
    elif id=='geography':
        geo(d,k,t,dur)
        txt(d,['दो राज्यों में सही चुनो','लगभग 23.5 डिग्री उत्तर','रेखा MP से गुजरती है','UP इस रेखा के उत्तर में है','UP या MP?'][k],470,56,BLUE)
        txt(d,'मध्य प्रदेश' if k==4 and t>dur-1.5 else ('रेखा पर चलते जाओ' if k<3 else 'नक्शे से याद करो'),1450,64,GREEN)
    elif id=='static_gk':
        txt(d,['बिना गिने जवाब चुनो','एक हिस्से में 6','चार बराबर हिस्से','6 x 4 = 24','अब कितनी तीलियाँ?'][k],475,61,BLUE)
        if k==0:flag(d)
        else:
            wheel(d,540,920,220,min(6,int(t/(dur*.65)*6)) if k==1 else (6 if k==2 else 24))
            d.line((320,920,760,920),fill='#C7A4A4',width=2);d.line((540,700,540,1140),fill='#C7A4A4',width=2)
            txt(d,'गिनने का बड़ा रेखाचित्र',1250,31,ui.MUTED)
        txt(d,'24 तीलियाँ' if k==4 and t>dur-1.5 else ('चार हिस्से, छह-छह' if k>=2 else '12 या 24?'),1450,67,GREEN)
    elif id=='current':
        medal(d,t)
        txt(d,['पहले नाम पहचानो','नवी पिल्लै','दक्षिण अफ्रीका','शांति और अंतरराष्ट्रीय कानून','2026 का विजेता नाम?'][k],475,59,BLUE)
        txt(d,'नवी पिल्लै' if k==4 and t>dur-1.5 else ('शांति नोबेल' if k<2 else 'नवी पिल्लै • दक्षिण अफ्रीका'),1300,57,GREEN)
        txt(d,'घोषणा: 9 अक्टूबर 2026',1450,43,ui.MUTED)
    return im
def preview(id):
    out=ROOT/id;out.mkdir(parents=True,exist_ok=True);sh=Image.new('RGB',(1080,768))
    for k in range(5):
        sh.paste(frame(id,k,.4,DURS[k]).resize((216,384)),(216*k,0))
        sh.paste(frame(id,k,DURS[k]-.3,DURS[k]).resize((216,384)),(216*k,384))
    sh.save(out/'contact_sheet.jpg');frame(id,0,0,DURS[0]).save(out/'cover.jpg')
def caption(id):
    t=TOPICS[id]
    return f"{t['title']} | {t['subject']} | 20 सेकंड में GS\n\n{t['facts']}\n\nअंत का सवाल बिना देखे कर पाए? अपने study partner को भेजकर जाँचो।\n\nस्रोत: {t['source']}\nयह concept practice है; किसी खास परीक्षा का verified PYQ होने का दावा नहीं।\n\n#MinuteMeGS #GS #SSC #RailwayExam #StudyHindi"
def build(id):
    import auto_poster as e
    import numpy as np
    e.FPS=24;e.USE_GEMINI_TTS=False;e.VOICE_NAME='hi-IN-SwaraNeural';e.VOICE_RATE='+12%';e.VOICE_PITCH='+0Hz'
    out=ROOT/id;out.mkdir(parents=True,exist_ok=True)
    vv=e.make_voices([{'segs':[(None,None,s)]} for s in TOPICS[id]['speech']],rot=0)
    arr=[]
    for v,dur in zip(vv,DURS):
        a=v[0];seconds=len(a)/e.SR
        if seconds>dur-.18:
            rate=seconds/(dur-.18)
            if rate>1.4:raise RuntimeError('Narration too long for comparable pacing: '+id)
            a=e.speed_voice(a,rate)
        if len(a)<e.SR*.5 or np.max(np.abs(a))<.001:raise RuntimeError('Real narration required')
        arr.append(a)
    starts=[sum(DURS[:k]) for k in range(5)];audio=e.beat_music(20,12)*.065
    for k,a in enumerate(arr):
        e.add_at(audio,a.astype(np.float32),starts[k]+.06,1)
        if k:e.add_at(audio,e.sfx_pop(.12),starts[k])
    def render(fi):
        t=fi/24;k=max(k for k,s in enumerate(starts) if s<=t);return frame(id,k,t-starts[k],DURS[k])
    e.encode_frames(render,480,np.clip(audio,-.98,.98),str(out/'reel.mp4'),key=lambda fi:fi)
    preview(id);(out/'caption.txt').write_text(caption(id),encoding='utf-8')
    m={'id':id,'subject':TOPICS[id]['subject'],'title':TOPICS[id]['title'],'duration':20,'scene_seconds':DURS,'voice':'hi-IN-SwaraNeural','source':TOPICS[id]['source'],'speech':TOPICS[id]['speech'],'sha256':hashlib.sha256((out/'reel.mp4').read_bytes()).hexdigest()}
    (out/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print('BUILT',id)
def publish(id):
    import auto_poster as e
    out=ROOT/id;marker=out/'published.json'
    if marker.exists():print('ALREADY_PUBLISHED',marker.read_text());return
    plan=json.loads(PLAN.read_text());slot=next(s for s in plan['slots'] if s['id']==id)
    now=datetime.datetime.now(datetime.timezone.utc);due=datetime.datetime.fromisoformat(slot['publish_utc'].replace('Z','+00:00'))
    if now<due:raise RuntimeError('Not due yet; no early publication')
    if now>due+datetime.timedelta(minutes=50):raise RuntimeError('Missed slot; refusing compressed late batch')
    digest=hashlib.sha256((out/'reel.mp4').read_bytes()).hexdigest()
    if digest!=slot.get('approved_sha256'):raise RuntimeError('Reviewed video hash mismatch')
    e._with_series=lambda c:c
    pid=e.post_reel(str(out/'reel.mp4'),(out/'caption.txt').read_text(),0)
    if not pid:raise RuntimeError('Publication unconfirmed')
    r={'id':id,'subject':TOPICS[id]['subject'],'media_id':pid,'sha256':digest,'scheduled_utc':slot['publish_utc'],'published_utc':now.isoformat()}
    marker.write_text(json.dumps(r,ensure_ascii=False,indent=2))
    try:
        obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink,timestamp','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
        r['permalink']=obj.get('permalink');r['published_utc']=obj.get('timestamp',datetime.datetime.now(datetime.timezone.utc).isoformat());marker.write_text(json.dumps(r,ensure_ascii=False,indent=2))
    except Exception:pass
    print('PUBLISH_RESULT',json.dumps(r,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preview','build','publish']);p.add_argument('--id',choices=list(TOPICS));a=p.parse_args()
    if a.mode=='publish' and not a.id:raise SystemExit('One explicit scheduled subject required')
    for id in ([a.id] if a.id else TOPICS):{'preview':preview,'build':build,'publish':publish}[a.mode](id)
