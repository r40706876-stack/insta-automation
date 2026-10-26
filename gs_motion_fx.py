"""Reusable perspective cards and coastal glow for topic-specific GS scenes."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
VERSION=1
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def perspective_card(canvas,center,size,rows,font,accent='#49ddf5',angle=0,tilt=0):
 """Rows = [(text, font_size, color), ...]. Preserve full Hindi glyphs."""
 w,h=size;scale=2
 tile=Image.new('RGBA',(w*scale,h*scale));d=ImageDraw.Draw(tile)
 for y in range(h*scale):
  q=y/max(1,h*scale-1);d.line((0,y,w*scale,y),fill=(int(22-7*q),int(56-15*q),int(79-20*q),255))
 d.rounded_rectangle((2,2,w*scale-3,h*scale-3),24*scale,outline=accent,width=3*scale)
 d.rounded_rectangle((25*scale,15*scale,(w-25)*scale,22*scale),3*scale,fill=accent)
 for j,(s,n,col) in enumerate(rows):
  n=int(n*scale);f=font(n)
  while d.textlength(s,font=f)>(w-40)*scale:n-=1;f=font(n)
  yy=(.31+j*.46/max(1,len(rows)-1))*h*scale
  d.text((w*scale/2,yy),s,font=f,fill=col,anchor='mm')
 tile=tile.resize((w,h),Image.Resampling.LANCZOS)
 a,b=angle,tilt
 ry=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
 rx=np.array([[1,0,0],[0,math.cos(b),-math.sin(b)],[0,math.sin(b),math.cos(b)]])
 verts=np.array([[-w/2,-h/2,0],[w/2,-h/2,0],[w/2,h/2,0],[-w/2,h/2,0]])@ry.T@rx.T
 focal=1000
 quad=[(center[0]+x*focal/(focal-z),center[1]+y*focal/(focal-z)) for x,y,z in verts]
 left=math.floor(min(x for x,y in quad))-2;top=math.floor(min(y for x,y in quad))-2
 right=math.ceil(max(x for x,y in quad))+2;bottom=math.ceil(max(y for x,y in quad))+2
 target=[(x-left,y-top) for x,y in quad];source=[(0,0),(w,0),(w,h),(0,h)]
 mat=[];rhs=[]
 for (x,y),(u,v) in zip(target,source):
  mat.append([x,y,1,0,0,0,-u*x,-u*y]);rhs.append(u)
  mat.append([0,0,0,x,y,1,-v*x,-v*y]);rhs.append(v)
 coeff=np.linalg.solve(np.array(mat),np.array(rhs))
 warped=tile.transform((right-left,bottom-top),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)
 shadow=Image.new('RGBA',canvas.size);sd=ImageDraw.Draw(shadow)
 sd.polygon([(x+8,y+16) for x,y in quad],fill=(0,0,0,125))
 shadow=shadow.filter(ImageFilter.GaussianBlur(11))
 canvas.paste(shadow,(0,0),shadow);canvas.paste(warped,(left,top),warped)
def coastline_light(mapim,landmask):
 """Artistic coastal rim, derived from coastline; not bathymetric data."""
 rim=ImageChops.subtract(landmask.filter(ImageFilter.GaussianBlur(10)),landmask)
 rim=rim.point(lambda v:min(150,v*2))
 mapim.paste(Image.new('RGB',mapim.size,'#2a8caa'),(0,0),rim)
