"""Read-only Instagram metrics, using the existing account token. Never infer skip rate."""
import datetime,json,os,urllib.request,urllib.parse,urllib.error
from pathlib import Path
ROOT=Path('experiments/all_subject_trial_20261026')
PLAN=Path('experiments/all_subject_trial_plan.json')
METRICS=['reels_skip_rate','ig_reels_avg_watch_time','views','reach','shares','saved']
GRAPH='https://graph.facebook.com/v19.0/'
def get(path,params):
    token=os.environ.get('IG_ACCESS_TOKEN','').strip()
    if not token:return {'error':{'message':'IG_ACCESS_TOKEN missing','code':10}}
    req=urllib.request.Request(GRAPH+path+'?'+urllib.parse.urlencode(params),headers={'Authorization':'Bearer '+token})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
    except urllib.error.HTTPError as e:
        try:return json.loads(e.read().decode())
        except Exception:return {'error':{'message':'HTTP '+str(e.code),'code':e.code}}
    except Exception as e:return {'error':{'message':type(e).__name__}}
def capture(mid):
    out={'media_id':mid,'metrics':{},'errors':{}}
    meta=get(mid,{'fields':'id,timestamp,permalink,like_count,comments_count'})
    if 'error' not in meta:out['media']=meta
    else:out['metadata_error']=meta['error']
    for met in METRICS:
        r=get(mid+'/insights',{'metric':met})
        data=r.get('data') or []
        if data:
            item=data[0]
            val=(item.get('total_value') or {}).get('value')
            if val is None and item.get('values'):val=item['values'][-1].get('value')
            if val is not None:out['metrics'][met]=val
            else:out['errors'][met]='Metric response contained no value'
        else:
            err=r.get('error') or {'message':'No metric data'}
            out['errors'][met]={k:err.get(k) for k in ['code','message','error_subcode'] if k in err}
            if err.get('code') in (10,200,403):
                out['permission_blocked']=True
                break
    out['captured_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return out
def parse(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def main():
    import sys
    ROOT.mkdir(parents=True,exist_ok=True)
    if len(sys.argv)>1 and sys.argv[1]=='probe':
        out=capture('18121456249987192')
        (ROOT/'metrics_access_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
        print(json.dumps({'permission_blocked':out.get('permission_blocked',False),'available':list(out['metrics']),'errors':out['errors']},ensure_ascii=False));return
    plan=json.loads(PLAN.read_text());now=datetime.datetime.now(datetime.timezone.utc)
    for slot in plan['slots']:
        d=ROOT/slot['id'];receipt=d/'published.json';snap=d/'metrics_24h.json'
        if snap.exists() or not receipt.exists():continue
        r=json.loads(receipt.read_text());published=parse(r['published_utc'])
        age=(now-published).total_seconds()/3600
        if age<24:continue
        out=capture(r['media_id']);out.update({'id':slot['id'],'subject':r['subject'],'published_utc':published.isoformat(),'age_hours':round(age,3),'within_24h_window':age<=24.75})
        snap.write_text(json.dumps(out,ensure_ascii=False,indent=2));print('SNAPSHOT',slot['id'],round(age,2))
    rows=[]
    for slot in plan['slots']:
        d=ROOT/slot['id'];snap=d/'metrics_24h.json'
        if snap.exists():rows.append(json.loads(snap.read_text()))
    all_ready=len(rows)==len(plan['slots'])
    summary={'trial':plan['trial'],'all_snapshots_ready':all_ready,'captured_count':len(rows),'rows':rows,'limitations':['One reel per subject; publication time and sample size confound subject comparisons.','Skip rate is the direct reels_skip_rate API metric, never average watch time or retention.','If API access is denied, native Instagram Insights screenshots are required.']}
    (ROOT/'comparison.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    md=['# Seven-subject trial — 24-hour snapshots','', '| Subject | Age (h) | Skip rate (API) | Views | Reach | Shares | Saves |','|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        m=r['metrics'];md.append('| '+str(r['subject'])+' | '+str(r['age_hours'])+' | '+str(m.get('reels_skip_rate','unavailable'))+' | '+str(m.get('views','unavailable'))+' | '+str(m.get('reach','unavailable'))+' | '+str(m.get('shares','unavailable'))+' | '+str(m.get('saved','unavailable'))+' |')
    md+=['','A missing/permission-blocked metric is not zero. One post per subject cannot establish a causal winner.']
    (ROOT/'comparison.md').write_text('\n'.join(md))
    if all_ready:(ROOT/'snapshots_complete.flag').write_text(now.isoformat())
    deadline=max(parse(s['publish_utc']) for s in plan['slots'])+datetime.timedelta(hours=28)
    if now>=deadline:(ROOT/'observer_timeout.flag').write_text(now.isoformat())
    print('CAPTURED',len(rows),'of',len(plan['slots']))
if __name__=='__main__':main()
