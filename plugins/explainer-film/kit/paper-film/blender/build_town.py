# What this does: builds the industrial town around the "two factories" (chapter 2, pages 3 and 8)
# in Blender and writes it as one .glb: the ground of the model set (cinder yards with darker damp
# patches and worn ground, a cobbled street running between the two works with jointed kerb stones,
# gas lamps with four-pane lanterns), rows of terraced houses (window and door openings cut into the
# brick, glass set back behind a meeting rail, stone sills and lintels, fanlights, gable parapets with
# kneelers, gutters and downpipes, chimney stacks with oversailing courses and rimmed pots), other
# works with sawtooth north-light roofs and tall round chimneys (corbelled caps, iron bands, soot
# towards the top), a gasholder with lattice bracing, a church spire and a water tower, an arched
# railway viaduct with a goods train on it, and a few things near the camera (a low brick wall with
# piers, saddleback coping stones and spear-headed railings, battened crates) to fill the bottom of
# a tall frame.
#
# Positions are in the three.js set's own units (factory A at x -1.4, z +2.2; factory B at x +1.6,
# z -4.2; the camera looks towards -z). Blender's y is three.js's -z, so this script converts.
# Kept clear and flat: both factory forecourts (about 5.8 x 5.4 around each works) and the street at
# three.js z -0.25. The ground's top is at y -0.02.
#
# Run: /home/user/work/blender-env/bin/python build_town.py OUT.glb
# Markers: smoke-0 ... smoke-5 (tops of the far chimneys), lamp-0 ... lamp-5 (gas lamp heads).
# Glowing materials (found by name by the pages): house-window-glow (lit windows), lamp-glow.
#
# Finishing (from the Blender MCP notes, chapter-2/reference/22): parts in view get a bevel with
# hardened normals plus a Weighted Normal modifier and smooth shading, so edges catch a soft
# highlight instead of showing facets; turned parts are lathed; the ground and the far chimneys carry
# colour attributes (COLOR_0) for large-scale grime; still parts sharing a material are joined so
# the stage draws far fewer meshes.

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402
import textures  # noqa: E402
import numpy as np  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'town.glb'
rng = np.random.default_rng(7)
mk.reset()


def at(x, z, y=0.0):
    """three.js (x, y up, z towards camera) -> Blender (x, y back, z up)."""
    return (x, -z, y)


# ------------------------------------------------------------------------------ local helpers
def smooth_finish(obj, width=0.008, segments=1, angle=30, bevel=True):
    """Soft edges that catch the light: bevel with hardened normals (flat faces stay flat, only the
    bevel shades round), then weighted normals and smooth shading (notes B1, B2)."""
    if bevel:
        b = obj.modifiers.new('bevel', 'BEVEL'); b.width = width; b.segments = segments
        b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle); b.use_clamp_overlap = True
        b.miter_outer = 'MITER_ARC'; b.harden_normals = True; b.face_strength_mode = 'FSTR_AFFECTED'
    wn = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL'); wn.mode = 'FACE_AREA'; wn.keep_sharp = True
    wn.use_face_influence = bevel
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    return obj


def bx(name, size, at=(0, 0, 0), material=None, bevel=0.0, segments=1, rotate=(0, 0, 0), map_units=None):
    """mk.box, but with a smooth hardened bevel instead of the kit's faceted one."""
    obj = mk.box(name, size, at=at, material=material, rotate=rotate, map_units=map_units)
    return smooth_finish(obj, bevel, segments) if bevel else obj


def slab(name, outline, a0, a1, material, axis='x', map_units=None):
    """An outline [(u, v), ...] pushed from a0 to a1 along an axis. axis 'x': outline in (y, z);
    axis 'y': outline in (x, z). Built in place (no rotation), so box_map keeps bricks true."""
    mesh = bpy.data.meshes.new(name); bm = bmesh.new()
    P = (lambda u, v, a: (a, u, v)) if axis == 'x' else (lambda u, v, a: (u, a, v))
    v0 = [bm.verts.new(P(u, v, a0)) for u, v in outline]
    v1 = [bm.verts.new(P(u, v, a1)) for u, v in outline]
    bm.faces.new(v0); bm.faces.new(v1)
    n = len(outline)
    for i in range(n): bm.faces.new((v0[i], v0[(i + 1) % n], v1[(i + 1) % n], v1[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material); mk.box_map(obj, map_units)
    return obj


def lathe(name, profile, at=(0, 0, 0), material=None, sides=12, sharp=40, map_units=None):
    """A turned part (notes B7): profile [(radius, height), ...] from bottom to top, spun round z.
    A radius of 0 closes the end. Smooth sides, sharp steps."""
    mesh = bpy.data.meshes.new(name); bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r <= 1e-6: rings.append([bm.verts.new((0, 0, z))])
        else: rings.append([bm.verts.new((r * math.cos(2 * math.pi * i / sides), r * math.sin(2 * math.pi * i / sides), z)) for i in range(sides)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1: continue
        for i in range(sides):
            j = (i + 1) % sides
            if len(a) == 1: bm.faces.new((a[0], b[j], b[i]))
            elif len(b) == 1: bm.faces.new((a[i], a[j], b[0]))
            else: bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    if material is not None: obj.data.materials.append(material)
    obj.data.set_sharp_from_angle(angle=math.radians(sharp))
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    if material is not None: mk.box_map(obj, map_units)
    return obj


def colour_by(obj, fn):
    """Colour attribute (COLOR_0 in glTF, multiplied into the base colour by three.js) from fn(world x, y, z)."""
    mesh = obj.data
    ca = mesh.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    m = obj.matrix_world
    values = []
    for loop in mesh.loops:
        p = m @ mesh.vertices[loop.vertex_index].co
        c = fn(p.x, p.y, p.z)
        values.extend((c, c, c, 1.0))
    ca.data.foreach_set('color', values)
    mesh.color_attributes.active_color = ca
    return obj


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------------------------- materials
cinders = mk.material('cinders', name='cinders', roughness=0.95)
setts = mk.material('setts', name='street-setts', roughness=0.8); setts['tile_units'] = (0.6, 0.6)
flags = mk.material('stone', name='flagstones', roughness=0.85)
stone = mk.material('stone', name='stone-trim', roughness=0.85)
brick_red = mk.material('brick-red', name='house-brick', roughness=0.9)
brick_brown = mk.material('brick-brown', name='works-brick', roughness=0.9)
chimney_brick = mk.material('brick-brown', name='chimney-brick', roughness=0.9)   # carries soot by colour attribute
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
sash_paint = mk.material(None, name='sash-paint', colour=(0.72, 0.68, 0.6), roughness=0.55)
wagon_paint = mk.material(None, name='wagon-paint', colour=(0.22, 0.12, 0.08), roughness=0.7)

parts = []
add = lambda p: parts.append(p) or p

# ----------------------------------------------------------------------------------- the ground
STREET_Z, STREET_W = -0.25, 0.62
BACK_STREET_Z = -7.3
SHEDS = ((-1.4, 2.2), (1.6, -4.2))      # the two works (3.2 wide x 2.0 deep each), for soft grime at their feet


def ground_colour(x, y, z):
    """Blender x, y (three.js z = -y). Large soft variation, never brighter than the texture itself."""
    z = -y
    n = (math.sin(0.31 * x + 1.3) * math.sin(0.27 * z + 0.4) + 0.5 * math.sin(0.9 * x + 0.7 * z + 2.0)
         + 0.35 * math.sin(1.7 * x - 1.1 * z + 5.0) + 0.25 * math.sin(2.9 * x + 2.3 * z + 1.0)) / 2.1
    c = 0.86 + 0.14 * n
    # darker, damp ground along both edges of the street (gutters)
    c *= 1 - 0.12 * math.exp(-((abs(z - STREET_Z) - STREET_W / 2 - 0.25) / 0.35) ** 2)
    # soot and wet at the feet of the two works
    for sx, sz in SHEDS:
        dx = max(0.0, abs(x - sx) - 1.6); dz = max(0.0, abs(z - sz) - 1.0)
        c *= 1 - 0.14 * math.exp(-math.hypot(dx, dz) / 0.45)
    # a few dark, damp patches in the open ground
    for px, pz, r in ((0.9, 8.6, 0.8), (-2.6, 9.9, 0.7), (3.6, 10.6, 0.9), (-5.8, 4.2, 0.9), (5.2, 3.0, 0.8), (-6.2, -5.0, 1.0)):
        c *= 1 - 0.22 * math.exp(-((x - px) ** 2 + (z - pz) ** 2) / (r * r))
    # a worn, lighter cart track from the street towards the front of the set (east of works A's forecourt)
    c = c + (1 - c) * 0.5 * math.exp(-((x - (2.35 + 0.08 * (z - 4))) / 0.35) ** 2) * smoothstep(0.4, 1.4, z) * (1 - smoothstep(11, 13, z))
    return max(0.55, min(1.0, c))


def ground_grid():
    """The 70 x 60 cinder ground as a graded grid (0.5 apart where the camera looks, coarse beyond),
    top at y -0.02, with a skirt down to -0.06 like the old slab, UVs in world units."""
    xs = sorted(set([-35.0, -26.0, -20.0, -16.0, -13.0] + [round(v, 3) for v in np.arange(-11.0, 11.001, 0.5)] + [13.0, 16.0, 20.0, 26.0, 35.0]))
    zs = sorted(set([-38.0, -32.0, -28.0, -24.0, -21.0, -19.0] + [round(v, 3) for v in np.arange(-17.5, -9.0, 1.0)] + [round(v, 3) for v in np.arange(-9.0, 13.001, 0.5)] + [14.5, 17.0, 22.0]))
    mesh = bpy.data.meshes.new('ground'); bm = bmesh.new()
    grid = [[bm.verts.new((x, -z, -0.02)) for x in xs] for z in zs]
    for j in range(len(zs) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    edges = [e for e in bm.edges if e.is_boundary]
    skirt = bmesh.ops.extrude_edge_only(bm, edges=edges)
    bmesh.ops.translate(bm, verts=[v for v in skirt['geom'] if isinstance(v, bmesh.types.BMVert)], vec=(0, 0, -0.04))
    for f in bm.faces:
        f.normal_update()
        if abs(f.normal.z) > 0.5 and f.normal.z < 0: f.normal_flip()
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new('ground', mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(cinders); mk.box_map(obj)
    colour_by(obj, ground_colour)
    return obj


add(ground_grid())
# the street between the two works, with jointed kerb stones, running across the set
add(mk.box('street', (40, STREET_W, 0.02), at=at(0, STREET_Z, -0.012), material=setts))
for side in (-1, 1):
    kz = STREET_Z + side * (STREET_W / 2 + 0.025)
    for x0, x1 in ((-20.0, -9.0), (9.0, 20.0)):
        add(mk.box(f'kerb-{side}-{x0}', (x1 - x0, 0.05, 0.03), at=at((x0 + x1) / 2, kz, -0.008), material=stone))
    for i in range(36):
        x = -9.0 + (i + 0.5) * 0.5
        add(bx(f'kerb-{side}-stone-{i}', (0.488, 0.05, 0.03), at=at(x, kz, -0.008), material=stone, bevel=0.005 if abs(x) < 6.5 else 0.0))
# a second street behind works B, in front of the first terrace, with kerbs and a pavement
add(mk.box('back-street', (40, 0.8, 0.02), at=at(0, BACK_STREET_Z, -0.012), material=setts))
add(mk.box('back-pavement', (40, 0.35, 0.03), at=at(0, BACK_STREET_Z - 0.58, -0.005), material=flags))
add(mk.box('back-kerb-near', (40, 0.05, 0.03), at=at(0, BACK_STREET_Z + 0.375, -0.008), material=stone))
add(mk.box('back-kerb-far', (40, 0.05, 0.034), at=at(0, BACK_STREET_Z - 0.4, -0.004), material=stone))


# ----------------------------------------------------------------------------- terraced houses
def terrace_row(name, houses=8, width=0.5, depth=0.62, height=0.72, seed=0):
    """One row of joined two-storey houses as a single part, built at the origin facing -y: window
    and door openings cut into the brick, glass set back behind a meeting rail, stone sills and lintels,
    recessed doors with fanlights, gable parapets with kneelers, gutter and downpipes, a slate roof,
    and chimney stacks with oversailing courses and rimmed pots."""
    r = np.random.default_rng(seed)
    pieces = []
    length = houses * width
    front = -depth / 2
    body = mk.box(f'{name}-walls', (length, depth, height), at=(0, 0, height / 2), material=brick_red)
    cutters, layout = [], []
    for i in range(houses):
        x = -length / 2 + (i + 0.5) * width
        lit_down, lit_up = r.random() < 0.55, r.random() < 0.4
        door_x = x - width * 0.28
        layout.append((x, door_x, lit_down, lit_up))
        cutters.append(mk.box(f'{name}-cut-door-{i}', (0.09, 0.1, 0.27), at=(door_x, front, 0.12)))
        for floor, z in ((0, 0.2), (1, 0.5)):
            wx = x + width * 0.12 if floor == 0 else x
            cutters.append(mk.box(f'{name}-cut-win-{i}-{floor}', (0.11, 0.06, 0.16), at=(wx, front, z)))
    mk.cut(body, cutters)
    smooth_finish(body, bevel=False)       # far off: a bevel would be under a pixel, so clean normals only
    pieces.append(body)
    # pitched roof (ridge along the row)
    roof_mesh = bpy.data.meshes.new(f'{name}-roof')
    rx, ry, rise = length / 2 + 0.02, depth / 2 + 0.05, 0.3
    roof_mesh.from_pydata([(-rx, -ry, 0), (rx, -ry, 0), (rx, 0, rise), (-rx, 0, rise), (-rx, ry, 0), (rx, ry, 0)], [],
                          [(0, 1, 2, 3), (3, 2, 5, 4), (0, 3, 4), (1, 5, 2)])
    roof = bpy.data.objects.new(f'{name}-roof', roof_mesh); bpy.context.scene.collection.objects.link(roof)
    roof.location = (0, 0, height + 0.01); roof.data.materials.append(slate)
    b = bmesh.new(); b.from_mesh(roof_mesh); bmesh.ops.recalc_face_normals(b, faces=b.faces); b.to_mesh(roof_mesh); b.free()
    mk.box_map(roof, (0.5, 0.5)); pieces.append(roof)
    pieces.append(mk.cylinder(f'{name}-ridge', 0.02, length + 0.04, at=(0, 0, height + 0.01 + rise), material=terracotta, sides=6, rotate=(0, math.pi / 2, 0)))
    # gutter along the eaves and a downpipe on every other party wall
    pieces.append(mk.cylinder(f'{name}-gutter', 0.016, length + 0.03, at=(0, -ry + 0.012, height), material=iron, sides=8, rotate=(0, math.pi / 2, 0)))
    for i in range(0, houses + 1, 2):
        px = -length / 2 + i * width + (0.03 if i == 0 else -0.03 if i == houses else 0)
        pieces.append(mk.box(f'{name}-downpipe-{i}', (0.016, 0.016, height), at=(px, front - 0.012, height / 2), material=iron))
    # gable parapets with stone copings and kneelers at both ends of the row
    roof_z = lambda y: height + 0.01 + rise * (1 - abs(y) / ry)
    for end in (-1, 1):
        xa, xb = sorted((end * (length / 2 - 0.05), end * (length / 2 + 0.025)))
        outline = [(-depth / 2, height - 0.01), (depth / 2, height - 0.01), (depth / 2, roof_z(depth / 2) + 0.04),
                   (0, roof_z(0) + 0.04), (-depth / 2, roof_z(-depth / 2) + 0.04)]
        pieces.append(slab(f'{name}-gable-{end}', outline, xa, xb, brick_red))
        cap = [(-depth / 2 - 0.012, roof_z(-depth / 2) + 0.04), (0, roof_z(0) + 0.04), (depth / 2 + 0.012, roof_z(depth / 2) + 0.04),
               (depth / 2 + 0.012, roof_z(depth / 2) + 0.062), (0, roof_z(0) + 0.064), (-depth / 2 - 0.012, roof_z(-depth / 2) + 0.062)]
        pieces.append(slab(f'{name}-gable-coping-{end}', cap, xa - 0.008, xb + 0.008, stone))
        for side in (-1, 1):
            pieces.append(mk.box(f'{name}-kneeler-{end}-{side}', (xb - xa + 0.02, 0.07, 0.06), at=((xa + xb) / 2, side * (depth / 2 - 0.025), roof_z(depth / 2) + 0.05), material=stone))
    for i, (x, door_x, lit_down, lit_up) in enumerate(layout):
        # recessed door with a fanlight over it, a stone head and a step
        pieces.append(mk.box(f'{name}-door-{i}', (0.09, 0.012, 0.2), at=(door_x, front + 0.044, 0.1), material=door_paint))
        pieces.append(mk.plane(f'{name}-fanlight-{i}', (0.09, 0.05), at=(door_x, front + 0.046, 0.225), material=house_window_lit if lit_down else house_window_dark, rotate=(math.pi / 2, 0, 0)))
        pieces.append(mk.box(f'{name}-door-head-{i}', (0.13, 0.02, 0.035), at=(door_x, front - 0.004, 0.272), material=stone))
        pieces.append(mk.box(f'{name}-step-{i}', (0.13, 0.055, 0.02), at=(door_x, front - 0.012, 0.01), material=stone))
        for floor, z, lit in ((0, 0.2, lit_down), (1, 0.5, lit_up)):
            wx = x + width * 0.12 if floor == 0 else x
            glass_y = front + 0.026
            pieces.append(mk.plane(f'{name}-window-{i}-{floor}', (0.11, 0.16), at=(wx, glass_y, z), material=house_window_lit if lit else house_window_dark, rotate=(math.pi / 2, 0, 0)))
            pieces.append(mk.box(f'{name}-sash-h-{i}-{floor}', (0.11, 0.01, 0.011), at=(wx, glass_y - 0.006, z), material=sash_paint))   # meeting rail
            pieces.append(mk.box(f'{name}-sill-{i}-{floor}', (0.15, 0.045, 0.018), at=(wx, front - 0.012, z - 0.089), material=stone))
            pieces.append(mk.box(f'{name}-lintel-{i}-{floor}', (0.15, 0.02, 0.032), at=(wx, front - 0.004, z + 0.096), material=stone))
    # chimney stacks on the party walls (and both gables), with oversailing courses and rimmed pots
    stack_xs = [-length / 2 + 0.06] + [-length / 2 + i * width for i in range(2, houses - 1, 2)] + [length / 2 - 0.06]
    pot = [(0.012, 0), (0.0095, 0.045), (0.0125, 0.05), (0.0125, 0.057), (0, 0.053)]
    for k, sx in enumerate(stack_xs):
        top = height + rise * 0.7 + 0.2
        pieces.append(mk.box(f'{name}-stack-{k}', (0.12, 0.09, 0.2), at=(sx, 0.04, top - 0.1), material=brick_red))
        pieces.append(mk.box(f'{name}-stack-course-{k}', (0.14, 0.11, 0.02), at=(sx, 0.04, top - 0.035), material=brick_red))
        pieces.append(mk.box(f'{name}-stack-cap-{k}', (0.132, 0.102, 0.014), at=(sx, 0.04, top + 0.007), material=stone))
        for j, kx in enumerate((-0.03, 0.03)):
            pieces.append(lathe(f'{name}-pot-{k}-{j}', pot, at=(sx + kx, 0.04, top + 0.014), material=terracotta, sides=6))
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
far_rng = np.random.default_rng(11)
for k, (x, z, width, depth, height) in enumerate(((-9.0, -17.0, 4.0, 2.2, 1.4), (2.5, -18.5, 5.0, 2.6, 1.6), (9.5, -16.0, 3.4, 2.0, 1.3), (-3.0, -22.0, 4.6, 2.4, 1.5))):
    add(bx(f'far-works-{k}', (width, depth, height), at=at(x, z, height / 2), material=brick_brown, bevel=0.012))
    front = -z - depth / 2          # Blender y of the front (towards the camera)
    # sawtooth north-light roof: teeth running across, glazed faces towards the camera
    teeth = max(3, int(depth / 0.55)); pitch = depth / teeth; tooth_h = 0.36
    for t in range(teeth):
        y0 = front + t * pitch
        add(slab(f'far-roof-{k}-{t}', [(y0, height), (y0 + pitch, height), (y0, height + tooth_h)], x - width / 2 - 0.02, x + width / 2 + 0.02, roof_iron))
        panes = int(width / 0.24)
        for p in range(panes):
            px = x - width / 2 + (p + 0.5) * width / panes
            lit = far_rng.random() < 0.35
            add(mk.plane(f'far-light-{k}-{t}-{p}', (width / panes - 0.012, tooth_h - 0.06), at=(px, y0 - 0.004, height + tooth_h / 2 + 0.005),
                         material=house_window_lit if lit else house_window_dark, rotate=(math.pi / 2, 0, 0)))
    # a stone cornice, pilasters and a row of tall windows on the front
    add(bx(f'far-cornice-{k}', (width + 0.06, 0.06, 0.06), at=(x, front - 0.015, height - 0.03), material=stone, bevel=0.008))
    bays = int(width / 0.8)
    for i in range(bays + 1):
        add(mk.box(f'far-pilaster-{k}-{i}', (0.09, 0.03, height - 0.06), at=(x - width / 2 + i * width / bays, front - 0.012, (height - 0.06) / 2), material=brick_brown))
    for i in range(bays):
        for w in (-1, 1):
            wx = x - width / 2 + (i + 0.5) * width / bays + w * width / bays * 0.22
            lit = far_rng.random() < 0.45
            add(mk.plane(f'far-window-{k}-{i}-{w}', (0.16, 0.36), at=(wx, front - 0.003, height * 0.62), material=house_window_lit if lit else house_window_dark, rotate=(math.pi / 2, 0, 0)))
            add(mk.box(f'far-sill-{k}-{i}-{w}', (0.2, 0.04, 0.025), at=(wx, front - 0.015, height * 0.62 - 0.19), material=stone))
smoke_tops = []
for k, (x, z, height) in enumerate(((-6.5, -16.5, 5.5), (-1.0, -19.5, 6.5), (4.5, -17.5, 5.0), (11.0, -15.0, 4.6), (-11.5, -20.5, 6.0), (7.5, -23.0, 7.0))):
    radius = lambda h, H=height: 0.24 - 0.09 * h / H
    base = at(x, z, 0)
    # a square plinth with a stone course
    plinth = add(bx(f'far-chimney-plinth-{k}', (0.62, 0.62, 0.6), at=at(x, z, 0.3), material=chimney_brick, bevel=0.012))
    add(bx(f'far-chimney-plinth-cap-{k}', (0.68, 0.68, 0.06), at=at(x, z, 0.62), material=stone, bevel=0.01))
    # the tapered shaft with a corbelled cap (stepped courses flaring out)
    rc = radius(height - 0.3)
    shaft = add(lathe(f'far-chimney-{k}', [(0, 0.6), (radius(0.6), 0.6), (rc, height - 0.3), (rc + 0.025, height - 0.28), (rc + 0.025, height - 0.21),
                                           (rc + 0.05, height - 0.19), (rc + 0.05, height - 0.11), (rc + 0.07, height - 0.09), (rc + 0.07, height - 0.04), (0, height - 0.04)],
                      at=base, material=chimney_brick, sides=16))
    # stone cornice on top with a rolled lip and a dark open flue
    add(lathe(f'far-chimney-cap-{k}', [(rc + 0.075, height - 0.04), (rc + 0.075, height + 0.03), (rc + 0.055, height + 0.07), (rc + 0.04, height + 0.12),
                                       (rc - 0.03, height + 0.12), (rc - 0.03, height + 0.04), (0, height + 0.04)], at=base, material=stone, sides=16))
    # iron bands round the shaft
    for f in (0.3, 0.5, 0.7, 0.86):
        h = height * f
        add(lathe(f'far-chimney-band-{k}-{f}', [(radius(h) + 0.008, h - 0.014), (radius(h) + 0.008, h + 0.014)], at=base, material=iron, sides=16, sharp=60))
    smoke_tops.append(mk.marker(f'smoke-{k}', at(x, z, height + 0.15)))
    # soot: the brick darkens towards the top (every part in chimney-brick carries the attribute)
    colour_by(shaft, lambda bx_, by_, bz_, H=height: 1.0 - 0.6 * smoothstep(0.45 * H, 0.97 * H, bz_))
    colour_by(plinth, lambda *a: 1.0)

# a church with a broach spire, and a water tower on iron legs, for the skyline
CX, CZ = -7.8, -23.6
add(bx('church-nave', (0.7, 1.5, 0.8), at=at(CX, CZ, 0.4), material=stone, bevel=0.01))
add(slab('church-roof', [(CX - 0.4, 0.8), (CX + 0.4, 0.8), (CX, 1.22)], -CZ - 0.78, -CZ + 0.78, slate, axis='y'))
add(bx('church-tower', (0.42, 0.42, 1.55), at=at(CX, CZ + 0.95, 0.775), material=stone, bevel=0.012))
add(bx('church-tower-band', (0.46, 0.46, 0.05), at=at(CX, CZ + 0.95, 1.55), material=stone, bevel=0.008))
for side in range(4):
    a = side * math.pi / 2
    ox, oz = 0.212 * math.sin(a), 0.212 * math.cos(a)
    add(mk.box(f'church-belfry-{side}', (0.12 if side % 2 == 0 else 0.004, 0.004 if side % 2 == 0 else 0.12, 0.26), at=at(CX + ox, CZ + 0.95 + oz, 1.33), material=iron))
    add(mk.cylinder(f'church-pinnacle-{side}', 0.035, 0.22, at=at(CX + (0.18 if side in (0, 1) else -0.18), CZ + 0.95 + (0.18 if side in (0, 3) else -0.18), 1.68), material=stone, sides=4, radius_top=0.0))
add(mk.cylinder('church-spire', 0.2, 1.5, at=at(CX, CZ + 0.95, 1.575 + 0.75), material=slate, sides=8, radius_top=0.0, rotate=(0, 0, math.pi / 8)))
add(mk.cylinder('church-vane', 0.006, 0.18, at=at(CX, CZ + 0.95, 3.38), material=iron, sides=4))
WX, WZ = 6.2, -15.4
for i, (dx, dz) in enumerate(((-0.27, -0.27), (0.27, -0.27), (0.27, 0.27), (-0.27, 0.27))):
    add(mk.box(f'water-tower-leg-{i}', (0.05, 0.05, 1.2), at=at(WX + dx, WZ + dz, 0.6), material=iron))
for lvl in (0.4, 0.85):
    for i, (sx, sz, ln) in enumerate(((0, -0.27, (0.56, 0.025)), (0, 0.27, (0.56, 0.025)), (-0.27, 0, (0.025, 0.56)), (0.27, 0, (0.025, 0.56)))):
        add(mk.box(f'water-tower-tie-{lvl}-{i}', (ln[0], ln[1], 0.025), at=at(WX + sx, WZ + sz, lvl), material=iron))
add(bx('water-tower-tank', (0.74, 0.74, 0.42), at=at(WX, WZ, 1.41), material=gas_iron, bevel=0.012))
add(bx('water-tower-rim', (0.78, 0.78, 0.035), at=at(WX, WZ, 1.63), material=iron, bevel=0.006))
add(mk.cylinder('water-tower-roof', 0.55, 0.16, at=at(WX, WZ, 1.72), material=iron, sides=4, radius_top=0.05, rotate=(0, 0, math.pi / 4)))

# a gasholder: a round iron tank inside a ring of columns tied by lattice girders
GX, GZ = -4.8, -15.2
add(mk.cylinder('gasholder-tank', 1.5, 1.6, at=at(GX, GZ, 0.8), material=gas_iron, sides=40))
add(mk.cylinder('gasholder-crown', 1.52, 0.12, at=at(GX, GZ, 1.66), material=gas_iron, sides=40, radius_top=1.3))
for h in (0.45, 1.15):
    add(mk.cylinder(f'gasholder-band-{h}', 1.515, 0.04, at=at(GX, GZ, h), material=iron, sides=40, cap=False))
for i in range(12):
    a = i / 12 * 2 * math.pi
    cx, cz = GX + 1.7 * math.cos(a), GZ + 1.7 * math.sin(a)
    add(mk.cylinder(f'gasholder-column-{i}', 0.04, 2.6, at=at(cx, cz, 1.3), material=iron, sides=8))
    add(mk.box(f'gasholder-column-cap-{i}', (0.11, 0.11, 0.05), at=at(cx, cz, 2.62), material=iron, rotate=(0, 0, -a)))
    add(mk.box(f'gasholder-column-foot-{i}', (0.12, 0.12, 0.08), at=at(cx, cz, 0.04), material=stone, rotate=(0, 0, -a)))
    # crossed lattice bracing to the next column, between the girder levels
    b2 = (i + 1) / 12 * 2 * math.pi
    nx, nz = GX + 1.7 * math.cos(b2), GZ + 1.7 * math.sin(b2)
    mx, mz = (cx + nx) / 2, (cz + nz) / 2
    chord = math.hypot(nx - cx, nz - cz)
    yaw = math.atan2(-(nz - cz), nx - cx)       # the bay's direction in Blender x-y
    for lo, hi in ((0.9, 1.75), (1.75, 2.55)):
        tilt = math.atan2(hi - lo, chord)
        diag = math.hypot(hi - lo, chord)
        for s in (-1, 1):
            add(mk.box(f'gasholder-brace-{i}-{lo}-{s}', (diag, 0.014, 0.014), at=(mx, -mz, (lo + hi) / 2), material=iron, rotate=(0, s * tilt, yaw)))
for level in (0.9, 1.75, 2.55):
    add(mk.cylinder(f'gasholder-girder-{level}', 1.72, 0.05, at=at(GX, GZ, level), material=iron, sides=48, cap=False))

# a railway viaduct across the back: brick arches between piers, imposts, string course, parapet
VZ, VH, SPAN = -20.0, 1.7, 0.9
PIER = 0.18
SPRING = VH - 0.45
add(bx('viaduct-deck', (40, 0.5, 0.18), at=at(0, VZ, VH + 0.09), material=brick_yellow, bevel=0.01))
n_piers = int(40 / SPAN) + 1
for i in range(n_piers):
    x = -20 + i * SPAN
    add(mk.box(f'viaduct-pier-{i}', (PIER, 0.5, VH), at=at(x, VZ, VH / 2), material=brick_yellow))
    add(mk.box(f'viaduct-impost-{i}', (PIER + 0.05, 0.54, 0.045), at=at(x, VZ, SPRING), material=stone))
    add(mk.box(f'viaduct-plinth-{i}', (PIER + 0.06, 0.56, 0.12), at=at(x, VZ, 0.06), material=brick_yellow))
    if i < n_piers - 1:
        xa, xb = x + PIER / 2, x + SPAN - PIER / 2
        xc, rad = (xa + xb) / 2, (xb - xa) / 2
        arc = [(xc + rad * math.cos(math.pi * j / 10), SPRING + rad * math.sin(math.pi * j / 10)) for j in range(1, 10)]
        outline = [(xa, SPRING), (xa, VH), (xb, VH), (xb, SPRING)] + arc
        add(slab(f'viaduct-arch-{i}', outline, -VZ - 0.25, -VZ + 0.25, brick_yellow, axis='y'))
add(bx('viaduct-string', (40, 0.56, 0.04), at=at(0, VZ, VH - 0.01), material=stone, bevel=0.006))
add(bx('viaduct-parapet', (40, 0.06, 0.12), at=at(0, VZ + 0.22, VH + 0.24), material=stone, bevel=0.006))
add(bx('viaduct-coping', (40, 0.09, 0.025), at=at(0, VZ + 0.22, VH + 0.31), material=stone, bevel=0.006))
add(mk.box('viaduct-parapet-back', (40, 0.06, 0.12), at=at(0, VZ - 0.22, VH + 0.24), material=brick_yellow))
# a goods train standing on it: a tank engine and five wagons, a silhouette against the sky
TY = VH + 0.18
TX = -2.2
add(mk.cylinder('train-boiler', 0.065, 0.36, at=(TX + 0.18, -VZ, TY + 0.13), material=iron, sides=12, rotate=(0, math.pi / 2, 0)))
add(bx('train-cab', (0.16, 0.2, 0.22), at=(TX - 0.06, -VZ, TY + 0.13), material=iron, bevel=0.008))
add(bx('train-cab-roof', (0.2, 0.24, 0.02), at=(TX - 0.06, -VZ, TY + 0.25), material=iron, bevel=0.005))
add(bx('train-tanks', (0.3, 0.2, 0.1), at=(TX + 0.16, -VZ, TY + 0.1), material=iron, bevel=0.006))
add(lathe('train-chimney', [(0, 0), (0.022, 0), (0.018, 0.07), (0.028, 0.09), (0.028, 0.1), (0, 0.1)], at=(TX + 0.31, -VZ, TY + 0.18), material=iron, sides=10))
add(lathe('train-dome', [(0, 0), (0.03, 0), (0.028, 0.03), (0.015, 0.05), (0, 0.055)], at=(TX + 0.17, -VZ, TY + 0.185), material=iron, sides=10))
add(mk.box('train-frame', (0.62, 0.22, 0.05), at=(TX + 0.1, -VZ, TY + 0.03), material=iron))
for w in range(5):
    wx = TX - 0.4 - w * 0.36
    add(bx(f'wagon-{w}', (0.32, 0.22, 0.13), at=(wx, -VZ, TY + 0.1), material=wagon_paint if w % 2 else timber, bevel=0.006))
    add(mk.box(f'wagon-frame-{w}', (0.34, 0.2, 0.04), at=(wx, -VZ, TY + 0.025), material=iron))
    if w % 2 == 0:
        add(mk.cylinder(f'wagon-load-{w}', 0.11, 0.06, at=(wx, -VZ, TY + 0.18), material=iron, sides=6, radius_top=0.03))

# ------------------------------------------------------------------------------- gas lamps
lamps = []
base_profile = [(0, 0), (0.042, 0), (0.042, 0.025), (0.032, 0.04), (0.03, 0.09), (0.022, 0.105), (0.02, 0.15), (0.015, 0.165), (0, 0.165)]
for k, (x, z) in enumerate(((-3.6, STREET_Z + 0.42), (0.4, STREET_Z + 0.42), (4.2, STREET_Z + 0.42), (-2.2, BACK_STREET_Z - 0.55), (2.8, BACK_STREET_Z - 0.55), (-4.6, 6.4))):
    bxy = at(x, z)
    add(lathe(f'lamp-base-{k}', base_profile, at=at(x, z, 0), material=iron, sides=10))
    add(mk.cylinder(f'lamp-post-{k}', 0.015, 0.72, at=at(x, z, 0.16 + 0.36), material=iron, sides=8, radius_top=0.012))
    add(lathe(f'lamp-collar-{k}', [(0.012, 0), (0.02, 0.01), (0.02, 0.02), (0.03, 0.03), (0.035, 0.035), (0, 0.035)], at=at(x, z, 0.865), material=iron, sides=8))
    # the ladder bar, with ball ends
    add(mk.box(f'lamp-ladder-bar-{k}', (0.13, 0.012, 0.012), at=at(x, z, 0.78), material=iron))
    for s in (-1, 1):
        add(mk.cylinder(f'lamp-ladder-end-{k}-{s}', 0.011, 0.02, at=(bxy[0] + s * 0.068, bxy[1], 0.78), material=iron, sides=6))
    # a four-pane lantern: glass (lamp-glow), iron corner posts and frames, a pyramid roof and finial
    add(mk.box(f'lamp-head-{k}', (0.06, 0.06, 0.08), at=at(x, z, 0.94), material=lamp))
    for cx_, cy_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        add(mk.box(f'lamp-frame-post-{k}-{cx_}{cy_}', (0.009, 0.009, 0.09), at=(bxy[0] + cx_ * 0.031, bxy[1] + cy_ * 0.031, 0.94), material=iron))
    add(mk.box(f'lamp-frame-foot-{k}', (0.072, 0.072, 0.012), at=at(x, z, 0.897), material=iron))
    add(mk.box(f'lamp-frame-top-{k}', (0.078, 0.078, 0.012), at=at(x, z, 0.984), material=iron))
    add(mk.cylinder(f'lamp-cap-{k}', 0.062, 0.04, at=at(x, z, 1.01), material=iron, sides=4, radius_top=0.012, rotate=(0, 0, math.pi / 4)))
    add(lathe(f'lamp-finial-{k}', [(0, 0), (0.008, 0), (0.005, 0.015), (0.01, 0.025), (0.004, 0.04), (0, 0.045)], at=at(x, z, 1.028), material=iron, sides=8))
    lamps.append(mk.marker(f'lamp-{k}', at(x, z, 0.94)))

# -------------------------------------------------- things near the camera, for the bottom of the frame
# a low brick wall with piers, a plinth, saddleback coping stones and spear-headed iron railings
WALL_Z = 6.3
add(bx('front-wall', (3.2, 0.14, 0.22), at=at(-3.4, WALL_Z, 0.11), material=brick_red, bevel=0.008))
add(bx('front-wall-plinth', (3.2, 0.17, 0.05), at=at(-3.4, WALL_Z, 0.025), material=brick_red, bevel=0.008))
PIERS = (-4.92, -3.4, -1.88)
for i, px in enumerate(PIERS):
    add(bx(f'front-wall-pier-{i}', (0.2, 0.2, 0.33), at=at(px, WALL_Z, 0.165), material=brick_red, bevel=0.01))
    add(bx(f'front-wall-pier-cap-{i}', (0.25, 0.25, 0.035), at=at(px, WALL_Z, 0.3475), material=stone, bevel=0.008))
    add(smooth_finish(mk.cylinder(f'front-wall-pier-top-{i}', 0.16, 0.07, at=at(px, WALL_Z, 0.4), material=stone, sides=4, radius_top=0.025, rotate=(0, 0, math.pi / 4)), 0.006))
coping = [(-0.09, 0.0), (0.09, 0.0), (0.09, 0.024), (0.0, 0.042), (-0.09, 0.024)]
for a, b in ((PIERS[0] + 0.1, PIERS[1] - 0.1), (PIERS[1] + 0.1, PIERS[2] - 0.1)):
    n = round((b - a) / 0.32)
    step = (b - a) / n
    for i in range(n):
        s = slab(f'front-wall-coping-{a:.2f}-{i}', [(u - WALL_Z, v + 0.22) for u, v in coping], a + i * step + 0.004, a + (i + 1) * step - 0.004, stone)
        add(smooth_finish(s, 0.006))
for i in range(32):
    x = -4.95 + i * 0.1
    if any(abs(x - px) < 0.12 for px in PIERS): continue
    add(mk.cylinder(f'railing-{i}', 0.006, 0.19, at=at(x, WALL_Z, 0.262 + 0.095), material=iron, sides=6))
    add(mk.cylinder(f'railing-spear-{i}', 0.012, 0.032, at=at(x, WALL_Z, 0.468), material=iron, sides=4, radius_top=0.0))
    add(mk.cylinder(f'railing-collar-{i}', 0.009, 0.012, at=at(x, WALL_Z, 0.448), material=iron, sides=6))
for a, b in ((PIERS[0] + 0.1, PIERS[1] - 0.1), (PIERS[1] + 0.1, PIERS[2] - 0.1)):
    add(mk.box(f'railing-top-{a:.2f}', (b - a, 0.014, 0.016), at=at((a + b) / 2, WALL_Z, 0.43), material=iron))
    add(mk.box(f'railing-low-{a:.2f}', (b - a, 0.012, 0.012), at=at((a + b) / 2, WALL_Z, 0.29), material=iron))
for k, (x, z, size) in enumerate(((2.6, 6.6, 0.26), (2.86, 6.75, 0.22), (2.72, 6.62, 0.2))):
    cz = size / 2 + (0.26 if k == 2 else 0)
    add(bx(f'near-crate-{k}', (size, size, size), at=at(x, z, cz), material=timber, bevel=0.006))
    # battens: corner boards and two bands round each crate
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        add(bx(f'near-crate-{k}-corner-{sx}{sy}', (0.03, 0.03, size + 0.004), at=(x + sx * (size / 2 - 0.012), -z + sy * (size / 2 - 0.012), cz), material=timber, bevel=0.004))
    for h in (-0.3, 0.3):
        add(bx(f'near-crate-{k}-band-{h}', (size + 0.012, size + 0.012, 0.03), at=at(x, z, cz + h * size), material=timber, bevel=0.004))


# ------------------------------------------------------------------------------ finishing
def join_by_material(objects):
    """Join still parts that share one material (notes B15: far fewer draws on the stage). Shared
    meshes (the terrace copies) and parts with several materials stay as they are."""
    groups = {}
    for o in objects:
        if o.type != 'MESH' or len(o.data.materials) != 1 or o.data.users > 1: continue
        groups.setdefault(o.data.materials[0].name, []).append(o)
    for name, members in groups.items():
        if len(members) < 2: continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in members: o.select_set(True)
        bpy.context.view_layer.objects.active = members[0]
        bpy.ops.object.join()
        members[0].name = name


def finish_town(path):
    """Like mk.finish (no baking): apply modifiers, join, and write the .glb with the colour
    attributes (COLOR_0) (notes B13, B14)."""
    scene = bpy.context.scene
    for o in [o for o in scene.objects if o.type == 'MESH' and o.modifiers]:
        mk.apply_modifiers(o)
    keep_apart = {o.name for o in copies} | {'ground'}
    join_by_material([o for o in scene.objects if o.type == 'MESH' and o.name not in keep_apart])
    meshes = [o for o in scene.objects if o.type == 'MESH']
    print(f'{os.path.basename(path)}: {len(meshes)} parts, {mk.count_triangles(meshes)} triangles')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_materials='EXPORT',
                              export_image_format='AUTO', export_extras=True, export_yup=True,
                              export_vertex_color='ACTIVE', export_all_vertex_colors=False)
    print(f'wrote {path} ({os.path.getsize(path) // 1024} KB)')


finish_town(OUT)
