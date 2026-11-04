"""Age-matched analytics. Missing values remain null; no proxy retention/follows."""
import datetime as dt
import json
import math
from pathlib import Path
METRICS = ('views','reach','likes','comments','saves','shares','average_watch_time','three_second_rate','retention','followers_gained','followers_lost','total_followers')
FORMATS = ('exam_trap','visual_mystery','map_pyq_challenge')
UTC = dt.timezone.utc

def timestamp(value):
    value = dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if value.tzinfo is None:
        raise ValueError('Timezone required')
    return value.astimezone(UTC)

def normalize(row):
    for key in ('media_id','published_at','observed_at','source','topic','format'):
        if not row.get(key): raise ValueError('Missing '+key)
    age = (timestamp(row['observed_at'])-timestamp(row['published_at'])).total_seconds()/3600
    if age < 0: raise ValueError('Observation precedes publication')
    result = {k:row[k] for k in ('media_id','published_at','observed_at','source','topic','format')}
    result.update(subject=row.get('subject'),duration=row.get('duration'),age_hours=age)
    # Fixed windows prevent a seven-day lifetime total becoming a 24-hour result.
    result['window'] = next((label for label,h,tol in (('24h',24,3),('72h',72,6),('7d',168,12)) if abs(age-h)<=tol),None)
    for key in METRICS:
        value=row.get(key)
        if value is not None and (isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or value<0):
            raise ValueError('Invalid metric '+key)
        if key=='three_second_rate' and value is not None and value>100: raise ValueError('Use percent 0..100')
        result[key]=value
    for metric in ('shares','saves'):
        result[metric+'_per_1000']=1000*result[metric]/result['views'] if result['views'] and result[metric] is not None else None
    result['net_followers']=result['followers_gained']-result['followers_lost'] if result['followers_gained'] is not None and result['followers_lost'] is not None else None
    result['source_freshness']=row.get('source_freshness','not supplied')
    result['missing']=[k for k in METRICS if result[k] is None]
    return result

def read_snapshots(path):
    path=Path(path)
    if not path.exists() or not path.read_text().strip():
        return []
    rows=json.loads(path.read_text())
    if not isinstance(rows,list):
        raise ValueError('Analytics snapshots must be a JSON array')
    return rows

def ingest(rows,path='experiments/learning/snapshots.json'):
    path=Path(path); old=read_snapshots(path)
    indexed={(r['media_id'],r['observed_at'],r['source']):r for r in old}
    for row in rows:
        row=normalize(row); indexed[row['media_id'],row['observed_at'],row['source']]=row
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(list(indexed.values()),ensure_ascii=False,indent=2))

def cohort(rows,window='72h'):
    # Exactly one closest-to-target observation per media ID, even after repeated imports.
    target={'24h':24,'72h':72,'7d':168}[window]; selected={}
    for row in rows:
        if row.get('window')!=window: continue
        key=row['media_id']
        def rank(r):return (sum(r.get(k) is not None for k in METRICS),-abs(r['age_hours']-target))
        if key not in selected or rank(row)>rank(selected[key]):selected[key]=row
    return list(selected.values())

def evidence_score(question,path='experiments/learning/snapshots.json'):
    rows=read_snapshots(path)
    samples=[r for r in cohort(rows) if r.get('subject')==question.get('subject') and r.get('topic')==question.get('topic_key',question.get('question'))]
    if len(samples)<3:
        samples=[r for r in cohort(rows) if r.get('subject')==question.get('subject')]
    complete=[r for r in samples if r.get('views',0) and r['views']>=100 and all(r.get(k) is not None for k in ('shares_per_1000','saves_per_1000'))]
    if len(complete)<3: return 0.0
    return sum(min(2,r['shares_per_1000']/3)+min(2,r['saves_per_1000']/8)+(min(1,r['three_second_rate']/60) if r.get('three_second_rate') is not None else 0) for r in complete)/len(complete)

def experiment(day,subject):
    # Stable balanced assignment; existing slots and PYQ/mega are preserved.
    offset=sum(subject.encode('utf-8'))
    # Map challenge only makes sense for Geography; other subjects got a meaningless
    # India map and a "नक्शा टेस्ट" label (e.g. Polity, 3 Nov), which killed the hook.
    pool=FORMATS if subject=='Geography' else tuple(f for f in FORMATS if f!='map_pyq_challenge')
    return pool[(dt.date.fromisoformat(day).toordinal()+offset)%len(pool)]

def report(rows):
    output={'generated_at':dt.datetime.now(UTC).isoformat(),'windows':{},'note':'3-sec rate is not retention. Targets are experiments, not guarantees.'}
    for window in ('24h','72h','7d'):
        groups={}
        for row in cohort(rows,window): groups.setdefault((row.get('subject'),row['format']),[]).append(row)
        output['windows'][window]=[]
        for (subject,fmt),group in groups.items():
            metrics={}
            for metric in ('shares_per_1000','saves_per_1000','average_watch_time','three_second_rate','retention','net_followers'):
                vals=[r[metric] for r in group if r.get(metric) is not None]
                metrics[metric]={'mean':sum(vals)/len(vals) if vals else None,'n':len(vals)}
            output['windows'][window].append({'subject':subject,'format':fmt,'reels':len(group),'metrics':metrics,'decision':'collect_more' if sum(bool(r.get('views',0) and r['views']>=100 and r.get('shares_per_1000') is not None and r.get('saves_per_1000') is not None) for r in group)<3 else 'review_matched_cohort','automatic_scale':False})
    now=dt.datetime.now(UTC)
    weekly={}
    for label,low,high in (('current',0,7),('previous',7,14)):
        recent=[r for r in cohort(rows,'24h') if low<=(now-timestamp(r['published_at'])).total_seconds()/86400<high]
        usable=[r for r in recent if r.get('views',0) and r['views']>=100 and r.get('shares_per_1000') is not None and r.get('saves_per_1000') is not None]
        score=lambda r:r['shares_per_1000']/3+r['saves_per_1000']/8
        comparable=len(usable)>=3 and max(map(score,usable))>min(map(score,usable))
        weekly[label]={'reels':len(recent),'best':max(usable,key=score)['media_id'] if comparable else None,'weakest':min(usable,key=score)['media_id'] if comparable else None,'basis':'24h share/save rate; hypotheses only','mean_shares_per_1000':sum(r['shares_per_1000'] for r in usable)/len(usable) if usable else None,'mean_saves_per_1000':sum(r['saves_per_1000'] for r in usable)/len(usable) if usable else None}
    # Require actual age-matched results before declaring a winner.
    candidates=[]
    for entry in output['windows']['72h']:
        m=entry['metrics']
        if entry['decision']!='review_matched_cohort':
            continue
        shares=m['shares_per_1000']['mean']
        saves=m['saves_per_1000']['mean']
        watch=m['average_watch_time']['mean']
        if shares is None or saves is None or watch is None:
            continue
        candidates.append({'subject':entry['subject'],'format':entry['format'],'reels':entry['reels'],
                           'shares_per_1000':shares,'saves_per_1000':saves,'average_watch_time':watch})
    output['format_evidence']={'eligible':candidates,'winner':None,
        'decision':'manual_review_required',
        'reason':'No automatic winner from sparse or unmatched cohorts; compare subject and age before rollout'}
    output['experimental_targets']={'three_second_rate_percent':60,'shares_per_1000':3,'saves_per_1000':8,'note':'Experimental goals; not benchmarks or guarantees'}
    output['weekly']=weekly
    output['weekly_change']={key:weekly['current'][key]-weekly['previous'][key] if weekly['current'][key] is not None and weekly['previous'][key] is not None else None for key in ('mean_shares_per_1000','mean_saves_per_1000')}
    return output

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--import-json');p.add_argument('--store',default='experiments/learning/snapshots.json');p.add_argument('--report',default='reports/gs_learning.json');a=p.parse_args()
    if a.import_json: ingest(json.loads(Path(a.import_json).read_text()),a.store)
    rows=read_snapshots(a.store)
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(report(rows),ensure_ascii=False,indent=2))
