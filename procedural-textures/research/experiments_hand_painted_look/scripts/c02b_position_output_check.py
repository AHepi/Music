# What this does: checks why a palette picked from the Voronoi 'Position' output showed straight cuts inside cells. Renders the Position output
# (x, y, z parts) and a white-noise hash of it, next to the Voronoi 'Color' output, for the seamless 4D cells.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
BASE = os.path.join(hp.OUT, 'pictures', 'c02b_position_check'); os.makedirs(BASE, exist_ok=True)
hp.SAMPLES = 1
def make(which):
    def b():
        tree, w = hp.new_group('pos_' + which, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
        hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=0, Scale=6.0, Randomness=1.0)
        w.link('in', 'Vector', 'cells', 'Vector')
        if which in ('pos_x', 'pos_y', 'pos_z'):
            w.add('ShaderNodeSeparateXYZ', 'sep', x=1); w.link('cells', 'Position', 'sep', 'Vector')
            w.add('ShaderNodeMapRange', 'mr', x=2, clamp=True)
            w.nodes['mr'].inputs['From Min'].default_value = -1.2; w.nodes['mr'].inputs['From Max'].default_value = 1.2
            w.link('sep', which[-1].upper(), 'mr', 'Value'); w.link('mr', 'Result', 'out', 'Height')
        elif which == 'white_of_pos':
            hp.cell_random(w, 'wn', 'cells', 'Position', 0.0, x=1); w.link('wn', 'Value', 'out', 'Height')
        elif which == 'color_r':
            w.add('ShaderNodeSeparateColor', 'sep', x=1); w.link('cells', 'Color', 'sep', 'Color'); w.link('sep', 'Red', 'out', 'Height')
        return tree
    return b
names = ['pos_x', 'pos_y', 'pos_z', 'white_of_pos', 'color_r']
for i, n in enumerate(names):
    hp.photograph_group(make(n), 'Height', os.path.join(BASE, f'{i}_{n}.png'), 320)
    a = hp.load(os.path.join(BASE, f'{i}_{n}.png'))[..., 0]
    # count straight cuts: columns/rows with large mean abs change that are very long straight edges
    dx = np.abs(np.diff(a, axis=1)); col_activity = (dx > 0.2).mean(axis=0)
    print(n, 'strongest vertical-edge column share %.2f at x=%d' % (col_activity.max(), col_activity.argmax()))

# --- the fix: hash the Color output (stable bits) instead of Position, or round Position first
def make2(which):
    def b():
        tree, w = hp.new_group('fix_' + which, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
        hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=0, Scale=6.0, Randomness=1.0)
        w.link('in', 'Vector', 'cells', 'Vector')
        if which == 'white_of_color':
            hp.cell_random(w, 'wn', 'cells', 'Color', 0.0, x=1); w.link('wn', 'Value', 'out', 'Height')
        elif which == 'white_of_rounded_pos':
            w.vector_math('snap', 'SNAP', x=1); w.link('cells', 'Position', 'snap', 0); w.nodes['snap'].inputs[1].default_value = (0.01, 0.01, 0.01)
            hp.cell_random(w, 'wn', 'snap', 0, 0.0, x=2); w.link('wn', 'Value', 'out', 'Height')
        return tree
    return b
for i, n in enumerate(['white_of_color', 'white_of_rounded_pos']):
    hp.photograph_group(make2(n), 'Height', os.path.join(BASE, f'9_{n}.png'.replace('9_', f'{5+i}_')), 320)
    a = hp.load(os.path.join(BASE, f'{5+i}_{n}.png'))[..., 0]
    dx = np.abs(np.diff(a, axis=1)); col_activity = (dx > 0.2).mean(axis=0)
    print(n, 'strongest vertical-edge column share %.2f at x=%d' % (col_activity.max(), col_activity.argmax()))
for n, b in (('hash of Position', make('white_of_pos')), ('hash of Color', make2('white_of_color')), ('hash of rounded Position', make2('white_of_rounded_pos'))):
    print(n, hp.periodicity_check(b, 'Height', 192))
