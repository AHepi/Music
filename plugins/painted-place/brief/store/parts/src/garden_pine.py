"""
garden_pine: a pruned Japanese garden pine (niwaki, a black pine trained for years): a trunk that leans out and curves
back with a flared foot and dark plated bark (the shelf's photographed bark), branches trained out nearly level from it
in a spiral up the trunk, the lower ones longest, each ending in a rounded, flattened pad of needles on top of its outer
part (the cloud pads), with fine branchlets fanning under each pad, and a domed pad on the top. Each pad is a dense
dark heart under brushes of real needles (tufts of fine needles pointing up and out), so its edge is bristly, not a
smooth blob. The trunk's foot is at the origin, z = 0.

Options:
    height   metres from the ground to the top of the top pad (default 3.5)
    pads     how many branches with pads, besides the top one (default 9)
    seed     the trunk's curve, where the branches go, every tuft

Where it came from: '/home/claude/build-57-garden/first pass/render_final.py', the pine (lines 1599-1622): a twisting
trunk of six points with five branches, each pad a short run of the store's hedge; rebuilt here as a trained pine: a
smooth leaning and returning trunk with a flared foot, branches trained level in a spiral, longest low down, pads shaped
as flattened domes over the branch ends with branchlets under them, made of needle tufts over a dark heart instead of
hedge leaves, and the shelf's photographed bark.
"""

import math
import os
import sys

from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import _shapes_garden_plants as plants  # noqa: E402

PART = 'garden_pine'
NEEDLE = [(-0.018, 0.0), (0.018, 0.0), (0.0, 1.0)]        # one needle: 1.0 long, a twentieth as wide at its foot

CARD = {
    'name': PART,
    'what': 'a pruned Japanese garden pine (niwaki): a leaning, returning trunk with dark plated bark (photographed), '
            'branches trained out level in a spiral, each ending in a flattened, rounded pad of needles on top of it '
            '(cloud pads) with branchlets under it, a domed pad on top; each pad a dark heart under bristling needle tufts',
    'size_m': (2.84, 2.51, 3.53),
    'options': {
        'height': 'metres from the ground to the top of the top pad (default 3.5; garden pines are trained from 2 to 6)',
        'pads': 'how many branches with pads, besides the top one (default 9; 4 to 16)',
        'seed': 'the trunk curve, where the branches go and how long they are, every tuft (default 0)',
    },
    'materials': ['SURFACE • bark_willow_02', 'PART • garden_pine: needles', 'PART • garden_pine: needle pad'],
    'source': "'/home/claude/build-57-garden/first pass/render_final.py', the pine (lines 1599-1622)",
    'views': 'reads from every side: the trunk curve and the level pads with sky between them are its shape; from below '
             'the branchlets show under each pad',
    'trap': 'the trunk leans out up to about 0.5 m from its foot and the lowest branches reach 1.4 m out: the part is '
            'not centred on its trunk; its pads are dark green, so set it against the sky, a pale wall or mist, not '
            'against dark trees',
}


def _pad(core, tufts, centre, along, rx, ry, h, rng, tone_base, s):
    """One cloud pad: a lumpy flattened dome (rx along `along`, ry across, h tall; its underside flatter) as the dark
    heart, and needle tufts over its top and sides."""
    along = Vector((along.x, along.y, 0.0)).normalized()
    across = Vector((-along.y, along.x, 0.0))
    seed_vec = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))

    def surface(theta, phi, inset=0.0):
        """A point on the pad's skin: theta round from `along`, phi up from the equator (-pi/2 .. pi/2)."""
        d = Vector((math.cos(phi) * math.cos(theta), math.cos(phi) * math.sin(theta), math.sin(phi)))
        lump = 1.0 + 0.22 * noise.noise(d * 1.7 + seed_vec) + 0.08 * noise.noise(d * 4.0 + seed_vec)
        z = h * (math.sin(phi) if phi > 0 else 0.35 * math.sin(phi))
        r = lump - inset
        return centre + along * (d.x * rx * r) + across * (d.y * ry * r) + Vector((0, 0, z * (lump - inset * 0.5)))

    # the heart: rings from the bottom to the top
    rings = []
    for j in range(9):
        phi = -math.pi / 2 + math.pi * j / 8
        if j == 0 or j == 8:
            rings.append(core._verts([surface(0.0, phi, 0.12)]))
            continue
        rings.append(core._verts([surface(2 * math.pi * k / 18, phi, 0.12) for k in range(18)]))
    core._rings(rings, True, False, False)
    # the needle tufts, spread evenly over the top and sides (a sunflower spiral on the dome)
    count = int(1.7 * math.pi * rx * ry / (0.06 * s) ** 2)
    golden = math.pi * (3.0 - math.sqrt(5.0))
    for k in range(count):
        u = (k + 0.5) / count
        phi = math.asin(1.0 - 1.1 * u) if 1.0 - 1.1 * u > -1 else -math.pi / 2
        if phi < -0.25:
            continue
        theta = k * golden
        base = surface(theta, phi, 0.1)
        top_dir = (surface(theta, phi, -0.05) - surface(theta, phi, 0.1))
        if top_dir.length < 1e-6:
            top_dir = Vector((0, 0, 1))
        direction = (top_dir.normalized() + Vector((0, 0, 0.9))).normalized()
        tone = min(1.0, max(0.0, tone_base + rng.uniform(-0.25, 0.3) + (0.25 if phi > 0.6 else 0.0)))
        if rng.random() < 0.03:
            tone = 0.99                                              # a few brown, dying needles
        needles = rng.randint(9, 13)
        length = rng.uniform(0.085, 0.125) * min(1.3, max(0.8, s))
        side = direction.cross(Vector((0.3, 0.7, 0.1))).normalized()
        for n in range(needles):
            spin = 2 * math.pi * n / needles + rng.uniform(-0.3, 0.3)
            tilt = rng.uniform(0.2, 0.8)
            d = Matrix.Rotation(spin, 3, direction) @ (Matrix.Rotation(tilt, 3, side) @ direction)
            up = d.cross(side)
            if up.length < 1e-6:
                up = Vector((0, 0, 1))
            frame = plants.frame_from(d, up)
            plants.leaf(tufts, base, frame, length * rng.uniform(0.85, 1.1), NEEDLE, tone)


def build(collection, seed=0, height=3.5, pads=9):
    height = barn.number('garden_pine height', height, 1.2, 10.0)
    pads = int(round(barn.number('garden_pine pads', pads, 2, 30)))
    rng = shapes.rng_for(PART, seed)
    s = height / 3.5
    wood = shapes.Shape()
    core = shapes.Shape()
    tufts = shapes.Shape()

    # ------------------------------------------------------------------ the trunk: leaning out, curving back, flared at its foot
    az = rng.uniform(0, 2 * math.pi)
    out = Vector((math.cos(az), math.sin(az), 0.0))
    perp = Vector((-out.y, out.x, 0.0))
    top_z = height - 0.42 * s
    control = [Vector((0, 0, -0.03)),
               out * 0.18 * s + Vector((0, 0, top_z * 0.2)),
               out * 0.48 * s + perp * rng.uniform(-0.12, 0.12) * s + Vector((0, 0, top_z * 0.42)),
               out * 0.38 * s + perp * rng.uniform(-0.12, 0.12) * s + Vector((0, 0, top_z * 0.62)),
               out * 0.08 * s + perp * rng.uniform(-0.1, 0.1) * s + Vector((0, 0, top_z * 0.82)),
               out * 0.12 * s + Vector((0, 0, top_z))]
    trunk = shapes.smooth_path(control, steps=5)
    n = len(trunk)
    r0 = 0.12 * s * rng.uniform(0.9, 1.1)
    radii = []
    for k, p in enumerate(trunk):
        t = k / (n - 1)
        flare = 1.0 + 0.55 * math.exp(-max(p.z, 0.0) / (0.2 * s))
        radii.append(r0 * flare * (1.0 - 0.68 * t))
    plants.tagged(wood, lambda: wood.sweep(trunk, r0, sides=14, radii=radii), piece=rng.random())
    for v in wood.bm.verts:                                      # the foot's tilted first ring cut level just under the ground
        v.co.z = max(v.co.z, -0.03)

    def on_trunk(t):
        f = t * (n - 1)
        k = min(n - 2, int(f))
        return trunk[k].lerp(trunk[k + 1], f - k), radii[k]

    # ------------------------------------------------------------------ the branches, trained level in a spiral up the trunk, each with its pad
    az0 = rng.uniform(0, 2 * math.pi)
    for i in range(pads):
        t = 0.3 + 0.62 * i / max(1, pads - 1) + rng.uniform(-0.03, 0.03)
        base, r_here = on_trunk(min(0.95, t))
        a = az0 + i * math.radians(137.5) + rng.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        # a branch on the side the trunk leans to reaches less far; the far side balances it
        lean_side = d.dot(out)
        length = (1.35 - 0.85 * t) * s * rng.uniform(0.85, 1.15) * (1.0 - 0.25 * lean_side)
        side = Vector((-d.y, d.x, 0.0))
        wiggle = rng.uniform(-0.08, 0.08) * length
        bpts = [base,
                base + d * 0.25 * length + Vector((0, 0, 0.1 * length)),
                base + d * 0.55 * length + side * wiggle + Vector((0, 0, 0.08 * length)),
                base + d * 0.82 * length - side * wiggle * 0.5 + Vector((0, 0, 0.1 * length)),
                base + d * length + Vector((0, 0, 0.14 * length))]
        bpts = shapes.smooth_path(bpts, steps=3)
        rb = max(0.012 * s, r_here * 0.42)
        bradii = [rb + (0.01 * s - rb) * (k / (len(bpts) - 1)) for k in range(len(bpts))]
        plants.tagged(wood, lambda: wood.sweep(bpts, rb, sides=8, radii=bradii), piece=rng.random())
        tip = bpts[-1]
        R = (0.3 + 0.28 * (1.0 - t)) * s * rng.uniform(0.85, 1.15)
        h = R * rng.uniform(0.42, 0.55)
        centre = tip - d * 0.18 * length + Vector((0, 0, h * 0.35))
        # branchlets fanning out under the pad
        for q in range(rng.randint(4, 6)):
            start = bpts[len(bpts) * 2 // 3]
            fan = Matrix.Rotation(rng.uniform(-1.3, 1.3), 3, 'Z') @ d
            end = centre + fan * R * rng.uniform(0.45, 0.8) + Vector((0, 0, -h * 0.25))
            mid = start.lerp(end, 0.5) + Vector((0, 0, 0.04 * s))
            lpts = shapes.smooth_path([start, mid, end], steps=3)
            plants.tagged(wood, lambda: wood.sweep(lpts, 0.008 * s, sides=5,
                                                     radii=[0.009 * s - 0.006 * s * k / (len(lpts) - 1) for k in range(len(lpts))]),
                          piece=rng.random())
        _pad(core, tufts, centre, d, R * 1.12, R * 0.92, h, rng, rng.uniform(0.25, 0.6), s)

    # ------------------------------------------------------------------ the top pad, domed
    top, _ = on_trunk(1.0)
    R = 0.36 * s * rng.uniform(0.9, 1.1)
    _pad(core, tufts, top + Vector((0, 0, 0.12 * s)), out, R, R * 0.95, R * 0.72, rng, rng.uniform(0.35, 0.65), s)

    # ------------------------------------------------------------------ the top exactly at the height asked for
    reach = max(max(v.co.z for v in shape.bm.verts) for shape in (wood, core, tufts))
    if reach > 0.0:
        k = height / reach
        scale = Matrix.Diagonal((k, k, k, 1.0))
        for shape in (wood, core, tufts):
            shape.transform(scale)
    bark = plants.bark(PART, 'plated bark', Scale=0.75, Darken=0.62, Wet=0.5)
    return [wood.finish('garden_pine wood', collection, bark, smooth=True, sharp=None),
            core.finish('garden_pine pad hearts', collection, plants.pad_material(PART), smooth=True, sharp=None),
            tufts.finish('garden_pine needles', collection, plants.needle_material(PART), smooth=False, normals=False)]
