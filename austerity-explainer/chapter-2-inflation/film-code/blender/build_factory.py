# What this does: builds one detailed model of a 1915 English munitions works in Blender and writes
# it as a .glb for the three.js stage (chapter 2, pages 3 and 8: the "two factories"). Replaces the
# plain card box (models.js paperFactory) the viewer called "a sudden drop in visual quality".
#
# The model: a brick shed 3.2 wide, 2.0 deep, 1.3 high (the same footprint as before, so the pages'
# layouts still fit) with recessed arched windows and stone sills, brick pilasters, a stone plinth and
# cornice; a four-bay sawtooth roof of corrugated iron with glazed north lights, ridge flashing and
# valley gutters; brick gables with stone copings; downpipes; an open loading door showing the lit
# works inside, with a lamp and a blank sign board; a tall tapered brick chimney with stone bands and
# a corbelled cap; a two-storey office with a slate roof, chimney pots and sash windows; a water tank
# on a steel trestle; a cobbled forecourt with sunken rails; barrels and crates.
#
# Run with Blender's Python module:
#   /home/user/work/blender-env/bin/python build_factory.py OUT.glb [--brick red|brown|yellow]
#       [--office left|right] [--seed N] [--no-bake]
# Lit parts are named so the page can turn them up and down: materials 'window-glow' (windows),
# 'roof-glow' (north lights), 'door-glow' (the works seen through the door), 'lamp-glow'.
# Markers (empties): chimney_top, door, yard, door_lamp, office_door.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402
import textures  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'factory.glb'
option = lambda name, default: arguments[arguments.index(name) + 1] if name in arguments else default
BRICK = option('--brick', 'red')
OFFICE_SIDE = -1 if option('--office', 'left') == 'left' else 1
SEED = int(option('--seed', '1'))
rng = np.random.default_rng(SEED)

W, D, H = 3.2, 2.0, 1.3          # the shed
BAYS, TOOTH = 4, 0.55             # sawtooth roof: bays across the width, height of each tooth
BAY = W / BAYS
FRONT, BACK = -D / 2, D / 2       # Blender -y is the front (three.js +z, towards the camera)

mk.reset()

# ------------------------------------------------------------------------------------- materials
brick = mk.material(f'brick-{BRICK}', name='brick', roughness=0.9)
stone = mk.material('stone', name='stone', roughness=0.85)
roof_iron = mk.material('corrugated', name='roof-iron', roughness=0.55, metallic=0.35)
slate = mk.material('slate', name='slate', roughness=0.7)
planks = mk.material('planks', name='door-planks', roughness=0.8)
iron = mk.material(None, name='iron', colour=(0.035, 0.038, 0.04), roughness=0.45, metallic=0.6)
tank_iron = mk.material('riveted', name='tank-iron', roughness=0.6, metallic=0.3)
setts = mk.material('setts', name='setts', roughness=0.8)
setts['tile_units'] = (0.6, 0.6)   # smaller setts than the texture's default
timber = mk.material('planks', name='crate-timber', roughness=0.85)
terracotta = mk.material(None, name='terracotta', colour=(0.42, 0.2, 0.12), roughness=0.8)
barrel_wood = mk.material(None, name='barrel-wood', colour=(0.22, 0.13, 0.07), roughness=0.75)

window_picture, window_glow_picture = textures.window_glass(columns=4, rows=7, pixels=(192, 336), seed=SEED)
window = mk.material(name='window-glow', roughness=0.25, metallic=0.1, picture=window_picture, glow_picture=window_glow_picture, glow_strength=1.0)
roof_picture, roof_glow_picture = textures.window_glass(columns=12, rows=3, pixels=(768, 192), seed=SEED + 7, broken=0.1)
roof_glass = mk.material(name='roof-glow', roughness=0.2, metallic=0.1, picture=roof_picture, glow_picture=roof_glow_picture, glow_strength=1.0)
office_picture, office_glow_picture = textures.window_glass(columns=2, rows=4, pixels=(160, 288), seed=SEED + 3, broken=0.0)
office_window = mk.material(name='office-glow', roughness=0.25, metallic=0.1, picture=office_picture, glow_picture=office_glow_picture, glow_strength=1.0)
inside = textures.interior(seed=SEED)
door_glow = mk.material(name='door-glow', roughness=1.0, picture=inside, glow_picture=inside, glow_strength=1.0)
lamp = mk.material(None, name='lamp-glow', colour=(1.0, 0.8, 0.5), glow=(1.0, 0.72, 0.4), glow_strength=3.0, roughness=0.4)

# a blank sign board: dark green with a cream border (no words)
sign_picture = Image.new('RGB', (512, 72), (34, 58, 46))
ink = ImageDraw.Draw(sign_picture)
ink.rectangle([6, 6, 505, 65], outline=(196, 180, 140), width=4)
ink.rectangle([16, 16, 495, 55], outline=(150, 136, 104), width=2)
sign = mk.material(name='sign', roughness=0.6, picture=sign_picture)


# --------------------------------------------------------------------------------------- helpers

def arch_outline(half_width, sill, spring, rise, steps=10):
    """Outline (x, z) of an opening with a shallow (segmental) arch on top."""
    radius = (half_width ** 2 + rise ** 2) / (2 * rise)
    centre = spring + rise - radius
    start = math.asin(half_width / radius)
    points = [(-half_width, sill), (half_width, sill), (half_width, spring)]
    for i in range(1, steps):
        a = start - 2 * start * i / steps
        points.append((radius * math.sin(a), centre + radius * math.cos(a)))
    points.append((-half_width, spring))
    return points


def arch_band(name, x, face_y, half_width, spring, rise, thickness=0.035, proud=0.012, material=stone, along='x'):
    """The ring of bricks or stones over an arched opening, standing a little proud of the wall."""
    radius = (half_width ** 2 + rise ** 2) / (2 * rise)
    centre = spring + rise - radius
    start = math.asin(half_width / radius)
    outer, inner = [], []
    steps = 12
    for i in range(steps + 1):
        a = start - 2 * start * i / steps
        outer.append(((radius + thickness) * math.sin(a), centre + (radius + thickness) * math.cos(a)))
        inner.append((radius * math.sin(a), centre + radius * math.cos(a)))
    outline = outer + inner[::-1]
    part = mk.prism(name, outline, proud * 2, at=(0, 0, 0), material=material, axis='y')
    if along == 'x':
        part.location = (x, face_y, 0)
    else:   # on a side wall: turn to face +-x
        part.rotation_euler = (0, 0, math.pi / 2)
        part.location = (face_y, x, 0)
    return part


def frustum(name, bottom_half, top_half, height, at, material, bevel=0.0):
    """A tapering square stack (a chimney)."""
    part = mk.box(name, (bottom_half * 2, bottom_half * 2, height), at=(at[0], at[1], at[2] + height / 2), material=None, map_units=False)
    for v in part.data.vertices:
        if v.co.z > 0:
            v.co.x *= top_half / bottom_half; v.co.y *= top_half / bottom_half
    part.data.materials.append(material)
    if bevel:
        mod = part.modifiers.new('bevel', 'BEVEL'); mod.width = bevel; mod.segments = 2
    mk.box_map(part)
    return part


parts = []
add = lambda p: parts.append(p) or p

# ------------------------------------------------------------------------------------ the shed
walls = add(mk.box('walls', (W, D, H), at=(0, 0, H / 2), material=brick))
cutters = []
FRONT_WINDOWS = [-1.38, -1.02, -0.55, 0.55, 1.02, 1.38]
SIDE_WINDOWS = [-0.55, 0.0, 0.55]
SILL, SPRING, RISE, HALF = 0.36, 0.84, 0.05, 0.11
for x in FRONT_WINDOWS:
    c = mk.prism('cut', arch_outline(HALF, SILL, SPRING, RISE), 0.12, at=(x, FRONT, 0), axis='y', map_units=False)
    cutters.append(c)
for side in (-1, 1):
    for y in SIDE_WINDOWS:
        if side == OFFICE_SIDE and y < 0.3: continue      # the office stands against this side's front half
        c = mk.prism('cut', arch_outline(HALF, SILL, SPRING, RISE), 0.12, at=(0, 0, 0), axis='y', map_units=False)
        c.rotation_euler = (0, 0, math.pi / 2); c.location = (side * W / 2, y, 0)
        cutters.append(c)
# the loading door: a wide arched opening, deep enough to see into
DOOR_HALF, DOOR_TOP = 0.27, 0.74
cutters.append(mk.prism('cut', arch_outline(DOOR_HALF, -0.05, DOOR_TOP, 0.07), 0.5, at=(0, FRONT, 0), axis='y', map_units=False))
mk.cut(walls, cutters)
mk.box_map(walls)

# glass in each window, set back in the opening
for i, x in enumerate(FRONT_WINDOWS):
    add(mk.plane(f'window-{i}', (HALF * 2, SPRING + RISE - SILL), at=(x, FRONT + 0.05, (SILL + SPRING + RISE) / 2), material=window, rotate=(math.pi / 2, 0, 0)))
    add(arch_band(f'arch-{i}', x, FRONT, HALF, SPRING, RISE))
    add(mk.box(f'sill-{i}', (HALF * 2 + 0.06, 0.06, 0.028), at=(x, FRONT - 0.02, SILL - 0.014), material=stone, bevel=0.006))
for side in (-1, 1):
    for j, y in enumerate(SIDE_WINDOWS):
        if side == OFFICE_SIDE and y < 0.3: continue
        add(mk.plane(f'window-side-{side}-{j}', (HALF * 2, SPRING + RISE - SILL), at=(side * (W / 2 - 0.05), y, (SILL + SPRING + RISE) / 2), material=window, rotate=(math.pi / 2, 0, side * math.pi / 2)))
        add(arch_band(f'arch-side-{side}-{j}', y, side * W / 2, HALF, SPRING, RISE, along='y'))
        add(mk.box(f'sill-side-{side}-{j}', (0.06, HALF * 2 + 0.06, 0.028), at=(side * (W / 2 + 0.02), y, SILL - 0.014), material=stone, bevel=0.006))

# plinth, pilasters, cornice
add(mk.box('plinth', (W + 0.05, D + 0.05, 0.1), at=(0, 0, 0.05), material=stone, bevel=0.008))
for x in (-W / 2, -0.8, 0.8, W / 2):
    add(mk.box(f'pilaster-{x:+.1f}', (0.08, 0.035, H - 0.1), at=(x, FRONT - 0.012, 0.1 + (H - 0.1) / 2), material=brick, bevel=0.004))
    add(mk.box(f'pilaster-cap-{x:+.1f}', (0.1, 0.05, 0.03), at=(x, FRONT - 0.018, H - 0.07), material=stone, bevel=0.005))
add(mk.box('cornice', (W + 0.08, D + 0.08, 0.05), at=(0, 0, H - 0.01), material=stone, bevel=0.01))
# a row of small brackets under the cornice (dentils), front only
dentil = mk.box('dentils', (0.025, 0.02, 0.025), at=(-W / 2 + 0.06, FRONT - 0.02, H - 0.05), material=stone)
add(mk.array(dentil, int((W - 0.1) / 0.07), (0.07, 0, 0)))

# the sawtooth roof
angle = math.atan2(TOOTH, BAY)
slope = math.hypot(BAY, TOOTH)
for y, name in ((FRONT + 0.03, 'front'), (BACK - 0.03, 'back')):
    for i in range(BAYS):   # one brick triangle per tooth
        x0 = -W / 2 + i * BAY
        add(mk.prism(f'gable-{name}-{i}', [(x0, 0), (x0 + BAY, 0), (x0 + BAY, TOOTH)], 0.06, at=(0, y, H + 0.015), material=brick, axis='y'))
for i in range(BAYS):
    x0 = -W / 2 + i * BAY
    sheet = mk.corrugated_sheet(f'roof-{i}', D + 0.1, slope + 0.03, material=roof_iron)
    sheet.rotation_mode = 'ZYX'; sheet.rotation_euler = (0, -angle, math.pi / 2)
    sheet.location = (x0 + BAY / 2, 0, H + 0.02 + TOOTH / 2 + 0.012)
    mk.box_map(sheet, (1, 1)); add(sheet)
    for y in (FRONT - 0.015, BACK + 0.015):
        add(mk.box(f'coping-{i}-{y:+.1f}', (slope + 0.02, 0.09, 0.03), at=(x0 + BAY / 2, y, H + 0.03 + TOOTH / 2), material=stone, rotate=(0, -angle, 0), bevel=0.006))
    # the glazed north light on the tooth's upright face, with iron glazing bars
    xg = x0 + BAY
    add(mk.plane(f'north-light-{i}', (TOOTH - 0.05, D - 0.14), at=(xg + 0.004, 0, H + 0.02 + TOOTH / 2), material=roof_glass, rotate=(0, math.pi / 2, 0)))
    for k in range(9):
        add(mk.box(f'glazing-bar-{i}-{k}', (0.012, 0.014, TOOTH - 0.04), at=(xg + 0.012, -D / 2 + 0.07 + k * (D - 0.14) / 8, H + 0.02 + TOOTH / 2), material=iron))
    add(mk.box(f'ridge-{i}', (0.05, D + 0.1, 0.022), at=(xg - 0.012, 0, H + 0.02 + TOOTH + 0.006), material=iron, bevel=0.004))
    add(mk.cylinder(f'valley-gutter-{i}', 0.022, D + 0.14, at=(xg + 0.02, 0, H + 0.04), material=iron, rotate=(math.pi / 2, 0, 0), sides=10))

# downpipes with hopper heads, on the front
for x in (-W / 2 + 0.07, -0.8, 0.8, W / 2 - 0.07):
    # against the wall, held by small brackets
    add(mk.cylinder(f'downpipe-{x:+.1f}', 0.011, H - 0.05, at=(x + 0.065, FRONT - 0.013, 0.05 + (H - 0.05) / 2), material=iron, sides=8))
    add(mk.box(f'hopper-{x:+.1f}', (0.045, 0.04, 0.045), at=(x + 0.065, FRONT - 0.02, H - 0.06), material=iron, bevel=0.004))
    add(mk.box(f'shoe-{x:+.1f}', (0.026, 0.04, 0.02), at=(x + 0.065, FRONT - 0.025, 0.06), material=iron))
    for z in (0.35, 0.75):
        add(mk.box(f'pipe-bracket-{x:+.1f}-{z}', (0.03, 0.012, 0.01), at=(x + 0.065, FRONT - 0.006, z), material=iron))

# roof ventilators
for i, x in enumerate((-0.4, 1.2)):
    add(mk.box(f'vent-{i}', (0.1, 0.1, 0.09), at=(x - 0.1, 0.25 - i * 0.5, H + TOOTH * 0.75 + 0.04), material=iron, bevel=0.006))
    add(mk.cylinder(f'vent-cap-{i}', 0.09, 0.05, at=(x - 0.1, 0.25 - i * 0.5, H + TOOTH * 0.75 + 0.11), material=iron, sides=4, radius_top=0.005, rotate=(0, 0, math.pi / 4)))

# ----------------------------------------------------------------------------- the loading door
add(arch_band('door-arch', 0, FRONT, DOOR_HALF, DOOR_TOP, 0.07, thickness=0.05))
add(mk.plane('door-inside', (DOOR_HALF * 2 + 0.04, DOOR_TOP + 0.1), at=(0, FRONT + 0.24, (DOOR_TOP + 0.1) / 2 - 0.02), material=door_glow, rotate=(math.pi / 2, 0, 0)))
for side in (-1, 1):   # the two leaves, swung open outwards
    # hinged at the opening's edge, closed it would reach the middle; swung 110 degrees outwards
    leaf = mk.box(f'door-leaf-{side}', (DOOR_HALF, 0.025, DOOR_TOP - 0.02), at=(0, 0, 0), material=planks, bevel=0.004)
    for v in leaf.data.vertices: v.co.x -= side * DOOR_HALF / 2
    leaf.rotation_euler = (0, 0, side * math.radians(110))
    leaf.location = (side * DOOR_HALF, FRONT - 0.02, (DOOR_TOP - 0.02) / 2)
    mk.box_map(leaf); add(leaf)
    for k, z in enumerate((0.12, 0.6)):
        b = mk.box(f'door-strap-{side}-{k}', (DOOR_HALF * 0.9, 0.012, 0.025), at=(0, 0, 0), material=iron)
        for v in b.data.vertices: v.co.x -= side * DOOR_HALF * 0.47; v.co.y -= 0.018
        b.rotation_euler = (0, 0, side * math.radians(110)); b.location = (side * DOOR_HALF, FRONT - 0.02, z)
        add(b)
add(mk.box('sign', (0.9, 0.02, 0.12), at=(0, FRONT - 0.03, DOOR_TOP + 0.22), material=sign, bevel=0.004, map_units=False))
sign_part = parts[-1]
# map the sign picture once over its front
import bmesh  # noqa: E402
bm = bmesh.new(); bm.from_mesh(sign_part.data)
uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
for f in bm.faces:
    for loop in f.loops: loop[uv].uv = (loop.vert.co.x / 0.9 + 0.5, loop.vert.co.z / 0.12 + 0.5)
bm.to_mesh(sign_part.data); bm.free()
add(mk.box('lamp-bracket', (0.012, 0.09, 0.012), at=(0, FRONT - 0.05, DOOR_TOP + 0.4), material=iron))
add(mk.box('lamp', (0.04, 0.04, 0.05), at=(0, FRONT - 0.1, DOOR_TOP + 0.37), material=lamp, bevel=0.004))
add(mk.cylinder('lamp-hood', 0.04, 0.02, at=(0, FRONT - 0.1, DOOR_TOP + 0.405), material=iron, sides=8, radius_top=0.012))
mk.marker('door_lamp', (0, FRONT - 0.1, DOOR_TOP + 0.36))

# ------------------------------------------------------------------------------------ the chimney
CX, CY = OFFICE_SIDE * -1 * (W / 2 - 0.45), BACK + 0.32
add(mk.box('chimney-base', (0.38, 0.38, 0.3), at=(CX, CY, 0.15), material=stone, bevel=0.01))
add(frustum('chimney', 0.15, 0.1, 2.75, (CX, CY, 0.3), brick, bevel=0.004))
for z in (1.1, 2.0):
    half = 0.15 - (0.05 * (z - 0.3) / 2.75)
    add(mk.box(f'chimney-band-{z}', (half * 2 + 0.03, half * 2 + 0.03, 0.04), at=(CX, CY, z), material=stone, bevel=0.005))
top = 0.3 + 2.75
for k, (grow, height) in enumerate(((0.025, 0.05), (0.045, 0.05), (0.06, 0.04))):
    add(mk.box(f'chimney-cap-{k}', (0.2 + grow * 2, 0.2 + grow * 2, height), at=(CX, CY, top + 0.025 + k * 0.05), material=brick if k < 2 else stone, bevel=0.004))
add(mk.box('chimney-soot', (0.17, 0.17, 0.02), at=(CX, CY, top + 0.16), material=iron))
add(mk.cylinder('lightning-rod', 0.005, 3.3, at=(CX + 0.1, CY - 0.1, 1.65 + 0.15), material=iron, sides=6))
mk.marker('chimney_top', (CX, CY, top + 0.2))

# ------------------------------------------------------------------------------------- the office
OW, OD, OH = 0.9, 1.1, 1.6
OX, OY = OFFICE_SIDE * (W / 2 + OW / 2), FRONT + OD / 2 + 0.06
office = add(mk.box('office', (OW, OD, OH), at=(OX, OY, OH / 2), material=brick))
office_cuts = []
for floor, z in ((0, 0.2), (1, 0.95)):
    for x in (-0.22, 0.22):
        office_cuts.append(mk.prism('cut', arch_outline(0.085, z, z + 0.42, 0.03), 0.1, at=(OX + x, OY - OD / 2, 0), axis='y', map_units=False))
    for y in (-0.2, 0.25):
        c = mk.prism('cut', arch_outline(0.085, z, z + 0.42, 0.03), 0.1, at=(0, 0, 0), axis='y', map_units=False)
        c.rotation_euler = (0, 0, math.pi / 2); c.location = (OX + OFFICE_SIDE * OW / 2, OY + y, 0)
        office_cuts.append(c)
mk.cut(office, office_cuts); mk.box_map(office)
for floor, z in ((0, 0.2), (1, 0.95)):
    for k, x in enumerate((-0.22, 0.22)):
        add(mk.plane(f'office-window-{floor}-{k}', (0.17, 0.45), at=(OX + x, OY - OD / 2 + 0.04, z + 0.225), material=office_window, rotate=(math.pi / 2, 0, 0)))
        add(mk.box(f'office-sill-{floor}-{k}', (0.23, 0.05, 0.025), at=(OX + x, OY - OD / 2 - 0.015, z - 0.012), material=stone, bevel=0.005))
        add(arch_band(f'office-arch-{floor}-{k}', OX + x, OY - OD / 2, 0.085, z + 0.42, 0.03, thickness=0.025))
    for k, y in enumerate((-0.2, 0.25)):
        add(mk.plane(f'office-side-window-{floor}-{k}', (0.17, 0.45), at=(OX + OFFICE_SIDE * (OW / 2 - 0.04), OY + y, z + 0.225), material=office_window, rotate=(math.pi / 2, 0, OFFICE_SIDE * math.pi / 2)))
        add(mk.box(f'office-side-sill-{floor}-{k}', (0.05, 0.23, 0.025), at=(OX + OFFICE_SIDE * (OW / 2 + 0.015), OY + y, z - 0.012), material=stone, bevel=0.005))
add(mk.box('office-plinth', (OW + 0.04, OD + 0.04, 0.08), at=(OX, OY, 0.04), material=stone, bevel=0.006))
add(mk.box('office-string-course', (OW + 0.04, OD + 0.04, 0.035), at=(OX, OY, 0.8), material=stone, bevel=0.005))
add(mk.box('office-cornice', (OW + 0.07, OD + 0.07, 0.045), at=(OX, OY, OH), material=stone, bevel=0.008))
# hipped slate roof
import bpy  # noqa: E402
roof_mesh = bpy.data.meshes.new('office-roof')
rx, ry, rh = OW / 2 + 0.06, OD / 2 + 0.06, 0.42
verts = [(-rx, -ry, 0), (rx, -ry, 0), (rx, ry, 0), (-rx, ry, 0), (0, -ry + rx * 0.9, rh), (0, ry - rx * 0.9, rh)]
faces = [(0, 1, 4), (1, 2, 5, 4), (2, 3, 5), (3, 0, 4, 5), (0, 3, 2, 1)]
roof_mesh.from_pydata(verts, [], faces)
import bmesh as _bm  # noqa: E402
_b = _bm.new(); _b.from_mesh(roof_mesh); _bm.ops.recalc_face_normals(_b, faces=_b.faces); _b.to_mesh(roof_mesh); _b.free()
office_roof = bpy.data.objects.new('office-roof', roof_mesh)
bpy.context.scene.collection.objects.link(office_roof)
office_roof.location = (OX, OY, OH + 0.022)
office_roof.data.materials.append(slate)
mk.box_map(office_roof, (0.5, 0.5)); add(office_roof)
add(mk.box('office-ridge', (0.03, 2 * (ry - rx * 0.9) + 0.02, 0.025), at=(OX, OY, OH + 0.022 + rh), material=iron))
add(mk.box('office-stack', (0.26, 0.12, 0.42), at=(OX - OFFICE_SIDE * 0.12, OY + 0.18, OH + 0.38), material=brick, bevel=0.004))
add(mk.box('office-stack-cap', (0.3, 0.16, 0.035), at=(OX - OFFICE_SIDE * 0.12, OY + 0.18, OH + 0.6), material=stone, bevel=0.004))
for k in (-1, 1):
    add(mk.cylinder(f'chimney-pot-{k}', 0.028, 0.1, at=(OX - OFFICE_SIDE * 0.12 + k * 0.065, OY + 0.18, OH + 0.665), material=terracotta, sides=12, radius_top=0.022))
# the office door, steps, and a small canopy
DX = OX + OFFICE_SIDE * 0.0
add(mk.box('office-door', (0.17, 0.03, 0.4), at=(DX, OY - OD / 2 - 0.005, 0.28), material=planks, bevel=0.004))
add(mk.box('office-fanlight', (0.17, 0.02, 0.06), at=(DX, OY - OD / 2 - 0.004, 0.52), material=office_window))
for k in range(2):
    add(mk.box(f'office-step-{k}', (0.3 - k * 0.05, 0.09 - k * 0.03, 0.04), at=(DX, OY - OD / 2 - 0.05 + k * 0.015, 0.02 + k * 0.04), material=stone, bevel=0.005))
add(mk.box('office-canopy', (0.3, 0.12, 0.02), at=(DX, OY - OD / 2 - 0.06, 0.6), material=slate, bevel=0.004))
mk.marker('office_door', (DX, OY - OD / 2 - 0.12, 0))

# ----------------------------------------------------------------------- the water tank on a trestle
TX, TY = -OFFICE_SIDE * (W / 2 + 0.38), BACK - 0.45
LEG, TANK_Z = 1.25, 1.25
for sx in (-1, 1):
    for sy in (-1, 1):
        add(mk.box(f'trestle-leg-{sx}{sy}', (0.035, 0.035, LEG), at=(TX + sx * 0.22, TY + sy * 0.22, LEG / 2), material=iron))
for z in (0.45, 0.9):
    for sy in (-1, 1):
        add(mk.box(f'trestle-rail-x-{z}-{sy}', (0.47, 0.02, 0.025), at=(TX, TY + sy * 0.22, z), material=iron))
    for sx in (-1, 1):
        add(mk.box(f'trestle-rail-y-{z}-{sx}', (0.02, 0.47, 0.025), at=(TX + sx * 0.22, TY, z), material=iron))
for sy in (-1, 1):   # diagonal braces
    length = math.hypot(0.44, 0.45)
    add(mk.box(f'trestle-brace-{sy}', (length, 0.012, 0.012), at=(TX, TY + sy * 0.22, 0.675), material=iron, rotate=(0, math.atan2(0.45, 0.44), 0)))
add(mk.box('tank', (0.56, 0.56, 0.36), at=(TX, TY, TANK_Z + 0.18), material=tank_iron, bevel=0.008))
add(mk.box('tank-lid', (0.6, 0.6, 0.025), at=(TX, TY, TANK_Z + 0.37), material=iron, bevel=0.005))
add(mk.cylinder('tank-pipe', 0.014, TANK_Z, at=(TX + 0.18 * OFFICE_SIDE, TY - 0.2, TANK_Z / 2), material=iron, sides=8))

# ------------------------------------------------------------------------------- the forecourt
COURT_W, COURT_D, COURT_Y = W + 2.6, D + 3.4, -0.75
add(mk.box('forecourt', (COURT_W, COURT_D, 0.03), at=(0, COURT_Y, -0.015), material=setts))
for k, (size, at) in enumerate((((COURT_W + 0.06, 0.06, 0.035), (0, COURT_Y - COURT_D / 2, -0.008)), ((COURT_W + 0.06, 0.06, 0.035), (0, COURT_Y + COURT_D / 2, -0.008)),
                                ((0.06, COURT_D, 0.035), (-COURT_W / 2, COURT_Y, -0.008)), ((0.06, COURT_D, 0.035), (COURT_W / 2, COURT_Y, -0.008)))):
    add(mk.box(f'kerb-{k}', size, at=at, material=stone, bevel=0.006))
# rails running into the loading door, sunk flush in the setts (nothing can catch on them)
for side in (-1, 1):
    add(mk.box(f'rail-{side}', (0.014, 2.6, 0.004), at=(side * 0.08, FRONT - 1.3 + 0.2, 0.0005), material=iron))

# ------------------------------------------------------------------------------- yard dressing
# beside the side wall away from the office, behind the line where page 3's queue of workers stands
DRESS_X = -OFFICE_SIDE * (W / 2 + 0.2)
for k in range(5):
    bx = DRESS_X + (rng.random() - 0.5) * 0.12
    by = -0.55 + k * 0.15 + (rng.random() - 0.5) * 0.04
    add(mk.cylinder(f'barrel-{k}', 0.065, 0.17, at=(bx, by, 0.085), material=barrel_wood, sides=14, radius_top=0.065))
    for z in (0.03, 0.14):
        add(mk.cylinder(f'barrel-hoop-{k}-{z}', 0.068, 0.012, at=(bx, by, z), material=iron, sides=14))
for k, (dx, dy, dz) in enumerate(((0, 0, 0), (0.21, 0.02, 0), (0.1, 0.01, 0.2))):
    add(mk.box(f'crate-{k}', (0.2, 0.2, 0.2), at=(-OFFICE_SIDE * (W / 2 + 0.38) + dx * -OFFICE_SIDE - 0.1 * -OFFICE_SIDE, -0.85 + dy, 0.1 + dz), material=timber, bevel=0.006))

mk.marker('door', (0, FRONT - 0.05, 0))
mk.marker('yard', (-0.1, FRONT - 1.1, 0))

mk.finish(OUT, bake='--no-bake' not in arguments, bake_skip=('forecourt', 'kerb', 'rail'))
