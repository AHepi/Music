# What this does: tests "snapping the coordinate to a grid" (Vector Math Snap / Floor on u and v before the pattern reads them): every little square of the
# picture then reads one single pattern value, so edges become staircases of squares (a pixel-painting / blocky-brush look; the reference patch edges
# look stair-stepped at 3-8 px). Renders 1254 px close-ups (a 300 x 300 crop) for several grid counts and checks the tile still repeats.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
import hp_tools as hp, recipe_tools as rt
BASE = os.path.join(hp.OUT, 'pictures'); os.makedirs(os.path.join(BASE, 'c16_coordinate_snap'), exist_ok=True)
hp.SAMPLES = 4
def snapped(grid, warp=0.004, name='snap'):
    tree, w = hp.new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor')])
    src = ('in', 'Vector')
    if warp > 0:
        hp.instance(w, hp.warp_vector_group(name + ' warp'), 'warp', x=0, Amount=warp, Scale=40.0); w.link('in', 'Vector', 'warp', 'Vector'); src = ('warp', 'Vector')
    if grid:
        w.vector_math('scale up', 'SCALE', x=1); w.link(*src, 'scale up', 0); w.nodes['scale up'].inputs['Scale'].default_value = float(grid)
        w.vector_math('floor', 'FLOOR', x=2); w.link('scale up', 0, 'floor', 0)
        w.vector_math('scale down', 'SCALE', x=3); w.link('floor', 0, 'scale down', 0); w.nodes['scale down'].inputs['Scale'].default_value = 1.0 / grid
        src = ('scale down', 0)
    hp.instance(w, rt.tileable_voronoi_group(), 'cells', x=4, Scale=14.0, Randomness=1.0); w.link(*src, 'cells', 'Vector')
    hp.cell_random(w, 'pick', 'cells', 'Color', 0.0, x=5); hp.palette_ramp(w, 'palette', hp.BRICK_PALETTE, x=6); w.link('pick', 'Value', 'palette', 'Fac'); w.link('palette', 'Color', 'out', 'Colour')
    return tree
grids = [0, 400, 250, 160, 100, 60]
labels = ['no snap'] + [f'grid {g} ({1254 / g:.0f} px blocks)' for g in grids[1:]]
files = []
for i, g in enumerate(grids):
    p = os.path.join(BASE, 'c16_coordinate_snap', f'full_{i}.png')
    hp.photograph_group(lambda: snapped(g, name=f'sn{i}'), 'Colour', p, 1254)
    a = hp.load(p)[400:700, 400:700]
    hp.save(a, os.path.join(BASE, 'c16_coordinate_snap', f'crop_{i}.png'))
    files.append(f'crop_{i}.png')
json.dump({'files': files, 'labels': labels}, open(os.path.join(BASE, 'c16_coordinate_snap', 'sweep.json'), 'w'))
import subprocess
subprocess.run(['python3', '-I', os.path.join(hp.LIB, 'make_strip.py'), os.path.join(BASE, 'c16_coordinate_snap'), os.path.join(BASE, 'c16_coordinate_snap', 'strip.png'), '--columns', '6', '--title', 'Coordinate snapped to a grid before the cells read it (300 x 300 px crops of a 1254 tile)', '--cell', '250'], check=True)
res = {}
for g in (250, 100):
    res[f'grid {g}'] = hp.periodicity_check(lambda: snapped(g, name='pc'), 'Colour', 192) if False else None
print(json.dumps(res))
