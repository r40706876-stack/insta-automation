"""Discover real retrievable references; no reliance on invented model URLs."""
import json,os,re,urllib.parse,xml.etree.ElementTree as ET
import requests
UA={'User-Agent':'MinuteMeGS-AnimationStudio/1.0 (https://github.com/r40706876-stack/insta-automation)'}
def search(topic,subject='auto'):
 urls=[]
 key=os.getenv('GEMINI_API_KEY')
 if key:
  try:
   r=requests.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',headers={'x-goog-api-key':key},json={'contents':[{'parts':[{'text':'Find factual readable HTML sources for this educational topic: '+topic+'. Subject '+subject+'. Search the web. Prefer official government, academic, museum or science institutions. Give 4 exact HTTPS source URLs, no PDFs.'}]}],'tools':[{'google_search':{}}],'generationConfig':{'temperature':.1}},timeout=(15,75))
   if r.status_code==200:
    c=r.json()['candidates'][0];text=' '.join(p.get('text','') for p in c['content']['parts']);urls+=re.findall(r'https://[^\s<>\]\)"`]+',text)
    urls += [x['web']['uri'] for x in c.get('groundingMetadata',{}).get('groundingChunks',[]) if x.get('web',{}).get('uri')]
  except (requests.RequestException,ValueError,KeyError,IndexError):pass
 if not urls:
  try:
   r=requests.get('https://www.bing.com/search',params={'q':topic+' official educational source','format':'rss'},headers=UA,timeout=(10,25));r.raise_for_status()
   for item in ET.fromstring(r.content).findall('.//item'):
    link=item.findtext('link','')
    if link.startswith('https://'):urls.append(link)
  except (requests.RequestException,ET.ParseError):pass
 return list(dict.fromkeys(u.rstrip('.,;') for u in urls))[:8]

def encyclopedia(query):
 # Last-resort secondary factual reference, recorded transparently in sources.json.
 for lang in ('en','hi'):
  try:
   base='https://'+lang+'.wikipedia.org/w/api.php'
   data=requests.get(base,params={'action':'query','list':'search','srsearch':query,'srlimit':2,'format':'json'},headers=UA,timeout=(10,25));data.raise_for_status()
   for item in data.json().get('query',{}).get('search',[]):
    title=item['title'];res=requests.get(base,params={'action':'query','titles':title,'prop':'extracts','explaintext':1,'format':'json'},headers=UA,timeout=(10,25));res.raise_for_status()
    for page in res.json().get('query',{}).get('pages',{}).values():
     text=page.get('extract','')
     if len(text)>500:return {'url':'https://'+lang+'.wikipedia.org/wiki/'+urllib.parse.quote(title.replace(' ','_')),'text':text[:14000],'source_type':'encyclopedia_fallback'}
  except (requests.RequestException,ValueError,KeyError):continue
 return None
