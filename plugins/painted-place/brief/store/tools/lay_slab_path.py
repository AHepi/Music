"""
What this file does: lays a garden path of split stone slabs along a line or curve you give (the path's middle). The
slabs are laid in rows across the path, each row split into one to three slabs, so the joints never line up. Every slab
has its own outline: a rough rectangle with its corners knocked off (some hardly, some deeply, never at the same angle),
edges that wander and here and there a bite out of them, as split stone breaks. Its top is rough, with low swells, pits
and one or two shallow hollows; its edges are worn round; it is set a little in or out of level, tipped this way and
that. After rain, water stands in the hollows of some slabs: each puddle lies inside its own slab, flat at a level a
little under the stone round it, so the stone's own high parts stand out of it and its edge is as ragged as the stone;
the water is semi transparent, as rain water on stone is: looking straight down, half of the wet stone under it shows
through, darker, and the other half is the water's mirror (more mirror at a glancing look, fading out towards each
pool's shallow edge), so it reads neither as a black hole nor as a liquid mirror, with a faint ripple; the lamps light
the stone under it (`see_through=0` gives the old clear water, which mirrors far less). The joints are filled
with gravel and moss from the photographed sets, a little below the slabs' tops. Each slab shows its own part of a
photographed dark stone (the number 'pp_piece') and is a little lighter or darker than the next. Nothing here chooses
where the path goes: the line, its width and how much water stands on it are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_slab_path
    made = lay_slab_path.lay([(0, 0, 0.05), (0.3, 4, 0.05), (1.5, 9, 0.08)], width=1.3, water=0.4, seed=3)
    made['slabs'], made['water'], made['bed']          # the slabs, the water standing in them, the joints' bed
    z = lay_slab_path.top_at(made, 0.2, 2.0)           # the stone's height there (to stand a jar or a leaf on it)
    litter.scatter(made['slabs'], kinds=('maple',), amount=1.5, seed=4)   # wet maple leaves on the slabs and the water

The line may be a list of points (x, y, z), a curve object, a mesh object made of a line of edges, or the path of a JSON
file holding {"points": [[x, y, z], ...]}. Its z is the height of the slabs' tops there, unless you give `ground`: then
each slab stands `rise` above the ground under it and follows its slope, and the joints' bed follows the ground too.

From the command line:

    python3 lay_slab_path.py --help
    python3 lay_slab_path.py --points "0,0,0.05 0.3,4,0.05 1.5,9,0.08" --width 1.3 --water 0.4 --out path.blend

Options, with their defaults:
    width        1.2 m     across the path, joint to joint
    slab         0.55 m    about how long a slab is along the path (each its own, 0.7 to 1.15 of it); across, about
                           0.65 to 1.35 of it, so a row holds one to three slabs
    joint        0.035 m   about how wide the joints are (each its own, 0.6 to 1.5 of it)
    water        0.35      the share of the slabs that hold water in their hollows, 0 dry to 1 every slab that can
    mirror       0.5       how strongly the water mirrors the sky, 0 plain puddle water to 1 a strong mirror (water seen
                           from above at dusk mirrors only a little of the sky and reads as black: 0.5 to 0.8 shows it)
    see_through  0.5       how much of the stone under the water shows through it looking straight down; the rest is
                           the water's mirror (`mirror` sets how strong): 0.5 for the store's water, 0 for a water material
                           of your own; 0 with the store's water gives the old clear water ('• clear on stone'), which
                           shows the stone by bending the light and mirrors far less
    rough        1.0       how rough the tops are and how broken the outlines: 0 sawn flags, 1 split stone, up to 2
    lean         1.0       how far each slab is set out of level (tipped, raised or sunk a few millimetres); 0 laid true
    wear         1.0       how round the slabs' edges are worn; 0 sharp
    wet          0.7       how wet the stone is (the material's Wet dial): 0 dry, 1 just rained (higher reads as foil under a lamp)
    joints       'gravel and moss'   what fills the joints: 'gravel and moss', 'gravel', 'moss' or 'none' (no bed:
                           your own ground shows between the slabs)
    shades       0.25      how much one slab is lighter or darker than the next, 0 to 0.9
    ground       none      a mesh object: the slabs stand `rise` above it and follow its slope
    rise         0.04 m    with a ground: how far the slabs' tops stand above it
    smooth       True      a smooth curve through your points; a curve object keeps its own shape; False: straight runs
    seed         0         the same seed lays the same path
    material     'SURFACE • dark_rock_02'   the slabs (photographed; each slab its own part by 'pp_piece')
    joint_material  'SURFACE • gravel_road' the joints' bed (photographed; moss is laid over it as `joints` asks)
    water_material  'MADE • puddle water'   the water: the store's puddle water is given as a see-through copy,
                           '<material> • mirror 0.50 • see-through 0.50'; another material is used as it is (mirror raised
                           by `mirror`; made see-through only if you give see_through)
    collection   none      where the objects go (a new collection 'lay_slab_path')

What it makes: 'slab path' (obj['slabs'] the count, obj['wet_slabs'] how many hold water), 'slab path water' (when any
slab holds water) and 'slab path joints' (unless joints='none'). Every face of the slabs carries its slab's 'pp_piece',
'stone_tone' and 'stone_number'; every point of their tops carries 'water' (how deep the water stands over it, metres),
'wetness' and 'hollow', which the litter tool reads (leaves gather in the hollows and float on the water). The water
carries 'shallow' (0 deep to 1 at its edge), which the store's puddle water reads if you give it as it is.
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
import numpy
from mathutils import Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402
import _rough_stones  # noqa: E402

STONE = 'SURFACE • dark_rock_02'
JOINT = 'SURFACE • gravel_road'
WATER = 'MADE • puddle water'
JOINT_KINDS = ('gravel and moss', 'gravel', 'moss', 'none')
OUTLINE = 72                         # points round a slab
RINGS = (1.0, 0.99, 0.977, 0.96, 0.937, 0.905, 0.865, 0.815, 0.75, 0.67, 0.575, 0.47, 0.355, 0.235, 0.115)
WATER_RING = 7                       # the water stays inside this ring (0.815 of the way out): inside the worn edge
THICK = 0.14                         # a slab's depth from its top to its foot
BED_BELOW = 0.03                     # the joints' bed lies this far under the slabs' tops
UP = Vector((0.0, 0.0, 1.0))

TOOL = {
    'name': 'lay_slab_path',
    'what': 'a garden path of split stone slabs along a line or curve you give: each slab its own outline with its corners '
            'knocked off and wandering edges, a rough top with shallow hollows, worn round edges, set a little out of '
            'level; after rain, water standing in the hollows of some slabs, each puddle inside its own slab with the '
            "stone's high parts standing out of it; gravel and moss in the joints; each slab its own part of a "
            'photographed dark stone',
    'call': "made = lay_slab_path.lay([(0, 0, 0.05), (0.3, 4, 0.05), (1.5, 9, 0.08)], width=1.3, water=0.4, seed=3)",
    'options': {
        'line': "the path's middle: a list of points, a curve or line-mesh object, or a JSON file; its z the slabs' tops (required)",
        'width': 'across the path, joint to joint (1.2 m)',
        'slab': 'about how long a slab is along the path; each its own, 0.7 to 1.15 of it; across, 0.65 to 1.35 of it (0.55 m)',
        'joint': 'about how wide the joints are; each its own (0.035 m)',
        'water': 'the share of the slabs holding water in their hollows, 0 dry to 1 every slab that can (0.35)',
        'mirror': 'how strongly the water mirrors the sky: 0 plain puddle water, 1 a strong mirror (0.5)',
        'rough': 'how rough the tops and how broken the outlines: 0 sawn flags, 1 split stone, up to 2 (1.0)',
        'lean': 'how far each slab is set out of level; 0 laid true (1.0)',
        'wear': "how round the slabs' edges are worn; 0 sharp (1.0)",
        'wet': "the stone's Wet dial: 0 dry, 1 just rained (0.7)",
        'joints': "what fills the joints: 'gravel and moss', 'gravel', 'moss' or 'none' ('gravel and moss')",
        'shades': 'how much one slab is lighter or darker than the next, 0 to 0.9 (0.25)',
        'ground, rise': 'a mesh object the slabs stand on, following its slope, their tops `rise` above it (none, 0.04 m)',
        'smooth': 'a smooth curve through your points; a curve object keeps its own shape (True); False: straight runs',
        'seed': 'the same seed lays the same path (0)',
        'see_through': "how much of the stone under the water shows through it, looking straight down; the rest is the "
                       "water's mirror, more of it at a glancing look, fading out at each pool's shallow edge; the lamps "
                       "still light the stone under it (0.5 for the store's water, 0 for a water material of your own; 0 "
                       "with the store's water: the old clear water, '<material> • clear on stone 0.50', which shows the "
                       "stone by bending the light and mirrors far less)",
        'material, joint_material, water_material': "the slabs ('%s'), the joints' bed ('%s'), the water ('%s')" % (STONE, JOINT, WATER),
        'collection': "where the objects go (a new collection 'lay_slab_path')",
        'top_at(made, x, y)': "the stone's height at a point, or None off the slabs",
    },
    'materials': [STONE, JOINT, WATER],
    'source': "`rough_slab` and the puddles in the slabs' hollows in the garden builders' '57 garden' scripts "
              "('/home/claude/build-57-garden/first pass/render_final.py' and 'second pass/render_final.py', lines 633-726 "
              "and 787-810), after the owner's second picture (a wet path of rough dark slabs, water in their hollows), "
              "made into a tool: the slabs now follow a line or curve, their outlines are broken by knocked-off corners "
              "and bites instead of pulled grid corners, and the water is a flat sheet cut by the stone's own relief "
              "(the builder's water was an oval laid on each slab). The see-through water (see_through, puddle.see_through) "
              "from the garden builder's water pass ('/home/claude/build-57-garden/moss/render_final.py', "
              "see_through_water(), lines 872-957), after the owner's words \"The pools of water on the pavement also "
              "need to be semi transparent. Right now, it looks like a liquid mirror\": half mirror looking down, more at "
              "a glance, each pool fading out towards its shallow edge, the stone under it lit (here the fade reads the "
              "water's own 'shallow', its depth, instead of the builder's distance from each pool's middle)",
    'trap': "the line's z is the slabs' tops, not the ground: on your own ground give ground= (or the slabs float or sink); "
            "joints and water need store.prepare_for_render(scene) once before drawing; water mirrors the sky only where "
            'the sky is in its mirror: under an eave it mirrors the eave and reads black (put the wet slabs out in the open); '
            'the see-through water lets less bright sky into a close view looking down on the pools than a mirror would: a '
            'close view whose warm light was a lamp mirrored in a pool gets darker (the garden builder raised its exposure '
            'from 4.4 to 4.8); with see_through=0 the old clear water bends the light, and water that bends the light and '
            'casts shadow leaves the stone under it unlit (caustics are off): the tool\'s water casts none',
}


# ------------------------------------------------------------------------------------------------ the line

class _Line:
    """The path's middle, finely sampled: the point, the way ahead and the way to its left at any distance along it."""

    def __init__(self, line, smooth):
        points = []
        for point in _lines.line_points(line):
            p = Vector((point[0], point[1], point[2] if len(point) > 2 else 0.0))
            if points and (p.xy - points[-1].xy).length < 1e-5:
                continue
            points.append(p)
        if len(points) < 2:
            raise ValueError('the line needs at least two different points (seen from above)')
        if isinstance(line, bpy.types.Object) or not smooth:
            fine = []
            for a, b in zip(points[:-1], points[1:]):
                steps = max(1, int(math.ceil((b - a).length / 0.05)))
                fine.extend(a.lerp(b, k / steps) for k in range(steps))
            fine.append(points[-1])
            self.path = _lines.Path(fine)
        else:
            self.path = _lines.Path(points).smooth(0.05)
        self.total = self.path.total

    def frame(self, s):
        here = self.path.at(s)
        ahead = self.path.at(min(s + 0.03, self.total)) - self.path.at(max(s - 0.03, 0.0))
        ahead = Vector((ahead.x, ahead.y, 0.0))
        ahead = ahead.normalized() if ahead.length > 1e-9 else Vector((1.0, 0.0, 0.0))
        return here, Vector((-ahead.y, ahead.x, 0.0))

    def world(self, s, t):
        """The world point `s` metres along the line and `t` metres to its left, at the line's own height."""
        here, left = self.frame(s)
        return here + left * t


class _Ground:
    """The height of your ground under a point (a ray straight down), or None without a ground."""

    def __init__(self, ground):
        self.ground = ground
        if ground is not None:
            if ground.type != 'MESH':
                raise ValueError('ground must be a mesh object')
            bpy.context.view_layer.update()
            self.depsgraph = bpy.context.evaluated_depsgraph_get()
            self.to_local = ground.matrix_world.inverted()
            self.down = (self.to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
            self.above = max((ground.matrix_world @ Vector(c)).z for c in ground.bound_box) + 1.0

    def height(self, x, y, fallback):
        if self.ground is None:
            return fallback
        hit, location, _, _ = self.ground.ray_cast(self.to_local @ Vector((x, y, self.above)), self.down, distance=1.0e5,
                                                   depsgraph=self.depsgraph)
        return (self.ground.matrix_world @ location).z if hit else fallback


# ------------------------------------------------------------------------------------------------ one slab's outline

def _resample(polygon, count):
    """`count` points spaced evenly round a closed polygon of (s, t) points."""
    pts = [Vector(p) for p in polygon]
    lengths = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    result, index = [], 0
    for k in range(count):
        d = total * k / count
        while lengths[index + 1] < d:
            index += 1
        a, b = pts[index], pts[(index + 1) % len(pts)]
        span = lengths[index + 1] - lengths[index]
        result.append(a.lerp(b, (d - lengths[index]) / span if span > 0 else 0.0))
    return result


def _outline(corners, rng, rough, seed_offset):
    """The slab's outline seen from above, in the path's own measure (s along, t to the left): a four-sided slab (its
    corners given counter-clockwise) with its corners knocked off by cuts of their own size and angle, broken in the
    middle, then its edges bowed and wandering inwards and a bite or two taken out, as split stone breaks. Always inside
    the four sides, counter-clockwise."""
    corners = [Vector(c) for c in corners]
    small = min((corners[1] - corners[0]).length, (corners[2] - corners[1]).length,
                (corners[3] - corners[2]).length, (corners[0] - corners[3]).length)
    polygon = []
    for i, corner in enumerate(corners):
        before = corners[i - 1]
        after = corners[(i + 1) % 4]
        if rng.random() < 0.22 or rough <= 0:
            cut_in, cut_out = 0.008, 0.008                            # hardly touched: only the arris rounded
        else:
            cut_in = small * rng.uniform(0.05, 0.24) * min(rough, 1.5)
            cut_out = cut_in * rng.uniform(0.45, 1.8)                 # never at the same angle
        to_before = (before - corner).normalized()
        to_after = (after - corner).normalized()
        a = corner + to_before * min(cut_in, (before - corner).length * 0.4)
        b = corner + to_after * min(cut_out, (after - corner).length * 0.4)
        polygon.append(a)
        if cut_in > 0.01:                                             # the break is never straight
            middle = a.lerp(b, rng.uniform(0.35, 0.65))
            inward = (to_before + to_after).normalized()
            polygon.append(middle + inward * (a - b).length * rng.uniform(-0.05, 0.22) * min(rough, 1.5))
        polygon.append(b)
    points = _resample(polygon, OUTLINE)
    bites = [(rng.uniform(0.0, 1.0), rng.uniform(0.012, 0.045) * rough, rng.uniform(0.02, 0.06)) for _ in range(rng.randint(0, 3))]
    bows = [(rng.uniform(0.0, 1.0), rng.uniform(0.004, 0.016) * rough, rng.uniform(0.12, 0.3)) for _ in range(rng.randint(1, 3))]
    perimeter = sum((points[(k + 1) % OUTLINE] - points[k]).length for k in range(OUTLINE))
    result = []
    for k, p in enumerate(points):
        prev, nxt = points[k - 1], points[(k + 1) % OUTLINE]
        along = (nxt - prev).normalized()
        inward = Vector((-along.y, along.x))                          # left of the way round: inside a CCW outline
        u = k / OUTLINE
        wander = 0.5 + noise.noise(Vector((math.cos(u * math.tau) * 2.3 + seed_offset, math.sin(u * math.tau) * 2.3, 1.7)))
        wander += 0.35 * (0.5 + noise.noise(Vector((math.cos(u * math.tau) * 7.0, math.sin(u * math.tau) * 7.0 + seed_offset, 4.1))))
        push = rough * (0.0025 + 0.009 * max(wander, 0.0))
        for centre, depth, spread in bites + bows:
            gap = min(abs(u - centre), 1.0 - abs(u - centre)) * perimeter
            push += depth * math.exp(-(gap / spread) ** 2)
        result.append(p + inward * push)
    return result


# ------------------------------------------------------------------------------------------------ the slabs

class _Slabs:
    """Slabs gathered into one mesh, each with its numbers."""

    def __init__(self):
        self.verts, self.faces = [], []
        self.face_piece, self.face_tone, self.face_number = [], [], []
        self.water, self.wetness, self.hollow = [], [], []
        self.count = 0
        self.wet = 0
        self.sheet_verts, self.sheet_faces, self.sheet_shallow = [], [], []

    def slab(self, line, ground, outline, rng, rough, lean, wear, rise, holds_water, seed):
        n = OUTLINE
        centre = Vector((sum(p.x for p in outline) / n, sum(p.y for p in outline) / n))
        size = max((p - centre).length for p in outline)
        here = line.world(centre.x, centre.y)
        base_here = ground.height(here.x, here.y, None)
        tilt_s = rng.gauss(0.0, 0.012) * lean                         # metres per metre: tipped a little this way and that
        tilt_t = rng.gauss(0.0, 0.012) * lean
        lift = rng.uniform(-0.006, 0.006) * lean                      # raised or sunk a few millimetres
        if base_here is not None:                                     # on your ground: follow its slope
            ahead_pt = line.world(centre.x + 0.15, centre.y)
            left_pt = line.world(centre.x, centre.y + 0.15)
            tilt_s += (ground.height(ahead_pt.x, ahead_pt.y, base_here) - base_here) / 0.15
            tilt_t += (ground.height(left_pt.x, left_pt.y, base_here) - base_here) / 0.15
        offset = Vector((rng.uniform(-90, 90), rng.uniform(-90, 90), rng.uniform(-90, 90)))
        hollows = []                                                  # (s, t, radius_s, radius_t, turn, depth)
        for k in range(1 if rng.random() < 0.6 else 2):
            depth = rng.uniform(0.003, 0.009) * rough
            reach, spread = 0.3, (0.35, 0.7)
            if holds_water and k == 0:                                # a hollow well inside the slab, deep enough to hold rain
                depth = rng.uniform(0.02, 0.034) * max(rough, 0.6)
                reach, spread = 0.12, (0.34, 0.56)
            hs, ht = centre.x + rng.uniform(-reach, reach) * size, centre.y + rng.uniform(-reach, reach) * size
            hollows.append((hs, ht, size * rng.uniform(*spread), size * rng.uniform(spread[0] * 0.75, spread[1] * 0.8), rng.uniform(0, math.pi), depth))
            if holds_water and k == 0:                                # a second, smaller dip beside it: the puddle is never a disc
                a = rng.uniform(0, math.tau)
                hollows.append((hs + math.cos(a) * size * 0.28, ht + math.sin(a) * size * 0.22, size * rng.uniform(0.18, 0.3),
                                size * rng.uniform(0.14, 0.24), rng.uniform(0, math.pi), depth * rng.uniform(0.6, 0.9)))
        round_r = 0.032 * max(wear, 0.05) * rng.uniform(0.75, 1.3)
        drop = 0.022 * wear

        def top(s, t, to_edge):
            p = line.world(s, t)
            z = (base_here + rise) if base_here is not None else p.z
            z += lift + tilt_s * (s - centre.x) + tilt_t * (t - centre.y)
            q = Vector((p.x * 4.5, p.y * 4.5, 0.0)) + offset
            relief = 0.0034 * noise.noise(q) + 0.0016 * noise.noise(q * 2.7)     # low swells: the photograph carries the grain
            pit = noise.noise(q * 1.9 + Vector((3.3, 1.1, 7.7)))
            if pit > 0.36:
                relief -= (pit - 0.36) * 0.014
            z += relief * rough
            dip = 0.0
            for hs, ht, rs, rt, turn, depth in hollows:
                ds, dt = s - hs, t - ht
                a = (ds * math.cos(turn) + dt * math.sin(turn)) / rs
                b = (-ds * math.sin(turn) + dt * math.cos(turn)) / rt
                ragged = 1.0 + 0.7 * noise.noise(Vector((s * 5.0, t * 5.0, offset.z + 2.0))) + 0.3 * noise.noise(Vector((s * 13.0, t * 13.0, offset.z)))
                dip += depth * math.exp(-(a * a + b * b) * max(ragged, 0.25) * 1.6)
            if dip > 0.002:                                           # the grain the water's edge follows
                z += 0.0016 * noise.noise(Vector((p.x * 26.0, p.y * 26.0, offset.y))) * min(1.0, dip / 0.006) * rough
            z -= dip
            if to_edge < round_r:
                z -= drop * (1.0 - to_edge / round_r) ** 2
            return Vector((p.x, p.y, z)), dip

        base = len(self.verts)
        tops, dips = [], []
        for f in RINGS:
            for p in outline:
                q = centre + (p - centre) * f
                point, dip = top(q.x, q.y, (1.0 - f) * (p - centre).length)
                tops.append(point)
                dips.append(dip)
        middle, middle_dip = top(centre.x, centre.y, size)
        tops.append(middle)
        dips.append(middle_dip)
        # the side: from the top's edge straight down to the foot (hidden in the joints' bed), its own points so the
        # top's edge keeps its own light and nothing laid on the top (a leaf) slides down the side
        side = [v.copy() for v in tops[:n]]
        foot = [Vector((v.x, v.y, v.z - THICK)) for v in tops[:n]]
        verts = tops + side + foot                                    # no underside: nothing sees it, and a leaf must not lie there
        rings = len(RINGS)
        faces = []
        for r in range(rings - 1):
            a, b = r * n, (r + 1) * n
            for k in range(n):
                k1 = (k + 1) % n
                faces.append((a + k, a + k1, b + k1, b + k))
        last = (rings - 1) * n
        centre_index = rings * n
        for k in range(n):
            faces.append((last + k, last + (k + 1) % n, centre_index))
        side0 = rings * n + 1
        foot0 = side0 + n
        for k in range(n):
            k1 = (k + 1) % n
            faces.append((side0 + k1, side0 + k, foot0 + k, foot0 + k1))

        # water: flat a little under the lowest stone round its ring, so the stone's high parts stand out of it
        depths = [0.0] * len(verts)
        if holds_water:
            ring_low = min(v.z for v in tops[WATER_RING * n:(WATER_RING + 1) * n])
            lowest = min(v.z for v in tops[WATER_RING * n:])          # the hollow's floor (not the worn edges)
            if ring_low - lowest > 0.004:
                level = lowest + (ring_low - 0.0015 - lowest) * rng.uniform(0.72, 0.97)
                keep = set()
                for r in range(WATER_RING, rings - 1):
                    a, b = r * n, (r + 1) * n
                    for k in range(n):
                        k1 = (k + 1) % n
                        quad = (a + k, a + k1, b + k1, b + k)
                        if min(tops[i].z for i in quad) < level + 0.0005:
                            keep.add(quad)
                for k in range(n):
                    tri = (last + k, last + (k + 1) % n, centre_index)
                    if min(tops[i].z for i in tri) < level + 0.0005:
                        keep.add(tri)
                if keep:
                    used = sorted({i for face in keep for i in face})
                    remap = {}
                    for i in used:
                        remap[i] = len(self.sheet_verts)
                        swell = 0.0004 * noise.noise(Vector((tops[i].x * 6.0, tops[i].y * 6.0, seed * 0.37 + 5.0)))
                        self.sheet_verts.append((tops[i].x, tops[i].y, level + swell))
                        self.sheet_shallow.append(min(1.0, max(0.0, 1.0 - (level - tops[i].z) / 0.011)))
                    self.sheet_faces.extend(tuple(remap[i] for i in face) for face in keep)
                    for i in used:                                    # only where the water lies (not the worn edges)
                        depths[i] = max(0.0, level - tops[i].z)
                    self.wet += 1
        deepest = max(dips) or 1.0
        for i, v in enumerate(verts):
            self.verts.append(tuple(v))
            is_top = i < len(tops)
            self.water.append(depths[i] if is_top else 0.0)
            self.wetness.append(1.0 if (is_top and depths[i] > 0) else (0.85 if is_top else 0.6))
            self.hollow.append(dips[i] / deepest if is_top and max(dips) > 0.002 else 0.0)
        tone = rng.random()
        piece = rng.random()
        for face in faces:
            self.faces.append(tuple(base + i for i in face))
            self.face_piece.append(piece)
            self.face_tone.append(tone)
            self.face_number.append(self.count)
        self.count += 1

    def make(self, name, material, collection, ground_z):
        mesh = bpy.data.meshes.new(name)
        origin = Vector(self.verts[0]) if self.verts else Vector()
        mesh.from_pydata([tuple(Vector(v) - origin) for v in self.verts], [], self.faces)
        for attribute, kind, domain, values in (('pp_piece', 'FLOAT', 'FACE', self.face_piece),
                                                ('stone_tone', 'FLOAT', 'FACE', self.face_tone),
                                                ('stone_number', 'INT', 'FACE', self.face_number),
                                                ('water', 'FLOAT', 'POINT', self.water),
                                                ('wetness', 'FLOAT', 'POINT', self.wetness),
                                                ('hollow', 'FLOAT', 'POINT', self.hollow)):
            layer = mesh.attributes.new(attribute, kind, domain)
            if values:
                layer.data.foreach_set('value', values)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces[:])
        tool.to_mesh(mesh)
        tool.free()
        mesh.shade_smooth()
        if hasattr(mesh, 'set_sharp_from_angle'):
            mesh.set_sharp_from_angle(angle=math.radians(50.0))
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        collection.objects.link(obj)
        store.use_material(obj, material, ground=ground_z)
        obj['slabs'] = self.count
        obj['wet_slabs'] = self.wet
        return obj

    def make_water(self, name, material, collection, ground_z):
        if not self.sheet_faces:
            return None
        mesh = bpy.data.meshes.new(name)
        origin = Vector(self.sheet_verts[0])
        mesh.from_pydata([tuple(Vector(v) - origin) for v in self.sheet_verts], [], self.sheet_faces)
        layer = mesh.attributes.new('shallow', 'FLOAT', 'POINT')
        layer.data.foreach_set('value', self.sheet_shallow)
        for polygon in mesh.polygons:                                 # faces up
            if polygon.normal.z < 0:
                polygon.flip()
        mesh.update()
        mesh.shade_smooth()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        obj.visible_shadow = False
        collection.objects.link(obj)
        store.use_material(obj, material, ground=ground_z)
        return obj


# ------------------------------------------------------------------------------------------------ materials

def _material(name_or_material):
    return store.material(name_or_material) if isinstance(name_or_material, str) else name_or_material


def _wet_copy(material, wet):
    """A copy of a photographed stone with its Wet dial at `wet` and its relief a little stronger (rain shows it)."""
    name = '%s • slab path wet %.2f' % (material.name, wet)
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_slab_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_slab_of'] = material.name
    nodes = copy.node_tree.nodes if copy.use_nodes and copy.node_tree else {}
    normal = nodes.get('Normal picture') if nodes else None
    if normal is not None and 'Strength' in normal.inputs:          # big facets glossy with rain read as crumpled foil
        normal.inputs['Strength'].default_value = min(normal.inputs['Strength'].default_value, 0.6)
    weather = nodes.get('Weather') if nodes else None
    if weather is not None:
        if 'Wet' in weather.inputs:
            weather.inputs['Wet'].default_value = float(wet)
        if 'Edge wear' in weather.inputs:
            weather.inputs['Edge wear'].default_value = max(weather.inputs['Edge wear'].default_value, 0.35)
    return copy


def clear_water(material, mirror):
    """The water standing on the slabs: a copy of the puddle water made clear, as rain water on stone is: the wet stone
    seen through it (darker where deeper, by refraction), the sky mirrored on it, its ripple kept; `mirror` raises its
    mirror as puddle.strong_mirror does. Named '<material> • clear on stone 0.50'; made once, then shared."""
    name = '%s • clear on stone %.2f' % (material.name, mirror)
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_clear_of') == material.name:
        return existing
    import puddle
    copy = puddle.strong_mirror(material, mirror).copy() if mirror > 0 else material.copy()
    copy.name = name
    copy['pp_clear_of'] = material.name
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    for node in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        for socket in ('Alpha', 'Base Color'):
            for link in list(node.inputs[socket].links):
                links.remove(link)
        node.inputs['Alpha'].default_value = 1.0
        node.inputs['Base Color'].default_value = (0.6, 0.62, 0.65, 1.0)     # the stone under the water a little darker
        node.inputs['Transmission Weight'].default_value = 1.0
    return copy


def _joint_copy(material, joints):
    """The joints' bed: the photographed gravel wet and darkened, with moss over it as asked."""
    name = '%s • slab joints %s' % (material.name, joints)
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_joints_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_joints_of'] = material.name
    weather = copy.node_tree.nodes.get('Weather') if copy.use_nodes and copy.node_tree else None
    if weather is not None:
        if 'Wet' in weather.inputs:
            weather.inputs['Wet'].default_value = 0.9
        if 'Darken' in weather.inputs:
            weather.inputs['Darken'].default_value = weather.inputs['Darken'].default_value * 0.5
    if joints in ('gravel and moss', 'moss'):
        import moss
        mossy = moss.add(copy, amount=1.0 if joints == 'gravel and moss' else 1.45, foot=0.0, facing=(0.2, 0.8),
                         scale=14.0 if joints == 'gravel and moss' else 8.0, colour=(0.022, 0.042, 0.012))
        mossy.name = name + ' •'
        bpy.data.materials.remove(copy)
        mossy.name = name
        mossy['pp_joints_of'] = material.name
        return mossy
    return copy


# ------------------------------------------------------------------------------------------------ laying

SEE_THROUGH = 0.5                    # the store's water on the slabs: half of the stone under it shows through, looking down


def lay(line, width=1.2, slab=0.55, joint=0.035, water=0.35, mirror=0.5, rough=1.0, lean=1.0, wear=1.0, wet=0.7,
        joints='gravel and moss', shades=0.25, ground=None, rise=0.04, smooth=True, seed=0, material=STONE,
        joint_material=JOINT, water_material=WATER, collection=None, see_through=None):
    """Lay the path (see the note at the top). Returns {'slabs': obj, 'water': obj or None, 'bed': obj or None}.
    `see_through` (0 to 1): how much of the stone under the water shows through it looking straight down, the rest the
    water's mirror (puddle.see_through); None: 0.5 for the store's puddle water, 0 for a water material of your own;
    0 with the store's water: the old clear water, which shows the stone by bending the light (clear_water)."""
    width, slab, joint = float(width), float(slab), float(joint)
    water, mirror, rough, lean, wear, wet, shades = (float(v) for v in (water, mirror, rough, lean, wear, wet, shades))
    if see_through is None:
        see_through = SEE_THROUGH if water_material == WATER else 0.0
    see_through = float(see_through)
    if width < 0.3 or slab < 0.15:
        raise ValueError('width is at least 0.3 m and slab at least 0.15 m, not %r and %r' % (width, slab))
    if not 0.0 <= water <= 1.0 or not 0.0 <= mirror <= 1.0 or not 0.0 <= see_through <= 1.0:
        raise ValueError('water, mirror and see_through are 0 to 1, not %r, %r and %r' % (water, mirror, see_through))
    if not 0.0 <= rough <= 2.0:
        raise ValueError('rough is 0 to 2, not %r' % (rough,))
    if not 0.0 <= shades <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    if joints not in JOINT_KINDS:
        raise ValueError('joints is one of %s, not %r' % (', '.join(repr(k) for k in JOINT_KINDS), joints))
    rng = random.Random(seed)
    path = _Line(line, smooth)
    floor = _Ground(ground)
    if collection is None:
        collection = bpy.data.collections.new('lay_slab_path')
        bpy.context.scene.collection.children.link(collection)
    slabs = _Slabs()
    half = width / 2.0
    s = 0.0
    skew = 0.0                                                        # the joint across the path is never quite square to it
    owed = water * random.Random(seed + 17).uniform(0.0, 1.0)         # the wet slabs: the share asked, spread unevenly
    picking = random.Random(seed + 29)
    while s < path.total - 0.12:
        depth = slab * rng.uniform(0.7, 1.15)
        next_skew = rng.uniform(-0.09, 0.09) * min(rough, 1.5)
        if path.total - (s + depth) < slab * 0.45:                    # the last row fitted to the line's end
            depth = path.total - s
            next_skew = 0.0
        if s == 0.0:
            skew = 0.0
        edges = [-half]
        while half - edges[-1] > slab * 1.35:
            edges.append(edges[-1] + slab * rng.uniform(0.65, 1.35))
        if half - edges[-1] < slab * 0.4 and len(edges) > 1:
            edges.pop()
        edges.append(half)
        for t0, t1 in zip(edges[:-1], edges[1:]):
            g = [joint * rng.uniform(0.3, 0.75) for _ in range(4)]    # half joints, each its own
            a, b = t0 + (g[2] if t0 > -half else 0.004), t1 - (g[3] if t1 < half else 0.004)
            back, front = s + g[0], s + depth - g[1]
            corners = [(back + skew * a, a), (front + next_skew * a, a), (front + next_skew * b, b), (back + skew * b, b)]
            outline = _outline(corners, rng, rough, rng.uniform(-60, 60))
            owed += water
            holds = owed >= picking.uniform(0.45, 1.0) and water > 0
            if holds:
                owed -= 1.0
            slabs.slab(path, floor, outline, rng, rough, lean, wear, float(rise), holds, seed + slabs.count)
        s += depth
        skew = next_skew
    start = path.world(0.0, 0.0)
    ground_z = floor.height(start.x, start.y, start.z - BED_BELOW)
    stone = _rough_stones.shaded(_wet_copy(_material(material), wet), shades)
    made = {'slabs': slabs.make('slab path', stone, collection, ground_z)}
    water_mat = _material(water_material)
    if see_through > 0:                                               # half mirror, half the stone seen through it
        import puddle
        water_mat = puddle.see_through(puddle.strong_mirror(water_mat, mirror) if mirror > 0 else water_mat, see_through)
    elif water_material == WATER:                                     # the old way: the store's water clear on the stone
        water_mat = clear_water(water_mat, mirror)
    elif mirror > 0:
        import puddle
        water_mat = puddle.strong_mirror(water_mat, mirror)
    made['water'] = slabs.make_water('slab path water', water_mat, collection, ground_z)
    made['bed'] = None if joints == 'none' else _bed(path, floor, width, float(rise), _joint_copy(_material(joint_material), joints), collection, ground_z)
    return made


def _bed(path, floor, width, rise, material, collection, ground_z):
    """The joints' bed: a strip under the whole path, a little below the slabs' tops, reaching a little past its sides."""
    across = [k / 8.0 for k in range(9)]
    reach = width / 2.0 + 0.06
    steps = max(2, int(math.ceil(path.total / 0.1)) + 1)
    verts = []
    for j in range(steps):
        s = path.total * j / (steps - 1)
        for u in across:
            t = -reach + 2 * reach * u
            p = path.world(s, t)
            z = floor.height(p.x, p.y, None)
            z = (z + rise if z is not None else p.z) - BED_BELOW - 0.006 * (abs(2 * u - 1) ** 2)
            verts.append((p.x, p.y, z))
    cols = len(across)
    faces = [(j * cols + i, j * cols + i + 1, (j + 1) * cols + i + 1, (j + 1) * cols + i) for j in range(steps - 1) for i in range(cols - 1)]
    mesh = bpy.data.meshes.new('slab path joints')
    origin = Vector(verts[0])
    mesh.from_pydata([tuple(Vector(v) - origin) for v in verts], [], faces)
    for polygon in mesh.polygons:
        if polygon.normal.z < 0:
            polygon.flip()
    mesh.update()
    mesh.shade_smooth()
    obj = bpy.data.objects.new('slab path joints', mesh)
    obj.location = origin
    collection.objects.link(obj)
    store.use_material(obj, material, ground=ground_z)
    return obj


def top_at(made, x, y):
    """The height of the stone at (x, y): the top of the slab there, or None where no slab is (a joint, off the path)."""
    obj = made['slabs'] if isinstance(made, dict) else made
    bpy.context.view_layer.update()
    to_local = obj.matrix_world.inverted()
    above = max((obj.matrix_world @ Vector(c)).z for c in obj.bound_box) + 1.0
    hit, location, _, _ = obj.ray_cast(to_local @ Vector((x, y, above)), (to_local.to_3x3() @ Vector((0, 0, -1))).normalized())
    return (obj.matrix_world @ location).z if hit else None


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of lay_slab_path.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the path\'s middle line as "x,y,z x,y,z ..."; makes a new file unless --blend is given')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--ground', help='the name of a ground mesh object in the --blend file')
    for name, default, help_text in (('width', 1.2, 'across the path, metres'), ('slab', 0.55, 'about how long a slab is, metres'),
                                     ('joint', 0.035, 'about how wide the joints are, metres'),
                                     ('water', 0.35, 'the share of the slabs holding water, 0 to 1'),
                                     ('mirror', 0.5, 'how strongly the water mirrors the sky, 0 to 1'),
                                     ('see_through', 0.5, 'how much of the stone shows through the water looking down, 0 to 1 (0: the old clear water)'),
                                     ('rough', 1.0, 'how rough and broken, 0 to 2'), ('lean', 1.0, 'how far out of level'),
                                     ('wear', 1.0, 'how round the edges are worn'), ('wet', 0.7, 'how wet the stone is, 0 to 1'),
                                     ('shades', 0.25, 'how much one slab is lighter or darker than the next'),
                                     ('rise', 0.04, 'with a ground: the slabs\' tops above it, metres')):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (help_text, default))
    parser.add_argument('--joints', default='gravel and moss', choices=list(JOINT_KINDS), help="what fills the joints; default 'gravel and moss'")
    parser.add_argument('--straight', action='store_true', help='straight between the points instead of a smooth curve')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same path; default 0')
    parser.add_argument('--out', help='save the result here (.blend)')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    if args.line:
        line = bpy.data.objects.get(args.line)
        if line is None:
            parser.error('no object %r in the file' % args.line)
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in p.split(',')) for p in args.points.split()]
    else:
        parser.error('give the line: --points, --points-json or --blend with --line')
    ground = bpy.data.objects.get(args.ground) if args.ground else None
    made = lay(line, width=args.width, slab=args.slab, joint=args.joint, water=args.water, mirror=args.mirror, see_through=args.see_through, rough=args.rough,
               lean=args.lean, wear=args.wear, wet=args.wet, joints=args.joints, shades=args.shades, ground=ground, rise=args.rise,
               smooth=not args.straight, seed=args.seed)
    print('laid %d slabs, %d holding water' % (made['slabs']['slabs'], made['slabs']['wet_slabs']))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
