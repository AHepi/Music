"""
What this file does: makes one puddle where you say: a sheet of water with a ragged, irregular outline (bays, spits and
a broken edge, never a clean disc or ellipse), its surface a few millimetres above the ground, and round it a larger
ragged film of wet ground. The water is dark and deep in the middle and clear at its shallow rim, so the ground shows
through there instead of a hard cut-out edge; the material adds a faint ripple that breaks the reflection. The wet film
darkens and glosses the ground right against the water and thins out in broken patches towards its own edge.
Give it your ground object and both sheets are draped onto it (rays cast straight down), so they follow uneven ground:
the water lies level over small hollows, and bumps that rise above it show through as wet mud. A puddle in a rut can be
long and thin (size and turn). Nothing here chooses where puddles go: one call, one puddle, where you say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import puddle
    water, film = puddle.make((2.0, 5.0, 0.0), size=(1.2, 1.0), seed=1)                         # on flat ground at z = 0
    water, film = puddle.make((0.5, 3.0, 0.0), size=(2.5, 0.6), turn=20, ground=my_ground, seed=2)   # a long one in a rut

From the command line:

    python3 puddle.py --help
    python3 puddle.py --blend IN.blend --at 2 5 0 --size 1.2 1.0 [--turn 20] [--ground Ground] [--seed 1] --out OUT.blend

Options:
    location        where the middle of the puddle is (x, y, z); z is the ground's height there when no ground is given
    size            (length, width) in metres, about the outer size of the water; default (1.2, 1.0)
    turn            degrees about Z the length is turned, counter-clockwise seen from above; default 0
    ground          your ground mesh object to drape both sheets onto; default None (flat ground at location's z)
    seed            the outline's bays and spits, the edge's wobble; default 0
    collection      where the two objects go; default a new collection 'puddle'
    water_material  default 'MADE • puddle water' (reads 'shallow')
    film_material   default 'MADE • wet ground film' (reads 'dry')
    lift            how far the water sits above the ground, metres; default 0.004 (the film sits at half that)
    level           a height in metres: the water lies flat at it instead of on the ground (a puddle among setts:
                    the setts object's 'top_height' + 0.002, so the highest stones stand out of it); default none
    film_reach      how far the wet ground reaches past the water, metres; default 0.3 x half the width + 0.08
    raggedness      how broken the outline is (0 a smooth blob, 1 normal, 2 very broken); default 1
    shallow_band    how wide the shallow, clear rim of the water is, metres; default about 0.4 x half the width (at most 0.22)
    film            False leaves out the wet film round the water (the ground tool's soil already wets the ground round its
                    water); default True
    mirror          how strongly the water mirrors the sky: 0 as the puddle water always was, up to 1 a strong mirror
                    (water seen from above at dusk mirrors only a little of the sky and reads as black: 0.5 to 0.8 shows
                    the sky in it); the water then wears a copy of its material, '<material> • mirror 0.50'; default 0
    no_ring         True: the wet film darkens the ground round the water without the broad glossy shine that draws a
                    pale ring round the water under a lamp (it wears a copy of its material, '<material> • no ring'),
                    and the water's clear rim is kept narrow (shallow_band 0.04 unless you give one); default False
    see_through     how much of the stone or ground under the water shows through it, looking straight down: 0 the
                    water as it always was; 0.5 half, the rest its mirror (more mirror at a glancing look, the mirror
                    fading out at the shallow edge); the lamps still light what is under it. For a puddle on stone
                    paving, which reads as a liquid mirror otherwise. The water wears a copy of its material,
                    '<material> • see-through 0.50'; puddle.see_through(material, 0.5) makes one for water of your own
                    (it reads 'shallow' for the edge, if your mesh has it); default 0

The water writes the number 'shallow' on each point (0 in the deep middle, rising to 1 at the rim, also 1 where a bump
rises to the surface); the film writes 'dry' (0 against the water and under it, rising to 1 at its outer edge). The two
made materials read exactly these. Neither sheet casts a shadow.
"""

import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import store  # noqa: E402

WATER_MATERIAL = 'MADE • puddle water'
FILM_MATERIAL = 'MADE • wet ground film'

TOOL = {
    'name': 'puddle',
    'what': 'makes one puddle where you say: ragged dark water, clear at its shallow rim, in a ragged wet film of ground',
    'call': "water, film = puddle.make((2.0, 5.0, 0.0), size=(2.5, 0.6), turn=20, ground=my_ground, seed=2)",
    'options': {
        'location': "the puddle's middle (x, y, z); z is the ground height when no ground is given",
        'size': '(length, width) of the water in metres, about; default (1.2, 1.0)',
        'turn': 'degrees about Z the length is turned; default 0',
        'ground': 'your ground mesh object to drape the puddle onto; default None (flat at z)',
        'seed': "the outline's bays, spits and broken edge; default 0",
        'collection': "where the two objects go; default a new collection 'puddle'",
        'water_material': "default '%s'" % WATER_MATERIAL,
        'film_material': "default '%s'" % FILM_MATERIAL,
        'lift': 'metres the water sits above the ground; default 0.004',
        'level': 'a height: the water lies flat at it instead of on the ground (a puddle among setts: 2 mm above the road\'s height); default none',
        'film_reach': 'metres the wet ground reaches past the water; default 0.3 x half the width + 0.08',
        'raggedness': 'how broken the outline is: 0 smooth, 1 normal, 2 very broken; default 1',
        'shallow_band': 'metres of shallow, clear rim; default about 0.4 x half the width, at most 0.22',
        'mirror': 'how strongly the water mirrors the sky: 0 as it always was, 1 a strong mirror (seen from above at dusk '
                  'plain water reads black: 0.5 to 0.8 shows the sky); default 0',
        'no_ring': 'True: the wet film darkens the ground round the water without the glossy shine that draws a pale ring '
                   'round it under a lamp, and the clear rim is kept narrow; default False',
        'see_through': 'how much of the stone or ground under the water shows through it, looking straight down: 0 the '
                       'water as it always was (dark, the ground showing only at its clear rim), 0.5 half (the rest its '
                       'mirror, more mirror at a glancing look, fading out at its shallow edge; the lamps still light what '
                       'is under it): for a puddle on stone paving, which otherwise reads as a liquid mirror; the water '
                       "then wears a copy of its material, '<material> • see-through 0.50' (puddle.see_through(material, "
                       'see) makes one for water of your own); default 0',
    },
    'materials': [WATER_MATERIAL, FILM_MATERIAL],
    'source': 'plugins/painted-place/materials/lay_details.py: puddles; lay_shore.py: wet_ground (rebuilt: ragged outline, shallow rim, wet film); '
              "see_through from the garden builder's water pass ('/home/claude/build-57-garden/moss/render_final.py', "
              "see_through_water(), lines 872-957, and the puddle on the path, lines 1920-1934), after the owner's words "
              '"The pools of water on the pavement also need to be semi transparent. Right now, it looks like a liquid '
              'mirror": its mix of the water with a see-through surface (half mirror looking down, a Fresnel share of '
              'IOR 1.7 at a glance, the stone under it tinted 0.62, 0.60, 0.56), its fade towards each pool\'s edge '
              "(here by the puddle's own 'shallow')",
    'trap': "the materials need the numbers this tool writes ('shallow', 'dry'): on your own mesh the water is deep all over; "
            'see-through water lets less bright sky into a close view than mirror water: a close view whose warm light '
            'came from a lamp mirrored in the water gets darker (the garden builder raised that view\'s exposure from '
            '4.4 to 4.8), so give the one puddle that mirrors a lamp less see_through',
}

def strong_mirror(material, mirror=0.6):
    """A copy of a water material that mirrors the sky more strongly: its IOR and its specular level raised and its
    ripples' roughness lowered by `mirror` (0 to 1). Named '<material> • mirror 0.60'; made once, then shared; mirror 0
    returns the material itself. Water seen from above mirrors only about 2 per cent of the sky, so at dusk it reads as
    black; a painter's puddle shows the sky."""
    material = store.material(material) if isinstance(material, str) else material
    mirror = min(max(float(mirror), 0.0), 1.0)
    if mirror <= 0:
        return material
    name = '%s • mirror %.2f' % (material.name, mirror)
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_mirror_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_mirror_of'] = material.name
    if copy.use_nodes and copy.node_tree is not None:
        for node in copy.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                ior = node.inputs['IOR']
                ior.default_value = ior.default_value + (2.2 - ior.default_value) * mirror
                level = node.inputs['Specular IOR Level']
                level.default_value = level.default_value + (1.0 - level.default_value) * mirror
                rough = node.inputs['Roughness']
                if rough.links and rough.links[0].from_node.type == 'MAP_RANGE':
                    ranged = rough.links[0].from_node
                    for key in ('To Min', 'To Max'):
                        ranged.inputs[key].default_value *= 1.0 - 0.6 * mirror
                elif not rough.links:
                    rough.default_value *= 1.0 - 0.6 * mirror
    return copy


SEE_TINT = (0.62, 0.60, 0.56)      # the stone seen through the water: darker and a little warmer than the dry stone
SEE_GLANCE = 1.7                   # how fast the mirror grows at a glancing look (a Fresnel IOR; water's own is 1.333)


def see_through(material, see=0.5, glance=SEE_GLANCE, tint=SEE_TINT, edge=True):
    """A copy of a water material made semi transparent, as the garden builder made its pools on the stone path (6
    November 2026, after the owner's words "The pools of water on the pavement also need to be semi transparent. Right
    now, it looks like a liquid mirror"): the water's own surface (its mirror) mixed with a see-through surface. Looking
    straight down, `see` of what is under the water shows through (0.5: half) and the rest is the water's mirror; at a
    glancing look the mirror grows towards all of it (a Fresnel share, IOR `glance`); with `edge`, the mirror fades out
    where the water is shallow (the mesh number 'shallow', 1 at the edge), so no cut edge of mirror is left. The
    see-through surface does not bend the light, so the lamps still light the stone under the water, which shows
    through darker by `tint`. Named '<material> • see-through 0.50'; made once, then shared; see 0 returns the material
    itself."""
    material = store.material(material) if isinstance(material, str) else material
    see = min(max(float(see), 0.0), 1.0)
    if see <= 0:
        return material
    name = '%s • see-through %.2f' % (material.name, see)
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_see_through_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_see_through_of'] = material.name
    copy['pp_see_through'] = see
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    shader = out.inputs['Surface'].links[0].from_socket
    clear = nodes.new('ShaderNodeBsdfTransparent')
    clear.inputs['Color'].default_value = (*[float(c) for c in tint], 1.0)
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.inputs['IOR'].default_value = float(glance)
    share = nodes.new('ShaderNodeMath')               # the mirror's share: 1 - see looking down, rising at a glance
    share.operation = 'MULTIPLY_ADD'
    share.use_clamp = True
    links.new(fresnel.outputs['Fac'], share.inputs[0])
    share.inputs[1].default_value = see
    share.inputs[2].default_value = 1.0 - see
    fac = share.outputs[0]
    if edge:
        shallow = nodes.new('ShaderNodeAttribute')
        shallow.attribute_type = 'GEOMETRY'
        shallow.attribute_name = 'shallow'
        fade = nodes.new('ShaderNodeMapRange')          # the mirror fades out over the shallow edge, keeping a little
        fade.inputs['From Min'].default_value = 0.35
        fade.inputs['From Max'].default_value = 1.0
        fade.inputs['To Min'].default_value = 1.0
        fade.inputs['To Max'].default_value = 0.12
        links.new(shallow.outputs['Fac'], fade.inputs['Value'])
        times = nodes.new('ShaderNodeMath')
        times.operation = 'MULTIPLY'
        links.new(fac, times.inputs[0])
        links.new(fade.outputs['Result'], times.inputs[1])
        fac = times.outputs[0]
    mix = nodes.new('ShaderNodeMixShader')
    mix.name = mix.label = 'See through'
    links.new(fac, mix.inputs['Fac'])
    links.new(clear.outputs['BSDF'], mix.inputs[1])
    links.new(shader, mix.inputs[2])
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return copy


see_through_copy = see_through      # make()'s option of the same name hides the function inside make()


def no_ring_film(material):
    """A copy of a wet-film material that darkens the ground without the broad glossy shine (rough 0.1 to 0.6) that
    draws a pale ring round the water under a lamp: rough and matte like damp soil, its darkening kept. Named
    '<material> • no ring'; made once, then shared."""
    material = store.material(material) if isinstance(material, str) else material
    name = '%s • no ring' % material.name
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_no_ring_of') == material.name:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_no_ring_of'] = material.name
    if copy.use_nodes and copy.node_tree is not None:
        nodes, links = copy.node_tree.nodes, copy.node_tree.links
        for node in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
            rough = node.inputs['Roughness']
            for link in list(rough.links):
                links.remove(link)
            rough.default_value = 0.85
            node.inputs['Specular IOR Level'].default_value = 0.2
            if node.inputs['Normal'].links:
                links.remove(node.inputs['Normal'].links[0])
    return copy


ANGLES = 160          # points round the outline
WATER_RINGS = 14
FILM_INNER_RINGS = 3  # rings of film under the water's rim (dry = 0 there)
FILM_OUTER_RINGS = 9


# ----------------------------------------------------------------------------------------------- the outline

def _loop_noise(angle, frequency, offset):
    """Smooth noise round a closed loop (about -0.5 to 0.5): sampled on a circle, so it joins up with itself."""
    return noise.noise(Vector((math.cos(angle) * frequency + offset.x, math.sin(angle) * frequency + offset.y, offset.z)))


def _outline(length, width, rng, raggedness):
    """The water's rim: ANGLES points (x, y) in the puddle's own frame (x along its length), ragged at every scale."""
    offsets = [Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50))) for _ in range(5)]
    angles = [math.tau * k / ANGLES for k in range(ANGLES)]
    inlets = [(rng.uniform(0, math.tau), rng.uniform(0.12, 0.32), rng.uniform(0.10, 0.24)) for _ in range(rng.randint(2, 4))]
    spits = [(rng.uniform(0, math.tau), rng.uniform(0.10, 0.22), rng.uniform(0.08, 0.18)) for _ in range(rng.randint(1, 3))]
    long_and_thin = length / max(width, 1e-6) > 1.6
    points = []
    for k, a in enumerate(angles):
        r = 1.0
        r += raggedness * (0.42 * _loop_noise(a, 1.2, offsets[0]) + 0.20 * _loop_noise(a, 2.9, offsets[1])
                           + 0.09 * _loop_noise(a, 7.0, offsets[2]) + 0.045 * _loop_noise(a, 17.0, offsets[3]))
        r += raggedness * rng.uniform(-0.012, 0.012)                   # the broken edge, point by point
        for centre, spread, depth in inlets:                           # bays where higher ground pushes in
            gap = math.atan2(math.sin(a - centre), math.cos(a - centre))
            r -= raggedness * depth * math.exp(-(gap / spread) ** 2)
        for centre, spread, reach in spits:                            # tongues of water running out
            gap = math.atan2(math.sin(a - centre), math.cos(a - centre))
            r += raggedness * reach * math.exp(-(gap / spread) ** 2)
        r = max(r, 0.42)
        x, y = 0.5 * length * r * math.cos(a), 0.5 * width * r * math.sin(a)
        if long_and_thin:                                              # a rut puddle pinches and swells along its length
            y *= 1.0 + 0.32 * raggedness * noise.noise(Vector((x / max(width, 0.2) * 0.9 + offsets[4].x, offsets[4].y, offsets[4].z)))
        points.append((x, y))
    return numpy.array(points, dtype=numpy.float64)


def _distance_to_loop(points, loop):
    """Shortest distance (metres) from each point to the closed loop of segments."""
    a = loop
    b = numpy.roll(loop, -1, axis=0)
    ab = b - a
    length2 = numpy.maximum((ab ** 2).sum(axis=1), 1e-12)
    p = points[:, None, :]
    t = numpy.clip(((p - a[None]) * ab[None]).sum(axis=2) / length2[None], 0.0, 1.0)
    nearest = a[None] + t[..., None] * ab[None]
    return numpy.sqrt(((p - nearest) ** 2).sum(axis=2)).min(axis=1)


def _bump_window(value):
    return 4.0 * value * (1.0 - value)


# ----------------------------------------------------------------------------------------------- the ground

class _Ground:
    """Heights of the ground under points of the world: your ground object (rays cast straight down), or flat."""

    def __init__(self, ground, flat_z):
        self.ground = ground
        self.flat_z = flat_z
        if ground is not None:
            if ground.type != 'MESH':
                raise ValueError('ground must be a mesh object')
            bpy.context.view_layer.update()
            self.depsgraph = bpy.context.evaluated_depsgraph_get()
            self.to_local = ground.matrix_world.inverted()
            self.down = (self.to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
            corners = [ground.matrix_world @ Vector(c) for c in ground.bound_box]
            self.above = max(c.z for c in corners) + 1.0

    def heights(self, xy):
        if self.ground is None:
            return numpy.full(len(xy), self.flat_z, dtype=numpy.float64)
        result = numpy.full(len(xy), numpy.nan, dtype=numpy.float64)
        matrix = self.ground.matrix_world
        for index, (x, y) in enumerate(xy):
            start = self.to_local @ Vector((x, y, self.above))
            hit, location, _, _ = self.ground.ray_cast(start, self.down, distance=1.0e5, depsgraph=self.depsgraph)
            if hit:
                result[index] = (matrix @ location).z
        if numpy.isnan(result).all():
            hint = ''
            if not self.ground.data.polygons:
                hint = (' (it has no faces of its own: setts and flags are drawn as copies that rays cannot hit; give the road '
                        'or nothing as ground, and level= the height of the water)')
            raise ValueError('rays cast straight down at the puddle found no face of the ground object %r%s' % (self.ground.name, hint))
        result[numpy.isnan(result)] = numpy.nanmean(result)
        return result


def _level(ground, centre, half_extent, radius, cell=0.03):
    """The water's level under each point: the ground smoothed over `radius` metres, so the water lies flat over small
    hollows but still follows the ground's slope. Returns a function (xy array) -> heights."""
    if ground.ground is None:
        return lambda xy: numpy.full(len(xy), ground.flat_z, dtype=numpy.float64)
    nx = max(4, int(math.ceil(2 * half_extent[0] / cell)) + 1)
    ny = max(4, int(math.ceil(2 * half_extent[1] / cell)) + 1)
    xs = numpy.linspace(centre[0] - half_extent[0], centre[0] + half_extent[0], nx)
    ys = numpy.linspace(centre[1] - half_extent[1], centre[1] + half_extent[1], ny)
    grid_x, grid_y = numpy.meshgrid(xs, ys)
    heights = ground.heights(numpy.stack([grid_x.ravel(), grid_y.ravel()], axis=1)).reshape(ny, nx)
    sigma = max(radius / cell, 0.5)
    reach = int(math.ceil(3 * sigma))
    kernel = numpy.exp(-0.5 * (numpy.arange(-reach, reach + 1) / sigma) ** 2)
    kernel /= kernel.sum()
    padded = numpy.pad(heights, reach, mode='edge')
    smooth = numpy.apply_along_axis(lambda row: numpy.convolve(row, kernel, mode='valid'), 1, padded)
    smooth = numpy.apply_along_axis(lambda column: numpy.convolve(column, kernel, mode='valid'), 0, smooth)

    def sample(xy):
        fx = numpy.clip((xy[:, 0] - xs[0]) / (xs[1] - xs[0]), 0, nx - 1.001)
        fy = numpy.clip((xy[:, 1] - ys[0]) / (ys[1] - ys[0]), 0, ny - 1.001)
        ix, iy = fx.astype(int), fy.astype(int)
        tx, ty = fx - ix, fy - iy
        return (smooth[iy, ix] * (1 - tx) * (1 - ty) + smooth[iy, ix + 1] * tx * (1 - ty)
                + smooth[iy + 1, ix] * (1 - tx) * ty + smooth[iy + 1, ix + 1] * tx * ty)
    return sample


# ----------------------------------------------------------------------------------------------- the sheets

def _rings_mesh(name, rings_xyz, values, attribute, centre_point=None, centre_value=None):
    """A sheet of rings round the puddle (each ring ANGLES points), faces up; optionally a middle point fanning out."""
    verts, faces, numbers = [], [], []
    if centre_point is not None:
        verts.append(tuple(centre_point))
        numbers.append(centre_value)
    first_ring = len(verts)
    for ring, ring_values in zip(rings_xyz, values):
        verts.extend(tuple(p) for p in ring)
        numbers.extend(float(v) for v in ring_values)
    if centre_point is not None:
        for k in range(ANGLES):
            faces.append((0, first_ring + k, first_ring + (k + 1) % ANGLES))
    for ring in range(len(rings_xyz) - 1):
        inner, outer = first_ring + ring * ANGLES, first_ring + (ring + 1) * ANGLES
        for k in range(ANGLES):
            k1 = (k + 1) % ANGLES
            faces.append((inner + k, outer + k, outer + k1, inner + k1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    layer = mesh.attributes.new(attribute, 'FLOAT', 'POINT')
    layer.data.foreach_set('value', numbers)
    mesh.update()
    mesh.shade_smooth()
    return mesh


def make(location, size=(1.2, 1.0), turn=0.0, ground=None, seed=0, collection=None, water_material=WATER_MATERIAL,
         film_material=FILM_MATERIAL, lift=0.004, film_reach=None, raggedness=1.0, shallow_band=None, level=None, film=True,
         mirror=0.0, no_ring=False, see_through=0.0):
    """Make one puddle with its middle at `location`. Returns (water, film): the objects 'puddle water' and
    'puddle wet film' (film is None with film=False: the ground tool's soil wets its own ground round the water). With `level` (a height in metres), the water lies flat at that height instead of on the ground:
    for a puddle among setts, give level about 2 mm above the stones' tops (the setts object's 'top_height'): the water covers
    most stones and the highest stand out of it; a centimetre lower, water shows only in the joints. `mirror` (0 to 1) gives the
    water a copy of its material that mirrors the sky more strongly; `no_ring` gives the film a matte copy that draws no pale
    ring round the water under a lamp and keeps the clear rim narrow. `see_through` (0 to 1) makes the water semi
    transparent, the stone or ground under it showing through (0.5: half, looking straight down; more mirror at a
    glancing look; the lamps still light what is under it): for a puddle on stone paving. All three are off by default:
    the puddle is as it always was."""
    see_through = float(see_through)
    if not 0.0 <= see_through <= 1.0:
        raise ValueError('see_through is 0 (the water as it always was) to 1 (all see-through), not %r' % (see_through,))
    length, width = float(size[0]), float(size[1])
    if length < width:
        length, width, turn = width, length, turn + 90.0
    rng = random.Random(seed)
    location = Vector(location)
    half_width = width / 2
    band = shallow_band if shallow_band is not None else min(0.22, max(0.05, 0.4 * half_width))
    if no_ring and shallow_band is None:                               # a narrow clear rim: no pale outline under a lamp
        band = 0.04
    reach = film_reach if film_reach is not None else min(0.4, max(0.12, 0.3 * half_width + 0.08))
    rim = _outline(length, width, rng, raggedness)                     # the puddle's own frame: x along its length
    turning = Matrix.Rotation(math.radians(turn), 2)
    to_world = numpy.array([[turning[0][0], turning[0][1]], [turning[1][0], turning[1][1]]])
    if ground is not None and level is None and ground.get('lay_cobbles_lowered'):
        raise ValueError("setts are laid on %r: its surface is now the bed under the stones, so water draped on it would lie "
                         "hidden under them; give level= instead (the setts object's 'top_height' plus about 0.002)" % ground.name)
    floor = _Ground(ground, location.z)

    # water: rings from the middle out to the rim, denser towards the rim where it turns clear
    fractions = [(i / WATER_RINGS) ** 0.75 for i in range(1, WATER_RINGS + 1)]
    water_local = [rim * f for f in fractions]
    flat = numpy.concatenate(water_local)
    to_rim = _distance_to_loop(flat, rim)
    shallow = numpy.clip(1.0 - to_rim / band, 0.0, 1.0) ** 0.6        # rises quickly: a wide, gradual clear rim
    world_xy = flat @ to_world.T + numpy.array([location.x, location.y])
    wobble = numpy.array([noise.noise(Vector((x * 2.6 + seed * 7.13, y * 2.6, 3.7))) for x, y in world_xy])
    shallow = numpy.clip(shallow + 0.35 * wobble * _bump_window(shallow), 0.0, 1.0)
    shallow[-ANGLES:] = 1.0                                             # the rim itself is clear

    # film: from well inside the water (hidden under it) out past the rim to its own ragged edge
    directions = rim / numpy.maximum(numpy.linalg.norm(rim, axis=1, keepdims=True), 1e-9)
    offsets = [Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50))) for _ in range(2)]
    angles = [math.tau * k / ANGLES for k in range(ANGLES)]
    spread = numpy.array([0.62 + raggedness * (0.9 * _loop_noise(a, 1.6, offsets[0]) + 0.35 * _loop_noise(a, 6.0, offsets[1]))
                          + raggedness * rng.uniform(-0.05, 0.05) for a in angles])
    film_reach_here = reach * numpy.clip(spread, 0.3, 1.4)
    film_local, film_dry = [], []
    for j in range(FILM_INNER_RINGS):
        film_local.append(rim * (0.55 + 0.45 * j / FILM_INNER_RINGS))
        film_dry.append(numpy.zeros(ANGLES))
    for j in range(FILM_OUTER_RINGS + 1):
        t = j / FILM_OUTER_RINGS
        film_local.append(rim + directions * (film_reach_here * t)[:, None])
        film_dry.append(numpy.full(ANGLES, t))
    film_flat = numpy.concatenate(film_local)
    film_world_xy = film_flat @ to_world.T + numpy.array([location.x, location.y])
    dry = numpy.concatenate(film_dry)
    patchy = numpy.array([noise.noise(Vector((x * 3.1 + 11.0, y * 3.1 - seed * 3.3, 8.1))) for x, y in film_world_xy])
    dry = numpy.clip(dry + 0.5 * patchy * _bump_window(dry), 0.0, 1.0)
    dry[:FILM_INNER_RINGS * ANGLES + ANGLES] = 0.0                    # under the water and right against it: wet
    dry[-ANGLES:] = 1.0                                                 # the film's own edge: dry

    # heights: draped on the ground; the water level over small hollows, bumps above it show through
    extent = numpy.abs(film_world_xy - numpy.array([location.x, location.y])).max(axis=0) + 0.1
    swell = numpy.array([noise.noise(Vector((x * 4.0 - seed * 1.7, y * 4.0, 5.3))) for x, y in world_xy])
    if level is None:
        level_at = _level(floor, (location.x, location.y), extent, radius=min(0.15, max(0.06, 0.45 * half_width)))
        under_water = floor.heights(world_xy)
        water_level = level_at(world_xy)
        above_level = numpy.clip((under_water - water_level - 0.002) / 0.006, 0.0, 1.0)
        shallow = numpy.maximum(shallow, above_level)
        water_z = numpy.maximum(under_water, water_level) + lift + 0.0005 * swell     # a sub-millimetre swell: reflections waver
        film_z = floor.heights(film_world_xy) + lift * 0.5
        centre_ground = float(floor.heights(numpy.array([[location.x, location.y]]))[0])
        centre_level = float(level_at(numpy.array([[location.x, location.y]]))[0])
    else:                    # flat water at the height given; whatever stands higher (stones, bumps) stands out of it
        level = float(level)
        if ground is not None:
            under_water = floor.heights(world_xy)
            # water shallower than 2 cm is clear: the bed shows through it, so the shore is soft wherever it falls
            shallow = numpy.maximum(shallow, 1.0 - numpy.clip((level - under_water) / 0.02, 0.0, 1.0))
            film_z = numpy.maximum(floor.heights(film_world_xy) + lift * 0.5, level - 0.0015)
        else:
            film_z = numpy.full(len(film_world_xy), level - 0.0015)
        water_z = level + 0.0005 * swell
        centre_ground = centre_level = level - lift
    origin = Vector((location.x, location.y, centre_ground))

    def rings(xy, z):
        points = numpy.column_stack([xy[:, 0] - origin.x, xy[:, 1] - origin.y, z - origin.z])
        return [points[i * ANGLES:(i + 1) * ANGLES] for i in range(len(points) // ANGLES)]

    water_values = [shallow[i * ANGLES:(i + 1) * ANGLES] for i in range(WATER_RINGS)]
    water_mesh = _rings_mesh('puddle water', rings(world_xy, water_z), water_values, 'shallow',
                             centre_point=(0.0, 0.0, max(centre_ground, centre_level) + lift - origin.z), centre_value=0.0)
    film_values = [dry[i * ANGLES:(i + 1) * ANGLES] for i in range(len(film_local))]
    film_mesh = _rings_mesh('puddle wet film', rings(film_world_xy, film_z), film_values, 'dry')

    if collection is None:
        collection = bpy.data.collections.new('puddle')
        bpy.context.scene.collection.children.link(collection)
    made = []
    if mirror and float(mirror) > 0:
        water_material = strong_mirror(water_material, mirror)
    if see_through > 0:
        water_material = see_through_copy(water_material, see_through)
    if no_ring:
        film_material = no_ring_film(film_material)
    sheets = ((water_mesh, water_material), (film_mesh, film_material)) if film else ((water_mesh, water_material),)
    if not film:
        bpy.data.meshes.remove(film_mesh)
    for mesh, material in sheets:
        obj = bpy.data.objects.new(mesh.name, mesh)
        collection.objects.link(obj)
        obj.location = origin
        obj.visible_shadow = False
        store.use_material(obj, store.material(material) if isinstance(material, str) else material, ground=centre_ground)
        made.append(obj)
    water = made[0]
    film_object = made[1] if film else None
    water['puddle_size'] = (length, width)
    water['puddle_seed'] = seed
    return water, film_object


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--at', type=float, nargs=3, metavar=('X', 'Y', 'Z'), help="the puddle's middle")
    parser.add_argument('--size', type=float, nargs=2, metavar=('LENGTH', 'WIDTH'), default=(1.2, 1.0), help='metres; default 1.2 1.0')
    parser.add_argument('--turn', type=float, default=0.0, help='degrees about Z; default 0')
    parser.add_argument('--ground', help='the ground object to drape the puddle onto (default: flat at Z)')
    parser.add_argument('--seed', type=int, default=0, help="the outline's bays and spits; default 0")
    parser.add_argument('--lift', type=float, default=0.004, help='metres the water sits above the ground; default 0.004')
    parser.add_argument('--level', type=float, default=None, help='a height: the water lies flat at it (a puddle among setts: 2 mm above the road height)')
    parser.add_argument('--shallow-band', type=float, default=None, help='metres of clear, shallow water at the rim; default from the size')
    parser.add_argument('--film-reach', type=float, default=None, help='metres the wet ground reaches past the water')
    parser.add_argument('--raggedness', type=float, default=1.0, help='0 smooth, 1 normal, 2 very broken; default 1')
    parser.add_argument('--mirror', type=float, default=0.0, help='how strongly the water mirrors the sky, 0 (as always) to 1; default 0')
    parser.add_argument('--no-ring', action='store_true', help='a matte wet film and a narrow clear rim: no pale ring round the water under a lamp')
    parser.add_argument('--see-through', type=float, default=0.0, help='how much of the ground under the water shows through, 0 (as always) to 1; 0.5 for a puddle on stone paving; default 0')
    parser.add_argument('--water-material', default=WATER_MATERIAL)
    parser.add_argument('--film-material', default=FILM_MATERIAL)
    parser.add_argument('--out', help='where to save the result (.blend)')
    args = parser.parse_args(argv)
    if not (args.blend and args.at and args.out):
        parser.error('--blend, --at and --out are needed to make a puddle')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    ground = None
    if args.ground:
        ground = bpy.data.objects.get(args.ground)
        if ground is None:
            parser.error('no object %r in %s' % (args.ground, args.blend))
    water, film = make(args.at, size=args.size, turn=args.turn, ground=ground, seed=args.seed, lift=args.lift, level=args.level,
                       shallow_band=args.shallow_band,
                       film_reach=args.film_reach, raggedness=args.raggedness, water_material=args.water_material,
                       film_material=args.film_material, mirror=args.mirror, no_ring=args.no_ring, see_through=args.see_through)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('made %s and %s, saved %s' % (water.name, film.name, args.out))


if __name__ == '__main__':
    main()
