"""Cinematic Cycles demo (8 s): prism splits white light, convex lens focuses rays.
Real glass refraction, glowing light beams, fog-glow, depth of field and a camera push-in on the key moment.
Run: blender -b --python cinematic_optics_demo.py -- OUTDIR"""
import bpy, math, sys, os
from mathutils import Vector

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/optics'
os.makedirs(OUT, exist_ok=True)
FPS = 24
SCENE_LEN = 4 * FPS            # two shots of 4 s
N = 2 * SCENE_LEN

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.getenv('OPTICS_SAMPLES', '24'))
sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 8
sc.cycles.transmission_bounces = 8
sc.cycles.glossy_bounces = 3
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, N
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy'
sc.render.film_transparent = False


def mat_principled(name, color, rough=.4, metal=0, transmission=0, ior=1.45, emit=None, strength=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = ior
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = strength
    return m


def link(o):
    bpy.context.collection.objects.link(o); return o


# ---------------- world: deep navy gradient + soft studio lights ----------------
w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground')
grad = nt.nodes.new('ShaderNodeTexGradient'); ramp = nt.nodes.new('ShaderNodeValToRGB'); tc = nt.nodes.new('ShaderNodeTexCoord')
mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, math.pi / 2, 0)
ramp.color_ramp.elements[0].color = (.004, .01, .03, 1); ramp.color_ramp.elements[1].color = (.02, .08, .14, 1)
nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs['Vector'], grad.inputs['Vector'])
nt.links.new(grad.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 1.0; nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

floor_m = mat_principled('Glossy floor', (.012, .02, .03), rough=.18, metal=.2)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); floor = bpy.context.object; floor.data.materials.append(floor_m)


def area_light(name, loc, energy, size, color=(1, 1, 1)):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.size = size; d.color = color
    o = link(bpy.data.objects.new(name, d)); o.location = loc
    o.rotation_euler = (Vector((0, 0, 1.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o


for x0 in (0, 40):
    area_light('Key', (x0 - 4, -5, 7), 900, 5, (1, .95, .9))
    area_light('Rim', (x0 + 4, 4, 5), 700, 4, (.6, .8, 1))


def beam(name, pts, radius, color, strength, x0):
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '3D'; c.bevel_depth = radius; c.bevel_resolution = 4
    sp = c.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, (x, z) in zip(sp.points, pts): p.co = (x0 + x, 0, z, 1)
    o = link(bpy.data.objects.new(name, c))
    o.data.materials.append(mat_principled(name + ' glow', color, emit=color, strength=strength))
    c.bevel_factor_end = 0.0; return o


def grow(o, f, frame):
    o.data.bevel_factor_end = max(0.0, min(1.0, f)); o.data.keyframe_insert('bevel_factor_end', frame=frame)


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


glass = mat_principled('Optical glass', (.92, .97, 1.0), rough=.02, transmission=1.0, ior=1.5)

# ---------------- SHOT 1: prism (x = 0) ----------------
verts = [(-1.0, -.6, .02), (1.0, -.6, .02), (0, -.6, 1.75), (-1.0, .6, .02), (1.0, .6, .02), (0, .6, 1.75)]
faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
me = bpy.data.meshes.new('Prism'); me.from_pydata(verts, [], faces); me.update()
prism = link(bpy.data.objects.new('Prism', me)); prism.data.materials.append(glass)
bev = prism.modifiers.new('Bevel', 'BEVEL'); bev.width = .04; bev.segments = 3
white_in = beam('White light', [(-4.5, .55), (-.48, 1.02)], .05, (1, 1, 1), 18, 0)
inner = beam('Inside', [(-.48, 1.02), (.46, .98)], .035, (1, 1, 1), 8, 0)
SPEC = [(.55, .15, 1), (.3, .2, 1), (.1, .45, 1), (.1, 1, .25), (1, .95, .1), (1, .45, .05), (1, .08, .05)]
spectrum = [beam('Colour %d' % i, [(.46, .98), (4.5, .25 + .17 * i)], .045, col, 14, 0) for i, col in enumerate(SPEC)]

# ---------------- SHOT 2: convex lens (x = 40) ----------------
X2 = 40
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0, location=(X2, 0, 1.5))
lens = bpy.context.object; lens.scale = (.22, .9, 1.25); lens.data.materials.append(glass)
for p in lens.data.polygons: p.use_smooth = True
F = 1.6
rays = []
for h in (-.75, 0, .75):
    z = 1.5 + h; end_x = 4.5; slope = (1.5 - z) / F
    rays.append(beam('Ray', [(-4.5, z), (0, z), (end_x, z + slope * end_x)], .04, (1, .85, .3), 16, X2))
focus_m = mat_principled('Focus', (1, .3, .2), emit=(1, .35, .2), strength=0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.12, location=(X2 + F, 0, 1.5)); focus = bpy.context.object; focus.data.materials.append(focus_m)
axis_m = mat_principled('Axis', (.5, .6, .7), emit=(.4, .55, .7), strength=.6)
ax = beam('Axis', [(-4.5, 1.5), (4.5, 1.5)], .008, (.4, .55, .7), .8, X2)

# ---------------- camera with push-in + depth of field ----------------
cam = link(bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))); sc.camera = cam
cam.data.lens = 35; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 2.2

for f in range(1, N + 1):
    shot = 0 if f <= SCENE_LEN else 1
    q = ((f - 1) % SCENE_LEN) / (SCENE_LEN - 1)
    x0 = 0 if shot == 0 else X2
    if shot == 0:
        grow(white_in, ease(q / .3), f); grow(inner, ease((q - .3) / .12), f)
        for i, s in enumerate(spectrum): grow(s, ease((q - .42 - i * .015) / .3), f)
        target = Vector((x0 + .4 * ease((q - .4) / .4), 0, 1.0))
        dist = 9.0 - 2.6 * ease((q - .35) / .5)          # push in when the colours burst out
    else:
        for i, r in enumerate(rays): grow(r, ease((q - i * .05) / .55), f)
        grow(ax, ease(q / .2), f)
        flash = ease((q - .55) / .1) * (1 - .6 * ease((q - .75) / .25))
        focus_m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 60 * flash
        focus_m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].keyframe_insert('default_value', frame=f)
        target = Vector((x0 + F * ease((q - .5) / .3), 0, 1.5))
        dist = 9.0 - 3.0 * ease((q - .45) / .45)
    cam.location = target + Vector((0, -dist, .9 + .25 * math.sin(q * math.pi)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.focus_distance = (target - cam.location).length
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    cam.data.dof.keyframe_insert('focus_distance', frame=f)

for o in [cam] + [x for x in bpy.data.objects if x.animation_data]:
    pass

# ---------------- compositor: fog glow so beams and focus bloom ----------------
sc.use_nodes = True
ct = sc.node_tree; ct.nodes.clear()
rl = ct.nodes.new('CompositorNodeRLayers'); gl = ct.nodes.new('CompositorNodeGlare'); comp = ct.nodes.new('CompositorNodeComposite')
gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'; gl.threshold = .8; gl.size = 8
ct.links.new(rl.outputs['Image'], gl.inputs['Image']); ct.links.new(gl.outputs['Image'], comp.inputs['Image'])

sc.render.image_settings.file_format = 'PNG'
sc.render.filepath = os.path.join(OUT, 'f_')
if os.getenv('OPTICS_STILLS'):
    for f in (int(x) for x in os.environ['OPTICS_STILLS'].split(',')):
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, 'still_%03d.png' % f); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print('OPTICS_DONE', flush=True)
