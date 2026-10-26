import base64,hashlib,json,datetime
from pathlib import Path
import auto_poster as e
root=Path('experiments/polished_publish'); receipt=root/'published.json'
if receipt.exists():
 print(receipt.read_text());raise SystemExit()
b=base64.b64decode(''.join((root/f'video.b64.{i}').read_text().strip() for i in range(5)))
assert hashlib.sha256(b).hexdigest()=='6ceb2ebf9d851bd113d911e0a50c1d60f223f7c6b9ed2a0d7916ade7bf3a3335'
p=root/'reel.mp4';p.write_bytes(b)
account=e.requests.get(e.GRAPH+e.IG_USER_ID,params={'fields':'username','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
assert account.get('username','').lower()=='minuteme_gs', 'Wrong Instagram account'
e._with_series=lambda x:x
caption='समुद्र बगल में, फिर भी रेगिस्तान! बारिश कहाँ गई? 🌊🏜️\nअटाकामा को समझो: ठंडी हम्बोल्ट धारा, हवा की स्थिर परत, नीचे उतरती सूखी हवा और एंडीज़ की वर्षाछाया मिलकर सूखे में योगदान देते हैं।\nकोहरा होना और बारिश होना अलग हैं।\nअपने study partner को समझाकर देखो।\nशिक्षण चित्र सांकेतिक हैं; शुरुआती तट का दृश्य AI से बना है।\n#MinuteMeGS #Geography #GS #SSC #RailwayExam #StudyHindi'
pid=e.post_reel(str(p),caption,0)
assert pid,'Publication unconfirmed'
r={'media_id':pid,'sha256':hashlib.sha256(b).hexdigest(),'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
receipt.write_text(json.dumps(r,indent=2))
obj=e.requests.get(e.GRAPH+pid,params={'fields':'permalink','access_token':e.IG_ACCESS_TOKEN},timeout=30).json()
r['permalink']=obj.get('permalink');receipt.write_text(json.dumps(r,indent=2));print(json.dumps(r))
