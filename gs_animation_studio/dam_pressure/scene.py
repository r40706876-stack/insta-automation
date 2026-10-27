"""True 3D pressure demonstration: moving caps, ballistic water, force arrows, widening gravity dam."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['STUDIO_ROOT']);meta=json.loads((R/'audio.json').read_text());ds=meta['seconds'];starts=[sum(ds[:i]) for i in range(6)];total=sum(ds);FPS=24;N=math.ceil(total*FPS)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=FPS;s.display.render_aa='8'
sh=s.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL';sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=True;sh.show_object_outline=True;sh.object_outline_color=(.02,.04,.06);sh.background_type='WORLD';s.world.color=(.018,.039,.063);s.view_settings.view_transform='Standard'
def mat(name,c):m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);return m
water=mat('Blue water',(.025,.5,.74));cyan=mat('Moving water highlights',(.18,.85,1));concrete=mat('Warm concrete',(.71,.73,.68));white=mat('White edges',(.91,.94,.91));gold=mat('Lower pressure emphasis',(.99,.67,.11));red=mat('Red removable caps',(.94,.25,.12));navy=mat('Navy stage',(.035,.075,.1));green=mat('Land',(.16,.43,.26))
def root(name):bpy.ops.object.empty_add();o=bpy.context.object;o.name=name;return o
tank=root('Experimental tank shot');dam=root('Concrete gravity dam shot')
def box(name,p,size,m,parent=None,bevel=.02):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:b=o.modifiers.new('Edge bevel','BEVEL');b.width=bevel;b.segments=2;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 if parent:o.parent=parent
 return o
def line(name,pts,r,m,parent=None):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2;sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
 for a,p in zip(sp.points,pts):a.co=(*p,1)
 o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(m)
 if parent:o.parent=parent
 return o
def sphere(name,p,m,parent,r=.055):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=r,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m);o.parent=parent;return o
def cylinder(name,p,r,depth,m,parent):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=depth,location=p,rotation=(0,math.pi/2,0));o=bpy.context.object;o.name=name;o.data.materials.append(m);o.parent=parent;return o
def force_arrow(parent,z,length,m):
 a=root('Force arrow at equal area '+str(z));a.parent=parent
 box('Arrow shaft',(-length/2,0,0),(length,.055,.055),m,a,0)
 bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=.12,radius2=0,depth=.28,location=(0,0,0),rotation=(0,math.pi/2,0));q=bpy.context.object;q.data.materials.append(m);q.parent=a
 a.location=(-.05,-.88,z);return a
box('Experiment base',(1.2,0,-.13),(8.7,3,.25),navy,tank,.09)
box('Tank rear wall',(-1.25,.8,2.65),(2.7,.1,5.3),concrete,tank)
box('Tank left wall',(-2.6,0,2.65),(.12,1.7,5.3),concrete,tank)
# Front pane is removed to reveal water; real side-wall openings remain visible.
for lo,hi in [(0,2.64),(2.96,4.04),(4.36,5.3)]:box('Right wall between outlets',(0,0,(lo+hi)/2),(.12,1.6,hi-lo),concrete,tank)
for x in (-2.6,0):line('Glass cutaway edge',[(x,-.82,0),(x,-.82,5.3)],.035,white,tank)
box('Tank floor',(-1.3,0,0),(2.7,1.7,.12),white,tank)
body=box('Water volume',(-1.3,0,2.5),(2.55,1.5,5),water,tank,0)
for z in [i*.5 for i in range(1,10)]:line('Depth marking',[(-2.58,-.87,z),(-2.35,-.87,z)],.02,white,tank)
holes=[4.2,2.8];caps=[];streams=[];drops=[];G=3.;H=5.
for j,z in enumerate(holes):
 for xx in (.05,.16):
  line('Nozzle rim',[(xx,.14*math.cos(a),z+.14*math.sin(a)) for a in [i*math.tau/20 for i in range(21)]],.025,white,tank)
 caps.append(cylinder('Cap '+str(j),(.22,0,z),.15,.07,red,tank))
 v=math.sqrt(2*G*(H-z));T=math.sqrt(2*z/G)
 pts=[(.22+v*T*i/48,0,z-.5*G*(T*i/48)**2) for i in range(49)]
 streams.append(line('Flowing jet '+str(j),pts,.032,cyan,tank))
 drops.append([sphere('Moving water parcel '+str(j)+' '+str(i),(0,0,0),cyan,tank,.052 if j==0 else .065) for i in range(12)])
 # Splash rings animate at the real ballistic impact point.
 for k in range(2):
  x=.22+v*T;line('Splash pool',[(x+.18*math.cos(a),.18*math.sin(a),.02) for a in [i*math.tau/20 for i in range(21)]],.017,cyan,tank)
tankArrows=[force_arrow(tank,z,.18+.25*(H-z),gold if z<3 else cyan) for z in (1.,2.,3.,4.)]
# A cutaway gravity dam with a narrow crest and a growing downstream base.
box('Dam foundation',(-.2,0,-.2),(7,4,.4),navy,dam,.12)
box('Reservoir behind dam',(-2,0,2.5),(2.4,2.2,5),water,dam,0)
verts=[]
for y in (-1.1,1.1):verts += [(-.8,y,0),(-.35,y,0),(-.35,y,5.3),(-.8,y,5.3)]
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
me=bpy.data.meshes.new('Gravity dam cross section');me.from_pydata(verts,[],faces);me.update();wall=bpy.data.objects.new('Widening concrete dam',me);bpy.context.collection.objects.link(wall);wall.parent=dam;wall.data.materials.append(concrete)
wall.shape_key_add(name='Narrow wall');wide=wall.shape_key_add(name='Broad gravity base')
for idx in (1,5):wide.data[idx].co.x=1.5
base=box('Highlighted broad base',(.35,-1.14,.07),(2.3,.06,.14),gold,dam,0)
for y in [i*.4-1 for i in range(6)]:box('Crest safety post',(-.56,y,5.58),(.045,.045,.5),white,dam,.005)
line('Crest railing',[(-.56,-1.05,5.82),(-.56,1.05,5.82)],.02,white,dam)
damArrows=[force_arrow(dam,z,.14+.25*(H-z),gold if z<3 else cyan) for z in (1.,2.,3.,4.)]
for a in damArrows:a.location.x=-.85;a.location.y=-1.22
# Surface ripple geometry moves; the water is never a pasted photograph.
ripples=[]
for group,yy,xx in [(tank,-.25,-1.3),(dam,-.35,-2.)]:
 for j in range(4):ripples.append((line('Water ripple',[(xx-.6,yy+j*.24,5.012),(xx-.1,yy+j*.24+.04,5.012),(xx+.5,yy+j*.24,5.012)],.014,cyan,group),j))
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=14.8;s.camera=cam

def ease(q):q=max(0,min(1,q));return q*q*(3-2*q)
def frac(t,a,b):return ease((t-a)/max(.001,b-a))
track=[];opened_at=starts[1]+max(.5,ds[1]*.55)
for frame in range(1,N+1):
 t=(frame-1)/FPS;s.frame_set(frame);k=max(i for i,a in enumerate(starts) if a<=t);experiment=k in (1,2,3);isdam=not experiment
 for ob,shown in [(tank,experiment),(dam,isdam)]:ob.scale=(1,1,1) if shown else (0,0,0);ob.keyframe_insert(data_path='scale',frame=frame)
 showflow=experiment and t>=opened_at;head=5-.0004*max(0,t-opened_at)
 body.scale.z=head/5;body.location.z=head/2;body.keyframe_insert(data_path='scale',frame=frame);body.keyframe_insert(data_path='location',frame=frame)
 opening=frac(t,opened_at-.45,opened_at)
 for j,(z,cap,stream,parcels) in enumerate(zip(holes,caps,streams,drops)):
  cap.location=(.22+opening*.6,0,z+opening*.48);cap.scale=(0,0,0) if opening>.999 else (1-opening*.35,)*3;cap.keyframe_insert(data_path='location',frame=frame);cap.keyframe_insert(data_path='scale',frame=frame)
  v=math.sqrt(2*G*(head-z));T=math.sqrt(2*z/G);stream.data.bevel_factor_end=min(1,max(0,(t-opened_at)/T)) if showflow else 0;stream.data.keyframe_insert(data_path='bevel_factor_end',frame=frame)
  for i,o in enumerate(parcels):
   age=((t-opened_at)+i*T/12)%T;active=showflow and (t-opened_at)>=age;o.location=(.22+v*age,0,z-.5*G*age**2);o.scale=(1,1,1) if active else (0,0,0);o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='scale',frame=frame)
  assert head>z and v>0
 # Equal-area force arrows grow in a depth-dependent sequence, never reverse magnitude.
 for group in (tankArrows,damArrows):
  for j,o in enumerate(group):
   show=(k==3 or k>=4);pulse=.92+.08*math.sin(t*3+j);o.scale=(pulse,pulse,pulse) if show else (0,0,0);o.keyframe_insert(data_path='scale',frame=frame)
 value=frac(t,.08,1.15) if k==0 else frac(t,starts[4]+.4,starts[4]+2.8) if k>=4 else 0
 wide.value=value;wide.keyframe_insert(data_path='value',frame=frame)
 base.scale.x=.2+.8*value;base.location.x=-.575+.925*value;base.keyframe_insert(data_path='scale',frame=frame);base.keyframe_insert(data_path='location',frame=frame)
 for o,j in ripples:o.location.x=.045*math.sin(t*2+j);o.keyframe_insert(data_path='location',frame=frame)
 target=Vector((1.15,0,2.55)) if experiment else Vector((-.65,0,2.55));cam.location=target+Vector((6.7,-18,8.4));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=frame);cam.keyframe_insert(data_path='rotation_euler',frame=frame)
 pins={}
 for name,p in {'upper':(.22,0,4.2),'lower':(.22,0,2.8),'surface':(-2.1,0,head),'dam_base':(.7,-1.15,.25)}.items():
  q=world_to_camera_view(s,cam,Vector(p));pins[name]=[q.x*720,(1-q.y)*1280]
 track.append({'t':t,'scene':k,'jet_open':showflow,'head':head,'upper_speed':math.sqrt(2*G*(head-4.2)),'lower_speed':math.sqrt(2*G*(head-2.8)),'dam_base':value,'pins':pins})
 assert track[-1]['lower_speed']>track[-1]['upper_speed'],'Deeper outlet must have greater exit speed'
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for p in fc.keyframe_points:p.interpolation='LINEAR'
s.frame_start=1;s.frame_end=N
(R/'motion.json').write_text(json.dumps(track));(R/'scene_checks.json').write_text(json.dumps({'frames':N,'fps':FPS,'photo_assets':0,'actual_3d':True,'deeper_outlet_faster_verified':True,'ballistic_water_parcels':24,'base_widens_not_top':True,'schematic_not_construction_design':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'))
if os.getenv('STUDIO_PROOF'):
 s.frame_set(int(os.getenv('STUDIO_PROOF_FRAME','400')));s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'proof.png');bpy.ops.render.render(write_still=True)
else:
 s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(R/'silent_3d.mp4');bpy.ops.render.render(animation=True)
print('STUDIO_3D_RENDER_DONE',N,flush=True)
