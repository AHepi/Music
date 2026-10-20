# What this does: tests the ways to turn a smooth grey pattern into a few flat levels inside the shader (Color Ramp with Constant interpolation, Math Floor,
# Math Snap, Math Round, Map Range with Interpolation Stepped) and prints how many different levels each really gives for a given Steps / N, plus
# strips of pictures. Source pattern = seamless noise stretched to use the full 0..1 range.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp
import recipe_tools as rt

BASE = os.path.join(hp.OUT, 'pictures')
hp.SAMPLES = 1   # no anti-aliasing so a flat patch is exactly one value
NS = [2, 3, 4, 6, 8, 16]
results = {}

def source_field(w, name='field'):
    """seamless noise 0..1 using the full range (Map Range 0.30..0.70 -> 0..1, clamped)"""
    w.add('ShaderNodeGroup', name + '_noise', x=0); w.nodes[name + '_noise'].node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', name + '_noise', 'Vector')
    w.nodes[name + '_noise'].inputs['Scale'].default_value = 3.0; w.nodes[name + '_noise'].inputs['Detail'].default_value = 5.0
    w.add('ShaderNodeMapRange', name, x=1, clamp=True)
    w.nodes[name].inputs['From Min'].default_value = 0.30; w.nodes[name].inputs['From Max'].default_value = 0.70
    w.link(name + '_noise', 'Fac', name, 'Value')
    return name

def grey_out(w, node, socket=0):
    w.link(node, socket, 'out', 'Height')

def build_ramp_constant(n):
    tree, w = hp.new_group(f'ramp constant {n}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    f = source_field(w)
    w.add('ShaderNodeValToRGB', 'ramp', x=3); ramp = w.nodes['ramp'].color_ramp
    ramp.interpolation = 'CONSTANT'
    # N colours: stops at 0, 1/N, 2/N ... (N-1)/N ; the colour at stop i is i/(N-1)
    while len(ramp.elements) < n: ramp.elements.new(0.5)
    for i, e in enumerate(ramp.elements):
        e.position = i / n; v = i / (n - 1); e.color = (v, v, v, 1)
    w.link(f, 'Result', 'ramp', 'Fac'); w.link('ramp', 'Color', 'out', 'Height')
    return tree

def build_math(op, n, scale_after=True):
    tree, w = hp.new_group(f'math {op} {n}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    f = source_field(w)
    if op == 'FLOOR':      # floor(x*n)/(n-1)
        w.math('mul', 'MULTIPLY', None, float(n), x=3); w.link(f, 'Result', 'mul', 0)
        w.math('fl', 'FLOOR', x=4); w.link('mul', 0, 'fl', 0)
        w.math('div', 'DIVIDE', None, float(n - 1), x=5, clamp=True); w.link('fl', 0, 'div', 0); last = 'div'
    elif op == 'ROUND':    # round(x*(n-1))/(n-1)
        w.math('mul', 'MULTIPLY', None, float(n - 1), x=3); w.link(f, 'Result', 'mul', 0)
        w.math('rd', 'ROUND', x=4); w.link('mul', 0, 'rd', 0)
        w.math('div', 'DIVIDE', None, float(n - 1), x=5); w.link('rd', 0, 'div', 0); last = 'div'
    elif op == 'SNAP':     # snap(x, 1/n) -> multiples of 1/n (n+1 levels incl. 0 and 1)
        w.math('sn', 'SNAP', None, 1.0 / n, x=3); w.link(f, 'Result', 'sn', 0); last = 'sn'
    grey_out(w, last)
    return tree

def build_maprange_stepped(n):
    tree, w = hp.new_group(f'map range stepped {n}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    f = source_field(w)
    w.add('ShaderNodeMapRange', 'steps', x=3, interpolation_type='STEPPED', clamp=True)
    w.nodes['steps'].inputs['Steps'].default_value = float(n)
    w.link(f, 'Result', 'steps', 'Value')
    grey_out(w, 'steps')
    return tree

methods = {
    'A_ColorRamp_Constant': build_ramp_constant,
    'B_Math_Floor': lambda n: build_math('FLOOR', n),
    'C_Math_Round': lambda n: build_math('ROUND', n),
    'D_Math_Snap': lambda n: build_math('SNAP', n),
    'E_MapRange_Stepped': build_maprange_stepped,
}
for name, builder in methods.items():
    arrays = hp.sweep(builder, NS, os.path.join(BASE, 'c01_' + name), labels=[f'{name.split("_",1)[1]} N={n}' for n in NS], channel='Height', size=256, title=name, cell=200)
    results[name] = {}
    for n, a in zip(NS, arrays):
        count, vals = hp.levels(a, 2)
        results[name][n] = {'levels_used': count, 'levels_and_shares': vals}
    print(name, {n: results[name][n]['levels_used'] for n in NS})
json.dump(results, open(os.path.join(hp.OUT, 'data', 'c01_posterise_levels.json'), 'w'), indent=1)
