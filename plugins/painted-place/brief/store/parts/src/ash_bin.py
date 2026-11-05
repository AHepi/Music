"""
ash_bin: a galvanised iron dustbin (ash bin) of about 1900, as a tenement stair carried its ashes down to the kerb in:
a slightly tapering drum with rolled ribs, a rolled rim, two drop handles at the sides (+X, -X), dented; the zinc
gone dull and blotched, rust and soot running down from the rim and the handles, a rust band at the foot where it
stands in the wet. Its domed lid with a strap handle is on it, lying top up on the ground beside it, or stood on its
rim leaning on the bin. Open, it is full of pale stove ash and clinker, heaped over the rim or a hand's breadth under it.

Options:
    lid      'on' (default); 'off': lying top up on the ground at its front right; 'leaning': stood on its rim against
             the bin's front left
    ash      'heaped' (default): ash heaped over the rim, clinker on it; 'low': the ash a hand's breadth under the rim
    seed     the dents, the lid's turn, the heap and the clinker

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', bin_mat() (line 845), ash_bin() (line 919),
heap() (line 985), lumps() (line 1018) and the two bins at the kerb (lines 1030-1064): a closed cone with dents,
ribs, handles, a separate rust ring, a domed lid; ash heaped on top. Rebuilt here as a hollow drum with a rolled rim
(so an open bin shows its mouth and the ash sits in it), the dents bending the ribs and the ash with the wall, drop
handles hanging from lugs, the lid hollow underneath (it shows when it lies or leans), and the clinker sitting on
the ash's own surface.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_street_things as street  # noqa: E402

PART = 'ash_bin'
RUST = 'RUST • rain-aged iron'
ASH = 'MADE • ash'
LIDS = ('on', 'off', 'leaning')
ASHES = ('heaped', 'low')
H, R0, R1 = 0.64, 0.225, 0.245        # height to the rim, radius at the foot and at the rim (the street builder's)

CARD = {
    'name': PART,
    'what': 'a galvanised iron ash bin: a ribbed, dented drum with drop handles and a domed lid, the zinc dull, rust and soot '
            'running down from the rim, rust at the foot; lid on, off on the ground, or leaning on it; open, heaped with pale ash and clinker',
    'size_m': (0.57, 0.53, 0.75),
    'options': {
        'lid': "'on' (default): the lid on; 'off': lying top up on the ground at its front right; 'leaning': stood on its rim, "
               "leaning on the bin's front left",
        'ash': "'heaped' (default): pale ash heaped over the rim, clinker on it (with the lid on, pressed down under it); 'low': "
               "the ash a hand's breadth under the rim (the ash shows only when the lid is off or leaning)",
        'seed': "the dents, the lid's turn, the heap and the clinker (default 0)",
    },
    'materials': ['PART • ash_bin: galvanised iron, dull, rust and soot runs', 'PART • ash_bin: dull galvanised steel', RUST, ASH,
                  'PART • ash_bin: clinker'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', bin_mat() (line 845), ash_bin() (line 919), heap() (line 985), "
              "lumps() (line 1018) and the two bins at the kerb (lines 1030-1064)",
    'views': 'reads from every side; the handles are at the sides (+X, -X)',
    'trap': "an open bin's lid takes ground beside it: 'off' it lies at the front right, reaching 0.69 m to the right (+X) and 0.62 m "
            "in front (-Y) of the bin's middle; 'leaning' it stands at the front left, 0.5 m out; leave it that room or turn the part",
}


def _radius(z):
    return R0 + (R1 - R0) * z / H


def _denter(rng):
    """The bin's dents: a few patches of the wall pushed in; returns a function that moves a point (the wall, its
    ribs and the ash inside all follow it, so nothing pokes through)."""
    dents = [(rng.uniform(0, 2 * math.pi), rng.uniform(0.12, 0.55), rng.uniform(0.016, 0.034)) for _ in range(5)]

    def dent(co):
        rr = math.hypot(co.x, co.y)
        if rr < 0.1 or co.z > H + 0.01:
            return
        a = math.atan2(co.y, co.x)
        push = 0.0
        for (da, dz, amount) in dents:
            dd = math.hypot((a - da + math.pi) % (2 * math.pi) - math.pi, (co.z - dz) * 3.0)
            push += amount * math.exp(-(dd / 0.35) ** 2)
        k = (rr - push * min(1.0, rr / R0)) / rr
        co.x *= k
        co.y *= k
    return dent


def _lid_shape():
    """The lid in its own frame: the skirt's bottom edge at z = 0, hollow underneath, a dome and a strap handle on top."""
    lid = shapes.Shape()
    ro = R1 + 0.019
    ri = R1 + 0.012
    lid.lathe([(0.0, 0.074), (0.06, 0.071), (0.15, 0.056), (ri - 0.01, 0.034), (ri, 0.028), (ri, 0.002), (ri + 0.002, 0.0),
               (ro, 0.0), (ro + 0.003, 0.006), (ro, 0.03), (ro - 0.012, 0.042), (0.16, 0.066), (0.07, 0.083), (0.0, 0.086)],
              segments=40)
    strap = shapes.smooth_path([(-0.075, 0.0, 0.078), (-0.06, 0.0, 0.112), (0.0, 0.0, 0.124), (0.06, 0.0, 0.112), (0.075, 0.0, 0.078)], steps=5)
    lid.sweep(strap, 0.0, section=[(-0.004, -0.014), (0.004, -0.014), (0.004, 0.014), (-0.004, 0.014)], up=Vector((0.0, 1.0, 0.0)))
    for sx in (-1, 1):
        lid.sphere((sx * 0.07, 0.0, 0.08), 0.009, segments=10, rings=5, squash=(1.0, 1.0, 0.6))
    return lid


def build(collection, seed=0, lid='on', ash='heaped'):
    if lid not in LIDS:
        raise ValueError("ash_bin lid is one of %s, not %r" % (', '.join(repr(s) for s in LIDS), lid))
    if ash not in ASHES:
        raise ValueError("ash_bin ash is one of %s, not %r" % (', '.join(repr(s) for s in ASHES), ash))
    rng = shapes.rng_for(PART, seed)
    dent = _denter(rng)
    objects = []

    # ------------------------------------------------------------------ the drum: one hollow turned shell with a rolled rim
    body = shapes.Shape()
    profile = [(0.0, 0.0), (R0 - 0.006, 0.0), (R0, 0.006)]
    for k in range(1, 14):
        z = 0.006 + (H - 0.02 - 0.006) * k / 13
        profile.append((_radius(z), z))
    profile += [(R1 + 0.004, H - 0.013), (R1 + 0.008, H - 0.007), (R1 + 0.007, H - 0.001), (R1 + 0.002, H + 0.001), (R1 - 0.003, H - 0.003)]
    for k in range(13, -1, -1):
        z = 0.02 + (H - 0.025 - 0.02) * k / 13
        profile.append((_radius(z) - 0.004, z))
    profile.append((0.0, 0.02))
    body.lathe(profile, segments=44)
    # rolled ribs round the body; the foot band (rusted) is the second material
    for z in (0.22, 0.42):
        body.torus((0, 0, z), _radius(z) + 0.002, 0.0075, segments=44, sides=8)
    body.material_index = 1
    body.torus((0, 0, 0.032), _radius(0.032) + 0.002, 0.009, segments=44, sides=8)
    body.material_index = 0
    # drop handles: a lug on each side, a bent rod hanging from it
    for sx in (-1, 1):
        zl = H - 0.12
        body.box((sx * (_radius(zl) + 0.006), 0.0, zl), (0.016, 0.16, 0.035))
        pts = []
        for k in range(15):
            t = math.pi * k / 14
            pts.append((sx * (_radius(zl) + 0.02 + 0.016 * math.sin(t)), -0.068 * math.cos(t), zl - 0.008 - 0.042 * math.sin(t)))
        body.sweep(pts, 0.0065, sides=8)
    for v in body.bm.verts:
        dent(v.co)
    objects.append(body.finish('ash_bin drum', collection, [street.bin_material(PART, H), RUST], smooth=True, sharp=50))

    # ------------------------------------------------------------------ the lid
    lid_shape = _lid_shape()
    if lid == 'on':
        m = Matrix.Translation((0.0, 0.0, H - 0.02)) @ Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, 'Y') @ \
            Matrix.Rotation(rng.uniform(0, math.pi), 4, 'Z')
        lid_shape.transform(m)
    elif lid == 'off':
        lid_shape.transform(Matrix.Translation((0.42, -0.36, 0.0)) @ Matrix.Rotation(rng.uniform(0, math.pi), 4, 'Z'))
    else:
        turn = math.radians(-118.0 + rng.uniform(-6, 6))
        lid_shape.transform(Matrix.Rotation(turn, 4, 'Z') @ Matrix.Rotation(math.radians(76.0), 4, 'Y'))
        direction = Vector((math.cos(turn), math.sin(turn), 0.0))
        low_z = min(v.co.z for v in lid_shape.bm.verts)
        near = min(v.co.dot(direction) for v in lid_shape.bm.verts)
        lid_shape.transform(Matrix.Translation(direction * (R1 + 0.014 - near) + Vector((0.0, 0.0, -low_z))))
    objects.append(lid_shape.finish('ash_bin lid', collection, shapes.galvanised_material(PART), smooth=True, sharp=50))

    # ------------------------------------------------------------------ the ash, and the clinker on it
    fill = shapes.Shape()
    if ash == 'heaped' and lid == 'on':
        # pressed down under the lid's dome (heaped higher it would come through the lid); nobody sees it, so no clinker
        street.heap(fill, (0.0, 0.0, H - 0.004), R1 - 0.002, R1 - 0.002, 0.028, rng, lobes=0.02, rough=0.005)
        top_z = None
    elif ash == 'heaped':
        street.heap(fill, (0.0, 0.0, H - 0.004), R1 - 0.002, R1 - 0.002, 0.12, rng, lobes=0.035, rough=0.014)
        top_z = H + 0.12
    else:
        z0 = H - 0.12
        street.heap(fill, (0.0, 0.0, z0), _radius(z0) - 0.006, _radius(z0) - 0.006, 0.035, rng, lobes=0.012, rough=0.01)
        top_z = z0 + 0.035
    for v in fill.bm.verts:
        dent(v.co)
    tree = BVHTree.FromBMesh(fill.bm)
    clinker = shapes.Shape()
    reach = (R1 - 0.03) if ash == 'heaped' else (_radius(H - 0.12) - 0.04)
    placed = 0
    for _ in range(80 if top_z is not None else 0):
        if placed >= 16:
            break
        a = rng.uniform(0, 2 * math.pi)
        d = math.sqrt(rng.uniform(0, 1)) * reach
        hit = tree.ray_cast(Vector((math.cos(a) * d, math.sin(a) * d, top_z + 0.1)), Vector((0.0, 0.0, -1.0)))
        if hit[0] is None:
            continue
        r = rng.uniform(0.012, 0.026)
        clinker.rock(hit[0] + Vector((0.0, 0.0, r * 0.25)), r, rng, squash=(1.0, 1.0, 0.7), jitter=0.35)
        placed += 1
    objects.append(fill.finish('ash_bin ash', collection, ASH, smooth=True, sharp=None))
    if not clinker.empty():
        objects.append(clinker.finish('ash_bin clinker', collection, street.clinker_material(PART), smooth=False))
    return objects
