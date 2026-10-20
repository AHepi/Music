# What this does: tests the texture and converter nodes INSIDE Geometry Nodes (Blender 5.2.2):
#  (1) is the Noise node's unconnected Vector input the Position there?  (2) a noise-displaced grid (real geometry) seen from the side,
#  (3) a noise stored as a named attribute and read back by a material (Attribute node), (4) which Shader-editor nodes are missing there.
# Writes gn_checks.json and pictures/g01_gn_displaced_grid.png, pictures/g02_gn_attribute_in_material.png
import os, sys, json, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
bh = pt.bh
import recipe_tools as rt
OUT = os.path.dirname(os.path.abspath(__file__))
PICS = os.path.join(OUT, 'pictures')
R = {}

def gn_tree(name='gn'):
    t = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    t.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    t.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    return t, rt.NodeWriter(t)

def build(scene_tile, store_name=None, displace=0.0, explicit_position=False, grid_n=129, noise_scale=6.0, material=None):
    t, w = gn_tree()
    gi = w.add('NodeGroupInput', 'gi', x=0); go = w.add('NodeGroupOutput', 'go', x=8)
    w.add('GeometryNodeMeshGrid', 'grid', x=1); g = w.nodes['grid']
    g.inputs['Size X'].default_value = 1.0; g.inputs['Size Y'].default_value = 1.0; g.inputs['Vertices X'].default_value = grid_n; g.inputs['Vertices Y'].default_value = grid_n
    w.add('GeometryNodeSetPosition', 'tr', x=2); w.link('grid', 'Mesh', 'tr', 'Geometry')           # grid is centred on 0: move to 0..1
    w.add('ShaderNodeCombineXYZ', 'half', x=1, y=-2, X=0.5, Y=0.5, Z=0.0); w.link('half', 'Vector', 'tr', 'Offset')
    n = w.add('ShaderNodeTexNoise', 'noise', x=3, y=-2, Scale=noise_scale, Detail=5.0, Roughness=0.6)
    if explicit_position:
        w.add('GeometryNodeInputPosition', 'pos', x=2, y=-3); w.link('pos', 'Position', 'noise', 'Vector')
    last = 'tr'
    if displace:
        w.math('centre', 'SUBTRACT', None, 0.5, x=4, y=-2); w.link('noise', 'Fac', 'centre', 0)
        w.math('amp', 'MULTIPLY', None, displace, x=5, y=-2); w.link('centre', 0, 'amp', 0)
        w.add('ShaderNodeCombineXYZ', 'up', x=6, y=-2); w.link('amp', 0, 'up', 'Z')
        w.add('GeometryNodeSetPosition', 'lift', x=6); w.link('tr', 'Geometry', 'lift', 'Geometry'); w.link('up', 'Vector', 'lift', 'Offset')
        last = 'lift'
    if store_name:
        w.add('GeometryNodeStoreNamedAttribute', 'store', x=7, data_type='FLOAT', domain='POINT'); s = w.nodes['store']
        w.link(last, 'Geometry', 'store', 'Geometry'); s.inputs['Name'].default_value = store_name; w.link('noise', 'Fac', 'store', 'Value')
        last = 'store'
    if material is not None:
        w.add('GeometryNodeSetShadeSmooth', 'smooth', x=7.5); w.link(last, 'Geometry', 'smooth', 'Geometry')
        w.add('GeometryNodeSetMaterial', 'setmat', x=7.8); w.link('smooth', 'Geometry', 'setmat', 'Geometry'); w.nodes['setmat'].inputs['Material'].default_value = material
        last = 'setmat'
    w.link(last, 'Geometry', 'go', 'Geometry')
    mod = scene_tile.modifiers.new('GN', 'NODES'); mod.node_group = t
    return t

# (1) Noise default Vector = Position?
scene, tile = bh.new_bake_scene(64)
build(tile, store_name='h')
dg = bpy.context.evaluated_depsgraph_get(); ev = tile.evaluated_get(dg); me = ev.to_mesh()
h1 = np.zeros(len(me.vertices)); me.attributes['h'].data.foreach_get('value', h1)
R['1_noise_in_GN_unconnected_vector'] = {'vertices': len(me.vertices), 'std of stored noise (0 = constant)': round(float(h1.std()), 4), 'min': round(float(h1.min()), 3), 'max': round(float(h1.max()), 3)}
ev.to_mesh_clear()
scene, tile = bh.new_bake_scene(64)
build(tile, store_name='h', explicit_position=True)
dg = bpy.context.evaluated_depsgraph_get(); ev = tile.evaluated_get(dg); me = ev.to_mesh()
h2 = np.zeros(len(me.vertices)); me.attributes['h'].data.foreach_get('value', h2)
R['1_noise_in_GN_unconnected_vector']['max |unconnected - explicit Position|'] = float(np.abs(h1 - h2).max())
ev.to_mesh_clear()

# (2) displaced grid side view (silhouette), top view lit
def emit_mat(tile, attr=None):
    m = bpy.data.materials.new('m'); m.use_nodes = True; m.node_tree.nodes.clear(); w = rt.NodeWriter(m.node_tree)
    e = w.add('ShaderNodeEmission', 'emit', x=2); o = w.add('ShaderNodeOutputMaterial', 'output', x=3); w.link('emit', 'Emission', 'output', 'Surface')
    if attr:
        a = w.add('ShaderNodeAttribute', 'attr', x=0, attribute_type='GEOMETRY', attribute_name=attr)
        w.add('ShaderNodeValToRGB', 'ramp', x=1); r = w.nodes['ramp'].color_ramp
        r.elements[0].position = 0.3; r.elements[0].color = (0.2, 0.09, 0.05, 1); r.elements[1].position = 0.7; r.elements[1].color = (0.9, 0.7, 0.4, 1)
        w.link('attr', 'Factor', 'ramp', 'Fac'); w.link('ramp', 'Color', 'emit', 'Color')
    tile.data.materials.append(m)
files = []
folder = os.path.join(PICS, '_work', 'g01'); os.makedirs(folder, exist_ok=True)
for i, (side, amp) in enumerate([(True, 0.0), (True, 0.2), (False, 0.2)]):
    scene, tile = bh.new_bake_scene(256)
    scene.cycles.samples = 4
    emit_mat(tile)
    build(tile, displace=amp, material=tile.data.materials[0])
    if side:
        cam = scene.camera; cam.location = (0.5, -3.0, 0.0); cam.rotation_euler = (math.radians(90), 0, 0); cam.data.ortho_scale = 1.0
    else:
        # lit top view needs normals: use a simple principled with a low sun
        tile.modifiers.clear()
        tile.data.materials.clear()
        m = bpy.data.materials.new('p'); m.use_nodes = True; m.node_tree.nodes.clear(); w = rt.NodeWriter(m.node_tree)
        p = w.add('ShaderNodeBsdfPrincipled', 'b', x=0, Base__Color=(0.65, 0.65, 0.65, 1), Roughness=0.8); p.inputs['Specular IOR Level'].default_value = 0.0
        o = w.add('ShaderNodeOutputMaterial', 'o', x=1); w.link('b', 'BSDF', 'o', 'Surface'); tile.data.materials.append(m)
        build(tile, displace=amp, material=m)
        scene.cycles.samples = 16; scene.cycles.max_bounces = 2
        ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 3.0
        sun = bpy.data.objects.new('sun', ld); scene.collection.objects.link(sun)
        from mathutils import Vector
        sun.rotation_euler = Vector((0.8, 0.8, -0.7)).to_track_quat('-Z', 'Y').to_euler()
        tile.data.polygons.foreach_set('use_smooth', [True] * len(tile.data.polygons)) if False else None
    path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
json.dump({'files': files, 'labels': ['side view, no displacement', 'side view, noise +-0.1', 'top view, low sun']}, open(os.path.join(folder, 'sweep.json'), 'w'))
subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'g01_gn_displaced_grid.png'), '--title', 'Geometry Nodes: Noise Texture moves real grid points', '--columns', '3', '--cell', '256'], check=True, capture_output=True)

# (3) attribute read back in a material
scene, tile = bh.new_bake_scene(256)
scene.cycles.samples = 4
emit_mat(tile, attr='wetness')
build(tile, store_name='wetness', noise_scale=5.0, material=tile.data.materials[0])
path = os.path.join(PICS, '_work', 'g02.png'); pt.render_png(scene, path, False)
import shutil; shutil.copy(path, os.path.join(PICS, 'g02_gn_attribute_in_material.png'))

# (4) shader-editor nodes that do NOT exist in a Geometry Nodes tree
t = bpy.data.node_groups.new('probe', 'GeometryNodeTree')
missing, present = [], []
for idn in ['ShaderNodeTexNoise', 'ShaderNodeTexVoronoi', 'ShaderNodeTexBrick', 'ShaderNodeTexChecker', 'ShaderNodeTexGabor', 'ShaderNodeTexGradient', 'ShaderNodeTexMagic', 'ShaderNodeTexWave', 'ShaderNodeTexWhiteNoise',
            'ShaderNodeValToRGB', 'ShaderNodeMapRange', 'ShaderNodeMath', 'ShaderNodeVectorMath', 'ShaderNodeClamp', 'ShaderNodeFloatCurve', 'ShaderNodeRGBCurve', 'ShaderNodeMix', 'ShaderNodeMixRGB',
            'ShaderNodeInvert', 'ShaderNodeHueSaturation', 'ShaderNodeBrightContrast', 'ShaderNodeGamma', 'ShaderNodeMapping', 'ShaderNodeVectorRotate', 'ShaderNodeSeparateColor', 'ShaderNodeCombineColor',
            'ShaderNodeSeparateXYZ', 'ShaderNodeCombineXYZ', 'ShaderNodeRadialTiling', 'ShaderNodeBump', 'ShaderNodeNormalMap', 'ShaderNodeDisplacement', 'ShaderNodeBevel', 'ShaderNodeAmbientOcclusion',
            'ShaderNodeWireframe', 'ShaderNodeFresnel', 'ShaderNodeLayerWeight', 'ShaderNodeNewGeometry', 'ShaderNodeBsdfPrincipled', 'ShaderNodeRGBToBW', 'ShaderNodeTexCoord', 'ShaderNodeSqueeze']:
    try:
        t.nodes.new(idn); present.append(idn.replace('ShaderNode', ''))
    except Exception:
        missing.append(idn.replace('ShaderNode', ''))
R['4_in_geometry_nodes'] = {'available': present, 'missing': missing}
json.dump(R, open(os.path.join(OUT, 'gn_checks.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
