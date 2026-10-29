"""Choose the next unposted Body topic (rotation) and add a teaser for the one after it.
python pick_next.py plan.json            -> writes the next topic's plan + 'next'
python pick_next.py plan.json --teaser   -> only adds 'next' to an existing plan.json"""
import json, sys, glob
from pathlib import Path
R = Path(__file__).parent; ROOT = R.parent.parent
idx = json.loads((R / 'topics' / 'index.json').read_text(encoding='utf-8'))
order = [k for k in idx if 'demo' not in k]
posted = set()
for f in glob.glob(str(ROOT / 'downloads' / 'body' / '*' / 'published.json')):
    t = json.loads(Path(f).read_text(encoding='utf-8')).get('title', '')
    posted.add(t.split('|')[-1].strip())
def hook(name): return json.loads((R / idx[name]).read_text(encoding='utf-8'))['scenes'][0]['title']
out = Path(sys.argv[1])
if '--teaser' in sys.argv:
    plan = json.loads(out.read_text(encoding='utf-8')); cur = plan.get('topic', '')
else:
    todo = [k for k in order if k not in posted] or order          # all done -> start the cycle again
    cur = todo[0]; plan = json.loads((R / idx[cur]).read_text(encoding='utf-8'))
plan['day'] = len(posted) + (0 if cur in posted else 1)          # series number shown on the badge
rest = [k for k in order if k not in posted and k != cur] or [k for k in order if k != cur]
if rest: plan['next'] = hook(rest[0])
out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding='utf-8')
print('TOPIC', plan.get('topic'), '| NEXT', plan.get('next'))
