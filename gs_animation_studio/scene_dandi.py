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

# Topic-specific stage: rounded anatomy, articulated limbs, mesh sea and sourced geography.
sand=mat('Warm sand',(.68,.48,.23));foam=mat('Sea foam',(.77,.96,.95));cloth=mat('Handwoven white',(.92,.9,.79));brown=mat('Staff wood',(.24,.1,.035));land=mat('Gujarat land',(.15,.57,.4));sea=mat('Arabian sea',(.025,.24,.37))
def ell(name,pos,scale,m,parent):
 o=sphere(name,pos,1,m,parent);o.scale=scale;return o

def bone(name,pivot,length,r,m):
 o=cyl(name,(0,0,-length/2),r,length,m,pivot);sphere(name+' joint',(0,0,-length),r,m,pivot);return o

def human(parent,pos=(0,0,0),gandhi=False,color=cyan,scale=1):
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
 else:
  cap=cyl('White Gandhi cap',(0,0,.23),.215,.14,cloth,head);cap.scale.y=.8
 # Dhoti folds, rather than the previous solid cube.
 bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.31,radius2=.23,depth=.55,location=(0,0,-.12));skirt=bpy.context.object;skirt.name='Dhoti cloth';skirt.parent=body;skirt.data.materials.append(cloth)
 for x in [-.12,0,.12]:line('Dhoti folds',[(x,-.225,.13),(x*.85,-.275,-.38)],.012,white,body)
 if gandhi:
  # A diagonal shawl leaves the lean torso visible.
  line('White shoulder shawl',[(-.2,-.05,.94),(-.23,-.2,.7),(-.08,-.21,.37),(.18,-.16,.18)],.1,cloth,body)
  ell('Shawl on shoulder',(-.23,0,.82),(.09,.2,.23),cloth,body)
 arms=[];legs=[]
 for side in [-1,1]:
  hip=empty('Hip',root);hip.location=(side*.13,0,.99)
  bone('Upper leg',hip,.43,.066,skin)
  knee=empty('Knee',hip);knee.location.z=-.43;bone('Shin',knee,.43,.052,skin)
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
 nx,ny=30,16;verts=[(-7+14*i/nx,1+7*j/ny,0) for j in range(ny+1) for i in range(nx+1)];faces=[]
 for j in range(ny):
  for i in range(nx):
   a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
 mesh=bpy.data.meshes.new('Deforming ocean surface');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Animated sea',mesh);bpy.context.collection.objects.link(o);o.parent=parent;o.data.materials.append(water)
 o.shape_key_add(name='Basis');wave=o.shape_key_add(name='Rolling waves')
 for v in wave.data:v.co.z=.10*math.sin(v.co.x*1.3+v.co.y*2)+.06*math.cos(v.co.y*4)
 crests=[]
 for j in range(5):crests.append(line('Traveling foam',[(-7+i*.28,1.3+j*.9+.11*math.sin(i*.3),.11) for i in range(51)],.025,foam,parent))
 for i in range(15):
  x=-2+(i%5)*.27;y=-.7+(i//5)*.24;o=box('Natural salt crust',(x,y,.025),(.12,.12,.06),white,parent);o.rotation_euler.z=i*1.17
 return wave,crests

def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
sets=[];actors={};seas={};coins=[];maps={};salt_ground=None
geo=json.loads((R/'dandi_map.json').read_text())
def mapxy(lonlat):return ((lonlat[0]-71.5)*.93,0,(lonlat[1]-22)*.93+1.6)
for k in range(6):
 g=empty('Dandi set '+str(k));g.location.x=k*30;sets.append(g)
 if k in (0,3,4,5):seas[k]=coast(g)
 else:box('Stage floor',(0,0,-.18),(12,8,.2),mat('Blue floor '+str(k),(.026,.075,.1)),g)
 if k==0:
  actors[k]=[human(g,(0,-.3,0),True,scale=1.25)]
 elif k==1:
  actors[k]=[human(g,(-1.15,0,0),False,cyan,1.05)]
  book=box('Salt law ledger',(1.1,.15,.45),(.9,.7,.85),red,g)
  for z in [.13,.4,.7]:box('Ledger pages',(1.1,-.22,z),(.82,.04,.04),white,g)
  for i in range(3):coins.append(cyl('Tax coin',(-.5-i*.18,-.3,.8),.17,.07,gold,g,(math.pi/2,0,0)))
 elif k==2:
  box('Sea map backplate',(0,.2,1.7),(6.5,.1,5),sea,g)
  for ring in geo['rings']:
   pts=[mapxy(p) for p in ring[:-1]]
   if len(pts)<3:continue
   # Curves fill the non-convex geographic polygon without a guessed convex hull.
   c=bpy.data.curves.new('Gujarat boundary','CURVE');c.dimensions='2D';c.fill_mode='BOTH';sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
   for v,p in zip(sp.points,pts):v.co=(p[0],p[2],0,1)
   sp.use_cyclic_u=True;o=bpy.data.objects.new('Gujarat geographical outline',c);bpy.context.collection.objects.link(o);o.parent=g;o.rotation_euler.x=math.pi/2;o.location.y=-.05;c.materials.append(land)
  a=Vector(mapxy(geo['ashram']));b=Vector(mapxy(geo['dandi']));a.y=b.y=-.16
  for name,p in [('Sabarmati endpoint',a),('Dandi endpoint',b)]:ell(name,p,(.075,.04,.075),gold,g)
  route=line('Schematic endpoint connector',[a,b],.038,gold,g);route.data.bevel_factor_end=0
  marker=ell('Moving journey marker',a,(.10,.055,.10),white,g);maps[k]=(route,marker,a,b)
 elif k==3:
  actors[k]=[human(g,(0,-.3,0),True,scale=1.2)]
  salt_ground=box('Salt picked from shore',(.22,-1.1,.06),(.22,.2,.12),white,g)
 elif k==4:
  actors[k]=[human(g,(-.6,-.7,0),True,scale=1.05)]
  for i,(x,y) in enumerate([(-1.25,.8),(.1,.7),(1.15,1.1),(-.45,2),(1.5,2.3)]):actors[k].append(human(g,(x,y,0),False,[cyan,white,gold][i%3],.88))
 elif k==5:
  actors[k]=[human(g,(-.65,0,0),True,scale=1.1),human(g,(.9,.7,0),False,cyan,.9)]

bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';s.camera=cam;track=[]
def screen(p):
 v=world_to_camera_view(s,cam,p);return [v.x*720,(1-v.y)*1280]
for frame in range(1,N+1):
 t=(frame-1)/FPS;k=max(i for i,a in enumerate(starts) if a<=t);q=min(1,(t-starts[k])/ds[k]);s.frame_set(frame);g=sets[k];offset=Vector((k*30,0,0))
 for j,h in enumerate(actors.get(k,[])):
  pose(h,q,frame,walk=k in (4,5),collect=k==3,hold=k in (0,5))
  if k in (4,5):h['root'].location.x+=.16*math.sin(q*math.pi);key(h['root'],'location',frame)
 if k in seas:
  wave,crests=seas[k];wave.value=.5+.5*math.sin(t*2);wave.keyframe_insert(data_path='value',frame=frame)
  for j,o in enumerate(crests):o.location.y=-.75*((t*.45+j*.19)%1);key(o,'location',frame)
 if k==1:
  for j,o in enumerate(coins):
   a=(q*1.25+j*.25)%1;o.location.x=-.6+1.5*a;o.location.z=.9+.22*math.sin(a*math.pi);o.rotation_euler.z=q*4;key(o,'location',frame);key(o,'rotation_euler',frame)
 if k==2:
  route,marker,a,b=maps[k];f=ease(q/.85);route.data.bevel_factor_end=max(.005,f);route.data.keyframe_insert(data_path='bevel_factor_end',frame=frame);marker.location=a.lerp(b,f);key(marker,'location',frame)
 if k==3:
  salt_ground.scale=(1,1,1) if q<.55 else (0,0,0);key(salt_ground,'scale',frame)
 # The dedicated map is front-on; coast shots have sea visible behind human figures.
 target=offset+Vector((0,0,1.3 if k!=2 else 1.65));cam.data.ortho_scale=(8.9 if k==2 else 8.2 if k==4 else 7.4)-.15*ease(q)
 cam.location=target+(Vector((0,-20,0)) if k==2 else Vector((2.3,-18,9)))
 cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();key(cam,'location',frame);key(cam,'rotation_euler',frame);cam.data.keyframe_insert(data_path='ortho_scale',frame=frame)
 bpy.context.view_layer.update();annotations=[]
 def label(txt,p):annotations.append({'text':txt,'anchor':screen(offset+Vector(p))})
 if k==0:label('गांधी • नमक सत्याग्रह',(-.1,0,3.1))
 if k==1:label('नमक पर कर',(1,.1,1.1));label('हर घर की ज़रूरत',(-1,0,2.9))
 if k==2:
  a=mapxy(geo['ashram']);b=mapxy(geo['dandi']);label('साबरमती आश्रम',(a[0]-.4,-.3,a[2]+.3));label('दांडी',(b[0]+.3,-.3,b[2]-.3));label('अरब सागर',(-1.7,-.3,.1))
 if k==3:label('दांडी • समुद्र तट',(-.4,1.8,.1))
 if k==4:label('अहिंसक विरोध',(-.1,0,3))
 if k==5:label('आम ज़रूरत → साझा विरोध',(0,0,3.1))
 track.append({'t':t,'scene':k,'pins':{},'annotations':annotations,'map_disclaimer':k==2})
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for keyframe in fc.keyframe_points:keyframe.interpolation='CONSTANT' if o==cam else 'LINEAR'
if cam.data.animation_data and cam.data.animation_data.action:
 for fc in cam.data.animation_data.action.fcurves:
  for keyframe in fc.keyframe_points:keyframe.interpolation='CONSTANT'
s.frame_start=1;s.frame_end=N
(R/'motion.json').write_text(json.dumps(track));(R/'scene_checks.json').write_text(json.dumps({'frames':N,'fps':FPS,'actual_3d':True,'photo_assets':0,'distinct_sets':6,'renderer':'dandi_coast_v3','deforming_sea':True,'articulated_limbs':True,'source_based_gujarat_outline':True,'route_is_schematic':True,'gandhi_is_stylized_likeness':True},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'scene.blend'));s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='HIGH';s.render.filepath=str(R/'silent_3d.mp4')
if os.getenv('STUDIO_PREVIEW_FRAME'):
 s.frame_set(int(os.environ['STUDIO_PREVIEW_FRAME']));s.render.image_settings.file_format='PNG';s.render.filepath=str(R/'preview.png');bpy.ops.render.render(write_still=True)
else:bpy.ops.render.render(animation=True)
print('DANDI_COAST_DONE',N,flush=True)
