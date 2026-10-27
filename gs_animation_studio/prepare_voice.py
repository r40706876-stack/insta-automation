"""Bounded Gemini Charon preference; one consistent fallback voice for all scenes."""
import os,json,base64,wave,subprocess,asyncio,math
from pathlib import Path
import numpy as np

def prepare(root,recipe):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);lines=recipe['speech'];provider=None
 # Each scene is separately timed to its real audio. No estimated word boundaries.
 key=os.getenv('GEMINI_API_KEY','');mode=os.getenv('STUDIO_VOICE','auto')
 if key and mode!='female_fallback':
  import requests
  try:
   for i,line in enumerate(lines):
    body={'contents':[{'parts':[{'text':line}]}],'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'prebuiltVoiceConfig':{'voiceName':'Charon'}}}}}
    resp=requests.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent',headers={'x-goog-api-key':key},json=body,timeout=45)
    if resp.status_code!=200:raise RuntimeError('Gemini HTTP '+str(resp.status_code))
    parts=resp.json()['candidates'][0]['content']['parts'];part=next(p['inlineData'] for p in parts if 'inlineData' in p)
    raw=base64.b64decode(part['data']);rate=24000
    with wave.open(str(root/f'gemini_{i}.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(raw)
   files=[root/f'gemini_{i}.wav' for i in range(len(lines))];provider='Gemini / Charon male'
  except Exception as exc:
   # Never log API URLs with keys or response bodies.
   print('Gemini male unavailable; using the approved female fallback:',type(exc).__name__,flush=True)
 if not provider:
  import edge_tts
  import edge_tts.communicate as ec
  ec._SSL_CTX.load_default_certs()
  async def create():
   for i,line in enumerate(lines):await edge_tts.Communicate(line,'hi-IN-SwaraNeural',rate='+14%').save(str(root/f'speech_{i}.mp3'))
  asyncio.run(create());files=[root/f'speech_{i}.mp3' for i in range(len(lines))];provider='Edge / Swara female fallback'
 chunks=[]
 for p in files:chunks.append(np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ar','44100','-ac','1','-']),np.float32).copy())
 ds=[len(c)/44100+.25 for c in chunks];out=np.zeros(math.ceil(sum(ds)*44100),np.float32)
 for c,t in zip(chunks,np.cumsum([0]+ds[:-1])):k=round((t+.08)*44100);out[k:k+len(c)]=c
 with wave.open(str(root/'voice.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100);w.writeframes((np.clip(out,-.97,.97)*32767).astype('<i2').tobytes())
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(root/'voice.wav'),str(root/'voice.flac')],check=True)
 (root/'audio.json').write_text(json.dumps({'speech':lines,'seconds':ds,'voice':provider},ensure_ascii=False,indent=2));print(provider,ds,flush=True)
if __name__=='__main__':
 import sys
 r=Path(sys.argv[1]);prepare(r,json.loads((r/'recipe.json').read_text()))
