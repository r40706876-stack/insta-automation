"""Original procedural 3D props for Meerut-to-Delhi history storytelling."""
import bpy,math,os,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(os.environ.get('GS_FILM_ROOT','experiments/meerut_delhi_film'));ROOT.mkdir(parents=True,exist_ok=True)
SHOT=os.environ.get('GS_SHOT','chains');FPS=12;N=48
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=720;s.render.resolution_y=1280;s.render.resolution_percentage=100;s.render.fps=FPS
s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.eevee.taa_render_samples=8
s.world.color=(.015,.022,.032);s.render.image_settings.color_mode='RGB'
s.view_settings.view_transform='AgX'
# Ambient occlusion, real bevel geometry, rough metals and soft area lighting.
def mat(name,c,metal=0,rough=.4):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 if 'sandstone' in name.lower() or 'historic' in name.lower() or 'iron' in name.lower():
  nodes=m.node_tree.nodes;links=m.node_tree.links
  tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=17;tex.inputs['Detail'].default_value=3
  bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=.09
  links.new(tex.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
 if 'sandstone' in name.lower():
  brick=m.node_tree.nodes.new('ShaderNodeTexBrick');brick.inputs['Scale'].default_value=5;brick.inputs['Mortar Size'].default_value=.025
  brick.inputs['Color1'].default_value=(*c,1);brick.inputs['Color2'].default_value=(*(v*.6 for v in c),1);brick.inputs['Mortar'].default_value=(.08,.035,.02,1)
  m.node_tree.links.new(brick.outputs['Color'],bs.inputs['Base Color'])
 return m
iron=mat('Aged dark iron',(.11,.14,.16),.8,.27);gold=mat('Warm brass',(.57,.31,.08),.8,.25);stone=mat('Red sandstone',(.39,.105,.06),0,.8);edge=mat('Sandstone edge',(.61,.25,.14),0,.7);dark=mat('Arched gateway shadow',(.017,.023,.026));floor=mat('Dark historic stage',(.038,.048,.057),.1,.6)
def cube(name,loc,scale,m,bevel=.05):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:mod=o.modifiers.new('Soft edge highlights','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cylinder(name,loc,r,depth,m):
 bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m);o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
def torus(name,loc,major,minor,m,rot=(0,0,0),scale=(1,1,1)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=40,minor_segments=12,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
cube('Ground',(0,0,-.3),(200,200,.5),floor,.02)
if SHOT=='chains':
 links=[]
 for j in range(9):
  x=(j-4)*.53;z=1.8+.09*math.cos(j)
  o=torus('Interlocking iron link '+str(j),(x,0,z),.34,.075,iron,(math.pi/2 if j%2 else .15,0,0),(1.3,1,1));links.append(o)
 lock=cube('Prison lock body',(0,-.3,1.4),(.9,.35,.9),iron,.1)
 torus('Brass lock shackle',(0,-.3,1.98),.3,.07,gold,(math.pi/2,0,0),(1,1.1,1))
 cylinder('Keyhole',(0,-.52,1.42),.08,.02,dark).rotation_euler=(math.pi/2,0,0)
 # Not a documentary reconstruction: a symbolic transition from confinement to release.
 for j,o in enumerate(links):
  o.keyframe_insert(data_path='location',frame=1);o.keyframe_insert(data_path='rotation_euler',frame=1)
  o.keyframe_insert(data_path='location',frame=15)
  if j<4:o.location.x-=2.5;o.location.z+=.1
  elif j>4:o.location.x+=2.5;o.location.z+=.1
  else:o.location.z-=1.1;o.rotation_euler.y=1.3
  o.keyframe_insert(data_path='location',frame=N);o.keyframe_insert(data_path='rotation_euler',frame=N)
 target=(0,0,1.6);camA=(.6,-7.7,3.1);camB=(-.3,-6.7,2.5)
elif SHOT=='fort':
 # Original architectural model inspired by Red Fort; deliberately labelled schematic.
 cube('Long curtain wall',(0,0,1.05),(7,.65,2.1),stone,.04)
 cube('Central gate block',(0,-.25,1.5),(2.1,1,3),edge,.06)
 # Dark arched opening is a real outlined mesh, not a black rectangular card.
 verts=[(-.54,-.79,0),(.54,-.79,0),(.54,-.79,1.55)]+[(.54*math.cos(a),-.79,1.55+.54*math.sin(a)) for a in [j*math.pi/24 for j in range(25)]]
 mesh=bpy.data.meshes.new('Arch opening');mesh.from_pydata(verts,[],[tuple(range(len(verts)))]);mesh.update()
 obj=bpy.data.objects.new('Arched gateway interior',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(dark)
 # Layered arch mesh at gateway, with carved radial voussoirs.
 for j in range(18):
  a=j*math.pi/17;x=.59*math.cos(a);z=1.55+.59*math.sin(a)
  q=cube('Carved arch stone',(x,-.81,z),(.18,.12,.25),edge,.015);q.rotation_euler.y=-a
 for x in (-2.8,-1.2,1.2,2.8):
  cylinder('Fort turret',(x,-.05,2.15),.33,.8,edge)
  cylinder('Chhatri top',(x,-.05,3.1),.5,.12,edge)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(x,-.05,3.25));o=bpy.context.object;o.scale=(.4,.4,.24);o.data.materials.append(stone)
  for a in range(4):
   xx=x+.26*math.cos(a*math.pi/2);yy=-.05+.26*math.sin(a*math.pi/2);cylinder('Chhatri pillar',(xx,yy,2.83),.035,.5,stone)
 for x in [j*.3-3.45 for j in range(24)]:cube('Battlement merlon',(x,-.05,2.25),(.18,.75,.32),stone,.02)
 for x in (-3.7,3.7):cylinder('Corner bastion',(x,0,1.25),.5,2.5,edge)
 # Small moving light points converge at the gate: symbolic people, not fake historical footage.
 for j in range(12):
  o=cylinder('Arrival marker '+str(j),((j%4-1.5)*.3,-2.7-j//4*.4,.1),.055,.16,gold)
  o.keyframe_insert(data_path='location',frame=1);o.location.y+=1.4;o.keyframe_insert(data_path='location',frame=N)
 target=(0,0,1.3);camA=(4,-9,4.5);camB=(1.5,-8.5,3.4)
else:raise ValueError(SHOT)
for loc,power,color,size in [((-4,-4,7),1300,(1,.68,.38),5),((4,1,6),1600,(.32,.67,1),4),((0,-5,3),400,(1,.8,.57),3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=camA);cam=bpy.context.object;s.camera=cam;cam.data.lens=46
for f,loc in ((1,camA),(N,camB)):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f)
for o in bpy.data.objects:
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for key in fc.keyframe_points:key.interpolation='LINEAR'
s.frame_start=1;s.frame_end=N
folder=ROOT/SHOT;folder.mkdir(exist_ok=True)
s.render.filepath=str(folder/'frame_')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/(SHOT+'.blend')))
if os.environ.get('GS_STILL')=='1':
 s.frame_set(24);s.render.filepath=str(ROOT/(SHOT+'_proof.png'));bpy.ops.render.render(write_still=True)
else:bpy.ops.render.render(animation=True)
print('REAL_3D_SCENE_COMPLETE',SHOT)
