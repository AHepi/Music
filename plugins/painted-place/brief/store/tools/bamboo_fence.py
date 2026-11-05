"""
What this file does: builds a Japanese garden fence of bamboo along a line or curve you give, the way such fences are
made: thick bamboo posts at every corner and every bay, cut just above a joint so rain does not stand in them; then
either an open lattice (yotsume-gaki: horizontal rails across the posts and thin upright canes in front of and behind
them by turns, leaving open squares) or a close fence (misu-gaki: canes packed side by side, held between pairs of
half-round rails on the front, a split bamboo capping their tops). Every crossing is tied with black palm-fibre cord in
a cross. Each cane is its own: its own thickness and shade, its joints (the rings) at their own spacing and a little
proud. The bamboo is old and greyed unless you ask for new green-yellow canes; it is darker and green at its foot,
where rain splashes soil up it and moss climbs. Nothing here chooses where a fence goes: the line and its height are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import bamboo_fence
    made = bamboo_fence.lay([(0.5, 0.6, 0), (1.3, 2.2, 0), (1.3, 4.0, 0)], kind='lattice', height=1.0, seed=2)
    made = bamboo_fence.lay(curve_object, kind='close', height=1.6, new=True, ground=my_ground, seed=3)
    made['bamboo'], made['cord']           # the canes, posts and rails; the black cord ties

The line may be a list of points (x, y, z), a curve object, a mesh object made of a line of edges, or the path of a
JSON file holding {"points": [[x, y, z], ...]}; its z is the ground under the fence unless you give `ground`. Looking
along the line from its first point, the fence's front (the ties, the close fence's rails) faces right, unless
`front='left'`.

From the command line:

    python3 bamboo_fence.py --help
    python3 bamboo_fence.py --points "0,0,0 4,0,0 4,3,0" --kind close --height 1.6 --out fence.blend

Options, with their defaults:
    kind          'lattice'   'lattice': an open lattice of rails and upright canes (yotsume-gaki); 'close': canes packed
                              side by side between half-round rails (misu-gaki)
    height        none        the ground to the post tops, metres (none: 1.0 for a lattice, 1.6 for a close fence)
    post_spacing  1.8 m       about how far apart the posts stand (one at every corner and end as well)
    spacing       none        the upright canes of a lattice, middle to middle (none: 0.27 m); the close fence's canes
                              touch (about 3 cm thick each)
    rails         none        how many rails (none: 3 on a lattice up to 1.2 m, 4 above; 3 on a close fence up to 1.6 m, 4 above)
    new           False       True: new green-yellow canes; False: old bamboo greyed by the weather
    front         'right'     which side of the line the front faces, looking along it: 'right' or 'left'
    ground        none        a mesh object: the posts' feet stand on it (one ray per post)
    smooth        False       True: a smooth curve through your points (the fence still runs straight from post to post,
                              as rails do); False: straight between your points, a post at each
    seed          0           the same seed builds the same fence
    material, cord_material   none: made here ('MADE • bamboo, greyed' or 'MADE • bamboo, new'; 'MADE • black cord')
    collection    none        where the objects go (a new collection 'bamboo_fence')

What it makes: 'bamboo fence' (obj['canes'], obj['posts']) and 'bamboo fence ties' (obj['ties']). Every point of the
bamboo carries 'cane_tone' (each cane's shade), 'cane_along' and 'cane_round' (where it lies on its cane, for the
streaks), 'cane_node' (1 at a joint) and 'cane_height' (metres above the ground under it, for the damp foot).
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402

KINDS = ('lattice', 'close')
OLD = 'MADE • bamboo, greyed'
NEW = 'MADE • bamboo, new'
CORD = 'MADE • black cord'
UP = Vector((0.0, 0.0, 1.0))
SIDES = 10

TOOL = {
    'name': 'bamboo_fence',
    'what': 'a bamboo garden fence along a line or curve you give: posts, horizontal rails and canes, tied at the crossings '
            'with black cord; an open lattice (yotsume-gaki) or a close fence of canes packed side by side (misu-gaki); '
            'old greyed bamboo, or new green-yellow canes if asked; darker and green at its foot',
    'call': "bamboo_fence.lay([(0.5, 0.6, 0), (1.3, 2.2, 0), (1.3, 4.0, 0)], kind='lattice', height=1.0, seed=2)",
    'options': {
        'line': 'a list of points, a curve or line-mesh object, or a JSON file; its z the ground under the fence (required)',
        'kind': "'lattice' (rails and upright canes leaving open squares, yotsume-gaki) or 'close' (canes packed side by "
                "side between half-round rails, misu-gaki) ('lattice')",
        'height': 'the ground to the post tops, metres (none: 1.0 for a lattice, 1.6 for a close fence)',
        'post_spacing': 'about how far apart the posts stand; one at every corner and end too (1.8 m)',
        'spacing': "a lattice's upright canes, middle to middle (none: 0.27 m)",
        'rails': 'how many rails (none: 3, or 4 on a fence higher than 1.2 m for a lattice or 1.6 m for a close fence)',
        'new': 'True: new green-yellow canes; False: old greyed bamboo (False)',
        'front': "which side of the line the front (ties, rails) faces, looking along it: 'right' or 'left' ('right')",
        'ground': "a mesh object the posts' feet stand on (none: the line's own heights)",
        'smooth': 'a smooth curve through your points, still straight from post to post (False: a post at each point)',
        'seed': 'the same seed builds the same fence (0)',
        'material, cord_material': "the bamboo and the ties (none: made here, '%s' or '%s', and '%s')" % (OLD, NEW, CORD),
        'collection': "where the objects go (a new collection 'bamboo_fence')",
    },
    'materials': [OLD + ' (made in code)', NEW + ' (made in code)', CORD + ' (made in code)'],
    'source': "the bamboo fence in the garden builders' '57 garden' scripts ('/home/claude/build-57-garden/second pass/"
              "render_final.py', lines 1064-1091, and its greyed bamboo with a damp foot, mat_bamboo() at line 449), made "
              "into a tool from the board's photograph 08 (a Sugita garden fence): posts cut above a joint, real joints on "
              "every cane, the lattice's canes in front and behind by turns, cross ties, and the close fence; no "
              "photographed bamboo is on the shelf, so its surface is made in code",
    'trap': "its canes are 2 to 4 cm thick and the cord 4 mm: from 10 m and more the lattice is a fine net and the ties "
            "vanish (put it near the eye or use the close fence); its foot's damp green hardly shows at dusk; a "
            "fence's line is its middle: leave its posts' 4 cm either side clear of a path's slabs",
}


# ------------------------------------------------------------------------------------------------ the mesh

class _Mesh:
    def __init__(self):
        self.verts, self.faces = [], []
        self.columns = {name: [] for name in ('cane_tone', 'cane_along', 'cane_round', 'cane_node', 'cane_height')}

    def _point(self, co, tone, along, round_, node, height):
        self.verts.append(tuple(co))
        for name, value in (('cane_tone', tone), ('cane_along', along), ('cane_round', round_), ('cane_node', node),
                            ('cane_height', height)):
            self.columns[name].append(value)
        return len(self.verts) - 1

    def cane(self, start, end, radius, rng, foot_z=None, tone=None, joint=0.3, open_top=False, half=False, out=None):
        """One cane from start to end: a tube with its joints (rings a little proud) every `joint` metres or so, its
        thickness wandering a little; open_top shows the hollow at its top end; half makes a half-round split cane
        whose flat back faces away from `out`."""
        start, end = Vector(start), Vector(end)
        axis = end - start
        length = axis.length
        if length < 1e-4:
            return
        ahead = axis / length
        side = ahead.cross(UP if abs(ahead.z) < 0.95 else Vector((1.0, 0.0, 0.0))).normalized()
        if out is not None:                                   # the round face looks along `out`
            side = Vector(out).cross(ahead).normalized()
        lift = side.cross(ahead).normalized() if out is None else Vector(out).normalized()
        tone = rng.random() if tone is None else tone
        rows = [0.0]
        first = rng.uniform(0.15, 1.0) * joint
        d = first
        while d < length - 0.02:
            for offset in (-0.006, 0.0, 0.006):              # a joint: three rings, the middle one proud
                if 0.0 < d + offset < length:
                    rows.append(d + offset)
            d += joint * rng.uniform(0.85, 1.2)
        for step in range(1, int(length / 0.12) + 1):        # plain rings between, so the tube can bend its light
            rows.append(step * 0.12)
        rows.append(length)
        rows = sorted(set(round(r, 4) for r in rows if 0.0 <= r <= length))
        joints = []
        d = first
        while d < length - 0.02:
            joints.append(d)
            d += joint * rng.uniform(0.85, 1.2)
        base = len(self.verts)
        count = SIDES + 1 if half else SIDES
        for r in rows:
            near = min((abs(r - j) for j in joints), default=1.0)
            node = 1.0 if near < 0.001 else max(0.0, 1.0 - near / 0.02)
            swell = 1.0 + 0.13 * (1.0 if near < 0.001 else 0.0) + 0.02 * math.sin(r * 3.1 + tone * 9.0)
            centre = start + ahead * r
            for k in range(count):
                a = (math.pi * k / SIDES) if half else (math.tau * k / SIDES)
                offset = side * math.cos(a) + lift * math.sin(a)
                co = centre + offset * radius * swell
                h = co.z - (foot_z if foot_z is not None else start.z)
                self._point(co, tone, r, a / math.tau, node, h)
        rings = len(rows)
        for i in range(rings - 1):
            a0, b0 = base + i * count, base + (i + 1) * count
            for k in range(count if not half else count - 1):
                k1 = (k + 1) % count
                self.faces.append((a0 + k, a0 + k1, b0 + k1, b0 + k))
        if half:                                              # the flat back of a split cane
            for i in range(rings - 1):
                a0, b0 = base + i * count, base + (i + 1) * count
                self.faces.append((a0 + count - 1, a0, b0, b0 + count - 1))
        # the ends: the foot closed; the top open, showing the wall and the dark hollow inside
        foot = base
        self.faces.append(tuple(foot + k for k in reversed(range(count))))
        top = base + (rings - 1) * count
        if open_top and not half:
            inner = []
            for k in range(SIDES):
                a = math.tau * k / SIDES
                co = end + (side * math.cos(a) + lift * math.sin(a)) * radius * 0.78 - ahead * 0.002
                inner.append(self._point(co, tone, length, a / math.tau, 1.0, co.z - (foot_z if foot_z is not None else start.z)))
            deep = [self._point(Vector(self.verts[i]) - ahead * 0.03, tone * 0.0, length, 0.0, 1.0, 0.0) for i in inner]
            for k in range(SIDES):
                k1 = (k + 1) % SIDES
                self.faces.append((top + k, top + k1, inner[k1], inner[k]))
                self.faces.append((inner[k], inner[k1], deep[k1], deep[k]))
            self.faces.append(tuple(reversed(deep)))
        else:
            self.faces.append(tuple(top + k for k in range(count)))

    def make(self, name, material, collection):
        mesh = bpy.data.meshes.new(name)
        origin = Vector(self.verts[0]) if self.verts else Vector()
        mesh.from_pydata([tuple(Vector(v) - origin) for v in self.verts], [], self.faces)
        for column, values in self.columns.items():
            layer = mesh.attributes.new(column, 'FLOAT', 'POINT')
            if values:
                layer.data.foreach_set('value', values)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces[:])
        tool.to_mesh(mesh)
        tool.free()
        mesh.shade_smooth()
        if hasattr(mesh, 'set_sharp_from_angle'):
            mesh.set_sharp_from_angle(angle=math.radians(60.0))
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = origin
        collection.objects.link(obj)
        obj.data.materials.append(material)
        store.mark(obj)
        return obj


def _tie(mesh, centre, along, up, out, size, rng):
    """A cross of black cord round a crossing: two bands crossed in front, a turn round behind, and the knot."""
    along, up, out = Vector(along).normalized(), Vector(up).normalized(), Vector(out).normalized()
    r = 0.0035
    for sign in (1.0, -1.0):
        a = centre + (along * sign + up) * size * 0.75 + out * 0.004
        b = centre - (along * sign + up) * size * 0.75 + out * 0.004
        mesh.cane(a, b, r, rng, tone=0.5, joint=10.0)
    for sign in (1.0, -1.0):                                  # the turns round the rail on either side of the cane
        mesh.cane(centre + along * size * 0.95 * sign - up * size * 0.55 - out * 0.002,
                  centre + along * size * 0.95 * sign + up * size * 0.55 - out * 0.002, r, rng, tone=0.5, joint=10.0)
    knot = centre + out * 0.007 + along * rng.uniform(-0.3, 0.3) * size - up * size * 0.25
    mesh.cane(knot - up * 0.006, knot + up * 0.006, 0.006, rng, tone=0.5, joint=10.0)
    mesh.cane(knot, knot - up * rng.uniform(0.02, 0.04) + along * rng.uniform(-0.01, 0.01), 0.0025, rng, tone=0.5, joint=10.0)


# ------------------------------------------------------------------------------------------------ materials

def bamboo_material(new=False):
    """Bamboo made in code: each cane its own shade, fine streaks along it, darker rings at its joints, waxy and
    a little glossy after rain; greyed by the weather, or new and green-yellow; dark and green at its foot."""
    name = NEW if new else OLD
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes['Principled BSDF']

    def attribute(name_):
        node = nodes.new('ShaderNodeAttribute')
        node.attribute_name = name_
        return node.outputs['Fac']

    def mix(fac, a, b):
        node = nodes.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        for socket, value in ((node.inputs[0], fac), (node.inputs[6], a), (node.inputs[7], b)):
            if isinstance(value, (int, float)):
                socket.default_value = value
            elif isinstance(value, tuple):
                socket.default_value = (*value, 1.0)
            else:
                links.new(value, socket)
        return node.outputs[2]

    def math_node(operation, a, b=None, clamp=False):
        node = nodes.new('ShaderNodeMath')
        node.operation = operation
        node.use_clamp = clamp
        for socket, value in ((node.inputs[0], a), (node.inputs[1], b)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                socket.default_value = value
            else:
                links.new(value, socket)
        return node.outputs[0]
    tone = attribute('cane_tone')
    if new:
        light, dark = (0.30, 0.29, 0.075), (0.17, 0.21, 0.045)
    else:
        light, dark = (0.30, 0.27, 0.19), (0.17, 0.155, 0.11)
    colour = mix(tone, dark, light)
    place = nodes.new('ShaderNodeCombineXYZ')                 # streaks run along the cane
    links.new(math_node('MULTIPLY', attribute('cane_round'), 9.0), place.inputs['X'])
    links.new(math_node('MULTIPLY', attribute('cane_along'), 0.35), place.inputs['Y'])
    links.new(math_node('MULTIPLY', tone, 31.0), place.inputs['Z'])
    streak = nodes.new('ShaderNodeTexNoise')
    streak.inputs['Scale'].default_value = 2.2
    streak.inputs['Detail'].default_value = 6.0
    links.new(place.outputs[0], streak.inputs['Vector'])
    colour = mix(math_node('MULTIPLY', math_node('SUBTRACT', streak.outputs['Fac'], 0.42, clamp=True), 1.6, clamp=True),
                 colour, (0.09, 0.08, 0.055) if not new else (0.12, 0.13, 0.03))
    node = attribute('cane_node')                             # the joints' rings: a dark ridge with a pale waxy band beside it
    colour = mix(math_node('MULTIPLY', math_node('SUBTRACT', math_node('MULTIPLY', node, 1.6), 0.6, clamp=True), 0.5), colour, (0.42, 0.40, 0.33) if not new else (0.38, 0.40, 0.2))
    colour = mix(math_node('POWER', node, 3.0), colour, (0.04, 0.035, 0.022))
    blotch = nodes.new('ShaderNodeTexNoise')                  # the damp foot's ragged top
    blotch.inputs['Scale'].default_value = 6.0
    links.new(nodes.new('ShaderNodeNewGeometry').outputs['Position'], blotch.inputs['Vector'])
    foot = math_node('SUBTRACT', 1.0, math_node('DIVIDE', attribute('cane_height'),
                                                 math_node('ADD', 0.12, math_node('MULTIPLY', blotch.outputs['Fac'], 0.3))), clamp=True)
    colour = mix(math_node('MULTIPLY', foot, 0.92), colour, (0.025, 0.04, 0.012))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.38
    principled.inputs['Coat Weight'].default_value = 0.25 if new else 0.12
    principled.inputs['Coat Roughness'].default_value = 0.2
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    links.new(streak.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    return material


def black_cord():
    existing = bpy.data.materials.get(CORD)
    if existing is not None:
        return existing
    material = bpy.data.materials.new(CORD)
    material.use_nodes = True
    principled = material.node_tree.nodes['Principled BSDF']
    principled.inputs['Base Color'].default_value = (0.012, 0.010, 0.009, 1.0)
    principled.inputs['Roughness'].default_value = 0.85
    return material


# ------------------------------------------------------------------------------------------------ the line

class _Ground:
    def __init__(self, ground):
        self.ground = ground
        if ground is not None:
            bpy.context.view_layer.update()
            self.depsgraph = bpy.context.evaluated_depsgraph_get()
            self.to_local = ground.matrix_world.inverted()
            self.down = (self.to_local.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()
            self.above = max((ground.matrix_world @ Vector(c)).z for c in ground.bound_box) + 1.0

    def at(self, point):
        if self.ground is None:
            return point.z
        hit, location, _, _ = self.ground.ray_cast(self.to_local @ Vector((point.x, point.y, self.above)), self.down,
                                                   distance=1.0e5, depsgraph=self.depsgraph)
        return (self.ground.matrix_world @ location).z if hit else point.z


def _posts(line, post_spacing, smooth):
    """Where the posts stand: every corner and end of the line, and between them about `post_spacing` apart."""
    points = []
    for p in _lines.line_points(line):
        p = Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0))
        if not points or (p.xy - points[-1].xy).length > 1e-4:
            points.append(p)
    if len(points) < 2:
        raise ValueError('the line needs at least two different points (seen from above)')
    if smooth and len(points) > 2 and not isinstance(line, bpy.types.Object):
        path = _lines.Path(points).smooth(0.05)
        count = max(1, int(round(path.total / post_spacing)))
        return [path.at(path.total * k / count) for k in range(count + 1)]
    if isinstance(line, bpy.types.Object) and len(points) > 2:
        path = _lines.Path(points)
        count = max(1, int(round(path.total / post_spacing)))
        return [path.at(path.total * k / count) for k in range(count + 1)]
    posts = [points[0]]
    for a, b in zip(points[:-1], points[1:]):
        count = max(1, int(round((b - a).xy.length / post_spacing)))
        posts.extend(a.lerp(b, k / count) for k in range(1, count + 1))
    return posts


# ------------------------------------------------------------------------------------------------ building

def lay(line, kind='lattice', height=None, post_spacing=1.8, spacing=None, rails=None, new=False, front='right', ground=None,
        smooth=False, seed=0, material=None, cord_material=None, collection=None):
    """Build the fence (see the note at the top). Returns {'bamboo': obj, 'cord': obj}."""
    if kind not in KINDS:
        raise ValueError("kind is 'lattice' or 'close', not %r" % (kind,))
    if front not in ('right', 'left'):
        raise ValueError("front is 'right' or 'left', not %r" % (front,))
    height = float(height) if height is not None else (1.0 if kind == 'lattice' else 1.6)
    if not 0.3 <= height <= 3.0:
        raise ValueError('height is 0.3 to 3 m, not %r' % (height,))
    post_spacing = float(post_spacing)
    if post_spacing < 0.4:
        raise ValueError('post_spacing is at least 0.4 m, not %r' % (post_spacing,))
    spacing = float(spacing) if spacing is not None else 0.27
    if rails is None:
        rails = 4 if height > (1.2 if kind == 'lattice' else 1.6) else 3
    rails = int(rails)
    rng = random.Random(seed)
    floor = _Ground(ground)
    posts = _posts(line, post_spacing, smooth)
    feet = [Vector((p.x, p.y, floor.at(p))) for p in posts]
    bamboo, cord = _Mesh(), _Mesh()
    canes = ties = 0
    post_r = 0.034
    # the posts: thick, cut a hand above a joint, set 0.3 m into the ground
    for foot in feet:
        top = foot + UP * (height + rng.uniform(-0.015, 0.015))
        bamboo.cane(foot - UP * 0.3, top, post_r * rng.uniform(0.9, 1.15), rng, foot_z=foot.z, joint=0.32, open_top=True)
    for a, b in zip(feet[:-1], feet[1:]):
        ahead = (b - a)
        ahead.z = 0.0
        span = ahead.length
        if span < 1e-3:
            continue
        ahead.normalize()
        out = Vector((ahead.y, -ahead.x, 0.0)) * (1.0 if front == 'right' else -1.0)     # towards the front
        rise = (b.z - a.z) / span

        def ground_z(d):
            return a.z + rise * d
        if kind == 'lattice':
            levels = [0.22 + (height - 0.36) * k / max(rails - 1, 1) for k in range(rails)]
            for z in levels:                                   # rails on the front of the posts, a little past them
                r = 0.017 * rng.uniform(0.9, 1.1)
                lift = rng.uniform(-0.008, 0.008)
                bamboo.cane(a + UP * (z + lift) + out * (post_r + r) - ahead * 0.06, b + UP * (z - lift) + out * (post_r + r) + ahead * 0.06,
                            r, rng, foot_z=None, joint=0.38)
            count = max(1, int(round(span / spacing)))
            for k in range(1, count):
                d = span * k / count + rng.uniform(-0.012, 0.012)
                r = 0.013 * rng.uniform(0.85, 1.2)
                in_front = (k % 2 == 0)
                depth = (post_r + 0.034 + r) if in_front else (post_r - 0.004 - r)
                foot = a + ahead * d + out * depth
                foot.z = ground_z(d)
                top_z = levels[-1] + rng.uniform(0.07, 0.13)
                bamboo.cane(foot - UP * 0.15, Vector((foot.x, foot.y, foot.z + top_z)), r, rng, foot_z=foot.z, joint=0.3, open_top=True)
                canes += 1
                for z in levels:
                    centre = a + ahead * d + out * (post_r + 0.017 + (0.017 + r if in_front else -0.002))
                    centre.z = a.z + rise * d + z
                    _tie(cord, centre + out * (r if in_front else 0.017), ahead, UP, out, 0.022, rng)
                    ties += 1
        else:
            levels = [0.25 + (height - 0.55) * k / max(rails - 1, 1) for k in range(rails)]
            d = post_r + 0.002
            while d < span - post_r - 0.012:                   # canes side by side, touching
                r = 0.0145 * rng.uniform(0.85, 1.15)
                d += r
                foot = a + ahead * d
                foot.z = ground_z(d)
                bamboo.cane(foot - UP * 0.12, Vector((foot.x, foot.y, foot.z + height - 0.05 + rng.uniform(-0.004, 0.004))), r, rng,
                            foot_z=foot.z, joint=0.28)
                d += r + rng.uniform(0.0, 0.002)
                canes += 1
            for z in levels:                                   # pairs of half-round rails on the front
                r = 0.02 * rng.uniform(0.9, 1.1)
                start = a + UP * z + out * 0.016 - ahead * 0.01
                end = b + UP * z + out * 0.016 + ahead * 0.01
                bamboo.cane(start, end, r, rng, joint=0.4, half=True, out=out)
                n = max(2, int(round(span / 0.3)))
                for k in range(1, n):
                    centre = a + ahead * (span * k / n)
                    centre.z = a.z + rise * span * k / n + z
                    _tie(cord, centre + out * (0.016 + r), ahead, UP, out, 0.026, rng)
                    ties += 1
            cap_r = 0.026                                      # the cap: a split bamboo over the canes' tops
            bamboo.cane(a + UP * (height - 0.05 + cap_r * 0.25) - ahead * 0.01, b + UP * (height - 0.05 + cap_r * 0.25) + ahead * 0.01,
                        cap_r, rng, joint=0.45, half=True, out=UP)
    target = collection
    if target is None:
        target = bpy.data.collections.new('bamboo_fence')
        bpy.context.scene.collection.children.link(target)
    bamboo_mat = (store.material(material) if isinstance(material, str) else material) if material is not None else bamboo_material(new)
    cord_mat = (store.material(cord_material) if isinstance(cord_material, str) else cord_material) if cord_material is not None else black_cord()
    made = {'bamboo': bamboo.make('bamboo fence', bamboo_mat, target)}
    made['bamboo']['canes'] = canes
    made['bamboo']['posts'] = len(feet)
    made['cord'] = cord.make('bamboo fence ties', cord_mat, target) if cord.verts else None
    if made['cord'] is not None:
        made['cord']['ties'] = ties
    return made


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of bamboo_fence.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--points', help='the fence\'s line as "x,y,z x,y,z ..."; makes a new file unless --blend is given')
    parser.add_argument('--blend', help='open this .blend file first')
    parser.add_argument('--line', help='the name of a curve or line-mesh object in the --blend file')
    parser.add_argument('--ground', help='the name of a ground mesh object in the --blend file')
    parser.add_argument('--kind', default='lattice', choices=list(KINDS), help="'lattice' or 'close'; default lattice")
    parser.add_argument('--height', type=float, default=None, help='the ground to the post tops, metres; default 1.0 lattice, 1.6 close')
    parser.add_argument('--post-spacing', type=float, default=1.8, help='about how far apart the posts stand; default 1.8')
    parser.add_argument('--spacing', type=float, default=None, help="a lattice's upright canes, middle to middle; default 0.27")
    parser.add_argument('--rails', type=int, default=None, help='how many rails; default 3 or 4 by the height')
    parser.add_argument('--new', action='store_true', help='new green-yellow canes instead of old greyed bamboo')
    parser.add_argument('--front', default='right', choices=['right', 'left'], help='which side the front faces; default right')
    parser.add_argument('--smooth', action='store_true', help='a smooth curve through the points')
    parser.add_argument('--seed', type=int, default=0, help='the same seed builds the same fence; default 0')
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
    elif args.points:
        line = [tuple(float(v) for v in p.split(',')) for p in args.points.split()]
    else:
        parser.error('give the line: --points, or --blend with --line')
    made = lay(line, kind=args.kind, height=args.height, post_spacing=args.post_spacing, spacing=args.spacing, rails=args.rails,
               new=args.new, front=args.front, ground=bpy.data.objects.get(args.ground) if args.ground else None,
               smooth=args.smooth, seed=args.seed)
    print('built %d posts, %d canes, %d ties' % (made['bamboo']['posts'], made['bamboo']['canes'], made['cord']['ties'] if made['cord'] else 0))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
