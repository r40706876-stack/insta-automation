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
# Inspect pixels inside each mechanism, excluding the title and footer.
def region(t,roi):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 im=np.array(Image.frombytes('RGB',(720,1280),raw),dtype=np.float32)
 x1,y1,x2,y2=roi;return im[y1:y2,x1:x2]
starts=np.cumsum([0]+meta['seconds'][:-1]);motion_checks={}
if (r/'recipe.json').exists():
 opened=starts[1]+max(.5,meta['seconds'][1]*.55)
 samples=[('caps_move',opened-.4,opened+.05,(230,440,380,700)),('water_flows',starts[2]+.4,starts[2]+.9,(350,500,630,940)),('dam_base_widens',starts[4]+.45,starts[4]+2.8,(250,600,560,950))]
else:
 samples=[('ship_entry',starts[1]+.4,starts[2]-.5,(80,450,570,1000)),('ship_lift',starts[3]+.2,starts[4]-.4,(130,400,640,1000))]
for name,t1,t2,roi in samples:
 delta=np.abs(region(t1,roi)-region(t2,roi));fraction=float((delta.max(axis=2)>12).mean())
 assert fraction>.001,('No visible motion in mechanism',name,fraction)
 motion_checks[name]={'changed_fraction':round(fraction,5)}
checks={'duration_seconds':dur,'dimensions':[720,1280],'fps':video['r_frame_rate'],'decoded_without_errors':True,'black_intervals':0,'audio_mean_db':mean,'audio_peak_db':peak,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'voice':meta.get('voice'),'published':False,'actual_rendered_motion_checks':motion_checks}
(r/'file_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2),flush=True)
