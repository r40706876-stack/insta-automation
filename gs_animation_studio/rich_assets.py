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

def map_asset(parent,spec):
 region=spec.get('map_region','world');bounds=MAP_BOUNDS[region];xmin,ymin,xmax,ymax=bounds
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
  c=bpy.data.curves.new('Source-based coast outline','CURVE');c.dimensions='2D';c.fill_mode='BOTH';sp=c.splines.new('POLY');sp.points.add(len(ring)-1)
  for v,p in zip(sp.points,ring):p=point(p);v.co=(p.x,p.z,0,1)
  sp.use_cyclic_u=True;o=bpy.data.objects.new('Geographic land',c);bpy.context.collection.objects.link(o);o.parent=parent;o.rotation_euler.x=math.pi/2;o.location.y=-.035;c.materials.append(land)
 route=None;marker=None
 if spec.get('route'):
  points=[point(p,-.13) for p in spec['route']];route=line('Animated geographic route',points,.024,gold,parent);route.data.bevel_factor_end=.01;marker=ell('Travel marker',points[0],(.055,.04,.055),white,parent)
 markers=[]
 for item in spec.get('markers',[]):
  p=point(item['at'],-.15);ell('Location marker',p,(.045,.035,.045),gold,parent);markers.append((item['label'],p))
 return {'route':route,'marker':marker,'route_points':[point(p,-.13) for p in spec.get('route',[])],'map_markers':markers}

def animate_map(details,q,frame):
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
     for a,b,c in tessellate_polygon([flat]):triangle(a,b,c)
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
