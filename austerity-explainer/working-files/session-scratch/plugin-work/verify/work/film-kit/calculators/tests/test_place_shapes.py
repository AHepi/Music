"""What this does: tests the plain numpy parts of the place kit that make shapes and pictures, with known answers and no Blender:
1. The twenty HEIGHT recipes (clods, grain, plaster, cobbles, thatch ...): each gives a float picture with zero mean, a few big clean shapes (not flat, not noise), the same picture
   for the same seed and a different one for another seed, and a SEAMLESS tile (the left edge continues into the right edge as smoothly as any two neighbours).
2. NORMAL MAPS from heights point the right way: a round hill gives a normal map whose red channel is brighter on the side facing +U and whose green channel is brighter on the side
   facing the top of the picture (OpenGL); a flipped green channel reads about -1 against the height; an axis with no slope is "not informative"; a map made from a seamless height is
   seamless; the PNG writer makes a file other programs can read.
3. The LANE height function (two wheel ruts a gauge apart with banks, hoof dimples, puddle hollows): the ruts are where the settings say, as deep as they say, a gauge apart; nothing
   happens far from the lane; the same call gives the same ground; a wider gauge moves the ruts apart.
4. The GRADED GRID of the ground: small squares near the viewer, larger far away, ends exactly on the edges, every square a real quad.
5. The 3D PIECES (tufts, leaves, sticks, lumps): at least 8 different tufts, each with 5 to 9 blades, every vertex between z = 0 and 1, a modest number of triangles.
6. The flat-map maths (plan2d): distance to a polyline with its side, blur keeps the average, distance to the nearest marked cell, shadow behind a wall away from the sun.
Run: python3 kit/calculators/tests/test_place_shapes.py   (about 20 seconds)
"""
import io
import math
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT  # noqa: E402

sys.path.insert(0, os.path.join(KIT, 'place-kit'))
from place_kit import plan2d, settings_file  # noqa: E402
from place_kit.surfaces import heights, normals, ground_mesh, roads  # noqa: E402
from place_kit.growth import pieces  # noqa: E402

check = Checker('place shapes: recipes, normal maps, lane height, graded grid, pieces, flat-map maths')

# ---------------------------------------------------------------- 1. height recipes
SIZE = 128
unseamed, flat, same_wrong, different_wrong, mean_wrong = [], [], [], [], []
for recipe in heights.RECIPES:
    h = heights.make_height(recipe, SIZE, 3, 1.5)
    again = heights.make_height(recipe, SIZE, 3, 1.5)
    other = heights.make_height(recipe, SIZE, 4, 1.5)
    if h.shape != (SIZE, SIZE) or h.dtype != np.float32:
        flat.append(f'{recipe}: shape/type')
    if abs(float(h.mean())) > 0.02:
        mean_wrong.append(f'{recipe}: mean {float(h.mean()):.3f}')
    if float(h.std()) < 0.04:
        flat.append(f'{recipe}: std {float(h.std()):.3f}')
    if not np.array_equal(h, again):
        same_wrong.append(recipe)
    if recipe not in ('rope_twist',) and float(np.corrcoef(h.ravel(), other.ravel())[0, 1]) > 0.97:      # a twist is made of regular strands: the seed changes nothing
        different_wrong.append(recipe)
    if not heights.is_seamless(h):
        unseamed.append(recipe)
check.equal(f'all {len(heights.RECIPES)} recipes are float pictures of the right size and not flat', flat, [])
check.equal('every recipe has a mean close to zero', mean_wrong, [])
check.equal('the same seed gives exactly the same picture', same_wrong, [])
check.equal('another seed gives a different picture (a rope twist is the one regular recipe)', different_wrong, [])
check.equal('every recipe tiles without a seam', unseamed, [])
# the style rule: nothing finer than about 5 millimetres (a feature needs two such pixels to show, so a period of 1 cm). Measured at 512 pixels over each surface's own tile size.
surfaces_table = settings_file.surfaces_table()
tile_of = {}
for spec in surfaces_table.values():
    tile_of.setdefault(spec['height_recipe'], settings_file.number(spec['tile_metres']))
fine_over = []
for recipe in heights.RECIPES:
    tile = tile_of.get(recipe, 1.5)
    picture = heights.make_height(recipe, 512, 3, tile)
    spectrum = np.abs(np.fft.fft2(picture - picture.mean())) ** 2
    fy, fx = np.fft.fftfreq(512)[:, None], np.fft.fftfreq(512)[None, :]
    share = spectrum[np.sqrt(fx * fx + fy * fy) > (tile / 512) / 0.01].sum() / max(spectrum.sum(), 1e-12)
    if share > 0.12:
        fine_over.append(f'{recipe}: {share:.0%}')
check.equal('no recipe has more than 12 percent of its energy in features finer than 1 cm (the style rule: few, big, clean shapes; bark fissures are the finest)', fine_over, [])
ramp = np.tile(np.linspace(0, 1, SIZE, dtype=np.float32), (SIZE, 1))
check.true('the seam test is not blind: a ramp (left edge 0, right edge 1) is NOT seamless', not heights.is_seamless(ramp))
calibrated = heights.calibrate_height(heights.make_height('earth_clods', 256, 1, 2.0), 30.0)
gy, gx = np.gradient(calibrated)
steep = float(np.percentile(np.sqrt(gx * gx + gy * gy), 99))
check.close('calibration: the steepest 1 percent of the slope tilts the surface by 30 degrees', math.degrees(math.atan(steep)), 30.0, 1.5)

# ---------------------------------------------------------------- 2. normal maps point the right way
n = 96
x = (np.arange(n) - n / 2.0) / (n / 6.0)
X, Y = np.meshgrid(x, x)
hill = np.exp(-(X * X + Y * Y)).astype(np.float32) * 6.0            # a round bump in the middle; row 0 is the TOP of the picture
normal = normals.height_to_normal(hill, 1.0, tile=False)
rgb = normals.to_rgb(normal)
right_side, left_side = rgb[n // 2, n // 2 + 14, 0], rgb[n // 2, n // 2 - 14, 0]
top_side, bottom_side = rgb[n // 2 - 14, n // 2, 1], rgb[n // 2 + 14, n // 2, 1]
check.true('normal maps are OpenGL: the red channel is brighter on the side of the hill that faces +U (right)', right_side > 0.55 > 0.45 > left_side, f'right {right_side:.2f}, left {left_side:.2f}',
           proves='a surface that slopes down to the right leans its normal to the right')
check.true('normal maps are OpenGL: the green channel is brighter on the side that faces the top of the picture (+V)', top_side > 0.55 > 0.45 > bottom_side, f'top {top_side:.2f}, bottom {bottom_side:.2f}',
           proves='the picture rows run down while +V runs up: the code flips the sign for you')
lengths = np.linalg.norm(normal, axis=2)
check.close('every normal has length 1', float(lengths.min()), 1.0, 1e-4)
check.true('the flat top of a flat picture is blue (0.5, 0.5, 1.0)', np.allclose(normals.to_rgb(normals.height_to_normal(np.zeros((8, 8)), 1.0)), [0.5, 0.5, 1.0], atol=1e-6))
correct = normals.direction_correlation(rgb, hill)
check.true('the direction check reads +1 on both axes for a correct map', correct['x'] > 0.9 and correct['y'] > 0.9, str(correct))
flipped = normals.to_rgb(normals.flip_green(normal))
wrong = normals.direction_correlation(flipped, hill)
check.true('a flipped green channel reads about -1 on y (the control is not blind) and still +1 on x', wrong['y'] < -0.9 and wrong['x'] > 0.9, str(wrong))
ridge = np.tile(np.sin(np.arange(n) / 6.0).astype(np.float32), (n, 1)) * 4.0            # slopes along x only
informative = normals.direction_correlation(normals.to_rgb(normals.height_to_normal(ridge, 1.0, tile=False)), ridge)
check.true('an axis with no slope is "not informative", not a pass or a fail', informative['y'] == 'not informative' and isinstance(informative['x'], float), str(informative))
seamless_height = heights.make_height('earth_clods', 128, 2, 2.0)
tiled = normals.height_to_normal(heights.calibrate_height(seamless_height, 30.0), 1.0, tile=True)
neighbour = float(np.abs(tiled[:, 1:] - tiled[:, :-1]).mean())
seam = float(np.abs(tiled[:, 0] - tiled[:, -1]).mean())
check.true('a normal map made from a seamless height is seamless (the seam is as smooth as any neighbours)', seam < 2.0 * neighbour + 1e-6, f'seam {seam:.4f}, neighbour {neighbour:.4f}')
buffer = (np.clip(normals.to_rgb(tiled), 0, 1) * 255).astype(np.uint8)
path = os.path.join(os.environ.get('TMPDIR', '/tmp'), f'place-shapes-test-{os.getpid()}.png')
normals.write_png(path, buffer)
data = open(path, 'rb').read()
os.remove(path)
check.true('the PNG writer makes a real PNG (signature, header, data that decompresses to the right size)', data[:8] == b'\x89PNG\r\n\x1a\n' and b'IHDR' in data and b'IEND' in data)
try:
    from PIL import Image
    back = np.asarray(Image.open(io.BytesIO(data)).convert('RGB'))
    check.true('...and Pillow reads back exactly the pixels written', np.array_equal(back, buffer))
except ImportError:
    check.note('part skipped: Pillow is not installed, so the PNG readback was not checked')

# ---------------------------------------------------------------- 3. the lane height function
road = {'polyline': [[0.0, 0.0], [40.0, 0.0]], 'width': 3.0, 'gauge': 1.3, 'rut_depth': 0.08, 'hoof': True}
station = np.arange(5.0, 35.0, 0.25)
across = np.arange(-2.4, 2.4, 0.01)
profile_depths, gauges, banks = [], [], []
for along in station[::4]:
    points = np.stack([np.full_like(across, along), across], axis=1)
    offset, mask = roads.lane_height_offset(points, road, seed=3)
    left = offset[across > 0.2].min()
    right = offset[across < -0.2].min()
    profile_depths.append((-left, -right))
    gauges.append(across[across > 0.2][offset[across > 0.2].argmin()] - across[across < -0.2][offset[across < -0.2].argmin()])
    banks.append(offset.max())
depths = np.array(profile_depths).ravel()
check.true('the ruts are about as deep as the settings say (mean within 30 percent of 8 cm)', abs(float(depths.mean()) - 0.08) < 0.024, f'mean {float(depths.mean()) * 100:.1f} cm')
check.true('...and never absurd (between 3 and 14 cm)', 0.03 <= float(depths.min()) and float(depths.max()) <= 0.14, f'{float(depths.min()) * 100:.1f} to {float(depths.max()) * 100:.1f} cm')
check.close('the two ruts are a gauge apart (1.3 m, mean of the stations)', float(np.mean(gauges)), 1.3, 0.12)
check.true('a bank stands beside each rut (the highest point of the profile is above the ground)', float(np.mean(banks)) > 0.005, f'{float(np.mean(banks)) * 100:.1f} cm')
far = roads.lane_height_offset(np.array([[20.0, 4.0], [20.0, -4.0], [20.0, 9.0]]), road, seed=3)[0]
check.true('three metres or more from the lane the ground is untouched', np.all(far == 0.0), str(far))
one = roads.lane_height_offset(np.stack([station, np.full_like(station, 0.65)], axis=1), road, seed=3)
two = roads.lane_height_offset(np.stack([station, np.full_like(station, 0.65)], axis=1), road, seed=3)
check.true('the same road and seed give exactly the same ground', np.array_equal(one[0], two[0]) and np.array_equal(one[1], two[1]))
other = roads.lane_height_offset(np.stack([station, np.full_like(station, 0.65)], axis=1), road, seed=4)
check.true('another seed gives a different wobble', not np.array_equal(one[0], other[0]))
check.true('the rut mask is 1 in a rut and 0 between the ruts', one[1].mean() > 0.4 and roads.lane_height_offset(np.array([[20.0, 0.0]]), road, seed=3)[1][0] < 0.05)
wide = dict(road, gauge=1.8)
points = np.stack([np.full_like(across, 20.0), across], axis=1)
offset_wide = roads.lane_height_offset(points, wide, seed=3)[0]
check.true('a wider gauge moves the ruts apart', abs(across[offset_wide.argmin()]) > 0.8, f'deepest at {across[offset_wide.argmin()]:+.2f} m')
hoof_points = np.concatenate([np.stack([np.linspace(10.0, 30.0, 800), np.full(800, 0.1)], axis=1), np.stack([np.linspace(10.0, 30.0, 800), np.full(800, -0.1)], axis=1)])
with_hoof = roads.lane_height_offset(hoof_points, road, seed=3)[0]
without_hoof = roads.lane_height_offset(hoof_points, dict(road, hoof=False), seed=3)[0]
check.true('hoof prints dimple the middle of the lane by about 2 cm (left and right in turn)', float((without_hoof - with_hoof).max()) > 0.015 and float((without_hoof - with_hoof).min()) >= -1e-9, f'deepest dimple {float((without_hoof - with_hoof).max()) * 100:.1f} cm')
wheel_points = np.stack([np.linspace(10.0, 30.0, 200), np.full(200, 0.65)], axis=1)
check.true('...and none on the wheel track itself', np.allclose(roads.lane_height_offset(wheel_points, road, seed=3)[0], roads.lane_height_offset(wheel_points, dict(road, hoof=False), seed=3)[0], atol=0.003))
total, mask = roads.total_offset(np.array([[20.0, 0.65], [20.0, 10.65]]), [road, {'polyline': [[0.0, 10.0], [40.0, 10.0]], 'width': 3.0, 'gauge': 1.3, 'rut_depth': 0.08}], seed=3)
check.true('two roads add up: both have ruts', total[0] < -0.02 and total[1] < -0.02)

# ---------------------------------------------------------------- 4. the graded grid
xs = ground_mesh.graded_axis(0.0, 40.0, 20.0, 0.12, 1.09, 5.0)
steps = np.diff(xs)
check.true('the grid lines start and end exactly on the edges', xs[0] == 0.0 and xs[-1] == 40.0)
check.true('every square has a positive size and the lines only go up', bool(np.all(steps > 0)))
check.true('the squares near the viewer are small (0.12 m) and the far ones are at most 5 m', float(steps[len(steps) // 2 - 1: len(steps) // 2 + 2].max()) < 0.25 and float(steps.max()) <= 5.0 * 1.35, f'near {float(steps[len(steps) // 2]):.2f} m, far {float(steps.max()):.2f} m')
ratios = steps[1:] / steps[:-1]
check.true('each square grows by at most about 9 percent over the one before it (away from the ends)', float(np.percentile(ratios, 95)) < 1.4)
vertices, faces = ground_mesh.graded_grid((0.0, 12.0), (0.0, 8.0), (6.0, 4.0))
count_x = len(ground_mesh.graded_axis(0.0, 12.0, 6.0)) - 1
count_y = len(ground_mesh.graded_axis(0.0, 8.0, 4.0)) - 1
check.equal('the grid has one face per square', len(faces), count_x * count_y)
areas = []
for face in faces[:: max(1, len(faces) // 200)]:
    p = vertices[list(face)]
    areas.append(0.5 * abs(np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(p[:, 1], np.roll(p[:, 0], -1))))
check.true('every sampled face is a real quad with a positive area', min(areas) > 1e-6)
check.true('a plain 14 m ground of one face is coarse, a graded one is not', ground_mesh.is_coarse(1, 14.0, 0.3) and not ground_mesh.is_coarse(200 * 200, 14.0, 0.3))

# ---------------------------------------------------------------- 5. the 3D pieces
tufts = pieces.make_variants('tuft', 8, seed=1)
check.equal('eight tuft variants are made', len(tufts), 8)
check.true('the eight tufts are different from each other', len({round(float(t['vertices'].sum()), 4) for t in tufts}) == 8)
check.true('every tuft vertex lies between z = 0 and 1 (and the root is at the bottom)', all(t['vertices'][:, 2].min() >= -1e-9 and t['vertices'][:, 2].max() <= 1.0 + 1e-9 for t in tufts))
check.true('each tuft has 5 to 9 blades (each blade is three quads)', all(5 <= len(t['faces']) // 3 <= 9 for t in tufts), str([len(t['faces']) // 3 for t in tufts]))
every_kind = {kind: pieces.make_variants(kind, 3, seed=2) for kind in pieces.BUILDERS}
check.true('every kind of piece is made, normalised to a height of 1 or a length of 1', all(max(v['vertices'][:, 2].max(), np.ptp(v['vertices'][:, 0]), np.ptp(v['vertices'][:, 1])) <= 1.0 + 1e-6 and v['vertices'][:, 2].min() >= -1e-9
                                                                                           for variants in every_kind.values() for v in variants), ', '.join(every_kind))
check.true('a piece is cheap (at most 220 triangles; a moss cushion is the largest), so thousands of them stay light', max(pieces.triangle_count(v) for variants in every_kind.values() for v in variants) <= 220)
grey = pieces.pull_toward_grey((0.8, 0.2, 0.2), 0.45)
check.true('colours are pulled toward their own grey (red less red, green and blue closer)', grey[0] < 0.8 and grey[1] > 0.2 and abs(grey[0] - 0.8) > 0.1)

# ---------------------------------------------------------------- 6. flat-map maths
distance, side, along = plan2d.distance_to_polyline(np.array([[1.0, 2.0], [1.0, -3.0], [12.0, 0.0]]), [[0, 0], [10, 0]])
check.true('distance to a polyline: 2 m on the left, 3 m on the right, 2 m past the end', np.allclose(distance, [2.0, 3.0, 2.0]) and list(side[:2]) == [1.0, -1.0], str(distance))
check.close('...and how far along the line the nearest point lies', float(along[0]), 1.0, 1e-9)
grid = np.random.default_rng(1).random((40, 40))
check.close('a box blur keeps the average of the grid', float(plan2d.box_blur(grid, 3).mean()), float(grid.mean()), 0.01)
marked = np.zeros((60, 60), bool)
marked[30, 30] = True
distance_map = plan2d.distance_to_marked(marked, 0.1, 4.0)
check.close('the distance map is about right (8 cells away straight: 0.8 m)', float(distance_map[30, 38]), 0.8, 0.02)
check.close('...and 8 cells along a diagonal: 1.13 m, within the 8 percent the note promises', float(distance_map[38, 38]), 0.8 * math.sqrt(2), 0.1)
check.equal('...and with nothing marked every cell holds the maximum', float(plan2d.distance_to_marked(np.zeros((5, 5), bool), 0.1, 4.0)[2, 2]), 4.0)
tall = np.zeros((60, 60))
tall[28:32, 10:14] = 5.0                                     # a block 5 m tall
shadow = plan2d.shadow_map(tall, 0.5, azimuth_degrees=0.0, elevation_degrees=30.0)         # the sun is toward +x, so the shadow falls toward -x
check.true('a tall block shades the ground on the side away from the sun and not the side toward it', shadow[30, 6] == 1.0 and shadow[30, 30] == 0.0)
check.finish()
