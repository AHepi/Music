"""
ore_car: a small side-tipping mine wagon (a "V-skip") for two-foot track: a V-shaped steel body whose end plates are
curved underneath into rockers, resting in crescent cradles on a channel-iron frame, so it can be rocked over to tip
its load to either side. Four flanged wheels on two axles in outside axle boxes, timber buffers, a coupling link at
each end, a latch at the front holding the body upright, grab handles on the end plates. Dented and rusty.

Options:
    loaded     True (default): heaped with broken ore; False: empty.
    on_rails   False (default): standing on its flanges on plain ground at the foot. True: built standing on the store's
               rails part, wheels 0.18 m up on the rail tops, so a car and a piece of track placed at the same point fit.

The track runs along Y, so the car's ends face -Y and +Y.

Where it came from: "46 desert-mine - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
mine_car() (line 1058): an open hopper box on plain discs; rebuilt here as a whole V-skip with a frame, wheels, rockers
and load, at real size.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_town as shapes  # noqa: E402

RUST = 'RUST • rain-aged iron'

CARD = {
    'name': 'ore_car',
    'what': 'a small side-tipping mine wagon (V-skip) on four flanged wheels for two-foot track; ends face -Y and +Y',
    'size_m': (1.08, 1.75, 1.25),
    'options': {
        'loaded': 'True (default): heaped with broken ore; False: empty',
        'on_rails': 'False (default): wheels on plain ground at the foot; True: wheels 0.18 m up, standing on the rails part placed at the same point',
    },
    'materials': ['SURFACE • rusty_metal_02 (ore_car)', RUST, 'SURFACE • rough_wood (ore_car)', 'PART • ore_car: broken ore'],
    'source': '"46 desert-mine - render_final.py", mine_car() (line 1058); builder\'s report "46 Desert mine builder\'s report.md"',
    'views': 'reads from every side',
    'trap': 'on the rails part, place it at the same point with on_rails=True, or its wheels sink into the rails',
}

TREAD_R = 0.150
FLANGE_R = 0.168
AXLE_Y = 0.30
WHEEL_PROFILE = [      # (radius, distance out from the middle of the axle) for the right-hand wheel; the flange is inboard
    (0.000, 0.262), (0.040, 0.262), (0.042, 0.272), (0.060, 0.278), (0.120, 0.281), (0.150, 0.283),
    (0.163, 0.285), (0.168, 0.290), (0.166, 0.296), (0.156, 0.300), (0.151, 0.304), (0.149, 0.356),
    (0.144, 0.362), (0.128, 0.364), (0.118, 0.357), (0.064, 0.351), (0.052, 0.360), (0.047, 0.384),
    (0.034, 0.392), (0.000, 0.392),
]


def _ore(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    big = shapes.noise_fac(nodes, links, vec, 6.0, detail=3.0)
    fine = shapes.noise_fac(nodes, links, vec, 38.0, detail=6.0, roughness=0.65)
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.inputs['Scale'].default_value = 22.0
    links.new(vec, voronoi.inputs['Vector'])
    stone = voronoi.outputs['Color']
    grey = shapes.mix_colour(nodes, links, fine, (0.040, 0.037, 0.034), (0.085, 0.078, 0.068))
    oxide = shapes.mix_colour(nodes, links, fine, (0.070, 0.036, 0.018), (0.120, 0.060, 0.026))
    sep = nodes.new('ShaderNodeSeparateColor')
    links.new(stone, sep.inputs['Color'])
    pick = shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'ADD', sep.outputs['Red'],
                                                             shapes.math_node(nodes, links, 'MULTIPLY', big, 0.4)), 0.78, 0.86)
    colour = shapes.mix_colour(nodes, links, pick, grey, oxide)
    links.new(colour, principled.inputs['Base Color'])
    links.new(shapes.map_range(nodes, links, fine, 0.0, 1.0, 0.72, 0.95), principled.inputs['Roughness'])
    links.new(shapes.bump(nodes, links, fine, 0.45, 0.004), principled.inputs['Normal'])
    m.diffuse_color = (0.06, 0.05, 0.045, 1.0)


def _wheel(shape, x_sign, y, axle_z):
    r = shapes.frame_along((x_sign, 0.0, 0.0))
    m = shapes.to4(r, (0.0, y, axle_z))
    shape.lathe(WHEEL_PROFILE, segments=36, matrix=m)
    # cast ribs across the dished web, outboard
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        inner = Vector((x_sign * 0.356, y + 0.060 * math.cos(a), axle_z + 0.060 * math.sin(a)))
        outer = Vector((x_sign * 0.356, y + 0.118 * math.cos(a), axle_z + 0.118 * math.sin(a)))
        shape.beam(inner, outer, 0.012, 0.012, up=(x_sign, 0.0, 0.0))


def _channel(shape, a, b, height, flange, inward, thick=0.007, up=(0.0, 0.0, 1.0)):
    """A channel iron from a to b: a web `height` tall with top and bottom flanges `flange` wide towards `inward`."""
    a, b = Vector(a), Vector(b)
    w = Vector(inward).normalized()
    shape.beam(a, b, thick, height, up=up)
    for s in (-1, 1):
        off = Vector((0.0, 0.0, s * (height / 2 - thick / 2))) + w * (flange / 2 - thick / 2)
        shape.beam(a + off, b + off, flange, thick, up=up)


def build(collection, seed=0, loaded=True, on_rails=False):
    rng = shapes.rng_for('ore_car', seed)
    objects = []
    zc = shapes.RAIL_TOP if on_rails else FLANGE_R - TREAD_R     # where the treads touch
    axle_z = zc + TREAD_R
    frame_low, frame_high = axle_z + 0.060, axle_z + 0.160
    rocker_r = 0.42
    rocker_low = frame_high + 0.040
    rocker_c = rocker_low + rocker_r
    top = zc + 1.00
    half_top = 0.52
    vee_low = rocker_low + 0.004
    body_half = 0.598

    # ------------------------------------------------------------------ running gear: wheels, axles, boxes (rusty iron)
    gear = shapes.Shape()
    for y in (-AXLE_Y, AXLE_Y):
        for s in (-1, 1):
            _wheel(gear, s, y, axle_z)
            # axle box hanging under the frame, its cover and bolts
            gear.box((s * 0.432, y, axle_z + 0.004), (0.058, 0.118, 0.112))
            gear.box((s * 0.466, y, axle_z), (0.012, 0.090, 0.086))
            for (dy, dz) in ((-0.032, -0.030), (0.032, -0.030), (-0.032, 0.030), (0.032, 0.030)):
                gear.cylinder((s * 0.470, y + dy, axle_z + dz), (s * 0.478, y + dy, axle_z + dz), 0.007, segments=6)
        gear.cylinder((-0.41, y, axle_z), (0.41, y, axle_z), 0.028, segments=14)
    objects.append(gear.finish('ore_car wheels and axles', collection, RUST, smooth=True, sharp=38))

    # ------------------------------------------------------------------ frame: channel irons, cradles, couplings, latch
    frame = shapes.Shape()
    frame_mid = (frame_low + frame_high) / 2
    height = frame_high - frame_low
    for s in (-1, 1):
        _channel(frame, (s * 0.432, -0.70, frame_mid), (s * 0.432, 0.70, frame_mid), height, 0.050, (-s, 0.0, 0.0))
    for s in (-1, 1):
        _channel(frame, (-0.47, s * 0.700, frame_mid), (0.47, s * 0.700, frame_mid), height, 0.050, (0.0, -s, 0.0))
        # the bearer under each cradle
        frame.box((0.0, s * 0.620, frame_high - 0.006), (0.86, 0.060, 0.012))
        # the cradle: a crescent plate whose top is the rocker's circle
        outline = [(-0.40, frame_high)]
        for k in range(25):
            x = -0.40 + 0.80 * k / 24
            outline.append((x, rocker_c - math.sqrt(max(0.0, (rocker_r + 0.002) ** 2 - x * x))))
        outline.append((0.40, frame_high))
        m = Matrix.Translation((0.0, s * 0.620, 0.0)) @ Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()
        frame.prism(list(reversed(outline)) if s < 0 else outline, -0.011, 0.011, m)
        # gusset strips stiffening the cradle's horns
        for sx in (-1, 1):
            frame.beam((sx * 0.37, s * 0.632, frame_high), (sx * 0.37, s * 0.632, rocker_c - math.sqrt(rocker_r ** 2 - 0.37 ** 2) - 0.004),
                       0.030, 0.008)
        # coupling: a plate bolted on the buffer's face and a hook turned up from it
        frame.box((0.0, s * 0.791, frame_mid + 0.01), (0.11, 0.018, 0.10))
        for sx in (-1, 1):
            for sz in (-1, 1):
                frame.cylinder((sx * 0.038, s * 0.799, frame_mid + 0.01 + sz * 0.032), (sx * 0.038, s * 0.806, frame_mid + 0.01 + sz * 0.032),
                               0.008, segments=6)
        hook = [(0.0, s * 0.798, frame_mid), (0.0, s * 0.835, frame_mid - 0.004), (0.0, s * 0.858, frame_mid + 0.012),
                (0.0, s * 0.862, frame_mid + 0.040)]
        frame.sweep(hook, 0.012, sides=8)
    # the latch at the front: a lever pivoted on the end beam, hooked over a lug on the end plate
    lug_z = rocker_c - rocker_r * math.cos(math.radians(38))
    lug_x = rocker_r * math.sin(math.radians(38))
    frame.cylinder((lug_x - 0.02, -0.67, frame_high + 0.02), (lug_x + 0.02, -0.67, frame_high + 0.02), 0.014, segments=10)
    frame.beam((lug_x, -0.672, frame_high + 0.02), (lug_x - 0.01, -0.650, lug_z + 0.055), 0.020, 0.012, up=(0.0, -1.0, 0.0))
    frame.box((lug_x - 0.012, -0.645, lug_z + 0.058), (0.030, 0.026, 0.016))
    objects.append(frame.finish('ore_car frame', collection, RUST, smooth=False))

    # ------------------------------------------------------------------ timber buffers on the end beams
    wood = shapes.surface_copy('rough_wood', 'ore_car', Grime=0.6, Darken=0.55)
    for s in (-1, 1):
        objects.append(shapes.timber(collection, 'ore_car buffer %s' % ('front' if s < 0 else 'back'),
                                     (-0.30, s * 0.705 + s * 0.040, frame_mid + 0.01), (0.30, s * 0.705 + s * 0.040, frame_mid + 0.01),
                                     0.075, 0.150, wood, rng=rng, chamfer=0.012))

    # ------------------------------------------------------------------ the body: a V of steel sheet, end plates, rockers
    body_mat = shapes.surface_copy('rusty_metal_02', 'ore_car', Darken=0.17, Grime=0.6, Bump=0.5)
    body = shapes.Shape()
    # the V section, outside surface from the top left round the bottom to the top right
    bottom_r = 0.11
    side_angle = math.atan2(top - vee_low - bottom_r, half_top)
    arc = []
    for k in range(9):
        a = -math.pi / 2 - side_angle + 2 * side_angle * k / 8
        arc.append((bottom_r * math.cos(a), vee_low + bottom_r + bottom_r * math.sin(a)))
    vee = []
    for k in range(7):                       # the left side, top corner down to the curve (points for the dents)
        t = k / 7
        vee.append((-half_top + (arc[0][0] + half_top) * t, top + (arc[0][1] - top) * t))
    vee += arc
    for k in range(1, 8):                    # the right side, up to the top corner
        t = k / 7
        vee.append((arc[-1][0] + (half_top - arc[-1][0]) * t, arc[-1][1] + (top - arc[-1][1]) * t))
    thick = 0.006
    inner = []
    for (x, z) in vee:
        d = Vector((0.0 - x, 0.0, (top + vee_low) * 0.62 - z))
        d.normalize()
        inner.append((x + d.x * thick, z + d.z * thick))
    section = vee + list(reversed(inner))
    path = [(0.0, -body_half + 2 * body_half * k / 20, 0.0) for k in range(21)]
    body.sweep(path, 1.0, section=[(x, z) for (x, z) in section], up=(0.0, 0.0, 1.0))
    # dents knocked into the sides
    for _ in range(rng.randint(3, 5)):
        side = rng.choice((-1, 1))
        dz = rng.uniform(vee_low + 0.20, top - 0.10)
        frac = (dz - vee_low) / (top - vee_low)
        cx = side * half_top * frac
        cy = rng.uniform(-0.45, 0.45)
        radius = rng.uniform(0.07, 0.15)
        depth = rng.uniform(0.008, 0.022)
        centre = Vector((cx, cy, dz))
        for v in body.bm.verts:
            dist = (v.co - centre).length
            if dist < radius:
                w = (1.0 - (dist / radius) ** 2) ** 2
                inward = Vector((-v.co.x, 0.0, (top + vee_low) * 0.62 - v.co.z)).normalized()
                v.co += inward * depth * w
    # the end plates: the V widened underneath into the rocker's curve
    for s in (-1, 1):
        plate = [(-half_top - 0.012, top + 0.012)]
        start = math.radians(-58)
        for k in range(21):
            a = start + (-2 * start) * k / 20
            plate.append((rocker_r * math.sin(a), rocker_c - rocker_r * math.cos(a)))
        plate.append((half_top + 0.012, top + 0.012))
        m = Matrix.Translation((0.0, s * (body_half + 0.004), 0.0)) @ Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()
        body.prism(plate, -0.004, 0.004, m)
        # the rocker: a heavy curved bar along the bottom of the end plate
        arc = []
        for k in range(21):
            a = start + (-2 * start) * k / 20
            arc.append((rocker_r * math.sin(a), rocker_c - rocker_r * math.cos(a)))
        bar = arc + [(x * 0.94, rocker_c - (rocker_c - z) * 0.94) for (x, z) in reversed(arc)]
        m2 = Matrix.Translation((0.0, s * (body_half + 0.020), 0.0)) @ Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0))).to_4x4()
        body.prism(bar, -0.013, 0.013, m2)
        # grab handles at the top corners of the end plate
        for sx in (-1, 1):
            hx = sx * 0.40
            handle = [(hx - 0.06, s * (body_half + 0.008), top - 0.07), (hx - 0.05, s * (body_half + 0.050), top - 0.07),
                      (hx + 0.05, s * (body_half + 0.050), top - 0.07), (hx + 0.06, s * (body_half + 0.008), top - 0.07)]
            body.sweep(handle, 0.009, sides=6)
    # the rolled rim round the top
    for sx in (-1, 1):
        body.cylinder((sx * (half_top + 0.006), -body_half - 0.012, top + 0.006), (sx * (half_top + 0.006), body_half + 0.012, top + 0.006),
                      0.016, segments=10)
    for s in (-1, 1):
        body.cylinder((-half_top - 0.02, s * (body_half + 0.004), top + 0.010), (half_top + 0.02, s * (body_half + 0.004), top + 0.010),
                      0.013, segments=10)
    body_obj = body.finish('ore_car body', collection, body_mat, smooth=True, sharp=50)
    objects.append(body_obj)
    body_parts = [body_obj]

    # ------------------------------------------------------------------ the load: broken ore heaped above the rim
    if loaded:
        ore = shapes.part_material('ore_car', 'broken ore', _ore)
        heap = shapes.Shape()
        nx, ny = 14, 16
        heap_top = rng.uniform(0.16, 0.24)
        peak_x = rng.uniform(-0.12, 0.12)
        peak_y = rng.uniform(-0.15, 0.15)
        grid = []
        for i in range(nx + 1):
            x = -half_top + 0.025 + (2 * half_top - 0.050) * i / nx
            col = []
            for j in range(ny + 1):
                y = -body_half + 0.01 + (2 * body_half - 0.02) * j / ny
                u = (x - peak_x) / half_top
                w = (y - peak_y) / body_half
                h = max(0.0, 1.0 - 0.75 * u * u - 0.6 * w * w)
                z = top - 0.05 + heap_top * h + rng.uniform(-0.012, 0.012)
                if i in (0, nx) or j in (0, ny):
                    z = top - 0.015
                col.append(heap.bm.verts.new((x, y, z)))
            grid.append(col)
        low = [[heap.bm.verts.new((v.co.x * 0.50, v.co.y * 0.97, top - 0.30)) for v in col] for col in grid]
        for i in range(nx):
            for j in range(ny):
                heap._face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
                heap._face([low[i][j + 1], low[i + 1][j + 1], low[i + 1][j], low[i][j]])
        for i in range(nx):
            for j in (0, ny):
                q = [grid[i][j], grid[i + 1][j], low[i + 1][j], low[i][j]]
                heap._face(q if j == 0 else list(reversed(q)))
        for j in range(ny):
            for i in (0, nx):
                q = [grid[i][j + 1], grid[i][j], low[i][j], low[i][j + 1]]
                heap._face(q if i == 0 else list(reversed(q)))
        heap_obj = heap.finish('ore_car load heap', collection, ore, smooth=True, sharp=None)
        objects.append(heap_obj)
        body_parts.append(heap_obj)
        lumps = shapes.Shape()
        for k in range(70):
            r = rng.uniform(0.035, 0.075) if k % 3 else rng.uniform(0.07, 0.11)
            x = rng.uniform(-0.42 + r, 0.42 - r)
            y = rng.uniform(-0.56 + r, 0.56 - r)
            u = (x - peak_x) / half_top
            w = (y - peak_y) / body_half
            h = max(0.0, 1.0 - 0.75 * u * u - 0.6 * w * w)
            z = top - 0.05 + heap_top * h + r * 0.2
            lumps.rock((x, y, z), r, rng, squash=(1.0, 0.85, 0.7))
        lumps_obj = lumps.finish('ore_car load lumps', collection, ore, smooth=False)
        objects.append(lumps_obj)
        body_parts.append(lumps_obj)

    # seeded: the body sits a touch rocked on its cradles
    rock = math.radians(rng.uniform(-1.5, 1.5))
    shapes.tilt_all(body_parts, ry=rock, pivot=(0.0, 0.0, rocker_c))
    return objects
