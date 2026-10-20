# What this does: lit renders (one low sun, straight-down camera, Cycles) that show what the SURFACE-EFFECT nodes do:
# Bump (Strength, Distance, Filter Width, Invert), Normal Map (OpenGL vs DirectX, Strength), true Displacement vs Bump (side view),
# Bevel, Ambient Occlusion, Pointiness, Wireframe, Layer Weight, Fresnel.
# Run: blender -b --disable-autoexec -t 2 --python t04_surface_effects.py -- [only_name ...]
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import numpy as np
import probe_tools as pt
from sweeps import lit_sweep, PICS
bh = pt.bh
import recipe_tools as rt
only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def want(n): return not only or n in only
D = 'ShaderNodeTex'

def make_material(tile, name='mat'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes.clear()
    tile.data.materials.clear(); tile.data.materials.append(m)
    return m, rt.NodeWriter(m.node_tree)

def standard_surface(w, normal_from=None, base=(0.65, 0.65, 0.65, 1), roughness=0.8):
    p = w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=5, Base__Color=base, Roughness=roughness)
    p.inputs['Specular IOR Level'].default_value = 0.0
    o = w.add('ShaderNodeOutputMaterial', 'output', x=6)
    w.link('bsdf', 'BSDF', 'output', 'Surface')
    if normal_from: w.link(normal_from[0], normal_from[1], 'bsdf', 'Normal')
    return p

def height_noise(w, scale=7.0, detail=8.0, name='height'):
    w.add('ShaderNodeTexCoord', 'tc', x=0)
    n = w.add(D + 'Noise', 'noise', x=1, Scale=scale, Detail=detail, Roughness=0.6)
    w.link('tc', 'UV', 'noise', 'Vector')
    m = w.add('ShaderNodeMapRange', name, x=2); m.inputs[1].default_value = 0.3; m.inputs[2].default_value = 0.7
    w.link('noise', 'Fac', name, 0)
    return name

# ---- bump -------------------------------------------------------------------------------------------------------
def bump_setup(kind):
    def setup(scene, tile, v):
        m, w = make_material(tile)
        h = height_noise(w)
        b = w.add('ShaderNodeBump', 'bump', x=3)
        b.inputs['Strength'].default_value = 1.0; b.inputs['Distance'].default_value = 0.03
        if kind == 'strength': b.inputs['Strength'].default_value = v
        elif kind == 'distance': b.inputs['Distance'].default_value = v
        elif kind == 'invert': b.invert = v
        w.link(h, 0, 'bump', 'Height')
        standard_surface(w, ('bump', 'Normal'))
    return setup
if want('e01_bump_strength'):
    lit_sweep('e01_bump_strength', bump_setup('strength'), [0.0, 0.25, 0.6, 1.0], ['Strength 0', 'Strength 0.25', 'Strength 0.6', 'Strength 1'], title='Bump: Strength (Distance 0.03)')
if want('e02_bump_distance'):
    lit_sweep('e02_bump_distance', bump_setup('distance'), [0.001, 0.01, 0.03, 0.1], ['Distance 0.001 (default)', 'Distance 0.01', 'Distance 0.03', 'Distance 0.1'], title='Bump: Distance (Strength 1)')
if want('e03_bump_invert'):
    lit_sweep('e03_bump_invert', bump_setup('invert'), [False, True], ['Invert off', 'Invert on'], title='Bump: Invert')
if want('e04_bump_filter_width'):
    def setup(scene, tile, fw):
        m, w = make_material(tile)
        w.add('ShaderNodeTexCoord', 'tc', x=0)
        b = w.add(D + 'Brick', 'brick', x=1, Scale=3.0, offset=0.5)
        b.inputs['Mortar Size'].default_value = 0.03; b.inputs['Mortar Smooth'].default_value = 0.0
        w.link('tc', 'UV', 'brick', 'Vector')
        bm = w.add('ShaderNodeBump', 'bump', x=3)
        bm.inputs['Distance'].default_value = 0.02; bm.inputs['Filter Width'].default_value = fw
        # brick Factor: 1 = mortar; we want mortar low, so invert
        w.math('flip', 'SUBTRACT', 1.0, None, x=2); w.link('brick', 'Factor', 'flip', 1)
        w.link('flip', 0, 'bump', 'Height')
        standard_surface(w, ('bump', 'Normal'))
    lit_sweep('e04_bump_filter_width', setup, [0.1, 1.0, 2.0, 4.0], ['Filter Width 0.1 (default)', 'Filter Width 1', 'Filter Width 2', 'Filter Width 4'], size=224, title='Bump: Filter Width on a hard-edged height (brick mortar)')

# ---- normal map: generated from our own noise height, both conventions -------------------------------------------
if want('e05_normal_map'):
    # own height -> own Sobel normal map (OpenGL convention), saved as a plain png in the work folder
    scene, tile = bh.new_bake_scene(256)
    g = pt.tree_from('h', lambda w: (w.add(D + 'Noise', 'n', x=0, Scale=7.0, Detail=8.0, Roughness=0.6), w.add('ShaderNodeMapRange', 'm', x=1),
                                    w.link('in', 'Vector', 'n', 'Vector'), w.link('n', 'Fac', 'm', 0),
                                    setattr(w.nodes['m'].inputs[1], 'default_value', 0.3), setattr(w.nodes['m'].inputs[2], 'default_value', 0.7),
                                    w.link('m', 0, 'out', 'Height')))
    height = pt.render_float_group(scene, tile, g, 'Height')
    nm = bh.sobel_normal(height, 6.0) * 0.5 + 0.5
    normal_path = os.path.join(PICS, '_work', 'own_noise_normal_opengl.png')
    os.makedirs(os.path.dirname(normal_path), exist_ok=True)
    bh.save_array_png(nm, normal_path, False)
    def setup(scene, tile, v):
        conv, strength = v
        m, w = make_material(tile)
        w.add('ShaderNodeTexCoord', 'tc', x=0)
        img = w.add('ShaderNodeTexImage', 'img', x=1, interpolation='Linear')
        img.image = bpy.data.images.load(normal_path, check_existing=False); img.image.colorspace_settings.name = 'Non-Color'
        w.link('tc', 'UV', 'img', 'Vector')
        nmn = w.add('ShaderNodeNormalMap', 'nmap', x=2, convention=conv)
        nmn.inputs['Strength'].default_value = strength
        w.link('img', 'Color', 'nmap', 'Color')
        standard_surface(w, ('nmap', 'Normal'))
    cases = [('OPENGL', 0.0), ('OPENGL', 1.0), ('DIRECTX', 1.0), ('OPENGL', 2.5)]
    lit_sweep('e05_normal_map', setup, cases, ['OpenGL, Strength 0', 'OpenGL, Strength 1', 'DirectX, Strength 1', 'OpenGL, Strength 2.5'], title='Normal Map node: Convention and Strength (same map, same sun)')
    # the same height through the Bump node, for comparison
    def setup_b(scene, tile, v):
        m, w = make_material(tile)
        h = height_noise(w)
        b = w.add('ShaderNodeBump', 'bump', x=3); b.inputs['Distance'].default_value = 6.0 / 256.0 * 1.0
        w.link(h, 0, 'bump', 'Height')
        standard_surface(w, ('bump', 'Normal'))
    lit_sweep('e05b_bump_vs_normalmap', setup_b, ['bump'], ['Same height through a Bump node'], title='Compare with the Bump node route')

print('done surface pictures (part 1)')
