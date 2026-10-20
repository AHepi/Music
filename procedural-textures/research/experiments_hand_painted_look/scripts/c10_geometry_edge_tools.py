# What this does: tests the three "real 3D" edge finders as outline / edge-darkening sources on a stepped relief (posterised height turned into real
# geometry, seen from straight above): Ambient Occlusion node, Bevel node (normal difference) and Geometry > Pointiness. Also checks what they do on a FLAT
# plane that only has a Bump node (answer: nothing, they need real geometry). Prints timings and how much of the picture each marks as edge.
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src_text = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c05_outlines_in_shader.py')).read().split('results = {}')[0]
exec(compile(src_text, 'c05head', 'exec'))
import bmesh
BASE = os.path.join(hp.OUT, 'pictures', 'c10_geometry_edges'); os.makedirs(BASE, exist_ok=True)
N = 256            # grid squares per side
RENDER = 512
STEP_HEIGHT = 0.02
res = {}

# 1 stepped height from the patch field (4 levels of random patch number -> steps)
hp.SAMPLES = 1
def hgroup():
    tree, w = hp.new_group('stepped height', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    hp.instance(w, field_group('cells', scale=5.0, warp_amount=0.01, warp_scale=20.0), 'f', x=0); w.link('in', 'Vector', 'f', 'Vector')
    w.add('ShaderNodeMapRange', 'steps', x=1, interpolation_type='STEPPED', clamp=True); w.nodes['steps'].inputs['Steps'].default_value = 3.0
    w.link('f', 'Id', 'steps', 'Value'); w.link('steps', 'Result', 'out', 'Height'); return tree
hp.photograph_group(hgroup, 'Height', os.path.join(BASE, 'stepped_height_source.png'), N + 1, sixteen=False)
height = hp.load(os.path.join(BASE, 'stepped_height_source.png'))[..., 0]          # rows top to bottom
hp.SAMPLES = 4

def make_scene(z_scale, flat=False):
    scene, tile = hp.bh.new_bake_scene(RENDER)
    scene.cycles.samples = 24
    mesh = bpy.data.meshes.new('relief')
    xs = np.linspace(0, 1, N + 1)
    gx, gy = np.meshgrid(xs, xs)                       # gy increases upwards (v)
    z = np.zeros_like(gx) if flat else height[::-1] * z_scale   # image rows run downwards, v runs upwards
    verts = np.stack([gx, gy, z], axis=-1).reshape(-1, 3)
    faces = []
    idx = lambda i, j: j * (N + 1) + i
    for j in range(N):
        for i in range(N):
            faces.append((idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)))
    mesh.from_pydata(verts.tolist(), [], faces)
    uv = mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (v.x, v.y)
    for p in mesh.polygons: p.use_smooth = True
    tile.data = mesh
    return scene, tile

def material_for(kind, bump_flat=False):
    m = bpy.data.materials.new('edge ' + kind); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    w = rt.NodeWriter(t)
    w.add('ShaderNodeOutputMaterial', 'out', x=6); w.add('ShaderNodeEmission', 'emit', x=5); w.link('emit', 'Emission', 'out', 'Surface')
    if kind == 'ao':
        w.add('ShaderNodeAmbientOcclusion', 'ao', x=1, samples=16, only_local=False); w.nodes['ao'].inputs['Distance'].default_value = 0.03
        w.link('ao', 'Color', 'emit', 'Color') if False else w.link('ao', 'AO', 'emit', 'Color')
    elif kind == 'ao_local':
        w.add('ShaderNodeAmbientOcclusion', 'ao', x=1, samples=16, only_local=True); w.nodes['ao'].inputs['Distance'].default_value = 0.03
        w.link('ao', 'AO', 'emit', 'Color')
    elif kind == 'bevel':
        w.add('ShaderNodeBevel', 'bev', x=1, samples=16); w.nodes['bev'].inputs['Radius'].default_value = 0.006
        w.add('ShaderNodeNewGeometry', 'geo', x=1, y=-2)
        w.add('ShaderNodeVectorMath', 'dot', x=2, operation='DOT_PRODUCT'); w.link('bev', 'Normal', 'dot', 0); w.link('geo', 'Normal', 'dot', 1)
        w.math('edge', 'SUBTRACT', 1.0, None, x=3); w.link('dot', 'Value', 'edge', 1)
        w.math('amp', 'MULTIPLY', None, 10.0, x=4, clamp=True); w.link('edge', 0, 'amp', 0); w.link('amp', 0, 'emit', 'Color')
    elif kind == 'pointiness':
        w.add('ShaderNodeNewGeometry', 'geo', x=1); w.link('geo', 'Pointiness', 'emit', 'Color')
    elif kind == 'flat_bump_ao':
        w.add('ShaderNodeBump', 'bump', x=1, Strength=1.0, Distance=0.05); w.add('ShaderNodeAmbientOcclusion', 'ao', x=2); w.nodes['ao'].inputs['Distance'].default_value = 0.03
        w.link('bump', 'Normal', 'ao', 'Normal'); w.link('ao', 'AO', 'emit', 'Color')
    t.nodes['emit'].inputs['Strength'].default_value = 1.0
    return m

def render(kind, name, flat=False):
    scene, tile = make_scene(STEP_HEIGHT, flat)
    scene.view_settings.view_transform = 'Raw'
    tile.data.materials.append(material_for(kind))
    scene.render.filepath = os.path.join(BASE, name + '.png'); scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_depth = '8'
    t = time.time(); bpy.ops.render.render(write_still=True); return time.time() - t

for kind in ('ao', 'ao_local', 'bevel', 'pointiness'):
    secs = render(kind, kind)
    a = hp.load(os.path.join(BASE, kind + '.png')).mean(axis=2)
    res[kind] = {'seconds': round(secs, 1), 'mean': float(a.mean()), 'share_below_0.9': float((a < 0.9).mean()), 'share_above_0.6': float((a > 0.6).mean()), 'min': float(a.min()), 'max': float(a.max())}
    print(kind, res[kind], flush=True)
# control: flat plane with Bump -> AO
secs = render('flat_bump_ao', 'flat_bump_ao', flat=True)
a = hp.load(os.path.join(BASE, 'flat_bump_ao.png')).mean(axis=2)
res['flat_plane_bump_then_ao'] = {'seconds': round(secs, 1), 'min': float(a.min()), 'max': float(a.max()), 'std': float(a.std())}
print('flat+bump AO', res['flat_plane_bump_then_ao'])
secs = render('pointiness', 'flat_pointiness', flat=True)
a = hp.load(os.path.join(BASE, 'flat_pointiness.png')).mean(axis=2)
res['flat_plane_pointiness'] = {'min': float(a.min()), 'max': float(a.max()), 'std': float(a.std())}
print('flat pointiness', res['flat_plane_pointiness'])
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c10_geometry_edge_tools.json'), 'w'), indent=1)
