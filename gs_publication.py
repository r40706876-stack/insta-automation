"""Shared future-reel branding and Instagram Collab policy."""
import hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
HANDLE='ar_publication'
PHONE='+91 89892 79637'
NOTES='सभी प्रतियोगी परीक्षाओं की तैयारी के लिए नोट्स उपलब्ध हैं।'
def caption(value):
    if PHONE not in value:
        value=value.rstrip()+'\n\n'+NOTES+'\nWhatsApp: '+PHONE+'\nhttps://wa.me/918989279637'
    if len(value)>2200:raise ValueError('Caption exceeds Instagram limit after notes footer; shorten original caption')
    return value

def footer(size,font):
    w,h=size;band=max(100,round(h*.085));im=Image.new('RGBA',(w,band),'#fff3d4');d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,4),fill='#078783')
    lines=['सभी प्रतियोगी परीक्षाओं के नोट्स उपलब्ध हैं','WhatsApp: '+PHONE]
    for j,line in enumerate(lines):
        n=round(w*(.034 if j==0 else .044))
        while d.textlength(line,font=font(n))>w-32:n-=1
        d.text((w/2,band*(.27+j*.45)),line,font=font(n),fill='#164047' if j==0 else '#a43123',anchor='mm')
    return im

def prepare_video(src,font):
    src=Path(src)
    if src.name.endswith(('_notes_safe_v2.mp4','_notes_end_v3.mp4')):return str(src)
    # The shared Studio compositor already includes the Notes banner (now as an end card).
    # Only skip the second banner for the exact hash verified by its export gate.
    check_path=src.parent/'file_checks.json'
    if check_path.exists():
        checked=json.loads(check_path.read_text());banner=checked.get('notes_banner') or {}
        if checked.get('quality_version')=='rich_3d_v1' and banner.get('version')=='studio-notes-v1' and banner.get('phone')==PHONE and checked.get('sha256')==hashlib.sha256(src.read_bytes()).hexdigest():
            return str(src)
    import re
    probe=subprocess.run(['ffmpeg','-hide_banner','-i',str(src)],capture_output=True,text=True)
    line=next((x for x in probe.stderr.splitlines() if 'Video:' in x),'')
    match=re.search(r'\b(\d{3,5})x(\d{3,5})\b',line)
    if not match:raise RuntimeError('Cannot determine reel dimensions')
    w,h=map(int,match.groups());w-=w%2;h-=h%2
    dm=re.search(r'Duration: (\d+):(\d+):([\d.]+)',probe.stderr)
    if not dm:raise RuntimeError('Cannot determine reel duration')
    dur=int(dm.group(1))*3600+int(dm.group(2))*60+float(dm.group(3))
    # 4 Nov: banner moved from a permanent top strip (which shrank the video and took the
    # hook's space) to an end card shown only in the last seconds. No scaling of the reel.
    show=min(3.0,max(1.2,dur*.3));start=max(0.0,dur-show)
    top=round(h*.105)//2*2
    banner_w=round(w*.80)//2*2
    band=footer((banner_w,h),font)
    digest=hashlib.sha256(src.read_bytes()+b'notes-end-v3').hexdigest()[:16]
    out=src.with_name(src.stem+'_'+digest+'_notes_end_v3.mp4');png=out.with_suffix('.png')
    if out.exists() and out.stat().st_size>1000:return str(out)
    band.save(png)
    graph=f"[0:v]scale={w}:{h}[base];[base][1:v]overlay={(w-banner_w)//2}:{top}:enable='gte(t,{start:.2f})':format=auto,format=yuv420p[v]"
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
