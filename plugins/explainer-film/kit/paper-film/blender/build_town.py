# What this does: builds the industrial town around the "two factories" (chapter 2, pages 3 and 8)
# in Blender and writes it as one .glb: the ground of the model set (cinder yards, a cobbled street
# running between the two works, kerbs and pavements, gas lamps), rows of terraced houses with slate
# roofs, chimney stacks and lit windows, other works with tall round chimneys, a gasholder and a
# railway viaduct further back, and a few things near the camera (a low wall with railings, a lamp
# post, crates) to fill the bottom of a tall frame. The viewer said the old set had "a sudden drop in
# visual quality" and asked to "fill the frame": this is the frame's top and bottom.
#
# Positions are in the three.js set's own units (factory A at x -1.4, z +2.2; factory B at x +1.6,
# z -4.2; the camera looks towards -z). Blender's y is three.js's -z, so this script converts.
#
# Run: /home/user/work/blender-env/bin/python build_town.py OUT.glb
# Markers: smoke-0, smoke-1, ... (tops of the far chimneys), lamp-0, lamp-1, ... (gas lamp heads).

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402
import textures  # noqa: E402
import numpy as np  # noqa: E402
import bpy  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'town.glb'
rng = np.random.default_rng(7)
mk.reset()


def at(x, z, y=0.0):
    """three.js (x, y up, z towards camera) -> Blender (x, y back, z up)."""
    return (x, -z, y)


# ------------------------------------------------------------------------------------- materials
cinders = mk.material('cinders', name='cinders', roughness=0.95)
setts = mk.material('setts', name='street-setts', roughness=0.8); setts['tile_units'] = (0.6, 0.6)
flags = mk.material('stone', name='flagstones', roughness=0.85)
stone = mk.material('stone', name='stone-trim', roughness=0.85)
brick_red = mk.material('brick-red', name='house-brick', roughness=0.9)
brick_brown = mk.material('brick-brown', name='works-brick', roughness=0.9)
brick_yellow = mk.material('brick-yellow', name='viaduct-brick', roughness=0.9)
slate = mk.material('slate', name='house-slate', roughness=0.7)
iron = mk.material(None, name='iron', colour=(0.035, 0.038, 0.04), roughness=0.45, metallic=0.6)
roof_iron = mk.material('corrugated', name='shed-iron', roughness=0.6, metallic=0.3)
terracotta = mk.material(None, name='terracotta', colour=(0.42, 0.2, 0.12), roughness=0.8)
timber = mk.material('planks', name='timber', roughness=0.85)
gas_iron = mk.material('riveted', name='gasholder-iron', roughness=0.6, metallic=0.3)
lamp = mk.material(None, name='lamp-glow', colour=(1.0, 0.8, 0.5), glow=(1.0, 0.72, 0.4), glow_strength=3.0, roughness=0.4)
house_picture, house_glow = textures.window_glass(columns=2, rows=3, pixels=(96, 144), seed=31, broken=0.0)
house_window_lit = mk.material(name='house-window-glow', roughness=0.3, picture=house_picture, glow_picture=house_glow, glow_strength=1.0)
house_window_dark = mk.material(name='house-window', roughness=0.3, picture=house_picture)
door_paint = mk.material(None, name='door-paint', colour=(0.14, 0.2, 0.17), roughness=0.6)

parts = []
add = lambda p: parts.append(p) or p

# ----------------------------------------------------------------------------------- the ground
add(mk.box('ground', (70, 60, 0.04), at=at(0, -8, -0.04), material=cinders))
# the street between the two works, with kerbs and pavements, running across the set
STREET_Z, STREET_W = -0.25, 0.62
add(mk.box('street', (40, STREET_W, 0.02), at=at(0, STREET_Z, -0.012), material=setts))
for side in (-1, 1):
    add(mk.box(f'kerb-{side}', (40, 0.05, 0.03), at=at(0, STREET_Z + side * (STREET_W / 2 + 0.025), -0.008), material=stone, bevel=0.005))
# a second street behind works B, in front of the first terrace
BACK_STREET_Z = -7.3
add(mk.box('back-street', (40, 0.8, 0.02), at=at(0, BACK_STREET_Z, -0.012), material=setts))
add(mk.box('back-pavement', (40, 0.35, 0.03), at=at(0, BACK_STREET_Z - 0.58, -0.005), material=flags))


# ----------------------------------------------------------------------------- terraced houses
def terrace_row(name, houses=8, width=0.5, depth=0.62, height=0.72, seed=0):
    """One row of joined two-storey houses as a single part, with slate roof, chimney stacks with
    pots on the party walls, doors, sills and lit or dark windows. Built at the origin facing -y."""
    r = np.random.default_rng(seed)
    pieces = []
    length = houses * width
    body = mk.box(f'{name}-walls', (length, depth, height), at=(0, 0, height / 2), material=brick_red)
    pieces.append(body)
    # pitched roof (ridge along the row)
    roof_mesh = bpy.data.meshes.new(f'{name}-roof')
    rx, ry, rise = length / 2 + 0.02, depth / 2 + 0.05, 0.3
    roof_mesh.from_pydata([(-rx, -ry, 0), (rx, -ry, 0), (rx, 0, rise), (-rx, 0, rise), (-rx, ry, 0), (rx, ry, 0)], [],
                          [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)])
    roof = bpy.data.objects.new(f'{name}-roof', roof_mesh); bpy.context.scene.collection.objects.link(roof)
    roof.location = (0, 0, height + 0.01); roof.data.materials.append(slate)
    import bmesh
    b = bmesh.new(); b.from_mesh(roof_mesh); bmesh.ops.recalc_face_normals(b, faces=b.faces); b.to_mesh(roof_mesh); b.free()
    mk.box_map(roof, (0.5, 0.5)); pieces.append(roof)
    pieces.append(mk.box(f'{name}-ridge', (length + 0.04, 0.035, 0.03), at=(0, 0, height + 0.01 + rise), material=terracotta))
    for i in range(houses):
        x = -length / 2 + (i + 0.5) * width
        lit_down, lit_up = r.random() < 0.55, r.random() < 0.4
        door_x = x - width * 0.28
        pieces.append(mk.box(f'{name}-door-{i}', (0.09, 0.012, 0.2), at=(door_x, -depth / 2 - 0.004, 0.1), material=door_paint))
        pieces.append(mk.box(f'{name}-step-{i}', (0.13, 0.04, 0.02), at=(door_x, -depth / 2 - 0.02, 0.01), material=stone))
        for floor, z, lit in ((0, 0.2, lit_down), (1, 0.5, lit_up)):
            wx = x + width * 0.12 if floor == 0 else x
            pieces.append(mk.plane(f'{name}-window-{i}-{floor}', (0.11, 0.16), at=(wx, -depth / 2 - 0.003, z), material=house_window_lit if lit else house_window_dark, rotate=(math.pi / 2, 0, 0)))
            pieces.append(mk.box(f'{name}-sill-{i}-{floor}', (0.14, 0.03, 0.015), at=(wx, -depth / 2 - 0.012, z - 0.088), material=stone))
            pieces.append(mk.box(f'{name}-lintel-{i}-{floor}', (0.14, 0.012, 0.025), at=(wx, -depth / 2 - 0.005, z + 0.092), material=stone))
        # a chimney stack on each party wall, with pots
        if i < houses:
            sx = -length / 2 + i * width + (width if i == houses - 1 else 0)
            if i % 2 == 0 or i == houses - 1:
                pieces.append(mk.box(f'{name}-stack-{i}', (0.12, 0.09, 0.2), at=(sx if i < houses - 1 else -length / 2 + houses * width - 0.06, 0.04, height + rise * 0.7 + 0.1), material=brick_red))
                for k in (-1, 0, 1):
                    pieces.append(mk.cylinder(f'{name}-pot-{i}-{k}', 0.012, 0.05, at=((sx if i < houses - 1 else -length / 2 + houses * width - 0.06) + k * 0.035, 0.04, height + rise * 0.7 + 0.225), material=terracotta, sides=8, radius_top=0.01))
    for p in pieces: mk.apply_modifiers(p)
    # join the row into one part (fewer parts draw faster)
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces: p.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = name
    return body


rows = []
row_module = terrace_row('terrace', houses=8, seed=1)
row_module_b = terrace_row('terrace-b', houses=6, seed=2)
row_module_b.location = (0, 50, 0)   # out of the way until placed
rows = [row_module, row_module_b]
placements = [
    # (module, x, z, turn) in three.js units; rows behind works B, then along the sides
    (0, -6.0, -8.6, 0), (0, -1.4, -8.6, 0), (1, 3.0, -8.6, 0), (0, 7.2, -8.6, 0),
    (1, -7.0, -11.2, 0), (0, -2.8, -11.2, 0), (0, 1.6, -11.2, 0), (1, 5.8, -11.2, 0), (0, 9.4, -11.2, 0),
    (0, -5.0, -13.6, 0), (0, -0.6, -13.6, 0), (0, 3.8, -13.6, 0), (1, 8.2, -13.6, 0),
    (0, -7.6, -2.4, math.pi / 2), (1, -7.6, 1.8, math.pi / 2),        # left side, end-on to the camera
    (0, 7.8, -2.6, -math.pi / 2), (1, 7.8, 1.6, -math.pi / 2),
]
copies, placed = [], set()
for k, (module, x, z, turn) in enumerate(placements):
    source = rows[module]
    if module not in placed:
        obj = source; placed.add(module)                           # the first use moves the original
    else:
        obj = bpy.data.objects.new(f'terrace-{k}', source.data)     # later ones are linked copies (share the shape)
        bpy.context.scene.collection.objects.link(obj)
    obj.location = at(x, z); obj.rotation_euler = (0, 0, turn)
    copies.append(obj)

# --------------------------------------------------------------------------- far works and chimneys
smoke_tops = []
for k, (x, z, width, depth, height) in enumerate(((-9.0, -17.0, 4.0, 2.2, 1.4), (2.5, -18.5, 5.0, 2.6, 1.6), (9.5, -16.0, 3.4, 2.0, 1.3), (-3.0, -22.0, 4.6, 2.4, 1.5))):
    add(mk.box(f'far-works-{k}', (width, depth, height), at=at(x, z, height / 2), material=brick_brown))
    bays = int(width / 0.8)
    for i in range(bays):
        x0 = x - width / 2 + i * width / bays
        add(mk.prism(f'far-roof-{k}-{i}', [(0, 0), (width / bays, 0), (width / bays, 0.5)], depth, at=(x0, -z, height), material=roof_iron, axis='y'))
for k, (x, z, height) in enumerate(((-6.5, -16.5, 5.5), (-1.0, -19.5, 6.5), (4.5, -17.5, 5.0), (11.0, -15.0, 4.6), (-11.5, -20.5, 6.0), (7.5, -23.0, 7.0))):
    add(mk.cylinder(f'far-chimney-{k}', 0.24, height, at=at(x, z, height / 2), material=brick_brown, sides=16, radius_top=0.15))
    add(mk.cylinder(f'far-chimney-cap-{k}', 0.2, 0.12, at=at(x, z, height + 0.06), material=stone, sides=16))
    smoke_tops.append(mk.marker(f'smoke-{k}', at(x, z, height + 0.15)))

# a gasholder: a round iron tank inside a ring of columns tied by lattice girders
GX, GZ = -4.8, -15.2
add(mk.cylinder('gasholder-tank', 1.5, 1.6, at=at(GX, GZ, 0.8), material=gas_iron, sides=40))
add(mk.cylinder('gasholder-crown', 1.52, 0.12, at=at(GX, GZ, 1.66), material=gas_iron, sides=40, radius_top=1.3))
for i in range(12):
    a = i / 12 * 2 * math.pi
    cx, cz = GX + 1.7 * math.cos(a), GZ + 1.7 * math.sin(a)
    add(mk.cylinder(f'gasholder-column-{i}', 0.04, 2.6, at=at(cx, cz, 1.3), material=iron, sides=8))
for level in (0.9, 1.75, 2.55):
    add(mk.cylinder(f'gasholder-girder-{level}', 1.72, 0.05, at=at(GX, GZ, level), material=iron, sides=48, cap=False))

# a railway viaduct across the back
VZ, VH, SPAN = -20.0, 1.7, 0.9
deck = add(mk.box('viaduct-deck', (40, 0.5, 0.18), at=at(0, VZ, VH + 0.09), material=brick_yellow))
for i in range(int(40 / SPAN) + 1):
    x = -20 + i * SPAN
    add(mk.box(f'viaduct-pier-{i}', (0.18, 0.5, VH), at=at(x, VZ, VH / 2), material=brick_yellow))
add(mk.box('viaduct-parapet', (40, 0.06, 0.12), at=at(0, VZ + 0.22, VH + 0.24), material=stone))

# ------------------------------------------------------------------------------- gas lamps
lamps = []
for k, (x, z) in enumerate(((-3.6, STREET_Z + 0.42), (0.4, STREET_Z + 0.42), (4.2, STREET_Z + 0.42), (-2.2, BACK_STREET_Z - 0.55), (2.8, BACK_STREET_Z - 0.55), (-4.6, 6.4))):
    add(mk.cylinder(f'lamp-post-{k}', 0.018, 0.9, at=at(x, z, 0.45), material=iron, sides=8))
    add(mk.cylinder(f'lamp-base-{k}', 0.035, 0.08, at=at(x, z, 0.04), material=iron, sides=8))
    add(mk.box(f'lamp-head-{k}', (0.06, 0.06, 0.08), at=at(x, z, 0.94), material=lamp))
    add(mk.cylinder(f'lamp-cap-{k}', 0.055, 0.04, at=at(x, z, 1.0), material=iron, sides=4, radius_top=0.01, rotate=(0, 0, math.pi / 4)))
    lamps.append(mk.marker(f'lamp-{k}', at(x, z, 0.94)))

# -------------------------------------------------- things near the camera, for the bottom of the frame
# a low brick wall with stone copings and iron railings along the front of the set (left part)
WALL_Z = 6.3
add(mk.box('front-wall', (3.2, 0.14, 0.22), at=at(-3.4, WALL_Z, 0.11), material=brick_red, bevel=0.004))
add(mk.box('front-wall-coping', (3.25, 0.18, 0.035), at=at(-3.4, WALL_Z, 0.235), material=stone, bevel=0.006))
for i in range(32):
    add(mk.cylinder(f'railing-{i}', 0.006, 0.2, at=at(-4.95 + i * 0.1, WALL_Z, 0.35), material=iron, sides=6))
add(mk.box('railing-top', (3.2, 0.015, 0.015), at=at(-3.4, WALL_Z, 0.44), material=iron))
for k, (x, z, size) in enumerate(((2.6, 6.6, 0.26), (2.86, 6.75, 0.22), (2.72, 6.62, 0.2))):
    add(mk.box(f'near-crate-{k}', (size, size, size), at=at(x, z, size / 2 + (0.26 if k == 2 else 0)), material=timber, bevel=0.008))

# no baked shading here: the town is mostly far off in haze, and its linked copies share materials
mk.finish(OUT, bake=False)
