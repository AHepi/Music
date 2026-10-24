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


# ------------------------------------------------- finishing helpers (Blender MCP notes B1, B2, B6, B15)
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402


def soften(obj, width, segments=1, angle=30):
    """Soft edges that catch the light: a bevel with hardened normals (flat faces stay flat, only the
    bevel shades round), smooth shading, then weighted normals. Replaces any plain 'bevel'."""
    for m in [m for m in obj.modifiers if m.type == 'BEVEL']: obj.modifiers.remove(m)
    b = obj.modifiers.new('bevel', 'BEVEL')
    b.width = width; b.segments = segments
    b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle)
    b.use_clamp_overlap = True; b.miter_outer = 'MITER_ARC'
    b.harden_normals = True; b.face_strength_mode = 'FSTR_AFFECTED'
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    w = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')
    w.mode = 'FACE_AREA'; w.keep_sharp = True; w.use_face_influence = True
    return obj


def _cube(bm, size, at, rotate=(0, 0, 0)):
    made = bmesh.ops.create_cube(bm, size=1.0)
    matrix = Matrix.Translation(Vector(at)) @ Euler(rotate).to_matrix().to_4x4() @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
    bmesh.ops.transform(bm, matrix=matrix, verts=made['verts'])


def _block(bm, outline, y0, y1):
    """A block whose face is a 4-point outline (x, z), from y0 to y1."""
    front = [bm.verts.new((x, y0, z)) for x, z in outline]
    back = [bm.verts.new((x, y1, z)) for x, z in outline]
    bm.faces.new(front); bm.faces.new(back[::-1])
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((front[i], front[j], back[j], back[i]))


def _ring(bm, half, spring, rise, inner, thick, count, y0, y1, gap=0.0, alternate=0.0, alternate_proud=0.0, key=0.0, key_proud=0.0):
    """Wedge blocks round a segmental arch (voussoirs), radiating from the arch's centre.
    inner: added to the opening's radius for the ring's inside edge. Odd blocks stand out by
    alternate (longer) and alternate_proud; the middle block (keystone) by key and key_proud."""
    radius = (half ** 2 + rise ** 2) / (2 * rise)
    centre = spring + rise - radius
    start = math.asin(half / radius)
    r0 = radius + inner
    pad = gap / max(r0, 0.01) / 2
    for i in range(count):
        a0 = -start + 2 * start * i / count + pad
        a1 = -start + 2 * start * (i + 1) / count - pad
        keystone = count % 2 == 1 and i == count // 2
        t = thick + (alternate if i % 2 else 0) + (key if keystone else 0)
        proud = (alternate_proud if i % 2 == 0 else 0) + (key_proud if keystone else 0)
        r1 = r0 + t
        outline = [(r0 * math.sin(a0), centre + r0 * math.cos(a0)), (r0 * math.sin(a1), centre + r0 * math.cos(a1)),
                   (r1 * math.sin(a1), centre + r1 * math.cos(a1)), (r1 * math.sin(a0), centre + r1 * math.cos(a0))]
        _block(bm, outline, y0 - proud, y1)


def built(name, bm, material, place=Matrix(), bevel=0.0, segments=1, map_units=None):
    """Turn a bmesh drawn in a local frame into a part: the placement is baked into the vertices
    (the part sits at the origin), so box_map projects the texture without smearing."""
    bmesh.ops.transform(bm, matrix=place, verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    if map_units is not False: mk.box_map(obj, map_units)
    if bevel: soften(obj, bevel, segments)
    return obj


def boxes(name, specs, material, place=Matrix(), bevel=0.0, segments=1):
    """Many boxes as one part: specs = [(size, at) or (size, at, rotate)]."""
    bm = bmesh.new()
    for spec in specs: _cube(bm, *spec)
    return built(name, bm, material, place, bevel, segments)


def wall_frame(x, face, side=0):
    """Placement for parts drawn on a wall in a local frame (x along the wall, z up, the wall face
    at y = 0, outside towards -y): the front wall (side 0) or a side wall (side -1 / +1)."""
    if side == 0: return Matrix.Translation((x, face, 0))
    return Matrix.Translation((face, x, 0)) @ Matrix.Rotation(side * math.pi / 2, 4, 'Z')


def voussoirs(name, place, half, spring, rise, count, thick=0.035, proud=0.012, gap=0.0018):
    """Stone voussoirs round an arched opening with a keystone, alternate stones a little longer and
    prouder, with real joints (the wall shows between them)."""
    bm = bmesh.new()
    _ring(bm, half, spring, rise, 0.0, thick, count, -proud, 0.01, gap=gap, alternate=thick * 0.3,
          alternate_proud=0.006, key=thick * 0.45, key_proud=0.008)
    return built(name, bm, stone, place, bevel=0.003, segments=1)


def window_grid(name, place, half, sill, spring, rise, columns, rows, depth, bar=0.008, frame=0.016):
    """Cast-iron glazing bars and an outer frame standing just in front of the glass (which sits at
    local y = depth), lined up with the panes painted on the glass picture."""
    radius = (half ** 2 + rise ** 2) / (2 * rise)
    centre = spring + rise - radius
    top_at = lambda x: centre + math.sqrt(max(radius ** 2 - x ** 2, 0.0))
    height = spring + rise - sill
    y_bar, y_frame = depth - 0.01, depth - 0.008
    bm = bmesh.new()
    for c in range(1, columns):
        x = -half + 2 * half * c / columns
        top = top_at(x) - 0.004
        _cube(bm, (bar, 0.01, top - sill), (x, y_bar, (sill + top) / 2))
    for r in range(1, rows):
        z = sill + height * r / rows
        span = 2 * half if z <= spring else 2 * math.sqrt(max(radius ** 2 - (z - centre) ** 2, 0.0)) - 0.01
        if span > 0.03: _cube(bm, (span, 0.01, bar), (0, y_bar, z))
    for s in (-1, 1):
        _cube(bm, (frame, 0.016, spring - sill), (s * (half - frame / 2), y_frame, (sill + spring) / 2))
    _cube(bm, (2 * half, 0.016, frame), (0, y_frame, sill + frame / 2))
    _ring(bm, half, spring, rise, -frame, frame, 6, y_frame - 0.008, y_frame + 0.008)
    return built(name, bm, iron, place)


def tube(name, points, radius, material, resolution=8):
    """A smooth iron rod along points (a NURBS curve with a round section), made into a mesh."""
    curve = bpy.data.curves.new(name, 'CURVE'); curve.dimensions = '3D'
    curve.bevel_depth = radius; curve.bevel_resolution = 1; curve.resolution_u = resolution; curve.use_fill_caps = True
    spline = curve.splines.new('NURBS'); spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points): p.co = (*co, 1.0)
    spline.order_u = 3; spline.use_endpoint_u = True
    temp = bpy.data.objects.new(name + '-curve', curve); bpy.context.scene.collection.objects.link(temp)
    graph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(temp.evaluated_get(graph))
    bpy.data.objects.remove(temp, do_unlink=True)
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    mesh.materials.clear(); mesh.materials.append(material)
    mesh.polygons.foreach_set('use_smooth', [True] * len(mesh.polygons))
    return obj


def join_by_material(keep_apart=()):
    """Fewer parts, cheaper drawing (notes B15): apply every part's modifiers, then join the parts that
    share a material into one mesh named after it. Parts whose names start with one of keep_apart
    (left out of the shading bake) are joined among themselves under that prefix."""
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes: mk.apply_modifiers(o)
    groups = {}
    for o in meshes:
        materials = [m for m in o.data.materials if m]
        if len(materials) != 1: continue
        prefix = next((p for p in keep_apart if o.name.startswith(p)), '')
        groups.setdefault((materials[0].name, prefix), []).append(o)
    for (material_name, prefix), objects in groups.items():
        target = objects[0]
        if len(objects) > 1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in objects: o.select_set(True)
            bpy.context.view_layer.objects.active = target
            bpy.ops.object.join()
        target.name = f'{prefix}-{material_name}' if prefix else f'{material_name}-parts'
        target.data.name = target.name


parts = []
add = lambda p: parts.append(p) or p

# ------------------------------------------------------------------------------------ the shed
walls = add(mk.box('walls', (W, D, H), at=(0, 0, H / 2), material=brick))
cutters = []
FRONT_WINDOWS = [-1.38, -1.02, -0.55, 0.55, 1.02, 1.38]
SIDE_WINDOWS = [-0.55, 0.0, 0.55]
SILL, SPRING, RISE, HALF = 0.36, 0.84, 0.05, 0.11
REVEAL, GLASS = 0.08, 0.07       # how deep the window openings go, and how far back the glass sits
for x in FRONT_WINDOWS:
    c = mk.prism('cut', arch_outline(HALF, SILL, SPRING, RISE), REVEAL * 2, at=(x, FRONT, 0), axis='y', map_units=False)
    cutters.append(c)
for side in (-1, 1):
    for y in SIDE_WINDOWS:
        if side == OFFICE_SIDE and y < 0.3: continue      # the office stands against this side's front half
        c = mk.prism('cut', arch_outline(HALF, SILL, SPRING, RISE), REVEAL * 2, at=(0, 0, 0), axis='y', map_units=False)
        c.rotation_euler = (0, 0, math.pi / 2); c.location = (side * W / 2, y, 0)
        cutters.append(c)
# the loading door: a wide arched opening, deep enough to see into
DOOR_HALF, DOOR_TOP = 0.27, 0.74
DOOR_DEEP = 0.44                  # how far back the works inside can be seen
cutters.append(mk.prism('cut', arch_outline(DOOR_HALF, -0.05, DOOR_TOP, 0.07), DOOR_DEEP * 2 + 0.02, at=(0, FRONT, 0), axis='y', map_units=False))
mk.cut(walls, cutters)
mk.box_map(walls)
soften(walls, 0.011, segments=2)   # after the cut (a bevel before the boolean breaks the openings)

# glass in each window, set back in the opening
def sill_stone(bm, half):
    """A stone sill in the local wall frame: a block running into the wall, a projecting top that
    catches the lamp light, and a nose hanging below its front edge (the drip)."""
    _cube(bm, (half * 2 + 0.06, 0.07, 0.022), (0, -0.015, SILL - 0.017))                          # body, into the wall
    _block(bm, [(-half - 0.03, SILL - 0.006), (half + 0.03, SILL - 0.006), (half + 0.03, SILL), (-half - 0.03, SILL)], -0.05, 0.0)  # weathered top
    _cube(bm, (half * 2 + 0.06, 0.012, 0.008), (0, -0.044, SILL - 0.031))                         # the nose below the drip


for i, x in enumerate(FRONT_WINDOWS):
    place = wall_frame(x, FRONT)
    add(mk.plane(f'window-{i}', (HALF * 2, SPRING + RISE - SILL), at=(x, FRONT + GLASS, (SILL + SPRING + RISE) / 2), material=window, rotate=(math.pi / 2, 0, 0)))
    add(voussoirs(f'arch-{i}', place, HALF, SPRING, RISE, 11))
    add(window_grid(f'window-bars-{i}', place, HALF, SILL, SPRING, RISE, 4, 7, GLASS))
    bm = bmesh.new(); sill_stone(bm, HALF); add(built(f'sill-{i}', bm, stone, place, bevel=0.004))
for side in (-1, 1):
    for j, y in enumerate(SIDE_WINDOWS):
        if side == OFFICE_SIDE and y < 0.3: continue
        place = wall_frame(y, side * W / 2, side)
        add(mk.plane(f'window-side-{side}-{j}', (HALF * 2, SPRING + RISE - SILL), at=(side * (W / 2 - GLASS), y, (SILL + SPRING + RISE) / 2), material=window, rotate=(math.pi / 2, 0, side * math.pi / 2)))
        add(voussoirs(f'arch-side-{side}-{j}', place, HALF, SPRING, RISE, 11))
        add(window_grid(f'window-bars-side-{side}-{j}', place, HALF, SILL, SPRING, RISE, 4, 7, GLASS))
        bm = bmesh.new(); sill_stone(bm, HALF); add(built(f'sill-side-{side}-{j}', bm, stone, place, bevel=0.004))

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
    # copings: on the front gables (seen against the bright sky) separate stones with real joints,
    # a kneeler at the foot and a block at the apex; the back ones stay one slab
    centre = Vector((x0 + BAY / 2, 0, H + 0.03 + TOOTH / 2))
    run = Vector((math.cos(angle), 0, math.sin(angle)))
    length, count = slope + 0.02, 8
    pitch = length / count
    stones = []
    for k in range(count):
        at = centre + run * (-length / 2 + pitch * (k + 0.5))
        stones.append(((pitch - 0.003, 0.09 + (0.006 if k % 2 else 0), 0.03), (at.x, FRONT - 0.015, at.z), (0, -angle, 0)))
    stones.append(((0.1, 0.1, 0.075), (x0 + 0.05, FRONT - 0.015, H + 0.015 + 0.0375)))              # kneeler
    stones.append(((0.07, 0.1, 0.05), (x0 + BAY - 0.035, FRONT - 0.015, H + 0.02 + TOOTH + 0.012)))   # apex block
    add(boxes(f'coping-{i}-front', stones, stone, bevel=0.005))
    add(mk.box(f'coping-{i}-back', (slope + 0.02, 0.09, 0.03), at=(x0 + BAY / 2, BACK + 0.015, H + 0.03 + TOOTH / 2), material=stone, rotate=(0, -angle, 0), bevel=0.006))
    # the glazed north light on the tooth's upright face, with iron glazing bars and a frame
    xg = x0 + BAY
    add(mk.plane(f'north-light-{i}', (TOOTH - 0.05, D - 0.14), at=(xg + 0.004, 0, H + 0.02 + TOOTH / 2), material=roof_glass, rotate=(0, math.pi / 2, 0)))
    bars = [((0.012, 0.014, TOOTH - 0.04), (xg + 0.012, -D / 2 + 0.07 + k * (D - 0.14) / 8, H + 0.02 + TOOTH / 2)) for k in range(9)]
    for z in (H + 0.02 + 0.03, H + 0.02 + TOOTH / 2, H + 0.02 + TOOTH - 0.03):
        bars.append(((0.016, D - 0.12, 0.014), (xg + 0.014, 0, z)))
    add(boxes(f'glazing-bar-{i}', bars, iron, bevel=0.002))
    add(mk.box(f'ridge-{i}', (0.05, D + 0.1, 0.022), at=(xg - 0.012, 0, H + 0.02 + TOOTH + 0.006), material=iron, bevel=0.004))
    add(mk.cylinder(f'ridge-roll-{i}', 0.012, D + 0.1, at=(xg - 0.012, 0, H + 0.02 + TOOTH + 0.02), material=iron, sides=10, rotate=(math.pi / 2, 0, 0)))
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
add(voussoirs('door-arch', wall_frame(0, FRONT), DOOR_HALF, DOOR_TOP, 0.07, 15, thick=0.05, proud=0.014))
add(mk.plane('door-inside', (DOOR_HALF * 2 + 0.04, DOOR_TOP + 0.1), at=(0, FRONT + DOOR_DEEP, (DOOR_TOP + 0.1) / 2 - 0.02), material=door_glow, rotate=(math.pi / 2, 0, 0)))
# the works inside: a dark floor, then machines, a line shaft and its belts in silhouette against the
# lit back (they move against it as the camera moves, which the flat picture alone cannot do)
add(boxes('works-floor', [((DOOR_HALF * 2, DOOR_DEEP - 0.03, 0.006), (0, FRONT + 0.03 + (DOOR_DEEP - 0.03) / 2, 0.103))], iron))
machines = [((0.12, 0.08, 0.17), (-0.15, FRONT + 0.33, 0.1 + 0.085)), ((0.05, 0.05, 0.05), (-0.15, FRONT + 0.33, 0.295)),   # a drill
            ((0.17, 0.07, 0.09), (0.12, FRONT + 0.28, 0.1 + 0.045)), ((0.035, 0.05, 0.06), (0.05, FRONT + 0.28, 0.22)),     # a lathe bed and head
            ((0.56, 0.02, 0.02), (0, FRONT + 0.36, 0.64)),                                                                 # the shaft hanger beam
            ((0.006, 0.004, 0.42), (-0.15, FRONT + 0.34, 0.5), (0, 0.12, 0)), ((0.006, 0.004, 0.4), (0.06, FRONT + 0.3, 0.44), (0, -0.1, 0))]   # belts
add(boxes('works-machines', machines, iron, bevel=0.004))
add(mk.cylinder('works-shaft', 0.008, DOOR_HALF * 2, at=(0, FRONT + 0.35, 0.62), material=iron, sides=8, rotate=(0, math.pi / 2, 0)))
add(mk.cylinder('works-flywheel', 0.055, 0.018, at=(0.19, FRONT + 0.31, 0.23), material=iron, sides=16, rotate=(math.pi / 2, 0, 0)))
for side in (-1, 1):   # the two leaves, swung open outwards
    # hinged at the opening's edge, closed it would reach the middle; swung 110 degrees outwards.
    # Drawn closed (hinge at x = 0, the leaf reaching towards the middle, its outside face at -y),
    # then turned and moved into place.
    place = Matrix.Translation((side * DOOR_HALF, FRONT - 0.02, 0)) @ Matrix.Rotation(side * math.radians(110), 4, 'Z')
    tall, gap = DOOR_TOP - 0.02, 0.0018
    plank = (DOOR_HALF - 6 * gap) / 7
    leaf = [((plank, 0.02, tall), (-side * (k * (plank + gap) + plank / 2), 0, tall / 2)) for k in range(7)]
    for z in (0.1, 0.36, 0.62):    # ledges on the inside face
        leaf.append(((DOOR_HALF * 0.9, 0.014, 0.05), (-side * DOOR_HALF / 2, 0.016, z)))
    rise_, run = 0.26 - 0.05, DOOR_HALF * 0.7
    for z0 in (0.1, 0.36):         # the braces between them, rising away from the hinge
        leaf.append(((math.hypot(rise_, run), 0.012, 0.04), (-side * DOOR_HALF / 2, 0.015, z0 + 0.13), (0, side * math.atan2(rise_, run), 0)))
    add(boxes(f'door-leaf-{side}', leaf, planks, place, bevel=0.003))
    straps = []
    for z in (0.12, 0.6):          # strap hinges on the outside, with a pointed end
        straps.append(((DOOR_HALF * 0.8, 0.005, 0.022), (-side * DOOR_HALF * 0.4, -0.0125, z)))
        straps.append(((0.024, 0.005, 0.024), (-side * DOOR_HALF * 0.8, -0.0125, z), (0, math.pi / 4, 0)))
        straps.append(((0.016, 0.03, 0.03), (side * 0.006, -0.004, z)))   # the hinge knuckle on the wall
    add(boxes(f'door-strap-{side}', straps, iron, place, bevel=0.002))
add(mk.box('sign', (0.9, 0.02, 0.12), at=(0, FRONT - 0.03, DOOR_TOP + 0.22), material=sign, bevel=0.004, map_units=False))
sign_part = parts[-1]
# map the sign picture once over its front
bm = bmesh.new(); bm.from_mesh(sign_part.data)
uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
for f in bm.faces:
    for loop in f.loops: loop[uv].uv = (loop.vert.co.x / 0.9 + 0.5, loop.vert.co.z / 0.12 + 0.5)
bm.to_mesh(sign_part.data); bm.free()
SZ = DOOR_TOP + 0.22   # a moulded frame round the board
add(boxes('sign-frame', [((0.95, 0.03, 0.022), (0, FRONT - 0.035, SZ + 0.07)), ((0.95, 0.03, 0.022), (0, FRONT - 0.035, SZ - 0.07)),
                         ((0.025, 0.03, 0.118), (-0.4625, FRONT - 0.035, SZ)), ((0.025, 0.03, 0.118), (0.4625, FRONT - 0.035, SZ))], stone, bevel=0.005))
# the lantern: glass on four sides in an iron frame, a pyramid hood with a finial, on a curled bracket
LZ = DOOR_TOP + 0.37
add(mk.box('lamp', (0.034, 0.034, 0.05), at=(0, FRONT - 0.1, LZ), material=lamp))
frame = [((0.006, 0.006, 0.058), (sx * 0.019, FRONT - 0.1 + sy * 0.019, LZ)) for sx in (-1, 1) for sy in (-1, 1)]
frame += [((0.05, 0.05, 0.008), (0, FRONT - 0.1, LZ - 0.031)), ((0.052, 0.052, 0.006), (0, FRONT - 0.1, LZ + 0.03))]
add(boxes('lantern-frame', frame, iron, bevel=0.0015))
add(mk.cylinder('lamp-hood', 0.042, 0.028, at=(0, FRONT - 0.1, LZ + 0.047), material=iron, sides=4, radius_top=0.006, rotate=(0, 0, math.pi / 4)))
add(mk.cylinder('lamp-finial', 0.007, 0.022, at=(0, FRONT - 0.1, LZ + 0.07), material=iron, sides=8, radius_top=0.002))
add(mk.cylinder('lamp-drop', 0.012, 0.016, at=(0, FRONT - 0.1, LZ - 0.043), material=iron, sides=8, radius_top=0.004, rotate=(math.pi, 0, 0)))
add(tube('lamp-bracket', [(0, FRONT + 0.005, LZ + 0.12), (0, FRONT - 0.06, LZ + 0.13), (0, FRONT - 0.1, LZ + 0.12), (0, FRONT - 0.1, LZ + 0.082)], 0.0045, iron))
add(tube('lamp-bracket-scroll', [(0, FRONT + 0.005, LZ - 0.02), (0, FRONT - 0.03, LZ + 0.03), (0, FRONT - 0.045, LZ + 0.1), (0, FRONT - 0.07, LZ + 0.126)], 0.0035, iron))
add(boxes('lamp-plate', [((0.03, 0.008, 0.17), (0, FRONT - 0.002, LZ + 0.05))], iron, bevel=0.002))
mk.marker('door_lamp', (0, FRONT - 0.1, DOOR_TOP + 0.36))

# ------------------------------------------------------------------------------------ the chimney
CX, CY = OFFICE_SIDE * -1 * (W / 2 - 0.45), BACK + 0.32
add(mk.box('chimney-base', (0.38, 0.38, 0.3), at=(CX, CY, 0.15), material=stone, bevel=0.01))
add(frustum('chimney', 0.15, 0.1, 2.75, (CX, CY, 0.3), brick, bevel=0.004))
for z in (1.1, 2.0):
    half = 0.15 - (0.05 * (z - 0.3) / 2.75)
    add(mk.box(f'chimney-band-{z}', (half * 2 + 0.03, half * 2 + 0.03, 0.04), at=(CX, CY, z), material=stone, bevel=0.005))
top = 0.3 + 2.75
# a corbelled cap: five courses stepping out, then a stone capping; two iron straps lower down
courses = ((0.012, 0.03, brick), (0.026, 0.03, brick), (0.04, 0.03, brick), (0.052, 0.035, stone), (0.04, 0.025, brick))
z = top
for k, (grow, height, material_) in enumerate(courses):
    add(mk.box(f'chimney-cap-{k}', (0.2 + grow * 2, 0.2 + grow * 2, height), at=(CX, CY, z + height / 2), material=material_, bevel=0.005))
    z += height
for zs in (1.55, 2.5):
    half = 0.15 - (0.05 * (zs - 0.3) / 2.75)
    add(mk.box(f'chimney-strap-{zs}', (half * 2 + 0.008, half * 2 + 0.008, 0.014), at=(CX, CY, zs), material=iron, bevel=0.002))
add(mk.box('chimney-soot', (0.17, 0.17, 0.02), at=(CX, CY, z + 0.005), material=iron))
add(mk.cylinder('lightning-rod', 0.005, 3.3, at=(CX + 0.1, CY - 0.1, 1.65 + 0.15), material=iron, sides=6))
add(mk.cylinder('lightning-rod-tip', 0.009, 0.05, at=(CX + 0.1, CY - 0.1, 3.475), material=iron, sides=6, radius_top=0.0005))
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
soften(office, 0.01, segments=2)
for floor, z in ((0, 0.2), (1, 0.95)):
    for k, x in enumerate((-0.22, 0.22)):
        place = wall_frame(OX + x, OY - OD / 2)
        add(mk.plane(f'office-window-{floor}-{k}', (0.17, 0.45), at=(OX + x, OY - OD / 2 + 0.04, z + 0.225), material=office_window, rotate=(math.pi / 2, 0, 0)))
        add(mk.box(f'office-sill-{floor}-{k}', (0.23, 0.05, 0.025), at=(OX + x, OY - OD / 2 - 0.015, z - 0.012), material=stone, bevel=0.005))
        add(voussoirs(f'office-arch-{floor}-{k}', place, 0.085, z + 0.42, 0.03, 9, thick=0.028))
        add(window_grid(f'office-bars-{floor}-{k}', place, 0.085, z, z + 0.42, 0.03, 2, 4, 0.04, bar=0.007, frame=0.012))
    for k, y in enumerate((-0.2, 0.25)):
        place = wall_frame(OY + y, OX + OFFICE_SIDE * OW / 2, OFFICE_SIDE)
        add(mk.plane(f'office-side-window-{floor}-{k}', (0.17, 0.45), at=(OX + OFFICE_SIDE * (OW / 2 - 0.04), OY + y, z + 0.225), material=office_window, rotate=(math.pi / 2, 0, OFFICE_SIDE * math.pi / 2)))
        add(mk.box(f'office-side-sill-{floor}-{k}', (0.05, 0.23, 0.025), at=(OX + OFFICE_SIDE * (OW / 2 + 0.015), OY + y, z - 0.012), material=stone, bevel=0.005))
        add(window_grid(f'office-side-bars-{floor}-{k}', place, 0.085, z, z + 0.42, 0.03, 2, 4, 0.04, bar=0.007, frame=0.012))
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

# finishing pass (notes B1/B2): every part still carrying the kit's plain faceted bevel gets the soft,
# hardened one instead (two segments on the larger trims, one on small parts); the brick gables too
for part in [o for o in bpy.context.scene.objects if o.type == 'MESH']:
    plain = [m for m in part.modifiers if m.type == 'BEVEL' and not m.harden_normals]
    if plain:
        width = plain[0].width
        soften(part, max(width, 0.005), segments=2 if width >= 0.008 else 1)
    elif part.name.startswith(('gable-', 'pilaster-', 'chimney-band', 'dentils')) and not part.modifiers.get('weighted'):
        soften(part, 0.006 if part.name.startswith('gable-') else 0.004)
print('triangles before joining:', mk.count_triangles())
BAKE_SKIP = ('forecourt', 'kerb', 'rail')
join_by_material(keep_apart=BAKE_SKIP)
mk.finish(OUT, bake='--no-bake' not in arguments, bake_skip=BAKE_SKIP)
