"""3D vertical timeline reel scene (Blender Cycles) for year PYQs. Plan from make_plan.py timeline.
Env as map_scene.py. Writes OUT/frames/NNNN.png and OUT/pins.json."""
import bpy, json, math, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

PLAN = json.load(open(os.environ['TOPIC'], encoding='utf-8'))
OUT = os.environ['OUT']; os.makedirs(OUT + '/frames', exist_ok=True)
FPS = PLAN['fps']
LEN = [round(s['seconds'] * FPS) for s in PLAN['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]
N = sum(LEN)
GAP, Z0 = 1.3, .7


def hexc(h): h = h.lstrip('#'); return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))
def fr(si, t): return START[si] + round(t * FPS)
def ease(x): x = max(0., min(1., x)); return x * x * (3 - 2 * x)
def link(o): bpy.context.collection.objects.link(o); return o


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.getenv('DEMO_SAMPLES', '16')); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 4; sc.cycles.transmission_bounces = 0
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.render.resolution_percentage = int(os.getenv('MAP_RES_PCT', '100'))
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, N - 1
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'; sc.view_settings.exposure = -.2
sc.render.image_settings.file_format = 'PNG'


def material(name, color, rough=.5, emit=None, strength=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    b.inputs['Emission Color'].default_value = (*(emit or color), 1); b.inputs['Emission Strength'].default_value = strength
    return m


def bsdf(m): return m.node_tree.nodes['Principled BSDF']
def key_input(m, name, value, frame):
    i = bsdf(m).inputs[name]; i.default_value = value; i.keyframe_insert('default_value', frame=frame)


# ------------------------------------------------------------------ stage
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs['Color'].default_value = (.008, .02, .045, 1)
floor = material('Floor', hexc('#0b1a2b'), rough=.42, metal=.2)
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); bpy.context.object.data.materials.append(floor)
for name, loc, energy, col in (('Key', (-5, -7, 9), 2600, (1, .95, .9)), ('Rim', (6, 5, 7), 1800, (.55, .75, 1))):
    L = link(bpy.data.objects.new(name, bpy.data.lights.new(name, 'AREA'))); L.data.energy = energy; L.data.size = 6; L.data.color = col; L.visible_glossy = False
    L.location = loc; L.rotation_euler = (Vector((0, 0, 2.5)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
# glowing grid lines on the floor for depth
grid = material('Grid', (0, 0, 0), emit=hexc('#1d5f86'), strength=1.2)
for k in range(-8, 9):
    for horiz in (0, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0 if horiz else k * 1.5, k * 1.5 if horiz else 0, .002))
        o = bpy.context.object; o.scale = (24, .012, .002) if horiz else (.012, 24, .002); o.data.materials.append(grid)

pole_m = material('Pole', (0, 0, 0), emit=hexc('#5fd3ff'), strength=4)
bpy.ops.mesh.primitive_cylinder_add(radius=.05, depth=1, location=(0, .35, 0)); pole = bpy.context.object; pole.data.materials.append(pole_m)
TOP = Z0 + GAP * 3 + 1.0
pole.scale.z = .001; pole.keyframe_insert('scale', frame=0)


def plate(year, color, name):
    root = link(bpy.data.objects.new(name, None))
    body = material(name + ' body', hexc('#13263b'), rough=.3, metal=.2)
    bpy.ops.mesh.primitive_cube_add(size=1); b = bpy.context.object; b.scale = (2.7, .32, .92); b.parent = root
    bev = b.modifiers.new('Bevel', 'BEVEL'); bev.width = .07; bev.segments = 3; b.data.materials.append(body)
    edge_m = material(name + ' edge', hexc(color), emit=hexc(color), strength=3)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-1.25, -.17, 0)); e = bpy.context.object; e.scale = (.12, .04, .78); e.parent = root; e.data.materials.append(edge_m)
    txt_m = material(name + ' text', hexc('#ffffff'), emit=hexc('#ffffff'), strength=1.4)
    c = bpy.data.curves.new(name + ' year', 'FONT'); c.body = str(year); c.align_x = 'CENTER'; c.align_y = 'CENTER'; c.size = .66; c.extrude = .04
    t = link(bpy.data.objects.new(name + ' year', c)); t.parent = root; t.location = (.12, -.2, 0); t.rotation_euler = (math.pi / 2, 0, 0)
    c.materials.append(txt_m)
    return {'root': root, 'body': body, 'edge': edge_m, 'text': txt_m}


def place(o, loc, frame, scale=None):
    o.location = loc; o.keyframe_insert('location', frame=frame)
    if scale is not None: o.scale = (scale,) * 3; o.keyframe_insert('scale', frame=frame)


years = PLAN['years']; cols = PLAN['option_colors']; slots = {int(k): v for k, v in PLAN['slots_opt'].items()}
PL = {i: plate(y, cols[i], f'Plate {i}') for i, y in enumerate(years)}
for i, p in PL.items(): place(p['root'], (9 if slots[i] % 2 else -9, 0, Z0 + GAP * slots[i]), 0, 1)
chain = PLAN['chain']; ans_i = PLAN['answer']; ans_y = PLAN['answer_year']
AN = {a['year']: plate(a['year'], '#9fb3c8', f'Anchor {a["year"]}') for a in PLAN['anchors']}
CH_Z = {y: Z0 + .65 + GAP * 1.15 * k for k, y in enumerate(chain)}
for y, p in AN.items(): place(p['root'], (0, 6, CH_Z[y]), 0, .001)
dot_m = material('Dot', hexc('#fff3c4'), emit=hexc('#ffd25c'), strength=16)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.13); dot = bpy.context.object; dot.data.materials.append(dot_m)
place(dot, (0, .35, CH_Z[chain[0]]), 0, .001)

for si, s in enumerate(PLAN['scenes']):
    for a in s['actions']:
        f0 = fr(si, a.get('t', 0))
        if a['type'] == 'pole':
            pole.scale.z = .001; pole.location.z = 0; pole.keyframe_insert('scale', frame=f0); pole.keyframe_insert('location', frame=f0)
            f1 = f0 + round(a['dur'] * FPS); pole.scale.z = TOP; pole.location.z = TOP / 2
            pole.keyframe_insert('scale', frame=f1); pole.keyframe_insert('location', frame=f1)
        elif a['type'] == 'plate_in':
            i = a['i']; r = PL[i]['root']; side = 9 if slots[i] % 2 else -9
            place(r, (side, 0, Z0 + GAP * slots[i]), f0)
            place(r, (0, 0, Z0 + GAP * slots[i]), f0 + 12)
        elif a['type'] == 'focus':
            for i, p in PL.items():
                r = p['root']; z = Z0 + GAP * slots[i]
                if i == ans_i:
                    place(r, (0, 0, z), f0, 1); place(r, (0, -.7, z), f0 + 10, 1.18)
                    for m, v in ((p['edge'], hexc('#ffd25c')), (p['text'], hexc('#ffe9a6'))):
                        key_input(m, 'Emission Color', (*bsdf(m).inputs['Emission Color'].default_value[:3], 1), f0)
                        key_input(m, 'Emission Color', (*v, 1), f0 + 10)
                    key_input(p['text'], 'Emission Strength', 1.4, f0); key_input(p['text'], 'Emission Strength', 5, f0 + 10)
                    key_input(p['body'], 'Base Color', (*bsdf(p['body']).inputs['Base Color'].default_value[:3], 1), f0)
                    key_input(p['body'], 'Base Color', (*hexc('#5a4310'), 1), f0 + 10)
                else:
                    place(r, (0, 0, z), f0, 1); place(r, (3.2 * (1 if slots[i] % 2 else -1), 1.6, z - .3), f0 + 14, .8)
                    key_input(p['text'], 'Emission Strength', 1.4, f0); key_input(p['text'], 'Emission Strength', .15, f0 + 14)
                    key_input(p['edge'], 'Emission Strength', 3, f0); key_input(p['edge'], 'Emission Strength', .2, f0 + 14)
        elif a['type'] == 'chain':
            for i, p in PL.items():
                r = p['root']; z = Z0 + GAP * slots[i]
                if i == ans_i: place(r, (0, -.7, z), f0, 1.18); place(r, (0, -.4, CH_Z[ans_y]), f0 + 16, 1.05)
                else: place(r, (3.2 * (1 if slots[i] % 2 else -1), 1.6, z - .3), f0, .8); place(r, (6 * (1 if slots[i] % 2 else -1), 7, z - 2), f0 + 14, .001)
        elif a['type'] == 'anchor_in':
            r = AN[a['year']]['root']; place(r, (0, 6, CH_Z[a['year']]), f0, .001); place(r, (0, 0, CH_Z[a['year']]), f0 + 12, .9)
        elif a['type'] == 'travel':
            f1 = f0 + round(a['dur'] * FPS); zs = [CH_Z[y] for y in chain]
            place(dot, (0, .35, zs[0]), f0 - 1, .001); place(dot, (0, .35, zs[0]), f0 + 3, 1)
            for f in range(f0 + 3, f1 + 1):
                u = ease((f - f0 - 3) / max(1, f1 - f0 - 3)); z = zs[0] + (zs[-1] - zs[0]) * u
                dot.location = (0, .35, z); dot.keyframe_insert('location', frame=f)
            place(dot, (0, .35, zs[-1]), f1 + 10, .001)

# ------------------------------------------------------------------ camera
cam = link(bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))); sc.camera = cam
cam.data.lens = 35; cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0


def cam_state(c, t, seconds, first):
    z, span, elev, yaw = c['z'], c['span'], c['elev'], c['yaw']
    drift = t / max(seconds, .1); span *= (1 - .06 * drift); yaw += 6 * drift
    if first and 'from_yaw' in c:
        k = ease(t / 1.8); yaw = c['from_yaw'] + (yaw - c['from_yaw']) * k; span = c['from_span'] + (span - c['from_span']) * k
    return [z, span, elev, yaw]


def place_cam(v, f):
    z, span, elev, yaw = v; T = Vector((0, 0, z)); D = span / .579
    e, y_ = math.radians(elev), math.radians(yaw)
    cam.location = T + Vector((D * math.cos(e) * math.sin(y_), -D * math.cos(e) * math.cos(y_), D * math.sin(e)))
    cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.dof.focus_distance = D
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f); cam.data.dof.keyframe_insert('focus_distance', frame=f)


prev = None
for si, s in enumerate(PLAN['scenes']):
    for k in range(LEN[si]):
        t = k / FPS; v = cam_state(s['cam'], t, s['seconds'], si == 0)
        if prev is not None and t < 1.0: e = ease(t); v = [p + (q - p) * e for p, q in zip(prev, v)]
        place_cam(v, START[si] + k)
    prev = cam_state(s['cam'], s['seconds'], s['seconds'], si == 0)
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR' if o in (cam, dot) else 'BEZIER'

# ------------------------------------------------------------------ label positions
pins = []
for f in range(N):
    sc.frame_set(f); d = {}
    for si, s in enumerate(PLAN['scenes']):
        if not START[si] <= f < START[si] + LEN[si]: continue
        for li, lab in enumerate(s.get('labels', [])):
            if 'plate' in lab: r = PL[lab['plate']]['root']; local = Vector((-1.62, -.2, 0))
            else:
                r = AN[lab['year']]['root'] if lab['year'] in AN else PL[ans_i]['root']; local = Vector((1.62, -.2, 0))
            v = world_to_camera_view(sc, cam, r.matrix_world @ local)
            d[f'{si}:{li}'] = [round(v.x * 720, 1), round((1 - v.y) * 1280, 1), round(v.z, 3)]
    pins.append(d)
json.dump(pins, open(OUT + '/pins.json', 'w'))

frames = [int(x) for x in os.getenv('DEMO_FRAMES', '').split(',') if x.strip()] or list(range(N))
for f in frames:
    sc.frame_set(f); sc.render.filepath = f'{OUT}/frames/{f:04d}.png'
    bpy.ops.render.render(write_still=True); print('Saved', f, flush=True)
print('DONE', len(frames), 'frames of', N, flush=True)
