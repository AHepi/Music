"""
What this file does: makes the ground a place stands on, and sets how wet it is. The ground is one finely divided sheet
with real height: soft swells and dips a metre or so across, a little hand-sized roughness, and, if you give it a line,
the camber of a road (its middle higher than its edges, which is what sheds water). Its soil is one material whose
wetness varies over it: when you set the place's wetness, water finds the low places first, so one ground holds all
four states at once (dry on the crowns, damp on the slopes, wet in the dips, standing water in the deepest), and the beds
of puddles that have dried show cracked mud. It decides nothing about where things go: the size, the line of the road
and the wetness are yours; the ground's own dips decide only where the water gathers.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import ground, puddle
    yard = ground.make(size=(14, 30), location=(0, 12, 0), relief=0.08,
                       camber=([(0, -3, 0), (0.6, 12, 0), (-0.4, 27, 0)], 4.0, 0.06), seed=3)
    spots = ground.wet(yard, wetness=0.6)                      # 0 dry .. 1 just rained; returns where water stands
    ground.fill(yard, spots)                                    # the puddle tool's water in those places (or choose some)

Lay tracks (the tracks tool) after wet() and before stones; call ground.spots(yard) at the end to get every puddle
spot, the tracks' included. To stand a part on the ground: store.add_part(name, location=(x, y, ground.height_at(yard, x, y))).

From the command line:

    python3 ground.py --help
    python3 ground.py --size 12 12 --wetness 0.6 --out ground.blend [--relief 0.08] [--seed 3] [--soil "dark dirt"]

make() options, with their defaults:
    size        (x, y) metres (12, 12)
    location    the middle of the ground (x, y, z) (0, 0, 0)
    cell        the size of its squares, metres (0.1); finer is smoother and heavier (tracks refine under themselves)
    relief      how much it rises and falls, metres (0.08); 0 is flat
    camber      a road's line, width and drop: (points, width, drop), or a list of them; the middle of the road is
                `drop` metres higher than its edges (none)
    seed        the same seed makes the same ground (0)
    soil        'dry dirt' (MADE • dirt), 'dark dirt' (MADE • dirt, dark), or any material name
    collection  where it goes (a new collection 'ground')
wet() options:
    wetness     0 dry, 0.3 damp, 0.6 after rain has drained, 1 just rained (0.5)
    pattern     'hollows' (the dips wetter than the crowns, after rain has drained) or 'even' (wet all over) ('hollows')
    crust       how strongly the dried beds of old puddles crack (1.0; 0 none)

The ground carries these numbers on each point, for the soil material and the other ground tools: 'hollow' (0 on the
crowns to 1 in the deepest dips), 'pool' (metres of water a dip would hold if full), 'wetness' (0 dry to 1; 0.86 and over
stands under water), 'crust', 'wear', and the tracks tool's 'tread', 'tread_u', 'tread_v', 'tread_kind', 'smear',
'track_wet', 'track_crust', 'drop_extra'.
"""

import argparse
import math
import os
import sys

import bpy
import numpy
from mathutils import Vector, noise

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402

TOOL = {
    'name': 'ground',
    'what': 'the ground: a finely divided sheet with soft dips and swells (and a road\'s camber if you give its line), its soil wet by height so one ground is dry, damp, wet and flooded at once',
    'call': "yard = ground.make(size=(14, 30), relief=0.08, seed=3); spots = ground.wet(yard, wetness=0.6)",
    'options': {
        'size': '(x, y) metres (12, 12)', 'location': 'its middle (0, 0, 0)',
        'cell': 'the size of its squares, metres (0.1)', 'relief': 'how much it rises and falls, metres (0.08)',
        'camber': 'a road: (points, width, drop) or a list of them; the road\'s middle drop metres above its edges (none)',
        'seed': 'the same seed, the same ground (0)', 'soil': "'dry dirt', 'dark dirt' or a material name ('dry dirt')",
        'wet(): wetness': '0 dry, 0.3 damp, 0.6 after rain has drained, 1 just rained (0.5)',
        'wet(): pattern': "'hollows' (dips wetter) or 'even' ('hollows')", 'wet(): crust': 'dried puddle beds crack, 0 to 1 (1.0)',
    },
    'materials': ['MADE • dirt', 'MADE • dirt, dark'],
    'source': 'the research of log 53 (how studios layer ground, how wet ground looks), made for the store',
    'trap': 'wet() only tells you where water stands (its spots); make the water with the puddle tool, level= the spot\'s level',
}

SOILS = {'dry dirt': 'MADE • dirt', 'dark dirt': 'MADE • dirt, dark'}
FLOODED = 0.86
POINT_NUMBERS = ('hollow', 'pool', 'water', 'pool_id', 'wetness', 'crust', 'wear', 'bare', 'tread', 'tread_u', 'tread_v',
                 'tread_kind', 'smear', 'track_wet', 'track_crust', 'drop_extra', 'soil_patch', 'soil_patch_on')
WATER_MATERIAL = 'MADE \u2022 puddle water'


# ----------------------------------------------------------------------------------------------- numbers on points

def numbers(mesh, name):
    """The float number `name` on every point of the mesh, as an array (zeros if it is not there)."""
    attribute = mesh.attributes.get(name)
    values = numpy.zeros(len(mesh.vertices), dtype=numpy.float64)
    if attribute is not None and attribute.domain == 'POINT' and attribute.data_type == 'FLOAT':
        buffer = numpy.zeros(len(mesh.vertices), dtype=numpy.float32)
        attribute.data.foreach_get('value', buffer)
        values[:] = buffer
    return values


def set_numbers(mesh, name, values):
    attribute = mesh.attributes.get(name)
    if attribute is None or attribute.domain != 'POINT' or attribute.data_type != 'FLOAT':
        if attribute is not None:
            mesh.attributes.remove(attribute)
        attribute = mesh.attributes.new(name, 'FLOAT', 'POINT')
    attribute.data.foreach_set('value', numpy.asarray(values, dtype=numpy.float32))


def world_points(obj):
    """Every point of the object's mesh in the world, as an (n, 3) array."""
    mesh = obj.data
    local = numpy.zeros(len(mesh.vertices) * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get('co', local)
    local = local.reshape(-1, 3)
    matrix = numpy.array(obj.matrix_world)
    return local @ matrix[:3, :3].T + matrix[:3, 3]


def set_world_heights(obj, heights):
    """Move every point of the object's mesh up or down so it stands at these world heights (the ground lies flat:
    turned about Z and scaled at most)."""
    mesh = obj.data
    local = numpy.zeros(len(mesh.vertices) * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get('co', local)
    local = local.reshape(-1, 3)
    matrix = numpy.array(obj.matrix_world)
    scale_z = numpy.linalg.norm(matrix[:3, 2]) or 1.0
    current = (local @ matrix[:3, :3].T + matrix[:3, 3])[:, 2]
    local[:, 2] += (numpy.asarray(heights) - current) / scale_z
    mesh.vertices.foreach_set('co', local.ravel())
    mesh.update()


def edges_of(mesh):
    edges = numpy.zeros(len(mesh.edges) * 2, dtype=numpy.int64)
    mesh.edges.foreach_get('vertices', edges)
    return edges.reshape(-1, 2)


def boundary_points(mesh):
    """The points on the open edge of the sheet (an edge used by one face only)."""
    loop_edges = numpy.zeros(len(mesh.loops), dtype=numpy.int64)
    mesh.loops.foreach_get('edge_index', loop_edges)
    use = numpy.bincount(loop_edges, minlength=len(mesh.edges))
    edges = edges_of(mesh)
    return numpy.unique(edges[use == 1].ravel())


def point_areas(mesh):
    """The ground area each point stands for (a share of the faces round it), square metres in the mesh's own units."""
    areas = numpy.zeros(len(mesh.polygons), dtype=numpy.float64)
    mesh.polygons.foreach_get('area', areas)
    totals = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
    mesh.polygons.foreach_get('loop_total', totals)
    loop_points = numpy.zeros(len(mesh.loops), dtype=numpy.int64)
    mesh.loops.foreach_get('vertex_index', loop_points)
    shares = numpy.repeat(areas / numpy.maximum(totals, 1), totals)
    result = numpy.zeros(len(mesh.vertices))
    numpy.add.at(result, loop_points, shares)
    return result


def _smoothstep(low, high, value):
    t = numpy.clip((numpy.asarray(value, dtype=numpy.float64) - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ----------------------------------------------------------------------------------------------- the sheet

def _grid_mesh(name, xs, ys, heights):
    nx, ny = len(xs), len(ys)
    grid_x, grid_y = numpy.meshgrid(xs, ys)
    points = numpy.column_stack([grid_x.ravel(), grid_y.ravel(), heights.ravel()])
    i, j = numpy.meshgrid(numpy.arange(nx - 1), numpy.arange(ny - 1))
    a = (j * nx + i).ravel()
    quads = numpy.column_stack([a, a + 1, a + nx + 1, a + nx])          # counter-clockwise seen from above: facing up
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set('co', points.astype(numpy.float32).ravel())
    mesh.loops.add(quads.size)
    mesh.loops.foreach_set('vertex_index', quads.astype(numpy.int32).ravel())
    mesh.polygons.add(len(quads))
    mesh.polygons.foreach_set('loop_start', numpy.arange(0, quads.size, 4, dtype=numpy.int32))
    mesh.update(calc_edges=True)
    mesh.validate()
    try:
        mesh.shade_smooth()
    except AttributeError:
        mesh.polygons.foreach_set('use_smooth', numpy.ones(len(mesh.polygons), dtype=bool))
    return mesh


def _relief(xy, relief, seed):
    """Soft swells and dips a metre or two across, and a little hand-sized roughness."""
    swell = numpy.array([noise.fractal(Vector((x / 1.7, y / 1.7, seed * 7.13)), 1.0, 2.0, 3) for x, y in xy])
    swell = (swell - swell.mean()) / max(swell.std(), 1e-9)
    rough = numpy.array([noise.noise(Vector((x / 0.35, y / 0.35, seed * 3.31 + 50.0))) for x, y in xy])
    return swell * relief * 0.3 + rough * relief * 0.06


def _camber(xy, cambers):
    lift = numpy.zeros(len(xy))
    if not cambers:
        return lift
    if not isinstance(cambers, list) or (cambers and not isinstance(cambers[0], (list, tuple))) or \
            (len(cambers) == 3 and isinstance(cambers[1], (int, float))):
        cambers = [cambers]
    for points, width, drop in cambers:
        path = _lines.Path(_lines.line_points(points)).smooth(0.1)
        along, across, _ = path.project(xy)
        half = width / 2.0
        inside = numpy.clip(1.0 - (across / half) ** 2, 0.0, None)
        beyond = (along < 0) | (along > path.total)
        fade = numpy.where(beyond, numpy.clip(1.0 - numpy.maximum(-along, along - path.total) / max(half, 0.5), 0.0, 1.0), 1.0)
        lift += drop * inside * fade
    return lift


def make(size=(12.0, 12.0), location=(0.0, 0.0, 0.0), cell=0.1, relief=0.08, camber=None, seed=0, soil='dry dirt',
         collection=None, name='ground'):
    """Make the ground and return it (dry until you call wet())."""
    size_x, size_y = float(size[0]), float(size[1])
    nx = max(2, int(round(size_x / cell)) + 1)
    ny = max(2, int(round(size_y / cell)) + 1)
    xs = numpy.linspace(-size_x / 2, size_x / 2, nx)
    ys = numpy.linspace(-size_y / 2, size_y / 2, ny)
    grid_x, grid_y = numpy.meshgrid(xs + location[0], ys + location[1])
    xy = numpy.column_stack([grid_x.ravel(), grid_y.ravel()])
    heights = _relief(xy, relief, seed) + _camber(xy, camber)
    mesh = _grid_mesh(name, xs, ys, heights.reshape(ny, nx))
    obj = bpy.data.objects.new(name, mesh)
    obj.location = tuple(float(v) for v in location)
    obj['store_ground'] = True
    obj['relief'] = float(relief)
    obj['hollow_scale'] = max(0.012, 0.3 * float(relief))
    obj['cell'] = float(cell)
    if collection is None:
        collection = bpy.data.collections.new('ground')
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)
    for number in POINT_NUMBERS:
        set_numbers(mesh, number, numpy.zeros(len(mesh.vertices)))
    _set_soil_patches(obj, seed)
    store.use_material(obj, SOILS.get(soil, soil), ground=location[2])
    bpy.context.view_layer.update()
    wet(obj, 0.0)
    return obj


def _set_soil_patches(obj, seed):
    """Where the soil's second photograph shows (0..1, in patches metres across): the soil material and detail() both
    follow it, so a lump in the ground and the photograph's colour stay together."""
    import _noise
    points = world_points(obj)
    wander = 0.5 + 0.5 * _noise.wander(points[:, 0], points[:, 1], scale=4.5, seed=int(seed) + 501, layers=3)
    set_numbers(obj.data, 'soil_patch', _smoothstep(0.38, 0.66, wander))
    set_numbers(obj.data, 'soil_patch_on', numpy.ones(len(points)))


# ----------------------------------------------------------------------------------------------- finer ground, real lumps

def refine(ground, inside, detail):
    """Divide the ground's faces where inside(xy) is true until they are about `detail` metres across (the numbers on
    the points are carried onto the new points). Returns how many faces were divided."""
    import bmesh
    mesh = ground.data
    matrix = numpy.array(ground.matrix_world)
    stretch = numpy.linalg.norm(matrix[:3, 0]) * numpy.linalg.norm(matrix[:3, 1])
    divided = 0
    for _ in range(3):                                         # faces of different sizes are divided in turn
        count = len(mesh.polygons)
        centres = numpy.zeros(count * 3)
        mesh.polygons.foreach_get('center', centres)
        world = centres.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
        areas = numpy.zeros(count)
        mesh.polygons.foreach_get('area', areas)
        sizes = numpy.sqrt(areas * stretch)
        want = (sizes > detail * 1.6) & inside(world[:, :2])
        if not want.any():
            break
        group = want & (sizes >= sizes[want].max() * 0.66)
        cuts = int(max(1, round(float(numpy.median(sizes[group])) / detail) - 1))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        chosen = [bm.faces[i] for i in numpy.flatnonzero(group)]
        edges = list({edge for face in chosen for edge in face.edges})
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True, quad_corner_type='STRAIGHT_CUT')
        many_sided = [face for face in bm.faces if len(face.verts) > 4]
        if many_sided:
            bmesh.ops.triangulate(bm, faces=many_sided, quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        divided += int(group.sum())
    return divided


_HEIGHT_PHOTOS = {}


def _height_photo(relative):
    """A height photograph from the shelf as an array of 0..1 (its rows from the bottom up, as the material reads it)."""
    if relative not in _HEIGHT_PHOTOS:
        from PIL import Image
        picture = Image.open(os.path.join(store.SHELF, relative)).convert('F')
        _HEIGHT_PHOTOS[relative] = numpy.flipud(numpy.asarray(picture, dtype=numpy.float64) / 255.0)
    return _HEIGHT_PHOTOS[relative]


def _photo_heights(photo, local_xy, size, turn, shift):
    """The photo's height (0..1) at points given in the ground's own coordinates, laid as the soil material lays it from
    above: one copy every `size` metres, turned and shifted."""
    from scipy import ndimage
    u = local_xy[:, 0] / size[0]                               # the material's coordinates use the width both ways from above
    v = local_xy[:, 1] / size[0]
    if turn or any(shift[:2]):
        cos, sin = math.cos(turn), math.sin(turn)
        u, v = cos * u - sin * v + shift[0], sin * u + cos * v + shift[1]
    rows, columns = photo.shape
    coordinates = numpy.vstack([numpy.mod(v, 1.0) * rows - 0.5, numpy.mod(u, 1.0) * columns - 0.5])
    return ndimage.map_coordinates(photo, coordinates, order=1, mode='grid-wrap')


def detail(ground, area=None, cell=0.015, strength=1.0):
    """Divide the ground finely within the area you give (where the camera is near) and push its surface up and down by
    its own soil photographs' height pictures, so their lumps, clods and boot marks are real and cast shadows: the
    same photographs and the same places the soil material shows them (churned mud where tracks left bare earth).
    Call it after the tracks and before grass, stones, litter and the water. Returns how many points moved."""
    import json
    import stones
    material = ground.data.materials[0] if ground.data.materials else None
    photos = json.loads(material.get('store_photos', 'null')) if material is not None else None
    if not photos:
        raise ValueError('the ground\'s soil is not one of the ground tool\'s soils (it records no photographs to follow)')
    if not 0.004 <= float(cell) <= 0.1:
        raise ValueError('cell is 0.004 to 0.1 metres, not %r' % (cell,))
    weigh, _box = stones._area(area)
    refine(ground, lambda xy: weigh(xy) > 0.5, float(cell))
    mesh = ground.data
    points = world_points(ground)
    inside = weigh(points[:, :2]) > 0.0
    if not inside.any():
        return 0
    local = numpy.zeros(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', local)
    local = local.reshape(-1, 3)[inside, :2]
    patch = numbers(mesh, 'soil_patch')[inside] * float(photos['second_weight'])
    churn = _smoothstep(0.15, 0.6, numbers(mesh, 'bare')[inside])
    lifted = numpy.zeros(len(local))
    for key, weight, turn, shift in ((photos['first'], (1.0 - patch) * (1.0 - churn), 0.0, (0.0, 0.0, 0.0)),
                                     (photos['second'], patch * (1.0 - churn), photos['second_turn'], photos['second_shift']),
                                     (photos['churned'], churn, photos['churned_turn'], photos['churned_shift'])):
        heights = _photo_heights(_height_photo(photos['heights'][key]), local, photos['sizes'][key], turn, shift)
        lifted += weight * (heights - 0.5) * float(photos['depths'][key])
    lifted *= float(strength)
    heights = points[:, 2].copy()
    heights[inside] += lifted * numpy.clip(weigh(points[inside, :2]), 0.0, 1.0)
    set_world_heights(ground, heights)
    ground['detailed'] = True
    return int(inside.sum())


# ----------------------------------------------------------------------------------------------- where water goes

def _blurred(points, sigma, cell=0.1):
    """The heights smoothed over about `sigma` metres (what the ground round each point is like)."""
    from scipy import ndimage
    low = points[:, :2].min(axis=0)
    shape = (numpy.ceil((points[:, :2].max(axis=0) - low) / cell).astype(int) + 1)[::-1]   # rows are y
    column = numpy.clip(((points[:, 0] - low[0]) / cell).astype(int), 0, shape[1] - 1)
    row = numpy.clip(((points[:, 1] - low[1]) / cell).astype(int), 0, shape[0] - 1)
    flat = row * shape[1] + column
    sums = numpy.bincount(flat, weights=points[:, 2], minlength=shape[0] * shape[1]).reshape(shape)
    counts = numpy.bincount(flat, minlength=shape[0] * shape[1]).reshape(shape).astype(float)
    spread = sigma / cell
    smooth_sums = ndimage.gaussian_filter(sums, spread, mode='nearest')
    smooth_counts = ndimage.gaussian_filter(counts, spread, mode='nearest')
    field = smooth_sums / numpy.maximum(smooth_counts, 1e-9)
    coordinates = numpy.vstack([(points[:, 1] - low[1]) / cell - 0.5, (points[:, 0] - low[0]) / cell - 0.5])
    return ndimage.map_coordinates(field, coordinates, order=1, mode='nearest')


def _filled(heights, edges, outlets):
    """The height water would stand at on every point if every dip were full: it drains off the sheet's open edge."""
    import heapq
    count = len(heights)
    ends = numpy.concatenate([edges[:, 0], edges[:, 1]])
    others = numpy.concatenate([edges[:, 1], edges[:, 0]])
    order = numpy.argsort(ends, kind='stable')
    others = others[order].tolist()
    starts = numpy.searchsorted(ends[order], numpy.arange(count + 1)).tolist()
    filled = heights.tolist()
    done = bytearray(count)
    queue = [(filled[i], i) for i in outlets.tolist()]
    heapq.heapify(queue)
    for i in outlets.tolist():
        done[i] = 1
    pop, push = heapq.heappop, heapq.heappush
    while queue:
        level, i = pop(queue)
        for k in range(starts[i], starts[i + 1]):
            j = others[k]
            if not done[j]:
                done[j] = 1
                if filled[j] < level:
                    filled[j] = level
                push(queue, (filled[j], j))
    return numpy.array(filled)


def _groups(mask, edges):
    """Which connected group each marked point belongs to (-1 for unmarked points), joined along the mesh's edges."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    index = numpy.full(len(mask), -1, dtype=numpy.int64)
    marked = numpy.flatnonzero(mask)
    index[marked] = numpy.arange(len(marked))
    if not len(marked):
        return index, 0
    both = mask[edges[:, 0]] & mask[edges[:, 1]]
    pairs = edges[both]
    graph = coo_matrix((numpy.ones(len(pairs)), (index[pairs[:, 0]], index[pairs[:, 1]])), shape=(len(marked), len(marked)))
    count, labels = connected_components(graph, directed=False)
    result = numpy.full(len(mask), -1, dtype=numpy.int64)
    result[marked] = labels
    return result, count


def wet(ground, wetness=0.5, pattern='hollows', crust=1.0):
    """Set how wet the ground is (0 dry .. 1 just rained). Returns the places water stands, largest first: a list of
    {'location', 'size', 'turn', 'level', 'depth', 'area', ...}, one for each dip holding water, for fill() (or for
    puddle.make(location, size=, turn=, ground=, level=) if you prefer the puddle tool's outline). Call it again after
    laying tracks: the tracks' dips fill too."""
    if pattern not in ('hollows', 'even'):
        raise ValueError("pattern is 'hollows' or 'even', not %r" % pattern)
    w = float(numpy.clip(wetness, 0.0, 1.0))
    mesh = ground.data
    bpy.context.view_layer.update()
    points = world_points(ground)
    heights = points[:, 2]
    edges = edges_of(mesh)
    if 'hollow_scale' not in ground:
        spread = _blurred(points, 0.8) - heights
        ground['hollow_scale'] = float(max(0.012, numpy.percentile(spread, 98)))
    relief = float(ground.get('relief', 0.08))
    hollow = numpy.clip((_blurred(points, 0.8) - heights) / float(ground['hollow_scale']), 0.0, 1.0)

    outlets = boundary_points(mesh)
    filled = _filled(heights, edges, outlets) if len(outlets) else heights.copy()
    pool = numpy.clip(filled - heights, 0.0, None)

    crown = float(numpy.clip(1.25 * w - 0.6, 0.0, 0.75))
    dip = float(min(0.84, 1.4 * w))
    if pattern == 'even':
        speckle = numpy.array([noise.noise(Vector((x * 1.3, y * 1.3, 9.1))) for x, y in points[:, :2]])
        base = numpy.clip(w * 0.84 + speckle * 0.05, 0.0, 0.84)
    else:
        base = crown + (dip - crown) * hollow ** 0.8

    # standing water: every dip is full just after rain; as the place dries its water level drops. A track may hold
    # its water lower (drop_extra, written by the tracks tool by its age).
    drop = (1.0 - w) ** 0.46 * max(0.025, 0.72 * relief)
    drop += 0.5 * (1.0 - min(w / 0.12, 1.0)) ** 2               # ground long dry (0 to about 0.1) holds no water at all
    extra = numpy.clip(numpy.nan_to_num(numbers(mesh, 'drop_extra')), 0.0, None)
    pooled = pool > 1e-4
    group, count = _groups(pooled, edges)
    level = numpy.full(len(heights), -numpy.inf)
    if count:
        members = group[pooled]
        spill = numpy.zeros(count)
        numpy.maximum.at(spill, members, filled[pooled])
        held = numpy.zeros(count)
        numpy.maximum.at(held, members, extra[pooled])
        level[pooled] = spill[members] - drop - held[members]
    water = numpy.where(pooled, numpy.clip(level - heights, 0.0, None), 0.0)
    flooded = water > 0.002

    # the bed of a dip just above its water is freshly wet; the bed long since uncovered has dried and cracked
    above = numpy.where(pooled, numpy.clip(heights - level, 0.0, None), numpy.inf)
    recent = numpy.where(pooled, numpy.exp(-above / 0.012), 0.0)
    in_bed = _smoothstep(0.002, 0.008, pool)
    ring = (0.45 + 0.4 * recent) * _smoothstep(0.15, 0.6, w) * in_bed * recent ** 0.25
    track_wet = numpy.clip(numbers(mesh, 'track_wet'), 0.0, 1.0)
    cracked = crust * _smoothstep(0.006, 0.02, pool) * (1.0 - recent) * (1.0 - _smoothstep(0.3, 0.7, base))
    cracked = cracked * _smoothstep(0.3, 0.7, hollow) * (1.0 - _smoothstep(0.02, 0.15, track_wet))   # beds, not the walls of a fresh rut
    wet_values = numpy.maximum(base, ring)
    wet_values = numpy.minimum(0.84, wet_values + track_wet)
    wet_values = numpy.where(flooded, 1.0, wet_values)
    crust_values = numpy.where(flooded, 0.0, numpy.maximum(cracked, numpy.clip(numbers(mesh, 'track_crust'), 0.0, 1.0)))

    set_numbers(mesh, 'hollow', hollow)
    set_numbers(mesh, 'pool', pool)
    set_numbers(mesh, 'water', water)
    set_numbers(mesh, 'pool_id', numpy.where(water > 0.0, group + 1.0, 0.0) if count else numpy.zeros(len(heights)))
    set_numbers(mesh, 'wetness', wet_values)
    set_numbers(mesh, 'crust', crust_values)
    ground['wetness_dial'] = w
    ground['wetness_pattern'] = pattern
    ground['crust_dial'] = float(crust)
    ground['water_stamp'] = int(ground.get('water_stamp', 0)) + 1
    mesh.update()
    return _spots(mesh, points, water, group, level, int(ground['water_stamp']))


def _spots(mesh, points, water, group, level, stamp):
    """The water of each dip that holds some, as one place each: where, how big, its level, and the points under it."""
    wet_points = water > 0.002
    if not wet_points.any():
        return []
    areas = point_areas(mesh)
    found = []
    for label in numpy.unique(group[wet_points]):
        members = numpy.flatnonzero(wet_points & (group == label))
        area = float(areas[members].sum())
        depth = float(water[members].max())
        if area < 0.02 or depth < 0.004:
            continue
        xy = points[members, :2]
        weights = areas[members] / max(area, 1e-12)
        centre = (xy * weights[:, None]).sum(axis=0)
        spread = numpy.cov((xy - centre).T, aweights=weights) if len(members) > 2 else numpy.eye(2) * 1e-4
        values, vectors = numpy.linalg.eigh(numpy.atleast_2d(spread))
        major = vectors[:, -1]
        along = (xy - centre) @ major
        across = (xy - centre) @ numpy.array([-major[1], major[0]])
        length = float(along.max() - along.min())
        width = float(across.max() - across.min())
        centre = centre + major * (along.max() + along.min()) / 2 + numpy.array([-major[1], major[0]]) * (across.max() + across.min()) / 2
        water_level = float(level[members].max())
        found.append({'location': (float(centre[0]), float(centre[1]), water_level),
                      'size': (round(length * 1.6 + 0.2, 3), round(width * 1.6 + 0.2, 3)),     # the outline covers every corner
                      'turn': round(math.degrees(math.atan2(major[1], major[0])), 2),
                      'level': water_level, 'depth': round(depth, 4), 'area': round(area, 4),
                      'pool': int(label) + 1, 'stamp': stamp, 'mesh_points': len(mesh.vertices)})
    found.sort(key=lambda spot: -spot['area'])
    return found


def _face_arrays(mesh):
    corners = numpy.zeros(len(mesh.loops), dtype=numpy.int64)
    mesh.loops.foreach_get('vertex_index', corners)
    starts = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
    mesh.polygons.foreach_get('loop_start', starts)
    totals = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
    mesh.polygons.foreach_get('loop_total', totals)
    return corners, starts, totals


def fill(ground, spots, seed=0, collection=None, material=WATER_MATERIAL, rain=0.0):
    """Put water in the places you pass (some or all of the spots wet() or spots() returned): for each, a flat sheet at
    its water level cut from the ground's own faces round the water, so it takes the true shape of the dip, never
    reaches another dip or past the ground's edge, and is hidden by the ground wherever the ground stands higher. It is
    clear where it is shallow, so the mud shows through at its edge. rain (0 none .. 1 steady rain) rings the water
    with spreading drops. Returns the water objects."""
    mesh = ground.data
    stamp = ground.get('water_stamp')
    for spot in spots:
        if spot.get('stamp') != stamp or spot.get('mesh_points') != len(mesh.vertices):
            raise ValueError('the ground has changed since these spots were found (tracks carved, or wet again): '
                             'call ground.spots(ground) again and fill those')
    if collection is None:
        collection = bpy.data.collections.new('ground water')
        bpy.context.scene.collection.children.link(collection)
    points = world_points(ground)
    pool_id = numbers(mesh, 'pool_id')
    water = numbers(mesh, 'water')
    corners, starts, totals = _face_arrays(mesh)
    face_of_corner = numpy.repeat(numpy.arange(len(starts)), totals)
    water_material = store.material(material) if isinstance(material, str) else material
    if rain > 0.0 and 'Rain' in water_material.node_tree.nodes:   # a copy with its rain dial turned, the original left alone
        name = '%s, rain %.2f' % (water_material.name, rain)
        rained = bpy.data.materials.get(name)
        if rained is None:
            rained = water_material.copy()
            rained.name = name
            rained.node_tree.nodes['Rain'].outputs[0].default_value = float(rain)
        water_material = rained
    made = []
    for number, spot in enumerate(spots):
        members = (numpy.abs(pool_id - spot['pool']) < 0.5) & (water > 0.0)
        for _ring in range(2):                                 # the faces round the water, and one ring more
            touching = numpy.zeros(len(starts), dtype=bool)
            touching[face_of_corner[members[corners]]] = True
            members = numpy.zeros(len(points), dtype=bool)
            members[corners[touching[face_of_corner]]] = True
        faces = numpy.flatnonzero(touching)
        if not len(faces):
            continue
        used = numpy.flatnonzero(members)
        new_index = numpy.full(len(points), -1, dtype=numpy.int64)
        new_index[used] = numpy.arange(len(used))
        level = float(spot['level'])
        sheet = bpy.data.meshes.new('ground water')
        sheet_points = points[used].copy()
        sheet_points[:, 2] = level
        sheet_faces = [new_index[corners[starts[f]:starts[f] + totals[f]]].tolist() for f in faces.tolist()]
        sheet.from_pydata(sheet_points.tolist(), [], sheet_faces)
        sheet.update()
        depth = level - points[used, 2]
        set_numbers(sheet, 'shallow', 1.0 - numpy.clip(depth / 0.025, 0.0, 1.0))
        set_numbers(sheet, 'dry', numpy.zeros(len(used)))
        obj = bpy.data.objects.new('ground water %d' % (number + 1), sheet)
        collection.objects.link(obj)
        obj.data.materials.append(water_material)
        store.mark(obj, ground=level)
        made.append(obj)
    return made


def spots(ground):
    """Where water stands now, with the ground's last wetness (the same as calling wet() again with it)."""
    return wet(ground, ground.get('wetness_dial', 0.5), ground.get('wetness_pattern', 'hollows'), ground.get('crust_dial', 1.0))


_HEIGHT_TREES = {}


def height_at(ground, x, y):
    """The ground's height in metres at the world point (x, y), or None off its edge: for standing a part on the ground
    (store.add_part(name, location=(x, y, ground.height_at(yard, x, y)))). It follows the tracks carved into it."""
    from mathutils.bvhtree import BVHTree
    mesh = ground.data
    local = numpy.zeros(len(mesh.vertices) * 3, dtype=numpy.float64)
    mesh.vertices.foreach_get('co', local)
    key = (mesh.as_pointer(), len(mesh.vertices), len(mesh.polygons), float(local[2::3].sum()))
    tree = _HEIGHT_TREES.get(mesh.as_pointer())
    if tree is None or tree[0] != key:
        corners = numpy.zeros(len(mesh.loops), dtype=numpy.int64)
        mesh.loops.foreach_get('vertex_index', corners)
        starts = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
        mesh.polygons.foreach_get('loop_start', starts)
        totals = numpy.zeros(len(mesh.polygons), dtype=numpy.int64)
        mesh.polygons.foreach_get('loop_total', totals)
        faces = [corners[a:a + n].tolist() for a, n in zip(starts.tolist(), totals.tolist())]
        tree = (key, BVHTree.FromPolygons(local.reshape(-1, 3).tolist(), faces))
        _HEIGHT_TREES[mesh.as_pointer()] = tree
    inverse = ground.matrix_world.inverted()
    origin = inverse @ Vector((x, y, 1000.0))
    down = (inverse.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
    hit = tree[1].ray_cast(origin, down)
    if hit[0] is None:
        return None
    return float((ground.matrix_world @ hit[0]).z)


# ----------------------------------------------------------------------------------------------- command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Make the ground and set how wet it is (see the note at the top of ground.py).')
    parser.add_argument('--blend', help='open this .blend file first (otherwise a new empty one)')
    parser.add_argument('--out', help='save the result here')
    parser.add_argument('--size', type=float, nargs=2, default=(12.0, 12.0), help='x y metres; default 12 12')
    parser.add_argument('--at', type=float, nargs=3, default=(0.0, 0.0, 0.0), help='the middle x y z; default 0 0 0')
    parser.add_argument('--cell', type=float, default=0.1, help='the size of its squares, metres; default 0.1')
    parser.add_argument('--relief', type=float, default=0.08, help='how much it rises and falls, metres; default 0.08')
    parser.add_argument('--wetness', type=float, default=0.0, help='0 dry .. 1 just rained; default 0')
    parser.add_argument('--pattern', choices=('hollows', 'even'), default='hollows', help="where the wet lies; default hollows")
    parser.add_argument('--soil', default='dry dirt', help="'dry dirt', 'dark dirt' or a material name; default 'dry dirt'")
    parser.add_argument('--seed', type=int, default=0, help='the same seed, the same ground; default 0')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    made = make(size=args.size, location=args.at, cell=args.cell, relief=args.relief, seed=args.seed, soil=args.soil)
    found = wet(made, args.wetness, args.pattern)
    print('made %s: %d points; water stands in %d places' % (made.name, len(made.data.vertices), len(found)))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
