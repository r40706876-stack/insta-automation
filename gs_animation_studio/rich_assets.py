"""Reusable Blender-only anatomy, coastline, and sourced map assets. No model-written code."""
import json,math
from pathlib import Path
from mathutils import Vector

def configure(context):
 globals().update({k:context[k] for k in ('bpy','R','mat','empty','sphere','cyl','cone','box','line','white','gold','skin','dark','water','cyan','green','red')})
 global sand,foam,cloth,brown,land,sea
 sand=mat('Warm sand',(.68,.48,.23));foam=mat('Sea foam',(.77,.96,.95));cloth=mat('Handwoven white',(.92,.9,.79));brown=mat('Staff wood',(.24,.1,.035));land=mat('Map land',(.15,.57,.4));sea=mat('Map sea',(.025,.24,.37))
def ell(name,pos,scale,m,parent):
 o=sphere(name,pos,1,m,parent);o.scale=scale;return o

def bone(name,pivot,length,r,m):
 o=cyl(name,(0,0,-length/2),r,length,m,pivot);sphere(name+' joint',(0,0,-length),r,m,pivot);return o

def human(parent,pos=(0,0,0),gandhi=False,color=None,scale=1,role='ordinary'):
 if color is None:color=cyan
 root=empty('Gandhi' if gandhi else 'Marcher',parent);root.location=pos;root.scale=(scale,)*3
 body=empty('Articulated pelvis',root);body.location.z=.99
 ell('Hips',(0,0,0),(.22,.15,.18),cloth,body)
 ell('Lean chest' if gandhi else 'Kurta',(0,0,.49),(.24 if gandhi else .31,.155,.49),skin if gandhi else color,body)
 ell('Neck',(0,0,1.02),(.085,.08,.14),skin,body)
 head=empty('Head',body);head.location=(0,-.015,1.29)
 ell('Bald head' if gandhi else 'Face',(0,0,0),(.205,.19,.27),skin,head)
 for x in [-.205,.205]:ell('Ear',(x,0,-.015),(.04,.035,.075),skin,head)
 ell('Nose',(0,-.195,-.015),(.045,.085,.075),skin,head)
 for x in [-.082,.082]:
  ell('Eye',(x,-.183,.052),(.021,.014,.013),dark,head)
  if gandhi:
   line('Round wire spectacles',[(x+.077*math.cos(j*math.tau/32),-.208,.045+.077*math.sin(j*math.tau/32)) for j in range(33)],.009,brown,head)
 if gandhi:
  line('Glasses bridge',[(-.025,-.21,.045),(.025,-.21,.045)],.009,brown,head)
  for x in [-1,1]:line('Glasses temple',[(x*.16,-.2,.05),(x*.2,.02,.05)],.008,brown,head)
  line('Small moustache',[(-.055,-.197,-.095),(0,-.21,-.1),(.055,-.197,-.095)],.012,white,head)
 elif role=='marcher':
  cap=cyl('White Gandhi cap',(0,0,.23),.215,.14,cloth,head);cap.scale.y=.8
 if not gandhi and role not in ('marcher','soldier'):
  ell('Hair',(0,.025,.16),(.208,.185,.14),dark,head)
 # Dhoti folds for Gandhi; trousers for other adults.
 if gandhi or role=='marcher':
  bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.31,radius2=.23,depth=.55,location=(0,0,-.12));skirt=bpy.context.object;skirt.name='Dhoti cloth';skirt.parent=body;skirt.data.materials.append(cloth)
  for x in [-.12,0,.12]:line('Dhoti folds',[(x,-.225,.13),(x*.85,-.275,-.38)],.012,white,body)
 if gandhi:
  # A diagonal shawl leaves the lean torso visible.
  line('White shoulder shawl',[(-.2,-.05,.94),(-.23,-.2,.7),(-.08,-.21,.37),(.18,-.16,.18)],.1,cloth,body)
  ell('Shawl on shoulder',(-.23,0,.82),(.09,.2,.23),cloth,body)
 arms=[];legs=[]
 for side in [-1,1]:
  hip=empty('Hip',root);hip.location=(side*.13,0,.99)
  bone('Upper leg',hip,.43,.066,skin if gandhi else dark)
  knee=empty('Knee',hip);knee.location.z=-.43;bone('Shin',knee,.43,.052,skin if gandhi else dark)
  ell('Sandals',(0,-.055,-.91),(.087,.17,.035),brown,hip)
  legs.append((hip,knee))
  shoulder=empty('Shoulder',body);shoulder.location=(side*.25,0,.85)
  bone('Upper arm',shoulder,.39,.051,skin if gandhi else color)
  elbow=empty('Elbow',shoulder);elbow.location.z=-.39;bone('Forearm',elbow,.35,.043,skin)
  hand=empty('Hand anchor',elbow);hand.location.z=-.37;ell('Hand',(0,0,0),(.065,.045,.09),skin,hand)
  arms.append((shoulder,elbow,hand))
 staff=line('Walking staff',[(-.05,0,-.7),(.02,0,.75)],.023,brown,arms[0][2]) if gandhi else None
 salt=box('Salt in raised hand',(0,-.04,-.04),(.11,.1,.09),white,arms[1][2]);salt.scale=(0,0,0)
 return {'root':root,'body':body,'head':head,'arms':arms,'legs':legs,'salt':salt,'gandhi':gandhi,'origin':Vector(pos)}

def key(o,path,frame):o.keyframe_insert(data_path=path,frame=frame)
def pose(h,q,frame,walk=False,collect=False,hold=False):
 cycle=q*math.tau*4;root=h['root'];body=h['body'];body.rotation_euler.x=0
 root.location=h['origin'];root.location.z+=.018*abs(math.sin(cycle)) if walk else 0
 for j,(hip,knee) in enumerate(h['legs']):
  hip.rotation_euler.x=.32*math.sin(cycle+j*math.pi) if walk else 0;knee.rotation_euler.x=-max(0,.35*math.sin(cycle+j*math.pi)) if walk else 0
  key(hip,'rotation_euler',frame);key(knee,'rotation_euler',frame)
 for j,(arm,elbow,hand) in enumerate(h['arms']):
  arm.rotation_euler=(.22*math.sin(cycle+j*math.pi) if walk else 0,(-1 if j==0 else 1)*.08,0);elbow.rotation_euler.x=-.15
  if j==0 and h['gandhi']:arm.rotation_euler.x=-.25;elbow.rotation_euler.x=-.75
  key(arm,'rotation_euler',frame);key(elbow,'rotation_euler',frame)
 h['salt'].scale=(0,0,0)
 if collect:
  bend=ease((q-.12)/.28)*(1-ease((q-.57)/.3));body.rotation_euler.x=1.25*bend;root.location.z-=.33*bend
  for hip,knee in h['legs']:
   hip.rotation_euler.x=1.0*bend;knee.rotation_euler.x=-1.8*bend;key(hip,'rotation_euler',frame);key(knee,'rotation_euler',frame)
  arm,elbow,_=h['arms'][1];arm.rotation_euler.x=-1.25*bend-1.3*ease((q-.65)/.25);arm.rotation_euler.y=-.24*bend;elbow.rotation_euler.x=-.15-.45*ease((q-.65)/.25)
  if q>.55:h['salt'].scale=(1,1,1)
  key(arm,'rotation_euler',frame);key(elbow,'rotation_euler',frame)
 if hold:
  arm,elbow,_=h['arms'][1];arm.rotation_euler.x=-1.05-.08*math.sin(cycle);elbow.rotation_euler.x=-.9;h['salt'].scale=(1,1,1);key(arm,'rotation_euler',frame);key(elbow,'rotation_euler',frame)
 key(body,'rotation_euler',frame);key(root,'location',frame);key(h['salt'],'scale',frame)

# Sea surface is a mesh whose vertices deform; white crest curves travel shoreward.
def coast(parent):
 box('Sandy coast',(0,-1,-.17),(14,7,.26),sand,parent)
 nx,ny=30,16;verts=[(-7+14*i/nx,1+7*j/ny,.08) for j in range(ny+1) for i in range(nx+1)];faces=[]
 for j in range(ny):
  for i in range(nx):
   a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 mesh=bpy.data.meshes.new('Deforming ocean surface');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Animated sea',mesh);bpy.context.collection.objects.link(o);o.parent=parent;o.data.materials.append(water)
 for polygon in mesh.polygons:polygon.use_smooth=True
 o.shape_key_add(name='Basis');wave=o.shape_key_add(name='Rolling waves')
 for v in wave.data:v.co.z=.08+.045*math.sin(v.co.x*1.3+v.co.y*2)+.025*math.cos(v.co.y*4)
 crests=[]
 for j in range(5):crests.append(line('Traveling foam',[(-7+i*.28,1.3+j*.9+.11*math.sin(i*.3),.19) for i in range(51)],.025,foam,parent))
 for i in range(15):
  x=-2+(i%5)*.27;y=-.7+(i//5)*.24;o=box('Natural salt crust',(x,y,.025),(.12,.12,.06),white,parent);o.rotation_euler.z=i*1.17
 return wave,crests

def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)

MAP_BOUNDS={'world':(-180,-85,180,85),'india':(67,6,98,37),'gujarat':(68,20,75,25)}
def clip_polygon(poly,bounds):
 xmin,ymin,xmax,ymax=bounds
 for axis,value,less in [(0,xmin,False),(0,xmax,True),(1,ymin,False),(1,ymax,True)]:
  source=poly;poly=[]
  if not source:break
  a=source[-1]
  for b in source:
   ia=a[axis]<=value if less else a[axis]>=value;ib=b[axis]<=value if less else b[axis]>=value
   if ia!=ib:
    t=(value-a[axis])/(b[axis]-a[axis]);v=[a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])];poly.append(v)
   if ib:poly.append(list(b[:2]))
   a=b
 return poly

PASTEL=[(1.0,.9,.42),(.82,.74,1.0),(.72,.95,.58),(1.0,.72,.55),(.6,.9,1.0),(1.0,.74,.88),(.88,1.0,.5),(1.0,.86,.62)]
def in_ring(pt,ring):
 x,y=pt;inside=False;j=len(ring)-1
 for i in range(len(ring)):
  xi,yi=ring[i][:2];xj,yj=ring[j][:2]
  if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/((yj-yi) or 1e-9)+xi:inside=not inside
  j=i
 return inside
def state_at(pt,states):
 for st in states:
  if any(in_ring(pt,r) for r in st['rings']):return st
 return None
def regional_bounds(spec):
 """Map Test 01 style: crop to the route region, always keep both seas in view."""
 pts=[p for p in spec.get('route',[])]+[m['at'] for m in spec.get('markers',[])]+[q for pair in spec.get('choice_lines',[]) for q in pair]+list(spec.get('frame_points',[]))+list(spec.get('_extra_pts',[]))
 if not pts:return None
 lat=[p[1] for p in pts]
 # State data has no J&K/Ladakh: never draw a regional state map for northern points.
 if max(lat)>31.5:return None
 ymin=max(8.0,min(lat)-3.2);ymax=min(31.5,max(lat)+3.2)
 if ymax-ymin<15:
  mid=(ymin+ymax)/2;ymin,ymax=mid-7.5,mid+7.5
  if ymin<8.0:ymin,ymax=8.0,23.0
  if ymax>31.5:ymin,ymax=16.5,31.5
 return (67.8,ymin,90.6,ymax)
def flat_fill(name,ring,point,m,parent,depth):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.fill_mode='BOTH';sp=c.splines.new('POLY');sp.points.add(len(ring)-1)
 for v,p in zip(sp.points,ring):p=point(p);v.co=(p.x,p.z,0,1)
 sp.use_cyclic_u=True;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=parent;o.rotation_euler.x=math.pi/2;o.location.y=depth;c.materials.append(m);return o
def _river_data():
 p=R/'india_rivers.json'
 return json.loads(p.read_text())['rivers'] if p.exists() else {}
def map_asset(parent,spec):
 region=spec.get('map_region','world');bounds=MAP_BOUNDS[region]
 if region=='india' and (spec.get('highlight_states') or spec.get('rivers') or spec.get('latitude_lines')):
  sts=json.loads((R/'india_states.json').read_text())['states'];extra=[]
  for st in sts:
   if st['name'] in spec.get('highlight_states',[]):
    big=max(st['rings'],key=len);extra+=[min(big,key=lambda q:q[0])[:2],max(big,key=lambda q:q[0])[:2],min(big,key=lambda q:q[1])[:2],max(big,key=lambda q:q[1])[:2]]
  rd=_river_data()
  for name in spec.get('rivers',[]):
   for seg in rd.get(name,{}).get('segments',[]):extra+=[seg[0],seg[-1]]
  for ll in spec.get('latitude_lines',[]):extra+=[[72,float(ll['lat'])],[88,float(ll['lat'])]]
  spec['_extra_pts']=extra
 regional=region=='india' and regional_bounds(spec)
 if regional:bounds=regional
 xmin,ymin,xmax,ymax=bounds
 if regional:
  # Upgrade (4 Nov): full-width coloured state map like the 1,789-view Map Test 01,
  # instead of a small dark single-colour silhouette.
  # The scene scales the whole group by spec size; keep the on-screen width ~6.0 units (frame ~6.4).
  scale=float((spec.get('size') or [1])[0]) or 1.0
  factor=6.0/((xmax-xmin)*scale);cz=0.0
  def point(p,y=-.08):return Vector(((p[0]-(xmin+xmax)/2)*factor,y,(p[1]-(ymin+ymax)/2)*factor+cz))
  sea_l=mat('Light map sea',(.62,.9,1.0));neigh=mat('Neighbour land',(.9,.88,.8));border=mat('State border',(.3,.33,.32));river=mat('River blue',(.02,.28,.78))
  box('Map ocean backplate',(0,.1,cz),((xmax-xmin)*factor+.15,.12,(ymax-ymin)*factor+.15),sea_l,parent)
  data=json.loads((R/'world_land.json').read_text())
  for feature in data['features']:
   geom=feature['geometry']
   for ring in ([q[0] for q in geom['coordinates']] if geom['type']=='MultiPolygon' else [geom['coordinates'][0]]):
    ring=clip_polygon(ring,bounds)
    if len(ring)>2:flat_fill('Neighbour and coast land',ring,point,neigh,parent,-.03)
  states=json.loads((R/'india_states.json').read_text())['states'];mats={}
  for i,st in enumerate(states):
   m=mats.setdefault(i%len(PASTEL),mat('State fill %d'%(i%len(PASTEL)),PASTEL[i%len(PASTEL)]))
   for ring in st['rings']:
    ring=clip_polygon([list(p[:2]) for p in ring],bounds)
    if len(ring)<3:continue
    flat_fill('Indian state '+st['name'],ring,point,m,parent,-.05)
    line('State boundary',[point(p,-.07) for p in ring+[ring[0]]],.005/scale,border,parent)
  context=[]
  for label,at in (('अरब सागर',(70.2,max(ymin+1.2,min(ymax-1.5,17.5)))),('बंगाल की खाड़ी',(87.6,max(ymin+1.2,min(ymax-1.5,17.5))))):
   if xmin<at[0]<xmax and ymin<at[1]<ymax and state_at(at,states) is None:context.append((label,point(at,-.15)))
  seen=set()
  for p in spec.get('route',[])[:1]+spec.get('route',[])[-1:]+[m['at'] for m in spec.get('markers',[])]:
   st=state_at(p,states)
   if st and st.get('hindi') and st['name'] not in seen and st['name']!='Andhra Pradesh':
    seen.add(st['name']);rings=st['rings'];big=max(rings,key=len);cx=sum(q[0] for q in big)/len(big);cy=sum(q[1] for q in big)/len(big)
    if xmin<cx<xmax and ymin<cy<ymax:context.append((st['hindi'],point((cx,cy),-.15)))
  choice=[]
  for a,b in spec.get('choice_lines',[]):
   pa,pb=point(a,-.12),point(b,-.12)
   for k in range(0,10,2):choice.append(line('Equal choice dash',[pa.lerp(pb,k/10),pa.lerp(pb,(k+1)/10)],.028/scale,dark,parent))
  route_mat=river
  hot=mat('Highlighted state',(.93,.2,.16));hot_edge=mat('Highlight edge',(.45,.05,.03));highlights=[]
  for st in states:
   if st['name'] in spec.get('highlight_states',[]) and st['name']!='Andhra Pradesh':
    grp=empty('Highlight '+st['name'],parent)
    for ring in st['rings']:
     ring=clip_polygon([list(p[:2]) for p in ring],bounds)
     if len(ring)<3:continue
     flat_fill('Highlighted '+st['name'],ring,point,hot,grp,-.11);line('Highlight border',[point(p,-.13) for p in ring+[ring[0]]],.014/scale,hot_edge,grp)
    highlights.append(grp)
    if st.get('hindi') and st['name'] not in seen:
     big=max(st['rings'],key=len);cx=sum(q[0] for q in big)/len(big);cy=sum(q[1] for q in big)/len(big);seen.add(st['name']);context.append((st['hindi'],point((cx,cy),-.18)))
  rivers=[];rd=_river_data()
  for name in spec.get('rivers',[]):
   info=rd.get(name)
   if not info:continue
   for seg in info['segments']:
    seg=[p for p in seg if xmin<=p[0]<=xmax and ymin<=p[1]<=ymax]
    if len(seg)<2:continue
    c=line('River '+name,[point(p,-.14) for p in seg],.03/scale,river,parent);c.data.bevel_factor_end=.004;rivers.append(c)
   src=info['source']
   if xmin<src[0]<xmax and ymin<src[1]<ymax:context.append((info['hindi'],point(src,-.18)))
  lat_lines=[]
  for ll in spec.get('latitude_lines',[]):
   la=float(ll['lat'])
   if not ymin<la<ymax:continue
   c=line('Latitude line',[point((xmin+.3,la),-.16),point((xmax-.3,la),-.16)],.022/scale,red,parent);c.data.bevel_factor_end=.004;lat_lines.append(c)
   if ll.get('label'):context.append((str(ll['label']),point((xmin+2.2,la+.6),-.18)))
 else:
  span=max(xmax-xmin,(ymax-ymin)*1.3);factor=3.5/span
  def point(p,y=-.08):return Vector(((p[0]-(xmin+xmax)/2)*factor,y,(p[1]-(ymin+ymax)/2)*factor+1.2))
  box('Map ocean backplate',(0,.1,1.2),(3.8,.12,3.4 if region!='world' else 2.2),sea,parent)
  if region=='gujarat':rings=json.loads((R/'dandi_map.json').read_text())['rings']
  else:
   data=json.loads((R/'world_land.json').read_text());rings=[]
   for feature in data['features']:
    geom=feature['geometry'];rings.extend([p[0] for p in geom['coordinates']] if geom['type']=='MultiPolygon' else [geom['coordinates'][0]])
  for ring in rings:
   ring=clip_polygon(ring,bounds)
   if len(ring)<3:continue
   flat_fill('Geographic land',ring,point,land,parent,-.035)
  context=[];route_mat=gold
 route=None;marker=None
 if spec.get('route'):
  points=[point(p,-.13) for p in spec['route']];route=line('Animated geographic route',points,.045 if regional else .024,route_mat,parent);route.data.bevel_factor_end=.01;marker=ell('Travel marker',points[0],(.075,.05,.075) if regional else (.055,.04,.055),white,parent)
 markers=[]
 for item in spec.get('markers',[]):
  p=point(item['at'],-.15);ell('Location marker',p,(.07,.05,.07) if regional else (.045,.035,.045),red if regional else gold,parent);markers.append((item['label'],p))
 out={'route':route,'marker':marker,'route_points':[point(p,-.13) for p in spec.get('route',[])],'map_markers':markers,'map_context':context}
 if regional:
  out.update(rivers=rivers,lat_lines=lat_lines,highlights=highlights)
  if (rivers or lat_lines or highlights) and not route:out['map_extras']=True
 return out

def animate_map(details,q,frame):
 for c in details.get('rivers',[]):
  c.data.bevel_factor_end=max(.004,ease(q/.75));c.data.keyframe_insert(data_path='bevel_factor_end',frame=frame)
 for c in details.get('lat_lines',[]):
  c.data.bevel_factor_end=max(.004,ease(q/.5));c.data.keyframe_insert(data_path='bevel_factor_end',frame=frame)
 for g in details.get('highlights',[]):
  # state rises out of the map and settles: the eye goes straight to the answer
  g.location.y=-.25*ease(q/.3)*(1-.3*ease((q-.3)/.3));g.keyframe_insert(data_path='location',frame=frame)
 route=details.get('route')
 if route:
  f=ease(q/.9);route.data.bevel_factor_end=max(.005,f);route.data.keyframe_insert(data_path='bevel_factor_end',frame=frame)
  pts=details['route_points'];z=f*(len(pts)-1);i=min(len(pts)-2,int(z));marker=details['marker'];marker.location=pts[i].lerp(pts[i+1],z-i);key(marker,'location',frame)

def ocean_asset(parent):
 wave,crests=coast(parent)
 return {'wave':wave,'crests':crests}
def animate_ocean(details,t,frame):
 wave=details['wave'];wave.value=.5+.5*math.sin(t*2);wave.keyframe_insert(data_path='value',frame=frame)
 for j,o in enumerate(details['crests']):o.location.y=-.75*((t*.45+j*.19)%1);key(o,'location',frame)

def world_coasts(parent):
 from mathutils.geometry import tessellate_polygon
 data=json.loads((R/'world_land.json').read_text())
 for f in data['features']:
  geom=f['geometry'];rings=[p[0] for p in geom['coordinates']] if geom['type']=='MultiPolygon' else [geom['coordinates'][0]]
  for ring in rings:
   pts=[]
   for lon,lat,*_ in ring:
    lon=math.radians(lon);lat=math.radians(lat);pts.append((1.06*math.cos(lat)*math.sin(lon),-1.06*math.cos(lat)*math.cos(lon),1.2+1.06*math.sin(lat)))
   if len(pts)>2:
    # Tessellate in geographic coordinates, then refine and project every vertex
    # onto the sphere: large triangles must not cut through the blue globe.
    flat=[];last=None
    for lon,lat,*_ in ring:
     if last is not None:
      while lon-last>180:lon-=360
      while lon-last< -180:lon+=360
     flat.append(Vector((lon,lat,0)));last=lon
    if (flat[0]-flat[-1]).length<.001:flat.pop()
    verts=[];faces=[]
    def triangle(a,b,c,depth=0):
     if depth<5 and max((a-b).length,(a-c).length,(b-c).length)>8:
      ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
      for x,y,z in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)):triangle(x,y,z,depth+1)
      return
     ids=[]
     for v in (a,b,c):
      lon=math.radians(v.x);lat=math.radians(v.y);ids.append(len(verts));verts.append((1.068*math.cos(lat)*math.sin(lon),-1.068*math.cos(lat)*math.cos(lon),1.2+1.068*math.sin(lat)))
     faces.append(tuple(ids))
    if len(flat)>2:
     for a,b,c in tessellate_polygon([flat]):triangle(*(flat[v] if isinstance(v,int) else v for v in (a,b,c)))
    if faces:
     mesh=bpy.data.meshes.new('Sourced filled continent');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Real geographic land surface',mesh);bpy.context.collection.objects.link(o);o.parent=parent;mesh.materials.append(land)
     for poly in mesh.polygons:poly.use_smooth=True
    line('Real continent coastline',pts,.008,green,parent)

def environment(setting,parent):
 if setting=='coast':return ocean_asset(parent)
 if setting=='laboratory':
  box('Laboratory bench',(0,2,.5),(5,1,.2),dark,parent)
  for x in [-1.6,1.6]:
   cyl('Lab tube',(x,2,.95),.13,.75,cyan,parent);cyl('Tube cap',(x,2,1.35),.15,.1,white,parent)
 elif setting=='institution':
  for x in [-2,-1,0,1,2]:cyl('Institution backdrop column',(x,1.7,1),.12,2,white,parent)
  box('Institution pediment',(0,1.7,2.05),(5.2,.5,.2),gold,parent)
 elif setting=='village':
  box('Village house',(-2,2.5,.65),(1.5,1,1.3),sand,parent);roof=cone('Village roof',(-2,2.5,1.65),1.05,.7,brown,parent);roof.scale.y=.7
  cyl('Tree trunk',(2,2.5,.7),.1,1.4,brown,parent);ell('Tree foliage',(2,2.5,1.6),(.7,.4,.8),green,parent)
 elif setting=='space':
  for j in range(28):sphere('Background star',(-4+(j*1.37)%8,3, .3+(j*1.71)%5),.018,white,parent)
 return {}



def terrain_asset(parent):
 """Connected mountain relief: multiple ridges, foothills and altitude snow."""
 verts=[];faces=[];steps=36
 for j in range(steps+1):
  y=-1.15+2.3*j/steps
  for i in range(steps+1):
   x=-1.4+2.8*i/steps
   envelope=max(0,1-(x/1.5)**4)*max(0,1-(y/1.3)**4)
   h=.12+envelope*(.55+.48*math.sin(3*x+1.6*y)**2+.55*math.exp(-((x-.25)**2+(y+.15)**2)*2))
   verts.append((x,y,h))
 for j in range(steps):
  for i in range(steps):
   a=j*(steps+1)+i;faces.append((a,a+1,a+steps+2,a+steps+1))
 mesh=bpy.data.meshes.new('Connected mountain relief');mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new('Mountain ridges and foothills',mesh);bpy.context.collection.objects.link(o);o.parent=parent
 for material in (brown,green,white):mesh.materials.append(material)
 for poly in mesh.polygons:
  z=sum(verts[i][2] for i in poly.vertices)/len(poly.vertices);poly.material_index=2 if z>1.25 else 1 if z<.55 else 0
 return o

def rock_layers(parent):
 """Continuous cross-section layers with shape-key shortening and buckling."""
 result=[]
 for layer in range(5):
  verts=[];faces=[];n=64
  for i in range(n+1):
   x=-1.5+3*i/n
   for y,z in ((-.3,0),(.3,0),(.3,.09),(-.3,.09)):verts.append((x,y,.18+layer*.15+z))
  for i in range(n):
   a=4*i
   for j in range(4):faces.append((a+j,a+(j+1)%4,a+4+(j+1)%4,a+4+j))
  faces.extend([(3,2,1,0),(4*n,4*n+1,4*n+2,4*n+3)])
  mesh=bpy.data.meshes.new('Continuous rock stratum');mesh.from_pydata(verts,[],faces);mesh.update()
  o=bpy.data.objects.new('Folding rock layer '+str(layer),mesh);bpy.context.collection.objects.link(o);o.parent=parent;mesh.materials.append(sand if layer%2 else brown)
  o.shape_key_add(name='Uncompressed');fold=o.shape_key_add(name='Shortened folded crust')
  for v in fold.data:
   x=v.co.x;v.co.x=x*.68;v.co.z+=.55*math.exp(-(x/.9)**2)+.18*math.sin(x*6+layer*.12)
  result.append(fold)
 return {'fold_keys':result}

def animate_folds(details,q,frame):
 for fold in details.get('fold_keys',[]):fold.value=ease(q);fold.keyframe_insert(data_path='value',frame=frame)

# ---------------- Physics teaching assets (Nov 2026) ----------------
# Most-asked physics chapters in the PYQ bank: mechanics, electricity, light, gravitation, magnetism, sound.
# Every asset returns details['anim'](q,frame) that moves the part which teaches the idea (rays, current, swing...).
PHYSICS_KINDS=('lens','mirror','prism','circuit','pendulum','spring','lever','wave')
RAY=None
def _ray_mat():
 global RAY
 if RAY is None:RAY=mat('Light ray',(1.0,.86,.2))
 return RAY
def _grow(curve,f,frame):
 curve.data.bevel_factor_end=max(.004,min(1,f));curve.data.keyframe_insert(data_path='bevel_factor_end',frame=frame)
def _solid2d(name,poly,depth,m,parent):
 """Flat polygon in the x-z plane extruded towards the camera axis (y)."""
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='2D';c.fill_mode='BOTH';c.extrude=depth;sp=c.splines.new('POLY');sp.points.add(len(poly)-1)
 for v,(x,z) in zip(sp.points,poly):v.co=(x,z,0,1)
 sp.use_cyclic_u=True;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=parent;o.rotation_euler.x=math.pi/2;c.materials.append(m);return o
def _rays(parent,paths,m,r=.035):
 out=[]
 for pts in paths:
  c=line('Light ray path',[(x,-.3,z) for x,z in pts],r,m,parent);c.data.bevel_factor_end=.004;out.append(c)
 return out
def _seq(curves,q,frame,start=0,end=.8):
 n=max(1,len(curves))
 for i,c in enumerate(curves):
  a=start+(end-start)*i/n*.35;_grow(c,ease((q-a)/max(.05,end-a)),frame)

def lens_asset(parent,spec):
 concave=spec.get('variant')=='concave';glass=mat('Lens glass',(.55,.9,1.0));cz=1.4;h=.9
 prof=[]
 for i in range(17):
  z=-h+2*h*i/16;t=1-(z/h)**2
  prof.append(((.06+.24*t) if not concave else (.3-.22*t),z))
 poly=[(x,cz+z) for x,z in prof]+[(-x,cz+z) for x,z in reversed(prof)]
 _solid2d('Lens',poly,.18,glass,parent);line('Principal axis',[(-2,-.25,cz),(2,-.25,cz)],.012,white,parent)
 F=1.05;paths=[]
 for hz in (-.55,0,.55):
  hit=(0,cz+hz)
  if concave:
   dx,dz=hit[0]+F,hit[1]-cz;k=(1.9-hit[0])/dx;end=(1.9,hit[1]+dz*k)
  else:
   dx,dz=F-hit[0],cz-hit[1];k=(1.9-hit[0])/dx;end=(1.9,hit[1]+dz*k)
  paths.append([(-1.9,hit[1]),hit,end])
 rays=_rays(parent,paths,_ray_mat());fx=-F if concave else F
 focus=sphere('Focus F',(fx,-.35,cz),.09,red,parent);focus.scale=(0,0,0)
 def anim(q,frame):
  _seq(rays,q,frame);s=ease((q-.55)/.2);focus.scale=(s,s,s);key(focus,'scale',frame)
 return {'anim':anim,'physics':True}

def mirror_asset(parent,spec):
 convex=spec.get('variant')=='convex';cz=1.4;Rr=2.2;F=Rr/2;vx=.7
 cx=vx+Rr if convex else vx-Rr;sgn=-1 if convex else 1
 arc=[(cx+sgn*Rr*math.cos(a),cz+Rr*math.sin(a)) for a in [(-.42+.84*i/24) for i in range(25)]]
 line('Mirror silver',[(x,-.25,z) for x,z in arc],.05,mat('Mirror silver',(.85,.9,.95)),parent)
 line('Mirror back',[(x+.09,-.2,z) for x,z in arc],.05,dark,parent);line('Principal axis',[(-2,-.25,cz),(1.6,-.25,cz)],.012,white,parent)
 fx=vx+F if convex else vx-F;paths=[]
 for hz in (-.6,.6):
  zz=cz+hz;hx=cx+sgn*math.sqrt(max(0,Rr*Rr-hz*hz))
  if convex:dx,dz=hx-fx,zz-cz
  else:dx,dz=fx-hx,cz-zz
  k=(-1.9-hx)/dx;paths.append([(-1.9,zz),(hx,zz),(-1.9,zz+dz*k)])
 rays=_rays(parent,paths,_ray_mat());focus=sphere('Focus F',(fx,-.35,cz),.09,red,parent);focus.scale=(0,0,0)
 def anim(q,frame):
  _seq(rays,q,frame);s=ease((q-.55)/.2);focus.scale=(s,s,s);key(focus,'scale',frame)
 return {'anim':anim,'physics':True}

SPECTRUM=[('V',(.55,.2,.95)),('I',(.3,.25,.95)),('B',(.15,.55,1)),('G',(.15,.85,.3)),('Y',(1,.92,.15)),('O',(1,.55,.1)),('R',(.95,.12,.1))]
def prism_asset(parent,spec):
 glass=mat('Prism glass',(.62,.92,1.0));tri=[(-.75,.55),(.75,.55),(0,1.85)]
 _solid2d('Prism',tri,.4,glass,parent)
 a=(-.4,1.2);b=(.38,1.18)
 white_in=line('White light',[(-1.9,-.3,.95),(a[0],-.3,a[1])],.05,white,parent);inner=line('Light inside prism',[(a[0],-.3,a[1]),(b[0],-.3,b[1])],.035,white,parent)
 for c in (white_in,inner):c.data.bevel_factor_end=.004
 colors=[]
 for i,(n,col) in enumerate(SPECTRUM):
  c=line('Spectrum '+n,[(b[0],-.3,b[1]),(1.9,-.3,.35+.13*i)],.03,mat('Spectrum '+n,col),parent);c.data.bevel_factor_end=.004;colors.append(c)
 def anim(q,frame):
  _grow(white_in,ease(q/.25),frame);_grow(inner,ease((q-.25)/.15),frame)
  for c in colors:_grow(c,ease((q-.4)/.3),frame)
 return {'anim':anim,'physics':True}

def circuit_asset(parent,spec):
 wire=mat('Copper wire',(.85,.45,.15));x0,x1,z0,z1=-1.4,1.4,.45,2.25
 loop=[(x0,z0),(x1,z0),(x1,z1),(x0,z1),(x0,z0)]
 line('Circuit wire',[(x,0,z) for x,z in loop],.035,wire,parent)
 bat=box('Battery',(x0,0,(z0+z1)/2),(.32,.32,.7),mat('Battery body',(.12,.12,.14)),parent);box('Battery + cap',(x0,0,(z0+z1)/2+.42),(.14,.14,.12),gold,parent)
 glow=mat('Bulb glow',(.35,.35,.3));bulb=sphere('Bulb glass',(0,0,z1+.32),.3,glow,parent);cyl('Bulb base',(0,0,z1+.02),.13,.18,white,parent)
 halo=sphere('Bulb light',(0,.15,z1+.32),.5,mat('Light halo',(1,.95,.45)),parent);halo.scale=(0,0,0)
 pivot=empty('Switch pivot',parent);pivot.location=(x1,0,(z0+z1)/2-.3);box('Switch lever',(0,0,.3),(.08,.08,.62),red,pivot);pivot.rotation_euler.y=.7
 per=[0,2.8,1.8,2.8,1.8];total=sum(per);dots=[sphere('Electron',(x0,-.12,z0),.07,cyan,parent) for _ in range(10)]
 def at(u):
  u=(u%1)*total;s=0
  for i in range(4):
   seg=per[i+1]
   if u<=s+seg:t=(u-s)/seg;(ax,az),(bx,bz)=loop[i],loop[i+1];return (ax+(bx-ax)*t,-.12,az+(bz-az)*t)
   s+=seg
  return (x0,-.12,z0)
 def anim(q,frame):
  closed=ease(q/.2);pivot.rotation_euler.y=.7*(1-closed);key(pivot,'rotation_euler',frame)
  on=q>.2;glow.diffuse_color=((1,.95,.5,1) if on else (.35,.35,.3,1));glow.keyframe_insert(data_path='diffuse_color',frame=frame)
  s=.9+.1*math.sin(q*math.tau*3) if on else 0;halo.scale=(s,s*.2,s);key(halo,'scale',frame)
  for i,d in enumerate(dots):
   d.location=at(i/len(dots)+(max(0,q-.2))*1.2) if on else (x0,-.12,z0+i*.18*(z1-z0)/1.8);key(d,'location',frame)
 return {'anim':anim,'physics':True}

def pendulum_asset(parent,spec):
 box('Support beam',(0,0,2.65),(1.6,.3,.15),dark,parent);pivot=empty('Pendulum pivot',parent);pivot.location=(0,0,2.55)
 line('Pendulum string',[(0,0,0),(0,0,-1.75)],.018,white,pivot);sphere('Pendulum bob',(0,0,-1.9),.24,gold,pivot)
 arc=[(1.9*math.sin(a),-.25,2.55-1.9*math.cos(a)) for a in [(-.45+.9*i/20) for i in range(21)]]
 trail=line('Swing path',arc,.012,mat('Swing path',(.5,.75,.9)),parent)
 def anim(q,frame):pivot.rotation_euler.y=.45*math.cos(q*math.tau*2);key(pivot,'rotation_euler',frame)
 return {'anim':anim,'physics':True}

def spring_asset(parent,spec):
 box('Base',(0,0,.1),(1.4,.8,.2),dark,parent);coil=empty('Spring coil',parent);coil.location=(0,0,.2)
 pts=[(.32*math.cos(a),.32*math.sin(a),a/(math.tau*8)*1.5) for a in [i*math.tau/24 for i in range(24*8+1)]]
 line('Spring wire',pts,.035,mat('Spring steel',(.75,.78,.82)),coil);block=box('Mass block',(0,0,1.9),(.9,.9,.6),spec.get('_m') or gold,parent)
 def anim(q,frame):
  c=1-.38*(.5-.5*math.cos(q*math.tau*2));coil.scale=(1,1,c);key(coil,'scale',frame);block.location.z=.2+1.5*c+.3;key(block,'location',frame)
 return {'anim':anim,'physics':True}

def lever_asset(parent,spec):
 cone('Fulcrum',(0,0,.45),.42,.8,dark,parent)
 beam=empty('Lever beam',parent);beam.location=(0,0,.88);box('Lever bar',(0,0,0),(3.4,.3,.1),gold,beam)
 box('Effort weight',(1.45,0,.28),(.35,.35,.45),cyan,beam);box('Load',(-1.0,0,.33),(.6,.6,.55),red,beam)
 def anim(q,frame):beam.rotation_euler.y=-.22*math.sin(q*math.tau*1.5);key(beam,'rotation_euler',frame)
 return {'anim':anim,'physics':True}

def wave_asset(parent,spec):
 n=17;balls=[sphere('Wave particle',(-1.8+3.6*i/(n-1),-.1,1.4),.11,mat('Wave particle %d'%(i%3),[(.2,.8,1),(.4,.6,1),(.3,.95,.8)][i%3]),parent) for i in range(n)]
 line('Rest line',[(-1.9,-.3,1.4),(1.9,-.3,1.4)],.01,white,parent)
 cycles=2 if spec.get('variant')=='high' else 1
 def anim(q,frame):
  for i,b in enumerate(balls):
   x=-1.8+3.6*i/(n-1);b.location=(x,-.1,1.4+.55*math.sin(x*math.pi*cycles-q*math.tau*2));key(b,'location',frame)
 return {'anim':anim,'physics':True}

PHYSICS_BUILDERS={'lens':lens_asset,'mirror':mirror_asset,'prism':prism_asset,'circuit':circuit_asset,'pendulum':pendulum_asset,'spring':spring_asset,'lever':lever_asset,'wave':wave_asset}
