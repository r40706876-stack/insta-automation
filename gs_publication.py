"""Shared future-reel branding and Instagram Collab policy."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
HANDLE='ar_publication'
PHONE='+91 89892 79637'
NOTES='सभी प्रतियोगी परीक्षाओं की तैयारी के लिए नोट्स उपलब्ध हैं।'
def caption(value):
    if PHONE not in value:
        value=value.rstrip()+'\n\n'+NOTES+'\nWhatsApp: '+PHONE+'\nhttps://wa.me/918989279637\n@'+HANDLE
    if len(value)>2200:raise ValueError('Caption exceeds Instagram limit after notes footer; shorten original caption')
    return value

def footer(size,font):
    w,h=size;band=max(120,round(h*.115));im=Image.new('RGBA',(w,band),'#fff3d4');d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,4),fill='#078783')
    lines=['सभी प्रतियोगी परीक्षाओं के लिए','नोट्स उपलब्ध हैं • AR Publication','WhatsApp: '+PHONE]
    for j,line in enumerate(lines):
        n=round(w*(.032 if j<2 else .040))
        while d.textlength(line,font=font(n))>w-32:n-=1
        d.text((w/2,band*(.20+j*.30)),line,font=font(n),fill='#164047' if j<2 else '#a43123',anchor='mm')
    return im

def prepare_video(src,font):
    src=Path(src)
    if src.name.endswith('_ar_notes.mp4'):return str(src)
    # Resolve dimensions without requiring a separate ffprobe binary.
    import re
    probe=subprocess.run(['ffmpeg','-hide_banner','-i',str(src)],capture_output=True,text=True)
    line=next((x for x in probe.stderr.splitlines() if 'Video:' in x),'')
    match=re.search(r'\b(\d{3,5})x(\d{3,5})\b',line)
    if not match:raise RuntimeError('Cannot determine reel dimensions')
    w,h=map(int,match.groups());w-=w%2;h-=h%2
    band=footer((w,h),font);reserved=band.height+(band.height%2)
    digest=hashlib.sha256(src.read_bytes()+b'ar-notes-v1').hexdigest()[:16]
    out=src.with_name(src.stem+'_'+digest+'_ar_notes.mp4');png=out.with_suffix('.png')
    if out.exists() and out.stat().st_size>1000:return str(out)
    band.save(png)
    # Reserve space instead of covering teaching text. Preserve aspect ratio and duration.
    graph=f'[0:v]scale={w}:{h-reserved}:force_original_aspect_ratio=decrease,pad={w}:{h}:x=(ow-iw)/2:y=0:color=0xf6f3ea[base];[base][1:v]overlay=0:{h-reserved}:format=auto,format=yuv420p[v]'
    try:
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-i',str(png),'-filter_complex',graph,'-map','[v]','-map','0:a?','-c:v','libx264','-profile:v','main','-pix_fmt','yuv420p','-preset','fast','-crf','19','-c:a','aac','-movflags','+faststart',str(out)],check=True,timeout=900)
    except Exception:
        out.unlink(missing_ok=True);raise
    finally:png.unlink(missing_ok=True)
    return str(out)

def container_policy(body):
    body['caption']=caption(body['caption'])
    body['collaborators']=json.dumps([HANDLE])
    return body
