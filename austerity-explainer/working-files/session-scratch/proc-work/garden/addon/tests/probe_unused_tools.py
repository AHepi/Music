# What this does: tries every Astra add-on tool the courtyard build did NOT use, on Blender 5.2.2, on tiny meshes
# (no rendering), and prints what works and what breaks. Read-only on the add-on folder.
# Use: blender -b --disable-autoexec --python probe_unused_tools.py -- ADDON_FOLDER [PATCHED]
import sys, importlib.util, traceback, math, json
sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
ARGS = sys.argv[sys.argv.index('--') + 1:]
FOLDER = ARGS[0]
SHIM = 'noshim' not in ARGS
def load(folder):
    name = 'astra_painted_workbench'
    spec = importlib.util.spec_from_file_location(name, folder + '/__init__.py', submodule_search_locations=[folder])
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    import astra_painted_workbench.runtime.api as api
    return api
api = load(FOLDER)
print('BLENDER', bpy.app.version_string)
if SHIM:
    sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work')
    from astra_loader import apply_blender_52_shim
    print('shim applied:', apply_blender_52_shim(api))
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
def attempt(label, fn):
    try:
        out = fn(); print('OK   ', label, '->', (str(out)[:160] if out is not None else '')); return out
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)[-1]
        print('FAIL ', label, '->', type(e).__name__, str(e)[:200], '@', tb.filename.split('/')[-1], tb.lineno); return None
def grid(nx, ny, step, fn):
    vs = [(i*step - nx*step/2, j*step - ny*step/2, 0.0) for j in range(ny+1) for i in range(nx+1)]
    vs = [(x, y, fn(x, y)) for x, y, _ in vs]
    fs = [(j*(nx+1)+i, j*(nx+1)+i+1, (j+1)*(nx+1)+i+1, (j+1)*(nx+1)+i) for j in range(ny) for i in range(nx)]
    return vs, fs
def principled_material(name, noise=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.2, 0.1, 0.05, 1)
    if noise:
        n = m.node_tree.nodes.new('ShaderNodeTexNoise'); r = m.node_tree.nodes.new('ShaderNodeValToRGB')
        m.node_tree.links.new(n.outputs['Fac'], r.inputs['Fac']); m.node_tree.links.new(r.outputs['Color'], b.inputs['Base Color'])
    return m
# 1. landscape with moss/pebbles (this one the courtyard used)
vs, fs = grid(40, 40, 0.25, lambda x, y: 0.1*math.sin(x))
me = bpy.data.meshes.new('ground'); me.from_pydata(vs, [], fs); me.update()
src = bpy.data.objects.new('ground', me); scene.collection.objects.link(src)
spec = api.default_spec(bounds=(-5, -5, 5, 5), seed=3)
land = attempt('create_landscape', lambda: api.create_landscape(src, spec, name='T'))
if land: attempt('audit_landscape', lambda: {k: v for k, v in api.audit_landscape(land, None).items() if k in ('counts', 'warnings', 'relief_peak')})
# 2. planks
attempt('create_planks', lambda: api.create_planks(length=2, width=1, count=8, seed=2))
# 3. roof/stone (shimmed)
attempt('create_stone', lambda: api.create_stone('S', api.StoneSpec(length=1, width=0.8, height=0.5)))
attempt('create_roof', lambda: api.create_roof('R', api.RoofSpec(width=4, half_depth=1.5, rise=0.6)))
# 4. pigment (timber, plaster), detail (timber, stone, ceramic) on simple boxes
import bmesh
def box(name, size, loc, mat):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    m = bpy.data.meshes.new(name); bm.to_mesh(m); bm.free(); m.materials.append(mat)
    o = bpy.data.objects.new(name, m); o.location = loc; scene.collection.objects.link(o); return o
beam = box('beam', (2.0, 0.2, 0.2), (0, 3, 0), principled_material('timber m', noise=True))
wall = box('wall', (2.0, 0.2, 1.5), (0, 4, 0), principled_material('plaster m'))
rock = box('rock', (0.6, 0.5, 0.45), (0, 5, 0), principled_material('rock m'))
tile = box('tile', (0.5, 0.3, 0.05), (0, 6, 0), principled_material('tile m'))
k1 = attempt('apply_pigment timber', lambda: api.apply_pigment(beam, 0, 'timber', 'X', 41, 0.75))
if k1: attempt('audit_surface', lambda: api.audit_surface(beam)['checks'])
if k1: attempt('restore_surface', lambda: api.restore_surface(beam))
k2 = attempt('apply_pigment plaster', lambda: api.apply_pigment(wall, 0, 'plaster', 'X', 41, 0.75, palette_mean=(0.72, 0.6, 0.4)))
attempt('apply_pigment stone (expected refusal)', lambda: api.apply_pigment(rock, 0, 'stone'))
attempt('apply_detail timber', lambda: api.apply_detail(box('plank2', (1.2, 0.15, 0.04), (0, 7, 0), principled_material('pm')), 'timber', 5))
attempt('apply_detail stone', lambda: api.apply_detail(box('rock2', (0.9, 0.7, 0.5), (0, 8, 0), principled_material('rm')), 'stone', 5))
attempt('apply_detail ceramic', lambda: api.apply_detail(box('tile2', (0.6, 0.3, 0.06), (0, 9, 0), principled_material('tm')), 'ceramic', 5))
# 5. live scatter
bank = bpy.data.collections.new('bank'); scene.collection.children.link(bank)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5); bmesh.ops.translate(bm, vec=(0, 0, 0.5), verts=bm.verts)
m = bpy.data.meshes.new('pebble'); bm.to_mesh(m); bm.free(); m.materials.append(principled_material('pebble m'))
po = bpy.data.objects.new('pebble0', m); bank.objects.link(po)
recs = [dict(id=f'p{i}', x=-1.5 + 0.3*i, y=0.2*i - 1, scale=[0.05, 0.05, 0.04], rot=[0, 0, 0.1*i], traffic=3.0, habitat=0.8, contact=0.3) for i in range(8)]
host = attempt('create_native_scatter', lambda: api.create_native_scatter('S', recs, bank, land['astra_ground'] if land else src, scene.collection, 'pebble'))
if host:
    attempt('audit_native_scatter', lambda: {k: v for k, v in api.audit_native_scatter(host).items() if k in ('checks', 'warnings')})
    attempt('set_scatter_controls', lambda: api.set_scatter_controls(host, Density=0.5))
