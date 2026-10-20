# What this does: tests four ways to draw dark outlines around flat paint patches INSIDE the shader (no compositor, no geometry):
#   1. Voronoi "Distance To Edge" thresholded (exact, constant width, only works for cells);
#   2. "same pattern a little way over" with 2 samples (+u, +v): one-sided outline like a shadow edge;
#   3. the same with 4 samples (+-u, +-v): centred outline, works for ANY flat-level pattern (posterised noise too);
#   4. the Bump node on the patch value (edge strength = how much the normal tips).
# It measures the real line width in pixels, how long each takes to render, and whether the tile still repeats.
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures')
SIZE = 384
hp.SAMPLES = 4
OUTLINE_COLOUR = (0.004, 0.004, 0.005, 1.0)   # near black, linear

def field_group(kind, scale=6.0, warp_amount=0.01, warp_scale=40.0, levels=4, randomness=1.0):
    """Group with input Vector and outputs: Id (float, different for neighbouring patches), Colour (palette), Edge (Voronoi distance to the nearest patch border)."""
    name = f'field {kind}'
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Id', 'NodeSocketFloat'), ('Colour', 'NodeSocketColor'), ('Edge', 'NodeSocketFloat')])
    src = ('in', 'Vector')
    if warp_amount > 0:
        hp.instance(w, hp.warp_vector_group(f'warp for {name}'), 'warp', x=0, Amount=warp_amount, Scale=warp_scale); w.link('in', 'Vector', 'warp', 'Vector'); src = ('warp', 'Vector')
    if kind == 'cells':
        hp.instance(w, hp.anisotropic_noise_group(f'cells for {name}', cells=True, feature='F1'), 'cells', x=1, **{'Scale__U': scale, 'Scale__V': scale, 'Randomness': randomness})
        w.link(*src, 'cells', 'Vector')
        hp.cell_random(w, 'rand', 'cells', 'Color', 0.0, x=2)
        w.link('rand', 'Value', 'out', 'Id')
        hp.palette_ramp(w, 'palette', hp.BRICK_PALETTE, x=3); w.link('rand', 'Value', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour')
        # distance to edge from a second Voronoi on the same coordinates
        hp.instance(w, hp.anisotropic_noise_group(f'edge for {name}', cells=True, feature='DISTANCE_TO_EDGE'), 'edge', x=1, y=-2, **{'Scale__U': scale, 'Scale__V': scale, 'Randomness': randomness})
        w.link(*src, 'edge', 'Vector')
        w.link('edge', 'Distance', 'out', 'Edge')
    elif kind == 'levels':
        hp.instance(w, hp.anisotropic_noise_group(f'noise for {name}', cells=False), 'noise', x=1, **{'Scale__U': scale, 'Scale__V': scale, 'Detail': 4.0})
        w.link(*src, 'noise', 'Vector')
        w.add('ShaderNodeMapRange', 'stretch', x=2, clamp=True); w.nodes['stretch'].inputs['From Min'].default_value = 0.30; w.nodes['stretch'].inputs['From Max'].default_value = 0.70
        w.link('noise', 'Fac', 'stretch', 'Value')
        w.add('ShaderNodeMapRange', 'steps', x=3, interpolation_type='STEPPED', clamp=True); w.nodes['steps'].inputs['Steps'].default_value = float(levels - 1)
        w.link('stretch', 'Result', 'steps', 'Value'); w.link('steps', 'Result', 'out', 'Id')
        hp.palette_ramp(w, 'palette', hp.BRICK_PALETTE, x=4); w.link('steps', 'Result', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour')
    return tree

def outlined(kind, method, width_px, strength=1.0, size=SIZE, name='outlined', field_kwargs=None):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor'), ('Mask', 'NodeSocketFloat')])
    field = field_group(kind, **(field_kwargs or {}))
    hp.instance(w, field, 'f0', x=0)
    w.link('in', 'Vector', 'f0', 'Vector')
    d = width_px / size
    def shifted(label, dx, dy):
        w.vector_math(f'shift {label}', 'ADD', x=0, y=-1); w.link('in', 'Vector', f'shift {label}', 0); w.nodes[f'shift {label}'].inputs[1].default_value = (dx, dy, 0)
        hp.instance(w, field, f'f {label}', x=1, y=-1); w.link(f'shift {label}', 0, f'f {label}', 'Vector')
    mask_node = None
    if method == 'edge_distance':
        # Distance To Edge is measured in cell units of the 4D donut space; convert width px -> a threshold by trial (see the numbers printed below)
        w.math('edge lt', 'LESS_THAN', None, 0.5 * width_px * 6.0 / size, x=3)   # half width in lattice units: 1 px = Scale/size lattice units (Scale 6)
        w.link('f0', 'Edge', 'edge lt', 0)
        mask_node = 'edge lt'
    elif method in ('offset2', 'offset4'):
        shifts = [('px', d, 0), ('py', 0, d)] + ([('mx', -d, 0), ('my', 0, -d)] if method == 'offset4' else [])
        mask_names = []
        for label, dx, dy in shifts:
            shifted(label, dx, dy)
            w.math(f'diff {label}', 'SUBTRACT', x=2, y=-1); w.link('f0', 'Id', f'diff {label}', 0); w.link(f'f {label}', 'Id', f'diff {label}', 1)
            w.math(f'abs {label}', 'ABSOLUTE', x=3, y=-1); w.link(f'diff {label}', 0, f'abs {label}', 0)
            w.math(f'ne {label}', 'GREATER_THAN', None, 0.02, x=4, y=-1); w.link(f'abs {label}', 0, f'ne {label}', 0)
            mask_names.append(f'ne {label}')
        current = mask_names[0]
        for i, other in enumerate(mask_names[1:]):
            w.math(f'max{i}', 'MAXIMUM', x=5 + i, y=-1); w.link(current, 0, f'max{i}', 0); w.link(other, 0, f'max{i}', 1); current = f'max{i}'
        mask_node = current
    elif method == 'bump':
        w.add('ShaderNodeBump', 'bump', x=1, Strength=1.0, Distance=1.0); w.nodes['bump'].inputs['Filter Width'].default_value = width_px * 0.5
        w.link('f0', 'Id', 'bump', 'Height')
        w.add('ShaderNodeSeparateXYZ', 'n', x=2); w.link('bump', 'Normal', 'n', 'Vector')
        w.math('tilt', 'SUBTRACT', 1.0, None, x=3); w.link('n', 'Z', 'tilt', 1)
        w.math('tilt gt', 'GREATER_THAN', None, 0.05, x=4); w.link('tilt', 0, 'tilt gt', 0); mask_node = 'tilt gt'
    elif method == 'none':
        w.math('zero', 'ADD', 0.0, 0.0, x=3); mask_node = 'zero'
    w.add('ShaderNodeMix', 'paint', x=8, data_type='RGBA', blend_type='MIX')
    w.link(mask_node, 0, 'paint', 'Factor'); w.link('f0', 'Colour', 'paint', 'A'); w.nodes['paint'].inputs['B'].default_value = OUTLINE_COLOUR
    w.link('paint', 'Result', 'out', 'Colour'); w.link(mask_node, 0, 'out', 'Mask')
    return tree

results = {}
for kind in ('cells', 'levels'):
    for method in ('none', 'edge_distance', 'offset2', 'offset4', 'bump'):
        if kind == 'levels' and method == 'edge_distance':
            continue
        for width in ((1, 2, 4, 8) if method != 'none' else (0,)):
            label = f'{kind}_{method}_{width}'
            path = os.path.join(BASE, 'c05_outline_' + label)
            os.makedirs(path, exist_ok=True)
            t0 = time.time()
            hp.photograph_group(lambda: outlined(kind, method, width, name='o_' + label), 'Colour', os.path.join(path, 'colour.png'), SIZE)
            t1 = time.time()
            hp.photograph_group(lambda: outlined(kind, method, width, name='m_' + label), 'Mask', os.path.join(path, 'mask.png'), SIZE)
            results[label] = {'seconds_for_colour_render': round(t1 - t0, 2)}
            print(label, results[label], flush=True)
json.dump(results, open(os.path.join(hp.OUT, 'data', 'c05_outline_methods.json'), 'w'), indent=1)
