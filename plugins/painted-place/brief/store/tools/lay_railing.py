"""
What this file does: lays a wrought-iron railing along a line you give, and makes a gate between two stone piers where
you say. The railing is upright square bars with spear tops, two flat rails through them, a heavier post every few
metres and at every corner, all standing on a low stone plinth (or straight on the ground); rust pools on the plinth
round the foot of each bar, where water sits. The gate is two leaves (or one) of the same bars, their tops rising
towards the closing side, hung on hinge stiles between two square stone piers with caps, swung open by the angle you
give. Nothing here chooses where a railing goes: the line and the gate's place are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_railing
    made = lay_railing.lay([(-6, 0, 0), (6, 0, 0), (6, 8, 0)], height=1.1, seed=2)        # along a line of points
    made = lay_railing.lay(bpy.data.objects['Fence line'], plinth=0)                        # a curve, no plinth
    gate = lay_railing.gate((0, 0, 0), width=1.2, open_angle=35, seed=2)                    # between two piers, front to -Y

The line may be a list of points (x, y, z), a curve object, a mesh object made of a line of edges, or the path of a
JSON file holding {"points": [[x, y, z], ...]}. The railing follows the line's own heights (z). Leave a gap in the line
where a gate goes (two separate calls to lay, one each side), and put the gate in the gap with gate().

From the command line:

    python3 lay_railing.py --help
    python3 lay_railing.py --points "-6,0,0 6,0,0 6,8,0" --out railing.blend
    python3 lay_railing.py --blend yard.blend --line "Fence line" --gate 0 0 0 --gate-open 30 --out yard_railed.blend

Options of lay(), with their defaults:
    height          1.1 m     the ground (or plinth top) to the spear points
    spacing         0.14 m    between bars, middle to middle (adjusted so the bars fit each straight run)
    plinth          0.15 m    height of the stone plinth the railing stands on; 0 for none
    plinth_width    0.30 m
    post_spacing    2.5 m     about how far apart the heavier posts stand (one at every corner and end as well)
    bar             0.016 m   a bar's thickness (square)
    rust            0.6       0 none to 1 heavy: rust pooled round the bars' feet
    seed            0         the bars' slight leans and the rust's spread
    collection      none      where the objects go (default: a new collection 'lay_railing')
    iron_material   'IRON • soot-black lamp posts'
    stone_material  'STONE • worn honey-grey architectural dressings'   (the plinth)
    rust_material   'MADE • stain rust'

Options of gate(), with their defaults:
    location        the middle of the opening at ground level (x, y, z)
    width           1.2 m     the clear opening between the piers
    turn            0         degrees about Z; before turning the gate's front faces -Y and the leaves swing to +Y
    open_angle      0         degrees each leaf is swung open (towards +Y, inwards; negative swings it out)
    leaves          2         two leaves meeting in the middle, or 1 hung on the left pier (seen from the front)
    height          1.3 m     the leaves' spear points at the closing side; the hinge side is `rise` lower
    rise            0.15 m
    piers           True      two square stone piers with caps and pointed tops; False for none (your own posts)
    pier_width      0.45 m
    pier_height     1.7 m     to the top of the cap (the point is 0.3 m higher)
    spacing, bar, seed, collection, iron_material, stone_material: as lay(); pier_material 'Hand-painted sandstone • shade 03'

Both return the objects made, in a dict by plain names: lay(): 'railing bars', 'railing rails', 'railing posts',
'railing plinth' (if any), 'railing rust' (if any); gate(): 'gate left leaf', 'gate right leaf' (the leaf objects turn
about their hinge: rotation_euler.z is turn + the swing), 'gate left pier', 'gate right pier' (if piers).
"""

import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402

IRON = 'IRON • soot-black lamp posts'
STONE = 'STONE • worn honey-grey architectural dressings'
PIER_STONE = 'Hand-painted sandstone • shade 03'
RUST = 'MADE • stain rust'

TOOL = {
    'name': 'lay_railing',
    'what': 'a wrought-iron railing along a line you give (spear-topped bars, two rails, posts, a stone plinth, rust at the bars\' feet) and a gate between two stone piers, swung open by the angle you ask',
    'call': "lay_railing.lay([(-6, 0, 0), (6, 0, 0), (6, 8, 0)], height=1.1, seed=2);  lay_railing.gate((0, 0, 0), width=1.2, open_angle=35, seed=2)",
    'options': {
        'height': 'the ground (or plinth top) to the spear points (1.1 m); a gate leaf\'s closing side (1.3 m)',
        'spacing': 'between bars, middle to middle (0.14 m)',
        'plinth': 'height of the stone plinth the railing stands on; 0 for none (0.15 m)',
        'plinth_width': '0.30 m',
        'post_spacing': 'about how far apart the heavier posts stand; one at every corner and end as well (2.5 m)',
        'bar': 'a bar\'s thickness, square (0.016 m)',
        'rust': 'rust pooled round the bars\' feet, 0 none to 1 heavy (0.6)',
        'seed': 'the bars\' slight leans and the rust\'s spread (0)',
        'gate: location, width': 'the middle of the opening at ground level; the clear opening between the piers (1.2 m)',
        'gate: turn': 'degrees about Z; before turning the front faces -Y (0)',
        'gate: open_angle': 'degrees each leaf is swung open towards +Y; negative swings it out (0)',
        'gate: leaves': 'two meeting in the middle, or 1 hung on the left pier (2)',
        'gate: rise': 'how much the bars rise from the hinge side to the closing side (0.15 m)',
        'gate: piers, pier_width, pier_height': 'two square stone piers with caps and pointed tops (True, 0.45 m, 1.7 m to the cap)',
        'collection': "where the objects go (a new collection 'lay_railing')",
    },
    'materials': [IRON, STONE, PIER_STONE, RUST],
    'source': "the chapel builder's `railing`, gate piers and gate leaves in '51 chapel - render_final.py' (line 404 on), made into a tool",
    'trap': 'the gate is hung in the opening you give: lay the railing in two runs that stop at the piers (the tool does not cut a railing for a gate); the pier stone projects one big picture over the place, so call store.prepare_for_render(scene) once before drawing',
}

UP = Vector((0.0, 0.0, 1.0))


# ------------------------------------------------------------------------------------------------ the line

def _chain(mesh):
    """The vertex order of a mesh made of one line of edges (from one end to the other)."""
    if not mesh.edges:
        return list(range(len(mesh.vertices)))
    neighbours = {index: [] for index in range(len(mesh.vertices))}
    for edge in mesh.edges:
        a, b = edge.vertices
        neighbours[a].append(b)
        neighbours[b].append(a)
    ends = [index for index, near in neighbours.items() if len(near) == 1]
    start = ends[0] if ends else next(index for index, near in neighbours.items() if near)
    order, seen = [start], {start}
    while True:
        following = [index for index in neighbours[order[-1]] if index not in seen]
        if not following:
            return order
        order.append(following[0])
        seen.add(following[0])


def line_points(line):
    """World points of the line: a list of points, a curve or mesh object, or a JSON file of points."""
    if isinstance(line, str):
        with open(line) as handle:
            data = json.load(handle)
        line = data['points'] if isinstance(data, dict) else data
    if isinstance(line, bpy.types.Object):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = line.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            points = [line.matrix_world @ mesh.vertices[index].co for index in _chain(mesh)]
        finally:
            evaluated.to_mesh_clear()
        return points
    points = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in line]
    kept = [points[0]]
    for point in points[1:]:
        if (point - kept[-1]).length > 1e-5:
            kept.append(point)
    if len(kept) < 2:
        raise ValueError('the line needs at least two different points')
    return kept


# ------------------------------------------------------------------------------------------------ mesh making

class Mesh:
    """Boxes and spear bars gathered into one mesh, with optional numbers per point."""

    def __init__(self, numbers=()):
        self.verts, self.faces = [], []
        self.numbers = {name: [] for name in numbers}

    def _add(self, verts, faces, values=None):
        base = len(self.verts)
        self.verts.extend(tuple(v) for v in verts)
        self.faces.extend(tuple(base + i for i in face) for face in faces)
        for name in self.numbers:
            self.numbers[name].extend([(values or {}).get(name, 0.0)] * len(verts))

    def box(self, centre, along, size, up=UP):
        """A box: `centre`, its length along the unit vector `along`, `size` = (length, width, height), `up` its height's way."""
        along = Vector(along).normalized()
        up = Vector(up).normalized()
        across = along.cross(up).normalized()
        length, width, height = size
        corners = []
        for dz in (-0.5, 0.5):
            for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                corners.append(Vector(centre) + along * (dx * length) + across * (dy * width) + up * (dz * height))
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(corners, faces)

    def bar(self, foot, top, thickness, spear=True, lean=(0.0, 0.0)):
        """An upright square bar from `foot` up to `top` (its spear point), leaning by `lean` metres at the top."""
        foot, top = Vector(foot), Vector(top) + Vector((lean[0], lean[1], 0.0))
        half = thickness / 2
        head = 0.12 if spear else 0.0
        neck = top - UP * head
        axis = (neck - foot)
        axis = axis.normalized() if axis.length > 1e-9 else UP
        side = Vector((1.0, 0.0, 0.0)) if abs(axis.x) < 0.9 else Vector((0.0, 1.0, 0.0))
        across = axis.cross(side).normalized()
        side = across.cross(axis).normalized()
        ring = lambda point, h: [point + side * (sx * h) + across * (sy * h) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        verts = ring(foot, half) + ring(neck, half)
        faces = [(0, 3, 2, 1)] + [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
        if spear:
            # a leaf-shaped spear: the bar swells to a collar, then tapers to the point
            collar = neck + UP * (head * 0.3)
            verts += ring(collar, half * 2.1) + [top]
            faces += [(4 + i, 4 + (i + 1) % 4, 8 + (i + 1) % 4, 8 + i) for i in range(4)]
            faces += [(8 + i, 8 + (i + 1) % 4, 12) for i in range(4)]
        else:
            faces.append((4, 5, 6, 7))
        self._add(verts, faces)

    def quad(self, corners, values):
        """One face with its own numbers per corner: `values` is {name: (v0, v1, v2, v3)}."""
        base = len(self.verts)
        self.verts.extend(tuple(c) for c in corners)
        self.faces.append((base, base + 1, base + 2, base + 3))
        for name in self.numbers:
            self.numbers[name].extend(values.get(name, (0.0,) * 4))

    def build(self, name, collection, material, origin=(0.0, 0.0, 0.0), ground=0.0, smooth=False, shadow=True, local=False):
        """The object: its points are world points unless `local` (already measured from `origin`); origin becomes its location."""
        if not self.faces:
            return None
        origin = Vector(origin)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([tuple(Vector(v) - (Vector() if local else origin)) for v in self.verts], [], self.faces)
        for attribute_name, data in self.numbers.items():
            layer = mesh.attributes.new(attribute_name, 'FLOAT', 'POINT')
            layer.data.foreach_set('value', data)
        mesh.update()
        if smooth:
            mesh.shade_smooth()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        obj.visible_shadow = shadow
        collection.objects.link(obj)
        store.use_material(obj, material, ground=ground)
        return obj


def _collection(collection):
    if collection is None:
        collection = bpy.data.collections.new('lay_railing')
        bpy.context.scene.collection.children.link(collection)
    return collection


# ------------------------------------------------------------------------------------------------ the railing

def _bars_along(mesh, rust_mesh, a, b, base_z, height, spacing, bar, rng, rust, start_at=0, end_at=0, rise=0.0):
    """Bars from a to b (points at the standing surface), base_z(point) giving the height to stand each on; the tops
    rise by `rise` from a to b. start_at / end_at: bars left out at the ends (where a post stands). Returns the count."""
    run = (b - a)
    length = run.length
    along = run.normalized()
    across = along.cross(UP).normalized()
    count = max(1, int(round(length / spacing)))
    made = 0
    for i in range(start_at, count + 1 - end_at):
        t = i / count
        foot = a.lerp(b, t)
        foot = Vector((foot.x, foot.y, base_z(foot)))
        lean = (rng.uniform(-0.006, 0.006), rng.uniform(-0.006, 0.006))
        mesh.bar(foot, foot + UP * (height + rise * t), bar, lean=lean)
        made += 1
        if rust_mesh is not None and rng.random() < rust * 0.9:
            reach = rng.uniform(0.05, 0.11) * (0.5 + rust)
            wide = reach * rng.uniform(0.6, 1.0)
            spot = foot + UP * 0.002 + across * rng.uniform(-0.01, 0.01)
            corners = [spot - along * reach - across * wide, spot + along * reach - across * wide,
                       spot + along * reach + across * wide, spot - along * reach + across * wide]
            # fade: 0 at the bar's foot (the middle), 1 at the patch's edge: a ring of eight points round a middle
            middle = len(rust_mesh.verts)
            rust_mesh.verts.append(tuple(spot))
            rust_mesh.numbers['fade'].append(0.0)
            ring = []
            for k in range(8):
                angle = math.tau * k / 8
                r = 1.0 + rng.uniform(-0.25, 0.25)
                ring.append(spot + along * (math.cos(angle) * reach * r) + across * (math.sin(angle) * wide * r))
            for point in ring:
                rust_mesh.verts.append(tuple(point))
                rust_mesh.numbers['fade'].append(1.0)
            for k in range(8):
                rust_mesh.faces.append((middle, middle + 1 + k, middle + 1 + (k + 1) % 8))
    return made


def lay(line, height=1.1, spacing=0.14, plinth=0.15, plinth_width=0.30, post_spacing=2.5, bar=0.016, rust=0.6, seed=0,
        collection=None, iron_material=IRON, stone_material=STONE, rust_material=RUST):
    """Lay the railing along the line; returns a dict of the objects made (see the note at the top)."""
    rng = random.Random(seed)
    points = line_points(line)
    collection = _collection(collection)
    iron, stone, rusty = store.material(iron_material), store.material(stone_material), store.material(rust_material)
    bars, rails, posts, plinths = Mesh(), Mesh(), Mesh(), Mesh()
    rust_mesh = Mesh(['fade']) if rust > 0 else None
    post_size = bar * 2.6
    rail_size = (0.035, 0.012)                   # a flat rail: across the bars, thick
    bar_count = post_count = 0
    post_spots = []

    for a, b in zip(points[:-1], points[1:]):
        a, b = Vector(a), Vector(b)
        run = b - a
        flat = Vector((run.x, run.y, 0.0))
        if flat.length < 1e-6:
            continue
        along = flat.normalized()
        across = along.cross(UP).normalized()
        length = flat.length
        slope = run.z / length

        def base_z(point, a=a, slope=slope, along=along):
            return a.z + slope * (Vector((point.x - a.x, point.y - a.y, 0.0)).dot(along)) + plinth

        # the plinth: a box along the run, its top where the bars stand
        tilt = run.normalized()
        tilt_up = across.cross(tilt).normalized()               # straight up on level ground, square to a sloping run
        if plinth > 0:
            plinths.box((a + b) / 2 + UP * (plinth / 2), tilt, (run.length + plinth_width * 0.5, plinth_width, plinth), up=tilt_up)
        # posts: at both ends and every post_spacing along, each bay between them then filled with bars
        bays = max(1, int(round(length / post_spacing)))
        stops = [a.lerp(b, i / bays) for i in range(bays + 1)]
        for i, stop in enumerate(stops):
            spot = Vector((stop.x, stop.y, base_z(stop)))
            if any((spot - p).length < 0.01 for p in post_spots):
                continue
            post_spots.append(spot)
            posts.bar(spot, spot + UP * (height + 0.05), post_size, spear=True)
            post_count += 1
        for left, right in zip(stops[:-1], stops[1:]):
            left2 = Vector((left.x, left.y, 0.0))
            right2 = Vector((right.x, right.y, 0.0))
            bar_count += _bars_along(bars, rust_mesh, left2, right2, base_z, height, spacing, bar, rng, rust, start_at=1, end_at=1)
        # two rails along the whole run, through the bars
        for z in (0.12, height - 0.22):
            centre = (a + b) / 2 + UP * (plinth + z)
            rails.box(centre, tilt, (run.length + post_size, rail_size[0], rail_size[1]), up=tilt_up)

    ground_z = min(p.z for p in points)
    origin = Vector(points[0])
    made = {}
    for key, mesh, material in (('railing bars', bars, iron), ('railing rails', rails, iron), ('railing posts', posts, iron),
                                ('railing plinth', plinths, stone)):
        obj = mesh.build(key, collection, material, origin=origin, ground=ground_z)
        if obj is not None:
            made[key] = obj
    if rust_mesh is not None:
        obj = rust_mesh.build('railing rust', collection, rusty, origin=origin, ground=ground_z, shadow=False)
        if obj is not None:
            made['railing rust'] = obj
    if 'railing bars' not in made:
        raise ValueError('the line is too short for a single bar between its posts (%.2f m)' % sum((Vector(b) - Vector(a)).length for a, b in zip(points[:-1], points[1:])))
    made['railing bars']['railing_bars'] = bar_count
    made['railing bars']['railing_posts'] = post_count
    bpy.context.view_layer.update()
    return made


# ------------------------------------------------------------------------------------------------ the gate

def _leaf(width, height, rise, spacing, bar, rng, hinge_side):
    """One gate leaf in its own frame: the hinge at the origin, the leaf running along +X (hinge_side 'left') or -X
    ('right'), the closing stile at the far end; bars rise from the hinge side to the closing side."""
    mesh = Mesh()
    sign = 1.0 if hinge_side == 'left' else -1.0
    stile = bar * 1.9
    foot_z = 0.05
    count = max(2, int(round(width / spacing)))
    # the two stiles
    for x, h in ((sign * stile / 2 + sign * 0.0, height - rise - 0.1), (sign * (width - stile / 2), height - 0.1)):
        mesh.bar((x, 0.0, foot_z), (x, 0.0, h), stile, spear=False)
    # bars between, with spear tops, rising to the closing side
    for i in range(1, count):
        t = i / count
        x = sign * width * t
        top = height - rise * (1.0 - t)
        mesh.bar((x, 0.0, foot_z), (x, 0.0, top), bar, lean=(rng.uniform(-0.003, 0.003), rng.uniform(-0.003, 0.003)))
    # two flat rails and a sloping top rail just under the spears
    for z in (foot_z + 0.10, height - rise - 0.30):
        mesh.box((sign * width / 2, 0.0, z), (1.0, 0.0, 0.0), (width, 0.035, 0.012))
    low, high = Vector((0.0, 0.0, height - rise - 0.16)), Vector((sign * width, 0.0, height - 0.16))
    along = (high - low).normalized()
    mesh.box((low + high) / 2, along, ((high - low).length, 0.035, 0.012), up=along.cross(UP).cross(along).normalized())
    # hinge knuckles on the hinge stile
    for z in (foot_z + 0.12, height - rise - 0.32):
        mesh.box((sign * stile * 0.2, 0.0, z), (1.0, 0.0, 0.0), (stile * 1.6, stile * 1.6, 0.05))
    return mesh


def gate(location, width=1.2, turn=0.0, open_angle=0.0, leaves=2, height=1.3, rise=0.15, spacing=0.14, bar=0.016,
         piers=True, pier_width=0.45, pier_height=1.7, seed=0, collection=None, iron_material=IRON,
         stone_material=STONE, pier_material=PIER_STONE):
    """A gate in an opening `width` wide, its middle at `location`, front to -Y before `turn`; returns a dict of the
    objects made (see the note at the top). Each leaf object's origin is its hinge and it is turned about it."""
    rng = random.Random(seed)
    location = Vector(location)
    collection = _collection(collection)
    iron, stone, pier_stone = store.material(iron_material), store.material(stone_material), store.material(pier_material)
    turning = Matrix.Rotation(math.radians(turn), 4, 'Z')
    made = {}
    leaf_width = width / leaves - 0.01
    sides = [('left', -1.0), ('right', 1.0)] if leaves == 2 else [('left', -1.0)]
    for name, side in sides:
        mesh = _leaf(leaf_width, height, rise, spacing, bar, rng, name)
        hinge = location + turning.to_3x3() @ Vector((side * width / 2, 0.0, 0.0))
        obj = mesh.build('gate %s leaf' % name, collection, iron, origin=hinge, ground=location.z, local=True)
        # the left leaf swings open by turning anti-clockwise seen from above (its far end goes to +Y), the right one clockwise
        obj.rotation_euler = (0.0, 0.0, math.radians(turn) + math.radians(open_angle) * (1.0 if side < 0 else -1.0))
        obj['gate_open_angle'] = float(open_angle)
        obj['gate_leaf_width'] = float(leaf_width)
        made['gate %s leaf' % name] = obj
    if piers:
        for name, side in (('left', -1.0), ('right', 1.0)):
            centre = location + turning.to_3x3() @ Vector((side * (width / 2 + pier_width / 2), 0.0, 0.0))
            along = turning.to_3x3() @ Vector((1.0, 0.0, 0.0))
            body, cap = Mesh(), Mesh()
            body.box(centre + UP * (pier_height - 0.12) / 2, along, (pier_width, pier_width, pier_height - 0.12))
            cap.box(centre + UP * (pier_height - 0.06), along, (pier_width + 0.17, pier_width + 0.17, 0.12))
            # a shallow pyramid on the cap
            base = len(cap.verts)
            half = pier_width * 0.55
            across = along.cross(UP)
            top_z = pier_height
            cap.verts.extend(tuple(centre + along * (sx * half) + across * (sy * half) + UP * top_z) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
            cap.verts.append(tuple(centre + UP * (top_z + 0.3)))
            cap.faces.extend([(base + i, base + (i + 1) % 4, base + 4) for i in range(4)] + [(base + 3, base + 2, base + 1, base)])
            made['gate %s pier' % name] = body.build('gate %s pier' % name, collection, pier_stone, origin=centre, ground=location.z)
            made['gate %s pier cap' % name] = cap.build('gate %s pier cap' % name, collection, stone, origin=centre, ground=location.z)
    bpy.context.view_layer.update()                      # so the leaves' world matrices carry their swing at once
    return made


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of lay_railing.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the line as "x,y,z x,y,z ..." (makes a new file unless --blend is given)')
    parser.add_argument('--points-json', help='a JSON file holding {"points": [[x, y, z], ...]}')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--out', help='save the result here (.blend)')
    for name, default, help_text in (('height', 1.1, 'the ground or plinth top to the spear points, metres'),
                                     ('spacing', 0.14, 'between bars, metres'), ('plinth', 0.15, 'the stone plinth\'s height, metres; 0 for none'),
                                     ('plinth-width', 0.30, 'metres'), ('post-spacing', 2.5, 'about how far apart the posts stand, metres'),
                                     ('bar', 0.016, 'a bar\'s thickness, metres'), ('rust', 0.6, 'rust round the bars\' feet, 0 to 1')):
        parser.add_argument('--' + name, type=float, default=default, help='%s; default %s' % (help_text, default))
    parser.add_argument('--gate', type=float, nargs=3, metavar=('X', 'Y', 'Z'), help='also make a gate with its middle here')
    parser.add_argument('--gate-width', type=float, default=1.2, help='the clear opening between the piers; default 1.2')
    parser.add_argument('--gate-turn', type=float, default=0.0, help='degrees about Z; default 0 (front to -Y)')
    parser.add_argument('--gate-open', type=float, default=0.0, help='degrees the leaves are swung open; default 0')
    parser.add_argument('--gate-leaves', type=int, default=2, choices=(1, 2), help='default 2')
    parser.add_argument('--no-piers', action='store_true', help='the gate without its stone piers')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same railing; default 0')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    line = None
    if args.line:
        if args.line not in bpy.data.objects:
            parser.error('no object %r in the file; its objects are: %s' % (args.line, ', '.join(o.name for o in bpy.data.objects)))
        line = bpy.data.objects[args.line]
    elif args.points_json:
        line = args.points_json
    elif args.points:
        line = [tuple(float(v) for v in point.split(',')) for point in args.points.split()]
    if line is None and args.gate is None:
        parser.error('give the line (--points, --points-json or --line) or a gate (--gate X Y Z), or both')
    if not args.out:
        print('note: nothing will be saved; give --out FILE.blend to keep the railing')
    if line is not None:
        made = lay(line, height=args.height, spacing=args.spacing, plinth=args.plinth, plinth_width=args.plinth_width,
                   post_spacing=args.post_spacing, bar=args.bar, rust=args.rust, seed=args.seed)
        print('made', ', '.join(made), '-', made['railing bars']['railing_bars'], 'bars,', made['railing bars']['railing_posts'], 'posts')
    if args.gate is not None:
        made = gate(args.gate, width=args.gate_width, turn=args.gate_turn, open_angle=args.gate_open, leaves=args.gate_leaves,
                    piers=not args.no_piers, spacing=args.spacing, bar=args.bar, seed=args.seed)
        print('made', ', '.join(made))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)


if __name__ == '__main__':
    main()
