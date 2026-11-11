"""30-day calendar for 3D template reels.
  python month_plan.py build  [start YYYY-MM-DD] [days]  -> calendar.json (map reel at 20:00, timeline reel at 22:00)
  python month_plan.py today  YYYY-MM-DD                  -> prints 'HHMM template question_id' lines for that date
Only questions that pass make_plan's checks (map geometry, verified facts) and are not time-sensitive are used;
already-posted ids (downloads/map3d/*/published.json) are skipped."""
import json, re, sys, datetime
from pathlib import Path
import make_plan as m

R = Path(__file__).parent
CAL = R / 'calendar.json'
SLOTS = {'2000': 'map', '2200': 'timeline'}
STALE = re.compile(r'20(1[0-9]|2\d)|सरकार|मुख्यमंत्री|पार्टी|नेता|राष्ट्रपति|हॉकी|चैंपियनशिप|(?<!परि)योजना|झांकी|जनगणना|हाल ही|वर्तमान|गेम्स|ट्रॉफी|अनुसार|प्रतिशत|%')


def posted_ids():
    ids = set()
    # questions already used by the old studio slots
    for sj in (R.parent / 'scheduled_visual_gs').glob('*/script.json'):
        try: ids.add(json.loads(sj.read_text(encoding='utf-8')).get('reference', {}).get('id'))
        except Exception: pass
    for p in (R.parent.parent / 'downloads' / 'map3d').glob('*/published.json'):
        plan = p.parent / 'plan.json'
        if plan.exists(): ids.add(json.loads(plan.read_text(encoding='utf-8')).get('id'))
    return ids


def candidates():
    bank = json.loads((R.parent.parent / 'science_pyq_bank.json').read_text(encoding='utf-8'))['questions']
    out = {'river_pin': [], 'state_pin': [], 'river': [], 'state': [], 'timeline': []}
    for q in bank:
        if q.get('subject') not in ('Geography', 'Traditional GK', 'History', 'Economics', 'Polity') or STALE.search(q['question']): continue
        if re.search(r'[\u00c0-\u024f]', m.fix_text(q['question'])): continue
        if re.search(r'[a-z]{6,}', q['question']) and not re.search(r'\([^)]*[a-z]{6,}[^)]*\)', q['question']): continue   # garbled text
        for t in ('river_place', 'state_place', 'timeline'):
            try: p = getattr(m, t)(q)
            except Exception: continue
            if t == 'timeline':
                opts = p['options']
                if any(len(re.findall(r'\d{4}', o)) > 1 or re.search(r'\d{4}\s*[-–]\s*\d{2}', o) for o in opts) or p['answer_year'] >= 2005 or str(p['answer_year']) in q['question']: break
            key = 'timeline' if t == 'timeline' else t.split('_')[0] + ('_pin' if p.get('place') else '')
            out[key].append({'id': q['id'], 'template': t, 'subject': q.get('subject'), 'q': q['question'][:90],
                             'answer': p['options'][p['answer']]})
            break
    return out


def build(start, days):
    c = candidates(); used = posted_ids()
    for k in c: c[k] = [x for x in c[k] if x['id'] not in used]
    # map slot rotation: pinned river/state questions first (most visual), then quoted-term state quizzes and river quizzes
    rot = ['river_pin', 'state_pin', 'state', 'state_pin', 'river', 'state']
    tl = sorted(c['timeline'], key=lambda x: ('Polity', 'History', 'Economics', 'Traditional GK').index(x['subject']) if x['subject'] in ('Polity', 'History', 'Economics', 'Traditional GK') else 9)
    # interleave timeline subjects
    by = {}
    for x in tl: by.setdefault(x['subject'], []).append(x)
    tl = [x for grp in zip(*[iter(v) for v in by.values()]) for x in grp] + [x for v in by.values() for x in v]
    seen, tl_u = set(), []
    for x in tl:
        if x['id'] not in seen: seen.add(x['id']); tl_u.append(x)
    cal = {}; d0 = datetime.date.fromisoformat(start); i = 0
    for n in range(days):
        day = (d0 + datetime.timedelta(days=n)).isoformat(); e = {}
        recent = [cal[d]['2000']['answer'] for d in list(cal)[-4:] if '2000' in cal[d]]
        recent_q = [cal[d]['2000']['q'][:25] for d in cal if '2000' in cal[d]]
        for _ in range(len(rot)):
            k = rot[i % len(rot)]; i += 1
            pick = next((x for x in c[k] if x['answer'] not in recent and x['q'][:25] not in recent_q), None)
            if pick: c[k].remove(pick); e['2000'] = pick; break
        recent_t = [cal[d]['2200']['answer'] for d in cal if '2200' in cal[d]]
        pick = next((x for x in tl_u if x['answer'] not in recent_t), None)
        if pick: tl_u.remove(pick); e['2200'] = pick
        cal[day] = e
    left = {k: len(v) for k, v in c.items()}; left['timeline'] = len(tl_u)
    CAL.write_text(json.dumps({'built': datetime.date.today().isoformat(), 'slots': SLOTS, 'left_after': left, 'days': cal}, ensure_ascii=False, indent=1), encoding='utf-8')
    print('calendar', days, 'days from', start, '| left after:', left)


if __name__ == '__main__':
    if sys.argv[1] == 'build':
        build(sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat(), int(sys.argv[3]) if len(sys.argv) > 3 else 30)
    elif sys.argv[1] == 'today':
        cal = json.loads(CAL.read_text(encoding='utf-8'))['days'].get(sys.argv[2], {})
        for slot, x in sorted(cal.items()): print(slot, x['template'], x['id'])
