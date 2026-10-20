# What this does: (1) sweeps of the Principled BSDF inputs that matter for our six surfaces (Roughness, Metallic, Coat, Specular IOR Level,
# Subsurface, Emission) on a sphere under a simple sky; (2) the "puddle" recipe built stage by stage (dry mud, wet darkening, low roughness,
# flattened bumps, water colour + coat) on a tilted plane, plus the older Mix-Shader way for comparison.
# Run: blender -b --disable-autoexec -t 2 --python t05_principled_and_puddles.py -- [only_name ...]
import os, sys, math, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
import numpy as np
import probe_tools as pt
from sweeps import PICS
bh = pt.bh
import recipe_tools as rt
from mathutils import Vector
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def want(n): return not only or n in only
D = 'ShaderNodeTex'

def sky_world(scene, strength=1.0):
    """A cheap sky: warm light-grey near the horizon, blue overhead, from the direction's height (Z). Gives something to reflect."""
    world = bpy.data.worlds.new('sky'); world.use_nodes = True
    t = world.node_tree; t.nodes.clear(); w = rt.NodeWriter(t)
    w.add('ShaderNodeTexCoord', 'tc', x=0)
    w.add('ShaderNodeSeparateXYZ', 'sep', x=1); w.link('tc', 'Generated', 'sep', 'Vector')
    r = w.add('ShaderNodeValToRGB', 'ramp', x=2)
    cr = r.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = (0.16, 0.14, 0.12, 1)       # below horizon: dark ground
    cr.elements[1].position = 1.0; cr.elements[1].color = (0.18, 0.4, 1.0, 1)
    e = cr.elements.new(0.5); e.color = (0.9, 0.88, 0.82, 1)                           # horizon
    e = cr.elements.new(0.75); e.color = (0.5, 0.65, 0.95, 1)
    w.add('ShaderNodeMath', 'z01', x=1.5, operation='MULTIPLY_ADD'); w.nodes['z01'].inputs[1].default_value = 0.5; w.nodes['z01'].inputs[2].default_value = 0.5
    w.link('sep', 'Z', 'z01', 0); w.link('z01', 0, 'ramp', 'Fac')
    w.add('ShaderNodeBackground', 'bg', x=3, Strength=strength); w.link('ramp', 'Color', 'bg', 'Color')
    w.add('ShaderNodeOutputWorld', 'out', x=4); w.link('bg', 'Background', 'out', 'Surface')
    scene.world = world

def sphere_scene(size=192, samples=48):
    scene, tile = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile)
    scene.cycles.samples = samples; scene.cycles.max_bounces = 6; scene.cycles.use_denoising = False
    sky_world(scene)
    cam = scene.camera; cam.data.ortho_scale = 1.15; cam.location = (0, -3, 0.35); cam.rotation_euler = (math.radians(86), 0, 0)
    me = bpy.data.meshes.new('s'); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=0.5); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('sphere', me); ob.location = (0, 0, 0.35); scene.collection.objects.link(ob)
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 2.5; ld.angle = math.radians(4)
    sun = bpy.data.objects.new('sun', ld); scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((-0.5, 0.7, -0.6)).to_track_quat('-Z', 'Y').to_euler()
    return scene, ob

def principled_for(ob, **kw):
    m = bpy.data.materials.new('p'); m.use_nodes = True; m.node_tree.nodes.clear()
    w = rt.NodeWriter(m.node_tree)
    p = w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=0)
    p.inputs['Base Color'].default_value = (0.55, 0.28, 0.14, 1); p.inputs['Roughness'].default_value = 0.5
    for k, v in kw.items():
        p.inputs[k.replace('__', ' ')].default_value = v
    o = w.add('ShaderNodeOutputMaterial', 'output', x=1); w.link('bsdf', 'BSDF', 'output', 'Surface')
    ob.data.materials.append(m)

if want('m01_principled_sweeps'):
    rows = [
        ('Roughness', [('Roughness', v) for v in (0.0, 0.15, 0.35, 0.6, 1.0)], {}),
        ('Metallic', [('Metallic', v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)], {'Roughness': 0.35}),
        ('Coat Weight', [('Coat Weight', v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)], {'Roughness': 0.9, 'Coat Roughness': 0.03}),
        ('Specular IOR Level', [('Specular IOR Level', v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)], {'Roughness': 0.3}),
        ('Subsurface Weight', [('Subsurface Weight', v) for v in (0.0, 0.25, 0.5, 0.75, 1.0)], {'Roughness': 0.6, 'Subsurface Scale': 0.2, 'Subsurface Radius': (1.0, 0.3, 0.1)}),
        ('Emission Strength', [('Emission Strength', v) for v in (0.0, 0.25, 0.5, 1.0, 2.0)], {'Roughness': 0.6, 'Emission Color': (1.0, 0.45, 0.1, 1)}),
    ]
    folder = os.path.join(PICS, '_work', 'm01_principled_sweeps'); os.makedirs(folder, exist_ok=True)
    files, labels = [], []
    for (rname, vals, base) in rows:
        for (k, v) in vals:
            scene, ob = sphere_scene(176, 40)
            kw = dict(base); kw[k] = v
            principled_for(ob, **{kk.replace(' ', '__'): vv for kk, vv in kw.items()})
            path = os.path.join(folder, f'tile_{len(files):02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path)); labels.append(f'{k} {v}')
    json.dump({'files': files, 'labels': labels}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'm01_principled_sweeps.png'), '--title',
                    'Principled BSDF inputs (rows: Roughness, Metallic, Coat Weight, Specular IOR Level, Subsurface Weight, Emission Strength)', '--columns', '5', '--cell', '176'], check=True, capture_output=True)

# ---- puddles -----------------------------------------------------------------------------------------------------
def puddle_scene(stage, size=288, samples=64, mix_shader=False):
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = samples; scene.cycles.max_bounces = 6; scene.cycles.use_denoising = False
    sky_world(scene)
    # perspective camera low over the plane
    cam = scene.camera; cam.data.type = 'PERSP'; cam.data.lens = 40
    cam.location = (0.5, -0.12, 0.5); cam.rotation_euler = (math.radians(55), 0, 0); cam.data.lens = 28
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 4.0; ld.angle = math.radians(3)
    sun = bpy.data.objects.new('sun', ld); scene.collection.objects.link(sun)
    sun.rotation_euler = Vector((-0.5, 0.8, -0.35)).to_track_quat('-Z', 'Y').to_euler()
    m = bpy.data.materials.new('mud'); m.use_nodes = True; m.node_tree.nodes.clear()
    tile.data.materials.append(m)
    w = rt.NodeWriter(m.node_tree)
    w.add('ShaderNodeTexCoord', 'tc', x=0)
    # height: soft big hills (puddle basins) + fine grain
    w.add(D + 'Noise', 'big', x=1, Scale=3.0, Detail=3.0, Roughness=0.55); w.link('tc', 'UV', 'big', 'Vector')
    w.add(D + 'Noise', 'fine', x=1, y=-1, Scale=40.0, Detail=4.0, Roughness=0.6); w.link('tc', 'UV', 'fine', 'Vector')
    w.add('ShaderNodeMapRange', 'bigr', x=2); w.nodes['bigr'].inputs[1].default_value = 0.3; w.nodes['bigr'].inputs[2].default_value = 0.7; w.link('big', 'Fac', 'bigr', 0)
    w.math('hmix', 'MULTIPLY_ADD', None, 0.15, None, x=3)              # fine*0.15 + big
    w.link('fine', 'Fac', 'hmix', 0); w.link('bigr', 0, 'hmix', 2)
    w.nodes['hmix'].inputs[2].default_value = 0.0
    w.math('height', 'DIVIDE', None, 1.15, x=4); w.link('hmix', 0, 'height', 0)
    # masks: puddle = low ground. Map Range with From Min > From Max turns "below the water level" into 1
    pm = w.add('ShaderNodeMapRange', 'puddle', x=5, interpolation_type='SMOOTHSTEP'); pm.inputs[1].default_value = 0.40; pm.inputs[2].default_value = 0.34; pm.inputs[3].default_value = 0.0; pm.inputs[4].default_value = 1.0
    w.link('height', 0, 'puddle', 0)
    wm = w.add('ShaderNodeMapRange', 'wet', x=5, y=-1, interpolation_type='SMOOTHSTEP'); wm.inputs[1].default_value = 0.55; wm.inputs[2].default_value = 0.34; wm.inputs[3].default_value = 0.0; wm.inputs[4].default_value = 1.0
    w.link('height', 0, 'wet', 0)
    # dry mud colour from the height (brown, lighter on the high ground)
    r = w.add('ShaderNodeValToRGB', 'mudcolour', x=5, y=-2)
    cr = r.color_ramp; cr.elements[0].position = 0.25; cr.elements[0].color = (0.2, 0.09, 0.05, 1); cr.elements[1].position = 0.8; cr.elements[1].color = (0.5, 0.27, 0.13, 1)
    w.link('height', 0, 'mudcolour', 'Fac')
    # bump: flatten inside the puddle by lifting the height to the water level
    w.math('flat_h', 'MAXIMUM', None, 0.40, x=6); w.link('height', 0, 'flat_h', 0)
    b = w.add('ShaderNodeBump', 'bump', x=7); b.inputs['Distance'].default_value = 0.03
    w.link('flat_h' if stage >= 4 else 'height', 0, 'bump', 'Height')
    p = w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=8)
    p.inputs['Specular IOR Level'].default_value = 0.4
    o = w.add('ShaderNodeOutputMaterial', 'output', x=9); w.link('bsdf', 'BSDF', 'output', 'Surface')
    w.link('bump', 'Normal', 'bsdf', 'Normal')
    # colour
    if stage >= 2:
        # darker where wet (wet rim), then water colour inside the puddle
        w.add('ShaderNodeMix', 'dark', x=6, y=-2, data_type='RGBA', blend_type='MULTIPLY'); w.nodes['dark'].inputs[0].default_value = 0.55
        dark = w.nodes['dark']; w.link('mudcolour', 'Color', 'dark', 'A'); dark.inputs['B'].default_value = (0.45, 0.4, 0.38, 1)
        w.add('ShaderNodeMix', 'wetcol', x=7, y=-2, data_type='RGBA'); w.link('wet', 0, 'wetcol', 'Factor'); w.link('mudcolour', 'Color', 'wetcol', 'A'); w.link('dark', 'Result', 'wetcol', 'B')
        col = 'wetcol'
        if stage == 5:
            w.add('ShaderNodeMix', 'watercol', x=8, y=-2, data_type='RGBA'); w.link('puddle', 0, 'watercol', 'Factor'); w.link('wetcol', 'Result', 'watercol', 'A')
            w.nodes['watercol'].inputs['B'].default_value = (0.12, 0.17, 0.25, 1)
            col = 'watercol'
        w.link(col, 'Result', 'bsdf', 'Base Color')
    else:
        w.link('mudcolour', 'Color', 'bsdf', 'Base Color')
    # roughness
    if stage >= 3:
        w.add('ShaderNodeMix', 'rough_wet', x=7, y=-3); w.nodes['rough_wet'].inputs[2].default_value = 0.9; w.nodes['rough_wet'].inputs[3].default_value = 0.35
        w.link('wet', 0, 'rough_wet', 'Factor')
        w.add('ShaderNodeMix', 'rough_pud', x=8, y=-3); w.link('rough_wet', 'Result', 'rough_pud', 'A'); w.nodes['rough_pud'].inputs[3].default_value = 0.02; w.link('puddle', 0, 'rough_pud', 'Factor')
        w.link('rough_pud', 'Result', 'bsdf', 'Roughness')
    else:
        p.inputs['Roughness'].default_value = 0.9
    if stage >= 5:
        p.inputs['IOR'].default_value = 1.33
    if stage == 6:
        # the older way: a separate glossy "water" shader mixed in by the puddle mask (flat bed, dark mud colour stays underneath)
        g = w.add('ShaderNodeBsdfAnisotropic', 'water', x=8, y=-4, Color=(0.35, 0.45, 0.6, 1), Roughness=0.02)
        mix = w.add('ShaderNodeMixShader', 'mixsh', x=9, y=-4)
        w.link('puddle', 0, 'mixsh', 'Factor'); w.link('bsdf', 'BSDF', 'mixsh', 1); w.link('water', 'BSDF', 'mixsh', 2)
        w.link('mixsh', 'Shader', 'output', 'Surface')
    return scene

if want('m02_puddle_stages'):
    stages = [1, 2, 3, 4, 5, 6]
    labels = ['1 dry mud', '2 + darker when wet', '3 + roughness drops', '4 + puddle bed flat', '5 + water colour, IOR 1.33', '6 Mix Shader way']
    folder = os.path.join(PICS, '_work', 'm02_puddle_stages'); os.makedirs(folder, exist_ok=True)
    files = []
    for i, st in enumerate(stages):
        scene = puddle_scene(st)
        path = os.path.join(folder, f'tile_{i:02d}.png'); pt.render_png(scene, path, False); files.append(os.path.basename(path))
    json.dump({'files': files, 'labels': labels}, open(os.path.join(folder, 'sweep.json'), 'w'))
    subprocess.run(['python3', '-I', os.path.join(pt.LIB, 'make_strip.py'), folder, os.path.join(PICS, 'm02_puddle_stages.png'), '--title', 'Puddles built up one step at a time (one Principled BSDF, mask-driven)', '--columns', '3', '--cell', '288'], check=True, capture_output=True)
print('done principled + puddles')
