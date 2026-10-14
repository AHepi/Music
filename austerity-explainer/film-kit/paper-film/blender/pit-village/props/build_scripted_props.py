# What this does: builds the pit-village props that no free model covers, in Blender by script, and
# writes each as its own .glb with its line in index.json:
#   coal-tub            riveted steel pit tub heaped with coal, four turning wheels
#   narrow-gauge-track  3 m of pit railway: flat-bottomed rails, wooden sleepers, spikes, fishplates
#   coal-tub-on-track   the two together, the tub standing on the rails
#   handcart            a coal merchant's two-wheeled handcart with large spoked wheels
#   coal-sacks          a stack of filled hessian coal sacks, some with stencilled marks
#   coal-pile           a heap of coal lumps on a bed of slack
#   safety-lamp         a Davy-style miner's safety lamp: brass vessel, wire gauze, little flame
#   colliery-name-board the painted "ABBOTSCLOUGH COLLIERY" board on two posts with iron straps
#   notice-paper        the printed lock-out notice on weathered paper, torn corners, four tacks
#   notice-on-board     the notice pasted on a black notice board with a rain hood
#
# Wheels that turn are their own objects (wheel_front_left, ...) with their origin on their axle.
# The axle runs along Blender's y, which the exporter turns into three.js's z, so in three.js
# wheel.rotation.z turns a wheel.
#
# Run (after download_poly_haven.py and paint_prop_pictures.py):
#   blender -b --python build_scripted_props.py                 (all)
#   blender -b --python build_scripted_props.py -- coal-tub     (some)

import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_library as library  # noqa: E402
import scripted_kit as kit  # noqa: E402

SCRIPTED = 'Built by script (paper-film/blender/pit-village/props/build_scripted_props.py) with Poly Haven CC0 surface textures'
LICENCE = 'Own work; textures CC0 1.0 (Poly Haven); lettering fonts: Ultra (Apache 2.0), Old Standard TT, Abril Fatface, Alfa Slab One (SIL Open Font Licence)'


# ------------------------------------------------------------------------------------ materials

def steel():
    return kit.surface_material('tub-steel', 'rusty_metal_02', 0.9, tint=(0.24, 0.205, 0.18), tint_strength=0.55)


def iron():
    return kit.surface_material('wrought-iron', 'rust_coarse_01', 0.5, tint=(0.30, 0.25, 0.21), tint_strength=0.6, metallic=0.6)


def black_iron():
    return kit.surface_material('black-iron', 'rusty_painted_metal', 0.6, tint=(0.16, 0.15, 0.15), tint_strength=0.85, metallic=0.4)


def grey_wood():
    return kit.surface_material('grey-timber', 'weathered_planks', 1.6)


def brown_wood():
    return kit.surface_material('brown-timber', 'weathered_brown_planks', 1.6)


def rough_wood():
    return kit.surface_material('rough-timber', 'rough_wood', 1.0)


def coal():
    return kit.surface_material('coal', 'dark_rock', 0.4, tint=(0.075, 0.075, 0.08), tint_strength=0.8, metallic=0.0,
                                roughness=0.38, normal_strength=1.4)


def slack():
    return kit.surface_material('coal-slack', 'dark_rock', 0.8, tint=(0.09, 0.085, 0.085), tint_strength=0.7, metallic=0.0,
                                roughness=0.8, normal_strength=1.0)


def brass():
    # worn brass: smooth metal, the roughness and relief of lightly scratched steel plate, a brass colour
    return kit.surface_material('brass', 'rusty_metal_04', 0.12, tint=(0.70, 0.52, 0.26), tint_strength=0.92, metallic=1.0, roughness=0.32, normal_strength=0.4)


# -------------------------------------------------------------------------------------- helpers

def wheel_ready(obj, location, name):
    """Bake the wheel's shape as built around the origin, then move it to its axle. Its origin stays
    on the axle so it can turn."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.name = name
    obj.location = location
    return obj


def profile_bar(name, outline, length, material, at=(0, 0, 0)):
    """A straight bar `length` long along x with the cross-section outline [(y, z), ...] (a rail)."""
    bm = bmesh.new()
    ends = []
    for x in (-length / 2, length / 2):
        ends.append([bm.verts.new((x, y, z)) for y, z in outline])
    count = len(outline)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new([ends[0][i], ends[0][j], ends[1][j], ends[1][i]])
    bm.faces.new(list(reversed(ends[0]))); bm.faces.new(ends[1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.location = at
    obj.data.materials.append(material)
    bpy.context.view_layer.update()
    kit.project_by_facing(obj, 0.6)
    return obj


def mound_height(x, y, radius_x, radius_y, height, rng_offsets):
    """Height of a heap at (x, y): a rounded cone with a little lumpy wobble."""
    r = math.sqrt((x / radius_x) ** 2 + (y / radius_y) ** 2)
    if r >= 1: return 0.0
    wobble = sum(a * math.sin(fx * x + fy * y + p) for a, fx, fy, p in rng_offsets)
    return height * (1 - r ** 1.6) ** 1.1 * (1 + wobble)


def wobbles(seed, count=5, amount=0.06):
    rng = random.Random(seed)
    return [(rng.uniform(0.3, 1) * amount, rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(0, 6.3)) for _ in range(count)]


def heap_surface(name, radius_x, radius_y, height, seed, material, cuts=28, base=0.0, skirt=1.08):
    """The ground-hugging body of a heap (under the lumps), as a grid lifted into a mound."""
    offsets = wobbles(seed)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=cuts, y_segments=cuts, size=1.0)
    for v in bm.verts:
        x, y = v.co.x * radius_x * skirt, v.co.y * radius_y * skirt
        v.co = Vector((x, y, base + mound_height(x, y, radius_x, radius_y, height, offsets) - 0.01))
    # drop the grid's square corners outside the heap
    outside = [v for v in bm.verts if (v.co.x / (radius_x * skirt)) ** 2 + (v.co.y / (radius_y * skirt)) ** 2 > 1.0]
    bmesh.ops.delete(bm, geom=outside, context='VERTS')
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for poly in mesh.polygons: poly.use_smooth = True
    kit.project_by_facing(obj, 0.8)
    return obj, offsets


def lumps_on_heap(name, count, radius_x, radius_y, height, offsets, seed, sizes=(0.025, 0.09), base=0.0,
                  spread=1.0, centre=(0, 0)):
    """Coal lumps lying on a heap's surface; bigger lumps roll to the bottom."""
    rng = random.Random(seed)
    originals = [kit.lump(f'lump-shape-{i}', 1.0, seed * 10 + i, coal()) for i in range(10)]
    placements = []
    for _ in range(count):
        angle = rng.uniform(0, 2 * math.pi)
        r = math.sqrt(rng.uniform(0, 1)) * spread
        x, y = math.cos(angle) * r * radius_x, math.sin(angle) * r * radius_y
        size = rng.uniform(*sizes) * (0.7 + 0.6 * r)
        z = base + mound_height(x, y, radius_x, radius_y, height, offsets) + size * 0.25
        placements.append(((x + centre[0], y + centre[1], z),
                           Euler((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0, 6.3))), size))
    lumps = kit.scatter_copies(name, originals, placements, coal())
    for o in originals: kit.remove(o)
    return lumps


# -------------------------------------------------------------------------------------- coal tub

TUB_LENGTH, TUB_WIDTH, TUB_HEIGHT, TUB_FLOOR = 1.0, 0.70, 0.52, 0.32
RAIL_CENTRES = 0.30   # rails at y = +-0.30 (about 22-inch gauge, common in British pits)
TUB_WHEEL_RADIUS = 0.15


def tub_wheel(name, location, inner_side):
    """A cast-iron flanged tub wheel with six spokes, its flange on the rail's inner side."""
    m = iron()
    tread = kit.ring('tread', 0.115, TUB_WHEEL_RADIUS, 0.05, material=m, segments=32)
    flange = kit.ring('flange', 0.13, TUB_WHEEL_RADIUS + 0.022, 0.014, at=(0, 0, inner_side * 0.022), material=m, segments=32)
    hub = kit.cylinder('hub', 0.04, 0.08, material=m, sides=16)
    boss = kit.cylinder('boss', 0.028, 0.10, material=m, sides=12)
    spokes = [kit.rod(f'spoke{i}', (0.035 * math.cos(a), 0.035 * math.sin(a), 0), (0.12 * math.cos(a), 0.12 * math.sin(a), 0), 0.012,
                      m, sides=6, radius_end=0.016) for i, a in enumerate(2 * math.pi * k / 6 for k in range(6))]
    wheel = kit.join('wheel', [tread, flange, hub, boss] + spokes)
    wheel.rotation_euler = (math.pi / 2, 0, 0)  # axle along y
    return wheel_ready(wheel, location, name)


def build_coal_tub(with_coal=True):
    parts = []
    s = steel()
    # the open steel body: a box with no lid, plates 6 mm thick
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * TUB_LENGTH, v.co.y * TUB_WIDTH, (v.co.z + 0.5) * TUB_HEIGHT))
    top = [f for f in bm.faces if f.normal.z > 0.9]
    bmesh.ops.delete(bm, geom=top, context='FACES')
    mesh = bpy.data.meshes.new('body'); bm.to_mesh(mesh); bm.free()
    body = bpy.data.objects.new('body', mesh); bpy.context.scene.collection.objects.link(body)
    body.location = (0, 0, TUB_FLOOR); body.data.materials.append(s)
    thick = body.modifiers.new('plates', 'SOLIDIFY'); thick.thickness = 0.006; thick.offset = -1
    bevel = body.modifiers.new('bevel', 'BEVEL'); bevel.width = 0.004; bevel.segments = 2; bevel.limit_method = 'ANGLE'
    kit.apply_all(body); kit.project_by_facing(body, 0.9)
    parts.append(body)
    top_z = TUB_FLOOR + TUB_HEIGHT
    hx, hy = TUB_LENGTH / 2, TUB_WIDTH / 2
    # rolled rim: a round bar along all four top edges
    rim = [kit.rod('rim', (-hx - 0.01, y, top_z), (hx + 0.01, y, top_z), 0.013, s, sides=10) for y in (-hy - 0.004, hy + 0.004)]
    rim += [kit.rod('rim', (x, -hy - 0.01, top_z), (x, hy + 0.01, top_z), 0.013, s, sides=10) for x in (-hx - 0.004, hx + 0.004)]
    parts += rim
    # corner angle irons and two horizontal bands, all standing proud of the plates
    angles = []
    for x in (-hx, hx):
        for y in (-hy, hy):
            sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
            centre_z = TUB_FLOOR + TUB_HEIGHT / 2
            angles.append(kit.box('angle', (0.06, 0.008, TUB_HEIGHT - 0.01), (x - sx * 0.03, y + sy * 0.004, centre_z), s, bevel=0.002))
            angles.append(kit.box('angle', (0.008, 0.06, TUB_HEIGHT - 0.01), (x + sx * 0.004, y - sy * 0.03, centre_z), s, bevel=0.002))
    bands = []
    for z in (TUB_FLOOR + 0.12, TUB_FLOOR + 0.36):
        for y in (-hy - 0.005, hy + 0.005):
            bands.append(kit.box('band', (TUB_LENGTH - 0.12, 0.007, 0.05), (0, y, z), s, bevel=0.002))
        for x in (-hx - 0.005, hx + 0.005):
            bands.append(kit.box('band', (0.007, TUB_WIDTH - 0.12, 0.05), (x, 0, z), s, bevel=0.002))
    parts += angles + bands
    # rivets: up every corner angle, along every band, and under the rim
    rivet = 0.008
    for normal, fixed_axis, fixed, span in (((0, -1, 0), 'y', -hy - 0.012, hx), ((0, 1, 0), 'y', hy + 0.012, hx),
                                            ((-1, 0, 0), 'x', -hx - 0.012, hy), ((1, 0, 0), 'x', hx + 0.012, hy)):
        points = []
        for corner in (-1, 1):
            along = corner * (span - 0.03)
            for k in range(7):
                z = TUB_FLOOR + 0.04 + k * (TUB_HEIGHT - 0.08) / 6
                points.append((along, z))
        for z in (TUB_FLOOR + 0.12, TUB_FLOOR + 0.36):
            for k in range(1, 8):
                points.append((-span + 0.06 + k * (2 * span - 0.12) / 8, z))
        for k in range(10):
            points.append((-span + 0.05 + k * (2 * span - 0.1) / 9, top_z - 0.035))
        world = [((fixed, a, z) if fixed_axis == 'x' else (a, fixed, z)) for a, z in points]
        parts.append(kit.studs('rivets', world, rivet, s, normal=normal))
    # underframe: two oak sole bars, iron axle boxes, axles, drawbars with hook and chain
    wood = rough_wood()
    for y in (-0.17, 0.17):
        parts.append(kit.box('sole-bar', (TUB_LENGTH + 0.08, 0.08, 0.10), (0, y, TUB_FLOOR - 0.05), wood, bevel=0.006))
        for x in (-0.3, 0.3):
            parts.append(kit.box('axle-box', (0.10, 0.06, 0.09), (x, y, TUB_WHEEL_RADIUS + 0.03), iron(), bevel=0.006))
            parts.append(kit.hex_bolts('axle-box-bolts', [(x - 0.03, y - 0.031, TUB_FLOOR - 0.04), (x + 0.03, y - 0.031, TUB_FLOOR - 0.04)], 0.009, iron()))
    for x in (-0.3, 0.3):
        parts.append(kit.rod('axle', (x, -RAIL_CENTRES - 0.05, TUB_WHEEL_RADIUS), (x, RAIL_CENTRES + 0.05, TUB_WHEEL_RADIUS), 0.022, iron(), sides=12))
    for end in (-1, 1):
        x = end * (hx + 0.04)
        parts.append(kit.box('drawbar', (0.16, 0.05, 0.04), (end * (hx + 0.06), 0, TUB_FLOOR - 0.02), iron(), bevel=0.005))
        parts.append(kit.box('buffer-block', (0.05, 0.40, 0.09), (x, 0, TUB_FLOOR - 0.03), wood, bevel=0.008))
    # a hook and three links of coupling chain hanging from one end
    hook_x = hx + 0.14
    parts.append(kit.chain_link('hook-eye', (hook_x, 0, TUB_FLOOR - 0.02), (0, 0, 0), iron()))
    for k in range(3):
        parts.append(kit.chain_link('chain', (hook_x + 0.035, 0, TUB_FLOOR - 0.06 - k * 0.05), (math.pi / 2, (k % 2) * math.pi / 2, math.pi / 2), iron()))
    tub = kit.join('tub-body', parts)
    wheels = []
    for x, front in ((0.3, 'front'), (-0.3, 'back')):
        for y, side in ((-RAIL_CENTRES, 'left'), (RAIL_CENTRES, 'right')):
            inner = 1 if y < 0 else -1  # flange towards the middle of the track
            # ring's +z becomes -y after the quarter turn about x, so flip the sign
            wheels.append(tub_wheel(f'wheel_{front}_{side}', (x, y, TUB_WHEEL_RADIUS), -inner))
    coal_parts = []
    if with_coal:
        offsets = wobbles(5)
        heap, offsets = heap_surface('coal-heap', hx - 0.02, hy - 0.02, 0.20, 5, slack(), cuts=18, base=top_z - 0.05, skirt=1.0)
        # square the heap to the tub: clamp its outline inside the body
        for v in heap.data.vertices:
            v.co.x = max(-hx + 0.012, min(hx - 0.012, v.co.x)); v.co.y = max(-hy + 0.012, min(hy - 0.012, v.co.y))
        lumps = lumps_on_heap('coal-lumps', 118, hx - 0.05, hy - 0.05, 0.20, offsets, 7, sizes=(0.03, 0.07), base=top_z - 0.05, spread=0.98)
        coal_parts = [heap, lumps]
    return tub, wheels, coal_parts


def build_track(length=3.0):
    parts = []
    # flat-bottomed rail, about 30 lb per yard: 80 mm tall, 70 mm foot, 38 mm head
    half_foot, half_web, half_head = 0.035, 0.006, 0.019
    outline = [(-half_foot, 0), (half_foot, 0), (half_foot, 0.006), (half_web + 0.004, 0.014), (half_web, 0.02), (half_web, 0.058),
               (half_head, 0.064), (half_head, 0.08), (-half_head, 0.08), (-half_head, 0.064), (-half_web, 0.058), (-half_web, 0.02),
               (-half_web - 0.004, 0.014), (-half_foot, 0.006)]
    rail_metal = kit.surface_material('rail-steel', 'rusty_metal_04', 0.6, metallic=0.7)
    sleeper_top = 0.09
    for y in (-RAIL_CENTRES, RAIL_CENTRES):
        rail = profile_bar('rail', outline, length, rail_metal, at=(0, y, sleeper_top))
        parts.append(rail)
    rng = random.Random(3)
    wood = grey_wood()
    spike_points = []
    count = int(length / 0.5)
    for k in range(count):
        x = -length / 2 + 0.25 + k * (length - 0.5) / (count - 1)
        turn = rng.uniform(-0.04, 0.04)
        parts.append(kit.box('sleeper', (0.15, 0.95, 0.09), (x + rng.uniform(-0.03, 0.03), rng.uniform(-0.02, 0.02), sleeper_top / 2 - rng.uniform(0, 0.01)),
                             wood, bevel=0.012, rotate=(rng.uniform(-0.02, 0.02), 0, turn)))
        for y in (-RAIL_CENTRES, RAIL_CENTRES):
            for side in (-1, 1):
                spike_points.append((x + side * 0.02, y + side * 0.045, sleeper_top + 0.004))
    for x, y, z in spike_points:
        parts.append(kit.box('spike', (0.018, 0.03, 0.014), (x, y - math.copysign(0.008, y - (RAIL_CENTRES if y > 0 else -RAIL_CENTRES)), z), iron(), bevel=0.002))
    # fishplates bolting the rail joint in the middle, with four bolts each side
    for y in (-RAIL_CENTRES, RAIL_CENTRES):
        for side in (-1, 1):
            parts.append(kit.box('fishplate', (0.40, 0.012, 0.036), (0, y + side * 0.013, sleeper_top + 0.04), rail_metal, bevel=0.003))
            parts.append(kit.hex_bolts('fishplate-bolts', [(bx, y + side * 0.019, sleeper_top + 0.04) for bx in (-0.15, -0.05, 0.05, 0.15)],
                                       0.011, iron(), normal=(0, side, 0)))
    # spilt coal and cinders lying between the sleepers
    originals = [kit.lump(f'chip{i}', 1.0, 90 + i, coal(), detail=1) for i in range(6)]
    placements = []
    for _ in range(46):
        placements.append(((rng.uniform(-length / 2, length / 2), rng.uniform(-0.55, 0.55), 0.008),
                           Euler((0, 0, rng.uniform(0, 6.3))), rng.uniform(0.012, 0.04)))
    parts.append(kit.scatter_copies('spilt-coal', originals, placements, coal()))
    for o in originals: kit.remove(o)
    return kit.join('track', parts)


def coal_tub():
    kit.reset()
    tub, wheels, coal_parts = build_coal_tub()
    library.stand_on_ground('coal-tub', keep_names=[w.name for w in wheels])
    library.save_prop('coal-tub', 'pit coal tub: riveted steel body, oak sole bars, cast-iron flanged wheels (22-inch gauge), coupling chain, heaped with coal; wheels wheel_front_left / _right, wheel_back_left / _right turn about their axle',
                      SCRIPTED, LICENCE, {'turning_parts': [w.name for w in wheels], 'turn_axis': 'local Y in Blender (three.js: rotate wheel.rotation.z after export, axle runs along the model\'s depth)'})


def narrow_gauge_track():
    kit.reset()
    build_track()
    library.stand_on_ground('narrow-gauge-track')
    library.save_prop('narrow-gauge-track', '3 m of narrow-gauge pit railway (22-inch gauge): flat-bottomed rails on weathered sleepers, dog spikes, bolted fishplates, spilt coal; rails run along x; rail top at 0.17 m',
                      SCRIPTED, LICENCE)


def coal_tub_on_track():
    kit.reset()
    track = build_track()
    tub, wheels, coal_parts = build_coal_tub()
    lift = 0.17  # rail top height
    for obj in [tub] + coal_parts + wheels:
        obj.location.z += lift
        obj.location.x += 0.35
    library.stand_on_ground('coal-tub-on-track', keep_names=[w.name for w in wheels])
    library.save_prop('coal-tub-on-track', 'the coal tub standing on the 3 m length of narrow-gauge track; wheels turn as in coal-tub',
                      SCRIPTED, LICENCE, {'turning_parts': [w.name for w in wheels]})


# -------------------------------------------------------------------------------------- handcart

CART_WHEEL_RADIUS = 0.55


def cart_wheel(name, location):
    """A wooden cart wheel: elm hub with iron hoops, twelve tapered oak spokes, ash felloes, iron tyre."""
    wood = brown_wood()
    m = iron()
    felloe = kit.ring('felloe', 0.47, 0.53, 0.06, material=wood, segments=48)
    tyre = kit.ring('tyre', 0.528, CART_WHEEL_RADIUS, 0.054, material=m, segments=48)
    hub = kit.cylinder('hub', 0.075, 0.20, material=wood, sides=20, bevel=0.01)
    hub_ends = [kit.cylinder('hub-end', 0.075, 0.05, at=(0, 0, side * 0.12), material=wood, sides=20, radius_top=0.05 if side > 0 else None) for side in (-1, 1)]
    hub_ends[0].rotation_euler = (math.pi, 0, 0)
    hoops = [kit.ring('hub-hoop', 0.074, 0.082, 0.02, at=(0, 0, z), material=m, segments=24) for z in (-0.085, 0.085)]
    spokes = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        stagger = 0.02 if k % 2 else -0.02  # spokes set in two staggered rows in the hub
        spokes.append(kit.rod(f'spoke{k}', (0.07 * math.cos(a), 0.07 * math.sin(a), stagger), (0.48 * math.cos(a), 0.48 * math.sin(a), 0.0),
                              0.02, wood, sides=8, radius_end=0.014))
    # tyre bolts through the felloe, and the joints between the six felloe pieces (iron plates)
    bolt_points = [(0.53 * math.cos(2 * math.pi * k / 12 + 0.13), 0.53 * math.sin(2 * math.pi * k / 12 + 0.13), 0.031) for k in range(12)]
    bolts = kit.hex_bolts('tyre-bolts', bolt_points, 0.008, m, normal=(0, 0, 1))
    plates = [kit.box('felloe-plate', (0.012, 0.07, 0.064), (0.50 * math.cos(2 * math.pi * k / 6 + 0.26), 0.50 * math.sin(2 * math.pi * k / 6 + 0.26), 0),
                      m, rotate=(0, 0, 2 * math.pi * k / 6 + 0.26)) for k in range(6)]
    wheel = kit.join('wheel', [felloe, tyre, hub, bolts] + hub_ends + hoops + spokes + plates)
    wheel.rotation_euler = (math.pi / 2, 0, 0)
    return wheel_ready(wheel, location, name)


def handcart():
    kit.reset()
    parts = []
    wood, frame_wood, m = grey_wood(), brown_wood(), iron()
    floor_z, bed_length, bed_width = 0.66, 1.5, 0.86
    axle_z = CART_WHEEL_RADIUS
    # long side frames that carry on forward as the shafts, tapering to round handles
    for y in (-0.40, 0.40):
        parts.append(kit.box('frame', (bed_length + 0.04, 0.07, 0.08), (0, y, floor_z - 0.055), frame_wood, bevel=0.008))
        parts.append(kit.rod('shaft', (bed_length / 2, y, floor_z - 0.055), (bed_length / 2 + 0.75, y * 0.82, floor_z - 0.04), 0.034, frame_wood, sides=10, radius_end=0.022))
    parts.append(kit.rod('handle-bar', (bed_length / 2 + 0.70, -0.36, floor_z - 0.04), (bed_length / 2 + 0.70, 0.36, floor_z - 0.04), 0.02, frame_wood, sides=10))
    # cross bearers under the floor and the axle-tree
    for x in (-0.65, 0.0, 0.65):
        parts.append(kit.box('bearer', (0.07, bed_width + 0.04, 0.06), (x, 0, floor_z - 0.12), frame_wood, bevel=0.006))
    parts.append(kit.box('axle-tree', (0.09, 1.04, 0.08), (0, 0, axle_z + 0.05), frame_wood, bevel=0.008))
    parts.append(kit.rod('axle', (0, -0.66, axle_z), (0, 0.66, axle_z), 0.028, m, sides=12))
    for y in (-0.40, 0.40):
        parts.append(kit.box('axle-strap', (0.11, 0.075, 0.012), (0, y, axle_z + 0.095), m, bevel=0.002))
        parts.append(kit.box('spring-block', (0.10, 0.07, 0.04), (0, y, axle_z + 0.1 + 0.03 - 0.03), frame_wood))
    # floor of five planks with gaps
    plank_width, gap = 0.165, 0.009
    for k in range(5):
        y = -bed_width / 2 + plank_width / 2 + k * (plank_width + gap)
        parts.append(kit.box('floor-plank', (bed_length, plank_width, 0.028), (0, y, floor_z), wood, bevel=0.004))
    # sides: two boards each side on four stakes, a front board and a drop tailboard with chains
    side_top = floor_z + 0.32
    for y in (-bed_width / 2 - 0.02, bed_width / 2 + 0.02):
        for row in range(2):
            parts.append(kit.box('side-board', (bed_length, 0.025, 0.14), (0, y, floor_z + 0.09 + row * 0.15), wood, bevel=0.004))
        for x in (-0.72, -0.25, 0.25, 0.72):
            parts.append(kit.box('stake', (0.05, 0.045, 0.40), (x, y + math.copysign(0.03, y), floor_z + 0.12), frame_wood, bevel=0.006))
        parts.append(kit.box('top-rail-iron', (bed_length + 0.02, 0.03, 0.008), (0, y, side_top - 0.005), m))
        bolt_points = [(x, y + math.copysign(0.055, y), floor_z + z) for x in (-0.72, -0.25, 0.25, 0.72) for z in (0.06, 0.24)]
        parts.append(kit.hex_bolts('stake-bolts', bolt_points, 0.009, m, normal=(0, math.copysign(1, y), 0)))
    for x, name in ((bed_length / 2 + 0.01, 'front-board'), (-bed_length / 2 - 0.01, 'tail-board')):
        for row in range(2):
            parts.append(kit.box(name, (0.025, bed_width + 0.06, 0.14), (x, 0, floor_z + 0.09 + row * 0.15), wood, bevel=0.004))
        parts.append(kit.box('end-strap', (0.008, 0.05, 0.30), (x + math.copysign(0.016, x), -0.30, floor_z + 0.165), m))
        parts.append(kit.box('end-strap', (0.008, 0.05, 0.30), (x + math.copysign(0.016, x), 0.30, floor_z + 0.165), m))
    # iron corner plates with bolts at the four top corners
    for x in (-bed_length / 2, bed_length / 2):
        for y in (-bed_width / 2 - 0.02, bed_width / 2 + 0.02):
            parts.append(kit.box('corner-plate', (0.14, 0.006, 0.12), (x - math.copysign(0.05, x), y + math.copysign(0.016, y), side_top - 0.07), m, bevel=0.002))
    # a prop leg under the shafts so the cart stands level
    for y in (-0.36, 0.36):
        parts.append(kit.rod('prop-leg', (bed_length / 2 + 0.35, y * 0.9, floor_z - 0.09), (bed_length / 2 + 0.42, y * 0.9, 0.0), 0.022, frame_wood, sides=8))
    # a few lumps of coal left in the corner of the bed and a folded empty sack
    originals = [kit.lump(f'cart-lump{i}', 1.0, 300 + i, coal()) for i in range(5)]
    rng = random.Random(8)
    placements = [((rng.uniform(-0.70, -0.45), rng.uniform(-0.38, 0.38), floor_z + 0.03), Euler((0, 0, rng.uniform(0, 6))), rng.uniform(0.03, 0.06)) for _ in range(14)]
    parts.append(kit.scatter_copies('left-coal', originals, placements, coal()))
    for o in originals: kit.remove(o)
    sack = kit.box('folded-sack', (0.45, 0.35, 0.03), (0.35, 0.1, floor_z + 0.03), sack_material('sack-plain', 'hessian-plain'), bevel=0.012, rotate=(0, 0, 0.3))
    parts.append(sack)
    kit.join('cart-body', parts)
    wheels = [cart_wheel('wheel_left', (0, -0.58, axle_z)), cart_wheel('wheel_right', (0, 0.58, axle_z))]
    library.stand_on_ground('handcart', keep_names=[w.name for w in wheels])
    library.save_prop('handcart', "coal merchant's two-wheeled handcart: 1.1 m spoked wooden wheels with iron tyres, plank bed with side boards on stakes, iron straps and bolts, shafts with handle bar, prop legs, a little coal and an empty sack in the bed; wheel_left / wheel_right turn about their axle",
                      SCRIPTED, LICENCE, {'turning_parts': [w.name for w in wheels]})


# ----------------------------------------------------------------------------------------- sacks

def sack_material(picture, name):
    return kit.picture_material(name, f'{picture}.jpg', normal_file='sack-normal.png', roughness=0.95, tile_metres=0.9)


def sack_lying(name, length, width, height, seed, material, marked=False):
    """A filled sack lying on its side: a soft pillow, lumpy with coal, its mouth end folded under."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=9, use_grid_fill=True)
    for v in bm.verts:
        x, y, z = v.co
        # round the box into a pillow
        v.co = Vector((x * (1 - 0.18 * (y * y + z * z) / 2), y * (1 - 0.30 * z * z) * (1 - 0.15 * x * x), z * (1 - 0.35 * y * y) * (1 - 0.2 * x * x)))
        # the mouth end (x > 0.5) is flattened and folded
        if x > 0.5:
            fold = (x - 0.5) / 0.5
            v.co.z *= 1 - 0.55 * fold
            v.co.y *= 1 - 0.15 * fold
        v.co.x *= length / 2; v.co.y *= width / 2; v.co.z *= height / 2
        v.co.z += height / 2 * 0.95
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    # lumpy contents
    texture = bpy.data.textures.new(f'{name}-lumps', 'VORONOI'); texture.noise_scale = 0.07
    push = obj.modifiers.new('lumps', 'DISPLACE'); push.texture = texture; push.strength = 0.022; push.mid_level = 0.5
    texture2 = bpy.data.textures.new(f'{name}-sag', 'CLOUDS'); texture2.noise_scale = 0.3
    sag = obj.modifiers.new('sag', 'DISPLACE'); sag.texture = texture2; sag.strength = 0.03
    kit.apply_all(obj)
    for poly in mesh.polygons: poly.use_smooth = True
    # texture: seen from above, the picture runs along the sack's length, so a stencil reads the right way
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            if marked:
                loop[uv].uv = (co.x / (length * 1.05) + 0.5, co.y / (width * 1.25) + 0.5 + co.z * 0.15)
            else:
                loop[uv].uv = (co.x / 0.9 + 0.5, (co.y + co.z) / 0.9)
    bm.to_mesh(obj.data); bm.free()
    return obj


def sack_standing(name, seed, material):
    """A filled sack standing up, its neck gathered and tied with twine."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=18, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        if z < -0.6: z = -0.6 + (z + 0.6) * 0.2  # flat bottom
        squeeze = 1.0
        if z > 0.55:  # gather the top into a neck
            t = (z - 0.55) / 0.45
            squeeze = 1 - 0.85 * t
            z = 0.55 + t * 0.65
        v.co = Vector((x * squeeze * 0.24, y * squeeze * 0.20, (z + 0.6) * 0.30))
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    texture = bpy.data.textures.new(f'{name}-lumps', 'VORONOI'); texture.noise_scale = 0.06
    push = obj.modifiers.new('lumps', 'DISPLACE'); push.texture = texture; push.strength = 0.02
    kit.apply_all(obj)
    for poly in mesh.polygons: poly.use_smooth = True
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            loop[uv].uv = (math.atan2(co.x, -co.y) / (2 * math.pi) * 1.4 + 0.5, co.z / 0.6 + 0.05)
    bm.to_mesh(obj.data); bm.free()
    top = max(v.co.z for v in obj.data.vertices)
    twine = kit.plain_material('twine', (0.42, 0.33, 0.20), roughness=0.9)
    tie = kit.ring(f'{name}-tie', 0.032, 0.042, 0.018, at=(0, 0, top - 0.10), material=twine, segments=16)
    tuft = kit.cylinder(f'{name}-tuft', 0.035, 0.08, at=(0, 0, top - 0.03), material=material, sides=10, radius_top=0.07)
    return [obj, tie, tuft]


def coal_sacks():
    kit.reset()
    plain = sack_material('sack-plain', 'hessian-plain')
    merchant = sack_material('sack-marked-merchant', 'hessian-merchant')
    colliery = sack_material('sack-marked-colliery', 'hessian-colliery')
    parts = []
    # bottom layer: three sacks side by side
    for k, (y, mat, marked) in enumerate(((-0.46, plain, False), (0.0, colliery, True), (0.46, plain, False))):
        sack = sack_lying(f'sack{k}', 0.92, 0.50, 0.30, 10 + k, mat, marked)
        sack.location = (0.02 * k, y, 0); sack.rotation_euler = (0, 0, 0.04 * (k - 1))
        parts.append(sack)
    # top layer: two sacks across the gaps
    for k, (y, mat, marked) in enumerate(((-0.23, merchant, True), (0.24, plain, False))):
        sack = sack_lying(f'sack-top{k}', 0.90, 0.48, 0.28, 20 + k, mat, marked)
        sack.location = (-0.03 + 0.05 * k, y, 0.25); sack.rotation_euler = (0.06 * (1 - 2 * k), 0, math.pi + 0.06 * (k - 0.5))
        parts.append(sack)
    # two standing sacks beside the stack
    parts += [p for p in sack_standing('sack-standing0', 30, plain)]
    for p in parts[-3:]: p.location += Vector((0.62, -0.30, 0))
    standing = sack_standing('sack-standing1', 31, merchant)
    for p in standing: p.location += Vector((0.66, 0.22, 0)); p.rotation_euler.z = 0.5
    parts += standing
    library.stand_on_ground('coal-sacks')
    library.save_prop('coal-sacks', 'stack of filled hessian coal sacks (five lying, two standing tied at the neck); faded stencils "J. HARTWELL COAL MERCHANT ABBOTSCLOUGH 1 CWT." and "A. C. & I. Co. No. 2 PIT BEST HOUSE" (all invented)',
                      SCRIPTED, LICENCE)


# ------------------------------------------------------------------------------------ coal pile

def coal_pile():
    kit.reset()
    radius, height = 1.0, 0.55
    heap, offsets = heap_surface('slack-heap', radius, radius * 0.85, height, 41, slack(), cuts=30)
    lumps = lumps_on_heap('coal-lumps', 300, radius, radius * 0.85, height, offsets, 43, sizes=(0.025, 0.08), spread=1.05)
    library.stand_on_ground('coal-pile')
    library.save_prop('coal-pile', 'heap of coal: about 300 angular lumps on a bed of slack, 2 m across, 0.6 m high', SCRIPTED, LICENCE)


# ---------------------------------------------------------------------------------- safety lamp

def safety_lamp():
    kit.reset()
    b, m = brass(), iron()
    parts = []
    parts.append(kit.cylinder('oil-vessel', 0.036, 0.055, at=(0, 0, 0.0275), material=b, sides=32, bevel=0.003))
    parts.append(kit.cylinder('vessel-foot', 0.038, 0.006, at=(0, 0, 0.003), material=b, sides=32))
    # knurled locking ring: a ring with small ridges
    parts.append(kit.ring('locking-ring', 0.030, 0.040, 0.014, at=(0, 0, 0.062), material=b, segments=40))
    ridge_points = [(0.0405 * math.cos(2 * math.pi * k / 36), 0.0405 * math.sin(2 * math.pi * k / 36), 0.062) for k in range(36)]
    for k, point in enumerate(ridge_points):
        parts.append(kit.box('knurl', (0.003, 0.002, 0.012), point, b, rotate=(0, 0, 2 * math.pi * k / 36)))
    parts.append(kit.cylinder('collar', 0.031, 0.012, at=(0, 0, 0.075), material=b, sides=32, bevel=0.002))
    # wick tube and a small steady flame inside the gauze
    parts.append(kit.cylinder('wick-tube', 0.004, 0.02, at=(0, 0, 0.09), material=b, sides=8))
    flame_material = kit.plain_material('lamp-flame', (1.0, 0.75, 0.35), roughness=1.0, glow=(1.0, 0.62, 0.22), glow_strength=6.0)
    lamp_body = kit.join('lamp-body', parts)
    flame = kit.cylinder('flame', 0.0045, 0.022, at=(0, 0, 0.111), material=flame_material, sides=10, radius_top=0.0005)
    # wire gauze chimney (double at the top, as Davy's was), seen through
    gauze = kit.picture_material('brass-gauze', 'gauze.png', see_through='blend', roughness=0.5, metallic=0.8, double_sided=True)
    chimney = []
    for name, radius, bottom, top in (('gauze', 0.022, 0.081, 0.205), ('gauze-top', 0.025, 0.165, 0.205)):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=28, radius1=radius, radius2=radius, depth=top - bottom)
        mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
        obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
        obj.location = (0, 0, (top + bottom) / 2); obj.data.materials.append(gauze)
        bm = bmesh.new(); bm.from_mesh(mesh)
        uv = bm.loops.layers.uv.new('UVMap')
        for face in bm.faces:
            for loop in face.loops:
                co = loop.vert.co
                loop[uv].uv = (math.atan2(co.y, co.x) * radius / 0.03, co.z / 0.03) if abs(face.normal.z) < 0.5 else (co.x / 0.03, co.y / 0.03)
        bm.to_mesh(mesh); bm.free()
        chimney.append(obj)
    # three pillars, the top plate, the cap and the carrying ring and hook
    frame = []
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        frame.append(kit.rod('pillar', (0.031 * math.cos(a), 0.031 * math.sin(a), 0.08), (0.031 * math.cos(a), 0.031 * math.sin(a), 0.215), 0.0028, m, sides=8))
    frame.append(kit.cylinder('top-plate', 0.036, 0.006, at=(0, 0, 0.215), material=b, sides=32, bevel=0.0015))
    frame.append(kit.cylinder('cap', 0.024, 0.016, at=(0, 0, 0.226), material=b, sides=24, radius_top=0.012))
    frame.append(kit.cylinder('cap-stem', 0.006, 0.014, at=(0, 0, 0.240), material=m, sides=10))
    ring = kit.ring('carry-ring', 0.017, 0.021, 0.004, at=(0, 0, 0.265), material=m, segments=28, rotate=(math.pi / 2, 0, 0))
    frame.append(ring)
    hook = kit.chain_link('hook', (0, 0, 0.292), (math.pi / 2, 0, 0), m, length=0.034, width=0.016, thickness=0.0022)
    frame.append(hook)
    # a stamped brass number tag hanging on the pillar (the miner's lamp number)
    frame.append(kit.cylinder('lamp-tag', 0.009, 0.0012, at=(0.036, 0, 0.17), material=b, sides=14, rotate=(0, math.pi / 2, 0)))
    kit.join('lamp-frame', frame)
    library.stand_on_ground('safety-lamp')
    library.save_prop('safety-lamp', "Davy-style miner's safety lamp: brass oil vessel with knurled locking ring, double brass wire gauze (see-through), three iron pillars, brass cap, carrying ring and hook, small glowing flame (material 'lamp-flame' for the page to flicker)",
                      SCRIPTED, LICENCE)


# --------------------------------------------------------------------------------------- signs

def plank_board(name, width, height, planks, thickness, centre, face_material, back_material, gap=0.005):
    """A board of horizontal planks whose front faces together show one painted picture, the plank
    joints falling where the picture shows them. Sides and back wear plain timber."""
    pieces = []
    plank_height = height / planks
    bottom = centre[2] - height / 2
    for k in range(planks):
        z = bottom + plank_height * (k + 0.5)
        plank = kit.box(f'{name}-plank{k}', (width, thickness, plank_height - gap), (centre[0], centre[1], z), back_material, bevel=0.003)
        plank.data.materials.append(face_material)
        bm = bmesh.new(); bm.from_mesh(plank.data)
        uv = bm.loops.layers.uv.get('UVMap')
        for face in bm.faces:
            if face.normal.y < -0.9:
                face.material_index = 1
                for loop in face.loops:
                    world = plank.matrix_world @ loop.vert.co
                    loop[uv].uv = ((world.x - centre[0]) / width + 0.5, (world.z - bottom) / height)
        bm.to_mesh(plank.data); bm.free()
        pieces.append(plank)
    return pieces


def colliery_name_board():
    kit.reset()
    board_material = kit.picture_material('colliery-board-paint', 'colliery-board.jpg', roughness=0.75)
    wood, post_wood, m = grey_wood(), rough_wood(), black_iron()
    width, height, centre_z = 2.4, 1.2, 3.55
    parts = plank_board('board', width, height, 6, 0.035, (0, 0, centre_z), board_material, wood)
    for x in (-0.8, 0.0, 0.8):
        parts.append(kit.box('batten', (0.09, 0.035, height - 0.04), (x, 0.035, centre_z), wood, bevel=0.005))
    # iron straps over the board ends, a bolt through every plank
    for x in (-1.10, 1.10):
        parts.append(kit.box('strap', (0.045, 0.007, height + 0.02), (x, -0.021, centre_z), m, bevel=0.0015))
        parts.append(kit.hex_bolts('strap-bolts', [(x, -0.025, centre_z - height / 2 + height / 6 * (k + 0.5)) for k in range(6)], 0.011, m))
    # two square posts with weathered caps, and forged brackets tying the board to them
    posts = []
    for x in (-1.33, 1.33):
        posts.append(kit.box('post', (0.18, 0.18, 4.35), (x, 0.02, 4.35 / 2), post_wood, bevel=0.012))
        posts.append(kit.cylinder('post-cap', 0.13, 0.08, at=(x, 0.02, 4.39), material=post_wood, sides=4, radius_top=0.02, rotate=(0, 0, math.pi / 4), smooth=False))
        for z in (centre_z - 0.40, centre_z + 0.40):
            side = 1 if x > 0 else -1
            posts.append(kit.box('bracket', (0.30, 0.012, 0.05), (x - side * 0.14, -0.026, z), m, bevel=0.002))
            posts.append(kit.box('bracket-wrap', (0.012, 0.20, 0.05), (x + side * 0.096, 0.02, z), m))
            posts.append(kit.hex_bolts('bracket-bolts', [(x - side * 0.24, -0.033, z), (x, -0.08, z)], 0.012, m))
        # the bottom of the post tarred against the wet
        posts.append(kit.box('post-tar', (0.186, 0.186, 0.45), (x, 0.02, 0.225), kit.surface_material('tarred-wood', 'black_painted_planks', 1.0)))
    kit.join('name-board', parts)
    kit.join('posts', posts)
    library.stand_on_ground('colliery-name-board')
    library.save_prop('colliery-name-board', 'painted colliery name board "ABBOTSCLOUGH COLLIERY / ABBOTSCLOUGH COAL & IRON COMPANY, LIMITED / No. 2 PIT" (invented): sign-writer lettering shaded in red on chipped green paint over six weathered planks, iron straps and bolts, on two 4.35 m posts with forged brackets; board 2.4 x 1.2 m centred 3.55 m up (object "posts" can be hidden to hang the board elsewhere)',
                      SCRIPTED, LICENCE, {'lettering': ['ABBOTSCLOUGH', 'COLLIERY', 'ABBOTSCLOUGH COAL & IRON COMPANY, LIMITED', 'No. 2 PIT'], 'texture': 'colliery-board 2048x1024'})


NOTICE_WIDTH, NOTICE_HEIGHT = 0.50, 0.70
TACK_PIXELS = ((100, 100), (1420, 300), (1312, 1898), (330, 1878))   # the same places as the rust runs in paint_prop_pictures.py


def notice_sheet(centre, material):
    """The notice paper: a softly wavy sheet (paste bubbles), facing -y, with its four tacks."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=10, y_segments=14, size=0.5)
    uv = bm.loops.layers.uv.new('UVMap')
    rng = random.Random(4)
    bumps = [(rng.uniform(-0.2, 0.2), rng.uniform(-0.3, 0.3), rng.uniform(0.002, 0.005)) for _ in range(6)]
    for v in bm.verts:
        u, w = v.co.x + 0.5, v.co.y + 0.5
        x, z = (u - 0.5) * NOTICE_WIDTH, (w - 0.5) * NOTICE_HEIGHT
        depth = sum(a * math.exp(-((x - bx) ** 2 + (z - bz) ** 2) / 0.006) for bx, bz, a in bumps)
        v.co = Vector((x, -depth, z))
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            loop[uv].uv = (co.x / NOTICE_WIDTH + 0.5, co.z / NOTICE_HEIGHT + 0.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for face in bm.faces:
        if face.normal.y > 0: face.normal_flip()
    mesh = bpy.data.meshes.new('notice'); bm.to_mesh(mesh); bm.free()
    paper = bpy.data.objects.new('notice', mesh); bpy.context.scene.collection.objects.link(paper)
    paper.location = centre; paper.data.materials.append(material)
    for poly in mesh.polygons: poly.use_smooth = True
    tacks = [((px / 1462 - 0.5) * NOTICE_WIDTH + centre[0], centre[1] - 0.002, (0.5 - py / 2048) * NOTICE_HEIGHT + centre[2]) for px, py in TACK_PIXELS]
    tack_heads = kit.studs('tacks', tacks, 0.007, iron(), height_ratio=0.35)
    return paper, tack_heads


def notice_material():
    return kit.picture_material('notice-paper', 'notice.png', see_through=True, roughness=0.9)


NOTICE_TEXT = 'ABBOTSCLOUGH COAL & IRON COMPANY, LTD. / NOTICE / TO ALL WORKMEN / Owing to the cessation of the Government Subsidy, the present Contracts of Service will terminate on FRIDAY, 30th APRIL, 1926, and these PITS WILL BE CLOSED from SATURDAY, 1st MAY, 1926, until the Workmen are prepared to accept the NEW TERMS now offered by the Owners ... By Order, T. H. WARBRECK, Agent. (all names invented)'


def notice_paper():
    kit.reset()
    notice_sheet((0, 0, NOTICE_HEIGHT / 2), notice_material())
    library.stand_on_ground('notice-paper')
    library.save_prop('notice-paper', 'printed lock-out notice on weathered, foxed, rust-stained paper with two torn corners (see-through), held by four tacks; 0.5 x 0.7 m; paste it on any wall (front faces -y in Blender, +z in three.js)',
                      SCRIPTED, LICENCE, {'text': NOTICE_TEXT, 'texture': 'notice 1462x2048 with transparency'})


def notice_on_board():
    kit.reset()
    painted = kit.surface_material('black-boards', 'black_painted_planks', 0.8)
    wood = grey_wood()
    width, height, centre_z = 0.72, 0.98, 0.49
    parts = []
    # a black backing behind the boards, so no light shows through the gaps between them
    parts.append(kit.box('backing', (width, 0.008, height), (0, 0.016, centre_z), painted))
    # vertical tongue-and-groove boards
    for k in range(6):
        x = -width / 2 + width / 12 + k * width / 6
        parts.append(kit.box('board', (width / 6 - 0.006, 0.022, height), (x, 0.0, centre_z), painted, bevel=0.003))
    # a moulded frame and a sloping rain hood on two shaped cheeks
    for z in (centre_z - height / 2 - 0.02, centre_z + height / 2 + 0.02):
        parts.append(kit.box('frame', (width + 0.08, 0.04, 0.05), (0, -0.012, z), wood, bevel=0.006))
    for x in (-width / 2 - 0.02, width / 2 + 0.02):
        parts.append(kit.box('frame', (0.05, 0.04, height + 0.09), (x, -0.012, centre_z), wood, bevel=0.006))
    hood_z = centre_z + height / 2 + 0.08
    parts.append(kit.box('hood', (width + 0.16, 0.20, 0.025), (0, -0.07, hood_z + 0.03), wood, bevel=0.004, rotate=(-0.30, 0, 0)))
    for x in (-width / 2 - 0.05, width / 2 + 0.05):
        parts.append(kit.box('hood-cheek', (0.025, 0.16, 0.10), (x, -0.06, hood_z - 0.01), wood, bevel=0.004))
    kit.join('notice-board', parts)
    notice_sheet((0.0, -0.014, centre_z - 0.03), notice_material())
    library.stand_on_ground('notice-on-board')
    library.save_prop('notice-on-board', 'the printed lock-out notice pasted on a black-painted notice board (vertical boards, timber frame, sloping rain hood); 0.88 x 1.17 m; hang on a wall or post',
                      SCRIPTED, LICENCE, {'text': NOTICE_TEXT})


BUILDERS = {
    'coal-tub': coal_tub, 'narrow-gauge-track': narrow_gauge_track, 'coal-tub-on-track': coal_tub_on_track,
    'handcart': handcart, 'coal-sacks': coal_sacks, 'coal-pile': coal_pile, 'safety-lamp': safety_lamp,
    'colliery-name-board': colliery_name_board, 'notice-paper': notice_paper, 'notice-on-board': notice_on_board,
}

if __name__ == '__main__':
    wanted = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(BUILDERS)
    for name in wanted:
        BUILDERS[name]()
