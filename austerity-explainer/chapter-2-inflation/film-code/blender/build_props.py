# What this does: builds a few loose things for the near foreground of model-set shots (chapter 2,
# pages 3 and 8), as one .glb with separate named groups a page can copy and place: 'barrels' (three
# iron-hooped barrels, one on its side), 'crates' (a stack of timber crates and two sacks), 'lamp-post'
# (a cast-iron gas lamp with a lit head) and 'cart' (a two-wheeled hand cart). Out of focus at the
# bottom of a tall frame they fill the space the research calls the foreground layer, so the work
# goes into silhouettes: spoked wheels, bulging barrels with hoops and a chime lip, a glazed lantern,
# battened crates and lumpy sacks (see chapter-2/reference/22 Blender MCP notes, section C4).
#
# Run: /home/user/work/blender-env/bin/python build_props.py OUT.glb
#
# Kept for the pages: the group names 'barrels', 'crates', 'lamp-post', 'cart' (each built around its
# own origin), the marker 'lamp-post-light' at (0, 0, 1.17) and the material name 'lamp-glow'.

import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402  (imports bpy first)
import textures as tx  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Euler, Matrix, Vector  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'props.glb'
mk.reset()


# ------------------------------------------------------------------ pictures for this model only
# (written here rather than in textures.py, which other helpers use at the same time)

def _stretch(field, axis, length):
    """Smear noise along one axis (wood grain)."""
    out = np.zeros_like(field)
    for k in range(length): out += np.roll(field, k, axis=axis)
    out -= out.min()
    return out / max(1e-9, out.max())


def staves_picture(size=512, staves=10, seed=31):
    """Oak barrel staves running up the picture, with dark joints, per-stave tone and grain."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    index = np.floor(xs * staves).astype(int)
    in_x = (xs * staves) % 1
    tone = (0.78 + 0.34 * rng.random(staves))[index]
    grain = _stretch(tx.fractal_noise(size, size, rng, roughness=0.9), 0, 40)
    colour = np.array([118, 74, 42]) / 255
    base = colour[None, None, :] * (tone * (0.72 + 0.45 * grain))[..., None]
    ends = 0.78 + 0.22 * np.sin(np.pi * ys) ** 0.6           # grimier towards the chimes
    base *= ends[..., None]
    joint = np.minimum(in_x, 1 - in_x) < 0.035
    base = np.where(joint[..., None], base * 0.3, base)
    height = np.clip(np.minimum(in_x, 1 - in_x) / 0.07, 0, 1) * 0.8 + grain * 0.2
    return tx.to_picture(base), tx.normal_map(tx.blur(height), strength=3.0)


def weathered_picture(size=512, seed=32):
    """Weathered grey-brown cart timber, grain running across the picture (along a board's length)."""
    rng = np.random.default_rng(seed)
    grain = _stretch(tx.fractal_noise(size, size, rng, roughness=0.8), 1, 60)
    patches = tx.fractal_noise(size, size, rng, roughness=2.4)
    brown, grey = np.array([92, 66, 44]) / 255, np.array([128, 116, 98]) / 255
    mix = np.clip((patches - 0.35) * 2.2, 0, 1)[..., None]
    base = (brown * (1 - mix) + grey * mix) * (0.62 + 0.55 * grain)[..., None]
    cracks = _stretch((rng.random((size, size)) > 0.9975).astype(float), 1, 90) > 0.25
    base = np.where(cracks[..., None], base * 0.45, base)
    height = grain * 0.7 + (~cracks) * 0.3
    return tx.to_picture(base), tx.normal_map(tx.blur(height), strength=2.5)


def hessian_picture(size=256, threads=40, seed=33):
    """Coarse sacking: a loose weave with dirt blotches."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    weave = 0.5 + 0.25 * np.sin(xs * threads * 2 * np.pi) * np.sign(np.sin(ys * threads * np.pi)) \
        + 0.25 * np.sin(ys * threads * 2 * np.pi) * np.sign(np.sin(xs * threads * np.pi))
    dirt = tx.fractal_noise(size, size, rng, roughness=2.2)
    colour = np.array([124, 98, 66]) / 255
    base = colour[None, None, :] * (0.7 + 0.25 * weave + 0.25 * (dirt - 0.5))[..., None]
    return tx.to_picture(base), tx.normal_map(tx.blur(weave), strength=1.5)


def add_normal_map(material, picture, strength=1.0):
    """Hang a normal map on a material made by mk.material (Image (Non-Color) -> Normal Map -> BSDF)."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    tex = nodes.new('ShaderNodeTexImage'); tex.image = mk._image(f'{material.name}-normal', picture, False)
    nmap = nodes.new('ShaderNodeNormalMap'); nmap.inputs['Strength'].default_value = strength
    links.new(tex.outputs['Color'], nmap.inputs['Color'])
    links.new(nmap.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])
    return material


# -------------------------------------------------------------------------- materials (names kept)

stave_colour, stave_normal = staves_picture()
cart_colour, cart_normal = weathered_picture()
sack_colour, sack_normal = hessian_picture()
barrel_wood = add_normal_map(mk.material(None, name='barrel-wood', picture=stave_colour, roughness=0.7), stave_normal, 1.0)
iron = mk.material(None, name='iron', colour=(0.035, 0.038, 0.04), roughness=0.45, metallic=0.6)
timber = mk.material('planks', name='crate-timber', roughness=0.85)
frame_wood = mk.material(None, name='crate-frame', colour=(0.075, 0.05, 0.03), roughness=0.85)
sacking = add_normal_map(mk.material(None, name='sacking', picture=sack_colour, roughness=0.95), sack_normal, 1.0)
lamp = mk.material(None, name='lamp-glow', colour=(1.0, 0.8, 0.5), glow=(1.0, 0.72, 0.4), glow_strength=3.0, roughness=0.4)
wheel_wood = add_normal_map(mk.material(None, name='cart-wood', picture=cart_colour, roughness=0.85), cart_normal, 1.0)


# --------------------------------------------------------------------------------- shape helpers

def soft(obj, width=None, segments=1):
    """Turn mk's bevel into one that catches a soft highlight (notes B1, B2): harden normals, arc
    mitres, smooth shading, then weighted normals so flat faces stay flat."""
    bevel = obj.modifiers.get('bevel')
    if bevel is None:
        bevel = obj.modifiers.new('bevel', 'BEVEL'); bevel.limit_method = 'ANGLE'
    if width: bevel.width = width
    bevel.segments = segments
    bevel.angle_limit = math.radians(30)
    bevel.use_clamp_overlap = True
    bevel.miter_outer = 'MITER_ARC'
    bevel.harden_normals = True
    bevel.face_strength_mode = 'FSTR_AFFECTED'
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    wn = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')
    wn.mode = 'FACE_AREA'; wn.keep_sharp = True; wn.use_face_influence = True
    return obj


def lathe(name, profile, sides=16, at=(0, 0, 0), rotate=(0, 0, 0), material=None, closed=False,
          u_repeat=1.0, v_length=1.0, cap_units=0.15, sharp=40):
    """Spin a half profile [(radius, z), ...] round z (a turned part: barrel, hub, lamp column; the
    same result as the Screw modifier, notes B7, but with texture coordinates of our own).
    Walk the profile with the solid on the left (bottom to top on the outside) so faces point out.
    Sides get wrap-around texture coordinates (u round, v up); flat rings and caps get flat ones."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))] * sides)
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z)) for k in range(sides)])
    uv = bm.loops.layers.uv.new('UVMap')
    pairs = list(range(len(profile) - 1)) + ([len(profile) - 1] if closed else [])
    for i in pairs:
        j = (i + 1) % len(profile)
        for k in range(sides):
            kk = (k + 1) % sides
            quad = [(rings[i][k], k, i), (rings[i][kk], k + 1, i), (rings[j][kk], k + 1, j), (rings[j][k], k, j)]
            seen, verts = set(), []
            for v, ku, pi in quad:
                if v not in seen: seen.add(v); verts.append((v, ku, pi))
            if len(verts) < 3: continue
            face = bm.faces.new([v for v, _, _ in verts])
            face.smooth = True
            face.normal_update()
            flat = abs(face.normal.z) > 0.7
            for loop, (v, ku, pi) in zip(face.loops, verts):
                if flat: loop[uv].uv = (v.co.x / cap_units, v.co.y / cap_units)
                else: loop[uv].uv = (ku / sides * u_repeat, profile[pi][1] / v_length)
    bm.to_mesh(mesh); bm.free()
    mesh.set_sharp_from_angle(angle=math.radians(sharp))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at; obj.rotation_euler = rotate
    if material is not None: mesh.materials.append(material)
    return obj


def frame(origin, yaw=0.0, pitch=0.0):
    """A local frame: place parts in a crate's or cart bed's own coordinates."""
    return Matrix.Translation(origin) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'Y')


def framed_box(name, frame_, size, local, material, local_rot=(0, 0, 0), bevel=0.0, segments=1):
    """mk.box placed in a local frame (location and rotation follow the frame)."""
    world = frame_ @ Vector(local)
    rot = (frame_.to_3x3() @ Euler(local_rot).to_matrix()).to_euler()
    obj = mk.box(name, size, at=tuple(world), material=material, bevel=bevel, rotate=tuple(rot))
    return soft(obj, segments=segments) if bevel else obj


def strut(name, p0, p1, thickness, material):
    """A thin bar from p0 to p1 (lantern corner bars)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    return mk.box(name, (thickness, thickness, d.length), at=tuple((p0 + p1) / 2), material=material,
                  rotate=tuple(d.to_track_quat('Z', 'Y').to_euler()))


def sack(name, at, yaw, length=0.25, width=0.16, height=0.1, seed=1):
    """A filled grain sack lying on its side: a lumpy, squarish pillow whose shoulders gather into a
    tied neck with a flared tuft of cloth (long axis along local y, the neck at +y)."""
    rnd = random.Random(seed)
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=10, radius=1.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, 'X'))  # poles on y
    lump = {v: 1 + rnd.uniform(-0.08, 0.08) for v in bm.verts}
    for v in bm.verts:   # smooth the lumps once so they read as filling, not spikes
        near = [e.other_vert(v) for e in v.link_edges]
        lump[v] = (lump[v] * 2 + sum(lump[n] for n in near) / max(1, len(near))) / 3
    body = length / 2
    for v in bm.verts:
        x, y, z = v.co
        sq = lambda a: math.copysign(abs(a) ** 0.75, a)          # squarer than a ball, like a pillow
        x, z = sq(x) * lump[v], sq(z) * lump[v]
        if y > 0.25: x, z = x * (1 - 0.5 * (y - 0.25) / 0.65), z * (1 - 0.5 * (y - 0.25) / 0.65)   # shoulders
        if y > 0.9: x, z, y = x * 0.3, z * 0.3, 0.9             # the gathered neck
        z = max(z, -0.8)                                        # settles flat on the ground
        v.co = Vector((x * width / 2, y * body, (z + 0.8) / 1.8 * height))
    for f in bm.faces: f.smooth = True
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at; obj.rotation_euler = (0, 0, yaw)
    mesh.materials.append(sacking)
    mk.box_map(obj, (0.15, 0.15))
    # the tie and the flared tuft beyond it, turned along +y from the neck
    neck_z = 0.8 / 1.8 * height
    tip = Vector(at) + Matrix.Rotation(yaw, 3, 'Z') @ Vector((0, body * 0.9, neck_z))
    tuft = lathe(f'{name}-tuft', [(0, -0.006), (0.015, -0.006), (0.009, 0.006), (0.009, 0.014), (0.012, 0.019), (0.022, 0.04),
                                  (0.031, 0.06), (0.024, 0.062), (0.014, 0.052), (0, 0.046)], sides=8, at=tuple(tip), rotate=(-math.pi / 2, 0, yaw),
                 material=sacking, cap_units=0.15, v_length=0.15, sharp=60)
    return [obj, tuft]


def join_by_material(parts, prefix):
    """Fewer draws (notes B15): apply each part's modifiers, then join the parts of a group that
    share a material into one mesh. Groups and markers stay; only part names change."""
    by_material = {}
    for p in parts:
        mk.apply_modifiers(p)
        by_material.setdefault(p.data.materials[0].name, []).append(p)
    joined = []
    for name, objs in by_material.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1: bpy.ops.object.join()
        objs[0].name = objs[0].data.name = f'{prefix}-{name}'
        joined.append(objs[0])
    return joined


# --------------------------------------------------------------------------------------- barrels

BARREL_H, R_END, R_BELLY = 0.18, 0.066, 0.077


def barrel_radius(z):
    return R_END + (R_BELLY - R_END) * math.sin(math.pi * min(max(z, 0), BARREL_H) / BARREL_H)


def barrel(name, at, lying=False, yaw=0.0):
    """A bulging barrel (lathed, notes B7) with a recessed head inside a chime lip and four hoops."""
    lip, head = 0.058, 0.01
    # a standing barrel's bottom head is never seen: leave it open (saves 80 triangles)
    profile = [(0, head), (lip, head), (lip, 0.0), (R_END, 0.0)] if lying else [(R_END, 0.0)]
    profile += [(barrel_radius(z), z) for z in (0.036, 0.072, 0.108, 0.144)]
    profile += [(R_END, BARREL_H), (lip, BARREL_H), (lip, BARREL_H - head), (0, BARREL_H - head)]
    if lying:
        # lie it along a horizontal line turned by yaw; the belly rests on the ground
        rotate = (math.pi / 2, 0, yaw)
        centre = Vector((at[0], at[1], R_BELLY + 0.004))
        base = centre + Matrix.Rotation(yaw, 3, 'Z') @ Vector((0, BARREL_H / 2, 0))   # the lathe's z=0 end
    else:
        rotate, base = (0, 0, yaw), Vector((at[0], at[1], 0))
    parts = [lathe(f'{name}-body', profile, sides=16, at=tuple(base), rotate=rotate, material=barrel_wood,
                   u_repeat=2.0, v_length=BARREL_H, cap_units=0.15, sharp=35)]
    for k, (z0, z1) in enumerate(((0.008, 0.02), (0.042, 0.054), (0.126, 0.138), (0.16, 0.172))):
        r0, r1 = barrel_radius(z0), barrel_radius(z1)
        hoop = [(r0 - 0.002, z0), (r0 + 0.0035, z0), (r1 + 0.0035, z1), (r1 - 0.002, z1)]
        if not lying: hoop = hoop[1:]          # a standing hoop's underside faces the ground: never seen
        parts.append(lathe(f'{name}-hoop-{k}', hoop, sides=16, at=tuple(base), rotate=rotate, material=iron))
    return parts


barrels = barrel('barrel-a', (0, 0), yaw=0.3) + barrel('barrel-b', (0.17, 0.05), yaw=1.1) \
    + barrel('barrel-c', (0.06, -0.19), lying=True, yaw=0.4)
mk.group('barrels', join_by_material(barrels, 'barrels'))


# ------------------------------------------------------------------------------- crates and sacks

def crate(name, size, at, yaw):
    """A painted-board crate with a raw timber frame: corner posts, top and bottom rims and a
    diagonal brace on three faces. All battens stand 0.01 proud so they catch light and cast lines."""
    f = frame((at[0], at[1], at[2] + size / 2), yaw)
    h = size / 2
    parts = [framed_box(f'{name}-boards', f, (size - 0.02, size - 0.02, size - 0.02), (0, 0, 0), timber, bevel=0.004)]
    post, t = 0.03, 0.016
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(framed_box(f'{name}-post', f, (post, post, size), (sx * (h - post / 2), sy * (h - post / 2), 0), frame_wood))
    inner = size - 2 * post
    for sz in (-1, 1):
        z = sz * (h - 0.016)
        for s in (-1, 1):
            parts.append(framed_box(f'{name}-rim', f, (inner, t, 0.032), (0, s * (h - t / 2), z), frame_wood))
            parts.append(framed_box(f'{name}-rim', f, (t, inner, 0.032), (s * (h - t / 2), 0, z), frame_wood))
    span = size - 2 * post - 0.01
    angle = math.atan2(span, span - 0.064)
    length = math.hypot(span, span - 0.064)
    parts.append(framed_box(f'{name}-brace', f, (0.026, t, length), (0, -(h - t / 2), 0), frame_wood, local_rot=(0, angle, 0)))
    for s in (-1, 1):
        parts.append(framed_box(f'{name}-brace', f, (t, 0.026, length), (s * (h - t / 2), 0, 0), frame_wood, local_rot=(s * angle, 0, 0)))
    return parts


crates = crate('crate-a', 0.22, (0, 0, 0), 0.0) + crate('crate-b', 0.2, (0.24, 0.03, 0), 0.15) \
    + crate('crate-c', 0.18, (0.1, 0.02, 0.22), -0.1)                       # the top one rests on the two below
crates += sack('sack-a', (-0.2, -0.05, 0), math.pi / 2 - 0.15, seed=3) \
    + sack('sack-b', (-0.17, 0.12, 0), math.pi / 2 + 0.5, length=0.23, width=0.14, height=0.095, seed=7)
mk.group('crates', join_by_material(crates, 'crates'))


# ------------------------------------------------------------------------------------- lamp-post

# one turned iron piece from the ground to the lantern: moulded foot, column, collar, ladder-bar
# boss and the spigot that carries the lantern
post_profile = [(0, 0), (0.062, 0), (0.062, 0.022), (0.054, 0.028), (0.05, 0.06), (0.04, 0.074), (0.036, 0.13),
                (0.03, 0.15), (0.03, 0.17), (0.022, 0.19), (0.02, 0.22), (0.018, 0.55), (0.025, 0.56), (0.025, 0.575),
                (0.0175, 0.585), (0.016, 0.995), (0.024, 1.005), (0.024, 1.04), (0.016, 1.05), (0.016, 1.065), (0.034, 1.085), (0, 1.085)]
post = [lathe('lamp-column', post_profile, sides=12, material=iron, sharp=50)]
# ladder bar with ball ends (lamplighters leant their ladders on it)
post.append(soft(mk.box('lamp-crossbar', (0.2, 0.014, 0.014), at=(0, 0, 1.022), material=iron, bevel=0.003)))
for s in (-1, 1):
    post.append(lathe('lamp-ball', [(0, -0.012), (0.009, -0.009), (0.012, 0), (0.009, 0.009), (0, 0.012)], sides=8, at=(s * 0.106, 0, 1.022), material=iron, sharp=80))
# the lantern: a square tray, four tapering glass panes (lamp-glow, centred on lamp-post-light at
# z 1.17), iron corner bars, a top band, a projecting eave, a pyramid roof, a vent and a finial
SQ = math.sqrt(2)
post.append(mk.cylinder('lamp-tray', 0.045 * SQ, 0.016, at=(0, 0, 1.093), material=iron, sides=4, rotate=(0, 0, math.pi / 4)))
post.append(mk.cylinder('lamp-head', 0.038 * SQ, 0.135, at=(0, 0, 1.1685), material=lamp, sides=4, radius_top=0.052 * SQ, rotate=(0, 0, math.pi / 4)))
for sx in (-1, 1):
    for sy in (-1, 1):
        post.append(strut('lamp-bar', (sx * 0.039, sy * 0.039, 1.1), (sx * 0.053, sy * 0.053, 1.237), 0.008, iron))
post.append(mk.cylinder('lamp-band', 0.057 * SQ, 0.014, at=(0, 0, 1.243), material=iron, sides=4, rotate=(0, 0, math.pi / 4)))
post.append(mk.cylinder('lamp-eave', 0.072 * SQ, 0.006, at=(0, 0, 1.253), material=iron, sides=4, rotate=(0, 0, math.pi / 4)))
post.append(mk.cylinder('lamp-roof', 0.07 * SQ, 0.05, at=(0, 0, 1.281), material=iron, sides=4, radius_top=0.014 * SQ, rotate=(0, 0, math.pi / 4)))
post.append(lathe('lamp-finial', [(0, 1.3), (0.016, 1.3), (0.016, 1.312), (0.006, 1.318), (0.009, 1.328), (0.006, 1.338), (0, 1.36)], sides=8, material=iron, sharp=50))
mk.group('lamp-post', join_by_material(post, 'lamp-post'))
mk.marker('lamp-post-light', (0, 0, 1.17))


# ------------------------------------------------------------------------------------------ cart

AXLE = (0.02, 0, 0.12)
PITCH = -0.22            # the bed tips back so the shafts rest on the ground behind
bed = frame(AXLE, 0.0, PITCH)
cart = []
for side in (-1, 1):
    y = side * 0.16
    # wheel: lathed round y (felloe in timber, an iron tyre on it, a turned hub), eight spokes
    wheel_rot = (math.pi / 2, 0, 0)
    cart.append(lathe(f'cart-felloe-{side}', [(0.1, -0.011), (0.116, -0.011), (0.116, 0.011), (0.1, 0.011)], sides=18,
                      at=(AXLE[0], y, AXLE[2]), rotate=wheel_rot, material=wheel_wood, closed=True, u_repeat=3, v_length=0.5, sharp=30))
    cart.append(lathe(f'cart-tyre-{side}', [(0.116, -0.0125), (0.1215, -0.0125), (0.1215, 0.0125), (0.116, 0.0125)], sides=18,
                      at=(AXLE[0], y, AXLE[2]), rotate=wheel_rot, material=iron, sharp=30))
    cart.append(lathe(f'cart-hub-{side}', [(0, -0.036), (0.02, -0.036), (0.028, -0.022), (0.03, 0), (0.028, 0.02), (0.02, 0.032), (0, 0.032)],
                      sides=8, at=(AXLE[0], y, AXLE[2]), rotate=(side * math.pi / 2, 0, 0), material=wheel_wood, sharp=50))
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        d = Vector((math.cos(a), 0, math.sin(a)))
        centre = Vector((AXLE[0], y, AXLE[2])) + d * 0.065
        cart.append(mk.box(f'cart-spoke-{side}', (0.013, 0.016, 0.076), at=tuple(centre), material=wheel_wood,
                           rotate=(0, math.atan2(d.x, d.z), 0)))
cart.append(mk.cylinder('cart-axle', 0.012, 0.36, at=AXLE, material=iron, sides=8, rotate=(math.pi / 2, 0, 0)))
# shafts run under the bed, past it as handles with turned grips, joined by a cross-bar
for side in (-1, 1):
    cart.append(framed_box(f'cart-shaft-{side}', bed, (0.74, 0.022, 0.022), (-0.15, side * 0.105, 0.023), wheel_wood, bevel=0.004))
    grip = bed @ Vector((-0.565, side * 0.105, 0.023))
    cart.append(lathe(f'cart-grip-{side}', [(0, -0.045), (0.009, -0.045), (0.011, -0.03), (0.011, 0.03), (0.008, 0.045), (0, 0.045)],
                      sides=8, at=tuple(grip), rotate=(0, math.pi / 2 + PITCH, 0), material=wheel_wood, sharp=50))
cart.append(framed_box('cart-crossbar', bed, (0.018, 0.232, 0.018), (-0.44, 0, 0.023), wheel_wood, bevel=0.003))
# bed: two bearers across the shafts, five floor boards, a front board, stakes and two rails a side
for x in (-0.17, 0.15):
    cart.append(framed_box('cart-bearer', bed, (0.03, 0.27, 0.016), (x, 0, 0.042), wheel_wood))
for i in range(5):
    cart.append(framed_box('cart-board', bed, (0.44, 0.048, 0.014), (-0.01, -0.106 + i * 0.053, 0.057), wheel_wood, bevel=0.003))
cart.append(framed_box('cart-front', bed, (0.014, 0.29, 0.1), (0.215, 0, 0.114), wheel_wood, bevel=0.004))
for side in (-1, 1):
    for x in (-0.21, -0.01, 0.19):
        cart.append(framed_box('cart-stake', bed, (0.018, 0.016, 0.13), (x, side * 0.139, 0.107), wheel_wood))
    for z in (0.098, 0.15):
        cart.append(framed_box('cart-rail', bed, (0.44, 0.012, 0.024), (-0.01, side * 0.124, z), wheel_wood, bevel=0.003))
mk.group('cart', join_by_material(cart, 'cart'))

mk.finish(OUT, bake=True, bake_size=1024, bake_samples=24)
