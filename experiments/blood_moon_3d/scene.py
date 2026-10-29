"""MinuteMe GS demo: why the Moon turns red in a lunar eclipse.
Fully procedural Blender (Cycles CPU) scene: no downloaded assets except the
Natural Earth land polygons already in the repo. Same file runs on a GitHub runner.

Run:  blender -b -t 0 --python scene.py
Env:  DEMO_ROOT (folder with timeline.json + textures)
      DEMO_FRAMES "a-b" or "a,b,c" (optional, for quick tests)
      DEMO_SAMPLES (default 32)
"""
import bpy, math, json, os
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view

R = Path(os.environ.get('DEMO_ROOT', Path(bpy.path.abspath('//')) if bpy.data.filepath else os.getcwd()))
TL = json.loads((R / 'timeline.json').read_text())
FPS = TL['fps']
LEN = [round(s['seconds'] * FPS) for s in TL['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]
N = sum(LEN)
SHOT = {s['id']: (START[i], LEN[i]) for i, s in enumerate(TL['scenes'])}

# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.getenv('DEMO_SAMPLES', '12'))
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
sc.cycles.transparent_max_bounces = 12; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 720, 1280, 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 0, N - 1
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.cycles.motion_blur_position = 'START'      # never blends across a camera cut
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.filepath = str(R / 'frames' / '####')
sc.view_settings.view_transform = 'AgX'
for look in ('AgX - Punchy', 'Punchy', 'None'):
    try: sc.view_settings.look = look; break
    except TypeError: pass

def ease(t): t = max(0., min(1., t)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def vlerp(a, b, t): return Vector(a).lerp(Vector(b), t)

def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); return m, nt, out

def no_shadow(o, diffuse=True):
    o.visible_shadow = False
    if not diffuse: o.visible_diffuse = False; o.visible_glossy = False

# ---------------------------------------------------------------- world: deep space + stars
w = bpy.data.worlds.new('Space'); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
wo = nt.nodes.new('ShaderNodeOutputWorld')
tc = nt.nodes.new('ShaderNodeTexCoord')
vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 260
nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.09
mr.inputs[3].default_value = 1; mr.inputs[4].default_value = 0
nt.links.new(vor.outputs['Distance'], mr.inputs[0])
pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 3
nt.links.new(mr.outputs[0], pw.inputs[0])
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
nt.links.new(tc.outputs['Generated'], nz.inputs['Vector'])
neb = nt.nodes.new('ShaderNodeValToRGB'); neb.color_ramp.elements[0].position = .55
neb.color_ramp.elements[0].color = (0.001, 0.0015, 0.004, 1); neb.color_ramp.elements[1].color = (0.018, 0.012, 0.05, 1)
nt.links.new(nz.outputs['Fac'], neb.inputs['Fac'])
star = nt.nodes.new('ShaderNodeMix'); star.data_type = 'RGBA'; star.blend_type = 'ADD'
nt.links.new(pw.outputs[0], star.inputs['Factor']); nt.links.new(neb.outputs['Color'], star.inputs[6])
star.inputs[7].default_value = (5, 5.2, 6, 1)
bg = nt.nodes.new('ShaderNodeBackground'); nt.links.new(star.outputs[2], bg.inputs['Color'])
lp = nt.nodes.new('ShaderNodeLightPath'); black = nt.nodes.new('ShaderNodeBackground'); black.inputs['Color'].default_value = (0, 0, 0, 1)
mix = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0]); nt.links.new(black.outputs[0], mix.inputs[1]); nt.links.new(bg.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], wo.inputs['Surface'])

# ---------------------------------------------------------------- Sun (visual) + sunlight
SUN_POS = Vector((-6.6, 0, 0))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.5, location=SUN_POS)
sun = bpy.context.object; sun.name = 'Sun'
m, t, out = node_mat('Sun plasma')
nz = t.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3; nz.inputs['Detail'].default_value = 8
ramp = t.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color = (1, .38, .05, 1); ramp.color_ramp.elements[1].color = (1, .92, .6, 1)
em = t.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 28
t.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); t.links.new(ramp.outputs['Color'], em.inputs['Color']); t.links.new(em.outputs[0], out.inputs[0])
sun.data.materials.append(m); no_shadow(sun, diffuse=False)
bpy.ops.object.shade_smooth()

bpy.ops.object.light_add(type='SUN', rotation=(0, -math.pi / 2, 0))
sunlight = bpy.context.object; sunlight.name = 'Sunlight'
sunlight.data.energy = 6.5; sunlight.data.angle = math.radians(1.2); sunlight.data.color = (1, .95, .88)

# faint fill so the night side is not pure black (reads better on a phone)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(70), 0, math.radians(30)))
fill = bpy.context.object; fill.data.energy = 0.05; fill.data.color = (.45, .6, 1)

# ---------------------------------------------------------------- Earth
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.5)
earth = bpy.context.object; earth.name = 'Earth'; bpy.ops.object.shade_smooth()
m, t, out = node_mat('Earth surface')
img = t.nodes.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(str(R / 'earth_color.png'))
wat = t.nodes.new('ShaderNodeTexImage'); wat.image = bpy.data.images.load(str(R / 'earth_water.png')); wat.image.colorspace_settings.name = 'Non-Color'
bsdf = t.nodes.new('ShaderNodeBsdfPrincipled')
rr = t.nodes.new('ShaderNodeMapRange'); rr.inputs[3].default_value = .85; rr.inputs[4].default_value = .32
t.links.new(img.outputs['Color'], bsdf.inputs['Base Color']); t.links.new(wat.outputs['Color'], rr.inputs[0])
t.links.new(rr.outputs[0], bsdf.inputs['Roughness']); t.links.new(bsdf.outputs[0], out.inputs[0])
earth.data.materials.append(m)

# clouds
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.52)
clouds = bpy.context.object; clouds.name = 'Clouds'; bpy.ops.object.shade_smooth(); no_shadow(clouds)
m, t, out = node_mat('Clouds'); m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else None
nz = t.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 4.5; nz.inputs['Detail'].default_value = 10; nz.inputs['Roughness'].default_value = .62
ramp = t.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = .52; ramp.color_ramp.elements[1].position = .7
tr = t.nodes.new('ShaderNodeBsdfTransparent'); dif = t.nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value = (.95, .96, 1, 1)
ms = t.nodes.new('ShaderNodeMixShader')
t.links.new(nz.outputs['Fac'], ramp.inputs['Fac']); t.links.new(ramp.outputs['Color'], ms.inputs[0])
t.links.new(tr.outputs[0], ms.inputs[1]); t.links.new(dif.outputs[0], ms.inputs[2]); t.links.new(ms.outputs[0], out.inputs[0])
clouds.data.materials.append(m)

# atmosphere: rim glow; blue on the day side, red at the terminator (sunset ring)
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=1.6)
atmo = bpy.context.object; atmo.name = 'Atmosphere'; bpy.ops.object.shade_smooth(); no_shadow(atmo, diffuse=False)
m, t, out = node_mat('Atmosphere glow')
lw = t.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .5
rim = t.nodes.new('ShaderNodeMath'); rim.operation = 'POWER'; rim.inputs[1].default_value = 3.2
t.links.new(lw.outputs['Facing'], rim.inputs[0])
geo = t.nodes.new('ShaderNodeNewGeometry')
dot = t.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'; dot.inputs[1].default_value = (-1, 0, 0)
t.links.new(geo.outputs['Normal'], dot.inputs[0])
lit = t.nodes.new('ShaderNodeMapRange'); lit.inputs[1].default_value = -.25; lit.inputs[2].default_value = .5
t.links.new(dot.outputs['Value'], lit.inputs[0])
col = t.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'
col.inputs[6].default_value = (1, .22, .03, 1); col.inputs[7].default_value = (.25, .58, 1, 1)
t.links.new(lit.outputs[0], col.inputs['Factor'])
redboost = t.nodes.new('ShaderNodeValue'); redboost.name = 'RingBoost'; redboost.outputs[0].default_value = 0
term = t.nodes.new('ShaderNodeMath'); term.operation = 'MULTIPLY'      # terminator band = 1-|lit-.33|
band = t.nodes.new('ShaderNodeMapRange'); band.inputs[1].default_value = .0; band.inputs[2].default_value = .45
band.inputs[3].default_value = 1; band.inputs[4].default_value = 0
ab = t.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
sub = t.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = .3
t.links.new(lit.outputs[0], sub.inputs[0]); t.links.new(sub.outputs[0], ab.inputs[0]); t.links.new(ab.outputs[0], band.inputs[0])
t.links.new(band.outputs[0], term.inputs[0]); t.links.new(redboost.outputs[0], term.inputs[1])
base = t.nodes.new('ShaderNodeMath'); base.operation = 'ADD'; base.inputs[1].default_value = .04
t.links.new(lit.outputs[0], base.inputs[0])
tot = t.nodes.new('ShaderNodeMath'); tot.operation = 'ADD'
t.links.new(base.outputs[0], tot.inputs[0]); t.links.new(term.outputs[0], tot.inputs[1])
st = t.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'
t.links.new(rim.outputs[0], st.inputs[0]); t.links.new(tot.outputs[0], st.inputs[1])
st2 = t.nodes.new('ShaderNodeMath'); st2.operation = 'MULTIPLY'; st2.inputs[1].default_value = 6
t.links.new(st.outputs[0], st2.inputs[0])
em = t.nodes.new('ShaderNodeEmission'); t.links.new(col.outputs[2], em.inputs['Color']); t.links.new(st2.outputs[0], em.inputs['Strength'])
tr = t.nodes.new('ShaderNodeBsdfTransparent'); add = t.nodes.new('ShaderNodeAddShader')
t.links.new(tr.outputs[0], add.inputs[0]); t.links.new(em.outputs[0], add.inputs[1]); t.links.new(add.outputs[0], out.inputs[0])
atmo.data.materials.append(m)
ATMO_BOOST = redboost

# ---------------------------------------------------------------- Moon
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.45)
moon = bpy.context.object; moon.name = 'Moon'; bpy.ops.object.shade_smooth()
m, t, out = node_mat('Moon regolith')
tc = t.nodes.new('ShaderNodeTexCoord')
vor = t.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 7; vor.feature = 'F1'
t.links.new(tc.outputs['Object'], vor.inputs['Vector'])
cr = t.nodes.new('ShaderNodeMapRange'); cr.inputs[1].default_value = .0; cr.inputs[2].default_value = .35
t.links.new(vor.outputs['Distance'], cr.inputs[0])
crf = t.nodes.new('ShaderNodeFloatCurve')
c = crf.mapping.curves[0]; c.points[0].location = (0, -.6); c.points[1].location = (1, 0)
c.points.new(.55, -.2); c.points.new(.8, .35); crf.mapping.update()
t.links.new(cr.outputs[0], crf.inputs['Value'])
nz = t.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.4; nz.inputs['Detail'].default_value = 4
t.links.new(tc.outputs['Object'], nz.inputs['Vector'])
maria = t.nodes.new('ShaderNodeValToRGB'); maria.color_ramp.elements[0].position = .45; maria.color_ramp.elements[1].position = .62
maria.color_ramp.elements[0].color = (.32, .32, .33, 1); maria.color_ramp.elements[1].color = (.62, .61, .6, 1)
t.links.new(nz.outputs['Fac'], maria.inputs['Fac'])
bump = t.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .6; bump.inputs['Distance'].default_value = .04
t.links.new(crf.outputs[0], bump.inputs['Height'])
bsdf = t.nodes.new('ShaderNodeBsdfPrincipled'); bsdf.inputs['Roughness'].default_value = .95
t.links.new(maria.outputs['Color'], bsdf.inputs['Base Color']); t.links.new(bump.outputs[0], bsdf.inputs['Normal'])
# eclipse glow: copper emission scaled by "Redness"
red = t.nodes.new('ShaderNodeValue'); red.name = 'Redness'; red.outputs[0].default_value = 0
tint = t.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'; tint.blend_type = 'MULTIPLY'; tint.inputs['Factor'].default_value = 1
t.links.new(maria.outputs['Color'], tint.inputs[6]); tint.inputs[7].default_value = (1, .16, .035, 1)
t.links.new(tint.outputs[2], bsdf.inputs['Emission Color'])
es = t.nodes.new('ShaderNodeMath'); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 1.15
t.links.new(red.outputs[0], es.inputs[0]); t.links.new(es.outputs[0], bsdf.inputs['Emission Strength'])
t.links.new(bsdf.outputs[0], out.inputs[0])
moon.data.materials.append(m)
MOON_RED = red

# red light refracted by Earth's atmosphere, linked to the Moon only
bpy.ops.object.light_add(type='POINT', location=(2.7, 0, 0))
redlight = bpy.context.object; redlight.name = 'Refracted red light'
redlight.data.color = (1, .22, .05); redlight.data.energy = 0; redlight.data.shadow_soft_size = .8
lc = bpy.data.collections.new('MoonOnly'); lc.objects.link(moon)
redlight.light_linking.receiver_collection = lc

# ---------------------------------------------------------------- Earth's umbra (teaching overlay in 3D)
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=1.5, radius2=.75, depth=9, location=(4.5, 0, 0), rotation=(0, math.pi / 2, 0))
umbra = bpy.context.object; umbra.name = 'Umbra'; no_shadow(umbra, diffuse=False); bpy.ops.object.shade_smooth()
m, t, out = node_mat('Umbra veil')
lw = t.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .35
em = t.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.55, .06, .04, 1); em.inputs['Strength'].default_value = .9
tr = t.nodes.new('ShaderNodeBsdfTransparent')
alpha = t.nodes.new('ShaderNodeValue'); alpha.name = 'Alpha'; alpha.outputs[0].default_value = 0
fa = t.nodes.new('ShaderNodeMath'); fa.operation = 'MULTIPLY'
t.links.new(lw.outputs['Fresnel'], fa.inputs[0]); t.links.new(alpha.outputs[0], fa.inputs[1])
ms = t.nodes.new('ShaderNodeMixShader')
t.links.new(fa.outputs[0], ms.inputs[0]); t.links.new(tr.outputs[0], ms.inputs[1]); t.links.new(em.outputs[0], ms.inputs[2]); t.links.new(ms.outputs[0], out.inputs[0])
umbra.data.materials.append(m)
UMBRA_A = alpha

# ---------------------------------------------------------------- light rays (scene 4)
def ray_mat(name, rgb, strength):
    m, t, out = node_mat(name)
    em = t.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*rgb, 1); em.inputs['Strength'].default_value = strength
    t.links.new(em.outputs[0], out.inputs[0]); return m
WHITE, BLUE, RED = ray_mat('White sunlight', (1, .93, .78), 4), ray_mat('Scattered blue', (.12, .38, 1), 3.2), ray_mat('Bent red', (1, .16, .02), 5)
def catmull(pts, n=12):
    P = [Vector(p) for p in pts]; P = [P[0]] + P + [P[-1]]; out = []
    for i in range(1, len(P) - 2):
        for k in range(n):
            s = k / n; p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s * s + (-p0 + 3 * p1 - 3 * p2 + p3) * s ** 3))
    out.append(P[-2]); return out
RAYS = []
def ray(name, pts, mat, width, grow):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = width; cu.bevel_resolution = 3
    cu.bevel_factor_mapping_end = 'SPLINE'; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); P = catmull(pts); sp.points.add(len(P) - 1)
    for i, p in enumerate(P): sp.points[i].co = (*p, 1)
    o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o); o.data.materials.append(mat); no_shadow(o, diffuse=False)
    cu.bevel_factor_end = 0; RAYS.append((cu, grow)); return o
s0, _ = SHOT['rays']
for sgn in (1, -1):
    for j, off in enumerate((0, .16)):
        ray(f'in{sgn}{j}', [(-9.2, -.05, sgn * (1.25 + off)), (-4, -.05, sgn * (1.45 + off)), (-.25, -.05, sgn * (1.6 + off))], WHITE, .028, (s0 + 6 + j * 4, s0 + 40 + j * 4))
        # red keeps going, bending inwards to the Moon
        ray(f'red{sgn}{j}', [(-.25, -.05, sgn * (1.6 + off)), (1.0, -.05, sgn * (1.5 + off * .6)), (2.7, -.05, sgn * (1.0 + off * .3)), (4.3, -.05, sgn * (.18 + off * .2))], RED, .034, (s0 + 70 + j * 5, s0 + 120 + j * 5))
    for k, ang in enumerate((35, 70, 110, 150, 200)):
        a = math.radians(ang) * (1 if sgn > 0 else -1); o = Vector((-.25, -.05, sgn * 1.62))
        d = Vector((math.sin(a) * .9 - .4, -.05, math.cos(a))).normalized()
        ray(f'blue{sgn}{k}', [o, o + d * .9, o + d * 1.9 + Vector((0, 0, .15 * sgn))], BLUE, .02, (s0 + 44 + k * 3, s0 + 66 + k * 3))
for cu, (a, b) in RAYS:
    for f, v in ((SHOT['rays'][0] - 1, 0), (a, 0), (b, 1)):
        cu.bevel_factor_end = v; cu.keyframe_insert('bevel_factor_end', frame=f)
    e = SHOT['ring'][0]                      # rays hidden after their scene
    cu.bevel_factor_end = 1; cu.keyframe_insert('bevel_factor_end', frame=e - 1)
    cu.bevel_factor_end = 0; cu.keyframe_insert('bevel_factor_end', frame=e)

# ---------------------------------------------------------------- animation helpers
def key_value(node, frames_vals):
    for f, v in frames_vals:
        node.outputs[0].default_value = v; node.outputs[0].keyframe_insert('default_value', frame=f)

H0, A0, S0, Y0, G0, Q0 = (SHOT[k][0] for k in ('hook', 'align', 'shadow', 'rays', 'ring', 'quiz'))
H1, A1, S1, Y1, G1, Q1 = (SHOT[k][0] + SHOT[k][1] for k in ('hook', 'align', 'shadow', 'rays', 'ring', 'quiz'))

def moon_pos(f):
    if f < A0: return Vector((4.6, 0, lerp(2.3, .35, ease((f - H0) / 70))))
    if f < S0: return Vector((4.6, 0, lerp(2.45, 2.3, (f - A0) / (A1 - A0))))
    if f < Y0: return Vector((4.6, 0, lerp(2.3, 0, ease((f - S0) / 112))))
    return Vector((4.6, 0, 0))
def moon_red(f):
    if f < A0: return ease((f - 34) / 44)
    if f < S0: return 0
    if f < Y0: return ease((f - (S0 + 82)) / 50)
    return 1

# ---------------------------------------------------------------- camera
cam_data = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'; cam_data.sensor_fit = 'VERTICAL'; cam_data.sensor_height = 24
cam_data.clip_start = .05; cam_data.clip_end = 200

def look(pos, target, up):
    f = (Vector(target) - Vector(pos)).normalized(); r = f.cross(Vector(up)).normalized(); u = r.cross(f)
    return Matrix((r, u, -f)).transposed().to_quaternion()

def shot(f):
    """returns pos, target, up, lens, focus_object, fstop for a frame"""
    M = moon_pos(f)
    if f < A0:
        k = ease((f - H0) / (H1 - H0)); return M + vlerp((-3.4, -3.1, .6), (-2.7, -2.5, .4), k), M + Vector((0, 0, .05)), (0, 0, 1), 45, 'Moon', 2.4
    if f < S0:
        k = ease((f - A0) / (A1 - A0)); return vlerp((.3, -22, 1.0), (.3, -21, .5), k), (.3, 0, .6), (-1, 0, 0), 30, None, 0
    if f < Y0:
        k = ease((f - S0) / (S1 - S0)); return vlerp((.3, -21, .5), (1.6, -14, .4), k), vlerp((.3, 0, .6), (2.0, 0, .35), k), (-1, 0, 0), 30, None, 0
    if f < G0:
        k = ease((f - Y0) / (Y1 - Y0)); return vlerp((1.0, -17.5, .3), (1.0, -16, .1), k), vlerp((1.0, 0, 0), (1.0, 0, 0), k), (-1, 0, 0), 30, None, 0
    if f < Q0:
        k = ease((f - G0) / (G1 - G0)); return vlerp((13.6, -.35, -.3), (12.6, -.28, -.22), k), (0, 0, .05), (0, 0, 1), 52, 'Earth', 3.2
    k = ease((f - Q0) / (Q1 - Q0)); return M + vlerp((-1.6, -4.4, 1.0), (-1.2, -3.7, .8), k), M + Vector((0, 0, .6)), (0, 0, 1), 45, 'Moon', 2.4

ends = {A0 - 1, S0 - 1, Y0 - 1, G0 - 1, Q0 - 1}
prevq = None
for f in range(0, N):
    p, tg, up, lens, foc, fst = shot(f)
    q = look(p, tg, up)
    if prevq is not None and q.dot(prevq) < 0: q.negate()
    prevq = q
    cam.location = p; cam.rotation_quaternion = q; cam_data.lens = lens
    cam_data.dof.use_dof = bool(foc)
    if foc:
        cam_data.dof.focus_distance = (Vector(p) - (moon_pos(f) if foc == 'Moon' else Vector((0, 0, 0)))).length - (.45 if foc == 'Moon' else 1.5)
        cam_data.dof.aperture_fstop = fst
    for path in ('location', 'rotation_quaternion'): cam.keyframe_insert(path, frame=f)
    cam_data.keyframe_insert('lens', frame=f); cam_data.dof.keyframe_insert('use_dof', frame=f)
    cam_data.dof.keyframe_insert('focus_distance', frame=f); cam_data.dof.keyframe_insert('aperture_fstop', frame=f)
    moon.location = moon_pos(f); moon.keyframe_insert('location', frame=f)
    moon.hide_render = G0 <= f < Q0; moon.keyframe_insert('hide_render', frame=f)   # ring shot = view from the Moon
    r = moon_red(f)
    MOON_RED.outputs[0].default_value = r; MOON_RED.outputs[0].keyframe_insert('default_value', frame=f)
    redlight.data.energy = 140 * r; redlight.data.keyframe_insert('energy', frame=f)
    ua = 0 if f < S0 + 8 else min(1, (f - S0 - 8) / 30) if f < Y0 + 40 else max(0, 1 - (f - Y0 - 40) / 20)
    UMBRA_A.outputs[0].default_value = ua * .55; UMBRA_A.outputs[0].keyframe_insert('default_value', frame=f)
    rb = 0 if f < G0 else 2.2 * ease((f - G0) / 40)
    ATMO_BOOST.outputs[0].default_value = rb; ATMO_BOOST.outputs[0].keyframe_insert('default_value', frame=f)
    earth.rotation_euler = (0, 0, math.radians(-115 + f * .06)); earth.keyframe_insert('rotation_euler', frame=f)
    clouds.rotation_euler = (0, 0, math.radians(-115 + f * .09)); clouds.keyframe_insert('rotation_euler', frame=f)
    sun.rotation_euler = (0, 0, f * .004); sun.keyframe_insert('rotation_euler', frame=f)

# per-frame keys -> linear; the last frame of each shot holds (no blur across cuts)
def fix_fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action: return
    fcs = ad.action.fcurves if hasattr(ad.action, 'fcurves') else [fc for l in ad.action.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = 'CONSTANT' if int(kp.co.x) in ends else 'LINEAR'
for idb in (cam, cam_data, moon, redlight.data, earth, clouds, sun) + tuple(bpy.data.materials) + tuple(bpy.data.curves):
    fix_fcurves(idb)
for mt in bpy.data.materials:
    if mt.node_tree: fix_fcurves(mt.node_tree)

# emissive props are visuals, not lights: skipping them as light sources is the big speed win
for mt in bpy.data.materials:
    try: mt.cycles.emission_sampling = 'NONE'
    except AttributeError: pass
sc.cycles.use_light_tree = False

# ---------------------------------------------------------------- compositor glow
sc.use_nodes = True
ct = sc.node_tree; ct.nodes.clear()
rl = ct.nodes.new('CompositorNodeRLayers'); comp = ct.nodes.new('CompositorNodeComposite')
gl = ct.nodes.new('CompositorNodeGlare'); gl.glare_type = 'FOG_GLOW'; gl.quality = 'HIGH'
try: gl.threshold = 1.0; gl.size = 8; gl.mix = -.35
except AttributeError:
    for k, v in (('Threshold', 1.0), ('Strength', .65), ('Size', .6)):
        if k in gl.inputs: gl.inputs[k].default_value = v
ct.links.new(rl.outputs['Image'], gl.inputs['Image']); ct.links.new(gl.outputs['Image'], comp.inputs['Image'])

# ---------------------------------------------------------------- export 2D pins for the overlay
pins = []
for f in range(N):
    sc.frame_set(f); row = {}
    for o in (sun, earth, moon):
        v = world_to_camera_view(sc, cam, o.matrix_world.translation)
        row[o.name.lower()] = [round(v.x * 720, 1), round((1 - v.y) * 1280, 1), round(v.z, 2)]
    pins.append(row)
(R / 'pins.json').write_text(json.dumps(pins))

bpy.ops.wm.save_as_mainfile(filepath=str(R / 'blood_moon.blend'), compress=True)
frames = os.getenv('DEMO_FRAMES')
(R / 'frames').mkdir(exist_ok=True)
if frames:
    sel = []
    for part in frames.split(','):
        a, _, b = part.partition('-'); sel += list(range(int(a), int(b or a) + 1))
    for f in sel:
        sc.frame_set(f); sc.render.filepath = str(R / 'frames' / f'{f:04d}'); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print('DONE frames', N)
