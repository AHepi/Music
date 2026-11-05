"""
bamboo_clump: a clump of living garden bamboo (a Phyllostachys, as grows in groves and beside fences in Japanese
gardens): straight culms rising close together, each leaning a little out from the clump and arching over at the top
under its leaves; nodes all the way up, close together at the foot and longest half way, each with its ridge, a dark
line and a pale waxy band under it; papery sheaths still clasping the lowest nodes of the young culms, split and
peeling; from the upper nodes thin branches in pairs, alternating side node by node, angled up and out, with fans of
narrow leaves hanging from their tips. Green and glossy when young, yellowing and mottled when old, darker at the damp
foot. The clump's middle is at the origin, z = 0.

Options:
    culms    how many culms (default 9)
    height   metres to the top of the tallest culm (default 6.0)
    seed     where each culm stands, its age, lean and nodes, every branch and leaf

Where it came from: '/home/claude/build-57-garden/first pass/render_final.py', the bamboo grove (lines 1500-1526):
culms of short cylinders with a ring at each joint and leaves strewn round the upper joints; rebuilt here as a clump:
culms close together that lean out and arch over, nodes spaced as real culms grow them (short at the foot, longest
half way), node ridges with the waxy band under them, sheaths on the lowest nodes, branches in pairs from the upper
nodes alternating side, leaves in hanging fans at the branch tips, each culm its own age.
"""

import math
import os
import sys

from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import _shapes_garden_plants as plants  # noqa: E402

PART = 'bamboo_clump'
LEAVES = [(0.0, (0.016, 0.042, 0.010)), (0.45, (0.032, 0.075, 0.016)), (0.85, (0.06, 0.10, 0.022)),
          (0.95, (0.17, 0.15, 0.045)), (1.0, (0.22, 0.16, 0.075))]
BLADE = plants.bamboo_outline()

CARD = {
    'name': PART,
    'what': 'a clump of living bamboo: straight culms close together, leaning out a little and arching over at the top; '
            'nodes close at the foot and longest half way, each with a ridge and a pale waxy band; papery sheaths on the '
            'lowest nodes of young culms; thin branches in pairs from the upper nodes; fans of narrow hanging leaves; '
            'green and glossy, the old culms yellowing',
    'size_m': (3.35, 3.67, 5.99),
    'options': {
        'culms': 'how many culms (default 9; 3 for a few canes, 25 for a thicket; the clump widens with them)',
        'height': 'metres to the top of the tallest culm (default 6.0; garden bamboo grows 3 to 10)',
        'seed': 'where each culm stands, its age, lean and nodes, every branch and leaf (default 0)',
    },
    'materials': ['PART • bamboo_clump: culms', 'PART • bamboo_clump: culm sheaths', 'PART • bamboo_clump: leaves'],
    'source': "'/home/claude/build-57-garden/first pass/render_final.py', the bamboo grove (lines 1500-1526)",
    'views': 'reads from every side; the culms and their nodes read near the eye, the leaves as a hanging canopy above '
             'it; seen from a few metres away the top is cut off by a tall frame: its leaves start half way up',
    'trap': 'the culms arch out at the top, so the leafy crown is up to about twice as wide as the clump at the ground; '
            'the culms are 3 to 5 cm thick: in a far, small picture they thin to lines, so set the clump near the eye or '
            'against the sky',
}


def _culm_path(base, out, lean, bow, height, count=24):
    """The culm's middle line: up from its foot, leaning out by `lean` (radians) and arching over by `bow` metres at
    its top."""
    pts = []
    for j in range(count + 1):
        u = j / count
        z = height * u
        offset = math.tan(lean) * z + bow * u ** 3
        pts.append(base + out * offset + Vector((0, 0, z)))
    return pts


def _at(path, z):
    """The point of the path at height z, and its direction there."""
    for j in range(len(path) - 1):
        a, b = path[j], path[j + 1]
        if b.z >= z or j == len(path) - 2:
            f = 0.0 if b.z == a.z else max(0.0, min(1.0, (z - a.z) / (b.z - a.z)))
            return a.lerp(b, f), (b - a).normalized()
    return path[-1], (path[-1] - path[-2]).normalized()


def build(collection, seed=0, culms=9, height=6.0):
    culms = int(round(barn.number('bamboo_clump culms', culms, 1, 60)))
    height = barn.number('bamboo_clump height', height, 1.5, 20.0)
    rng = shapes.rng_for(PART, seed)
    s = height / 6.0
    stems = shapes.Shape()
    sheaths = shapes.Shape()
    foliage = shapes.Shape()
    golden = math.radians(137.5)
    spread = 0.42 * math.sqrt(culms / 9.0) * max(0.6, s ** 0.5)

    def leaf_fan(tip, direction, count, size):
        """A fan of narrow leaves hanging from a branch tip, spread like the fingers of a hand."""
        flat = Vector((direction.x, direction.y, 0.0))
        if flat.length < 1e-4:
            flat = Vector((1.0, 0.0, 0.0))
        flat.normalize()
        side = Vector((-flat.y, flat.x, 0.0))
        for n in range(count):
            spread_a = (n / max(1, count - 1) - 0.5) * math.radians(110) + rng.uniform(-0.15, 0.15)
            hang = math.radians(rng.uniform(25, 65))
            d = (flat * math.cos(spread_a) + side * math.sin(spread_a)) * math.cos(hang) - Vector((0, 0, math.sin(hang)))
            up = Vector((0, 0, 1)) - d * d.z
            frame = plants.frame_from(d, up + side * rng.uniform(-0.4, 0.4))
            tone = 0.92 * rng.random() ** 1.5
            if rng.random() < 0.035:
                tone = rng.uniform(0.95, 1.0)                    # a yellowed, withering leaf
            plants.leaf(foliage, tip + d * 0.005, frame, size * rng.uniform(0.8, 1.15), BLADE, tone, curl=0.18,
                        width=rng.uniform(0.9, 1.2))

    tallest = rng.randrange(culms)
    for i in range(culms):
        r = spread * math.sqrt((i + 0.5) / culms)
        a = i * golden + rng.uniform(-0.3, 0.3)
        base = Vector((math.cos(a) * r, math.sin(a) * r, -0.02))
        out = Vector((math.cos(a), math.sin(a), 0.0)) if r > 0.02 else Vector((1.0, 0.0, 0.0))
        out = (out + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0.0))).normalized()
        age = rng.random() ** 1.7                    # most culms young and green, a few old and yellowing
        tall = height * (1.0 if i == tallest else rng.uniform(0.62, 0.97))
        radius = (0.018 + 0.01 * rng.random()) * max(0.5, s) ** 0.8 * (0.75 + 0.25 * tall / height)
        lean = math.radians(rng.uniform(2.0, 7.0))
        bow = tall * rng.uniform(0.06, 0.16)
        path = _culm_path(base, out, lean, bow, tall)
        # the nodes: close at the foot, longest half way, a little shorter near the top
        nodes = [0.0]
        z = 0.0
        while True:
            u = z / tall
            gap = (0.07 + 0.27 * min(1.0, u / 0.35) - 0.07 * max(0.0, (u - 0.55) / 0.45)) * s * rng.uniform(0.9, 1.1)
            z += max(0.05, gap)
            if z > tall - 0.08 * s:
                break
            nodes.append(z)
        # the culm's skin, ring by ring: a ridge just above each node, the waxy band under it
        ring_z, ring_r, ring_band, ring_ring = [], [], [], []
        for j, nz in enumerate(nodes):
            nxt = nodes[j + 1] if j + 1 < len(nodes) else tall
            taper = 1.0 - 0.62 * (nz / tall) ** 1.3
            r_here = radius * taper
            entries = [(nz, 1.03, 0.6, 1.0), (nz + 0.006, 1.075, 0.0, 0.7), (nz + 0.018, 1.0, 0.0, 0.0),
                       ((nz + nxt) / 2, 0.985, 0.0, 0.0)]
            if nxt - nz > 0.12:
                entries.append((nxt - 0.07, 0.99, 0.0, 0.0))          # the waxy band starts sharply 5 cm under the node
                entries.append((nxt - 0.055, 1.0, 1.0, 0.0))
            entries.append((nxt - 0.006, 1.0, 1.0, 0.0))
            for (zz, f, band, ring) in entries:
                if zz >= tall:
                    continue
                ring_z.append(zz)
                ring_r.append(r_here * f)
                ring_band.append(band)
                ring_ring.append(ring)
        pts = [_at(path, zz)[0] for zz in ring_z]
        first = len(stems.bm.verts)
        plants.tagged(stems, lambda: stems.sweep(pts, radius, sides=10, radii=ring_r), age=lambda co: age)
        # the band and ring numbers, ring by ring (the sweep makes 10 points a ring, in order)
        bm = stems.bm
        bm.verts.ensure_lookup_table()
        band_layer = bm.verts.layers.float.get('band') or bm.verts.layers.float.new('band')
        ring_layer = bm.verts.layers.float.get('ring') or bm.verts.layers.float.new('ring')
        for j in range(len(pts)):
            for q in range(10):
                v = bm.verts[first + j * 10 + q]
                v[band_layer] = ring_band[j]
                v[ring_layer] = ring_ring[j]
        # sheaths still clasping the lowest nodes of the young culms, split down one side, flaring and peeling
        for j in range(min(len(nodes) - 1, 1 + int(4 * (1.0 - age)))):
            nz, nxt = nodes[j], nodes[j + 1]
            top = nz + (nxt - nz) * rng.uniform(0.55, 0.95)
            gap_at = rng.uniform(0, 2 * math.pi)
            peel = rng.uniform(0.0, 0.25) if rng.random() < 0.4 else 0.0
            rings = []
            for h in range(4):
                zz = nz + (top - nz) * h / 3
                centre, _ = _at(path, zz)
                rr = radius * (1.0 - 0.62 * (zz / tall) ** 1.3) * (1.09 + 0.12 * (h / 3) ** 2 + peel * (h / 3) ** 2)
                ring = []
                for q in range(13):
                    ang = gap_at + math.radians(25) + math.radians(310) * q / 12
                    slant = 1.0 - 0.35 * (h / 3) * (0.5 + 0.5 * math.cos(ang - gap_at - math.pi))
                    ring.append(centre + Vector((math.cos(ang) * rr, math.sin(ang) * rr, (zz - centre.z) * 0.0 - (top - nz) * (1.0 - slant) * (h / 3) * 0.6)))
                rings.append(sheaths._verts(ring))
            sheaths._rings(rings, closed_ring=False)
        # branches in pairs from the upper nodes, alternating side node by node, with fans of leaves
        start = tall * rng.uniform(0.34, 0.45)
        branch_nodes = [nz for nz in nodes if nz > start]
        phase = rng.uniform(0, 2 * math.pi)
        for j, nz in enumerate(branch_nodes):
            u = (nz - start) / max(1e-3, tall - start)
            centre, axis = _at(path, nz)
            a_side = phase + math.pi * j + rng.uniform(-0.3, 0.3)
            for b in range(2):
                ab = a_side + (0.0 if b == 0 else rng.uniform(0.35, 0.7))
                horiz = Vector((math.cos(ab), math.sin(ab), 0.0))
                up_angle = math.radians(rng.uniform(38, 55))
                d = (axis * math.cos(up_angle) + horiz * math.sin(up_angle)).normalized()
                blen = (0.35 + 0.65 * math.sin(math.pi * min(1.0, u * 1.1 + 0.1))) * s * (1.0 if b == 0 else 0.6) * rng.uniform(0.8, 1.15)
                b0 = centre + horiz * radius * 0.8
                b1 = b0 + d * blen * 0.5
                b2 = b0 + d * blen + Vector((0, 0, -blen * rng.uniform(0.05, 0.25)))
                bpts = shapes.smooth_path([b0, b1, b2], steps=2)
                rb = max(0.0025, 0.0045 * s ** 0.5)
                plants.tagged(stems, lambda: stems.sweep(bpts, rb, sides=4, radii=[rb, rb * 0.75, rb * 0.6, rb * 0.5, rb * 0.4]),
                              age=lambda co: age)
                size = 0.17 * min(1.25, max(0.8, s ** 0.4))
                leaf_fan(b2, d, rng.randint(5, 8), size)
                leaf_fan(b0.lerp(b2, 0.4), d, rng.randint(3, 5), size * 0.9)
                leaf_fan(b0.lerp(b2, 0.72), d, rng.randint(3, 5), size * 0.95)
                for tw, sd in enumerate((-0.7, 0.7)):
                    if blen < 0.25 * s and tw:
                        break
                    twig_d = (d + horiz.cross(Vector((0, 0, 1))) * sd).normalized()
                    t0 = b0.lerp(b2, rng.uniform(0.45, 0.75))
                    t1 = t0 + twig_d * blen * rng.uniform(0.3, 0.45) + Vector((0, 0, -0.03 * s))
                    plants.tagged(stems, lambda: stems.sweep([t0, t1], rb * 0.5, sides=4), age=lambda co: age)
                    leaf_fan(t1, twig_d, rng.randint(4, 6), size)
        # a last fan at the culm's top
        top_point, top_axis = path[-1], (path[-1] - path[-2]).normalized()
        leaf_fan(top_point, top_axis, rng.randint(4, 6), 0.16 * max(0.8, min(1.25, s ** 0.4)))

    for shape in (stems, sheaths, foliage):
        for v in shape.bm.verts:
            v.co.z = max(v.co.z, -0.02)
    made = [stems.finish('bamboo_clump culms', collection, plants.culm_material(PART), smooth=True, sharp=None)]
    if not sheaths.empty():
        made.append(sheaths.finish('bamboo_clump sheaths', collection, plants.sheath_material(PART), smooth=True, sharp=None, normals=False))
    made.append(foliage.finish('bamboo_clump leaves', collection,
                               plants.leaf_material(PART, 'leaves', LEAVES, veins='pinnate', translucent=0.2, rough=0.5, coat=0.08, specular=0.1,
                                                    vein_light=0.35),
                               smooth=False, normals=False))
    return made
