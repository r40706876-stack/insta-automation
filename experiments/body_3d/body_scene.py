"""Human-body reel renderer. Everything topic-specific comes from a topic JSON (see topics/).
Run: blender -b -t 0 --python body_scene.py
Env: BODY_ROOT  folder with body_assets.blend, organ_index.json
     TOPIC      path to topic json
     OUT        output folder (frames/, pins.json)
     DEMO_FRAMES "a-b" / "a,b,c" / "none"   (optional subset)
     DEMO_SAMPLES (default 12)"""
import bpy, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

R = Path(os.environ.get('BODY_ROOT', Path(__file__).parent))
TOP = json.loads(Path(os.environ['TOPIC']).read_text(encoding='utf-8'))
OUT = Path(os.environ.get('OUT', R / 'out')); (OUT / 'frames').mkdir(parents=True, exist_ok=True)
IDX = json.loads((R / 'organ_index.json').read_text(encoding='utf-8'))
FPS = TOP.get('fps', 24)
LEN = [round(s['seconds'] * FPS) for s in TOP['scenes']]
START = [sum(LEN[:i]) for i in range(len(LEN))]; N = sum(LEN)
ENDS = {s + l - 1 for s, l in zip(START, LEN)}

bpy.ops.wm.open_mainfile(filepath=str(R / 'body_assets.blend'))
sc = bpy.context.scene
OBJ = {o.name: o for o in sc.objects if o.type == 'MESH'}
LAYER_OF = {k: v['src'] for k, v in IDX.items()}
LAYER_OF.update({'skin': 'skin'})

# ------------------------------------------------------------- render settings
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = int(os.getenv('DEMO_SAMPLES', '12')); sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = .03
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPENIMAGEDENOISE'
sc.cycles.max_bounces = 6; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 12; sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.cycles.use_light_tree = False
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 720, 1280, int(os.getenv('BODY_RES_PCT', '100'))
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, N - 1
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
sc.view_settings.view_transform = os.getenv('BODY_VIEW', 'Standard'); sc.view_settings.look = 'None'; sc.view_settings.exposure = float(os.getenv('BODY_EXPOSURE', '-0.6'))
for m in bpy.data.materials: m.cycles.emission_sampling = 'NONE'

# ------------------------------------------------------------- world + lights (studio, dark navy)
w = bpy.data.worlds.new('Studio'); sc.world = w; w.use_nodes = True
nt = w.node_tree; nt.nodes.clear()
wo = nt.nodes.new('ShaderNodeOutputWorld'); tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
nt.links.new(tc.outputs['Generated'], sep.inputs[0])
ramp = nt.nodes.new('ShaderNodeValToRGB'); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
ramp.color_ramp.elements[0].position = .35; ramp.color_ramp.elements[0].color = (.002, .006, .014, 1)
ramp.color_ramp.elements[1].position = .75; ramp.color_ramp.elements[1].color = (.012, .03, .06, 1)
bg = nt.nodes.new('ShaderNodeBackground'); nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
lp = nt.nodes.new('ShaderNodeLightPath'); amb = nt.nodes.new('ShaderNodeBackground'); amb.inputs['Color'].default_value = (.03, .045, .07, 1)
mx = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0])
nt.links.new(amb.outputs[0], mx.inputs[1]); nt.links.new(bg.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], wo.inputs['Surface'])

def area(loc, energy, size, color, target=(0, 0, 1.25)):
    bpy.ops.object.light_add(type='AREA', location=loc); l = bpy.context.object
    l.data.energy = energy; l.data.size = size; l.data.color = color
    l.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return l
area((-1.3, -1.8, 2.0), 260, 1.6, (1, .95, .9)); area((1.5, .9, 1.7), 200, 1.0, (.45, .72, 1)); area((0, -1.5, .2), 60, 2, (.9, .8, 1))

# ------------------------------------------------------------- helpers
def ease(t): t = max(0., min(1., t)); return t * t * (3 - 2 * t)
def bbox(keys):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for k in keys:
        b = IDX[k]; lo = Vector(map(min, lo, b['min'])); hi = Vector(map(max, hi, b['max']))
    return lo, hi
ORIGIN_OF = {'artery': 'heart', 'vein': 'heart', 'heart': 'heart', 'pulmonary': 'heart', 'nerve': 'brain', 'cord': 'brain', 'brain': 'brain',
             'brain2': 'brain', 'digestive': 'tongue', 'digestive2': 'tongue', 'liver': 'tongue', 'bile': 'liver', 'gland': 'tongue',
             'airway': 'larynx', 'lung': 'larynx', 'kidney': 'kidneys', 'urine': 'kidneys'}
for k, o in OBJ.items():
    org = ORIGIN_OF.get(IDX.get(k, {}).get('class'))
    if org and org in IDX:
        lo, hi = bbox([org]); c = (lo + hi) / 2
        o['flow_x'], o['flow_y'], o['flow_z'] = c.x, c.y, c.z

# clock for travelling pulses
clk = bpy.data.node_groups['Clock'].nodes['T']
for f, v in ((0, 0.), (N, N / FPS)):
    clk.outputs[0].default_value = v; clk.outputs[0].keyframe_insert('default_value', frame=f)

# ------------------------------------------------------------- camera
cd = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cam.rotation_mode = 'QUATERNION'; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24; cd.clip_start = .01; cd.shift_y = .045
ANG = {'front': 0, 'three_quarter': 35, 'three_quarter_left': -35, 'side': 90, 'side_left': -90, 'back': 180}
WIDE = {'viscera_other', 'bones', 'nerves', 'arteries', 'veins', 'skin'}   # catch-all groups: too big to frame
HEAD = {'brain', 'cerebellum', 'eyes', 'tongue', 'teeth', 'skull', 'pharynx', 'larynx', 'ear_bones', 'thyroid'}
def scene_focus(s, idx):
    cam = s.get('camera', {}); keys = [k for k in cam.get('focus', []) if k in IDX and k not in WIDE]
    seq = next((e.split(':', 1)[1].split(',') for e in s.get('effects', []) if e.startswith('sequence:')), [])
    talk = [l if isinstance(l, str) else l['key'] for l in s.get('labels', [])] + seq + s.get('solid', [])
    talk = [k for k in talk if k in IDX and k != 'skin']
    if (idx == 0 or not keys) and talk and not (set(keys) & set(talk[:2])): keys = talk[:2]   # hook / vague focus: frame the organ being talked about          # hook: start close on the organ
    return keys or ['skin']
def cam_pose(spec, k, keys=None):
    keys = keys or spec.get('focus') or ['skin']
    lo, hi = bbox(keys); ctr = (lo + hi) / 2; size = hi - lo
    lens = spec.get('lens', 50); vf = 2 * math.atan(12 / lens); hf = 2 * math.atan(math.tan(vf / 2) * 720 / 1280)
    ang = math.radians(ANG.get(spec.get('angle', 'front'), 0)); mv = spec.get('move', 'push')
    if mv == 'orbit': ang += math.radians(lerp(-14, 14, k))
    width = abs(size.x * math.cos(ang)) + abs(size.y * math.sin(ang))
    d = max(size.z / 2 / math.tan(vf / 2 * .5), width / 2 / math.tan(hf / 2 * .72)) / spec.get('zoom', 1.0)
    d += (abs(size.y * math.cos(ang)) + abs(size.x * math.sin(ang))) / 2
    d *= {'push': lerp(1.1, .94, k), 'pull': lerp(.94, 1.1, k)}.get(mv, 1.0)
    d = max(d, .25)
    lift = {'rise': lerp(-.04, .04, k), 'down': lerp(.04, -.04, k)}.get(mv, 0) * max(size.z, .2) * 2
    pos = ctr + Vector((math.sin(ang) * d, -math.cos(ang) * d, .06 * d + lift))
    tgt = ctr + Vector((0, 0, lift))
    return pos, tgt, lens
def lerp(a, b, t): return a + (b - a) * t
def look(pos, tgt):
    f = (tgt - pos).normalized(); r = f.cross(Vector((0, 0, 1))).normalized(); u = r.cross(f)
    return Matrix((r, u, -f)).transposed().to_quaternion()

# ------------------------------------------------------------- per-frame state from the topic
def scene_at(f):
    for i in range(len(START) - 1, -1, -1):
        if f >= START[i]: return i, (f - START[i]) / max(1, LEN[i] - 1)
def heartbeat(t):                       # ~72 bpm, sharp systole
    ph = (t * 1.2) % 1; return math.exp(-((ph - .1) / .06) ** 2) + .45 * math.exp(-((ph - .32) / .07) ** 2)

prevq = None
_last = {}
def setk(idb, path, value, f):
    key = (idb.name_full if hasattr(idb, 'name_full') else id(idb), path)
    old = _last.get(key)
    if old is not None and old[1] == value: return
    if old is not None and old[0] < f - 1:          # hold the previous value until the frame before
        _apply(idb, path, old[1]); idb.keyframe_insert(path, frame=f - 1)
    _apply(idb, path, value); idb.keyframe_insert(path, frame=f); _last[key] = (f, value)
def _apply(idb, path, v):
    if path.startswith('["'): idb[path[2:-2]] = v
    else: setattr(idb, path, v)
CAM_ROWS = []
FOCUS = [scene_focus(s, i) for i, s in enumerate(TOP['scenes'])]
def hits(lo, hi, p0, p1):                       # segment p0->p1 vs axis-aligned box (slab test)
    t0, t1 = 0., .92
    for ax in range(3):
        d = p1[ax] - p0[ax]
        if abs(d) < 1e-9:
            if not lo[ax] <= p0[ax] <= hi[ax]: return False
            continue
        a_, b_ = (lo[ax] - p0[ax]) / d, (hi[ax] - p0[ax]) / d
        t0, t1 = max(t0, min(a_, b_)), min(t1, max(a_, b_))
        if t0 > t1: return False
    return True
OCCL = []
for i, s in enumerate(TOP['scenes']):
    pos, tgt, _ = cam_pose(s.get('camera', {}), .5, FOCUS[i]); keep = set(FOCUS[i]) | set(s.get('solid', [])) | {l if isinstance(l, str) else l['key'] for l in s.get('labels', [])}
    occ = set()
    if FOCUS[i] != ['skin']:
        for key in OBJ:
            if key in keep or key == 'skin' or key not in IDX: continue
            b = IDX[key]
            if hits(Vector(b['min']), Vector(b['max']), pos, tgt): occ.add(key)
    OCCL.append(occ)
for f in range(N):
    i, k = scene_at(f); s = TOP['scenes'][i]; t = f / FPS; age = (f - START[i]) / FPS
    layers = set(s.get('layers', ['skin', 'visceral', 'cardio']))
    solid = set(s.get('solid', [])); labels = {l if isinstance(l, str) else l['key'] for l in s.get('labels', [])}
    effects = s.get('effects', [])
    seq = next((e.split(':', 1)[1].split(',') for e in effects if e.startswith('sequence:')), [])
    flows = {e.split(':', 1)[1] for e in effects if e.startswith('flow:')}
    hidden = set(s.get('hide', []))
    for key, o in OBJ.items():
        lay = LAYER_OF.get(key, 'skin'); vis = lay in layers and key not in hidden

        if key == 'skin': g = (.0 if not solid else .35) if not (set(FOCUS[i]) & HEAD) else .62
        elif key in OCCL[i] and key not in seq: g = .93
        elif solid and key not in solid and key not in seq:
            g = .95 if IDX.get(key, {}).get('class') in ('artery', 'vein', 'nerve', 'pulmonary', 'bone') else .85
        else: g = 0.
        hl = 0.
        if key in labels: hl = .55 + .25 * math.sin(age * 4)
        if key in seq:
            j = seq.index(key); win = 1 / len(seq); on = ease((k - j * win) / (win * .5))
            hl = max(hl, on * (1.3 if k < (j + 1) * win else .5)); g = 0.
        if g >= .9: vis = False                       # fully faded organs are skipped, not rendered transparent
        setk(o, 'hide_render', not vis, f)
        fl = 1. if (key in flows or IDX.get(key, {}).get('class') in flows) else 0.
        setk(o, '["ghost"]', round(g, 3), f); setk(o, '["hl"]', round(hl, 3), f); setk(o, '["flow"]', fl, f)
    # organ motion
    if 'heart' in OBJ:
        b = 1 + (.07 * heartbeat(t) if 'beat' in effects else 0)
        setk(OBJ['heart'], 'scale', (round(b, 4),) * 3, f)
    if 'lungs' in OBJ:
        br = .5 - .5 * math.cos(2 * math.pi * t / 3.6) if 'breathe' in effects else 0
        setk(OBJ['lungs'], 'scale', (round(1 + .05 * br, 4), round(1 + .04 * br, 4), round(1 + .06 * br, 4)), f)
    cs = dict(s.get('camera', {}))
    if i == 0 and FOCUS[i] != (cs.get('focus') or ['skin']): cs['zoom'] = max(cs.get('zoom', 1), 1.15)
    pos, tgt, lens = cam_pose(cs, ease(k), FOCUS[i])
    q = look(pos, tgt)
    if prevq is not None and q.dot(prevq) < 0: q.negate()
    CAM_ROWS.append((pos.copy(), q.copy(), lens))
    prevq = q; cam.location = pos; cam.rotation_quaternion = q; cd.lens = lens
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_quaternion', frame=f); cd.keyframe_insert('lens', frame=f)

def fix(idb):
    ad = getattr(idb, 'animation_data', None)
    if not ad or not ad.action: return
    fcs = ad.action.fcurves if hasattr(ad.action, 'fcurves') else [fc for l in ad.action.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT' if int(kp.co.x) in ENDS else 'LINEAR'
for x in list(OBJ.values()) + [cam, cd, bpy.data.node_groups['Clock']]: fix(x)

# ------------------------------------------------------------- 2D pins for overlay labels
label_keys = sorted({(l if isinstance(l, str) else l['key']) for s in TOP['scenes'] for l in s.get('labels', [])})
pins = []
for f in range(N):
    pos, q, lens = CAM_ROWS[f]; row = {}; inv = q.inverted(); vh = 12 / lens; hh = vh * 720 / 1280
    for key in label_keys:
        if key not in OBJ: continue
        pc = inv @ (OBJ[key].matrix_world.translation - pos)
        if pc.z >= 0: row[key] = [0, 0, -1]; continue
        x = pc.x / -pc.z / hh; y = (pc.y / -pc.z - cd.shift_y * 2 * vh) / vh
        row[key] = [round(360 + x * 360, 1), round(640 - y * 640, 1), round(-pc.z, 3)]
    pins.append(row)
(OUT / 'pins.json').write_text(json.dumps(pins))

sel = os.getenv('DEMO_FRAMES')
if sel == 'none': raise SystemExit(0)
frames = []
if sel:
    for part in sel.split(','):
        a, _, b = part.partition('-'); frames += list(range(int(a), int(b or a) + 1))
else: frames = list(range(N))
for f in frames:
    sc.frame_set(f); sc.render.filepath = str(OUT / 'frames' / f'{f:04d}'); bpy.ops.render.render(write_still=True)
print('DONE', len(frames))
