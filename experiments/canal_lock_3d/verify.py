import json,subprocess,hashlib,re,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path(__file__).resolve().parent;p=R/'panama_water_lift_3d.mp4'
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]))
v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'])==(720,1280);duration=float(info['format']['duration']);expected=sum(json.loads((R/'audio.json').read_text())['seconds']);assert abs(duration-expected)<.15
proc=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-vf','blackdetect=d=0.15:pix_th=0.08','-af','volumedetect','-f','null','-'],capture_output=True,text=True)
assert proc.returncode==0,proc.stderr[-1500:];assert not re.search(r'black_start:',proc.stderr),'Black interval found'
mean=float(re.search(r'mean_volume: ([\-\d.]+)',proc.stderr)[1]);peak=float(re.search(r'max_volume: ([\-\d.]+)',proc.stderr)[1]);assert mean>-35 and peak<=0
TIMES=[2,8,13,16,22,28,32,39];sheet=Image.new('RGB',(4*270,2*510),(7,20,30));d=ImageDraw.Draw(sheet)
for i,t in enumerate(TIMES):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 im=Image.frombytes('RGB',(720,1280),raw);im.resize((270,480)).save(R/f'qa_{t:02d}.jpg');x=i%4*270;y=i//4*510;sheet.paste(im.resize((270,480)),(x,y));d.text((x+8,y+484),f'{t}s',fill='white')
sheet.save(R/'contact_sheet.jpg',quality=92)
# Check actual rendered mechanism region, excluding text banners, changes during each physical action.
def crop(t):
 raw=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(p),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
 return np.array(Image.frombytes('RGB',(720,1280),raw),dtype=np.float32)[370:1010,130:640]
changes={}
for name,t1,t2 in [('ship_entry',6,11),('gate_closure',12.3,14),('actual_lift',18,27),('upper_gate_opening',27.5,30),('ship_departure',32,40)]:
 diff=np.abs(crop(t1)-crop(t2));changes[name]={'mean_pixel_difference':round(float(diff.mean()),3),'changed_fraction':round(float((diff.max(axis=2)>12).mean()),4)};assert changes[name]['changed_fraction']>.005,name
out={'duration_seconds':duration,'dimensions':[720,1280],'fps':v['r_frame_rate'],'decoded_without_errors':True,'black_intervals':0,'audio_mean_db':mean,'audio_peak_db':peak,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actual_rendered_motion_checks':changes,'video_published':False}
(R/'file_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
