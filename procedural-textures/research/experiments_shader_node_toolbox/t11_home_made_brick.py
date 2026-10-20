# What this does: builds a brick layout from plain Math nodes (instead of the Brick Texture node) so that (a) every brick has its own random value that
# REPEATS correctly when the tile repeats, (b) every brick has its own local coordinates (fx, fy from 0 to 1 inside the brick), which the Brick node does
# not give. Tests it: shift by one whole tile must give the identical picture. Writes pictures/r01_home_made_brick.png and home_made_brick.json
import os, sys, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import probe_tools as pt
from sweeps import PICS
bh = pt.bh
D = 'ShaderNodeTex'

def brick_chain(w, src, cols=4, rows=12, mortar=0.07):
    """returns names: rand (per-brick random 0..1), fx, fy (local coordinates), edge (0 inside the brick .. 1 in the mortar)"""
    w.add('ShaderNodeSeparateXYZ', 'uv', x=-8); w.link(src[0], src[1], 'uv', 'Vector')
    w.math('vs', 'MULTIPLY', None, rows, x=-7); w.link('uv', 'Y', 'vs', 0)
    w.math('row', 'FLOOR', x=-6); w.link('vs', 0, 'row', 0)
    w.math('fy', 'FRACT', x=-6, y=-1); w.link('vs', 0, 'fy', 0)
    w.math('us0', 'MULTIPLY', None, cols, x=-7, y=-2); w.link('uv', 'X', 'us0', 0)
    w.math('odd', 'FLOORED_MODULO', None, 2.0, x=-5); w.link('row', 0, 'odd', 0)
    w.math('us', 'MULTIPLY_ADD', None, 0.5, None, x=-4); w.link('odd', 0, 'us', 0); w.link('us0', 0, 'us', 2)
    w.math('col', 'FLOOR', x=-3); w.link('us', 0, 'col', 0)
    w.math('fx', 'FRACT', x=-3, y=-1); w.link('us', 0, 'fx', 0)
    w.math('col_wrapped', 'FLOORED_MODULO', None, cols, x=-2); w.link('col', 0, 'col_wrapped', 0)
    w.math('row_wrapped', 'FLOORED_MODULO', None, rows, x=-2, y=-1); w.link('row', 0, 'row_wrapped', 0)
    w.add('ShaderNodeCombineXYZ', 'id', x=-1); w.link('col_wrapped', 0, 'id', 'X'); w.link('row_wrapped', 0, 'id', 'Y')
    w.add(D + 'WhiteNoise', 'rnd', x=0, noise_dimensions='2D'); w.link('id', 'Vector', 'rnd', 0)
    # edge: distance to the nearest brick side (bricks are 2.5 times wider than tall in these units, so scale x and y separately)
    w.math('ex1', 'MINIMUM', x=-1, y=-3); w.link('fx', 0, 'ex1', 0)
    w.math('ex2', 'SUBTRACT', 1.0, None, x=-2, y=-3); w.link('fx', 0, 'ex2', 1); w.link('ex2', 0, 'ex1', 1)
    w.math('ey1', 'MINIMUM', x=-1, y=-4); w.link('fy', 0, 'ey1', 0)
    w.math('ey2', 'SUBTRACT', 1.0, None, x=-2, y=-4); w.link('fy', 0, 'ey2', 1); w.link('ey2', 0, 'ey1', 1)
    # convert both distances to the same unit: x distance counts 1/ (rows/cols aspect)
    w.math('exs', 'MULTIPLY', None, rows / cols, x=0, y=-3); w.link('ex1', 0, 'exs', 0)   # a brick is (1/cols) wide and (1/rows) tall in tile units
    w.math('emin', 'MINIMUM', x=1, y=-3); w.link('exs', 0, 'emin', 0); w.link('ey1', 0, 'emin', 1)
    return {'rand': ('rnd', 'Value'), 'fx': ('fx', 0), 'fy': ('fy', 0), 'edge_distance': ('emin', 0)}

def body(w, src=('in', 'Vector')):
    c = brick_chain(w, src)
    w.math('in_brick', 'GREATER_THAN', None, 0.07, x=2, y=-3); w.link(*c['edge_distance'], 'in_brick', 0)
    w.add('ShaderNodeValToRGB', 'tint', x=2); r = w.nodes['tint'].color_ramp
    r.elements[0].position = 0.0; r.elements[0].color = (0.1, 0.03, 0.02, 1); r.elements[1].position = 1.0; r.elements[1].color = (0.45, 0.12, 0.05, 1)
    w.link(*c['rand'], 'tint', 'Fac')
    # light chip highlight along the TOP of each brick, from its own local y
    w.math('top', 'SUBTRACT', None, 0.8, x=2, y=-1); w.link(*c['fy'], 'top', 0)
    w.math('top2', 'MULTIPLY', None, 2.5, clamp=True, x=3, y=-1); w.link('top', 0, 'top2', 0)
    w.add('ShaderNodeMix', 'lit', x=4, data_type='RGBA', blend_type='ADD'); w.link('top2', 0, 'lit', 'Factor'); w.link('tint', 'Color', 'lit', 'A'); w.nodes['lit'].inputs['B'].default_value = (0.2, 0.15, 0.1, 1)
    w.add('ShaderNodeMix', 'final', x=5, data_type='RGBA'); w.link('in_brick', 0, 'final', 'Factor'); w.nodes['final'].inputs['A'].default_value = (0.2, 0.15, 0.1, 1); w.link('lit', 'Result', 'final', 'B')
    w.link('final', 'Result', 'out', 'Colour')
    w.link('in_brick', 0, 'out', 'Height')

R = {}
# periodicity test on the random value and the picture
def make_shift(dx, dy):
    def b(w):
        w.add('ShaderNodeVectorMath', 'shift', x=-12, operation='ADD'); w.nodes['shift'].inputs[1].default_value = (dx, dy, 0.0); w.link('in', 'Vector', 'shift', 0)
        c = brick_chain(w, ('shift', 0))
        w.link(*c['rand'], 'out', 'Height')
    return b
base = pt.render_float(make_shift(0, 0), 'Height', 192)
R['per-brick random: u+1 difference'] = round(float(np.abs(base - pt.render_float(make_shift(1, 0), 'Height', 192)).mean()), 5)
R['per-brick random: v+1 difference'] = round(float(np.abs(base - pt.render_float(make_shift(0, 1), 'Height', 192)).mean()), 5)
R['per-brick random: distinct values (bricks in the tile = 4 x 12 = 48)'] = int(len(np.unique(np.round(base, 4))))
R['per-brick random: min / mean / max'] = [round(float(base.min()), 3), round(float(base.mean()), 3), round(float(base.max()), 3)]
def pic(dx, dy):
    def b(w):
        w.add('ShaderNodeVectorMath', 'shift', x=-12, operation='ADD'); w.nodes['shift'].inputs[1].default_value = (dx, dy, 0.0); w.link('in', 'Vector', 'shift', 0)
        body(w, ('shift', 0))
    return b
c0 = pt.render_float(pic(0, 0), 'Colour', 192); cx = pt.render_float(pic(1, 0), 'Colour', 192); cy = pt.render_float(pic(0, 1), 'Colour', 192)
R['finished colour picture: u+1 difference'] = round(float(np.abs(c0 - cx).mean()), 5); R['finished colour picture: v+1 difference'] = round(float(np.abs(c0 - cy).mean()), 5)
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'home_made_brick.json'), 'w'), indent=1)
print(json.dumps(R, indent=1))
# picture: the colour, tiled 2 x 2
tile = np.clip(c0, 0, 1) ** (1 / 2.2)
big = np.vstack([np.hstack([tile, tile]), np.hstack([tile, tile])])
pt.save_png(big, os.path.join(PICS, 'r01_home_made_brick_tiled_2x2.png'))
