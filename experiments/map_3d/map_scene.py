"""3D India map reel scene (Blender Cycles). Reads a plan from make_plan.py.
Env: TOPIC=plan.json  OUT=dir  MAP_ROOT=this folder  DEMO_FRAMES=comma list (default all)
     DEMO_SAMPLES (16)  MAP_RES_PCT (100)
Writes OUT/frames/NNNN.png and OUT/pins.json (screen position of every label, every frame)."""
import bpy, json, math, os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

PLAN = json.load(open(os.environ['TOPIC'], encoding='utf-8'))
ROOT = os.environ.get('MAP_ROOT', os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ['OUT']; os.makedirs(OUT + '/frames', exist_ok=True)
FPS = PLAN['fps']
LEN = [round(s['seconds'] * FPS) for s in PLAN['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]
N = sum(LEN)
STATES = json.load(open(ROOT + '/india_states.json', encoding='utf-8'))['states']
RIV = json.load(open(ROOT + '/rivers.json', encoding='utf-8'))['rivers']
K, COSL, H = .25, .93, .07


def X(lon): return (lon - 82.5) * K * COSL
def Y(lat): return (lat - 22.5) * K
def P(p, z=H + .015): return Vector((X(p[0]), Y(p[1]), z))
def hexc(h): h = h.lstrip('#'); return tuple((int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4))
def fr(scene_i, t): return START[scene_i] + round(t * FPS)


bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.getenv('DEMO_SAMPLES', '16')); sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 0
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.render.resolution_percentage = int(os.getenv('MAP_RES_PCT', '100'))
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, N - 1
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'Medium High Contrast'; sc.view_settings.exposure = -.35
sc.render.image_settings.file_format = 'PNG'


def material(name, color, rough=.6, emit=None, strength=0.0, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Emission Color'].default_value = (*(emit or color), 1); b.inputs['Emission Strength'].default_value = strength
    return m


def bsdf(m): return m.node_tree.nodes['Principled BSDF']
def key_input(m, name, value, frame):
    i = bsdf(m).inputs[name]; i.default_value = value; i.keyframe_insert('default_value', frame=frame)


def link(o): bpy.context.collection.objects.link(o); return o


# ------------------------------------------------------------------ world, sea, light
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; nt = w.node_tree
nt.nodes['Background'].inputs['Color'].default_value = (.010, .025, .05, 1); nt.nodes['Background'].inputs['Strength'].default_value = .9
sea = material('Sea', hexc('#0d3557'), rough=.32)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); bpy.context.object.data.materials.append(sea)
sun = link(bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')))
sun.data.energy = 2.4; sun.data.angle = math.radians(4); sun.rotation_euler = (math.radians(38), math.radians(-22), math.radians(-30))
fill = link(bpy.data.objects.new('Fill', bpy.data.lights.new('Fill', 'AREA')))
fill.data.energy = 1200; fill.data.size = 20; fill.location = (0, -6, 14); fill.data.color = (.75, .85, 1)


def fill_curve(name, rings, mat, depth, z0, extrude=True):
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '2D'; c.fill_mode = 'BOTH'
    if extrude: c.extrude = depth / 2
    for ring in rings:
        sp = c.splines.new('POLY'); sp.points.add(len(ring) - 1)
        for v, p in zip(sp.points, ring): v.co = (X(p[0]), Y(p[1]), 0, 1)
        sp.use_cyclic_u = True
    o = link(bpy.data.objects.new(name, c)); o.location.z = z0; c.materials.append(mat); return o


def outline(name, rings, mat, radius, parent, z):
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '3D'; c.bevel_depth = radius; c.bevel_resolution = 1
    for ring in rings:
        sp = c.splines.new('POLY'); sp.points.add(len(ring))
        for v, p in zip(sp.points, list(ring) + [ring[0]]): v.co = (X(p[0]), Y(p[1]), 0, 1)
    o = link(bpy.data.objects.new(name, c)); o.parent = parent; o.location.z = z; c.materials.append(mat); return o


def clip(ring, x0, y0, x1, y1):
    """Sutherland-Hodgman clip of a lon/lat ring to a box (no chords across the frame)."""
    pts = [p[:2] for p in ring]
    for inside_, cut in ((lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
                         (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
                         (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
                         (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside_(b):
                if not inside_(a): out.append(cut(a, b))
                out.append(b)
            elif inside_(a): out.append(cut(a, b))
        pts = out
        if not pts: break
    return pts


# neighbouring land (context only, low and dark)
land = material('Neighbour land', hexc('#2b3a47'), rough=.85)
wl = json.load(open(ROOT + '/world_land.json'))
rings = []
for f in wl['features']:
    g = f['geometry']
    for poly in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]):
        r = clip(poly[0], 52, -2, 112, 44)
        if len(r) > 3: rings.append(r)
fill_curve('Neighbours', rings, land, .02, .012)

# Indian states: raised tiles, four-colour-ish palette so neighbours never share a colour
PAL = ['#f2cf86', '#9fd4b0', '#f4ab90', '#bfaee3', '#94cbe6', '#e6c39c']
def near(a, b):
    sa = [p for r in a['rings'] for p in r[::6]]; sb = [p for r in b['rings'] for p in r[::6]]
    return any(abs(p[0] - q[0]) < .12 and abs(p[1] - q[1]) < .12 for p in sa for q in sb)
order = sorted(range(len(STATES)), key=lambda i: -sum(len(r) for r in STATES[i]['rings']))
colour = {}
for i in order:
    used = {colour[j] for j in colour if near(STATES[i], STATES[j])}
    colour[i] = next((c for c in range(len(PAL)) if c not in used), i % len(PAL))
border = material('Border', hexc('#ffffff'), rough=.5, emit=hexc('#ffffff'), strength=.35)
STATE_OBJ, STATE_MAT = {}, {}
for i, st in enumerate(STATES):
    m = material('State ' + st['name'], hexc(PAL[colour[i]]), rough=.62)
    o = fill_curve('State ' + st['name'], st['rings'], m, H, H / 2)
    outline('Border ' + st['name'], st['rings'], border, .0045, o, H / 2 + .001)
    STATE_OBJ[st['name']] = o; STATE_MAT[st['name']] = m
    cx = sum(p[0] for r in st['rings'] for p in r) / sum(len(r) for r in st['rings'])
    cy = sum(p[1] for r in st['rings'] for p in r) / sum(len(r) for r in st['rings'])
    st['_c'] = (cx, cy)


# lakes / reservoirs (real shapes) sit on top of the state that holds them; others (Tibet) float on neighbour land
lake_m = material('Lake', hexc('#2f7fb8'), rough=.18, emit=hexc('#4aa3df'), strength=.25)
LAKES = json.load(open(ROOT + '/lakes.json', encoding='utf-8'))['lakes'] if os.path.exists(ROOT + '/lakes.json') else []
def _inside(p, ring):
    x, y = p; c = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1], ring[i]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
for lk in LAKES:
    r0 = lk['rings'][0]; c_ = (sum(p[0] for p in r0) / len(r0), sum(p[1] for p in r0) / len(r0))
    host = next((st['name'] for st in STATES if any(_inside(c_, r) for r in st['rings'])), None)
    o = fill_curve('Lake ' + lk['name'], lk['rings'], lake_m, .004, 0)
    if host: o.parent = STATE_OBJ[host]; o.location.z = H / 2 + .003
    else: o.location.z = .025


def set_build(o, s, frame):
    o.scale.z = max(.02, s); o.location.z = H / 2 * max(.02, s)
    o.keyframe_insert('scale', index=2, frame=frame); o.keyframe_insert('location', index=2, frame=frame)


# ------------------------------------------------------------------ rivers
RIV_OBJ, RIV_MAT = {}, {}
def river_curve(name, path, color, radius, z, strength):
    c = bpy.data.curves.new(name, 'CURVE'); c.dimensions = '3D'; c.bevel_depth = radius; c.bevel_resolution = 3
    c.use_fill_caps = True; c.bevel_factor_mapping_end = 'SPLINE'
    sp = c.splines.new('POLY'); sp.points.add(len(path) - 1)
    for v, p in zip(sp.points, path): v.co = (X(p[0]), Y(p[1]), z, 1)
    m = material(name + ' glow', hexc(color), rough=.3, emit=hexc(color), strength=strength)
    o = link(bpy.data.objects.new(name, c)); c.materials.append(m); c.bevel_factor_end = 0; return o, m


for r in PLAN.get('rivers', []):
    o, m = river_curve('River ' + r['key'], RIV[r['key']]['path'], r['color'], .03, H + .018, 1.6)
    RIV_OBJ[r['key']] = o; RIV_MAT[r['key']] = m
    o.data.keyframe_insert('bevel_factor_end', frame=0)
ans = PLAN.get('answer_river')
trail = trail_m = dot = None
if ans:
    trail, trail_m = river_curve('Gold trail', RIV[ans]['path'], '#ffc93c', .042, H + .03, 3)
    trail.data.keyframe_insert('bevel_factor_end', frame=0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.075, segments=24, ring_count=12); dot = bpy.context.object
    dot.data.materials.append(material('Travel dot', hexc('#fff3c4'), emit=hexc('#ffe08a'), strength=14))
    dot.scale = (0, 0, 0); dot.keyframe_insert('scale', frame=0)

# ------------------------------------------------------------------ pin + ripple
def make_pin(at, color='#ff3b3b'):
    pn = link(bpy.data.objects.new('Pin', None))
    red = material('Pin ' + color, hexc(color), rough=.25, emit=hexc(color), strength=.8)
    bpy.ops.mesh.primitive_cone_add(radius1=.0, radius2=.085, depth=.28, location=(0, 0, .14)); cone = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.11, location=(0, 0, .32)); head = bpy.context.object
    for o in (cone, head): o.data.materials.append(red); o.parent = pn; bpy.ops.object.shade_smooth()
    b = P(at, H * 1.65); pn.location = b + Vector((0, 0, 6)); pn.keyframe_insert('location', frame=0)
    pn.scale = (0, 0, 0); pn.keyframe_insert('scale', frame=0); return pn, b


RIPPLES = []
def ripple(at, f0, color='#ff6b6b'):
    c = bpy.data.curves.new('Ripple', 'CURVE'); c.dimensions = '3D'; c.bevel_depth = .012
    sp = c.splines.new('POLY'); sp.points.add(47)
    for k, v in enumerate(sp.points): a = 2 * math.pi * k / 47; v.co = (math.cos(a) * .3, math.sin(a) * .3, 0, 1)
    m = material('Ripple', (0, 0, 0), emit=hexc(color), strength=0)
    o = link(bpy.data.objects.new('Ripple', c)); c.materials.append(m); o.location = P(at, H + .006)
    for f, s, e in ((0, .001, 0), (f0, .05, 0), (f0 + 1, .1, 5), (f0 + 24, 1.6, 0), (f0 + 25, .001, 0)):
        o.scale = (s, s, 1); o.keyframe_insert('scale', frame=f); key_input(m, 'Emission Strength', e, f)


# ------------------------------------------------------------------ actions (keyframes)
def ease(x): x = max(0., min(1., x)); return x * x * (3 - 2 * x)


STATE_ON = {}
BASE_COL = {n: tuple(bsdf(m).inputs['Base Color'].default_value[:3]) for n, m in STATE_MAT.items()}
for si, s in enumerate(PLAN['scenes']):
    for a in s.get('actions', []):
        f0 = fr(si, a.get('t', 0))
        if a['type'] == 'build':
            # tiles rise from the sea outward from the centre (staggered by distance)
            for st in STATES:
                d = math.hypot(st['_c'][0] - 80, st['_c'][1] - 22) / 18
                fa = f0 + round(d * .55 * a['dur'] * FPS); fb = fa + round(.45 * a['dur'] * FPS)
                set_build(STATE_OBJ[st['name']], .02, 0); set_build(STATE_OBJ[st['name']], .02, fa); set_build(STATE_OBJ[st['name']], 1, fb)
        elif a['type'] == 'pin':
            pin, base = make_pin(a['at'], a.get('color', '#ff3b3b'))
            pin.scale = (0, 0, 0); pin.keyframe_insert('scale', frame=f0 - 1); pin.scale = (1, 1, 1); pin.keyframe_insert('scale', frame=f0)
            pin.location = base + Vector((0, 0, 6)); pin.keyframe_insert('location', frame=f0)
            pin.location = base; pin.keyframe_insert('location', frame=f0 + 9)
            pin.location = base + Vector((0, 0, .18)); pin.keyframe_insert('location', frame=f0 + 13)
            pin.location = base; pin.keyframe_insert('location', frame=f0 + 17)
            ripple(a['at'], f0 + 9, a.get('color', '#ff6b6b'))
        elif a['type'] == 'ripple':
            ripple(a['at'], f0)
        elif a['type'] == 'river':
            o = RIV_OBJ[a['key']]; o.data.bevel_factor_end = 0; o.data.keyframe_insert('bevel_factor_end', frame=f0)
            o.data.bevel_factor_end = 1; o.data.keyframe_insert('bevel_factor_end', frame=f0 + round(a['dur'] * FPS))
        elif a['type'] == 'river_hide':
            o = RIV_OBJ[a['key']]; o.data.bevel_factor_end = 1; o.data.keyframe_insert('bevel_factor_end', frame=f0)
            o.data.bevel_factor_end = 0; o.data.keyframe_insert('bevel_factor_end', frame=f0 + 5)
        elif a['type'] == 'river_focus':
            for k, o in RIV_OBJ.items():
                m = RIV_MAT[k]
                key_input(m, 'Emission Strength', 1.6, f0)
                if k == a['key']:
                    key_input(m, 'Emission Strength', 3.5, f0 + 10)
                    o.data.bevel_depth = .03; o.data.keyframe_insert('bevel_depth', frame=f0)
                    o.data.bevel_depth = .04; o.data.keyframe_insert('bevel_depth', frame=f0 + 10)
                else:
                    key_input(m, 'Emission Strength', .12, f0 + 10)
                    key_input(m, 'Base Color', (*bsdf(m).inputs['Base Color'].default_value[:3], 1), f0)
                    key_input(m, 'Base Color', (.08, .1, .12, 1), f0 + 10)
        elif a['type'] == 'travel' and trail:
            f1 = f0 + round(a['dur'] * FPS); path = RIV[a['key']]['path']
            seg = [math.hypot(b[0] - q[0], b[1] - q[1]) for q, b in zip(path, path[1:])]; tot = sum(seg)
            trail.data.bevel_factor_end = 0; trail.data.keyframe_insert('bevel_factor_end', frame=f0)
            for f in range(f0, f1 + 1):
                u = (f - f0) / max(1, f1 - f0); u = u * u * (3 - 2 * u) * .15 + u * .85   # gentle ease, steady middle
                trail.data.bevel_factor_end = u; trail.data.keyframe_insert('bevel_factor_end', frame=f)
                goal = u * tot
                for idx, ((q, b), L) in enumerate(zip(zip(path, path[1:]), seg)):
                    if goal <= L or idx == len(seg) - 1:
                        t = min(1, goal / L) if L else 0; pt = (q[0] + t * (b[0] - q[0]), q[1] + t * (b[1] - q[1])); break
                    goal -= L
                dot.location = P(pt, H + .05); dot.keyframe_insert('location', frame=f)
            dot.scale = (0, 0, 0); dot.keyframe_insert('scale', frame=f0 - 1)
            dot.scale = (1, 1, 1); dot.keyframe_insert('scale', frame=f0 + 4)
            dot.keyframe_insert('scale', frame=f1)
            dot.scale = (0, 0, 0); dot.keyframe_insert('scale', frame=f1 + 12)
        elif a['type'] == 'state_on':
            m = STATE_MAT[a['name']]; o = STATE_OBJ[a['name']]
            key_input(m, 'Base Color', (*bsdf(m).inputs['Base Color'].default_value[:3], 1), f0)
            key_input(m, 'Base Color', (*hexc(a.get('color', '#ffb347')), 1), f0 + 8)
            key_input(m, 'Emission Color', (*bsdf(m).inputs['Emission Color'].default_value[:3], 1), f0)
            key_input(m, 'Emission Color', (*hexc(a.get('color', '#ffb347')), 1), f0 + 8)
            key_input(m, 'Emission Strength', 0, f0); key_input(m, 'Emission Strength', a.get('glow', .25), f0 + 8)
            hi_ = a.get('raise', 1.6)
            for f, s_ in ((f0, 1), (f0 + 8, hi_ * 1.35), (f0 + 20, hi_)): set_build(o, s_, f)
            STATE_ON[a['name']] = hi_
        elif a['type'] == 'state_off':
            m = STATE_MAT[a['name']]; o = STATE_OBJ[a['name']]
            key_input(m, 'Base Color', (*bsdf(m).inputs['Base Color'].default_value[:3], 1), f0)
            key_input(m, 'Base Color', (*BASE_COL[a['name']], 1), f0 + 8)
            key_input(m, 'Emission Strength', bsdf(m).inputs['Emission Strength'].default_value, f0); key_input(m, 'Emission Strength', 0, f0 + 8)
            set_build(o, STATE_ON.get(a['name'], 1), f0); set_build(o, 1, f0 + 8); STATE_ON[a['name']] = 1

# ------------------------------------------------------------------ camera (every frame, smooth hand-offs)
cam = link(bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))); sc.camera = cam
cam.data.lens = 35; cam.data.sensor_fit = 'AUTO'; cam.data.clip_end = 200


def cam_state(c, t_in_scene, seconds, first):
    cx, cy = c['center']; span = c['span']; tilt = c['tilt']; yaw = c.get('yaw', 0)
    drift = t_in_scene / max(seconds, .1)
    span = span * (1 - .05 * drift); yaw = yaw * drift
    if first and 'from_tilt' in c:
        k = ease(t_in_scene / 1.6); tilt = c['from_tilt'] + (tilt - c['from_tilt']) * k; span = c['from_span'] + (span - c['from_span']) * k
    return [cx, cy, span, tilt, yaw]


def place_cam(v, f):
    cx, cy, span, tilt, yaw = v
    T = Vector((X(cx), Y(cy), 0)); D = span * K * COSL / .578
    th, ph = math.radians(tilt), math.radians(yaw)
    cam.location = T + Vector((D * math.sin(th) * math.sin(ph), -D * math.sin(th) * math.cos(ph), D * math.cos(th)))
    cam.rotation_euler = (T - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)


prev = None
for si, s in enumerate(PLAN['scenes']):
    for k in range(LEN[si]):
        t = k / FPS; v = cam_state(s['cam'], t, s['seconds'], si == 0)
        if prev is not None and t < 1.0:
            e = ease(t / 1.0); v = [p + (q - p) * e for p, q in zip(prev, v)]
        place_cam(v, START[si] + k)
    prev = cam_state(s['cam'], s['seconds'], s['seconds'], si == 0)
for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR' if o == cam or o == dot else 'BEZIER'

# ------------------------------------------------------------------ label screen positions (for compose)
def label_spot(rings):
    """Point inside the state + usable width: widest horizontal run through the biggest ring, tried at a few latitudes."""
    ring = max(rings, key=len); ys = [p[1] for p in ring]; best = None
    for fy in (.5, .4, .6, .3, .7):
        y = min(ys) + (max(ys) - min(ys)) * fy; xs = []
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
            if (y1 > y) != (y2 > y): xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            if best is None or b - a > best[2] - best[1]: best = (y, a, b)
    return best


SPOT = {st['name']: label_spot(st['rings']) for st in STATES}
STATIC = [('अरब सागर', 66.0, 15.0), ('बंगाल की खाड़ी', 88.8, 15.5), ('हिंद महासागर', 79.5, 3.5), ('पाकिस्तान', 69.0, 28.6),
          ('नेपाल', 83.6, 28.3), ('चीन', 86.0, 33.0), ('बांग्लादेश', 90.2, 23.6), ('श्रीलंका', 80.7, 7.7), ('म्यांमार', 96.0, 21.5)]
HI = {st['name']: st['hindi'] for st in STATES}
pins = []
deps = bpy.context.evaluated_depsgraph_get()
for f in range(N):
    sc.frame_set(f); d = {}
    for si, s in enumerate(PLAN['scenes']):
        if not START[si] <= f < START[si] + LEN[si]: continue
        for li, lab in enumerate(s.get('labels', [])):
            z = H + (.45 if lab.get('kind') == 'pin' else .03)
            v = world_to_camera_view(sc, cam, P(lab['at'], z))
            d[f'{si}:{li}'] = [round(v.x * 720, 1), round((1 - v.y) * 1280, 1), round(v.z, 3)]
    sts = []
    for name, sp in SPOT.items():
        if not sp: continue
        y, a, b = sp; z = H * STATE_OBJ[name].scale.z + .004
        va = world_to_camera_view(sc, cam, Vector((X(a), Y(y), z))); vb = world_to_camera_view(sc, cam, Vector((X(b), Y(y), z)))
        vm = world_to_camera_view(sc, cam, Vector((X((a + b) / 2), Y(y), z)))
        if vm.z <= 0 or not (0 < vm.x < 1 and 0 < vm.y < 1): continue
        sts.append([HI[name], round(vm.x * 720, 1), round((1 - vm.y) * 1280, 1), round(abs(vb.x - va.x) * 720, 1)])
    d['_states'] = sts
    stat = []
    for txt, lon, lat in STATIC:
        v = world_to_camera_view(sc, cam, Vector((X(lon), Y(lat), .03)))
        if v.z > 0 and 0 < v.x < 1 and 0 < v.y < 1: stat.append([txt, round(v.x * 720, 1), round((1 - v.y) * 1280, 1)])
    d['_static'] = stat
    pins.append(d)
json.dump(pins, open(OUT + '/pins.json', 'w'))

# ------------------------------------------------------------------ render
frames = [int(x) for x in os.getenv('DEMO_FRAMES', '').split(',') if x.strip()] or list(range(N))
for f in frames:
    sc.frame_set(f); sc.render.filepath = f'{OUT}/frames/{f:04d}.png'
    bpy.ops.render.render(write_still=True); print('Saved', f, flush=True)
print('DONE', len(frames), 'frames of', N, flush=True)
