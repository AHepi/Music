# Plain note: writes a Material Maker graph file (.ptex) for a red brick wall using ONLY nodes from Material Maker's own library
# (Bricks, Fill-to-random-grey, Colorize, Blend, noise, Normal Map ...), no custom code. It aims at the brick reference picture:
# 12 rows, 4 bricks across per row, pale grey-brown mortar with a dark outline, red/orange/dark brick colours, sooty streaks and pale chips.
# Usage: python3 -I make_brick_stock_graph.py OUT.ptex [--seed N]   (then export it with mm_export.py)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptex_builder import Graph, gradient, colour

out = sys.argv[1]
seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 1

g = Graph()
ROWS, COLS = 12, 4

# 1. layout: the brick pattern (output 0 = grey picture, 0 in mortar and rising to 1 inside the brick; output 1 = "fill" = one id per brick)
brick = g.add('bricks3', 'Bricks', {'pattern': 0, 'repeat': 1, 'rows': ROWS, 'columns': COLS, 'row_offset': 0.5, 'mortar': 0.19, 'bevel': 0.04, 'round': 0.05, 'corner': 0.1}, seed=seed)
# a second, slightly wider-mortar copy: the difference of the two pictures is a thin ring = the dark outline round each brick
brick_outer = g.add('bricks3', 'BricksOuter', {'pattern': 0, 'repeat': 1, 'rows': ROWS, 'columns': COLS, 'row_offset': 0.5, 'mortar': 0.13, 'bevel': 0.012, 'round': 0.06, 'corner': 0.1}, seed=seed)

# masks: brick body (hard edge) and ring
body = g.add('colorize', 'BodyMask', {'gradient': gradient([(0.0, (0, 0, 0)), (0.25, (1, 1, 1))])})
g.connect(brick, 0, body, 0)
outer = g.add('colorize', 'OuterMask', {'gradient': gradient([(0.0, (0, 0, 0)), (0.05, (1, 1, 1))])})
g.connect(brick_outer, 0, outer, 0)
ring_math = g.add('blend2', 'Ring', {'blend_type1': 11, 'amount1': 1.0})   # 11 = Difference
g.connect(outer, 0, ring_math, 0)
g.connect(body, 0, ring_math, 1)
ring_mask = g.add('colorize', 'RingBoost', {'gradient': gradient([(0.0, (0, 0, 0)), (0.2, (1, 1, 1))])})
g.connect(ring_math, 0, ring_mask, 0)

# 2. one random grey per brick -> brick colour palette (dark / red / orange)
rand_grey = g.add('fill_to_random_grey2', 'PerBrickGrey', {'edgecolor': 1.0}, seed=seed + 11)
g.connect(brick, 1, rand_grey, 0)
palette = [(0.00, (0.30, 0.20, 0.17)), (0.20, (0.45, 0.23, 0.17)), (0.45, (0.55, 0.27, 0.18)), (0.75, (0.65, 0.31, 0.19)), (1.00, (0.74, 0.38, 0.23))]
brick_col = g.add('colorize', 'BrickColour', {'gradient': gradient(palette, interpolation=1)})
g.connect(rand_grey, 0, brick_col, 0)

# 3. blotchy variation inside each brick (value noise -> darker/lighter)
blot = g.add('perlin', 'Blotches', {'scale_x': 12, 'scale_y': 14, 'iterations': 6, 'persistence': 0.6}, seed=seed + 21)
blot_col = g.add('colorize', 'BlotchColour', {'gradient': gradient([(0.0, (0.78, 0.62, 0.55)), (0.5, (1.05, 0.97, 0.92)), (1.0, (1.30, 1.18, 1.08))])})
g.connect(blot, 0, blot_col, 0)
brick_blot = g.add('blend2', 'BrickBlotched', {'blend_type1': 2, 'amount1': 1.0})   # 2 = Multiply
g.connect(brick_col, 0, brick_blot, 0)
g.connect(blot_col, 0, brick_blot, 1)

# 4. sooty streaks (stretched noise) -> dark brown/black, only on some bricks
streak = g.add('noise_anisotropic', 'Streaks', {'scale_x': 40, 'scale_y': 2, 'smoothness': 1, 'interpolation': 1}, seed=seed + 31)
soot_big = g.add('perlin', 'SootAreas', {'scale_x': 4, 'scale_y': 4, 'iterations': 4, 'persistence': 0.6}, seed=seed + 32)
soot_mul = g.add('blend2', 'SootMask', {'blend_type1': 2, 'amount1': 1.0})
g.connect(streak, 0, soot_mul, 0)
g.connect(soot_big, 0, soot_mul, 1)
soot_mask = g.add('colorize', 'SootThreshold', {'gradient': gradient([(0.10, (0.95, 0.95, 0.95)), (0.34, (0, 0, 0))])})
g.connect(soot_mul, 0, soot_mask, 0)
soot_col = g.add('colorize', 'SootColour', {'gradient': gradient([(0.0, (0.08, 0.06, 0.05)), (1.0, (0.2, 0.12, 0.1))])})
g.connect(soot_mul, 0, soot_col, 0)
brick_soot = g.add('blend2', 'BrickSooty', {'blend_type1': 0, 'amount1': 0.9})
g.connect(brick_blot, 0, brick_soot, 0)
g.connect(soot_col, 0, brick_soot, 1)
g.connect(soot_mask, 0, brick_soot, 2)

# 5. pale chips (worn spots showing pale clay): noise -> hard threshold -> tan colour
chip_noise = g.add('fbm4', 'ChipNoise', {'noise': 0, 'scale_x': 14, 'scale_y': 14, 'folds': 0, 'iterations': 5, 'persistence': 0.6, 'lacunarity': 2.0, 'offset': 0}, seed=seed + 41)
chip_mask = g.add('colorize', 'ChipThreshold', {'gradient': gradient([(0.64, (0, 0, 0)), (0.70, (1, 1, 1))])})
g.connect(chip_noise, 0, chip_mask, 0)
chip_col = g.add('colorize', 'ChipColour', {'gradient': gradient([(0.0, (0.62, 0.52, 0.40)), (1.0, (0.72, 0.60, 0.46))])})
g.connect(chip_noise, 0, chip_col, 0)
brick_chip = g.add('blend2', 'BrickChipped', {'blend_type1': 0, 'amount1': 0.9})
g.connect(brick_soot, 0, brick_chip, 0)
g.connect(chip_col, 0, brick_chip, 1)
g.connect(chip_mask, 0, brick_chip, 2)

# 6. mortar colour, then bricks over mortar, then the dark outline ring over both
mort_noise = g.add('perlin', 'MortarNoise', {'scale_x': 16, 'scale_y': 16, 'iterations': 5, 'persistence': 0.6}, seed=seed + 51)
mort_col = g.add('colorize', 'MortarColour', {'gradient': gradient([(0.0, (0.34, 0.27, 0.22)), (0.6, (0.47, 0.39, 0.31)), (1.0, (0.58, 0.49, 0.39))])})
g.connect(mort_noise, 0, mort_col, 0)
wall = g.add('blend2', 'BricksOnMortar', {'blend_type1': 0, 'amount1': 1.0})
g.connect(mort_col, 0, wall, 0)
g.connect(brick_chip, 0, wall, 1)
g.connect(body, 0, wall, 2)
dark = g.add('uniform', 'OutlineColour', {'color': colour((0.10, 0.07, 0.06))})
wall2 = g.add('blend2', 'WithOutline', {'blend_type1': 0, 'amount1': 0.9})
g.connect(wall, 0, wall2, 0)
g.connect(dark, 0, wall2, 1)
g.connect(ring_mask, 0, wall2, 2)

# 7. painterly flattening: Kuwahara filter (keeps edges, turns noise into flat painted patches), then the maps the way the reference was made:
#    height = brightness of the colour picture, normal map = slope of that height
paint = g.add('generalized_kuwahara', 'PaintedLook', {'buffer': 1, 'resolution': 11, 'size': 6})
g.connect(wall2, 0, paint, 0)
grey = g.add('greyscale', 'BrightnessOfColour', {'mode': 4})
g.connect(paint, 0, grey, 0)
height = g.add('colorize', 'Height', {'gradient': gradient([(0.0, (0.0, 0.0, 0.0)), (0.55, (0.8, 0.8, 0.8)), (1.0, (1.0, 1.0, 1.0))])})
g.connect(grey, 0, height, 0)
normal = g.add('normal_map2', 'NormalFromHeight', {'strength': 1.0, 'size': 11})
g.connect(height, 0, normal, 0)

# 8. roughness and ambient occlusion
rough = g.add('colorize', 'Roughness', {'gradient': gradient([(0.0, (0.95, 0.95, 0.95)), (1.0, (0.78, 0.78, 0.78))])})
g.connect(brick, 0, rough, 0)
ao = g.add('colorize', 'AmbientOcclusion', {'gradient': gradient([(0.0, (0.45, 0.45, 0.45)), (0.3, (0.9, 0.9, 0.9)), (1.0, (1, 1, 1))])})
g.connect(brick, 0, ao, 0)

# 9. the material node collects the maps
mat = g.material('Material', metallic=0.0, depth_scale=0.5)
if '--probe' in sys.argv:
    # debug mode: show intermediate pictures through the spare outputs (port: 0 albedo, 1 metal, 2 rough, 3 emission, 5 occlusion, 6 depth, 8 sss)
    probes = dict(item.split('=') for item in sys.argv[sys.argv.index('--probe') + 1].split(','))
    for port, node in probes.items():
        g.connect(node, 0, mat, int(port))
else:
    g.connect(paint, 0, mat, 0)
    g.connect(rough, 0, mat, 2)
    g.connect(normal, 0, mat, 4)
    g.connect(ao, 0, mat, 5)
    g.connect(height, 0, mat, 6)
g.save(out)
print('wrote', out, 'with', len(g.nodes), 'nodes and', len(g.connections), 'connections')
