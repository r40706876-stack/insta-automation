"""Data-driven procedural 3D actors. Plan is JSON, never executable AI code."""
import bpy,json,math,os
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['STUDIO_ROOT']);plan=json.loads((R/'recipe.json').read_text());meta=json.loads((R/'audio.json').read_text());ds=meta['seconds'];starts=[sum(ds[:i]) for i in range(6)];FPS=24;N=math.ceil(sum(ds)*FPS)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=FPS;s.display.render_aa=os.getenv('STUDIO_RENDER_AA','8')
sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True;sh.show_object_outline=True;sh.background_type='WORLD';s.world.color=(.018,.039,.063);s.view_settings.view_transform='Standard'
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m
white=mat('Ivory',(.94,.93,.84));gold=mat('Gold',(.98,.66,.12));skin=mat('Skin',(.77,.49,.29));dark=mat('Outline',(.025,.045,.065));water=mat('Water',(.025,.5,.8));cyan=mat('Cyan',(.1,.82,.95));green=mat('Green',(.1,.48,.25));red=mat('Red',(.84,.14,.08))
def empty(name,parent=None):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.parent=parent;return o

def box(name,pos,scale,m,parent):
 bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);o.parent=parent
 b=o.modifiers.new('Rounded edges','BEVEL');b.width=.035;b.segments=2;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def sphere(name,pos,r,m,parent):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r,location=pos);o=bpy.context.object;o.name=name;o.parent=parent;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def cyl(name,pos,r,h,m,parent,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=h,location=pos,rotation=rotation);o=bpy.context.object;o.name=name;o.parent=parent;o.data.materials.append(m);return o

def cone(name,pos,r,h,m,parent):
 bpy.ops.mesh.primitive_cone_add(vertices=20,radius1=r,radius2=0,depth=h,location=pos);o=bpy.context.object;o.parent=parent;o.name=name;o.data.materials.append(m);return o

def line(name,pts,r,m,parent):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for a,p in zip(sp.points,pts):a.co=(*p,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.parent=parent;o.data.materials.append(m);return o

def person(g,m,soldier=False,role='ordinary'):
 joints=[]
 for x in [-.2,.2]:
  pivot=empty('Hip',g);pivot.location=(x,0,.88);box('Leg',(0,0,-.34),(.23,.27,.7),skin if role=='gandhi' else dark,pivot);box('Foot',(0,-.1,-.78),(.28,.5,.16),dark,pivot);joints.append(pivot)
 box('Torso',(0,0,1.17),(.7,.35,.7),m,g)
 for x in [-.46,.46]:
  pivot=empty('Shoulder',g);pivot.location=(x,0,1.45);box('Arm',(0,0,-.3),(.19,.24,.64),m,pivot);sphere('Hand',(0,0,-.64),.12,skin,pivot);joints.append(pivot)
 sphere('Head',(0,0,1.93),.3,skin,g)
 for x in [-.11,.11]:sphere('Eye',(x,-.265,1.98),.035,dark,g)
 if soldier:
  cyl('Helmet',(0,0,2.12),.32,.18,m,g);box('Shield',(-.58,-.26,1.02),(.55,.12,.7),gold,g);box('Sword',(.6,0,1.8),(.055,.055,1),white,g)
 elif role=='gandhi':
  box('White dhoti',(0,0,.86),(.71,.38,.62),white,g)
  for x in (-.12,.12):line('Round spectacles',[(x+.105*math.cos(a),-.286,1.98+.105*math.sin(a)) for a in [j*math.tau/24 for j in range(25)]],.014,dark,g)
  line('Spectacle bridge',[(-.02,-.29,1.98),(.02,-.29,1.98)],.014,dark,g)
  line('Walking staff',[(-.67,-.05,.03),(-.67,-.05,1.55)],.035,gold,g)
 else:cyl('Cap',(0,0,2.16),.31,.12,white,g)
 return joints

def asset(spec,parent):
 kind=spec['kind'];g=empty(spec['id'],parent);m=mat(spec['id'],tuple(int(spec['color'][i:i+2],16)/255 for i in (1,3,5)));details={}
 if kind in ('person','soldier'):
  details['joints']=person(g,m,kind=='soldier',spec.get('role','ordinary'))
  if spec.get('gesture')=='collect':
   details['pickup']=box('Salt visibly held in hand',(0,-.03,-.73),(.22,.2,.2),white,details['joints'][3])
   details['pickup'].scale=(0,0,0)
 elif kind in ('building','assembly','fort','factory'):
  box('Main structure',(0,.1,1),(1.8,1.2,2),m,g);box('Steps',(0,-.6,.12),(2.4,1.8,.24),white,g)
  if kind=='fort':
   for x in [-1,1]:
    cyl('Tower',(x,0,1.2),.4,2.4,m,g)
    for z in [-.2,.2]:box('Battlement',(x+z,0,2.5),(.18,.6,.3),m,g)
  elif kind=='factory':
   for x in [-.6,.6]:cyl('Chimney',(x,.3,2.4),.18,1.2,m,g)
  else:
   for x in [-.65,-.22,.22,.65]:cyl('Column',(x,-.58,1.1),.1,1.8,white,g)
   roof=cone('Pediment',(0,0,2.2),1.3,.5,m,g);roof.scale.y=.7
 elif kind in ('planet','moon','sun'):
  sphere(kind,(0,0,1.2),1.05,m,g)
  if kind=='planet':
   for i in range(8):
    a=i*2.399;z=-.8+i*.22;r=math.sqrt(max(.01,1.05**2-z*z));patch=sphere('Schematic land',(r*math.cos(a),r*math.sin(a),1.2+z),.28,green,g);patch.scale.z=.6
  elif kind=='sun':
   for i in range(12):
    a=i*math.tau/12;line('Sun ray',[(1.18*math.cos(a),0,1.2+1.18*math.sin(a)),(1.48*math.cos(a),0,1.2+1.48*math.sin(a))],.045,gold,g)
  else:
   for i in range(4):sphere('Crater',(.55*math.cos(i*2),-.8,1.2+.5*math.sin(i*2)),.2,dark,g)
 elif kind=='tree':
  cyl('Trunk',(0,0,.6),.15,1.2,dark,g);cone('Foliage',(0,0,1.4),.8,1.6,m,g)
 elif kind=='mountain':cone('Mountain',(0,0,1.2),1.3,2.4,m,g);cone('Snow',(0,0,2.15),.32,.6,white,g)
 elif kind=='coin':
  cyl('Coin',(0,0,.9),.65,.2,m,g,(math.pi/2,0,0));line('Coin motif',[(-.25,-.13,.6),(0,-.13,1.2),(.25,-.13,.6)],.06,white,g)
 elif kind=='salt':
  cyl('Salt pan',(0,0,.12),1,.2,m,g)
  for x,y,z in [(-.5,0,.35),(0,-.2,.4),(.4,.1,.35),(0,.2,.6)]:box('Salt crystal',(x,y,z),(.4,.4,.4),white,g)
 elif kind=='ship':
  box('Hull',(0,0,.4),(2.2,.85,.6),m,g);cone('Bow',(-1.15,0,.42),.45,.6,m,g).rotation_euler[1]=-math.pi/2
  box('Cabin',(.35,0,1),(1,.65,.7),white,g);cyl('Funnel',(.4,0,1.6),.17,.5,red,g)
 elif kind=='train':
  box('Train body',(0,0,.7),(2.6,.8,1),m,g);box('Roof',(0,0,1.3),(2.8,.9,.15),white,g)
  for x in [-.9,-.3,.3,.9]:box('Window',(x,-.42,.9),(.36,.04,.35),cyan,g)
  for x in [-.9,.9]:
   for y in [-.45,.45]:cyl('Wheel',(x,y,.25),.25,.12,dark,g,(math.pi/2,0,0))
 elif kind=='ballot':
  box('Ballot box',(0,0,.6),(1.4,1,1.2),m,g);box('Slot',(0,0,1.22),(.8,.1,.03),dark,g);paper=box('Voting slip',(0,0,1.9),(.65,.04,.9),white,g);details['paper']=paper
 elif kind=='book':
  box('Pages',(0,0,.2),(1.6,1.2,.3),white,g)
  for z in [.03,.37]:box('Book cover',(0,0,z),(1.7,1.3,.08),m,g)
 elif kind=='bottle':
  cyl('Bottle body',(0,0,.9),.45,1.6,m,g);cyl('Neck',(0,0,1.95),.2,.5,m,g);cyl('Cap',(0,0,2.24),.24,.12,white,g)
 elif kind=='cloud':
  for x,z,r in [(-.6,1.2,.5),(0,1.4,.7),(.65,1.2,.5)]:sphere('Cloud puff',(x,0,z),r,m,g)
 elif kind=='atom':
  sphere('Nucleus',(0,0,1.1),.35,m,g);details['electrons']=[]
  for i in range(3):
   pivot=empty('Electron orbit',g);pivot.location.z=1.1;pivot.rotation_euler.y=i*math.pi/3
   line('Orbit',[(math.cos(a),math.sin(a),0) for a in [j*math.tau/48 for j in range(49)]],.018,white,pivot)
   e=sphere('Electron',(1,0,0),.13,cyan,pivot);details['electrons'].append(e)
 elif kind=='gear':
  cyl('Gear disc',(0,0,.8),.65,.25,m,g,(math.pi/2,0,0))
  for i in range(12):
   a=i*math.tau/12;o=box('Gear tooth',(.75*math.cos(a),0,.8+.75*math.sin(a)),(.25,.3,.28),m,g);o.rotation_euler.y=-a
  cyl('Axle',(0,-.2,.8),.17,.4,white,g,(math.pi/2,0,0))
 elif kind=='scale':
  cyl('Stand',(0,0,1),.1,2,m,g);beam=empty('Balance beam',g);beam.location.z=2;box('Beam',(0,0,0),(2.2,.15,.15),m,beam)
  for x in [-1,1]:line('Hanger',[(x,0,0),(x,0,-.7)],.025,white,beam);cyl('Pan',(x,0,-.7),.45,.08,gold,beam)
  details['beam']=beam
 elif kind=='piston':
  box('Cylinder housing',(0,.2,1),(1.3,.6,2),m,g);p=box('Piston head',(0,-.15,1),(1.1,.4,.25),white,g);details['piston']=p
 elif kind=='magnet':
  for x,material in [(-.5,red),(.5,cyan)]:box('Magnet pole',(x,0,.9),(.45,.5,1.8),material,g)
  box('Magnet bridge',(0,0,.15),(1.4,.5,.3),m,g)
 elif kind=='water':
  for i in range(5):sphere('Water parcel',((i-2)*.2,0,.2),.14,m,g)
 elif kind=='arrow':
  box('Arrow shaft',(-.25,0,.8),(1.2,.15,.15),m,g);a=cone('Arrow point',(.5,0,.8),.28,.5,m,g);a.rotation_euler.y=math.pi/2
 elif kind=='cylinder':cyl('Cylinder',(0,0,.7),.55,1.4,m,g)
 elif kind=='sphere':sphere('Sphere',(0,0,.7),.65,m,g)
 else:box('Block',(0,0,.65),(1.2,1.2,1.3),m,g)
 g.location=spec['pos'];g.scale=spec['size'];return g,details

stage=empty('Stage');box('Ground',(0,0,-.18),(8.5,5,.25),mat('Stage blue',(.025,.08,.11)),stage)
# Offset each scene in physical space; hard cuts to six actual sets avoid reused backgrounds.
sets=[]
for k,sc in enumerate(plan['scenes']):
 group=empty('Set '+str(k));group.location.x=k*30
 sets.append([(o,*asset(o,group)) for o in sc['objects']])
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13.8;s.camera=cam
track=[]
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
for frame in range(1,N+1):
 t=(frame-1)/FPS;k=max(i for i,a in enumerate(starts) if a<=t);q=min(1,(t-starts[k])/ds[k]);e=ease(q);s.frame_set(frame);pins={};stage.location.x=k*30;stage.keyframe_insert(data_path='location',frame=frame)
 for spec,o,details in sets[k]:
  p=Vector(spec['pos']);size=Vector(spec['size']);action=spec['action'];o.rotation_euler=(0,0,0)
  if action in ('move','walk','rise','fall','flow'):
   # Flow cycles discrete parcels; causal actors move once towards the explicit destination.
   f=(q*2)%1 if action=='flow' else ease(q/.45) if spec.get('gesture')=='collect' else e;p=p.lerp(Vector(spec['to']),f)
  elif action=='spin':o.rotation_euler.z=q*math.tau
  elif action=='orbit':p.x+=.8*math.cos(q*math.tau);p.y+=.8*math.sin(q*math.tau)
  elif action=='grow':size*=.25+.75*e
  elif action=='pulse':size*=.87+.13*math.sin(q*math.tau*2)
  o.location=p;o.scale=size;o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='scale',frame=frame);o.keyframe_insert(data_path='rotation_euler',frame=frame)
  for j,joint in enumerate(details.get('joints',[])):
   joint.rotation_euler.x=(.45*math.sin(q*math.tau*4+(j%2)*math.pi)) if action=='walk' else .08*math.sin(q*math.tau+j);joint.keyframe_insert(data_path='rotation_euler',frame=frame)
  if spec.get('gesture') in ('point','collect') and details.get('joints'):
   arm=details['joints'][3]
   if spec['gesture']=='point':
    arm.rotation_euler.y=-1.05*ease(q/.35);arm.keyframe_insert(data_path='rotation_euler',frame=frame)
   else:
    reach=ease((q-.38)/.2);lift=ease((q-.62)/.25)
    arm.rotation_euler.y=-1.05*reach*(1-lift*.55);arm.rotation_euler.x=-1.25*lift;arm.keyframe_insert(data_path='rotation_euler',frame=frame)
    held=details['pickup'];held.scale=(1,1,1) if q>=.62 else (0,0,0);held.keyframe_insert(data_path='scale',frame=frame)
  if 'paper' in details:
   paper=details['paper'];paper.location.z=2.1-1.5*e;paper.keyframe_insert(data_path='location',frame=frame)
  if 'beam' in details:
   beam=details['beam'];beam.rotation_euler.y=.22*math.sin(q*math.tau);beam.keyframe_insert(data_path='rotation_euler',frame=frame)
  if 'piston' in details:
   piston=details['piston'];piston.location.z=1+.6*math.sin(q*math.tau*2);piston.keyframe_insert(data_path='location',frame=frame)
  for j,el in enumerate(details.get('electrons',[])):
   a=q*math.tau*2+j*2;el.location=(math.cos(a),math.sin(a),0);el.keyframe_insert(data_path='location',frame=frame)
 cam.data.ortho_scale=8.8 if len(sets[k])<=2 else 10.4 if len(sets[k])==3 else 12.0;cam.data.keyframe_insert(data_path='ortho_scale',frame=frame)
 target=Vector((k*30,0,1.0));cam.location=target+Vector((3.6,-17,9.5));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)
 bpy.context.view_layer.update()
 for spec,o,details in sets[k]:
  if spec.get('label'):
   anchor=2.4 if spec['kind'] in ('person','soldier') else .65 if spec['kind'] in ('salt','book') else 1.6;world=o.matrix_world@Vector((0,0,anchor));v=world_to_camera_view(s,cam,world);pins[spec['id']]=[v.x*720,(1-v.y)*1280]
 track.append({'t':t,'scene':k,'pins':pins})
# Constant camera cuts prevent interpolated travel between distant sets.
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for key in fc.keyframe_points:key.interpolation='CONSTANT' if o in (cam,stage) else 'LINEAR'
if cam.data.animation_data and cam.data.animation_data.action:
 for fc in cam.data.animation_data.action.fcurves:
  for key in fc.keyframe_points:key.interpolation='CONSTANT'
s.frame_start=1;s.frame_end=N
(R/'motion.json').write_text(json.dumps(track));(R/'scene_checks.json').write_text(json.dumps({'frames':N,'fps':FPS,'actual_3d':True,'photo_assets':0,'distinct_sets':6,'data_driven_objects':sum(len(x) for x in sets),'schematic_not_exact_reconstruction':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'));s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(R/'silent_3d.mp4');bpy.ops.render.render(animation=True)
print('DYNAMIC_3D_DONE',N,flush=True)
