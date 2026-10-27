"""Verify the generated MP4 itself, not just the scene script."""
import json,subprocess,re,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
r=Path(sys.argv[1]);p=r/'final.mp4';meta=json.loads((r/'audio.json').read_text())
v=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));video=next(s for s in v['streams'] if s['codec_type']=='video');assert any(s['codec_type']=='audio' for s in v['streams']);dur=float(v['format']['duration']);assert abs(dur-sum(meta['seconds']))<.2;assert (video['width'],video['height'])==(720,1280)
run=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-vf','blackdetect=d=0.15:pix_th=0.08','-af','volumedetect','-f','null','-'],text=True,capture_output=True);assert run.returncode==0;assert 'black_start:' not in run.stderr
mean=float(re.search(r'mean_volume: ([\-\d.]+)',run.stderr)[1]);peak=float(re.search(r'max_volume: ([\-\d.]+)',run.stderr)[1]);assert mean>-35 and peak<=0
sheet=Image.new('RGB',(1080,1020),(7,20,30));draw=ImageDraw.Draw(sheet);times=np.linspace(1,dur-1,8)
for i,t in enumerate(times):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-']);im=Image.frombytes('RGB',(720,1280),raw);x=i%4*270;y=i//4*510;sheet.paste(im.resize((270,480)),(x,y));draw.text((x+8,y+484),f'{t:.1f}s',fill='white')
sheet.save(r/'contact_sheet.jpg',quality=92)
checks={'duration_seconds':dur,'dimensions':[720,1280],'fps':video['r_frame_rate'],'decoded_without_errors':True,'black_intervals':0,'audio_mean_db':mean,'audio_peak_db':peak,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'voice':meta.get('voice'),'published':False}
(r/'file_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2),flush=True)
