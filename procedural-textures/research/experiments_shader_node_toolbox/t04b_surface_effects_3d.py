# What this does: lit renders with real 3D objects for: true Displacement vs Bump (top view and side silhouette), Bevel node, Ambient Occlusion,
# Pointiness (and how mesh density changes it), Wireframe, Fresnel and Layer Weight. Cycles, small, CPU.
# Run: blender -b --disable-autoexec -t 2 --python t04b_surface_effects_3d.py -- [only_name ...]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
import probe_tools as pt
from sweeps import lit_sweep, PICS
bh = pt.bh
import recipe_tools as rt
from mathutils import Vector
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def want(n): return not only or n in only
D = 'ShaderNodeTex'

def mat(obj, name='mat'):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    obj.data.materials.clear(); obj.data.materials.append(m)
    return m, rt.NodeWriter(m.node_tree)

def emit_output(w, source_node, source_socket):
    e = w.add('ShaderNodeEmission', 'emit', x=8); o = w.add('ShaderNodeOutputMaterial', 'output', x=9)
    w.link(source_node, source_socket, 'emit', 'Color'); w.link('emit', 'Emission', 'output', 'Surface')

def principled(w, normal=None, base=(0.65, 0.65, 0.65, 1), roughness=0.8, spec=0.0, x=8):
    p = w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=x, Base__Color=base, Roughness=roughness)
    p.inputs['Specular IOR Level'].default_value = spec
    o = w.add('ShaderNodeOutputMaterial', 'output', x=x + 1); w.link('bsdf', 'BSDF', 'output', 'Surface')
    if normal: w.link(normal[0], normal[1], 'bsdf', 'Normal')
    return p

def object_scene(size=224, cam=(2.4, -1.8, 1.7), target=(0.5, 0.5, 0.2), ortho=1.6, sun_from=(-0.4, -0.8, 0.9), world=0.25, samples=32):
    scene, tile = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile)
    scene.cycles.samples = samples; scene.cycles.max_bounces = 4
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (world, world, world * 1.05, 1)
    cam_obj = scene.camera; cam_obj.data.ortho_scale = ortho
    cam_obj.location = cam
    direction = Vector(target) - Vector(cam)
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 3.0; ld.angle = math.radians(2)
    sun = bpy.data.objects.new('sun', ld); scene.collection.objects.link(sun)
    sun.rotation_euler = (-Vector(sun_from)).to_track_quat('-Z', 'Y').to_euler()
    return scene

def add_mesh(scene, name, build, location=(0, 0, 0)):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.location = location; scene.collection.objects.link(ob)
    return ob
def cube_build(size=0.5):
    def b(bm): bmesh.ops.create_cube(bm, size=size)
    return b
def sphere_build(radius=0.45):
    def b(bm): bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=radius)
    return b
def plane_build(size=1.0):
    def b(bm): bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    return b

# ---- displacement vs bump ------------------------------------------------------------------------------------------
def displacement_scene(method, side, size=256, scale=0.12):
    scene, tile = pt.lit_scene(size) if not side else bh.new_bake_scene(size)
    scene.cycles.samples = 16
    if side:
        cam = scene.camera
        cam.location = (0.5, -3.0, 0.0); cam.rotation_euler = (math.radians(90), 0, 0)
        cam.data.ortho_scale = 1.0
        scene.cycles.max_bounces = 0
    mod = tile.modifiers.new('sub', 'SUBSURF'); mod.subdivision_type = 'SIMPLE'; mod.levels = 8; mod.render_levels = 8
    m, w = mat(tile)
    m.displacement_method = method
    w.add('ShaderNodeTexCoord', 'tc', x=0)
    n = w.add(D + 'Noise', 'noise', x=1, Scale=5.0, Detail=6.0, Roughness=0.6); w.link('tc', 'UV', 'noise', 'Vector')
    d = w.add('ShaderNodeDisplacement', 'disp', x=3); d.inputs['Midlevel'].default_value = 0.5; d.inputs['Scale'].default_value = scale
    w.link('noise', 'Fac', 'disp', 'Height')
    if side:
        e = w.add('ShaderNodeEmission', 'emit', x=4); o = w.add('ShaderNodeOutputMaterial', 'output', x=5)
        w.link('emit', 'Emission', 'output', 'Surface')
    else:
        bsdf = w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=4, Base__Color=(0.65, 0.65, 0.65, 1), Roughness=0.8)
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        o = w.add('ShaderNodeOutputMaterial', 'output', x=5); w.link('bsdf', 'BSDF', 'output', 'Surface')
    w.link('disp', 'Displacement', 'output', 'Displacement')
    return scene
if want('e10_displacement'):
    methods = ['BUMP', 'DISPLACEMENT', 'BOTH']
    for side in (False, True):
        name = 'e10_displacement_' + ('side' if side else 'top')
        lit_sweep(name, lambda scene, tile, v: None, methods, ['Bump Only', 'Displacement Only', 'Displacement and Bump'], size=256,
                  title='Displacement method: ' + ('side silhouette (white = surface)' if side else 'seen from above, low sun'),
                  make_scene=None) if False else None
        folder = os.path.join(PICS, '_work', name); os.makedirs(folder, exist_ok=True)
        files = []
        for i, mth in enumerate(methods):
            scene = displacement_scene(mth, side)
            path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
        import json, subprocess
        json.dump({'files': files, 'labels': ['Bump Only', 'Displacement Only', 'Displacement and Bump']}, open(os.path.join(folder, 'sweep.json'), 'w'))
        subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, name + '.png'), '--title',
                        'Material Displacement setting: ' + ('side silhouette' if side else 'top view'), '--columns', '3', '--cell', '256'], check=True, capture_output=True)

# ---- bevel node -------------------------------------------------------------------------------------------------
if want('e11_bevel'):
    radii = [None, 0.01, 0.03, 0.08]
    def setup(radius, mask):
        scene = object_scene(224, samples=48)
        cube = add_mesh(scene, 'cube', cube_build(0.5), (0.5, 0.5, 0.25))
        m, w = mat(cube)
        if radius is None:
            if mask:
                w.add('ShaderNodeValue', 'zero', x=1); w.nodes['zero'].outputs[0].default_value = 0.0; emit_output(w, 'zero', 0)
            else:
                principled(w, roughness=0.3, spec=0.5)
        else:
            b = w.add('ShaderNodeBevel', 'bevel', x=1, samples=16); b.inputs['Radius'].default_value = radius
            if mask:
                w.add('ShaderNodeNewGeometry', 'geo', x=1)
                w.vector_math('dot', 'DOT_PRODUCT', x=2); w.link('bevel', 'Normal', 'dot', 0); w.link('geo', 'True Normal', 'dot', 1)
                w.math('edge', 'SUBTRACT', 1.0, None, x=3); w.link('dot', 'Value', 'edge', 1)
                w.math('boost', 'MULTIPLY', None, 12.0, clamp=True, x=4); w.link('edge', 0, 'boost', 0)
                emit_output(w, 'boost', 0)
            else:
                principled(w, normal=('bevel', 'Normal'), roughness=0.3, spec=0.5)
        return scene
    for mask in (False, True):
        name = 'e11_bevel_' + ('edge_mask' if mask else 'shading')
        folder = os.path.join(PICS, '_work', name); os.makedirs(folder, exist_ok=True)
        files = []
        for i, r in enumerate(radii):
            scene = setup(r, mask); path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
        import json, subprocess
        json.dump({'files': files, 'labels': ['no Bevel node'] + [f'Radius {r}' for r in radii[1:]]}, open(os.path.join(folder, 'sweep.json'), 'w'))
        subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, name + '.png'), '--title',
                        'Bevel node: ' + ('edge mask = 1 - dot(bevel normal, true normal), x12' if mask else 'bevelled normal into a glossy surface'), '--columns', '4', '--cell', '224'], check=True, capture_output=True)

# ---- ambient occlusion ------------------------------------------------------------------------------------------
if want('e12_ao'):
    cases = [(0.1, False, False), (0.3, False, False), (1.0, False, False), (0.3, True, False), (0.3, False, True)]
    def setup(v):
        dist, inside, local = v
        scene = object_scene(224, cam=(0.5, 0.5, 4.0), target=(0.5, 0.5, 0.0), ortho=1.7, samples=32)
        scene.camera.rotation_euler = (0, 0, 0)
        ground = add_mesh(scene, 'ground', plane_build(1.0), (0.5, 0.5, 0)); ground.scale = (1.6, 1.6, 1.6)
        for (x, y, s, h) in [(0.3, 0.35, 0.28, 0.18), (0.68, 0.62, 0.2, 0.12), (0.62, 0.25, 0.14, 0.2)]:
            c = add_mesh(scene, 'cube', cube_build(1.0), (x, y, h / 2)); c.scale = (s, s, h)
        for ob in scene.objects:
            if ob.type == 'MESH':
                m, w = mat(ob)
                a = w.add('ShaderNodeAmbientOcclusion', 'ao', x=1, samples=32, inside=inside, only_local=local); a.inputs['Distance'].default_value = dist
                emit_output(w, 'ao', 'AO')
        return scene
    folder = os.path.join(PICS, '_work', 'e12_ao'); os.makedirs(folder, exist_ok=True)
    files = []
    for i, v in enumerate(cases):
        scene = setup(v); path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
    import json, subprocess
    json.dump({'files': files, 'labels': ['Distance 0.1', 'Distance 0.3', 'Distance 1', 'D 0.3, Inside', 'D 0.3, Only Local']}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'e12_ao.png'), '--title', 'Ambient Occlusion node (AO output) from above', '--columns', '5', '--cell', '224'], check=True, capture_output=True)

# ---- pointiness vs mesh density -----------------------------------------------------------------------------------
if want('e13_pointiness'):
    levels = [0, 1, 2, 3]
    folder = os.path.join(PICS, '_work', 'e13_pointiness'); os.makedirs(folder, exist_ok=True)
    files = []
    stats = {}
    for i, lv in enumerate(levels):
        scene = object_scene(224, samples=8)
        cube = add_mesh(scene, 'cube', cube_build(0.5), (0.5, 0.5, 0.25))
        bev = cube.modifiers.new('bevel', 'BEVEL'); bev.width = 0.04; bev.segments = 3
        if lv:
            sub = cube.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = lv; sub.render_levels = lv
        m, w = mat(cube)
        w.add('ShaderNodeNewGeometry', 'geo', x=1)
        w.math('centre', 'SUBTRACT', None, 0.5, x=2); w.link('geo', 'Pointiness', 'centre', 0)
        w.math('gain', 'MULTIPLY_ADD', None, 6.0, 0.5, clamp=True, x=3); w.link('centre', 0, 'gain', 0)
        emit_output(w, 'gain', 0)
        path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
    import json, subprocess
    json.dump({'files': files, 'labels': [f'Simple subdivision {l}' for l in levels]}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'e13_pointiness.png'), '--title', 'Pointiness (x6 around 0.5) on a bevelled cube, more mesh density', '--columns', '4', '--cell', '224'], check=True, capture_output=True)

# ---- wireframe, fresnel, layer weight -----------------------------------------------------------------------------
if want('e14_fresnel_layer_weight'):
    cases = [('Fresnel IOR 1.1', 'fresnel', 1.1), ('Fresnel IOR 1.45', 'fresnel', 1.45), ('Fresnel IOR 3', 'fresnel', 3.0),
             ('LayerWeight Fresnel b0.2', 'lw_fresnel', 0.2), ('LayerWeight Fresnel b0.5', 'lw_fresnel', 0.5), ('LayerWeight Facing b0.5', 'lw_facing', 0.5)]
    folder = os.path.join(PICS, '_work', 'e14_fresnel_layer_weight'); os.makedirs(folder, exist_ok=True)
    files = []
    for i, (lab, kind, v) in enumerate(cases):
        scene = object_scene(192, cam=(0.5, 0.5, 4.0), target=(0.5, 0.5, 0.0), ortho=1.1, samples=4)
        scene.camera.rotation_euler = (0, 0, 0)
        sp = add_mesh(scene, 'sphere', sphere_build(0.45), (0.5, 0.5, 0))
        for p in sp.data.polygons: p.use_smooth = True
        m, w = mat(sp)
        if kind == 'fresnel':
            f = w.add('ShaderNodeFresnel', 'f', x=1); f.inputs['IOR'].default_value = v; emit_output(w, 'f', 'Factor')
        else:
            f = w.add('ShaderNodeLayerWeight', 'f', x=1); f.inputs['Blend'].default_value = v; emit_output(w, 'f', 'Fresnel' if kind == 'lw_fresnel' else 'Facing')
        path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
    import json, subprocess
    json.dump({'files': files, 'labels': [c[0] for c in cases]}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'e14_fresnel_layer_weight.png'), '--title', 'Fresnel and Layer Weight on a sphere seen from above', '--columns', '6', '--cell', '192'], check=True, capture_output=True)
if want('e15_wireframe'):
    cases = [(0.005, False), (0.02, False), (0.05, False)]
    folder = os.path.join(PICS, '_work', 'e15_wireframe'); os.makedirs(folder, exist_ok=True)
    files = []
    for i, (sz, px) in enumerate(cases):
        scene = object_scene(192, samples=4)
        cube = add_mesh(scene, 'cube', cube_build(0.5), (0.5, 0.5, 0.25))
        sub = cube.modifiers.new('sub', 'SUBSURF'); sub.subdivision_type = 'SIMPLE'; sub.levels = 2; sub.render_levels = 2
        m, w = mat(cube)
        wf = w.add('ShaderNodeWireframe', 'wf', x=1, use_pixel_size=px); wf.inputs['Size'].default_value = sz
        emit_output(w, 'wf', 'Factor')
        path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
    import json, subprocess
    json.dump({'files': files, 'labels': [f'Size {c[0]}' for c in cases]}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'e15_wireframe.png'), '--title', 'Wireframe node: Size (cube cut into 4x4 per face)', '--columns', '3', '--cell', '192'], check=True, capture_output=True)
print('done surface pictures (part 2)')
