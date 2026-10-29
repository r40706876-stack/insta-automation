"""Hand-written, fact-checked (NCERT level) story plans for every dropdown topic.
Run: python build_topics.py  -> topics/<slug>.json + topics/index.json (dropdown text -> file)."""
import json
from pathlib import Path
R = Path(__file__).parent

def S(id, sec, title, sub, focus, effects, labels=(), solid=None, layers=('skin', 'visceral'), angle='three_quarter', move='push', zoom=1.0, hide=(), quiz=None):
    s = {'id': id, 'seconds': sec, 'title': title, 'sub': sub, 'camera': {'focus': list(focus), 'angle': angle, 'move': move, 'zoom': zoom},
         'layers': list(layers), 'solid': list(solid if solid is not None else focus), 'effects': list(effects), 'labels': list(labels)}
    if hide: s['hide'] = list(hide)
    if quiz: s['quiz'] = dict(zip(('q', 'a', 'b'), quiz), cta='जवाब कमेंट में लिखो')
    return s
def Q(title, q, a, b, focus, effects, layers=('skin', 'visceral'), solid=None, angle='three_quarter'):
    return S('quiz', 5, title, '', focus, effects, (), solid, layers, angle, 'orbit', 1.0, quiz=(q, a, b))

C = ('skin', 'cardio'); CV = ('skin', 'visceral', 'cardio'); V = ('skin', 'visceral'); N_ = ('skin', 'nervous'); B = ('skin', 'skeletal')
BLOOD_OUT = 'travel:heart,aorta,arteries'; BLOOD_IN = 'travel:veins,vena_cava,heart'; AIR = 'travel:larynx,trachea,bronchi,lungs'
FOOD = 'travel:tongue,oesophagus,stomach,small_intestine,large_intestine'; SIGNAL = 'travel:brain,spinal_cord,nerves'; URINE = 'travel:kidneys,ureters,bladder'

T = {}
T['दिल एक दिन में कितनी बार धड़कता है'] = ('heart_beats', ['धड़कन', 'पंप', 'शरीर', 'याद'], [
    S('hook', 3.5, 'ये दिल रुकता क्यों नहीं?', 'एक दिन में लगभग 1 लाख धड़कन', ['heart'], ['beat', 'flow:heart'], ['heart'], layers=CV, zoom=1.2),
    S('rate', 5.5, '1 मिनट में लगभग 72 बार', '72 × 60 × 24 = करीब 1 लाख धड़कन रोज़', ['heart'], ['beat', BLOOD_OUT], ['heart', 'aorta'], ['heart', 'aorta'], C, zoom=1.1),
    S('pump', 5.5, 'हर धड़कन = खून का धक्का', 'धमनियों से पूरे शरीर में खून पहुँचता है', ['skin'], ['beat', BLOOD_OUT, 'flow:arteries'], ['heart', 'aorta'], ['heart', 'aorta', 'arteries'], C, hide=['veins', 'vena_cava'], zoom=1.35),
    S('size', 5.5, 'मुट्ठी जितना, चार कक्ष', 'दो अलिंद ऊपर, दो निलय नीचे', ['heart'], ['beat', 'pulse:heart'], ['heart'], ['heart'], C, 'front', 'orbit', 1.25),
    Q('परीक्षा का पक्का सवाल', 'सामान्य व्यक्ति का दिल 1 मिनट में कितनी बार धड़कता है?', 'A) लगभग 72 बार', 'B) लगभग 150 बार', ['heart'], ['beat', BLOOD_OUT], C)])
T['धमनी और शिरा में अंतर'] = ('artery_vein', ['धमनी', 'शिरा', 'दीवार', 'याद'], [
    S('hook', 3.5, 'लाल नली या नीली नली?', 'धमनी और शिरा का असली फ़र्क', ['heart', 'aorta'], [BLOOD_OUT], ['heart'], ['heart', 'aorta', 'arteries', 'veins'], C, zoom=1.1),
    S('artery', 6, 'धमनी: दिल से बाहर', 'ऑक्सीजन वाला शुद्ध खून शरीर तक ले जाती है', ['skin'], ['beat', BLOOD_OUT, 'flow:arteries'], ['aorta'], ['heart', 'aorta', 'arteries'], C, hide=['veins', 'vena_cava'], zoom=1.35),
    S('vein', 6, 'शिरा: वापस दिल तक', 'अशुद्ध खून लौटाती है, इसमें वाल्व होते हैं', ['skin'], ['beat', BLOOD_IN, 'flow:veins'], ['vena_cava'], ['heart', 'veins', 'vena_cava'], C, 'three_quarter_left', 'pull', 1.35, hide=['arteries', 'aorta']),
    S('wall', 5, 'धमनी की दीवार मोटी', 'तेज़ दबाव झेलती है, शिरा की दीवार पतली', ['heart', 'aorta'], ['beat', 'flow:aorta'], ['aorta', 'vena_cava'], ['heart', 'aorta', 'vena_cava'], C, 'front', 'orbit', 1.2),
    Q('परीक्षा का पक्का सवाल', 'किस नली में वाल्व होते हैं?', 'A) शिरा', 'B) धमनी', ['heart'], ['beat', BLOOD_IN], C)])
T['फुफ्फुसीय धमनी अशुद्ध खून क्यों ले जाती है'] = ('pulmonary_artery', ['दिल', 'फेफड़े', 'शुद्ध', 'याद'], [
    S('hook', 3.5, 'धमनी में अशुद्ध खून?', 'ये परीक्षा का सबसे बड़ा ट्रिक सवाल है', ['heart', 'lungs'], ['beat', 'travel:heart,pulmonary_vessels,lungs'], ['pulmonary_vessels'], ['heart', 'pulmonary_vessels'], CV),
    S('rule', 5.5, 'धमनी का नियम: दिल से बाहर', 'खून शुद्ध हो या अशुद्ध, दिल से बाहर = धमनी', ['heart'], ['beat', 'flow:pulmonary_vessels'], ['heart', 'pulmonary_vessels'], ['heart', 'pulmonary_vessels'], CV, 'front', 'orbit', 1.2),
    S('to_lungs', 6, 'फुफ्फुसीय धमनी → फेफड़े', 'दायाँ निलय अशुद्ध खून फेफड़ों में भेजता है', ['lungs'], ['beat', 'breathe', 'travel:heart,pulmonary_vessels,lungs'], ['lungs', 'pulmonary_vessels'], ['lungs', 'heart', 'pulmonary_vessels'], CV, 'front', 'push', 1.05),
    S('back', 6, 'फुफ्फुसीय शिरा: शुद्ध खून', 'फेफड़ों से ऑक्सीजन लेकर खून दिल में लौटता है', ['lungs', 'heart'], ['breathe', 'particles:lungs,heart,oxygen'], ['heart', 'lungs'], ['lungs', 'heart', 'pulmonary_vessels'], CV, 'three_quarter_left', 'pull'),
    Q('परीक्षा का पक्का सवाल', 'कौन-सी शिरा शुद्ध खून ले जाती है?', 'A) महाशिरा', 'B) फुफ्फुसीय शिरा', ['heart', 'lungs'], ['beat', 'breathe'], CV)])
T['दोहरा परिसंचरण: दिल से फेफड़े और पूरा शरीर'] = ('double_circulation', ['फेफड़े', 'शरीर', 'दोहरा', 'याद'], [
    S('hook', 3.5, 'खून दो बार दिल से क्यों?', 'इसे कहते हैं दोहरा परिसंचरण', ['heart'], ['beat', 'pulse:heart'], ['heart'], ['heart'], CV, zoom=1.2),
    S('small', 6, 'पहला चक्कर: फेफड़ों तक', 'दिल → फेफड़े → दिल, खून में ऑक्सीजन भरती है', ['lungs', 'heart'], ['beat', 'breathe', 'travel:heart,pulmonary_vessels,lungs', 'particles:lungs,heart,oxygen'], ['lungs', 'heart'], ['lungs', 'heart', 'pulmonary_vessels'], CV, 'front'),
    S('big', 6, 'दूसरा चक्कर: पूरे शरीर तक', 'दिल → धमनियाँ → अंग → शिराएँ → दिल', ['skin'], ['beat', BLOOD_OUT, 'flow:arteries'], ['heart', 'aorta'], ['heart', 'aorta', 'arteries'], C, hide=['veins', 'vena_cava'], zoom=1.35),
    S('return', 5.5, 'शिराएँ खून वापस लाती हैं', 'एक पूरे चक्कर में खून दिल से 2 बार गुज़रता है', ['skin'], ['beat', BLOOD_IN, 'flow:veins'], ['vena_cava'], ['heart', 'veins', 'vena_cava'], C, 'three_quarter_left', 'pull', 1.35, hide=['arteries', 'aorta']),
    Q('परीक्षा का पक्का सवाल', 'मनुष्य के हृदय में कितने कक्ष होते हैं?', 'A) तीन', 'B) चार', ['heart'], ['beat'], CV)])
T['महाधमनी: शरीर की सबसे बड़ी धमनी'] = ('aorta', ['दिल', 'महाधमनी', 'शाखाएँ', 'याद'], [
    S('hook', 3.5, 'शरीर की सबसे बड़ी धमनी?', 'दिल से निकलती है ये मोटी नली', ['heart', 'aorta'], ['beat', 'travel:heart,aorta'], ['aorta'], ['heart', 'aorta'], C, zoom=1.1),
    S('start', 5.5, 'बायाँ निलय → महाधमनी', 'सबसे ताकतवर धक्का बायाँ निलय देता है', ['heart'], ['beat', 'flow:aorta'], ['heart', 'aorta'], ['heart', 'aorta'], C, 'front', 'orbit', 1.25),
    S('branch', 6, 'महाधमनी से सारी शाखाएँ', 'सिर, हाथ, पेट, पैर — हर जगह शुद्ध खून', ['skin'], ['beat', BLOOD_OUT, 'flow:arteries'], ['aorta'], ['heart', 'aorta', 'arteries'], C, hide=['veins', 'vena_cava'], zoom=1.35),
    S('vein', 5, 'सबसे बड़ी शिरा: महाशिरा', 'पूरे शरीर का खून इसी से दिल में लौटता है', ['heart', 'vena_cava'], ['beat', BLOOD_IN], ['vena_cava'], ['heart', 'vena_cava', 'veins'], C, 'three_quarter_left', 'pull', 1.1, hide=['arteries', 'aorta']),
    Q('परीक्षा का पक्का सवाल', 'शरीर की सबसे बड़ी धमनी कौन-सी है?', 'A) महाधमनी', 'B) फुफ्फुसीय धमनी', ['heart', 'aorta'], ['beat', 'flow:aorta'], C)])
T['साँस लेने की प्रक्रिया: नाक से फेफड़ों तक'] = ('breathing', ['नाक', 'श्वासनली', 'फेफड़े', 'याद'], [
    S('hook', 3.5, 'हवा अंदर जाकर कहाँ जाती है?', 'एक साँस का पूरा सफ़र', ['lungs'], ['breathe', AIR], ['lungs'], ['lungs', 'trachea', 'bronchi', 'larynx'], V, 'front', zoom=1.05),
    S('nose', 5, 'नाक → ग्रसनी → स्वरयंत्र', 'नाक के बाल और म्यूकस धूल रोकते हैं', ['larynx', 'trachea'], ['travel:pharynx,larynx,trachea'], ['larynx', 'trachea'], ['pharynx', 'larynx', 'trachea'], V, 'side', zoom=1.3),
    S('tube', 5.5, 'श्वासनली से दो श्वसनी', 'हवा दाएँ और बाएँ फेफड़े में बँट जाती है', ['trachea', 'bronchi'], ['breathe', 'travel:trachea,bronchi'], ['trachea', 'bronchi'], ['trachea', 'bronchi', 'lungs'], V, 'front', 'push', 1.15),
    S('exchange', 6, 'वायुकोष में गैसों की अदला-बदली', 'ऑक्सीजन खून में जाती है, CO₂ बाहर आती है', ['lungs', 'heart'], ['breathe', 'beat', 'particles:lungs,heart,oxygen'], ['lungs', 'heart'], ['lungs', 'heart'], CV, 'three_quarter_left'),
    Q('परीक्षा का पक्का सवाल', 'फेफड़ों में गैसों का आदान-प्रदान कहाँ होता है?', 'A) वायुकोष (एल्वियोली)', 'B) श्वासनली', ['lungs'], ['breathe', AIR], V, angle='front')])
T['श्वासनली और श्वसनी का काम'] = ('trachea_bronchi', ['श्वासनली', 'छल्ले', 'श्वसनी', 'याद'], [
    S('hook', 3.5, 'ये नली पिचकती क्यों नहीं?', 'राज़ है इसके छल्लों में', ['trachea'], ['travel:larynx,trachea'], ['trachea'], ['trachea', 'larynx'], V, 'side', zoom=1.4),
    S('rings', 5.5, 'C-आकार के उपास्थि छल्ले', 'ये श्वासनली को हमेशा खुला रखते हैं', ['trachea'], ['breathe', 'flow:trachea'], ['trachea'], ['trachea', 'bronchi'], V, 'front', 'orbit', 1.4),
    S('split', 5.5, 'नीचे जाकर दो श्वसनी', 'एक दाएँ फेफड़े में, एक बाएँ फेफड़े में', ['bronchi'], ['breathe', 'travel:trachea,bronchi,lungs'], ['bronchi', 'lungs'], ['trachea', 'bronchi', 'lungs'], V, 'front', 'push', 1.1),
    S('lobes', 5.5, 'दायाँ फेफड़ा 3 पालियाँ, बायाँ 2', 'बाईं ओर दिल के लिए जगह छोड़नी होती है', ['lungs'], ['breathe', 'beat', 'sequence:lungs,heart'], ['lungs', 'heart'], ['lungs', 'heart'], CV, 'front', 'orbit', 1.05),
    Q('परीक्षा का पक्का सवाल', 'बाएँ फेफड़े में कितनी पालियाँ होती हैं?', 'A) तीन', 'B) दो', ['lungs'], ['breathe'], V, angle='front')])
T['स्वरयंत्र: आवाज़ कहाँ से बनती है'] = ('larynx_voice', ['स्वरयंत्र', 'स्वर-रज्जु', 'ढक्कन', 'याद'], [
    S('hook', 3.5, 'आपकी आवाज़ कहाँ बनती है?', 'गले के इस छोटे से डिब्बे में', ['larynx'], ['travel:larynx,trachea', 'pulse:larynx'], ['larynx'], ['larynx', 'trachea'], V, 'side', zoom=1.5),
    S('box', 5.5, 'स्वरयंत्र = वॉयस बॉक्स', 'इसमें स्वर-रज्जु (वोकल कॉर्ड) होते हैं', ['larynx'], ['pulse:larynx', 'flow:larynx'], ['larynx', 'thyroid'], ['larynx', 'thyroid'], V, 'front', 'orbit', 1.5),
    S('vibrate', 5.5, 'हवा से रज्जु काँपते हैं', 'इसी कंपन से आवाज़ पैदा होती है', ['larynx', 'trachea'], ['travel:trachea,larynx', 'pulse:larynx'], ['larynx'], ['larynx', 'trachea'], V, 'side', 'push', 1.4),
    S('lid', 5.5, 'एपिग्लॉटिस: खाने का ढक्कन', 'निगलते समय भोजन को श्वासनली में जाने से रोकता है', ['pharynx', 'larynx'], ['travel:tongue,pharynx,oesophagus'], ['pharynx', 'oesophagus'], ['pharynx', 'larynx', 'oesophagus'], V, 'side', zoom=1.4),
    Q('परीक्षा का पक्का सवाल', 'स्वरयंत्र को आम भाषा में क्या कहते हैं?', 'A) वॉयस बॉक्स', 'B) विंड पाइप', ['larynx'], ['pulse:larynx'], V, angle='side')])
T['फेफड़े: शरीर में ऑक्सीजन का दरवाज़ा'] = ('lungs', ['फेफड़े', 'वायुकोष', 'खून', 'याद'], [
    S('hook', 3.5, 'फेफड़े खुद साँस नहीं लेते!', 'तो फिर ये फूलते कैसे हैं?', ['lungs'], ['breathe', 'pulse:lungs'], ['lungs'], ['lungs'], V, 'front', zoom=1.05),
    S('diaphragm', 5.5, 'डायाफ्राम नीचे खिंचता है', 'छाती में जगह बनती है, हवा अंदर आती है', ['lungs'], ['breathe', AIR], ['lungs', 'trachea'], ['lungs', 'trachea', 'bronchi'], V, 'front', 'push'),
    S('alveoli', 6, 'करोड़ों छोटे वायुकोष', 'यहाँ ऑक्सीजन खून में घुलती है', ['lungs', 'heart'], ['breathe', 'beat', 'particles:lungs,heart,oxygen'], ['lungs'], ['lungs', 'heart'], CV, 'three_quarter_left'),
    S('ribs', 5, 'पसलियाँ फेफड़ों की ढाल', 'दिल और फेफड़ों की रक्षा करती हैं', ['ribs'], ['breathe', 'sequence:ribs,lungs'], ['ribs', 'lungs'], ['ribs', 'lungs'], ('skin', 'visceral', 'skeletal'), 'front', 'orbit', 1.0),
    Q('परीक्षा का पक्का सवाल', 'साँस लेने में मुख्य पेशी कौन-सी है?', 'A) डायाफ्राम', 'B) हृदय पेशी', ['lungs'], ['breathe', AIR], V, angle='front')])
T['ग्रासनली: भोजन की नली'] = ('oesophagus', ['मुँह', 'ग्रासनली', 'आमाशय', 'याद'], [
    S('hook', 3.5, 'उल्टा लटककर भी खाना पेट में!', 'ग्रासनली का कमाल', ['oesophagus'], ['travel:tongue,pharynx,oesophagus,stomach'], ['oesophagus'], ['oesophagus', 'stomach', 'tongue'], V, 'side', zoom=1.0),
    S('tube', 5.5, 'लगभग 25 सेमी लंबी नली', 'गले से आमाशय तक भोजन ले जाती है', ['oesophagus'], ['travel:pharynx,oesophagus', 'flow:oesophagus'], ['oesophagus'], ['oesophagus', 'pharynx'], V, 'side', 'push', 1.0),
    S('wave', 6, 'क्रमाकुंचन: लहर जैसी गति', 'पेशियाँ सिकुड़कर भोजन को नीचे धकेलती हैं', ['oesophagus', 'stomach'], ['travel:oesophagus,stomach', 'pulse:oesophagus'], ['oesophagus', 'stomach'], ['oesophagus', 'stomach'], V, 'three_quarter', 'rise'),
    S('gate', 5, 'नीचे एक वाल्व', 'भोजन वापस ऊपर नहीं आता', ['stomach'], ['travel:oesophagus,stomach', 'pulse:stomach'], ['stomach'], ['oesophagus', 'stomach'], V, 'front', 'push', 1.2),
    Q('परीक्षा का पक्का सवाल', 'भोजन नली में भोजन किस गति से आगे बढ़ता है?', 'A) क्रमाकुंचन', 'B) परासरण', ['oesophagus'], ['travel:oesophagus,stomach'], V, angle='side')])
T['आमाशय में भोजन का पाचन'] = ('stomach', ['आमाशय', 'अम्ल', 'प्रोटीन', 'याद'], [
    S('hook', 3.5, 'पेट में तेज़ाब, फिर भी सुरक्षित!', 'आमाशय का अनोखा राज़', ['stomach'], ['pulse:stomach', 'travel:oesophagus,stomach'], ['stomach'], ['stomach', 'oesophagus'], V, zoom=1.2),
    S('churn', 5.5, 'आमाशय भोजन को मथता है', 'पेशियाँ भोजन को घोल जैसा बना देती हैं', ['stomach'], ['pulse:stomach', 'travel:stomach'], ['stomach'], ['stomach'], V, 'three_quarter', 'orbit', 1.3),
    S('acid', 5.5, 'हाइड्रोक्लोरिक अम्ल (HCl)', 'कीटाणु मारता है, पेप्सिन को सक्रिय करता है', ['stomach'], ['pulse:stomach', 'flow:stomach'], ['stomach', 'liver'], ['stomach', 'liver'], V, 'front', 'push', 1.25),
    S('protein', 5.5, 'प्रोटीन का पाचन यहीं शुरू', 'श्लेष्मा (म्यूकस) पेट की दीवार को बचाता है', ['stomach', 'small_intestine'], ['travel:stomach,small_intestine'], ['stomach', 'small_intestine'], ['stomach', 'small_intestine'], V, 'three_quarter_left'),
    Q('परीक्षा का पक्का सवाल', 'आमाशय में कौन-सा अम्ल बनता है?', 'A) हाइड्रोक्लोरिक अम्ल', 'B) सल्फ्यूरिक अम्ल', ['stomach'], ['pulse:stomach'], V)])
T['छोटी आँत में पाचन और अवशोषण'] = ('small_intestine', ['पाचन', 'रस', 'अवशोषण', 'याद'], [
    S('hook', 3.5, 'शरीर की सबसे लंबी नली कौन?', 'पेट में मुड़ी हुई है', ['small_intestine'], ['travel:stomach,small_intestine'], ['small_intestine'], ['small_intestine', 'stomach'], V, 'front', zoom=1.1),
    S('long', 5.5, 'आहार नाल का सबसे लंबा भाग', 'लगभग 7.5 मीटर, कुंडली जैसी मुड़ी हुई', ['small_intestine'], ['travel:small_intestine', 'pulse:small_intestine'], ['small_intestine'], ['small_intestine'], V, 'front', 'orbit', 1.25),
    S('juices', 5.5, 'पित्त और अग्न्याशय रस', 'पाचन यहीं पूरा होता है', ['small_intestine', 'pancreas'], ['travel:liver,gallbladder,small_intestine', 'particles:pancreas,small_intestine,nutrient'], ['pancreas', 'gallbladder'], ['small_intestine', 'pancreas', 'liver', 'gallbladder'], V),
    S('villi', 6, 'दीर्घरोम (विलाई) सोखते हैं', 'पचा हुआ भोजन खून में चला जाता है', ['small_intestine', 'liver'], ['travel:small_intestine', 'particles:small_intestine,liver,nutrient'], ['small_intestine', 'liver'], ['small_intestine', 'liver'], V, 'three_quarter_left'),
    Q('परीक्षा का पक्का सवाल', 'आहार नाल का सबसे लंबा भाग कौन-सा है?', 'A) छोटी आँत', 'B) बड़ी आँत', ['small_intestine'], ['travel:small_intestine'], V, angle='front')])
T['बड़ी आँत का काम'] = ('large_intestine', ['बड़ी आँत', 'पानी', 'बाहर', 'याद'], [
    S('hook', 3.5, 'मोटी, पर छोटी — कौन?', 'बड़ी आँत का असली काम', ['large_intestine'], ['travel:small_intestine,large_intestine'], ['large_intestine'], ['large_intestine', 'small_intestine'], V, 'front', zoom=1.05),
    S('frame', 5.5, 'छोटी आँत को घेरे हुए', 'लगभग 1.5 मीटर लंबी, पर ज़्यादा चौड़ी', ['large_intestine'], ['travel:large_intestine'], ['large_intestine', 'small_intestine'], ['large_intestine', 'small_intestine'], V, 'front', 'orbit'),
    S('water', 6, 'पानी और लवण सोखती है', 'बचा अपशिष्ट गाढ़ा हो जाता है', ['large_intestine'], ['travel:large_intestine', 'particles:large_intestine,veins,water'], ['large_intestine'], ['large_intestine'], V, 'three_quarter_left', 'push', 1.15),
    S('out', 5, 'मलाशय से बाहर', 'अपचा भोजन शरीर से बाहर निकलता है', ['large_intestine'], ['travel:large_intestine', 'pulse:large_intestine'], ['large_intestine', 'appendix'], ['large_intestine', 'appendix'], V, 'front', 'rise', 1.15),
    Q('परीक्षा का पक्का सवाल', 'बड़ी आँत मुख्य रूप से क्या सोखती है?', 'A) पानी और लवण', 'B) प्रोटीन', ['large_intestine'], ['travel:large_intestine'], V, angle='front')])
T['अपेंडिक्स: एक अवशेषी अंग'] = ('appendix', ['कहाँ', 'अवशेषी', 'सूजन', 'याद'], [
    S('hook', 3.5, 'ये छोटा अंग किसी काम का नहीं?', 'मिलिए अपेंडिक्स से', ['appendix'], ['travel:small_intestine,large_intestine,appendix', 'pulse:appendix'], ['appendix'], ['appendix', 'large_intestine'], V, 'front', zoom=1.5),
    S('where', 5.5, 'पेट के दाईं ओर नीचे', 'बड़ी आँत की शुरुआत (सीकम) से जुड़ा', ['appendix', 'large_intestine'], ['travel:large_intestine,appendix'], ['appendix', 'large_intestine'], ['appendix', 'large_intestine', 'small_intestine'], V, 'front', 'push', 1.25),
    S('vestigial', 5.5, 'अवशेषी अंग', 'मनुष्य में इसका पाचन में खास काम नहीं', ['appendix'], ['pulse:appendix', 'flow:appendix'], ['appendix'], ['appendix', 'large_intestine'], V, 'three_quarter', 'orbit', 1.6),
    S('swell', 5.5, 'सूजन = अपेंडिसाइटिस', 'तब ऑपरेशन से इसे निकालना पड़ता है', ['appendix'], ['pulse:appendix'], ['appendix'], ['appendix'], V, 'front', 'push', 1.7),
    Q('परीक्षा का पक्का सवाल', 'मनुष्य में अवशेषी अंग कौन-सा है?', 'A) अपेंडिक्स', 'B) अग्न्याशय', ['appendix'], ['pulse:appendix'], V, angle='front')])
T['जीभ और स्वाद'] = ('tongue', ['जीभ', 'स्वाद', 'निगलना', 'याद'], [
    S('hook', 3.5, 'नाक बंद तो स्वाद गायब!', 'जीभ और स्वाद का रिश्ता', ['tongue'], ['pulse:tongue', 'flow:tongue'], ['tongue'], ['tongue', 'teeth'], ('skin', 'visceral', 'skeletal'), 'side', zoom=1.6),
    S('buds', 5.5, 'जीभ पर स्वाद कलिकाएँ', 'मीठा, नमकीन, खट्टा, कड़वा पहचानती हैं', ['tongue'], ['pulse:tongue', 'flow:tongue'], ['tongue'], ['tongue'], V, 'front', 'orbit', 1.7),
    S('chew', 5.5, 'चबाने में मदद', 'जीभ भोजन को दाँतों के बीच घुमाती है', ['tongue', 'teeth'], ['pulse:tongue', 'sequence:teeth,tongue'], ['tongue', 'teeth'], ['tongue', 'teeth'], ('skin', 'visceral', 'skeletal'), 'side', 'push', 1.6),
    S('swallow', 5.5, 'निगलने की शुरुआत', 'भोजन को गले की ओर धकेलती है', ['tongue', 'oesophagus'], ['travel:tongue,pharynx,oesophagus'], ['tongue', 'pharynx'], ['tongue', 'pharynx', 'oesophagus'], V, 'side', zoom=1.3),
    Q('परीक्षा का पक्का सवाल', 'जीभ पर स्वाद किससे पहचाना जाता है?', 'A) स्वाद कलिकाएँ', 'B) दीर्घरोम', ['tongue'], ['pulse:tongue'], V, angle='side')])
T['यकृत: शरीर की सबसे बड़ी ग्रंथि'] = ('liver', ['यकृत', 'पित्त', 'भंडार', 'याद'], [
    S('hook', 3.5, 'शरीर की सबसे बड़ी ग्रंथि?', 'पेट के दाईं ओर ऊपर', ['liver'], ['pulse:liver', 'flow:liver'], ['liver'], ['liver'], V, zoom=1.2),
    S('where', 5.5, 'यकृत (लिवर) दाईं ओर', 'डायाफ्राम के ठीक नीचे, आमाशय के पास', ['liver', 'stomach'], ['sequence:liver,stomach'], ['liver', 'stomach'], ['liver', 'stomach'], V, 'front', 'orbit'),
    S('bile', 6, 'पित्त रस बनाता है', 'पित्त वसा के पाचन में मदद करता है', ['liver', 'gallbladder'], ['travel:liver,gallbladder,small_intestine'], ['liver', 'gallbladder'], ['liver', 'gallbladder', 'small_intestine'], V, 'three_quarter', 'push', 1.2),
    S('store', 5.5, 'ग्लाइकोजन का भंडार', 'ज़रूरत पर खून में शुगर छोड़ता है', ['liver'], ['particles:small_intestine,liver,nutrient', 'pulse:liver'], ['liver', 'small_intestine'], ['liver', 'small_intestine'], V, 'three_quarter_left'),
    Q('परीक्षा का पक्का सवाल', 'मानव शरीर की सबसे बड़ी ग्रंथि कौन-सी है?', 'A) यकृत', 'B) अग्न्याशय', ['liver'], ['pulse:liver'], V)])
T['पित्ताशय और पित्त रस का काम'] = ('gallbladder', ['यकृत', 'पित्ताशय', 'वसा', 'याद'], [
    S('hook', 3.5, 'हरे रंग की छोटी थैली क्या है?', 'यकृत के नीचे छिपी है', ['gallbladder'], ['pulse:gallbladder', 'travel:liver,gallbladder'], ['gallbladder'], ['gallbladder', 'liver'], V, zoom=1.5),
    S('make', 5.5, 'पित्त यकृत में बनता है', 'पित्ताशय उसे जमा करके रखता है', ['liver', 'gallbladder'], ['travel:liver,gallbladder'], ['liver', 'gallbladder'], ['liver', 'gallbladder'], V, 'front', 'push', 1.15),
    S('release', 5.5, 'भोजन आते ही पित्त छोटी आँत में', 'ग्रहणी (ड्यूओडेनम) में पहुँचता है', ['gallbladder', 'small_intestine'], ['travel:gallbladder,small_intestine', 'pulse:gallbladder'], ['gallbladder', 'small_intestine'], ['gallbladder', 'small_intestine', 'liver'], V),
    S('fat', 5.5, 'वसा को छोटी बूँदों में तोड़ता है', 'पित्त में कोई एंजाइम नहीं होता', ['small_intestine'], ['travel:small_intestine', 'particles:gallbladder,small_intestine,nutrient'], ['small_intestine'], ['small_intestine', 'gallbladder'], V, 'front', 'orbit'),
    Q('परीक्षा का पक्का सवाल', 'पित्त रस कहाँ बनता है?', 'A) पित्ताशय', 'B) यकृत', ['liver', 'gallbladder'], ['pulse:gallbladder'], V)])
T['अग्न्याशय: इंसुलिन बनाने वाली ग्रंथि'] = ('pancreas', ['अग्न्याशय', 'रस', 'इंसुलिन', 'याद'], [
    S('hook', 3.5, 'एक अंग, दो काम!', 'पाचन भी, हार्मोन भी', ['pancreas'], ['pulse:pancreas', 'flow:pancreas'], ['pancreas'], ['pancreas'], V, zoom=1.4),
    S('where', 5.5, 'आमाशय के पीछे', 'पत्ती जैसी लंबी ग्रंथि', ['pancreas', 'stomach'], ['sequence:stomach,pancreas'], ['pancreas', 'stomach'], ['pancreas', 'stomach'], V, 'front', 'orbit', 1.2),
    S('juice', 5.5, 'अग्न्याशय रस → छोटी आँत', 'प्रोटीन, वसा, कार्बोहाइड्रेट का पाचन', ['pancreas', 'small_intestine'], ['travel:pancreas,small_intestine', 'particles:pancreas,small_intestine,nutrient'], ['pancreas', 'small_intestine'], ['pancreas', 'small_intestine'], V),
    S('insulin', 6, 'लैंगरहैंस द्वीप: इंसुलिन', 'खून में शुगर घटाता है, कमी से मधुमेह', ['pancreas'], ['particles:pancreas,veins,nutrient', 'pulse:pancreas'], ['pancreas'], ['pancreas'], V, 'three_quarter_left', 'push', 1.4),
    Q('परीक्षा का पक्का सवाल', 'इंसुलिन की कमी से कौन-सा रोग होता है?', 'A) मधुमेह', 'B) घेंघा', ['pancreas'], ['pulse:pancreas'], V)])
T['किडनी खून को कैसे साफ़ करती है'] = ('kidney', ['खून', 'छानना', 'मूत्र', 'याद'], [
    S('hook', 3.5, 'शरीर का फ़िल्टर कौन?', 'रोज़ खून को बार-बार साफ़ करता है', ['kidneys'], ['pulse:kidneys', 'particles:arteries,kidneys,blood'], ['kidneys'], ['kidneys'], V, 'back', zoom=1.2),
    S('where', 5.5, 'पीठ की ओर, दो सेम जैसे', 'कमर के ऊपर, रीढ़ के दोनों ओर', ['kidneys'], ['sequence:kidneys,adrenal'], ['kidneys', 'adrenal'], ['kidneys', 'adrenal'], V, 'back', 'orbit', 1.1),
    S('filter', 6, 'नेफ्रॉन: छलनी की इकाई', 'खून से यूरिया और ज़्यादा पानी छानते हैं', ['kidneys'], ['particles:arteries,kidneys,blood', 'pulse:kidneys', 'flow:kidneys'], ['kidneys'], ['kidneys'], V, 'back', 'push', 1.35),
    S('urine', 5.5, 'बचा = मूत्र', 'मूत्रवाहिनी से मूत्राशय तक जाता है', ['kidneys', 'bladder'], [URINE], ['ureters', 'bladder'], ['kidneys', 'ureters', 'bladder'], V, 'front'),
    Q('परीक्षा का पक्का सवाल', 'वृक्क की कार्यात्मक इकाई क्या है?', 'A) न्यूरॉन', 'B) नेफ्रॉन', ['kidneys'], ['pulse:kidneys'], V, angle='back')])
T['मूत्र तंत्र: किडनी से मूत्राशय तक'] = ('urinary', ['किडनी', 'नली', 'मूत्राशय', 'याद'], [
    S('hook', 3.5, 'मूत्र बनता कहाँ है?', 'मूत्र तंत्र का पूरा रास्ता', ['kidneys', 'bladder'], [URINE], ['kidneys', 'bladder'], ['kidneys', 'ureters', 'bladder'], V, 'front'),
    S('kidney', 5.5, 'दो वृक्क खून छानते हैं', 'यूरिया, नमक और ज़्यादा पानी अलग करते हैं', ['kidneys'], ['pulse:kidneys', 'particles:arteries,kidneys,blood'], ['kidneys'], ['kidneys'], V, 'back', 'push', 1.2),
    S('ureter', 5.5, 'मूत्रवाहिनी: नीचे की नलियाँ', 'मूत्र को मूत्राशय तक ले जाती हैं', ['ureters'], ['travel:kidneys,ureters,bladder', 'flow:ureters'], ['ureters'], ['kidneys', 'ureters', 'bladder'], V, 'front', 'down'),
    S('bladder', 5.5, 'मूत्राशय: थैली', 'भरने पर मूत्रमार्ग से बाहर निकलता है', ['bladder'], ['travel:ureters,bladder', 'pulse:bladder'], ['bladder'], ['bladder', 'ureters'], V, 'front', 'push', 1.4),
    Q('परीक्षा का पक्का सवाल', 'मूत्र में मुख्य अपशिष्ट क्या होता है?', 'A) यूरिया', 'B) ग्लूकोज़', ['kidneys', 'bladder'], [URINE], V, angle='front')])
T['थायरॉइड ग्रंथि और आयोडीन'] = ('thyroid', ['गला', 'थायरॉक्सिन', 'आयोडीन', 'याद'], [
    S('hook', 3.5, 'गले की तितली जैसी ग्रंथि', 'नमक में आयोडीन क्यों मिलाते हैं?', ['thyroid'], ['pulse:thyroid', 'flow:thyroid'], ['thyroid'], ['thyroid', 'larynx', 'trachea'], V, 'front', zoom=1.5),
    S('where', 5.5, 'गले में, श्वासनली के आगे', 'स्वरयंत्र के ठीक नीचे', ['thyroid', 'trachea'], ['sequence:larynx,thyroid,trachea'], ['thyroid', 'trachea'], ['thyroid', 'larynx', 'trachea'], V, 'side', 'orbit', 1.4),
    S('hormone', 5.5, 'थायरॉक्सिन हार्मोन', 'शरीर की चयापचय (मेटाबॉलिज़्म) दर तय करता है', ['thyroid'], ['particles:thyroid,arteries,nutrient', 'pulse:thyroid'], ['thyroid'], ['thyroid'], V, 'front', 'push', 1.6),
    S('iodine', 5.5, 'बनाने के लिए आयोडीन ज़रूरी', 'कमी से गला फूलता है = घेंघा', ['thyroid'], ['pulse:thyroid'], ['thyroid'], ['thyroid'], V, 'three_quarter', 'orbit', 1.7),
    Q('परीक्षा का पक्का सवाल', 'आयोडीन की कमी से कौन-सा रोग होता है?', 'A) घेंघा', 'B) रिकेट्स', ['thyroid'], ['pulse:thyroid'], V, angle='front')])
T['अधिवृक्क ग्रंथि: आपातकाल का हार्मोन एड्रेनालिन'] = ('adrenal', ['जगह', 'एड्रेनालिन', 'दिल', 'याद'], [
    S('hook', 3.5, 'डर लगते ही दिल तेज़ क्यों?', 'ज़िम्मेदार है एक छोटी ग्रंथि', ['adrenal', 'kidneys'], ['pulse:adrenal', 'particles:adrenal,heart,blood'], ['adrenal'], ['adrenal', 'kidneys'], V, 'back', zoom=1.4),
    S('where', 5.5, 'हर किडनी के ऊपर एक टोपी', 'इसीलिए नाम अधिवृक्क', ['adrenal', 'kidneys'], ['sequence:kidneys,adrenal'], ['adrenal', 'kidneys'], ['adrenal', 'kidneys'], V, 'back', 'orbit', 1.3),
    S('rush', 6, 'एड्रेनालिन खून में', 'दिल तेज़ धड़कता है, साँस तेज़ होती है', ['heart', 'lungs'], ['beat', 'breathe', 'particles:adrenal,heart,blood'], ['heart', 'lungs'], ['heart', 'lungs', 'adrenal'], CV, 'front', 'push'),
    S('fight', 5, 'लड़ो या भागो हार्मोन', 'आपात स्थिति में शरीर को तैयार करता है', ['adrenal'], ['pulse:adrenal', 'flow:adrenal'], ['adrenal'], ['adrenal', 'kidneys'], V, 'back', 'push', 1.5),
    Q('परीक्षा का पक्का सवाल', 'आपातकालीन हार्मोन किसे कहते हैं?', 'A) एड्रेनालिन', 'B) इंसुलिन', ['adrenal'], ['pulse:adrenal'], V, angle='back')])
T['मानव शरीर की प्रमुख अंतःस्रावी ग्रंथियाँ'] = ('endocrine', ['मस्तिष्क', 'गला', 'पेट', 'याद'], [
    S('hook', 3.5, 'बिना नली वाली ग्रंथियाँ', 'हार्मोन सीधे खून में छोड़ती हैं', ['thyroid', 'pancreas'], ['sequence:brain,thyroid,adrenal,pancreas'], ['thyroid', 'pancreas'], ['thyroid', 'pancreas', 'adrenal'], V, 'front', zoom=0.9),
    S('pituitary', 5.5, 'पीयूष ग्रंथि: मास्टर ग्रंथि', 'मस्तिष्क के नीचे, बाकी ग्रंथियों को चलाती है', ['brain'], ['pulse:brain', 'flow:brain'], ['brain'], ['brain'], N_, 'side', 'push', 1.2),
    S('thyroid', 5, 'थायरॉइड: गले में', 'थायरॉक्सिन, आयोडीन ज़रूरी', ['thyroid'], ['pulse:thyroid', 'particles:thyroid,arteries,nutrient'], ['thyroid'], ['thyroid', 'larynx'], V, 'front', 'push', 1.5),
    S('belly', 6, 'अधिवृक्क और अग्न्याशय', 'एड्रेनालिन और इंसुलिन', ['adrenal', 'pancreas'], ['sequence:adrenal,pancreas', 'particles:pancreas,veins,nutrient'], ['adrenal', 'pancreas'], ['adrenal', 'pancreas', 'kidneys'], V, 'three_quarter'),
    Q('परीक्षा का पक्का सवाल', 'मास्टर ग्रंथि किसे कहते हैं?', 'A) पीयूष ग्रंथि', 'B) थायरॉइड', ['brain'], ['pulse:brain'], N_, angle='side')])
T['मस्तिष्क के भाग और उनके काम'] = ('brain_parts', ['प्रमस्तिष्क', 'अनुमस्तिष्क', 'मेडुला', 'याद'], [
    S('hook', 3.5, 'सोचता कौन, संतुलन कौन रखता है?', 'दिमाग के तीन हिस्से', ['brain'], ['pulse:brain', SIGNAL], ['brain'], ['brain', 'cerebellum'], N_, 'side', zoom=1.1),
    S('cerebrum', 5.5, 'प्रमस्तिष्क: सबसे बड़ा भाग', 'सोचना, याद रखना, बोलना, समझना', ['brain'], ['pulse:brain', 'flow:brain'], ['brain'], ['brain'], N_, 'three_quarter', 'orbit', 1.2),
    S('cerebellum', 5.5, 'अनुमस्तिष्क: संतुलन', 'चलते समय शरीर को गिरने नहीं देता', ['cerebellum'], ['pulse:cerebellum', 'sequence:brain,cerebellum'], ['cerebellum'], ['cerebellum', 'brain'], N_, 'back', 'push', 1.3),
    S('medulla', 5.5, 'मेडुला: अपने आप होने वाले काम', 'दिल की धड़कन, साँस — बिना सोचे', ['brain', 'spinal_cord'], ['travel:brain,spinal_cord', 'flow:spinal_cord'], ['spinal_cord'], ['brain', 'spinal_cord', 'cerebellum'], N_, 'side', 'down'),
    Q('परीक्षा का पक्का सवाल', 'शरीर का संतुलन कौन बनाए रखता है?', 'A) अनुमस्तिष्क', 'B) प्रमस्तिष्क', ['cerebellum', 'brain'], ['pulse:cerebellum'], N_, angle='side')])
T['अनुमस्तिष्क: शरीर का संतुलन'] = ('cerebellum', ['जगह', 'संतुलन', 'तालमेल', 'याद'], [
    S('hook', 3.5, 'आँख बंद करके भी सीधे खड़े कैसे?', 'काम है "छोटे दिमाग" का', ['cerebellum'], ['pulse:cerebellum'], ['cerebellum'], ['cerebellum', 'brain'], N_, 'back', zoom=1.3),
    S('where', 5.5, 'सिर के पीछे, नीचे की ओर', 'प्रमस्तिष्क के नीचे छोटा भाग', ['cerebellum', 'brain'], ['sequence:brain,cerebellum'], ['cerebellum', 'brain'], ['cerebellum', 'brain'], N_, 'side', 'orbit', 1.1),
    S('balance', 6, 'शरीर का संतुलन', 'चलना, दौड़ना, साइकिल चलाना', ['cerebellum'], ['pulse:cerebellum', SIGNAL], ['cerebellum'], ['cerebellum', 'spinal_cord'], N_, 'back', 'push', 1.3),
    S('coord', 5, 'पेशियों का तालमेल', 'लिखना, खेलना — सटीक गति', ['skin'], [SIGNAL, 'flow:nerves'], ['cerebellum'], ['cerebellum', 'brain', 'spinal_cord', 'nerves'], N_, 'front', 'pull', 1.0),
    Q('परीक्षा का पक्का सवाल', 'शराब पीने से चाल लड़खड़ाती है, किस भाग पर असर?', 'A) अनुमस्तिष्क', 'B) मेडुला', ['cerebellum'], ['pulse:cerebellum'], N_, angle='back')])
T['मेरुरज्जु और प्रतिवर्ती क्रिया'] = ('reflex', ['मेरुरज्जु', 'प्रतिवर्ती', 'तेज़', 'याद'], [
    S('hook', 3.5, 'छूते ही हाथ क्यों हटता है?', 'दिमाग से पहले कौन फैसला करता है?', ['spinal_cord'], ['travel:nerves,spinal_cord,nerves'], ['spinal_cord'], ['spinal_cord', 'nerves'], N_, 'back', zoom=0.9),
    S('cord', 5.5, 'मेरुरज्जु: रीढ़ के अंदर', 'दिमाग से नीचे आती तंत्रिकाओं की रस्सी', ['spinal_cord'], ['travel:brain,spinal_cord', 'flow:spinal_cord'], ['spinal_cord', 'brain'], ['spinal_cord', 'brain'], N_, 'back', 'down'),
    S('reflex', 6, 'प्रतिवर्ती क्रिया', 'मेरुरज्जु तुरंत जवाब भेजता है, बिना सोचे', ['skin'], ['travel:nerves,spinal_cord,nerves', 'flow:nerves'], ['spinal_cord'], ['spinal_cord', 'nerves'], N_, 'three_quarter', 'push', 1.0),
    S('guard', 5, 'रीढ़ की हड्डी इसकी ढाल', 'कशेरुक मेरुरज्जु को बचाते हैं', ['spine'], ['sequence:spine'], ['spine'], ['spine'], B, 'back', 'rise', 0.9),
    Q('परीक्षा का पक्का सवाल', 'प्रतिवर्ती क्रिया कौन नियंत्रित करता है?', 'A) मेरुरज्जु', 'B) प्रमस्तिष्क', ['spinal_cord'], ['flow:spinal_cord'], N_, angle='back')])
T['तंत्रिका तंत्र: संदेश कैसे जाता है'] = ('nervous_signal', ['आँख-कान', 'तंत्रिका', 'दिमाग', 'याद'], [
    S('hook', 3.5, 'शरीर का इंटरनेट!', 'संदेश पलक झपकते पहुँचता है', ['skin'], [SIGNAL, 'flow:nerves'], ['brain'], ['brain', 'spinal_cord', 'nerves'], N_, 'front', zoom=1.0),
    S('net', 5.5, 'पूरे शरीर में तंत्रिकाएँ', 'हर अंग दिमाग से जुड़ा है', ['skin'], ['flow:nerves', 'travel:spinal_cord,nerves'], ['nerves', 'spinal_cord'], ['brain', 'spinal_cord', 'nerves'], N_, 'three_quarter', 'orbit', 1.0),
    S('up', 5.5, 'संवेदी तंत्रिका: अंग → दिमाग', 'छूना, देखना, सुनना ऊपर पहुँचता है', ['brain', 'spinal_cord'], ['travel:nerves,spinal_cord,brain'], ['brain'], ['brain', 'spinal_cord', 'nerves'], N_, 'side', 'rise'),
    S('down', 5.5, 'प्रेरक तंत्रिका: दिमाग → पेशी', 'हुक्म नीचे आता है, हाथ-पैर चलते हैं', ['skin'], [SIGNAL, 'flow:nerves'], ['spinal_cord'], ['brain', 'spinal_cord', 'nerves'], N_, 'front', 'down', 1.0),
    Q('परीक्षा का पक्का सवाल', 'तंत्रिका तंत्र की इकाई क्या है?', 'A) न्यूरॉन', 'B) नेफ्रॉन', ['brain'], [SIGNAL], N_, angle='side')])
T['मानव आँख की बनावट'] = ('eye', ['आँख', 'लेंस', 'रेटिना', 'याद'], [
    S('hook', 3.5, 'आँख में तस्वीर उलटी बनती है!', 'फिर भी सब सीधा दिखता है', ['eyes'], ['pulse:eyes', 'travel:eyes,brain'], ['eyes'], ['eyes', 'brain'], N_, 'front', zoom=1.5),
    S('front', 5.5, 'कॉर्निया और लेंस', 'रोशनी को मोड़कर पीछे फोकस करते हैं', ['eyes'], ['pulse:eyes', 'flow:eyes'], ['eyes'], ['eyes'], N_, 'side', 'push', 1.6),
    S('retina', 5.5, 'रेटिना पर उलटा, वास्तविक चित्र', 'शलाका और शंकु रोशनी पहचानते हैं', ['eyes'], ['flow:eyes', 'pulse:eyes'], ['eyes'], ['eyes'], N_, 'three_quarter', 'orbit', 1.7),
    S('brain', 5.5, 'दृक् तंत्रिका → दिमाग', 'दिमाग चित्र को सीधा करके समझता है', ['eyes', 'brain'], ['travel:eyes,brain', 'flow:brain'], ['brain', 'eyes'], ['eyes', 'brain'], N_, 'side', 'pull', 1.0),
    Q('परीक्षा का पक्का सवाल', 'आँख में चित्र कहाँ बनता है?', 'A) रेटिना', 'B) कॉर्निया', ['eyes'], ['pulse:eyes'], N_, angle='front')])
T['मानव कंकाल: वयस्क में 206 हड्डियाँ'] = ('skeleton_206', ['खोपड़ी', 'धड़', 'हाथ-पैर', 'याद'], [
    S('hook', 3.5, 'बच्चे में ज़्यादा हड्डियाँ!', 'फिर बड़े होकर 206 कैसे?', ['skin'], ['sequence:skull,spine,ribs,pelvis,femur'], ['skull'], ['skull', 'spine', 'ribs', 'pelvis', 'femur', 'arm_bones', 'leg_bones', 'hand_bones', 'bones'], B, 'front', zoom=1.0),
    S('count', 5.5, 'जन्म पर लगभग 300 हड्डियाँ', 'कई हड्डियाँ आपस में जुड़कर 206 बनती हैं', ['skull', 'spine'], ['sequence:skull,spine,pelvis'], ['skull', 'spine', 'pelvis'], ['skull', 'spine', 'pelvis', 'ribs'], B, 'three_quarter', 'orbit', 0.9),
    S('axial', 5.5, 'खोपड़ी, रीढ़, पसलियाँ', 'मस्तिष्क, दिल और फेफड़ों की रक्षा', ['skull', 'ribs'], ['sequence:skull,spine,ribs'], ['skull', 'ribs'], ['skull', 'spine', 'ribs'], B, 'front', 'down', 0.9),
    S('limbs', 5.5, 'हाथ-पैर से चलना-फिरना', 'हड्डियाँ, जोड़ और पेशियाँ मिलकर काम करती हैं', ['skin'], ['sequence:arm_bones,hand_bones,femur,leg_bones'], ['femur', 'arm_bones'], ['arm_bones', 'hand_bones', 'femur', 'leg_bones', 'pelvis', 'spine', 'ribs', 'skull', 'bones'], B, 'three_quarter_left', 'pull', 1.0),
    Q('परीक्षा का पक्का सवाल', 'वयस्क मनुष्य में कितनी हड्डियाँ होती हैं?', 'A) 206', 'B) 300', ['skin'], ['sequence:skull,spine,femur'], B, solid=['skull', 'spine', 'ribs', 'pelvis', 'femur', 'arm_bones', 'leg_bones', 'hand_bones', 'bones'], angle='front')])
T['सबसे लंबी हड्डी: फीमर'] = ('femur', ['जाँघ', 'लंबी', 'मज़बूत', 'याद'], [
    S('hook', 3.5, 'शरीर की सबसे लंबी हड्डी?', 'और सबसे मज़बूत भी', ['femur'], ['sequence:pelvis,femur', 'pulse:femur'], ['femur'], ['femur', 'pelvis'], B, 'front', zoom=1.0),
    S('thigh', 5.5, 'फीमर: जाँघ की हड्डी', 'कूल्हे से घुटने तक', ['femur', 'pelvis'], ['sequence:pelvis,femur,leg_bones'], ['femur', 'pelvis'], ['femur', 'pelvis', 'leg_bones'], B, 'three_quarter', 'down'),
    S('strong', 5.5, 'पूरे शरीर का वज़न उठाती है', 'खड़े होने, चलने, दौड़ने में', ['femur'], ['pulse:femur', 'sequence:femur'], ['femur'], ['femur'], B, 'side', 'orbit', 1.1),
    S('joints', 5.5, 'ऊपर कूल्हा, नीचे घुटना', 'बॉल-सॉकेट जोड़ कूल्हे पर', ['pelvis', 'femur'], ['sequence:pelvis,femur'], ['pelvis', 'femur'], ['pelvis', 'femur'], B, 'front', 'push', 1.2),
    Q('परीक्षा का पक्का सवाल', 'मानव शरीर की सबसे लंबी हड्डी कौन-सी है?', 'A) फीमर', 'B) टिबिया', ['femur'], ['pulse:femur'], B, angle='front')])
T['सबसे छोटी हड्डी: स्टेपीज़ (कान में)'] = ('stapes', ['कान', 'तीन हड्डियाँ', 'स्टेपीज़', 'याद'], [
    S('hook', 3.5, 'चावल के दाने से भी छोटी हड्डी!', 'आपके कान के अंदर', ['ear_bones'], ['pulse:ear_bones'], ['ear_bones'], ['ear_bones', 'skull'], B, 'side', zoom=1.0),
    S('where', 5.5, 'मध्य कर्ण में', 'खोपड़ी की टेम्पोरल हड्डी के अंदर', ['ear_bones', 'skull'], ['sequence:skull,ear_bones'], ['ear_bones', 'skull'], ['ear_bones', 'skull'], B, 'side', 'push', 0.9),
    S('three', 5.5, 'मैलियस, इंकस, स्टेपीज़', 'हथौड़ा, निहाई और रकाब', ['ear_bones'], ['pulse:ear_bones', 'sequence:ear_bones'], ['ear_bones'], ['ear_bones'], B, 'side', 'orbit', 1.0),
    S('sound', 5.5, 'ध्वनि की कंपन आगे बढ़ाती हैं', 'कान के पर्दे से भीतरी कान तक', ['ear_bones'], ['pulse:ear_bones', 'travel:ear_bones,brain'], ['ear_bones'], ['ear_bones', 'brain'], ('skin', 'skeletal', 'nervous'), 'side', 'pull', 0.9),
    Q('परीक्षा का पक्का सवाल', 'मानव शरीर की सबसे छोटी हड्डी कौन-सी है?', 'A) स्टेपीज़', 'B) मैलियस', ['ear_bones'], ['pulse:ear_bones'], B, angle='side')])
T['खोपड़ी: मस्तिष्क का कवच'] = ('skull', ['कवच', 'हड्डियाँ', 'जबड़ा', 'याद'], [
    S('hook', 3.5, 'सिर की एक ही हड्डी हिलती है!', 'कौन-सी? अंत तक देखो', ['skull'], ['sequence:skull,teeth'], ['skull'], ['skull', 'teeth'], B, 'three_quarter', zoom=1.0),
    S('armor', 5.5, 'मस्तिष्क का कवच', 'कपाल की हड्डियाँ दिमाग को चारों ओर से ढकती हैं', ['skull'], ['sequence:skull', 'pulse:brain'], ['skull'], ['skull'], B, 'side', 'orbit', 1.0),
    S('bones', 5.5, 'खोपड़ी में 22 हड्डियाँ', 'ज़्यादातर आपस में मज़बूती से जुड़ी', ['skull'], ['sequence:skull,teeth'], ['skull', 'teeth'], ['skull', 'teeth'], B, 'front', 'push', 1.0),
    S('jaw', 5.5, 'निचला जबड़ा: अकेली हिलने वाली', 'बोलने और चबाने के लिए', ['skull', 'teeth'], ['sequence:teeth', 'pulse:teeth'], ['teeth'], ['skull', 'teeth'], B, 'side', 'push', 1.1),
    Q('परीक्षा का पक्का सवाल', 'खोपड़ी की कौन-सी हड्डी हिल सकती है?', 'A) निचला जबड़ा', 'B) ललाट हड्डी', ['skull'], ['sequence:skull,teeth'], B, solid=['skull', 'teeth'], angle='side')])
T['रीढ़ की हड्डी की बनावट'] = ('spine', ['कशेरुक', 'भाग', 'रक्षा', 'याद'], [
    S('hook', 3.5, 'रीढ़ एक हड्डी नहीं!', 'ये कई छोटी हड्डियों की माला है', ['spine'], ['sequence:spine', 'travel:brain,spinal_cord'], ['spine'], ['spine'], B, 'back', zoom=0.9),
    S('beads', 5.5, '33 कशेरुक', 'वयस्क में कुछ जुड़कर 26 रह जाते हैं', ['spine'], ['sequence:spine'], ['spine'], ['spine'], B, 'side', 'down', 0.9),
    S('parts', 5.5, 'गर्दन, छाती, कमर के भाग', 'नीचे त्रिकास्थि और अनुत्रिक', ['spine', 'pelvis'], ['sequence:spine,pelvis'], ['spine', 'pelvis'], ['spine', 'pelvis'], B, 'back', 'down', 0.9),
    S('guard', 5.5, 'अंदर मेरुरज्जु सुरक्षित', 'रीढ़ शरीर को सीधा खड़ा रखती है', ['spine', 'spinal_cord'], ['travel:brain,spinal_cord', 'flow:spinal_cord'], ['spinal_cord'], ['spine', 'spinal_cord'], ('skin', 'skeletal', 'nervous'), 'side', 'rise', 0.9),
    Q('परीक्षा का पक्का सवाल', 'रीढ़ की हड्डी के अंदर क्या होता है?', 'A) मेरुरज्जु', 'B) फीमर', ['spine'], ['sequence:spine'], B, angle='back')])
T['पसलियाँ: दिल और फेफड़ों की रक्षा'] = ('ribs', ['पसलियाँ', 'जोड़ी', 'रक्षा', 'याद'], [
    S('hook', 3.5, 'छाती का पिंजरा', 'दिल और फेफड़े इसी में बंद हैं', ['ribs'], ['breathe', 'beat', 'sequence:ribs'], ['ribs'], ['ribs', 'heart', 'lungs'], ('skin', 'skeletal', 'visceral', 'cardio'), 'front', zoom=1.0),
    S('pairs', 5.5, '12 जोड़ी पसलियाँ', 'पीछे रीढ़ से, आगे उरोस्थि से जुड़ी', ['ribs'], ['sequence:spine,ribs'], ['ribs', 'spine'], ['ribs', 'spine'], B, 'three_quarter', 'orbit', 1.0),
    S('types', 5.5, '7 सच्ची, 3 झूठी, 2 तैरती', 'तैरती पसलियाँ आगे से नहीं जुड़तीं', ['ribs'], ['sequence:ribs'], ['ribs'], ['ribs'], B, 'front', 'push', 1.1),
    S('protect', 5.5, 'साँस में ऊपर-नीचे', 'फेफड़ों को फैलने की जगह देती हैं', ['ribs', 'lungs'], ['breathe', 'beat'], ['lungs', 'heart'], ['ribs', 'lungs', 'heart'], ('skin', 'skeletal', 'visceral', 'cardio'), 'three_quarter_left'),
    Q('परीक्षा का पक्का सवाल', 'मनुष्य में कितनी जोड़ी पसलियाँ होती हैं?', 'A) 12 जोड़ी', 'B) 10 जोड़ी', ['ribs'], ['breathe', 'sequence:ribs'], B, angle='front')])
T['दाँतों के प्रकार और काम'] = ('teeth', ['काटना', 'फाड़ना', 'पीसना', 'याद'], [
    S('hook', 3.5, 'शरीर का सबसे कठोर पदार्थ?', 'आपके दाँतों के ऊपर है', ['teeth'], ['pulse:teeth', 'sequence:teeth'], ['teeth'], ['teeth', 'skull'], B, 'front', zoom=1.5),
    S('cut', 5.5, 'कृंतक: काटने वाले', 'सामने के 8 दाँत', ['teeth'], ['sequence:teeth', 'pulse:teeth'], ['teeth'], ['teeth'], B, 'front', 'push', 1.7),
    S('tear', 5.5, 'रदनक फाड़ते, दाढ़ पीसती हैं', 'हर दाँत का अलग काम', ['teeth', 'tongue'], ['sequence:teeth,tongue', 'pulse:tongue'], ['teeth', 'tongue'], ['teeth', 'tongue'], ('skin', 'skeletal', 'visceral'), 'side', 'orbit', 1.6),
    S('count', 5.5, 'दूध के 20, स्थायी 32 दाँत', 'इनेमल शरीर का सबसे कठोर पदार्थ', ['teeth'], ['pulse:teeth'], ['teeth'], ['teeth', 'skull'], B, 'three_quarter', 'pull', 1.4),
    Q('परीक्षा का पक्का सवाल', 'शरीर का सबसे कठोर पदार्थ कौन-सा है?', 'A) इनेमल', 'B) हड्डी', ['teeth'], ['pulse:teeth'], B, angle='front')])
T['हाथ और पैर की हड्डियाँ'] = ('limb_bones', ['बाँह', 'हाथ', 'पैर', 'याद'], [
    S('hook', 3.5, 'एक हाथ में 27 हड्डियाँ!', 'इसीलिए उँगलियाँ इतनी लचीली हैं', ['hand_bones'], ['sequence:arm_bones,hand_bones', 'pulse:hand_bones'], ['hand_bones'], ['hand_bones', 'arm_bones'], B, 'front', zoom=1.0),
    S('arm', 5.5, 'बाँह: ह्यूमरस, रेडियस, अल्ना', 'कंधे से कलाई तक', ['arm_bones'], ['sequence:arm_bones,hand_bones'], ['arm_bones'], ['arm_bones', 'hand_bones'], B, 'three_quarter', 'down'),
    S('hand', 5.5, 'कलाई, हथेली, उँगलियाँ', 'उँगलियों की हड्डियाँ = फैलेंजेस', ['hand_bones'], ['sequence:hand_bones', 'pulse:hand_bones'], ['hand_bones'], ['hand_bones'], B, 'front', 'push', 1.2),
    S('leg', 5.5, 'पैर: फीमर, टिबिया, फिबुला', 'एक पैर के पंजे में 26 हड्डियाँ', ['femur', 'leg_bones'], ['sequence:pelvis,femur,leg_bones'], ['femur', 'leg_bones'], ['pelvis', 'femur', 'leg_bones'], B, 'three_quarter_left', 'down', 0.9),
    Q('परीक्षा का पक्का सवाल', 'घुटने की टोपी (पटेला) किस अंग में है?', 'A) पैर', 'B) हाथ', ['leg_bones'], ['sequence:femur,leg_bones'], B, solid=['femur', 'leg_bones'], angle='front')])
T['श्रोणि (पेल्विस) की हड्डी'] = ('pelvis', ['जगह', 'जोड़', 'रक्षा', 'याद'], [
    S('hook', 3.5, 'शरीर का कटोरा!', 'जो पेट के निचले अंगों को सँभालता है', ['pelvis'], ['sequence:spine,pelvis', 'pulse:pelvis'], ['pelvis'], ['pelvis', 'spine'], B, 'front', zoom=1.1),
    S('bowl', 5.5, 'श्रोणि मेखला', 'दो कूल्हे की हड्डियाँ, पीछे त्रिकास्थि', ['pelvis', 'spine'], ['sequence:pelvis,spine'], ['pelvis', 'spine'], ['pelvis', 'spine'], B, 'three_quarter', 'orbit'),
    S('joint', 5.5, 'फीमर यहीं जुड़ती है', 'कूल्हे का बॉल-सॉकेट जोड़', ['pelvis', 'femur'], ['sequence:pelvis,femur'], ['pelvis', 'femur'], ['pelvis', 'femur'], B, 'front', 'push', 1.15),
    S('protect', 5.5, 'मूत्राशय की रक्षा', 'और शरीर का वज़न पैरों तक पहुँचाती है', ['pelvis', 'bladder'], ['pulse:bladder', 'sequence:pelvis'], ['bladder', 'pelvis'], ['pelvis', 'bladder'], ('skin', 'skeletal', 'visceral'), 'front', 'orbit', 1.1),
    Q('परीक्षा का पक्का सवाल', 'कूल्हे का जोड़ किस प्रकार का है?', 'A) कंदुक-खल्लिका (बॉल-सॉकेट)', 'B) कब्ज़ा जोड़', ['pelvis', 'femur'], ['sequence:pelvis,femur'], B, angle='front')])
T['मानव शरीर के प्रमुख अंग तंत्र'] = ('organ_systems', ['पाचन', 'श्वसन', 'परिसंचरण', 'तंत्रिका'], [
    S('hook', 3.5, 'शरीर की 5 टीमें', 'हर टीम का अपना काम', ['skin'], ['sequence:stomach,lungs,heart,brain'], ['heart'], ['stomach', 'lungs', 'heart', 'small_intestine', 'large_intestine'], CV, 'front', zoom=1.0),
    S('digest', 5, 'पाचन तंत्र', 'भोजन को ऊर्जा में बदलता है', ['stomach', 'small_intestine'], [FOOD], ['stomach', 'small_intestine'], ['oesophagus', 'stomach', 'small_intestine', 'large_intestine'], V, 'front', 'push'),
    S('breathe', 5, 'श्वसन तंत्र', 'ऑक्सीजन अंदर, कार्बन डाइऑक्साइड बाहर', ['lungs'], ['breathe', AIR], ['lungs'], ['lungs', 'trachea', 'bronchi'], V, 'front', 'push'),
    S('blood', 5.5, 'परिसंचरण तंत्र', 'दिल खून को पूरे शरीर में भेजता है', ['skin'], ['beat', BLOOD_OUT, 'flow:arteries'], ['heart'], ['heart', 'aorta', 'arteries'], C, hide=['veins', 'vena_cava'], zoom=1.35),
    S('nerve', 5.5, 'तंत्रिका तंत्र', 'दिमाग पूरे शरीर को चलाता है', ['skin'], [SIGNAL, 'flow:nerves'], ['brain'], ['brain', 'spinal_cord', 'nerves'], N_, 'three_quarter', 'pull', 1.0),
    Q('परीक्षा का पक्का सवाल', 'खून को पूरे शरीर में कौन पंप करता है?', 'A) हृदय', 'B) फेफड़े', ['heart'], ['beat'], CV)])
T['मानव शरीर के सबसे बड़े अंग: त्वचा और यकृत'] = ('largest_organs', ['त्वचा', 'यकृत', 'फ़र्क', 'याद'], [
    S('hook', 3.5, 'शरीर का सबसे बड़ा अंग?', 'जवाब आपकी आँखों के सामने है', ['skin'], ['pulse:skin', 'sequence:skin,liver'], ['skin'], [], ('skin',), 'front', zoom=1.0),
    S('skin', 5.5, 'त्वचा: सबसे बड़ा अंग', 'पूरे शरीर को ढकती और बचाती है', ['skin'], ['sequence:skin'], ['skin'], [], ('skin',), 'three_quarter', 'orbit', 1.0),
    S('liver', 5.5, 'यकृत: सबसे बड़ा आंतरिक अंग', 'और सबसे बड़ी ग्रंथि भी', ['liver'], ['pulse:liver', 'travel:liver,gallbladder'], ['liver'], ['liver', 'gallbladder'], V, 'front', 'push', 1.2),
    S('duties', 5.5, 'दोनों के काम', 'त्वचा तापमान सँभालती है, यकृत पित्त बनाता है', ['liver', 'skin'], ['sequence:skin,liver', 'travel:liver,gallbladder,small_intestine'], ['liver'], ['liver', 'gallbladder', 'small_intestine'], V, 'three_quarter_left', 'pull', 1.0),
    Q('परीक्षा का पक्का सवाल', 'शरीर का सबसे बड़ा आंतरिक अंग कौन-सा है?', 'A) यकृत', 'B) फेफड़ा', ['liver'], ['pulse:liver'], V)])

if __name__ == '__main__':
    import planner
    index = {'पाचन तंत्र में भोजन का सफ़र': 'topics/digestion.json', 'दिल और खून का सफ़र (तैयार demo)': 'topics/heart_blood.json'}
    bad = 0
    for name, (slug, steps, scenes) in T.items():
        for j, s in enumerate(scenes): s['step'] = -1 if j == 0 else min(j - 1, len(steps) - 1)
        plan = {'topic': name, 'brand': 'मानव शरीर', 'fps': 24, 'steps': steps, 'scenes': scenes}
        err = planner.validate(plan)
        if err: bad += 1; print('X', name, err)
        (R / 'topics' / f'{slug}.json').write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
        index[name] = f'topics/{slug}.json'
    (R / 'topics' / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    print('topics', len(T), 'invalid', bad)
