"""
What this file does: builds and draws "A barn on a farm": a farmyard after rain at dusk, about 1915, in the south of
England. A lane of trodden mud with cart ruts holding water runs from the eye to the gable end of a big weatherboarded
barn on a brick plinth under slate; its tall cart doors stand open (one leaf swung right back, one most of the way) and
the barn is lit inside: a cart stands side-on against the gold hay, a ladder leans on the hay mow, and a lantern hangs on
a nail by the door. On the left a dry-stone wall with a five-bar gate swung part open, a field, a hedge and a bare tree
against the last light; on the right a low limewashed rubble-stone cow house with a lean-to iron roof, a stable door
with its top half open and a lantern beside it. Against the cow-house wall: two milk churns, a barrow of muck, a
pitchfork, a besom and bucket; a trail of dropped hay from the barn door to the cow house.

Uses the kit's store (its tools, parts and materials) from /home/claude/build-54-barn/kit/store; the scene is built in
order: ground, tracks, grass/stones/litter, buildings, things, water, sky and light, camera, then drawn with Cycles to
an EXR and finished with the store's finish step (exposure 1.35, bloom, a warm veil on the horizon, softening).

    python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png        (defaults 540 960 48 final.png beside this file)
"""

import math
import os
import random
import sys
import time

KIT = '/home/claude/build-54-barn/kit'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(KIT, 'store', 'tools'))

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector, Euler, Matrix  # noqa: E402

import store  # noqa: E402
import ground  # noqa: E402
import tracks  # noqa: E402
import stones  # noqa: E402
import grass  # noqa: E402
import litter  # noqa: E402
import puddle  # noqa: E402
import sky_and_haze  # noqa: E402
import lay_boards  # noqa: E402
import finish  # noqa: E402

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 540
HEIGHT = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 48
OUT = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else os.path.join(HERE, 'final.png')
T0 = time.time()
EXPOSURE = 1.35


def log(*a):
    print('[%6.1fs]' % (time.time() - T0), *a, flush=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
rng = random.Random(54)

# ============================================================================================ helpers


class Boxes:
    """Many boxes in one mesh, each face carrying a 'tone' (0..1) and a material slot."""

    def __init__(self):
        self.v, self.f, self.tone, self.mat = [], [], [], []

    def box(self, centre, size, rot=(0.0, 0.0, 0.0), tone=0.5, mat=0, top_scale=1.0):
        cx, cy, cz = centre
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        R = Euler(rot).to_matrix()
        base = len(self.v)
        for (x, y, z) in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            k = top_scale if z > 0 else 1.0
            p = R @ Vector((x * sx * k, y * sy * k, z * sz))
            self.v.append((cx + p.x, cy + p.y, cz + p.z))
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append(tuple(base + i for i in q))
            self.tone.append(tone)
            self.mat.append(mat)

    def make(self, name, materials, collection=None, bevel=0.0):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in materials:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mat)
        a = me.attributes.new('tone', 'FLOAT', 'FACE')
        a.data.foreach_set('value', self.tone)
        me.update()
        ob = bpy.data.objects.new(name, me)
        (collection or scene.collection).objects.link(ob)
        if bevel > 0:
            mod = ob.modifiers.new('bevel', 'BEVEL')
            mod.width = bevel
            mod.segments = 2
            mod.limit_method = 'NONE'
        return ob


def mix_socket(node, ident):
    for s in list(node.inputs) + list(node.outputs):
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def tint(mat, value=0.6, sat=1.0, hue=0.5):
    """Darken (or desaturate) a material's base colour in place."""
    nt = mat.node_tree
    for b in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
        inp = b.inputs['Base Color']
        if inp.is_linked:
            src = inp.links[0].from_socket
            hs = nt.nodes.new('ShaderNodeHueSaturation')
            hs.inputs['Value'].default_value = value
            hs.inputs['Saturation'].default_value = sat
            hs.inputs['Hue'].default_value = hue
            nt.links.new(src, hs.inputs['Color'])
            nt.links.new(hs.outputs['Color'], inp)
        else:
            c = inp.default_value
            inp.default_value = (c[0] * value, c[1] * value, c[2] * value, 1.0)
    return mat


def dial(mat, **kw):
    w = mat.node_tree.nodes.get('Weather')
    if w is None:
        return mat
    for k, v in kw.items():
        name = {'mud_height': 'Mud height', 'mud_color': 'Mud color', 'edge_wear': 'Edge wear'}.get(k, k.capitalize())
        if name in w.inputs:
            w.inputs[name].default_value = v
    return mat


def mat_copy(name, new_name=None):
    m = store.material(name).copy()
    m.name = new_name or (name + ' (barn)')
    return m


def simple_material(name, colour, rough=0.7, noise_scale=12.0, noise_amt=0.35, bump=0.3, colour2=None, metallic=0.0,
                    stretch=None):
    """A plain made material: a colour broken by noise (two colours if colour2), with a bump."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N['Principled BSDF']
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    if stretch:
        mp.inputs['Scale'].default_value = stretch
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = noise_scale
    nz.inputs['Detail'].default_value = 8.0
    L.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    c2 = colour2 or tuple(c * (1.0 - noise_amt) for c in colour)
    ramp.color_ramp.elements[0].color = (*c2, 1.0)
    ramp.color_ramp.elements[1].color = (*colour, 1.0)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    if bump > 0:
        bp = N.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump
        bp.inputs['Distance'].default_value = 0.02
        L.new(nz.outputs['Fac'], bp.inputs['Height'])
        L.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def add_obj(name, mesh, collection=None):
    ob = bpy.data.objects.new(name, mesh)
    (collection or scene.collection).objects.link(ob)
    return ob


def cylinder(name, p0, p1, r0, r1=None, verts=8, material=None):
    """A tapered cylinder from p0 to p1."""
    r1 = r0 if r1 is None else r1
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r0, radius2=r1, depth=length)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = add_obj(name, me)
    ob.location = (p0 + p1) / 2
    ob.rotation_euler = axis.to_track_quat('Z', 'Y').to_euler()
    if material:
        me.materials.append(material)
    return ob


def lamp(name, kind, location, energy, colour, size=0.1, rotation=None, camera=True, glossy=True):
    light = bpy.data.lights.new(name, kind)
    light.energy = energy
    light.color = colour
    if kind == 'AREA':
        light.shape = 'RECTANGLE'
        light.size, light.size_y = size if isinstance(size, tuple) else (size, size)
    elif kind != 'SUN':
        light.shadow_soft_size = size
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    if rotation:
        obj.rotation_euler = rotation
    obj.visible_camera = camera
    obj.visible_glossy = glossy
    return obj


# ============================================================================================ materials
M_BOARDS = tint(mat_copy('MADE • weathered boards, peeling paint', 'barn boards, tarred and greyed'), value=0.62, sat=0.7)
M_PLANKS = dial(tint(mat_copy('SURFACE • old_planks_02', 'barn door planks'), value=0.85), Wet=0.25, Grime=0.6, mud_height=0.35)
M_ROUGH = dial(mat_copy('SURFACE • rough_wood', 'rough timber'), Grime=0.5)
M_INTERIOR = tint(mat_copy('SURFACE • old_planks_02', 'barn inside'), value=0.55)
M_BRICK = dial(mat_copy('SURFACE • brick_wall_02', 'barn plinth brick'), Wet=0.5, Grime=0.7, mud_height=0.35)
M_DRYSTONE = dial(mat_copy('SURFACE • old_stone_wall_02', 'dry stone'), Wet=0.35, Grime=0.5, mud_height=0.25)
M_LIMEWASH = dial(mat_copy('SURFACE • worn_plaster_wall', 'limewashed stone'), Wet=0.2, Grime=0.6, mud_height=0.55)
M_JOINTS = tint(dial(mat_copy('SURFACE • damaged_plaster', 'lime mortar joints'), Grime=0.8), value=0.55)
M_DOORPAINT = store.material('WOOD • peeling dark painted doors')
M_RUST = store.material('RUST • rain-aged iron')
M_IRON = store.material('IRON • soot-black lamp posts')
M_RECESS = store.material('RECESSES • near-black blue')
M_HAY = simple_material('hay', (0.6, 0.45, 0.19), rough=0.75, noise_scale=45.0, colour2=(0.16, 0.1, 0.035), bump=1.0,
                        stretch=(1.0, 1.0, 6.0))
M_STRAW = bpy.data.materials.new('dropped straw')
M_STRAW.use_nodes = True
_n = M_STRAW.node_tree.nodes
_l = M_STRAW.node_tree.links
_a = _n.new('ShaderNodeAttribute')
_a.attribute_name = 'tone'
_r = _n.new('ShaderNodeValToRGB')
_r.color_ramp.elements[0].color = (0.07, 0.05, 0.03, 1.0)
_r.color_ramp.elements[0].position = 0.25
_r.color_ramp.elements[1].color = (0.62, 0.47, 0.2, 1.0)
_r.color_ramp.elements[1].position = 0.75
_e = _r.color_ramp.elements.new(0.5)
_e.color = (0.38, 0.27, 0.11, 1.0)
_l.new(_a.outputs['Fac'], _r.inputs['Fac'])
_l.new(_r.outputs['Color'], _n['Principled BSDF'].inputs['Base Color'])
_n['Principled BSDF'].inputs['Roughness'].default_value = 0.55
M_MUCK = simple_material('muck', (0.075, 0.048, 0.025), rough=0.62, noise_scale=8.0, colour2=(0.035, 0.022, 0.012), bump=1.0)
M_HEDGE = simple_material('hedge', (0.035, 0.045, 0.035), rough=0.9, noise_scale=3.0, colour2=(0.015, 0.02, 0.018), bump=0.5)
M_BARK = store.material('MADE • wet bark')
M_FIELD = simple_material('far field', (0.06, 0.07, 0.045), rough=0.85, noise_scale=0.3, colour2=(0.035, 0.04, 0.03), bump=0.0)
M_SACK = store.material('SURFACE • hessian_380')

# ============================================================================================ 1. the ground
LANE = [(0.55, -6.0, 0.0), (0.45, 2.0, 0.0), (0.2, 8.0, 0.0), (0.0, 12.5, 0.0), (0.0, 16.6, 0.0)]
yard = ground.make(size=(24.0, 46.0), location=(0.0, 14.0, 0.0), cell=0.1, relief=0.06, seed=5, soil='dark dirt')
ground.wet(yard, wetness=0.88)
log('ground made')

tracks.ruts(yard, [(1.0, -6.0, 0.0), (1.25, 2.0, 0.0), (1.85, 7.5, 0.0), (2.1, 10.0, 0.0)], vehicle='cart', passes=2, age=0.75, seed=5)
tracks.ruts(yard, LANE, vehicle='cart', passes=3, age=0.4, seed=2)
tracks.potholes(yard, LANE, at=[20.6], size=0.7, age=0.6, which='both', seed=3)
tracks.path(yard, [(2.55, -6.0, 0.0), (2.5, 4.0, 0.0), (2.45, 13.0, 0.0)], width=0.6, age=0.6, seed=1)
tracks.footprints(yard, [(2.5, 8.6, 0.0), (1.8, 11.0, 0.0), (1.2, 13.6, 0.0), (0.8, 15.7, 0.0)], age=0.15, seed=4)
tracks.footprints(yard, [(0.6, 15.6, 0.0), (1.4, 13.0, 0.0), (2.0, 10.6, 0.0), (2.55, 8.3, 0.0)], age=0.2, seed=6, start='right')
log('tracks carved')

way_pts = numpy.array([(p[0], p[1]) for p in LANE])


def lane_across(xy):
    """Distance from the lane's middle line (piecewise)."""
    d = numpy.full(len(xy), 1e9)
    for a, b in zip(way_pts[:-1], way_pts[1:]):
        ab = b - a
        t = numpy.clip(((xy - a) @ ab) / (ab @ ab), 0.0, 1.0)
        proj = a + t[:, None] * ab
        d = numpy.minimum(d, numpy.linalg.norm(xy - proj, axis=1))
    return d


def field(xy):
    return ((xy[:, 0] < -3.25) & (xy[:, 1] > 4.0)).astype(float)


def wall_feet(xy):
    x, y = xy[:, 0], xy[:, 1]
    wall_x = numpy.where(y < 8.35, -1.95 + (y + 4.5) / 12.85 * (-2.85 + 1.95), -2.85)
    left = ((x > wall_x - 0.1) & (x < wall_x + 0.85) & (y < 15.5)).astype(float)
    right = ((x > 2.75) & (x < 3.0) & (y < 13.2) & ((y < 7.4) | (y > 9.0))).astype(float)
    barn = ((y > 15.3) & (y < 15.85) & (numpy.abs(x) > 2.3) & (numpy.abs(x) < 4.6)).astype(float)
    return numpy.clip(left + right + barn, 0, 1)


def near_eye(xy):
    x, y = xy[:, 0], xy[:, 1]
    return ((y < 5.0) & (y > -3.0) & (numpy.abs(x) < 3.0)).astype(float)


def yard_floor(xy):
    x, y = xy[:, 0], xy[:, 1]
    return ((x > -2.6) & (x < 2.8) & (y < 15.6)).astype(float)


ground.detail(yard, area=near_eye, cell=0.015)


def lane_grass(xy):
    x, y = xy[:, 0], xy[:, 1]
    across = lane_across(xy)
    sides = numpy.clip((across - 1.0) / 0.5, 0.0, 1.0)
    middle = 0.4 * (across < 0.35)
    keep = ((y < 13.5) & (x > -2.6) & (x < 2.15)).astype(float)
    return numpy.clip(sides + middle, 0.0, 1.0) * keep


grass.grow(yard, area=lane_grass, layers=('turf', 'tussocks'), amount=0.9, seed=14)
grass.grow(yard, area=field, layers=('turf', 'tussocks'), amount=0.7, seed=2)
grass.grow(yard, area=wall_feet, layers=('turf', 'tussocks', 'weeds', 'herbs'), amount=1.4, seed=8)
stones.scatter(yard, area=yard_floor, layers=('pebbles', 'grit'), amount=0.7, where='hollows', seed=3)
stones.scatter(yard, area=wall_feet, layers=('rocks', 'pebbles'), amount=1.0, where='hollows', seed=9)
litter.scatter(yard, area=near_eye, kinds=('twigs', 'leaves'), amount=0.8, seed=5)
stones.scatter(yard, area=near_eye, layers=('rocks', 'pebbles'), amount=1.6, where='crowns', seed=12)
log('grass, stones, litter')

# a far field to the horizon, under everything
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400.0)
me = bpy.data.meshes.new('far field')
bm.to_mesh(me)
bm.free()
far = add_obj('far field', me)
far.location = (0, 200, -0.08)
me.materials.append(M_FIELD)


def gz(x, y):
    return ground.height_at(yard, x, y)


# ============================================================================================ 2. the barn
BARN_X0, BARN_X1, BARN_Y0, BARN_Y1, BARN_H = -4.5, 4.5, 16.0, 30.0, 4.6
DOOR_X0, DOOR_X1, DOOR_H = -1.8, 1.8, 3.8
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
me = bpy.data.meshes.new('barn')
bm.to_mesh(me)
bm.free()
barn = add_obj('barn', me)
barn.scale = (BARN_X1 - BARN_X0, BARN_Y1 - BARN_Y0, BARN_H)
barn.location = ((BARN_X0 + BARN_X1) / 2, (BARN_Y0 + BARN_Y1) / 2, BARN_H / 2)
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = barn
barn.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
barn.select_set(False)
made = lay_boards.lay(barn, openings=[('front', 'door', DOOR_X0 - BARN_X0, 0.0, DOOR_X1 - DOOR_X0, DOOR_H),
                                      ('front', 'window', -0.55 - BARN_X0, 4.35, 1.1, 1.0)],
                      eaves='pitched', pitch=42.0, overhang=0.5, roof_material='MADE • slate roof',
                      boards_material=M_BOARDS, fill=False, seed=7)
log('barn boarded', dict(made['boards'].items()) if made['boards'] else '')

# the barn's own box becomes a hollow shell with the doorway open into it
B = Boxes()
t = 0.12
cx = (BARN_X0 + BARN_X1) / 2
B.box((cx, (BARN_Y0 + BARN_Y1) / 2, 0.015), (BARN_X1 - BARN_X0, BARN_Y1 - BARN_Y0, 0.03), mat=1)            # floor
B.box((cx, (BARN_Y0 + BARN_Y1) / 2, BARN_H - 0.05), (BARN_X1 - BARN_X0, BARN_Y1 - BARN_Y0, 0.1))            # ceiling
B.box(((BARN_X0 + DOOR_X0) / 2, BARN_Y0 + t / 2, BARN_H / 2), (DOOR_X0 - BARN_X0, t, BARN_H))
B.box(((BARN_X1 + DOOR_X1) / 2, BARN_Y0 + t / 2, BARN_H / 2), (BARN_X1 - DOOR_X1, t, BARN_H))
B.box((0.0, BARN_Y0 + t / 2, (DOOR_H + BARN_H) / 2), (DOOR_X1 - DOOR_X0, t, BARN_H - DOOR_H))
B.box((BARN_X0 + t / 2, (BARN_Y0 + BARN_Y1) / 2, BARN_H / 2), (t, BARN_Y1 - BARN_Y0, BARN_H))
B.box((BARN_X1 - t / 2, (BARN_Y0 + BARN_Y1) / 2, BARN_H / 2), (t, BARN_Y1 - BARN_Y0, BARN_H))
B.box((cx, BARN_Y1 - t / 2, BARN_H / 2), (BARN_X1 - BARN_X0, t, BARN_H))
shell = B.make('barn shell', [M_INTERIOR, M_ROUGH])
barn.data = shell.data
bpy.data.objects.remove(shell)
store.mark(barn, ground=0.0)

# brick plinth round the foot of the walls, broken at the doorway
P = Boxes()
ph, pt = 0.5, 0.13
P.box(((BARN_X0 - pt + DOOR_X0) / 2, BARN_Y0 - pt / 2 - 0.02, ph / 2), (DOOR_X0 - BARN_X0 + pt, pt, ph))
P.box(((BARN_X1 + pt + DOOR_X1) / 2, BARN_Y0 - pt / 2 - 0.02, ph / 2), (BARN_X1 - DOOR_X1 + pt, pt, ph))
P.box((BARN_X0 - pt / 2 - 0.02, (BARN_Y0 + BARN_Y1) / 2, ph / 2), (pt, BARN_Y1 - BARN_Y0 + 0.3, ph))
P.box((BARN_X1 + pt / 2 + 0.02, (BARN_Y0 + BARN_Y1) / 2, ph / 2), (pt, BARN_Y1 - BARN_Y0 + 0.3, ph))
P.box(((BARN_X0 - pt + DOOR_X0) / 2, BARN_Y0 - pt - 0.02, ph + 0.02), (DOOR_X0 - BARN_X0 + pt + 0.04, 0.06, 0.05))   # a weathered top course
P.box(((BARN_X1 + pt + DOOR_X1) / 2, BARN_Y0 - pt - 0.02, ph + 0.02), (BARN_X1 - DOOR_X1 + pt + 0.04, 0.06, 0.05))
plinth = P.make('barn plinth', [M_BRICK], bevel=0.01)
store.use_material(plinth, M_BRICK, ground=0.0)


def plank_door(name, width, height, hinge, angle, inward_ledges=True, seed=0, planks=8):
    """A ledged and braced plank door leaf, hinged at `hinge` (x, y, z) on its left (-x) edge, swung `angle` degrees
    outwards (towards -y, positive swings the free edge towards the camera)."""
    r = random.Random(seed)
    D = Boxes()
    x = 0.0
    widths = [r.uniform(0.85, 1.15) for _ in range(planks)]
    k = width / sum(widths)
    for i, w in enumerate(widths):
        w *= k
        drop = r.uniform(0.0, 0.06)          # rotted ragged feet
        D.box((x + w / 2, 0.0, (height + drop) / 2), (w - 0.008, 0.032, height - drop), tone=r.random())
        x += w
    side = 1.0 if inward_ledges else -1.0
    for z in (0.35, height / 2, height - 0.35):
        D.box((width / 2, side * 0.034, z), (width - 0.08, 0.036, 0.16), tone=r.random())
    for z0, z1 in ((0.35, height / 2), (height / 2, height - 0.35)):         # braces rising from the hinge side
        dx, dz = width - 0.3, z1 - z0
        L = math.hypot(dx, dz)
        D.box((width / 2, side * 0.034, (z0 + z1) / 2), (L, 0.034, 0.13), rot=(0.0, -math.atan2(dz, dx), 0.0), tone=r.random())
    for z in (0.35, height / 2, height - 0.35):                                 # strap hinges outside
        D.box((0.45, -side * 0.024, z), (0.9, 0.012, 0.05), mat=1)
        D.box((0.06, -side * 0.024, z), (0.1, 0.03, 0.09), mat=1)
    ob = D.make(name, [M_PLANKS, M_RUST])
    ob.location = hinge
    ob.rotation_euler = (0.0, 0.0, math.radians(-angle))
    return ob


FRONT = BARN_Y0 - 0.075   # outside face of the boards
plank_door('cart door left', 1.8, DOOR_H - 0.05, (DOOR_X0, FRONT, 0.03), 100.0, seed=1, planks=8)
# the right leaf is hinged on the right: build it mirrored
right = plank_door('cart door right', 1.8, DOOR_H - 0.05, (0, 0, 0), 0.0, seed=2, planks=8)
right.scale = (-1.0, 1.0, 1.0)
right.location = (DOOR_X1, FRONT, 0.03)
right.rotation_euler = (0.0, 0.0, math.radians(68.0))
loft = plank_door('loft door', 1.1, 1.0, (-0.55, FRONT - 0.01, 4.35), 0.0, seed=3, planks=5)
VS = Boxes()                                   # narrow slits for air high in the gable, with a sill and head board each
for vx in (-0.55, 0.0, 0.55):
    VS.box((vx, FRONT - 0.005, 6.55), (0.11, 0.03, 0.75), mat=0)
    VS.box((vx, FRONT - 0.03, 6.14), (0.22, 0.06, 0.05), mat=1, tone=0.4)
    VS.box((vx, FRONT - 0.03, 6.96), (0.22, 0.06, 0.05), mat=1, tone=0.6)
VS.make('gable air slits', [M_RECESS, M_PLANKS])
# a threshold timber across the doorway, worn
th = Boxes()
th.box((0.0, BARN_Y0 + 0.02, 0.04), (DOOR_X1 - DOOR_X0, 0.22, 0.09), tone=0.3)
store.use_material(th.make('threshold', [M_ROUGH], bevel=0.015), M_ROUGH, ground=0.0)

# inside: posts, braces and tie beam of the first two bays
T = Boxes()
for yy in (19.0, 23.5, 28.0):
    for xx in (-2.3, 2.3):
        T.box((xx, yy, BARN_H / 2), (0.26, 0.26, BARN_H), tone=rng.random())
        s = 1.0 if xx < 0 else -1.0
        T.box((xx + s * 0.55, yy, BARN_H - 0.75), (1.4, 0.15, 0.15), rot=(0.0, s * math.radians(-45), 0.0), tone=rng.random())
    T.box((0.0, yy, BARN_H - 0.3), (BARN_X1 - BARN_X0, 0.28, 0.3), tone=rng.random())
frame = T.make('barn frame', [M_ROUGH], bevel=0.01)
store.use_material(frame, M_ROUGH, ground=0.0)


def hay_stack(name, x0, x1, y0, y1, h, seed):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=14, use_grid_fill=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = add_obj(name, me)
    ob.scale = (x1 - x0, y1 - y0, h)
    ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, h / 2)
    tex = bpy.data.textures.new(name + ' lumps', 'CLOUDS')
    tex.noise_scale = 0.35
    tex.noise_depth = 4
    mod = ob.modifiers.new('lumps', 'DISPLACE')
    mod.texture = tex
    mod.strength = 0.35
    mod.mid_level = 0.5
    mod.texture_coords = 'GLOBAL'
    ob.modifiers.new('smooth', 'SUBSURF').levels = 1
    me.materials.append(M_HAY)
    return ob


hay_stack('hay left', -4.35, -2.55, 17.0, 29.6, 4.2, 1)
hay_stack('hay right', 2.55, 4.35, 21.8, 29.6, 3.6, 2)
hay_stack('hay back', -4.3, 4.3, 25.0, 29.7, 4.45, 4)


def hay_heap(name, x, y, rx, ry, h, seed):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = add_obj(name, me)
    ob.scale = (rx, ry, h)
    ob.location = (x, y, 0.0)
    tex = bpy.data.textures.new(name + ' lumps', 'CLOUDS')
    tex.noise_scale = 0.3
    tex.noise_depth = 4
    mod = ob.modifiers.new('lumps', 'DISPLACE')
    mod.texture = tex
    mod.strength = 0.25
    mod.texture_coords = 'GLOBAL'
    me.materials.append(M_HAY)
    return ob


hay_heap('hay heap', -1.0, 23.4, 1.5, 1.3, 1.25, 5)
LD = Boxes()
lean = math.radians(16)
for xx in (-1.55, -1.05):
    LD.box((xx, 24.15 - 1.9 * math.sin(lean) / 1.0 * 0.5, 1.9), (0.06, 0.07, 3.9), rot=(-lean, 0, 0), tone=0.4)
for k in range(11):
    zz = 0.3 + k * 0.33
    yy = 24.6 - (3.9 - zz) * math.tan(lean) * 0.0 - (1.9 - zz) * math.tan(lean)
    LD.box((-1.3, yy - 0.55, zz), (0.5, 0.035, 0.035), tone=0.5)
ladder = LD.make('hay ladder', [M_ROUGH], bevel=0.006)
store.use_material(ladder, M_ROUGH, ground=0.0)
hay_heap('hay heap 2', 1.4, 24.2, 1.2, 1.0, 1.6, 6)


def straw_clump(cx, cy, n=90, spread=0.35, seed=0, lift=0.0, height=0.06, length=(0.08, 0.26), trodden=0.3):
    """A forkful of hay dropped and partly trodden: strands tangled round a middle, the outer ones pressed dark into the mud."""
    r = random.Random(seed)
    g0 = gz(cx, cy)
    for _ in range(n):
        dx, dy = r.gauss(0.0, spread * 0.45), r.gauss(0.0, spread * 0.45)
        d = min(1.0, math.hypot(dx, dy) / spread)
        x, y = cx + dx, cy + dy
        z = g0 + lift + r.uniform(0.0, height) * (1.0 - d) ** 1.5
        L = r.uniform(*length)
        tone = r.uniform(0.55, 1.0) if r.random() > trodden * (0.4 + d) else r.uniform(0.0, 0.5)
        STRAW.box((x, y, z + 0.003), (L, 0.004, 0.003), rot=(r.uniform(-0.5, 0.5), r.uniform(-0.35, 0.35), r.uniform(0, math.pi)),
                  tone=tone)


STRAW = Boxes()
for i, (sx, sy, n, sp) in enumerate([(0.4, 15.9, 520, 0.8), (-1.0, 16.1, 260, 0.45), (1.15, 14.5, 260, 0.32), (1.6, 12.8, 220, 0.3),
                                     (2.05, 10.9, 200, 0.28), (2.3, 9.3, 300, 0.36), (1.95, 8.3, 160, 0.25), (2.2, 3.3, 200, 0.3),
                                     (1.9, 2.4, 120, 0.22), (-0.95, 0.9, 150, 0.25)]):
    straw_clump(sx, sy, n=n, spread=sp, seed=10 + i)
# loose hay on the barn floor
for i in range(6):
    straw_clump(rng.uniform(-1.6, 1.6), rng.uniform(16.4, 20.5), n=260, spread=0.6, seed=40 + i, lift=0.03, trodden=0.1)
straw = STRAW.make('dropped straw', [M_STRAW])
import stain
stain.on_wall(barn, 'front', 0.0, DOOR_X0 - BARN_X0, 0.45, 1.25, kind='mud', strong_at='bottom', strength=0.9, offset=0.085, seed=2)
stain.on_wall(barn, 'front', DOOR_X1 - BARN_X0, BARN_X1 - BARN_X0, 0.45, 1.2, kind='mud', strong_at='bottom', strength=0.9, offset=0.085, seed=3)
stain.on_wall(barn, 'front', 0.3, DOOR_X0 - BARN_X0 - 0.2, 3.9, 4.7, kind='damp', strong_at='top', strength=0.7, offset=0.085, seed=4)
log('barn built')

# ============================================================================================ 3. the cow house (right)
BY_X0, BY_X1, BY_Y0, BY_Y1, BY_H = 3.05, 7.05, 2.4, 13.2, 2.35
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
me = bpy.data.meshes.new('cow house')
bm.to_mesh(me)
bm.free()
byre = add_obj('cow house', me)
byre.scale = (BY_X1 - BY_X0, BY_Y1 - BY_Y0, BY_H)
byre.location = ((BY_X0 + BY_X1) / 2, (BY_Y0 + BY_Y1) / 2, BY_H / 2)
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = byre
byre.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
byre.select_set(False)
byre_made = lay_boards.lay(byre, sides=['right'], eaves='lean-to', high_side='right', pitch=12.0, overhang=0.45,
                           roof_material='SURFACE • rusty_corrugated_iron', boards_material=M_BOARDS, backing_material=None, seed=3)
store.use_material(byre, M_JOINTS, ground=0.0)
if byre_made['roof'] is not None:
    _dark = tint(M_BOARDS.copy(), value=0.5)
    _dark.name = 'cow house fascia, dark'
    byre_made['roof'].data.materials[1] = _dark
PITCH = math.tan(math.radians(12.0))

DOOR_Y0, DOOR_Y1, BDOOR_H = 7.6, 8.8, 1.9
WIN_Y0, WIN_Y1, WIN_Z0, WIN_Z1 = 4.4, 5.1, 1.05, 1.65


def rubble_face(Bx, origin, along, out, length, height_at, openings=(), seed=0, course=(0.1, 0.19), stone=(0.18, 0.46),
                relief=(0.03, 0.09), gap=0.012, tone_mat=0):
    """Rubble stones in rough courses over a wall face: origin is the face's left foot, along/out unit vectors (x, y),
    height_at(u) the face's top at u, openings as (u0, u1, z0, z1) to leave clear."""
    r = random.Random(seed)
    ox, oy = origin
    ax, ay = along
    nx, ny = out
    z = 0.0
    top_max = max(height_at(u) for u in numpy.linspace(0, length, 30))
    while z < top_max:
        ch = r.uniform(*course)
        u = -r.uniform(0.0, 0.2)
        while u < length:
            w = r.uniform(*stone)
            u0, u1 = max(u, 0.0), min(u + w, length)
            uc = (u0 + u1) / 2
            zc = z + ch / 2
            if u1 - u0 > 0.06 and zc + ch * 0.3 < height_at(uc):
                clear = all(not (u1 > a - 0.03 and u0 < b + 0.03 and zc + ch / 2 > c - 0.02 and zc - ch / 2 < d + 0.02) for a, b, c, d in openings)
                if clear:
                    depth = r.uniform(*relief)
                    hh = min(ch - gap, (height_at(uc) - z) - gap)
                    px = ox + ax * uc + nx * (depth / 2 - 0.02)
                    py = oy + ay * uc + ny * (depth / 2 - 0.02)
                    rot = (r.uniform(-0.06, 0.06), r.uniform(-0.06, 0.06), math.atan2(ay, ax) + r.uniform(-0.05, 0.05))
                    Bx.box((px, py, zc + r.uniform(-0.01, 0.01)), (u1 - u0 - gap, depth + 0.04, hh), rot=rot, tone=r.random(),
                           mat=tone_mat, top_scale=r.uniform(0.85, 1.0))
            u += w
        z += ch


R = Boxes()
# the face to the lane (-x): seen from outside its left end is at +y
rubble_face(R, (BY_X0, BY_Y1), (0.0, -1.0), (-1.0, 0.0), BY_Y1 - BY_Y0, lambda u: BY_H,
            openings=[(BY_Y1 - DOOR_Y1, BY_Y1 - DOOR_Y0, 0.0, BDOOR_H), (BY_Y1 - WIN_Y1, BY_Y1 - WIN_Y0, WIN_Z0, WIN_Z1)],
            seed=21)
# the end to the camera (-y), rising with the lean-to: left end at -x
rubble_face(R, (BY_X0, BY_Y0), (1.0, 0.0), (0.0, -1.0), BY_X1 - BY_X0, lambda u: BY_H + u * PITCH, seed=22)
cow_walls = R.make('cow house stones', [M_LIMEWASH], bevel=0.012)
store.use_material(cow_walls, M_LIMEWASH, ground=0.0)
# the gable wedge behind the end stones, and quoin-like big stones at the corner
G = Boxes()
for i in range(12):
    u0 = i * (BY_X1 - BY_X0) / 12
    G.box((BY_X0 + u0 + 0.17, BY_Y0 + 0.15, BY_H + (u0 + 0.17) * PITCH / 2 + 0.01), (0.34, 0.3, (u0 + 0.17) * PITCH + 0.02))
z = 0.0
k = 0
while z < BY_H - 0.1:
    h = rng.uniform(0.22, 0.3)
    long_y = (k % 2 == 0)
    G.box((BY_X0 - 0.05 + (0.0 if long_y else 0.2), BY_Y0 - 0.05 + (0.25 if long_y else 0.0), z + h / 2),
          (0.24 if long_y else 0.55, 0.6 if long_y else 0.24, h - 0.015), tone=rng.random())
    z += h
    k += 1
quoins = G.make('cow house corner', [M_LIMEWASH], bevel=0.015)
store.use_material(quoins, M_LIMEWASH, ground=0.0)

# stable door (two halves, top open), door frame, window shutter
F = Boxes()
F.box((BY_X0 - 0.03, DOOR_Y0 - 0.06, BDOOR_H / 2), (0.16, 0.12, BDOOR_H), tone=0.3)
F.box((BY_X0 - 0.03, DOOR_Y1 + 0.06, BDOOR_H / 2), (0.16, 0.12, BDOOR_H), tone=0.4)
F.box((BY_X0 - 0.04, (DOOR_Y0 + DOOR_Y1) / 2, BDOOR_H + 0.08), (0.2, DOOR_Y1 - DOOR_Y0 + 0.4, 0.16), tone=0.5)
F.box((BY_X0 - 0.03, (WIN_Y0 + WIN_Y1) / 2, WIN_Z1 + 0.05), (0.14, WIN_Y1 - WIN_Y0 + 0.24, 0.1), tone=0.5)
F.box((BY_X0 - 0.05, (WIN_Y0 + WIN_Y1) / 2, WIN_Z0 - 0.04), (0.18, WIN_Y1 - WIN_Y0 + 0.2, 0.07), tone=0.6)
store.use_material(F.make('cow house frames', [M_ROUGH], bevel=0.01), M_ROUGH, ground=0.0)
hd = Boxes()
n = 5
for i in range(n):                                  # lower half door, shut
    w = (DOOR_Y1 - DOOR_Y0) / n
    drop = rng.uniform(0, 0.05)
    hd.box((BY_X0 - 0.02, DOOR_Y0 + w * (i + 0.5), (1.0 + drop) / 2 + 0.02), (0.035, w - 0.01, 1.0 - drop), tone=rng.random())
hd.box((BY_X0 - 0.045, (DOOR_Y0 + DOOR_Y1) / 2, 0.85), (0.03, DOOR_Y1 - DOOR_Y0 - 0.06, 0.13), tone=0.5)
hd.box((BY_X0 - 0.045, (DOOR_Y0 + DOOR_Y1) / 2, 0.25), (0.03, DOOR_Y1 - DOOR_Y0 - 0.06, 0.13), tone=0.5)
# the upper half, swung open back against the wall towards the camera
for i in range(n):
    w = (DOOR_Y1 - DOOR_Y0) / n
    hd.box((BY_X0 - 0.09, DOOR_Y0 - 0.06 - w * (i + 0.5), 1.47), (0.035, w - 0.01, 0.86), tone=rng.random())
# window shutter, open a crack
for i in range(4):
    w = (WIN_Y1 - WIN_Y0) / 4
    hd.box((BY_X0 - 0.06 - 0.03 * i, WIN_Y0 + w * (i + 0.5) - 0.02, (WIN_Z0 + WIN_Z1) / 2), (0.03, w - 0.008, WIN_Z1 - WIN_Z0 - 0.02),
           rot=(0, 0, math.radians(-14)), tone=rng.random())
store.use_material(hd.make('cow house door', [M_DOORPAINT], bevel=0.006), M_DOORPAINT, ground=0.0)
rc = Boxes()
rc.box((BY_X0 + 0.005, (DOOR_Y0 + DOOR_Y1) / 2, (1.0 + BDOOR_H) / 2 + 0.02), (0.02, DOOR_Y1 - DOOR_Y0, BDOOR_H - 1.0))
rc.box((BY_X0 + 0.005, (WIN_Y0 + WIN_Y1) / 2, (WIN_Z0 + WIN_Z1) / 2), (0.02, WIN_Y1 - WIN_Y0, WIN_Z1 - WIN_Z0))
rc.make('cow house dark inside', [M_RECESS])
log('cow house built')

# ============================================================================================ 4. the dry-stone wall and gate (left)
WALL_X = -2.85


def dry_wall(Bx, p0, p1, h=1.25, base=0.62, top=0.42, seed=0, skip=()):
    r = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    L = d.length
    a = d.normalized()
    n = Vector((-a.y, a.x))
    ang = math.atan2(a.y, a.x)
    z = 0.0
    while z < h - 0.12:
        ch = r.uniform(0.07, 0.15)
        half = (base + (top - base) * (z / h)) / 2
        for side in (-1, 1):
            u = -r.uniform(0, 0.3)
            while u < L:
                w = r.uniform(0.2, 0.5)
                u0, u1 = max(u, 0.0), min(u + w, L)
                if u1 - u0 > 0.08 and not any(s0 < (u0 + u1) / 2 < s1 for s0, s1 in skip):
                    dep = r.uniform(0.2, 0.32)
                    c = p0 + a * ((u0 + u1) / 2) + n * (side * (half - dep / 2 + r.uniform(-0.015, 0.025)))
                    Bx.box((c.x, c.y, z + ch / 2), (u1 - u0 - 0.015, dep, ch - 0.012),
                           rot=(r.uniform(-0.07, 0.07), side * r.uniform(0.02, 0.12), ang + r.uniform(-0.06, 0.06)), tone=r.random())
                u += w
        # the core between the faces
        c = p0 + a * (L / 2)
        z += ch
    # cope stones on edge along the top
    u = 0.0
    while u < L:
        tk = r.uniform(0.09, 0.2)
        if not any(s0 < u < s1 for s0, s1 in skip):
            ch = r.uniform(0.16, 0.32)
            c = p0 + a * (u + tk / 2)
            Bx.box((c.x, c.y, z + ch / 2 - 0.03), (tk - 0.015, top + r.uniform(0.0, 0.12), ch),
                   rot=(r.uniform(-0.08, 0.08), r.uniform(-0.3, 0.3), ang + r.uniform(-0.12, 0.12)), tone=r.random(),
                   top_scale=r.uniform(0.6, 0.95))
        u += tk
    # a dark core so nothing shows through
    Bx.box(((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, h / 2 - 0.05), (L, base - 0.22, h - 0.12), rot=(0, 0, ang), tone=0.0)
    return z


W = Boxes()
GATE_Y0, GATE_Y1 = 8.6, 11.6
dry_wall(W, (-1.95, -4.5), (WALL_X, GATE_Y0 - 0.25), seed=31)
dry_wall(W, (WALL_X, GATE_Y1 + 0.25), (BARN_X0 + 0.2, BARN_Y0 - 0.35), seed=32)
for i, (fx, fy) in enumerate([(-1.92, 3.1), (-2.2, 5.9), (-2.3, 12.9)]):       # slipped stones at the foot
    W.box((fx, fy, gz(fx, fy) + 0.05), (0.32, 0.22, 0.1), rot=(0.2, 0.1, rng.uniform(0, 3)), tone=rng.random())
drystone = W.make('dry-stone wall', [M_DRYSTONE], bevel=0.02)
store.use_material(drystone, M_DRYSTONE, ground=0.0)

# gate posts and a five-bar gate, swung part open into the field
GP = Boxes()
for gy in (GATE_Y0 - 0.12, GATE_Y1 + 0.12):
    GP.box((WALL_X, gy, 0.75), (0.24, 0.24, 1.6), rot=(rng.uniform(-0.02, 0.02), rng.uniform(-0.03, 0.03), 0), tone=rng.random())
GL, GHH = GATE_Y1 - GATE_Y0 - 0.1, 1.15
gate = Boxes()
gate.box((0.06, 0.0, GHH / 2 + 0.1), (0.1, 0.09, GHH + 0.15), tone=0.4)          # hanging stile
gate.box((GL - 0.05, 0.0, GHH / 2 + 0.1), (0.08, 0.08, GHH), tone=0.6)            # head stile
for i, zz in enumerate((0.22, 0.42, 0.62, 0.84, 1.1)):
    gate.box((GL / 2, 0.0, zz), (GL, 0.045 if i < 4 else 0.08, 0.09 if i < 4 else 0.11), tone=rng.random())
dl = math.hypot(GL - 0.2, 0.85)
gate.box((GL / 2, 0.03, 0.66), (dl, 0.04, 0.09), rot=(0, -math.atan2(0.85, GL - 0.2), 0), tone=0.5)
gate.box((0.15, -0.05, 0.3), (0.18, 0.012, 0.04), mat=1)
gate.box((0.15, -0.05, 1.05), (0.18, 0.012, 0.04), mat=1)
gate_ob = gate.make('five-bar gate', [M_ROUGH, M_RUST], bevel=0.008)
gate_ob.location = (WALL_X, GATE_Y1, 0.0)
gate_ob.rotation_euler = (math.radians(1.2), 0.0, math.radians(-90 + 38))          # swung part open into the yard
store.use_material(GP.make('gate posts', [M_ROUGH], bevel=0.015), M_ROUGH, ground=0.0)
log('wall and gate built')

# ============================================================================================ 5. hedge and a bare tree beyond the field
hb = bmesh.new()
noise_r = random.Random(77)
xs = numpy.arange(-90.0, 30.0, 0.35)
hts = 1.7 + 0.5 * numpy.sin(xs * 0.21 + 1.3) + 0.35 * numpy.sin(xs * 0.67) + numpy.array([noise_r.uniform(-0.35, 0.35) for _ in xs])
for row, (dy, k) in enumerate(((0.0, 1.0), (1.2, 1.12))):
    verts = []
    for x, h in zip(xs, hts):
        verts.append(hb.verts.new((x, 52.0 + dy, -0.2)))
        verts.append(hb.verts.new((x + noise_r.uniform(-0.15, 0.15), 52.0 + dy, h * k + noise_r.uniform(-0.25, 0.3))))
    for i in range(len(xs) - 1):
        hb.faces.new((verts[2 * i], verts[2 * i + 2], verts[2 * i + 3], verts[2 * i + 1]))
me = bpy.data.meshes.new('hedge')
hb.to_mesh(me)
hb.free()
hedge = add_obj('hedge', me)
me.materials.append(M_HEDGE)


def tree(base, height, seed=0):
    r = random.Random(seed)
    TB = bmesh.new()

    def branch(p, d, length, radius, depth):
        q = p + d * length
        # a tapered cylinder between p and q
        mat = Matrix.Translation((p + q) / 2) @ d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(TB, cap_ends=False, segments=6, radius1=radius, radius2=radius * 0.72, depth=length, matrix=mat)
        if depth == 0 or radius < 0.006:
            return
        kids = 2 if depth > 6 else r.choice((2, 3, 3))
        for k in range(kids):
            nd = (d * 0.8 + Vector((r.uniform(-0.9, 0.9), r.uniform(-0.9, 0.9), r.uniform(-0.15, 0.45)))).normalized()
            branch(q, nd, length * r.uniform(0.6, 0.78), radius * 0.66, depth - 1)

    branch(Vector(base), Vector((0.05, 0.0, 1.0)).normalized(), height * 0.3, height * 0.03, 8)
    me = bpy.data.meshes.new('bare tree')
    TB.to_mesh(me)
    TB.free()
    ob = add_obj('bare tree', me)
    me.materials.append(M_BARK)
    return ob


tree((-12.0, 44.0, 0.0), 13.0, seed=4)
tree((11.0, 47.0, 0.0), 11.0, seed=9)
log('hedge and trees')

# ============================================================================================ 6. the things people left


def stand(name, x, y, turn=0.0, lift=0.0, **options):
    return store.add_part(name, location=(x, y, gz(x, y) + lift), turn=turn, **options)


stand('coal_cart', 0.05, 20.3, turn=-90.0, loaded=False, prop=True)
stand('milk_churn', 2.62, 7.15, turn=20.0)
stand('milk_churn', 2.68, 6.62, turn=-35.0, seed=1)
barrow = stand('wheelbarrow', 2.35, 4.2, turn=-160.0, loaded='none', seed=2)
stand('besom_and_bucket', 2.62, 6.02, turn=-90.0, seed=3)
lantern = store.add_part('hurricane_lantern', location=(2.15, FRONT - 0.12, 1.62))
bpy.data.objects['hurricane_lantern light'].data.energy = 110.0
cow_lantern = store.add_part('hurricane_lantern', location=(BY_X0 - 0.2, DOOR_Y0 - 0.28, 1.5), seed=2)
for ob in bpy.data.objects:
    if ob.name.startswith('hurricane_lantern light') and ob.name != 'hurricane_lantern light':
        ob.data.energy = 35.0
cylinder('cow lantern nail', (BY_X0 + 0.02, DOOR_Y0 - 0.28, 1.83), (BY_X0 - 0.2, DOOR_Y0 - 0.28, 1.82), 0.006, material=M_IRON)
# a nail for it
cylinder('lantern nail', (2.15, FRONT + 0.02, 1.95), (2.15, FRONT - 0.1, 1.94), 0.006, material=M_IRON)

# muck heaped in the barrow
mb = bmesh.new()
bmesh.ops.create_icosphere(mb, subdivisions=3, radius=1.0)
me = bpy.data.meshes.new('muck')
mb.to_mesh(me)
mb.free()
muck = add_obj('muck', me)
muck.scale = (0.3, 0.42, 0.17)
bx, by = 2.35, 4.2
muck.location = (bx + 0.05, by + 0.1, gz(bx, by) + 0.62)
mt = bpy.data.textures.new('muck lumps', 'CLOUDS')
mt.noise_scale = 0.25
mm = muck.modifiers.new('lumps', 'DISPLACE')
mm.texture = mt
mm.strength = 0.12
me.materials.append(M_MUCK)
STRAW_M = Boxes()
_r = random.Random(5)
for _ in range(70):
    a = _r.uniform(0, 2 * math.pi)
    d = 0.22 * math.sqrt(_r.random())
    STRAW_M.box((bx + 0.05 + d * math.cos(a), by + 0.1 + 1.3 * d * math.sin(a), gz(bx, by) + 0.62 + 0.15 * (1 - d / 0.22) + _r.uniform(-0.02, 0.03)),
                (_r.uniform(0.08, 0.2), 0.004, 0.003), rot=(_r.uniform(-0.4, 0.4), _r.uniform(-0.4, 0.4), _r.uniform(0, math.pi)),
                tone=_r.uniform(0.2, 0.9))
STRAW_M.make('straw in the muck', [M_STRAW])

# the pitchfork leant on the barn wall, left of the door
foot = Vector((2.5, 5.45, gz(2.5, 5.45)))
topp = Vector((2.9, 5.62, 1.42))
cylinder('pitchfork shaft', foot, topp, 0.017, material=M_ROUGH)
axis = (topp - foot).normalized()
side = axis.cross(Vector((1, 0, 0))).normalized()
for k in (-1, 0, 1):
    s = topp + side * (k * 0.055)
    mid = s + axis * 0.16 + Vector((-0.012, 0, 0))
    tip = mid + axis * 0.14 + Vector((-0.03, 0, 0))
    cylinder('tine', topp, s + axis * 0.02, 0.008, material=M_RUST)
    cylinder('tine', s + axis * 0.02, mid, 0.0065, material=M_RUST)
    cylinder('tine', mid, tip, 0.0055, 0.002, material=M_RUST)
cylinder('fork cross', topp - side * 0.06, topp + side * 0.06, 0.009, material=M_RUST)

# an empty sack hung over the cart's side and one dropped by the churns
sk = Boxes()
sk.box((2.45, 6.15, gz(2.45, 6.15) + 0.04), (0.55, 0.42, 0.06), rot=(0.05, -0.08, 0.6), tone=0.4)
sk.box((2.25, 6.35, gz(2.25, 6.35) + 0.09), (0.35, 0.3, 0.05), rot=(0.25, 0.1, 0.9), tone=0.6)
store.use_material(sk.make('sacks', [M_SACK], bevel=0.02), M_SACK, ground=0.0)
log('props placed')

# ============================================================================================ 7. water
spots = ground.spots(yard)
ground.fill(yard, spots, seed=1)
puddle.make((-0.35, 6.3, gz(-0.35, 6.3)), size=(3.4, 0.75), turn=86.0, ground=yard, seed=4)
puddle.make((1.2, 11.2, gz(1.2, 11.2)), size=(1.4, 0.6), turn=70.0, ground=yard, seed=7)
puddle.make((0.25, 3.5, gz(0.25, 3.5)), size=(2.6, 0.8), turn=84.0, ground=yard, seed=11)
log('water')

# ============================================================================================ 8. sky, haze, light
sky_and_haze.sky(scene, horizon=(0.95, 0.42, 0.13), low_band=(0.42, 0.2, 0.11), strength=0.8, clouds=1.0, seed=3)
sky_and_haze.haze(low=(-60, -8, 0), high=(60, 15.7, 28), density=0.0024)
sky_and_haze.haze(low=(-60, 30.5, 0), high=(60, 160, 28), density=0.0024)

WARM = (1.0, 0.58, 0.26)
lamp('barn inside', 'POINT', (-1.7, 21.8, 3.9), 600.0, WARM, 0.4, camera=False)
lamp('barn inside low', 'POINT', (-1.2, 22.5, 1.4), 170.0, WARM, 0.4, camera=False)
store.add_part('hurricane_lantern', location=(2.12, 18.84, 1.75), turn=0.0)
lamp('door spill', 'AREA', (0.0, 16.6, 2.2), 520.0, WARM, (3.2, 3.4), rotation=(math.radians(-90), 0, 0), camera=False, glossy=False)
lamp('sky fill', 'AREA', (0.0, 6.0, 9.0), 380.0, (0.5, 0.66, 1.0), 12.0, camera=False, glossy=False)
moon = bpy.data.objects.new('moon fill', bpy.data.lights.new('moon fill', 'SUN'))
moon.data.energy = 0.58
moon.data.color = (0.45, 0.6, 1.0)
moon.data.angle = math.radians(3)
moon.rotation_euler = (math.radians(62), 0.0, math.radians(8))
scene.collection.objects.link(moon)
rim = bpy.data.objects.new('dusk rim', bpy.data.lights.new('dusk rim', 'SUN'))
rim.data.energy = 1.6
rim.data.color = (1.0, 0.55, 0.3)
rim.data.angle = math.radians(2)
rim.rotation_euler = (math.radians(84), 0.0, math.radians(200))          # the last light low from the far left
scene.collection.objects.link(rim)

# ============================================================================================ 9. camera
camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
camera.data.lens = 27
camera.data.shift_y = -0.06
camera.location = (0.25, -3.4, 1.62)
camera.rotation_euler = (Vector((0.0, 16.0, 2.75)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================================================ draw and finish
store.prepare_for_render(scene)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.cycles.transparent_max_bounces = 8
scene.cycles.volume_bounces = 0
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
raw = os.path.join(os.path.dirname(OUT), 'raw - ' + os.path.splitext(os.path.basename(OUT))[0] + '.exr')
scene.render.filepath = raw
log('rendering %dx%d at %d samples' % (WIDTH, HEIGHT, SAMPLES))
bpy.ops.render.render(write_still=True)
log('rendered')
finish.finish(raw, OUT, exposure=EXPOSURE, bloom=1.0, veil=0.35, veil_height=0.47, soften=0.5)
log('drew', OUT)
