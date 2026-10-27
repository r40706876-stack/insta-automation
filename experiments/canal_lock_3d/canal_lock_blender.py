"""Entirely modelled and animated single canal-lock teaching scene. No photographs or billboards."""
import bpy,math,os,json,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('CANAL_ROOT','experiments/canal_lock_3d'));R.mkdir(parents=True,exist_ok=True)
meta=json.loads((R/'audio.json').read_text()) if (R/'audio.json').exists() else {'seconds':[5,6,7,6,7,5]}
ds=meta['seconds'];starts=[sum(ds[:i]) for i in range(6)];total=sum(ds);FPS=24;N=math.ceil(total*FPS)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=FPS
sh=s.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.4;sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.curvature_ridge_factor=1.4;sh.curvature_valley_factor=1.1;sh.show_specular_highlight=True;sh.show_object_outline=True;sh.object_outline_color=(.025,.055,.075);sh.background_type='WORLD';s.world.color=(.018,.039,.063)
s.display.render_aa='8';s.view_settings.view_transform='Standard';s.render.image_settings.color_mode='RGB'
def mat(name,col):m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);return m
sand=mat('Pale engineered concrete',(.69,.72,.68));stone=mat('Dark wall edge',(.25,.36,.4));water=mat('Visible water volume',(.025,.39,.58));highwater=mat('Upper reservoir',(.04,.49,.64));navy=mat('Ship steel',(.035,.1,.17));white=mat('Ship white',(.92,.95,.93));gold=mat('Warm cargo',(.97,.58,.1));orange=mat('Orange cargo',(.94,.29,.09));blue=mat('Teal cargo',(.05,.62,.65));gateM=mat('Mitre gate panels',(.18,.28,.31));brass=mat('Gate edge',(.74,.55,.19));red=mat('Valve handle',(.92,.2,.15));flowM=mat('Flow tracer',(.2,.91,1));floorM=mat('Navy stage',(.035,.075,.1))
def box(name,loc,size,material,bevel=.03,parent=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material)
 if bevel:
  m=o.modifiers.new('Edge bevel','BEVEL');m.width=bevel;m.segments=2;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 if parent:o.parent=parent
 return o
def sphere(name,loc,r,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=r,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(material)
 for f in o.data.polygons:f.use_smooth=True
 return o
def line(name,pts,r,material,parent=None):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;p=c.splines.new('POLY');p.points.add(len(pts)-1)
 for v,co in zip(p.points,pts):v.co=(*co,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 if parent:o.parent=parent
 return o
box('Presentation plinth',(0,0,-.25),(6.2,15,.4),floorM,.16)
# Low approach, chamber and high exit, separated by genuine opening gate meshes.
box('Low basin floor',(0,-4.5,0),(2.45,5,.25),sand)
box('Lock chamber floor',(0,0,0),(2.45,4,.25),sand)
box('Upper basin floor',(0,4.5,0),(2.45,5,.25),sand)
low=box('Low approach water',(0,-4.5,.55),(2.15,5,1),water,0)
upper=box('Upper reservoir water',(0,4.5,1.35),(2.15,5,2.6),highwater,0)
chamber=box('Rising chamber water',(0,0,.55),(2.15,4,1),water,0)
for side in (-1,1):
 # Near wall is cut down so the water surface and boat movement remain visible.
 height=3.2 if side==-1 else .32
 box('Far lock wall' if side==-1 else 'Cutaway near lock wall',(side*1.3,0,height/2),(.32,4.4,height),sand)
 for y in (-4.5,4.5):box('Reservoir bank',(side*1.3,y,height/2),(.32,4.8,height),sand)
 # Repeating coping blocks, bollards and railings make the model spatially readable.
 for y in [j*.8-6.4 for j in range(17)]:
  if side==-1:
   box('Coping',(side*1.3,y,3.24),(.4,.72,.12),white,.02)
for z in (1,1.4,1.8,2.2,2.6):line('Fixed level mark',[(-1.105,-.65,z),(-1.105,.65,z)],.025,gold)
# Detailed small container vessel, all parts parented to a single moving root.
bpy.ops.object.empty_add();ship=bpy.context.object;ship.name='Ship root - moves with water level'
verts=[(-.38,-1.15,-.25),(.38,-1.15,-.25),(.42,.82,-.25),(0,1.3,-.25),(-.42,.82,-.25),(-.45,-1.2,.28),(.45,-1.2,.28),(.48,.82,.28),(0,1.48,.28),(-.48,.82,.28)]
faces=[(0,1,2,3,4),(5,9,8,7,6),(0,5,6,1),(1,6,7,2),(2,7,8,3),(3,8,9,4),(4,9,5,0)]
m=bpy.data.meshes.new('Hull geometry');m.from_pydata(verts,[],faces);m.update();h=bpy.data.objects.new('Boat hull',m);bpy.context.collection.objects.link(h);h.data.materials.append(navy);h.parent=ship
box('Deck',(0,0,.29),(.82,2.3,.12),white,.02,ship)
for i in (-1,1):
 for j in range(3):
  for k in range(2):
   x=i*.19;y=-.15+j*.42;z=.49+k*.28
   box('Cargo container',(x,y,z),(.35,.38,.25),[gold,orange,blue][(j+k+(i==1))%3],.018,ship)
   for stripe in (-.08,.08):line('Container rib',[(x-.16,y+stripe,z-.1),(x+.16,y+stripe,z-.1)],.008,white,ship)
box('Bridge',(0,-.82,.61),(.69,.51,.52),white,.05,ship);box('Bridge windows',(0,-1.083,.72),(.55,.012,.16),blue,.005,ship)
box('Bridge roof',(0,-.82,.91),(.8,.61,.08),navy,.01,ship);box('Funnel',(.23,-.75,1.09),(.15,.17,.32),orange,.02,ship)
line('Antenna',[(-.2,-.85,.94),(-.2,-.85,1.45)],.017,white,ship)
for x in (-.44,.44):line('Deck rail',[(x,-1.05,.5),(x,1.05,.5)],.017,white,ship)
# Hinged leaves rotate on their own axes; they are not sliding images.
gates=[]
for gy in (-2.04,2.04):
 pair=[]
 for side in (-1,1):
  bpy.ops.object.empty_add(location=(side*1.08,gy,0));pivot=bpy.context.object;pivot.name=('Low' if gy<0 else 'High')+' gate hinge '+str(side)
  leaf=box('Gate leaf',(-side*.54,0,1.65),(1.08,.12,3.3),gateM,.025,pivot)
  for z in (.4,1.1,1.8,2.5,3.1):box('Gate cross member',(-side*.54,-.08,z),(1.04,.08,.07),brass,.01,pivot)
  line('Gate diagonal brace',[(-side*.1,-.14,.3),(-side*1,-.14,2.9)],.035,stone,pivot)
  pair.append(pivot)
 gates.append(pair)
# Cutaway supply culvert on the visible side, carrying gravity-fed water from the high reservoir.
path=[(1.95,4,1.55),(1.95,3.15,.35),(1.95,0,.35),(1.04,0,.35)]
for offset in (-.11,.11):line('Cutaway culvert edge',[(x+offset,y,z) for x,y,z in path],.035,stone)
for y in [j*.28 for j in range(12)]:
 line('Culvert hoop',[(1.95+.13*math.cos(a),y,.35+.13*math.sin(a)) for a in [j*math.tau/16 for j in range(17)]],.015,brass)
bpy.ops.object.empty_add(location=(1.95,2.25,.65));valve=bpy.context.object;valve.name='Rotating fill valve'
line('Valve wheel',[(.27*math.cos(a),0,.27*math.sin(a)) for a in [j*math.tau/24 for j in range(25)]],.035,red,valve)
for a in (0,math.pi/2):line('Valve spoke',[(.24*math.cos(a),0,.24*math.sin(a)),(-.24*math.cos(a),0,-.24*math.sin(a))],.025,red,valve)
tracers=[sphere('Moving flow tracer '+str(i),path[0],.065,flowM) for i in range(12)]
# Water ripples are geometric strips, all animated with their own water surface.
ripples=[]
for basin in range(3):
 for j in range(6):
  cy=(-4.5,0,4.5)[basin]+(j-2.5)*.42
  z=(1,1,2.6)[basin]+.012
  o=line('Water surface ripple',[(-.7,cy,z),(-.25,cy+.04,z),(.15,cy-.03,z),(.65,cy,z)],.012,flowM);ripples.append((basin,j,o,z))
# Fixed camera reference during the lift prevents camera movement from disguising the rise.
bpy.ops.object.camera_add(location=(8,-12,10));cam=bpy.context.object;s.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=15.8
cam.rotation_euler=(Vector((0,.1,1.3))-cam.location).to_track_quat('-Z','Y').to_euler()
def ease(q):q=max(0,min(1,q));return q*q*(3-2*q)
def fraction(t,a,b):return ease((t-a)/max(.001,b-a))
def pathpoint(q):
 lengths=[0]
 for a,b in zip(path,path[1:]):lengths.append(lengths[-1]+(Vector(b)-Vector(a)).length)
 v=q*lengths[-1]
 for i in range(len(path)-1):
  if v<=lengths[i+1]:return Vector(path[i]).lerp(Vector(path[i+1]),(v-lengths[i])/(lengths[i+1]-lengths[i]))
 return Vector(path[-1])
track=[]
for frame in range(1,N+1):
 t=(frame-1)/FPS;s.frame_set(frame);k=max(i for i,v in enumerate(starts) if v<=t)
 close=fraction(t,starts[2],starts[2]+1.65)
 fill_start=starts[2]+2.05;fill_end=starts[4]-.35;fill=fraction(t,fill_start,fill_end)
 level=1+1.6*fill
 high_open=fraction(t,starts[4]+.55,starts[4]+2.35)
 if t<starts[1]:sy=-4.9+.7*fraction(t,0,starts[1])
 elif t<starts[2]:sy=-4.2+4.2*fraction(t,starts[1],starts[2]-.3)
 else:sy=5.6*fraction(t,starts[4]+2.5,total-.5)
 ship.location=(0,sy,(1 if sy<-2 else 2.6 if sy>2 else level));ship.keyframe_insert(data_path='location',frame=frame)
 chamber.scale.z=level;chamber.location.z=.05+level/2;chamber.keyframe_insert(data_path='scale',frame=frame);chamber.keyframe_insert(data_path='location',frame=frame)
 for pair,q in zip(gates,(1-close,high_open)):
  for side,o in zip((-1,1),pair):o.rotation_euler.z=-side*q*math.pi/2;o.keyframe_insert(data_path='rotation_euler',frame=frame)
 valve.rotation_euler.y=fraction(t,starts[2]+1.65,fill_start)*math.pi/2;valve.keyframe_insert(data_path='rotation_euler',frame=frame)
 flowing=fill_start<=t<fill_end
 for i,o in enumerate(tracers):
  o.location=pathpoint((t*.29+i/12)%1);o.scale=(1,1,1) if flowing else (0,0,0);o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='scale',frame=frame)
 for basin,j,o,z in ripples:
  o.location.x=.08*math.sin(t*1.1+j);o.location.y=.035*math.sin(t*1.4+j);o.location.z=level-1 if basin==1 else 0;o.keyframe_insert(data_path='location',frame=frame)
 # Small camera establishing move; it becomes fixed during the changing water level.
 angle=.16*fraction(t,0,starts[2]);cam.location=(8-2*angle,-12,10);cam.rotation_euler=(Vector((0,.1,1.3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)
 if flowing:assert close>=.999 and high_open<.001,'Never fill against an open end gate'
 if high_open>.001:assert abs(level-2.6)<.01,'Do not open gate with unequal levels'
 if sy>1.0:assert high_open>.999,'Do not drive a ship through a closed gate'
 pins={}
 for name,co in {'ship':ship.location+Vector((0,0,.8)),'valve':valve.location,'water':Vector((1,0,level)),'low':Vector((0,-4.5,1)),'high':Vector((0,4.5,2.6))}.items():
  q=world_to_camera_view(s,cam,co);pins[name]=[q.x*720,(1-q.y)*1280]
 track.append({'t':t,'scene':k,'level':level,'ship_y':sy,'low_gate_closed':close,'high_gate_open':high_open,'pins':pins})
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for p in fc.keyframe_points:p.interpolation='LINEAR'
s.frame_start=1;s.frame_end=N
(R/'motion.json').write_text(json.dumps(track));(R/'scene_checks.json').write_text(json.dumps({'frames':N,'fps':FPS,'whole_scene_3d':True,'photo_assets':0,'gate_pressure_interlock_verified':True,'ship_clearance_verified':True,'lift_max':2.6,'level_note':'Schematic model units, not metres or a complete Panama Canal replica'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'canal_lock.blend'))
if os.environ.get('CANAL_STILL')=='1':
 s.frame_set(int(os.environ.get('CANAL_PROOF_FRAME',round((starts[3]+ds[3]*.5)*FPS))));s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'proof.png');bpy.ops.render.render(write_still=True)
else:
 s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(R/'silent_3d.mp4');bpy.ops.render.render(animation=True)
print('CANAL_FULL_3D_RENDER_DONE',N)
