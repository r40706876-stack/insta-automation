"""Gemini -> topic JSON for the human-body template (strictly validated, never executable code).
Usage: python planner.py "मानव शरीर की सबसे बड़ी ग्रंथि" topics/auto.json
Needs GEMINI_API_KEY. Retries with the validation errors fed back (max 3)."""
import json, os, sys, re, requests
from pathlib import Path

R = Path(__file__).parent
IDX = json.loads((R / 'organ_index.json').read_text(encoding='utf-8'))
LAYERS = {'skin', 'visceral', 'cardio', 'nervous', 'skeletal'}
ANGLES = {'front', 'three_quarter', 'three_quarter_left', 'side', 'side_left', 'back'}
MOVES = {'push', 'pull', 'orbit', 'rise', 'down', 'still'}
EXAMPLE = (R / 'topics' / 'heart_blood.json').read_text(encoding='utf-8')

def catalog():
    return '\n'.join(f"- {k} = {v['hi']} (layer: {v['src']})" for k, v in IDX.items())

PROMPT = """तुम MinuteMe GS (SSC, Railway, State परीक्षाएँ) के लिए 3D मानव-शरीर रील की योजना बनाते हो।
विषय: {topic}

सिर्फ़ एक JSON लौटाओ, ठीक इस उदाहरण वाले ढाँचे में (कोई markdown नहीं):
{example}

नियम:
1. 5 से 7 scenes। पहला id "hook" (3-4 sec, जिज्ञासा जगाने वाला सवाल), आख़िरी scene में "quiz" (q, a, b, cta) — एक विकल्प सही हो।
2. हर scene 3.5 से 7 sec, कुल 25-40 sec। title ≤ 30 अक्षर, sub ≤ 48 अक्षर, आसान बोलचाल की हिंदी।
3. तथ्य सिर्फ़ NCERT स्तर के पक्के तथ्य। कोई संख्या तभी जब पाठ्यपुस्तक में मानक हो। शक हो तो संख्या मत लिखो।
4. हर scene में कहानी एक कदम आगे बढ़े (कारण → असर)। एक जैसी बात दोहराना मना।
5. camera.focus में वही खास अंग लिखो जिसकी बात हो रही है (viscera_other/bones/nerves नहीं)। camera.focus, solid, labels, hide, flow: में सिर्फ़ नीचे की keys। labels अधिकतम 3, और वे keys जिनकी layer "layers" में हो।
6. camera.angle ∈ {angles}; camera.move ∈ {moves}; camera.zoom 0.7-1.6।
7. layers ∈ {layers}। effects ∈ "beat" (दिल धड़कना), "breathe" (फेफड़े), "flow:<key>" (उस अंग में बहाव की चमक: खून/नस/भोजन/हवा), "sequence:<key1>,<key2>,..." (अंग क्रम से चमकें, जैसे भोजन का रास्ता)। सबसे ज़रूरी: "travel:<key1>,<key2>,..." = चमकता गोला उन अंगों से होकर चलता है (भोजन/हवा/खून/संदेश का सफ़र) — जहाँ भी कुछ एक जगह से दूसरी जगह जाता है, यही लगाओ; "pulse:<key>" = अंग सिकुड़ता-फैलता है (आमाशय का मंथन, आँत की गति); "particles:<from>,<to>" = छोटे कण एक अंग से दूसरे तक जाते हैं (पोषक तत्व आँत से यकृत, पानी आँत से शिरा, ऑक्सीजन फेफड़े से हृदय)। हर scene में कम से कम एक चलता हुआ effect हो — ठहरी हुई तस्वीर मना है।
8. steps: 3-4 छोटे शब्द (≤ 10 अक्षर), हर scene का "step" उसका index (hook = -1)।
9. किताब या नोट्स का नाम कभी मत लिखो।

उपलब्ध अंग keys:
{catalog}
"""

def validate(p):
    E = []
    sc = p.get('scenes', [])
    if not 5 <= len(sc) <= 7: E.append('need 5-7 scenes')
    tot = sum(s.get('seconds', 0) for s in sc)
    if not 25 <= tot <= 40: E.append(f'total seconds {tot} not in 25-40')
    if sc and sc[0].get('id') != 'hook': E.append('first scene id must be hook')
    if sc and 'quiz' not in sc[-1]: E.append('last scene needs quiz')
    steps = p.get('steps', [])
    if not 3 <= len(steps) <= 4 or any(len(x) > 12 for x in steps): E.append('steps: 3-4 items, each <= 10 chars')
    for i, s in enumerate(sc):
        tag = f'scene {i}'
        if not 3.5 <= s.get('seconds', 0) <= 7: E.append(f'{tag}: seconds 3.5-7')
        if len(s.get('title', '')) > 32: E.append(f'{tag}: title too long')
        if len(s.get('sub', '')) > 50: E.append(f'{tag}: sub too long')
        lay = set(s.get('layers', []))
        if not lay or not lay <= LAYERS: E.append(f'{tag}: bad layers')
        cam = s.get('camera', {})
        if cam.get('angle', 'front') not in ANGLES: E.append(f'{tag}: bad angle')
        if cam.get('move', 'push') not in MOVES: E.append(f'{tag}: bad move')
        if not .7 <= cam.get('zoom', 1) <= 1.6: E.append(f'{tag}: zoom 0.7-1.6')
        if any(k in ('viscera_other', 'bones', 'nerves', 'skin') for k in cam.get('focus', [])) and i > 0:
            E.append(f'{tag}: camera.focus must name the specific organ, not a catch-all group')
        for k in cam.get('focus', []) + s.get('solid', []) + s.get('hide', []):
            if k not in IDX: E.append(f'{tag}: unknown key {k}')
        labs = s.get('labels', [])
        if len(labs) > 3: E.append(f'{tag}: max 3 labels')
        for l in labs:
            k = l if isinstance(l, str) else l.get('key')
            if k not in IDX: E.append(f'{tag}: unknown label {k}')
            elif IDX[k]['src'] not in lay: E.append(f'{tag}: label {k} layer not shown')
        for e in s.get('effects', []):
            if e in ('beat', 'breathe'): continue
            if e.startswith('flow:') and e[5:] in IDX: continue
            if e.startswith('sequence:') and all(k in IDX for k in e[9:].split(',')): continue
            if e.startswith('travel:') and all(k in IDX for k in e[7:].split(',')): continue
            if e.startswith('pulse:') and e[6:] in IDX: continue
            if e.startswith('particles:') and all(k in IDX for k in e[10:].split(',')[:2]): continue
            E.append(f'{tag}: bad effect {e}')
        moving = [e for e in s.get('effects', []) if e.split(':')[0] in ('travel', 'pulse', 'particles', 'flow', 'beat', 'breathe', 'sequence')]
        if not moving: E.append(f'{tag}: needs at least one moving effect (travel/pulse/particles/flow/beat/breathe)')
        if 'quiz' in s:
            q = s['quiz']
            if not all(q.get(x) for x in ('q', 'a', 'b', 'cta')): E.append(f'{tag}: quiz needs q,a,b,cta')
    return E

def ask(prompt):
    import time
    last = ''
    for model in ('gemini-2.5-flash', 'gemini-2.5-flash-lite'):
        for wait in (0, 20, 60, 120):              # busy / rate-limit: wait and try again
            time.sleep(wait)
            try:
                r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                                  headers={'x-goog-api-key': os.environ['GEMINI_API_KEY']}, timeout=300,
                                  json={'contents': [{'parts': [{'text': prompt}]}],
                                        'generationConfig': {'temperature': .35, 'responseMimeType': 'application/json'}})
            except requests.RequestException as e:
                last = str(e); print('network', model, last[:120]); continue
            if r.ok:
                try:
                    txt = r.json()['candidates'][0]['content']['parts'][0]['text']
                    return json.loads(re.sub(r'^```(json)?|```$', '', txt.strip()))
                except (KeyError, IndexError, ValueError) as e:
                    last = 'bad answer: ' + str(e); print(last); continue
            last = f'{r.status_code} {r.text[:160]}'; print('model failed', model, last)
            if r.status_code not in (429, 500, 502, 503, 504): break
    raise RuntimeError('Gemini unavailable: ' + last)

if __name__ == '__main__':
    topic, out = sys.argv[1], Path(sys.argv[2])
    base = PROMPT.format(topic=topic, example=EXAMPLE, catalog=catalog(), angles=sorted(ANGLES), moves=sorted(MOVES), layers=sorted(LAYERS))
    prompt, errors = base, []
    for attempt in range(5):
        plan = ask(prompt); errors = validate(plan)
        if not errors:
            plan.setdefault('fps', 24); plan.setdefault('brand', 'मानव शरीर')
            out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8'); print('PLAN OK', out); break
        print('attempt', attempt, errors)
        prompt = base + '\nपिछले JSON में ये गलतियाँ थीं, इन्हें ठीक करके पूरा JSON दोबारा दो:\n' + '\n'.join(errors) + '\n\nपिछला JSON:\n' + json.dumps(plan, ensure_ascii=False)
    else:
        raise SystemExit('plan failed validation: ' + '; '.join(errors))
