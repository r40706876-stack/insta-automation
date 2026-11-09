"""Data-driven procedural 3D actors. Plan is JSON, never executable AI code."""
import bpy,json,math,os
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['STUDIO_ROOT']);plan=json.loads((R/'recipe.json').read_text());meta=json.loads((R/'audio.json').read_text());ds=meta['seconds'];starts=[sum(ds[:i]) for i in range(6)];FPS=24;N=math.ceil(sum(ds)*FPS)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=FPS;s.display.render_aa=os.getenv('STUDIO_RENDER_AA','8')
sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True;sh.show_object_outline=True;sh.background_type='WORLD';s.world.color=(.018,.039,.063);s.view_settings.view_transform='Standard'
CINE=os.getenv('STUDIO_CINEMATIC')=='1'
GLASS_KEYS=('glass','Optical')
EMIT={'Light ray':7,'Spectrum':9,'Flame':12,'Lava':7,'Sun':5,'Bulb glow':0,'Light halo':5,'Latitude line':2,'White light':10,'Light inside':6,'Magma':4,'Electron':2,'Rain':1.5}
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
 if CINE:
  m.use_nodes=True;b=m.node_tree.nodes['Principled BSDF'];b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.38
  if any(k.lower() in name.lower() for k in GLASS_KEYS):
   b.inputs['Transmission Weight'].default_value=1;b.inputs['Roughness'].default_value=.03;b.inputs['IOR'].default_value=1.5
  for k,v in EMIT.items():
   if name.startswith(k):b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=v
  if name in ('Stage blue','Outline'):b.inputs['Roughness'].default_value=.16;b.inputs['Metallic'].default_value=.3
 return m
if CINE:
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=int(os.getenv('STUDIO_SAMPLES','20'));s.cycles.use_adaptive_sampling=True;s.cycles.use_denoising=True;s.cycles.denoiser='OPENIMAGEDENOISE'
 s.cycles.max_bounces=8;s.cycles.transmission_bounces=8;s.cycles.caustics_reflective=False;s.cycles.caustics_refractive=False;s.render.use_persistent_data=True
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Punchy'
 w=bpy.data.worlds.new('Cinematic sky');s.world=w;w.use_nodes=True;wn=w.node_tree;bgn=wn.nodes['Background'];bgn.inputs['Color'].default_value=(.012,.03,.06,1);bgn.inputs['Strength'].default_value=.6
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

import sys
sys.path.insert(0,str(R))
import rich_assets as rich
rich.configure(globals())

def asset(spec,parent):
 kind=spec['kind'];g=empty(spec['id'],parent);m=mat(spec['id'],tuple(int(spec['color'][i:i+2],16)/255 for i in (1,3,5)));details={}
 if kind in ('person','soldier'):
  details['human']=rich.human(g,gandhi=spec.get('role')=='gandhi',color=m,scale=1.18,role=spec.get('role','soldier' if kind=='soldier' else 'ordinary'))
  if kind=='soldier':
   h=details['human'];cyl('Helmet',(0,0,.23),.23,.15,m,h['head']);box('Shield',(-.3,-.2,.25),(.5,.1,.65),gold,h['body'])
 elif kind=='map':details.update(rich.map_asset(g,spec))
 elif kind in rich.PHYSICS_BUILDERS:
  inner=empty(spec['id']+' diagram',g);inner.scale=(1.22,1.22,1.22);inner.location.z=-.4;spec['_m']=m;details.update(rich.PHYSICS_BUILDERS[kind](inner,spec));details['map_markers']=[(t,Vector((x*1.22,y*1.22,z*1.22-.4))) for t,(x,y,z) in details.pop('labels',[])]
 elif kind=='ocean':
  # Ocean is a diorama; its mesh and moving foam are scaled together.
  details.update(rich.ocean_asset(g))
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
  if kind=='planet':rich.world_coasts(g)
  elif kind=='sun':
   for i in range(12):
    a=i*math.tau/12;line('Sun ray',[(1.18*math.cos(a),0,1.2+1.18*math.sin(a)),(1.48*math.cos(a),0,1.2+1.48*math.sin(a))],.045,gold,g)
  else:
   for i in range(4):sphere('Crater',(.55*math.cos(i*2),-.8,1.2+.5*math.sin(i*2)),.2,dark,g)
 elif kind=='tree':
  cyl('Trunk',(0,0,.6),.15,1.2,dark,g);cone('Foliage',(0,0,1.4),.8,1.6,m,g)
 elif kind=='mountain':rich.terrain_asset(g)
 elif kind=='rock_layers':details.update(rich.rock_layers(g))
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
 phys=any(o['kind'] in rich.PHYSICS_BUILDERS for o in sc['objects'])
 sc['_environment']=rich.environment('neutral' if phys else sc.get('setting','neutral'),group)
 if CINE:
  for nm,loc,en,size,col in (('Key',(-4,-6,8),1400,6,(1,.95,.88)),('Rim',(4,5,6),900,4,(.55,.78,1)),('Fill',(5,-7,3),350,5,(1,.9,.8))):
   ld=bpy.data.lights.new(nm,'AREA');ld.energy=en;ld.size=size;ld.color=col;lo=bpy.data.objects.new(nm+' light',ld);bpy.context.collection.objects.link(lo);lo.location=(k*30+loc[0],loc[1],loc[2]);lo.rotation_euler=(Vector((k*30,0,1.2))-Vector(lo.location)).to_track_quat('-Z','Y').to_euler()
 sets.append([(o,*asset(o,group)) for o in sc['objects']])
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=13.8;s.camera=cam
track=[]
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
for frame in range(1,N+1):
 t=(frame-1)/FPS;k=max(i for i,a in enumerate(starts) if a<=t);q=min(1,(t-starts[k])/ds[k]);e=ease(q);s.frame_set(frame);pins={};annotations=[];stage.location.z=-100 if any(sp['kind']=='map' for sp,_,_ in sets[k]) or plan['scenes'][k].get('setting')=='space' else 0;stage.location.x=k*30;stage.keyframe_insert(data_path='location',frame=frame)
 if plan['scenes'][k].get('_environment'):rich.animate_ocean(plan['scenes'][k]['_environment'],t,frame)
 for spec,o,details in sets[k]:
  aq=q;window=spec.get('animation_window',[0,1]);q=max(0,min(1,(aq-window[0])/(window[1]-window[0])));e=ease(q)
  p=Vector(spec['pos']);size=Vector(spec['size']);action='none' if spec['kind'] in rich.PHYSICS_BUILDERS else spec['action'];o.rotation_euler=(0,0,0)
  if action in ('move','walk','rise','fall','flow'):
   # Flow cycles discrete parcels; causal actors move once towards the explicit destination.
   f=(q*2)%1 if action=='flow' else ease(q/.45) if spec.get('gesture')=='collect' else e;p=p.lerp(Vector(spec['to']),f)
  elif action=='spin':o.rotation_euler.z=q*math.tau
  elif action=='orbit':p.x+=.8*math.cos(q*math.tau);p.y+=.8*math.sin(q*math.tau)
  elif action=='grow':size*=.25+.75*e
  elif action=='pulse':size*=.87+.13*math.sin(q*math.tau*2)
  if spec['kind']=='arrow' and action=='move':
   travel=Vector(spec['to'])-Vector(spec['pos'])
   if travel.length>.01:o.rotation_euler=Vector((1,0,0)).rotation_difference(travel.normalized()).to_euler()
  o.location=p;o.scale=size;o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='scale',frame=frame);o.keyframe_insert(data_path='rotation_euler',frame=frame)
  if 'fold_keys' in details:rich.animate_folds(details,q,frame)
  if 'human' in details:
   h=details['human'];pickup=spec.get('gesture')=='collect';poseq=max(0,min(1,(q-.4)/.6)) if pickup else q;rich.pose(h,poseq,frame,walk=action=='walk' and (not pickup or q<.45),collect=pickup,hold=spec.get('gesture')=='hold')
   if action=='walk' and 'to' in spec:
    travel=Vector(spec['to'])-Vector(spec['pos'])
    if abs(travel.x)+abs(travel.y)>.01:h['root'].rotation_euler.z=math.atan2(travel.x,-travel.y)*(1-ease((q-.3)/.15) if pickup else 1)
    rich.key(h['root'],'rotation_euler',frame)
   if spec.get('gesture')=='point':
    arm=h['arms'][1][0];arm.rotation_euler.y=-1.0*ease(q/.35);rich.key(arm,'rotation_euler',frame)
   if spec.get('gesture') in ('collect','hold'):
    target=next((sp for sp,_,_ in sets[k] if sp['id']==spec.get('interact_with')),None)
    if target and target['kind']!='salt':
     # This engine has no matching grasp payload for this object; do not show fake salt.
     h['salt'].scale=(0,0,0);rich.key(h['salt'],'scale',frame)
  if details.get('route') or details.get('map_extras'):rich.animate_map(details,q,frame)
  if 'anim' in details:details['anim'](q,frame)
  if 'wave' in details:rich.animate_ocean(details,t,frame)
  if 'paper' in details:
   paper=details['paper'];paper.location.z=2.1-1.5*e;paper.keyframe_insert(data_path='location',frame=frame)
  if 'beam' in details:
   beam=details['beam'];beam.rotation_euler.y=.22*math.sin(q*math.tau);beam.keyframe_insert(data_path='rotation_euler',frame=frame)
  if 'piston' in details:
   piston=details['piston'];piston.location.z=1+.6*math.sin(q*math.tau*2);piston.keyframe_insert(data_path='location',frame=frame)
  q=aq;e=ease(q)
  for j,el in enumerate(details.get('electrons',[])):
   a=q*math.tau*2+j*2;el.location=(math.cos(a),math.sin(a),0);el.keyframe_insert(data_path='location',frame=frame)
 cam.data.ortho_scale=(11.5 if any(sp['kind']=='map' for sp,_,_ in sets[k]) else 8.8 if len(sets[k])<=2 else 10.4 if len(sets[k])==3 else 12.0)-.12*ease(q);cam.data.keyframe_insert(data_path='ortho_scale',frame=frame)
 target=Vector((k*30,0,1.0));_dir=(Vector((0,-20,0)) if any(sp['kind']=='map' for sp,_,_ in sets[k]) else ({'front':Vector((0,-20,3)), 'top':Vector((0,-.01,20)), 'oblique':Vector((3.6,-17,9.5))}['front' if any(sp['kind'] in rich.PHYSICS_BUILDERS for sp,_,_ in sets[k]) else plan['scenes'][k].get('camera_view','oblique')]))
 if CINE:
  cam.data.type='PERSP';cam.data.lens=50;S=cam.data.ortho_scale*(1-.1*ease(q));cam.location=target+_dir.normalized()*(S*50/36)+Vector((.35*math.sin(q*math.pi),0,0))
  cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=3.2;cam.data.dof.focus_distance=(target-cam.location).length;cam.data.dof.keyframe_insert(data_path='focus_distance',frame=frame)
 else:cam.location=target+_dir
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)
 bpy.context.view_layer.update()
 for spec,o,details in sets[k]:
  for label,point in details.get('map_markers',[]):
   v=world_to_camera_view(s,cam,o.matrix_world@point);annotations.append({'text':label,'anchor':[v.x*720,(1-v.y)*1280]})
  for label,point in details.get('map_context',[]):
   v=world_to_camera_view(s,cam,o.matrix_world@point);annotations.append({'text':label,'anchor':[v.x*720,(1-v.y)*1280],'style':'context'})
  if spec.get('label'):
   anchor=2.4 if spec['kind'] in ('person','soldier') else .65 if spec['kind'] in ('salt','book') else 1.6;world=o.matrix_world@Vector((0,0,anchor));v=world_to_camera_view(s,cam,world);pins[spec['id']]=[v.x*720,(1-v.y)*1280]
 track.append({'t':t,'scene':k,'pins':pins,'annotations':annotations,'map_disclaimer':any(sp['kind']=='map' and sp.get('route') for sp,_,_ in sets[k])})
# Constant camera cuts prevent interpolated travel between distant sets.
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for key in fc.keyframe_points:key.interpolation='CONSTANT' if o in (cam,stage) else 'LINEAR'
if cam.data.animation_data and cam.data.animation_data.action:
 for fc in cam.data.animation_data.action.fcurves:
  for key in fc.keyframe_points:key.interpolation='CONSTANT'
s.frame_start=1;s.frame_end=N
if CINE:
 for m in bpy.data.materials:
  ad=m.animation_data
  if not (ad and ad.action and m.use_nodes):continue
  b=m.node_tree.nodes.get('Principled BSDF')
  frames=sorted({int(kp.co[0]) for fc in ad.action.fcurves if fc.data_path=='diffuse_color' for kp in fc.keyframe_points})
  for f in frames:
   col=[next((fc.evaluate(f) for fc in ad.action.fcurves if fc.data_path=='diffuse_color' and fc.array_index==i),1) for i in range(4)]
   b.inputs['Base Color'].default_value=col;b.inputs['Base Color'].keyframe_insert('default_value',frame=f)
   if m.name.startswith('Bulb glow'):
    b.inputs['Emission Color'].default_value=col;b.inputs['Emission Strength'].default_value=12*max(0,col[0]-.4);b.inputs['Emission Color'].keyframe_insert('default_value',frame=f);b.inputs['Emission Strength'].keyframe_insert('default_value',frame=f)
 s.use_nodes=True;ct=s.node_tree;ct.nodes.clear();rl=ct.nodes.new('CompositorNodeRLayers');gl=ct.nodes.new('CompositorNodeGlare');co=ct.nodes.new('CompositorNodeComposite')
 gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=.85;gl.size=7;ct.links.new(rl.outputs['Image'],gl.inputs['Image']);ct.links.new(gl.outputs['Image'],co.inputs['Image'])
(R/'motion.json').write_text(json.dumps(track));(R/'scene_checks.json').write_text(json.dumps({'frames':N,'fps':FPS,'actual_3d':True,'quality_version':'rich_3d_v1','articulated_people':any(sp['kind'] in ('person','soldier') for sc in sets for sp,_,_ in sc),'source_based_maps':any(sp['kind'] in ('map','planet') for sc in sets for sp,_,_ in sc),'continuous_rock_layers':any(sp['kind']=='rock_layers' for sc in sets for sp,_,_ in sc),'terrain_relief':any(sp['kind']=='mountain' for sc in sets for sp,_,_ in sc),'photo_assets':0,'distinct_sets':6,'data_driven_objects':sum(len(x) for x in sets),'schematic_not_exact_reconstruction':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'));s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(R/'silent_3d.mp4');
if os.getenv('STUDIO_PREVIEW_FRAME'):
 s.frame_set(int(os.environ['STUDIO_PREVIEW_FRAME']));s.render.image_settings.file_format='JPEG';s.render.filepath=str(R/'preview.jpg');bpy.ops.render.render(write_still=True)
else:bpy.ops.render.render(animation=True)
print('DYNAMIC_3D_DONE',N,flush=True)

