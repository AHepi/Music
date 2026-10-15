# What this does: builds the far town seen beyond the Works ("34 Plan - chapter 2 full redesign", part 1 A)
# at true size in Blender by script, and writes it to assets/models/inflation-chapter-2-newcomers/works/:
#   far-town.glb    for the film (one root, "far-town")
#   far-town.blend  for drawing plates (its pictures stay outside the file)
# The old town of build_town.py (a model-set town at about a tenth of true size, around the old two
# factories) is left as it is, with the old models in assets/models/inflation-chapter-2/.
#
# What is in it, all behind the works (the Works' layout as in works_kit.py: y away from the lane, 0 at
# the works wall; the factories reach back to about 42 m), from about 60 m to 450 m behind the wall:
#   - rows of two-storey terraced houses (slate roofs, chimney stacks with pots, some windows lit),
#     in streets running across, some blocks turned a little, as copies of three row lengths
#   - four tall mills (four and five storeys, many windows lit) with stair towers
#   - eight mill chimneys, 36 to 55 m, round and tapering, sooted at the top, with corbelled caps
#     (markers far-town-chimney-top-1 to -8 at their tops, for smoke)
#   - a gasholder: an iron bell 34 m across inside a guide frame of sixteen columns with girders and
#     cross bracing, 36 m high, far to the left
#   - a church with a stone tower and a broach spire, 58 m to its tip
#   - a dark cinder ground under it all
# From the plan's W3 view (30 m in front of the wall on the lane's centre line, eye 4.6 m up) the factories'
# roofs hide everything in the town lower than about 4.6 m + 0.15 x its distance from the camera, so W3
# shows only the tall things, and only at its edges: the gasholder's frame at the left, the spire and one
# chimney at the right. No far chimney stands where W3 would show it over a factory's roof (it could be
# counted as one of the factories' own: No. 1 has one, No. 2 has two).
# No lettering, no clock faces, no figures, no flags.
#
# Run (paint_works_pictures.py first):
#   blender -b --python build_far_town.py -- [--out FOLDER] [--replace]

import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import works_kit as kit  # noqa: E402

OUT_FOLDER = os.path.abspath(kit.option('--out', kit.WORKS_FOLDER))
REPLACE = kit.flag('--replace')
PREFIX = 'far-town'
chooser = random.Random(7)


def materials():
    return {
        'brick': kit.surface_material('far-town-brick', 'red_brick', tint=(0.46, 0.36, 0.33)),
        'mill brick': kit.surface_material('far-town-mill-brick', 'castle_brick_02_red', tint=(0.4, 0.3, 0.27)),
        'stone': kit.surface_material('far-town-stone', 'stone_brick_wall_001', tint=(0.55, 0.53, 0.5)),
        'slate': kit.surface_material('far-town-slate', 'roof_slates_03', tint=(0.33, 0.35, 0.41), roughness=0.55),
        'iron': kit.surface_material('far-town-iron', 'rusty_metal_02', tint=(0.12, 0.12, 0.12), roughness=0.55, metallic=0.6),
        'gasholder': kit.surface_material('far-town-gasholder-iron', 'rusty_metal_02', tint=(0.2, 0.21, 0.22), roughness=0.6, metallic=0.4),
        'sooted': kit.surface_material('far-town-brick-sooted', 'castle_brick_02_red', tint=(0.14, 0.11, 0.1)),
        'ground': kit.surface_material('far-town-ground', 'muddy_tracks', tint=(0.2, 0.19, 0.18), roughness=0.95),
        'lit': kit.glass_material(PREFIX, 'mill-window-narrow', 'lit'),
        'dark': kit.glass_material(PREFIX, 'mill-window-narrow', 'dark'),
    }


def window(builder, stuff, x0, x1, y, z0, z1, facing, lit):
    """A window quad on a front facing minus y (facing -1) or plus y (facing +1)."""
    corners = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)] if facing < 0 else [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)]
    variant = chooser.randrange(4)
    builder.quad(corners, stuff['lit' if lit else 'dark'], uvs=[(variant / 4, 0), ((variant + 1) / 4, 0), ((variant + 1) / 4, 1), (variant / 4, 1)])


def terrace_row(stuff, houses, seed):
    """One row of two-storey terraced houses at the origin, fronts facing minus y, built once and copied:
    brick walls, a slate roof with its ridge along the row, chimney stacks with two pots on every party
    wall, and two windows a floor on each house, some lit."""
    lit_chance = random.Random(seed)
    builder = kit.MeshBuilder()
    width, depth, eaves, rise = 4.6, 8.0, 6.2, 2.6
    length = houses * width
    builder.box((-length / 2, -depth / 2, 0.0), (length / 2, depth / 2, eaves), stuff['brick'])
    builder.roof_slope((-length / 2 - 0.2, -depth / 2 - 0.3, eaves - 0.15), (length / 2 + 0.2, -depth / 2 - 0.3, eaves - 0.15),
                       (length / 2 + 0.2, 0.0, eaves + rise), (-length / 2 - 0.2, 0.0, eaves + rise), stuff['slate'])
    builder.roof_slope((length / 2 + 0.2, depth / 2 + 0.3, eaves - 0.15), (-length / 2 - 0.2, depth / 2 + 0.3, eaves - 0.15),
                       (-length / 2 - 0.2, 0.0, eaves + rise), (length / 2 + 0.2, 0.0, eaves + rise), stuff['slate'])
    for end in (-1, 1):
        builder.prism([(-depth / 2, eaves), (depth / 2, eaves), (0.0, eaves + rise)], end * length / 2 - (0.3 if end > 0 else 0),
                      end * length / 2 + (0.3 if end < 0 else 0), stuff['brick'], axis='x')
    for k in range(houses + 1):
        x = -length / 2 + k * width
        builder.box((x - 0.35, -0.6, eaves + rise - 0.6), (x + 0.35, 0.6, eaves + rise + 1.3), stuff['brick'])
        for pot in (-0.3, 0.3):
            builder.lathe([(0.15, eaves + rise + 1.3), (0.12, eaves + rise + 1.85)], stuff['sooted'], centre=(x, pot, 0), sides=6, smooth=False)
    for k in range(houses):
        x = -length / 2 + (k + 0.5) * width
        for z0, z1 in ((1.0, 2.5), (3.8, 5.3)):
            for offset in (-1.1, 1.1):
                window(builder, stuff, x + offset - 0.45, x + offset + 0.45, -depth / 2 - 0.02, z0, z1, -1, lit_chance.random() < 0.3)
                window(builder, stuff, x + offset - 0.45, x + offset + 0.45, depth / 2 + 0.02, z0, z1, 1, lit_chance.random() < 0.15)
    return builder, length


def place_rows(stuff, parent):
    """Streets of terraced rows behind the works, as copies of three row lengths."""
    modules = {}
    for houses, seed in ((8, 1), (12, 2), (16, 3)):
        builder, length = terrace_row(stuff, houses, seed)
        part = builder.finish(f'far-town-terrace-of-{houses}', parent=parent)
        modules[houses] = (part, length)
    used = set()
    count = 0
    y = 62.0
    while y < 440.0:
        x = -260.0 + chooser.uniform(0, 30)
        while x < 260.0:
            houses = chooser.choice((8, 12, 16))
            part, length = modules[houses]
            if x + length > 260.0:
                break
            turn = math.radians(chooser.choice((0, 0, 0, 4, -6, 9)))
            if houses not in used:
                copy = part                      # the first use moves the row itself
                used.add(houses)
            else:
                copy = bpy.data.objects.new(f'far-town-terrace-{count + 1:03d}', part.data)
                kit.collection('parts').objects.link(copy)
                copy.parent = parent
            copy.location = (x + length / 2, y + chooser.uniform(-1.5, 1.5), 0.0)
            copy.rotation_euler.z = turn
            count += 1
            x += length + chooser.choice((6.0, 8.0, 10.0, 14.0))
        y += chooser.choice((19.0, 21.0, 24.0))
    return count


def town_mill(stuff, parent, name, x, y, width, depth, storeys, turn):
    """A tall mill: brick walls with rows of windows on its two long sides (some lit), a slate roof, a
    stair tower at one end."""
    builder = kit.MeshBuilder()
    floor = 3.8
    height = storeys * floor + 1.0
    builder.box((x - width / 2, y - depth / 2, 0.0), (x + width / 2, y + depth / 2, height), stuff['mill brick'])
    rise = depth / 2 * math.tan(math.radians(25))
    builder.roof_slope((x - width / 2 - 0.3, y - depth / 2 - 0.3, height - 0.1), (x + width / 2 + 0.3, y - depth / 2 - 0.3, height - 0.1),
                       (x + width / 2 + 0.3, y, height + rise), (x - width / 2 - 0.3, y, height + rise), stuff['slate'])
    builder.roof_slope((x + width / 2 + 0.3, y + depth / 2 + 0.3, height - 0.1), (x - width / 2 - 0.3, y + depth / 2 + 0.3, height - 0.1),
                       (x - width / 2 - 0.3, y, height + rise), (x + width / 2 + 0.3, y, height + rise), stuff['slate'])
    for end in (-1, 1):
        builder.prism([(y - depth / 2, height), (y + depth / 2, height), (y, height + rise)],
                      x + end * width / 2 - (0.4 if end > 0 else 0), x + end * width / 2 + (0.4 if end < 0 else 0), stuff['mill brick'], axis='x')
    tower_x = x - width / 2 + 3.0
    builder.box((tower_x - 3.0, y - depth / 2 - 4.0, 0.0), (tower_x + 3.0, y - depth / 2 + 0.5, height + 4.5), stuff['mill brick'])
    builder.box((tower_x - 3.3, y - depth / 2 - 4.3, height + 4.5), (tower_x + 3.3, y - depth / 2 + 0.8, height + 5.1), stuff['stone'])
    bays = int(width / 3.2)
    for storey in range(storeys):
        z0 = storey * floor + 1.0
        for k in range(bays):
            wx = x - width / 2 + (k + 0.5) * width / bays
            if abs(wx - tower_x) < 3.6:
                continue
            for facing in (-1, 1):
                window(builder, stuff, wx - 0.8, wx + 0.8, y + facing * (depth / 2 + 0.02), z0, z0 + 2.2, facing, chooser.random() < 0.55)
    part = builder.finish(f'far-town-{name}', parent=parent, origin=(x, y, 0.0))
    part.rotation_euler.z = turn          # turned about its own middle
    return part


def town_chimney(stuff, parent, number, x, y, height):
    """A round, tapering mill chimney on a square plinth, sooted near the top, with a corbelled cap."""
    builder = kit.MeshBuilder()
    builder.box((x - 2.4, y - 2.4, 0.0), (x + 2.4, y + 2.4, 5.0), stuff['mill brick'])
    bottom, top = 1.9, 1.15
    radius_at = lambda z: bottom + (top - bottom) * (z - 5.0) / (height - 6.5)
    builder.lathe([(bottom, 5.0), (radius_at(height * 0.72), height * 0.72)], stuff['mill brick'], centre=(x, y, 0), sides=16)
    builder.lathe([(radius_at(height * 0.72), height * 0.72), (top, height - 1.5)], stuff['sooted'], centre=(x, y, 0), sides=16)
    builder.lathe([(top + 0.15, height - 1.5), (top + 0.35, height - 0.8), (top + 0.35, height), (top - 0.2, height), (0.001, height - 0.8)],
                  stuff['sooted'], centre=(x, y, 0), sides=16, smooth=False)
    builder.finish(f'far-town-chimney-{number}', parent=parent)
    kit.empty(f'far-town-chimney-top-{number}', (x, y, height + 0.4), parent=ROOT)


def gasholder(stuff, parent, x, y):
    """A gasholder: an iron bell with a domed crown inside a guide frame of sixteen columns, three girder
    rings and crosswise bracing, on a low brick ring."""
    builder = kit.MeshBuilder()
    radius, bell_top, frame_top, columns = 17.0, 22.0, 36.0, 16
    builder.lathe([(radius + 1.5, 0.0), (radius + 1.5, 2.0), (0.001, 2.0)], stuff['brick'], centre=(x, y, 0), sides=48, smooth=False)
    builder.lathe([(radius, 2.0), (radius, bell_top), (radius * 0.8, bell_top + 2.2), (radius * 0.45, bell_top + 3.2), (0.001, bell_top + 3.6)],
                  stuff['gasholder'], centre=(x, y, 0), sides=48)
    for band in (7.0, 12.0, 17.0, 21.5):
        builder.lathe([(radius + 0.12, band - 0.25), (radius + 0.12, band + 0.25)], stuff['iron'], centre=(x, y, 0), sides=48)
    ring = radius + 2.6
    points = [(x + ring * math.cos(2 * math.pi * k / columns), y + ring * math.sin(2 * math.pi * k / columns)) for k in range(columns)]
    levels = (2.0, 13.0, 24.5, frame_top)
    for px, py in points:
        builder.centred_box((px, py, frame_top / 2), (0.9, 0.9, frame_top), stuff['iron'])
        builder.centred_box((px, py, frame_top + 0.6), (1.3, 1.3, 1.2), stuff['iron'])
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        for level in levels[1:]:
            builder.beam((ax, ay, level), (bx, by, level), 0.5, 1.2, stuff['iron'])
        for low, high in zip(levels, levels[1:]):
            builder.beam((ax, ay, low), (bx, by, high), 0.25, 0.25, stuff['iron'])
            builder.beam((bx, by, low), (ax, ay, high), 0.25, 0.25, stuff['iron'])
    builder.finish('far-town-gasholder-frame-and-bell', parent=parent)


def church(stuff, parent, x, y):
    """A stone church: a nave with a steep slate roof, and a west tower with a parapet and pinnacles
    carrying an octagonal broach spire."""
    builder = kit.MeshBuilder()
    nave_width, nave_length, walls = 12.0, 30.0, 10.0
    builder.box((x - nave_width / 2, y, 0.0), (x + nave_width / 2, y + nave_length, walls), stuff['stone'])
    builder.roof_slope((x - nave_width / 2 - 0.4, y + nave_length, walls - 0.2), (x - nave_width / 2 - 0.4, y, walls - 0.2),
                       (x, y, walls + 6.5), (x, y + nave_length, walls + 6.5), stuff['slate'])
    builder.roof_slope((x + nave_width / 2 + 0.4, y, walls - 0.2), (x + nave_width / 2 + 0.4, y + nave_length, walls - 0.2),
                       (x, y + nave_length, walls + 6.5), (x, y, walls + 6.5), stuff['slate'])
    builder.prism([(x - nave_width / 2, walls), (x + nave_width / 2, walls), (x, walls + 6.5)], y + nave_length - 0.6, y + nave_length, stuff['stone'], axis='y')
    tower = 8.0
    tower_top = 26.0
    builder.box((x - tower / 2, y - tower, 0.0), (x + tower / 2, y, tower_top), stuff['stone'])
    builder.box((x - tower / 2 - 0.3, y - tower - 0.3, tower_top), (x + tower / 2 + 0.3, y + 0.3, tower_top + 1.0), stuff['stone'])
    for corner_x in (-1, 1):
        for corner_y in (-1, 1):
            builder.lathe([(0.5, tower_top + 1.0), (0.001, tower_top + 4.0)], stuff['stone'],
                          centre=(x + corner_x * (tower / 2 - 0.2), y - tower / 2 + corner_y * (tower / 2 - 0.2), 0), sides=4, smooth=False)
    builder.lathe([(tower / 2 - 0.4, tower_top + 1.0), (0.12, 58.0), (0.001, 58.2)], stuff['slate'], centre=(x, y - tower / 2, 0), sides=8, smooth=False)
    builder.rod((x, y - tower / 2, 58.0), (x, y - tower / 2, 59.6), 0.08, stuff['iron'], sides=6)
    builder.finish('far-town-church-and-spire', parent=parent)


def ground(stuff, parent):
    builder = kit.MeshBuilder()
    builder.box((-700.0, 42.0, -0.2), (700.0, 900.0, -0.01), stuff['ground'])
    builder.finish('far-town-cinder-ground', parent=parent)


def main():
    global ROOT
    paths = [os.path.join(OUT_FOLDER, f'far-town.{ending}') for ending in ('glb', 'blend')]
    kit.stop_if_files_exist(paths, REPLACE)
    kit.empty_scene()
    ROOT = kit.empty('far-town', size=5.0, collection_name='roots')
    stuff = materials()
    groups = {name: kit.empty(f'far-town-{name}', parent=ROOT) for name in ('terraces', 'mills', 'chimneys', 'gasholder', 'church', 'ground')}
    rows = place_rows(stuff, groups['terraces'])
    for name, x, y, width, depth, storeys, turn in (('mill-1', -95.0, 118.0, 56.0, 20.0, 5, 0.0), ('mill-2', 70.0, 132.0, 48.0, 18.0, 4, math.radians(-8)),
                                                     ('mill-3', -18.0, 250.0, 60.0, 20.0, 5, math.radians(5)), ('mill-4', 150.0, 300.0, 50.0, 18.0, 4, 0.0)):
        town_mill(stuff, groups['mills'], name, x, y, width, depth, storeys, turn)
    for number, (x, y, height) in enumerate(CHIMNEYS, start=1):
        town_chimney(stuff, groups['chimneys'], number, x, y, height)
    # the gasholder far to the left, so W3 shows only the edge of its frame and it does not crowd No. 1's
    # chimney; the spire to the right, where W3 sees it over the low end of No. 2's roof
    gasholder(stuff, groups['gasholder'], -75.0, 175.0)
    church(stuff, groups['church'], 95.0, 300.0)
    ground(stuff, groups['ground'])
    bpy.context.view_layer.update()
    parts = kit.descendants(ROOT)
    low, high = kit.bounds(parts)
    print(f'far-town: {len(parts)} objects ({rows} terrace rows), {kit.count_triangles(parts)} triangles, '
          f'from {tuple(round(v, 1) for v in low)} to {tuple(round(v, 1) for v in high)}')
    os.makedirs(OUT_FOLDER, exist_ok=True)
    kit.export_glb(ROOT, paths[0])
    entry = kit.describe(ROOT, paths[0], 'The far town beyond the Works: terraced streets, four tall mills, eight mill chimneys, '
                         'a gasholder and a church spire, about 60 to 450 m behind the works wall.',
                         {'chimneys': [{'x': x, 'y': y, 'height': height} for x, y, height in CHIMNEYS],
                          'gasholder': {'x': -75.0, 'y': 175.0, 'diameter': 34.0, 'frame_height': 36.0},
                          'spire': {'x': 95.0, 'y': 296.0, 'height': 58.0}, 'terrace_rows': rows})
    kit.save_blend(paths[1])
    kit.record(OUT_FOLDER, entry)


ROOT = None
# the town's chimneys stand outside the middle of W3's frame, so W3 never shows a far chimney rising over
# a factory's roof where it could be counted as a third chimney of No. 2 or a second of No. 1: one shows at
# W3's right edge beside the spire, the others beyond its sides (the front views show them all)
CHIMNEYS = ((-118.0, 160.0, 50.0), (-58.0, 128.0, 42.0), (-150.0, 250.0, 48.0), (110.0, 330.0, 52.0),
            (52.0, 112.0, 40.0), (98.0, 250.0, 52.0), (160.0, 196.0, 44.0), (-170.0, 330.0, 36.0))
main()
