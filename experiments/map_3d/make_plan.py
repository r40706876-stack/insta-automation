"""Deterministic plan for a 3D India-map PYQ reel. No AI decides what is on screen:
every object comes from the question, the verified facts table and real map geometry.
Templates:
  river_place : "X (dam/project/falls) is on which river?"  -> pin + all option rivers + answer path
  state_place : "X is in which state?"                       -> pin + option states light up + answer state rises
Usage: python make_plan.py <template> <question_id or text match> plan.json"""
import json, math, sys, re
from pathlib import Path

R = Path(__file__).parent
FACTS = json.loads((R / 'facts.json').read_text(encoding='utf-8'))
RIV = json.loads((R / 'rivers.json').read_text(encoding='utf-8'))['rivers']
STATES = json.loads((R / 'india_states.json').read_text(encoding='utf-8'))['states']
HI2RIV = {v['hindi']: k for k, v in RIV.items()}
HI2RIV.update({'ताप्ती': 'Tapi', 'तापी नदी': 'Tapi', 'सिन्धु': 'Indus', 'कावेरी नदी': 'Kaveri'})
HI2STATE = {s['hindi']: s['name'] for s in STATES}
OPT_COL = ['#ff7a45', '#4ade80', '#c084fc', '#38bdf8']          # A B C D (same colours in 3D and on the cards)
LET = 'ABCD'


def inside(p, ring):
    x, y = p; c = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1], ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c


def state_at(p):
    for s in STATES:
        if any(inside(p, r) for r in s['rings']): return s['name']


def states_along(path):
    """Indian states the river really crosses, in order, with the share of its length inside each."""
    seq, share = [], {}
    for a, b in zip(path, path[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); L = math.hypot(b[0] - a[0], b[1] - a[1]); s = state_at(m)
        if not s: continue
        share[s] = share.get(s, 0) + L
        if not seq or seq[-1] != s: seq.append(s)
    total = sum(share.values()) or 1
    keep = [s for s in dict.fromkeys(seq) if share[s] / total > .06]
    return keep


def at_fraction(path, f):
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]; goal = f * sum(seg)
    for (a, b), L in zip(zip(path, path[1:]), seg):
        if goal <= L: t = goal / L if L else 0; return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])]
        goal -= L
    return path[-1]


def bbox(points, pad=1.5):
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    span = max(max(xs) - min(xs), (max(ys) - min(ys)) * .9) + 2 * pad
    return [round(cx, 2), round(cy, 2)], round(max(span, 7), 2)


def exam_short(q):
    e_ = (q.get('exams') or [''])[0]; m = re.match(r'([A-Za-z][A-Za-z .-]*?)\s*[\d/-]*\s*\d{2}[-/]\d{2}[-/](\d{4})', e_)
    if m: return m.group(1).strip() + ' ' + m.group(2)
    return (e_.split('(')[0].strip() or ' '.join(q.get('years', [])))[:24]


def clean_opt(s): return re.sub(r'\s+नदी$', '', s.strip())


def find_question(match):
    bank = json.loads((R.parent.parent / 'science_pyq_bank.json').read_text(encoding='utf-8'))
    bank = bank if isinstance(bank, list) else bank.get('questions', bank)
    for q in bank:
        if q.get('id') == match or match in q['question']: return q
    raise SystemExit('question not found: ' + match)


def river_place(q):
    place = next((k for k in FACTS['places'] if k in q['question'] and 'river' in FACTS['places'][k]), None)
    assert place, 'no verified place for: ' + q['question']
    P = FACTS['places'][place]; opts = [clean_opt(q['options'][k]) for k in 'abcd' if k in q['options']]
    ans_i = 'abcd'.index(q['answer']); ans_key = HI2RIV.get(opts[ans_i])
    assert ans_key == P['river'], ('answer/facts mismatch', opts[ans_i], P['river'])
    keys = [HI2RIV.get(o) for o in opts]
    path = RIV[ans_key]['path']; crossed = states_along(path); f = FACTS['rivers'][ans_key]
    hi = RIV[ans_key]['hindi']; kind = P['kind']
    all_pts = [p for k in keys if k for p in RIV[k]['path'] if 66 < p[0] < 99 and 5 < p[1] < 37] + [P['at']]
    full_c, full_s = [82.4, 22.0], 30.0
    near_c, near_s = [P['at'][0], P['at'][1] - .6], 9.0
    path_c, path_s = bbox([p for p in path if 66 < p[0] < 99], 1.2)
    rivers = [{'key': k, 'color': OPT_COL[i], 'letter': LET[i], 'label': opts[i], 'anchor': at_fraction(RIV[k]['path'], .55 if k != 'Ganga' else .45)}
              for i, k in enumerate(keys) if k]
    state_hi = {s['name']: s['hindi'] for s in STATES}
    route = ', '.join(state_hi[s] for s in crossed)
    q_text = q['question'].replace('(चरण-1) ', '')
    plan = {
        'template': 'river_place', 'fps': 24, 'brand': 'भूगोल · नक्शे से याद करो', 'id': q.get('id'),
        'question': q_text, 'exam_short': exam_short(q), 'options': opts, 'answer': ans_i, 'exam': (q.get('exams') or [''])[0],
        'place': {'name': place, 'at': P['at'], 'kind': kind},
        'rivers': rivers, 'answer_river': ans_key,
        'credit': 'नक्शा: datameet (MIT) · नदियाँ: Natural Earth',
        'scenes': [
            {'id': 'hook', 'seconds': 3.6, 'title': q_text, 'sub': 'नक्शा देखकर बताओ', 'speak': q_text,
             'cam': {'center': full_c, 'span': full_s, 'tilt': 34, 'from_tilt': 58, 'from_span': 40},
             'actions': [{'type': 'build', 't': 0, 'dur': 1.1}, {'type': 'pin', 'at': P['at'], 't': .9}],
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 1.3, 'kind': 'pin'}]},
            {'id': 'options', 'seconds': 5.2, 'title': 'कौन-सी नदी इस ' + kind + ' से होकर बहती है?', 'sub': '',
             'speak': 'ऑप्शन देखिए — ' + ', '.join(f'{LET[i]}, {o}' for i, o in enumerate(opts)) + '। कमेंट में अपना जवाब लिखिए!',
             'cam': {'center': full_c, 'span': full_s, 'tilt': 30},
             'actions': [{'type': 'river', 'key': r['key'], 't': .2 + .55 * i, 'dur': 1.4} for i, r in enumerate(rivers)],
             'labels': [{'text': r['letter'] + '  ' + r['label'], 'at': r['anchor'], 'color': r['color'], 't': .7 + .55 * i, 'kind': 'river'} for i, r in enumerate(rivers)]
                       + [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'}],
             },
            {'id': 'reveal', 'seconds': 4.2, 'title': 'सही उत्तर: ' + LET[ans_i] + '  ' + opts[ans_i], 'sub': place + ' ' + kind + ' — ' + hi + ' नदी पर',
             'speak': 'सही उत्तर है — ' + opts[ans_i] + '। ' + place + ' ' + kind + ', ' + hi + ' नदी पर बना है।',
             'cam': {'center': near_c, 'span': near_s, 'tilt': 40},
             'actions': [{'type': 'river_focus', 'key': ans_key, 't': .15}, {'type': 'ripple', 'at': P['at'], 't': .5}],
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'},
                        {'text': hi, 'at': at_fraction(path, .35), 'color': '#ffd25c', 't': .4, 'kind': 'river'}]},
            {'id': 'path', 'seconds': 6.4, 'title': hi + ' नदी का सफ़र', 'sub': 'उद्गम: ' + f['source'],
             'sub2': 'बहाव: ' + route, 'sub3': 'मुहाना: ' + f['mouth'],
             'speak': hi + ' नदी ' + f['source'] + ' से निकलती है, ' + route + ' से होकर बहती है, और ' + f['mouth'] + ' में मिलती है।',
             'cam': {'center': path_c, 'span': path_s, 'tilt': 32},
             'actions': [{'type': 'travel', 'key': ans_key, 't': .3, 'dur': 5.4}]
                        + [{'type': 'state_on', 'name': s, 't': .3 + 5.4 * (k + .5) / max(1, len(crossed))} for k, s in enumerate(crossed)],
             'labels': [{'text': 'उद्गम', 'at': path[0], 'color': '#7ee2ff', 't': .3, 'kind': 'point'},
                        {'text': 'मुहाना', 'at': path[-1], 'color': '#7ee2ff', 't': 5.4, 'kind': 'point'}]},
            {'id': 'end', 'seconds': 3.8, 'title': 'याद रखो', 'sub': place + ' ' + kind + ' : ' + hi + ' नदी', 'speak': 'याद रखिए — ' + place + ', ' + hi + '। सही था तो कमेंट में लिखिए, और ऐसे ही नक्शे वाले सवालों के लिए फ़ॉलो कीजिए।',
             'cam': {'center': near_c, 'span': near_s * 1.6, 'tilt': 46, 'yaw': 14},
             'actions': [], 'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'}], 'end': True},
        ]}
    return plan


def centroid(name):
    st = next(x for x in STATES if x['name'] == name); big = max(st['rings'], key=len)
    pts = [p for p in big]; cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    if not inside((cx, cy), big):                       # concave state: nearest inside vertex mean
        cx, cy = min(pts, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    return [round(cx, 3), round(cy, 3)]


def first_sentence(text, limit=95):
    for part in re.split(r'(?<=।)\s*', text or ''):
        part = part.strip()
        if 12 < len(part) <= limit: return part
    return ''


def state_place(q):
    place = next((k for k in FACTS['places'] if k in q['question']), None)
    assert place, 'no verified place for: ' + q['question']
    P = FACTS['places'][place]; opts = [q['options'][k].strip() for k in 'abcd' if k in q['options']]
    ans_i = 'abcd'.index(q['answer']); ans_state = HI2STATE.get(opts[ans_i])
    assert ans_state == P['state'] == state_at(P['at']), ('answer/facts/map mismatch', opts[ans_i], P['state'])
    st_hi = {x['name']: x['hindi'] for x in STATES}
    opt_states = [HI2STATE.get(o) for o in opts]
    cap = FACTS['capitals'].get(ans_state); kind = P['kind']
    fact = first_sentence(q.get('explanation', ''))
    pts = [centroid(s_) for s_ in opt_states if s_] + [P['at']]
    full_c, full_s = [82.4, 22.0], 30.0
    near_c, near_s = bbox([p for p in next(x for x in STATES if x['name'] == ans_state)['rings'][0]] + ([cap[1]] if cap else []), 1.4)
    near_c = [near_c[0], near_c[1] - .4]
    q_text = q['question'].replace('........', '____').replace('–', '').strip()
    on = [{'type': 'state_on', 'name': s_, 'color': OPT_COL[i], 't': .2 + .55 * i, 'raise': 1.5, 'glow': .35} for i, s_ in enumerate(opt_states) if s_]
    off = [{'type': 'state_off', 'name': s_, 't': .1} for s_ in opt_states if s_ and s_ != ans_state]
    labels_opt = [{'text': LET[i] + '  ' + opts[i], 'at': centroid(s_), 'color': OPT_COL[i], 't': .45 + .55 * i, 'kind': 'state'} for i, s_ in enumerate(opt_states) if s_]
    plan = {
        'template': 'state_place', 'fps': 24, 'id': q.get('id'), 'question': q_text, 'exam_short': exam_short(q),
        'options': opts, 'answer': ans_i, 'option_colors': OPT_COL, 'place': {'name': place, 'at': P['at'], 'kind': kind},
        'credit': 'नक्शा: datameet (MIT) · राज्य सीमाएँ सरलीकृत',
        'scenes': [
            {'id': 'hook', 'seconds': 3.6, 'title': q_text, 'speak': q_text.replace('____', 'किस'),
             'cam': {'center': full_c, 'span': full_s, 'tilt': 34, 'from_tilt': 58, 'from_span': 40},
             'actions': [{'type': 'build', 't': 0, 'dur': 1.1}, {'type': 'pin', 'at': P['at'], 't': .9}],
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 1.3, 'kind': 'pin'}]},
            {'id': 'options', 'seconds': 5.2, 'title': place + ' किस राज्य में है?',
             'speak': 'ऑप्शन देखिए — ' + ', '.join(f'{LET[i]}, {o}' for i, o in enumerate(opts)) + '। कमेंट में अपना जवाब लिखिए!',
             'cam': {'center': full_c, 'span': full_s, 'tilt': 30}, 'actions': on,
             'labels': labels_opt + [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'}]},
            {'id': 'reveal', 'seconds': 4.2, 'title': 'सही उत्तर: ' + LET[ans_i] + '  ' + opts[ans_i], 'sub': place + ' — ' + st_hi[ans_state] + ' में',
             'speak': 'सही उत्तर है — ' + opts[ans_i] + '। ' + place + ', ' + st_hi[ans_state] + ' में है।',
             'cam': {'center': near_c, 'span': near_s, 'tilt': 38},
             'actions': off + [{'type': 'state_on', 'name': ans_state, 'color': '#ffc93c', 't': .3, 'raise': 1.65, 'glow': .5}, {'type': 'ripple', 'at': P['at'], 't': .5}],
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'},
                        {'text': st_hi[ans_state], 'at': centroid(ans_state), 'color': '#ffd25c', 't': .5, 'kind': 'state'}]},
            {'id': 'fact', 'seconds': 5.6, 'title': st_hi[ans_state] + ' — याद रखने का तरीका', 'sub': fact,
             'sub2': ('राजधानी: ' + cap[0]) if cap else '', 'sub3': kind + ': ' + place,
             'speak': (fact + ' ' if fact else '') + ((st_hi[ans_state] + ' की राजधानी ' + cap[0] + ' है।') if cap else ''),
             'cam': {'center': near_c, 'span': near_s * 1.1, 'tilt': 44, 'yaw': -12},
             'actions': ([{'type': 'pin', 'at': cap[1], 't': .9, 'color': '#3b82f6'}] if cap else []),
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'}]
                       + ([{'text': cap[0] + ' (राजधानी)', 'at': cap[1], 'color': '#7eb6ff', 't': 1.3, 'kind': 'pin'}] if cap else [])},
            {'id': 'end', 'seconds': 3.8, 'title': 'याद रखो', 'sub': place + ' : ' + st_hi[ans_state],
             'speak': 'याद रखिए — ' + place + ', ' + st_hi[ans_state] + '। सही था तो कमेंट में लिखिए, और ऐसे ही नक्शे वाले सवालों के लिए फ़ॉलो कीजिए।',
             'cam': {'center': [(P['at'][0] + 80) / 2, P['at'][1] - 1], 'span': 20, 'tilt': 40, 'yaw': 10}, 'actions': [],
             'labels': [{'text': place, 'at': P['at'], 'color': '#ff5a5a', 't': 0, 'kind': 'pin'}], 'end': True},
        ]}
    return plan


def year_of(s):
    m = re.search(r'(\d{4})', s); return int(m.group(1)) if m else None


def timeline(q):
    opts = [q['options'][k].strip() for k in 'abcd' if k in q['options']]
    years = [year_of(o) for o in opts]; assert all(years) and len(set(years)) == len(years), opts
    ans_i = 'abcd'.index(q['answer']); ans = years[ans_i]
    A = {int(k): v for k, v in FACTS['anchors'].items() if int(k) != ans}
    before = max((y for y in A if y < ans), default=None); after = min((y for y in A if y > ans), default=None)
    if before and ans - before > 40: before = None
    if after and after - ans > (15 if before else 40): after = None
    anchors = [y for y in (before, after) if y]
    assert anchors, 'no anchor year near ' + str(ans)
    order = sorted(range(len(years)), key=lambda i: years[i])
    # plate slots: options bottom->top in time order; later the answer moves between its anchors
    slots_opt = {i: r for r, i in enumerate(order)}
    chain = sorted(anchors + [ans])
    q_text = re.sub(r'[_.–-]{3,}', '____', q['question']).strip()
    def gap(a, b):
        n = abs(b - a); return f'{n} साल ' + ('बाद' if b > a else 'पहले')
    if before:
        d_ = ans - before
        trick = f'{before} में {A[before]}, ' + ('अगले ही साल' if d_ == 1 else f'उसके {d_} साल बाद') + f' {ans}'
        trick += (f', फिर {after} में {A[after]}।' if after else '।')
    else:
        trick = f'{ans}, यानी {A[after]} ({after}) से {after - ans} साल पहले।'
    plan = {
        'template': 'timeline', 'badge': 'MinuteMe 3D टाइमलाइन', 'fps': 24, 'id': q.get('id'), 'question': q_text, 'exam_short': exam_short(q),
        'options': opts, 'answer': ans_i, 'option_colors': OPT_COL, 'years': years, 'answer_year': ans,
        'anchors': [{'year': y, 'label': A[y]} for y in anchors], 'chain': chain,
        'slots_opt': slots_opt, 'credit': 'MinuteMe GS · PYQ ' + exam_short(q),
        'scenes': [
            {'id': 'hook', 'seconds': 3.6, 'title': q_text, 'speak': q_text.replace('____', 'किस वर्ष'),
             'cam': {'z': 2.5, 'span': 8.0, 'elev': 4, 'yaw': -28, 'from_yaw': -70, 'from_span': 13},
             'actions': [{'type': 'pole', 't': 0, 'dur': .9}] + [{'type': 'plate_in', 'i': i, 't': .5 + .18 * r} for r, i in enumerate(order)],
             'labels': []},
            {'id': 'options', 'seconds': 5.2, 'title': 'सही वर्ष कौन-सा?',
             'speak': 'ऑप्शन देखिए — ' + ', '.join(f'{LET[i]}, {o}' for i, o in enumerate(opts)) + '। कमेंट में अपना जवाब लिखिए!',
             'cam': {'z': 2.5, 'span': 7.4, 'elev': 6, 'yaw': 18},
             'actions': [], 'labels': [{'text': LET[i], 'plate': i, 'color': OPT_COL[i], 't': .2 + .3 * r, 'kind': 'letter'} for r, i in enumerate(order)],
             },
            {'id': 'reveal', 'seconds': 4.2, 'title': 'सही उत्तर: ' + LET[ans_i] + '  ' + opts[ans_i], 'sub': '',
             'speak': 'सही उत्तर है — ' + str(ans) + '।',
             'cam': {'z': 2.5, 'span': 6.4, 'elev': 2, 'yaw': -10},
             'actions': [{'type': 'focus', 'i': ans_i, 't': .15}], 'labels': []},
            {'id': 'trick', 'seconds': 6.0, 'title': 'याद रखने की ट्रिक', 'sub': trick,
             'speak': 'याद रखने की ट्रिक — ' + trick,
             'cam': {'z': 2.5, 'span': 7.2, 'elev': 8, 'yaw': 16},
             'actions': [{'type': 'chain', 't': .1}] + [{'type': 'anchor_in', 'year': y, 't': .5 + .5 * k} for k, y in enumerate(anchors)]
                        + [{'type': 'travel', 't': 1.8, 'dur': 2.6}],
             'labels': [{'text': A[y], 'year': y, 'color': '#d9e6f2', 't': .9 + .5 * k, 'kind': 'anchor'} for k, y in enumerate(anchors)]
                       + [{'text': 'यह सवाल', 'year': ans, 'color': '#ffd25c', 't': 1.2, 'kind': 'anchor'}]},
            {'id': 'end', 'seconds': 3.8, 'title': 'याद रखो', 'sub': opts[ans_i], 'speak': 'याद रखिए — ' + str(ans) + '। सही था तो कमेंट में लिखिए, और रोज़ ऐसे PYQ के लिए फ़ॉलो कीजिए।',
             'cam': {'z': 2.5, 'span': 8.4, 'elev': 10, 'yaw': -20}, 'actions': [], 'labels': [], 'end': True},
        ]}
    return plan


def main():
    tpl, match, out = sys.argv[1:4]
    q = find_question(match)
    plan = {'river_place': river_place, 'state_place': state_place, 'timeline': timeline}[tpl](q)
    Path(out).write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
    print('PLAN', tpl, plan['question'], '->', plan['options'][plan['answer']])


if __name__ == '__main__':
    main()
