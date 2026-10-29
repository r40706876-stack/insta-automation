"""One-time asset build: Z-Anatomy FBX -> body_assets.blend (one object per organ key, shared materials).
Run: blender -b -t 0 --python prepare_assets.py   (env ZA_DIR = folder with the FBX files)
The output is cached on GitHub, so this runs only when this script or organs.json changes."""
import bpy, os, json, re
from pathlib import Path
from mathutils import Vector

R = Path(os.environ.get('BODY_ROOT', Path(__file__).parent))
ZA = Path(os.environ.get('ZA_DIR', '/tmp/za/Resources/Models/FBX'))
CAT = json.loads((R / 'organs.json').read_text(encoding='utf-8'))
SRC = {'visceral': 'VisceralSystem100.fbx', 'cardio': 'CardioVascular41.fbx', 'nervous': 'NervousSystem100.fbx',
       'skeletal': 'SkeletalSystem100.fbx', 'skin': 'Regions of human body100.fbx'}
EXCL = CAT['exclude_any']; KEEP = set(CAT['keep_suffix'])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ------------------------------------------------------------- shared materials
COL = {'heart': (.6, .045, .04), 'artery': (.8, .035, .03), 'vein': (.08, .16, .7), 'pulmonary': (.45, .2, .75),
       'lung': (.88, .46, .5), 'airway': (.88, .82, .72), 'digestive': (.9, .55, .45), 'digestive2': (.78, .48, .36),
       'liver': (.42, .08, .06), 'bile': (.22, .55, .18), 'gland': (.92, .62, .18), 'kidney': (.52, .12, .09),
       'urine': (.88, .76, .28), 'brain': (.86, .6, .6), 'brain2': (.78, .48, .55), 'cord': (.92, .86, .7),
       'nerve': (.98, .8, .22), 'eye': (.93, .93, .96), 'bone': (.87, .83, .73), 'tooth': (.96, .96, .92), 'other': (.8, .6, .5)}
FLOW = {'artery': 1, 'heart': 1, 'pulmonary': 1, 'vein': -1, 'nerve': 1, 'cord': 1, 'brain': 1}   # +1 outward, -1 inward

def clock_group():
    g = bpy.data.node_groups.new('Clock', 'ShaderNodeTree')
    g.interface.new_socket('T', in_out='OUTPUT', socket_type='NodeSocketFloat')
    v = g.nodes.new('ShaderNodeValue'); v.name = 'T'; o = g.nodes.new('NodeGroupOutput'); g.links.new(v.outputs[0], o.inputs[0]); return g
CLOCK = clock_group()

def organ_material(cls):
    m = bpy.data.materials.new('M_' + cls); m.use_nodes = True; t = m.node_tree; N = t.nodes; L = t.links; N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    def attr(name):
        a = N.new('ShaderNodeAttribute'); a.attribute_type = 'OBJECT'; a.attribute_name = name; return a.outputs['Fac']
    def math(op, a, b):
        n = N.new('ShaderNodeMath'); n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)): n.inputs[i].default_value = x
            else: L.new(x, n.inputs[i])
        return n.outputs[0]
    c = COL[cls]
    b = N.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = (*c, 1)
    b.inputs['Roughness'].default_value = .42 if cls not in ('bone', 'tooth') else .55
    b.inputs['Subsurface Weight'].default_value = 0.0   # SSS is the slowest part of CPU rendering; sheen fakes the soft look
    b.inputs['Sheen Weight'].default_value = .0 if cls in ('bone', 'tooth') else .25; b.inputs['Sheen Tint'].default_value = (1, .75, .7, 1)
    b.inputs['Subsurface Radius'].default_value = (.5, .12, .07); b.inputs['Subsurface Scale'].default_value = .008
    b.inputs['Coat Weight'].default_value = .3; b.inputs['Coat Roughness'].default_value = .25
    # highlight: rim glow driven by object property "hl"
    fr = N.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = .35
    rim = math('ADD', math('MULTIPLY', fr.outputs['Facing'], 1.6), .12)
    glow = math('MULTIPLY', rim, attr('hl'))
    # flow: travelling pulse = distance from origin (object prop flow_x/y/z) minus time
    geo = N.new('ShaderNodeNewGeometry'); comb = N.new('ShaderNodeCombineXYZ')
    for i, ax in enumerate('xyz'): L.new(attr('flow_' + ax), comb.inputs[i])
    dist = N.new('ShaderNodeVectorMath'); dist.operation = 'DISTANCE'; L.new(geo.outputs['Position'], dist.inputs[0]); L.new(comb.outputs[0], dist.inputs[1])
    clk = N.new('ShaderNodeGroup'); clk.node_tree = CLOCK
    phase = math('SUBTRACT', math('MULTIPLY', dist.outputs['Value'], 14.0), math('MULTIPLY', clk.outputs[0], 9.0 * FLOW.get(cls, 1)))
    wave = math('POWER', math('MULTIPLY', math('ADD', math('SINE', phase, 0), 1), .5), 10)
    flow = math('MULTIPLY', wave, math('MULTIPLY', attr('flow'), 4.0))
    em = math('ADD', glow, flow)
    glowcol = tuple(min(1, x * 1.35) for x in c)
    b.inputs['Emission Color'].default_value = (*glowcol, 1); L.new(em, b.inputs['Emission Strength'])
    # ghost: 0 = solid, 1 = invisible
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
    L.new(attr('ghost'), mx.inputs[0]); L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    return m

def skin_material():
    m = bpy.data.materials.new('M_skin'); m.use_nodes = True; t = m.node_tree; N = t.nodes; L = t.links; N.clear()
    out = N.new('ShaderNodeOutputMaterial'); lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = .22
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.4; L.new(lw.outputs['Facing'], pw.inputs[0])
    a = N.new('ShaderNodeAttribute'); a.attribute_type = 'OBJECT'; a.attribute_name = 'ghost'
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L.new(a.outputs['Fac'], inv.inputs[1])
    f = N.new('ShaderNodeMath'); f.operation = 'MULTIPLY'; L.new(pw.outputs[0], f.inputs[0]); L.new(inv.outputs[0], f.inputs[1])
    em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (.32, .72, 1, 1); em.inputs['Strength'].default_value = 1.5
    tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
    L.new(f.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs[0])
    m.cycles.emission_sampling = 'NONE'; return m

MATS = {c: organ_material(c) for c in COL}; MATS['skin'] = skin_material()

# ------------------------------------------------------------- import + classify + join
def classify(name, src):
    n = name.lower()
    for o in CAT['organs']:
        if o['src'] == src and any(k in n for k in o['any']): return o
info = {}
for src, fn in SRC.items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(ZA / fn))
    new = [o for o in bpy.data.objects if o not in before]
    groups = {}
    for o in new:
        name = re.sub(r'\.\d{3}$', '', o.name)
        base, suf = name.rsplit('.', 1) if '.' in name else (name, '')
        if o.type != 'MESH' or suf not in KEEP or any(x in name.lower() for x in EXCL) or len(o.data.vertices) < 12:
            continue
        org = classify(base, src)
        if org: groups.setdefault(org['key'], (org, []))[1].append(o)
    keep = {id(o) for _, objs in groups.values() for o in objs}
    bpy.context.view_layer.update()
    world = {id(o): o.matrix_world.copy() for _, objs in groups.values() for o in objs}
    for _, objs in groups.values():
        for o in objs: o.parent = None; o.matrix_world = world[id(o)]
    for o in new:
        if id(o) not in keep: bpy.data.objects.remove(o, do_unlink=True)
    col = bpy.data.collections.new(src); sc.collection.children.link(col)
    bpy.context.view_layer.update()
    for key, (org, objs) in groups.items():
        for o in objs:
            for uc in o.users_collection: uc.objects.unlink(o)
            col.objects.link(o); mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
            o.data.materials.clear(); o.data.materials.append(MATS[org['class']])
            for p in o.data.polygons: p.use_smooth = True
        with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs, object=objs[0]):
            bpy.ops.object.join()
        j = objs[0]; j.name = key; j.data.name = key
        with bpy.context.temp_override(active_object=j, selected_editable_objects=[j], selected_objects=[j], object=j):
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        for p in ('hl', 'ghost', 'flow', 'flow_x', 'flow_y', 'flow_z'): j[p] = 0.0
        if org['class'] == 'skin': j.visible_shadow = False
        bb = [j.matrix_world @ Vector(c) for c in j.bound_box]
        info[key] = {'src': src, 'class': org['class'], 'hi': org['hi'], 'verts': len(j.data.vertices),
                     'min': [round(min(v[i] for v in bb), 4) for i in range(3)], 'max': [round(max(v[i] for v in bb), 4) for i in range(3)]}
        print('organ', key, info[key]['verts'])
for o in list(bpy.data.objects):
    if o.type != 'MESH': bpy.data.objects.remove(o, do_unlink=True)
for b in (bpy.data.meshes, bpy.data.materials):
    for x in list(b):
        if x.users == 0: b.remove(x)
(R / 'organ_index.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(R / 'body_assets.blend'), compress=True)
print('ASSETS OK', len(info))
