"""Read existing Graph insights; unsupported metrics stay missing, never zero."""
import datetime as dt
import json
import os
from pathlib import Path
import requests
from gs_learning import ingest,timestamp

def collect():
    token=os.getenv('IG_ACCESS_TOKEN');account=os.getenv('IG_USER_ID')
    if not token or not account: raise RuntimeError('Instagram analytics credentials unavailable')
    # Use the same API version as the publisher; do not silently change account integrations.
    base='https://graph.facebook.com/'+os.getenv('IG_GRAPH_VERSION','v19.0')+'/'
    diagnostics=[]
    def get(path,**params):
        response=requests.get(base+path,params=dict(params,access_token=token),timeout=40)
        data=response.json()
        if response.status_code>=400 or 'error' in data:
            err=data.get('error',{})
            diagnostics.append({'endpoint':path,'http_status':response.status_code,'code':err.get('code'),'type':err.get('type')})
            return None
        return data
    now=dt.datetime.now(dt.timezone.utc);metadata={}
    for parent in ('experiments/scheduled_visual_gs','experiments/daily_visual_gs'):
        for p in Path(parent).glob('*/published.json'):
            try:
                receipt=json.loads(p.read_text());script=json.loads((p.parent/'script.json').read_text());metadata[str(receipt['media_id'])]=script
            except (OSError,ValueError,KeyError):continue
    account_data=get(account,fields='followers_count') or {}
    rows=[];after=None;errors=[]
    for page in range(6):
        params=dict(fields='id,timestamp,caption,media_product_type,like_count,comments_count',limit=50)
        if after:params['after']=after
        media=get(account+'/media',**params)
        if media is None:raise RuntimeError('Cannot read Instagram media; inspect token permissions/API version')
        stop=False
        for item in media.get('data',[]):
            age=(now-timestamp(item['timestamp'])).total_seconds()/3600
            if age>180:stop=True;continue
            if item.get('media_product_type')!='REELS':continue
            script=metadata.get(str(item['id']),{})
            row=dict(media_id=str(item['id']),published_at=item['timestamp'],observed_at=now.isoformat(),source='instagram_graph',topic=script.get('reference',{}).get('topic_key') or script.get('reference',{}).get('question') or 'unmapped:'+str(item['id']),subject=script.get('subject'),format=script.get('experiment_format','legacy_unclassified'),likes=item.get('like_count'),comments=item.get('comments_count'),total_followers=account_data.get('followers_count'))
            # Same metric names as the repository's weekly report; query independently so
            # a deprecated metric cannot discard all the other observations.
            for target,metric in (('views','views'),('reach','reach'),('saves','saved'),('shares','shares')):
                result=get(str(item['id'])+'/insights',metric=metric)
                if result and result.get('data'):
                    row[target]=(result['data'][0].get('values') or [{}])[0].get('value')
                else:errors.append({'media_id':str(item['id']),'metric':metric,'status':'unavailable'})
            rows.append(row)
        after=media.get('paging',{}).get('cursors',{}).get('after')
        if stop or not media.get('paging',{}).get('next') or not after:break
    ingest(rows)
    if errors:print('::warning::Some Instagram insights are unavailable; use the connected Metricool snapshot bridge. Missing values were not changed to zero.')
    path=Path('reports/gs_collection.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps({'observed_at':now.isoformat(),'reels':len(rows),'status':'partial' if errors else 'ok','unavailable':errors,'diagnostics':diagnostics,'note':'Watch time, 3-sec rate, retention and per-reel follows require verified export with explicit units. Total followers is an account snapshot, not reel attribution.'},indent=2))
if __name__=='__main__':collect()
