# What this does: builds a reviewer's desk in Blender for chapter 2, page 8 ("An independent review of
# the Reserve Bank says..."), where the printed report drops onto it and a rubber stamp comes down
# twice. The viewer called the old bare table "plain and boring"; this desk fills the tall frame
# around the report: a polished wooden desk top with a green leather blotter (the report lands in its
# middle), a brass banker's lamp with a green glass shade, a stack of folders tied with tape, loose
# typed papers (unreadable grey lines, no words), an open ink pad for the stamp, a fountain pen,
# reading glasses, a cup of tea on its saucer, and bookshelves behind (soft with focus).
#
# Detail pass (with the Blender MCP, notes "22 Blender MCP notes - detailed models.md", C3): planked
# mahogany with real grain, seams, a polish (roughness) map and a moulded front edge; leather corner
# pockets and a tooled border groove on the blotter; glasses with dark glass lenses, wire rims, a
# bridge, hinges and temples; a turned cup and saucer with a foot ring, a well, a D handle and a tea
# surface; a lamp with a stepped turned base, a collar, a curved arm, a shade with thickness and a
# pale lining, rolled brass end caps and a bead pull chain; folders with page edges, bowed covers and
# a thin red tape that follows the stack and ends in a bow; a turned pen with nib, band and clip; an
# ink tin with rolled rims and a hinged lid; papers with a slight curl. Soft edges use bevels with
# hardened normals; parts sharing a material are joined (fewer draws). AO is baked with a short reach.
#
# The model's origin is the middle of the blotter, on its surface (the report lies there). Blender -y
# is towards the camera (three.js +z). Markers: desk_lamp (the bulb), ink_pad. Keep the blotter's
# middle 1.5 x 1.9 clear and flat (the printed report, about 1.3 x 1.65, lies there).
#
# Run: /home/user/work/blender-env/bin/python build_desk.py OUT.glb [--no-bake]
# (OUT must end in .glb: Blender adds .glb to any other name)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402
import textures as tx  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'desk.glb'
rng = np.random.default_rng(5)
mk.reset()

# AO with a short reach for desk items (notes B12b: 0.3), without touching model_kit (shared)
_bake_shading = mk.bake_shading
mk.bake_shading = lambda objects, **kw: _bake_shading(objects, reach=0.3, **kw)


# ------------------------------------------------------------------------------------- helpers

def smooth_all(obj):
    obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
    return obj


def soft(obj, width, segments=2, angle=30, profile=0.5):
    """Soft edges that catch the light (notes B1 + B2): bevel with hardened normals, then weighted
    normals, smooth shading, so flat faces stay flat and only the bevel shades round."""
    b = obj.modifiers.new('soft', 'BEVEL')
    b.width = width; b.segments = segments; b.profile = profile
    b.limit_method = 'ANGLE'; b.angle_limit = math.radians(angle)
    b.use_clamp_overlap = True; b.miter_outer = 'MITER_ARC'
    b.harden_normals = True; b.face_strength_mode = 'FSTR_AFFECTED'
    w = obj.modifiers.new('weighted', 'WEIGHTED_NORMAL')
    w.mode = 'FACE_AREA'; w.keep_sharp = True; w.use_face_influence = True
    return smooth_all(obj)


def _mesh_object(name, bm, material, at=(0, 0, 0), rotate=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at; obj.rotation_euler = rotate
    if material is not None: obj.data.materials.append(material)
    return obj


def lathe(name, profile, at=(0, 0, 0), material=None, steps=32, rotate=(0, 0, 0), sharp=40, keep=None):
    """A turned part (notes B7): a half profile [(radius, height), ...] spun round local z."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    if keep is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co)], context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = _mesh_object(name, bm, material, at, rotate)
    smooth_all(obj); obj.data.set_sharp_from_angle(angle=math.radians(sharp))
    mk.box_map(obj, (1, 1))
    return obj


def tube(name, points, radius, material, at=(0, 0, 0), rotate=(0, 0, 0), res=2, smooth_path=True, cyclic=False, squash=None):
    """A rod or wire along points (notes B6), turned into a mesh. squash=(sx, sy, sz) flattens it
    about its own middle (a ribbon loop, a flat handle)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = res; cu.resolution_u = 8; cu.use_fill_caps = not cyclic
    sp = cu.splines.new('NURBS' if smooth_path else 'POLY')
    sp.points.add(len(points) - 1)
    for i, p in enumerate(points): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = cyclic
    if smooth_path: sp.order_u = min(4, len(points)); sp.use_endpoint_u = not cyclic
    tmp = bpy.data.objects.new(name + '-path', cu)
    bpy.context.scene.collection.objects.link(tmp)
    mesh = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp, do_unlink=True); bpy.data.curves.remove(cu)
    if squash is not None:
        middle = sum((v.co for v in mesh.vertices), Vector()) / max(1, len(mesh.vertices))
        for v in mesh.vertices: v.co = middle + Vector([(v.co[i] - middle[i]) * squash[i] for i in range(3)])
    mesh.name = name
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = at; obj.rotation_euler = rotate
    if material is not None: obj.data.materials.append(material)
    smooth_all(obj); mk.box_map(obj, (1, 1))
    return obj


def sheet(name, size, at, material, rotate=(0, 0, 0), segments=(8, 10), lift=None, thickness=0.002):
    """A sheet (paper, folder cover) as a subdivided plane whose picture covers it once, bent by
    lift(u, v) -> dz (u, v from 0 to 1), with real thickness (notes B4)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    nx, ny = segments
    grid = [[bm.verts.new(((i / nx - 0.5) * size[0], (j / ny - 0.5) * size[1], lift(i / nx, j / ny) if lift else 0.0))
             for i in range(nx + 1)] for j in range(ny + 1)]
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
            for loop in f.loops: loop[uv].uv = (loop.vert.co.x / size[0] + 0.5, loop.vert.co.y / size[1] + 0.5)
    obj = _mesh_object(name, bm, material, at, rotate)
    s = obj.modifiers.new('thick', 'SOLIDIFY'); s.thickness = thickness; s.offset = 1; s.use_even_offset = True
    return smooth_all(obj)


def strip(name, path, width, material, at=(0, 0, 0), rotate=(0, 0, 0), thickness=0.003, axis='y'):
    """A thin band (tape) whose middle line runs through path [(a, z), ...]; for axis 'y' the path
    is in local x-z and the band is `width` wide along y (axis 'x': path in y-z, wide along x)."""
    bm = bmesh.new()
    rows = []
    for a, z in path:
        if axis == 'y': rows.append((bm.verts.new((a, -width / 2, z)), bm.verts.new((a, width / 2, z))))
        else: rows.append((bm.verts.new((-width / 2, a, z)), bm.verts.new((width / 2, a, z))))
    for k in range(len(rows) - 1):
        bm.faces.new([rows[k][0], rows[k + 1][0], rows[k + 1][1], rows[k][1]])
    bm.normal_update()
    if sum(f.normal.z for f in bm.faces) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
    obj = _mesh_object(name, bm, material, at, rotate)
    s = obj.modifiers.new('thick', 'SOLIDIFY'); s.thickness = thickness; s.offset = 1
    smooth_all(obj); mk.box_map(obj, (1, 1))
    return obj


def add_maps(m, normal=None, rough=None, normal_strength=1.0):
    """Hang a normal map and a roughness picture (glTF: roughness in G, metal in B) on a material."""
    nodes, links = m.node_tree.nodes, m.node_tree.links
    shader = nodes['Principled BSDF']
    if normal is not None:
        t = nodes.new('ShaderNodeTexImage'); t.image = mk._image(f'{m.name}-normal', normal, False)
        n = nodes.new('ShaderNodeNormalMap'); n.inputs['Strength'].default_value = normal_strength
        links.new(t.outputs['Color'], n.inputs['Color']); links.new(n.outputs['Normal'], shader.inputs['Normal'])
    if rough is not None:
        t = nodes.new('ShaderNodeTexImage'); t.image = mk._image(f'{m.name}-rough', rough, False)
        sep = nodes.new('ShaderNodeSeparateColor')
        links.new(t.outputs['Color'], sep.inputs['Color'])
        links.new(sep.outputs['Green'], shader.inputs['Roughness']); links.new(sep.outputs['Blue'], shader.inputs['Metallic'])


def join_by_material(skip=()):
    """Join parts that share one material and never move (notes B15: fewer draws)."""
    groups = {}
    for o in list(bpy.context.scene.objects):
        if o.type != 'MESH' or len(o.data.materials) != 1 or any(o.name.startswith(s) for s in skip): continue
        groups.setdefault(o.data.materials[0].name, []).append(o)
    for objects in groups.values():
        if len(objects) < 2: continue
        for o in objects: mk.apply_modifiers(o)
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects: o.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()


# ------------------------------------------------------------------------------------- pictures

def desk_wood_pictures(size=1024, seed=31, colour=(92, 50, 28)):
    """Planked mahogany. One tile = 2.5 (along the grain, u) x 1.2 (across, v) units: two planks
    0.6 wide with a dark seam between, grain lines about 2.7 cm apart with a flame figure."""
    r = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    plank = (ys * 2).astype(int)                        # 0 or 1
    across = ys * 2 - plank                             # 0..1 inside a plank
    warp = tx.blur(tx.fractal_noise(size, size, r, roughness=4.0), 6)   # smooth, so lines stay lines
    figure = np.sin(2 * math.pi * (xs * 2 + plank * 0.37)) * (0.6 + 0.4 * np.sin(2 * math.pi * (xs + plank * 0.21)))
    phase = across * 22 + warp * 2.5 + figure * 1.6 * (1 - 1.6 * np.abs(across - 0.5)) + plank * 7.3
    rings = (np.sin(phase * 2 * math.pi) * 0.5 + 0.5) ** 3      # thin dark late-wood lines
    fibre = tx.fractal_noise(size, size, r, roughness=1.1)
    fibre = sum(np.roll(fibre, k * 8, axis=1) for k in range(40)) / 40   # stretched along the grain
    fibre = (fibre - fibre.min()) / max(1e-9, np.ptp(fibre))
    edge = np.minimum(across, 1 - across) * size / 2  # pixels to the nearest seam
    seam = np.clip(edge / 4.0, 0, 1)
    tone = np.where(plank == 0, 1.0, 0.9) * (0.92 + 0.12 * tx.fractal_noise(size, size, r, roughness=3.0))
    shade = (0.72 + 0.22 * (1 - rings) + 0.14 * fibre) * tone * (0.35 + 0.65 * seam)
    colour_picture = tx.to_picture(tx.tint(colour, 1)[None, None, :] * shade[..., None] * np.array([1.0, 0.97, 0.95])[None, None, :])
    height = (1 - rings) * 0.3 + fibre * 0.1 + (seam - 1) * 0.9
    normal_picture = tx.normal_map(tx.blur(height, 2), strength=2.5)
    wear = tx.fractal_noise(size, size, r, roughness=2.8)
    roughness = np.clip(0.22 + 0.1 * rings + 0.08 * fibre + 0.12 * wear + 0.3 * (1 - seam), 0, 1)
    rough_picture = Image.fromarray(np.stack([np.full_like(roughness, 255), roughness * 255, np.zeros_like(roughness)], -1).astype(np.uint8))
    return colour_picture, normal_picture, rough_picture


def leather_pictures(w=1024, h=820, seed=12):
    """Green leather for the blotter, with a tooled gold border pressed in as a groove."""
    r = np.random.default_rng(seed)
    crinkle = tx.fractal_noise(h, w, r, roughness=1.0)
    blotch = tx.fractal_noise(h, w, r, roughness=3.0)
    base = tx.tint((50, 84, 68), 1)[None, None, :] * (0.8 + 0.18 * crinkle + 0.14 * blotch)[..., None]
    picture = tx.to_picture(base)
    ink = ImageDraw.Draw(picture)
    ink.rectangle([22, 22, w - 23, h - 23], outline=(176, 142, 74), width=5)
    ink.rectangle([36, 36, w - 37, h - 37], outline=(140, 112, 60), width=2)
    groove = Image.new('L', (w, h), 0)
    g = ImageDraw.Draw(groove)
    g.rectangle([22, 22, w - 23, h - 23], outline=255, width=5)
    g.rectangle([36, 36, w - 37, h - 37], outline=200, width=2)
    height = crinkle * 0.35 - np.asarray(groove, dtype=float) / 255 * 1.2
    return picture, tx.normal_map(tx.blur(height), strength=2.0)


def paper_edge_picture(size=256, seed=13):
    """Stacked page edges: thin uneven horizontal lines (one tile = 0.3 x 0.03 units)."""
    r = np.random.default_rng(seed)
    ys = np.arange(size)[:, None].repeat(size, 1).astype(float)
    lines = np.sin(ys / size * 2 * math.pi * 12 + tx.fractal_noise(size, size, r, roughness=2.0) * 3) * 0.5 + 0.5
    return tx.to_picture(tx.tint((228, 220, 200), 1)[None, None, :] * (0.84 + 0.16 * lines)[..., None])


def typed_page(seed, size=(512, 680)):
    """A typed page: rows of grey bars of uneven length (unreadable, no letters)."""
    r = np.random.default_rng(seed)
    page = Image.new('RGB', size, (232, 226, 210))
    draw = ImageDraw.Draw(page)
    y = 70
    while y < size[1] - 60:
        if r.random() < 0.12: y += 22; continue          # a paragraph gap
        x = 56
        end = size[0] - 56 - (r.random() * 160 if r.random() < 0.2 else 0)
        while x < end:
            word = 14 + r.random() * 46
            draw.rectangle([x, y, min(x + word, end), y + 7], fill=(92, 90, 86))
            x += word + 9
        y += 19
    return page


# ------------------------------------------------------------------------------------- materials
# the plain polished wood of textures.py (the planked figure made here looked like a contour map on a phone)
wood = mk.material('wood', name='desk-wood', roughness=0.35)
leather_picture, leather_normal = leather_pictures()
leather = mk.material(name='blotter-leather', roughness=0.55, picture=leather_picture)
add_maps(leather, leather_normal, None, normal_strength=1.0)
brass = mk.material(None, name='brass', colour=(0.75, 0.55, 0.25), roughness=0.28, metallic=0.9)
shade_glass = mk.material(None, name='shade-glass', colour=(0.04, 0.3, 0.16), roughness=0.4, metallic=0.1)   # satin: glossy glass showed white blobs
lining = mk.material(None, name='shade-lining', colour=(0.93, 0.9, 0.8), roughness=0.6)
bulb = mk.material(None, name='lamp-glow', colour=(1.0, 0.85, 0.6), glow=(1.0, 0.78, 0.5), glow_strength=4.0, roughness=0.3)
manila = mk.material(None, name='manila', colour=(0.72, 0.6, 0.38), roughness=0.85)
paper_edge = mk.material(name='paper-edge', roughness=0.9, picture=paper_edge_picture())
loose_sheet = mk.material(None, name='paper-sheet', colour=(0.9, 0.87, 0.8), roughness=0.9)
tape = mk.material(None, name='red-tape', colour=(0.55, 0.12, 0.1), roughness=0.7)
black = mk.material(None, name='black-lacquer', colour=(0.02, 0.02, 0.025), roughness=0.15, metallic=0.2)
gold = mk.material(None, name='gold', colour=(0.85, 0.65, 0.3), roughness=0.22, metallic=1.0)
china = mk.material(None, name='china', colour=(0.92, 0.91, 0.87), roughness=0.15)
tea = mk.material(None, name='tea', colour=(0.22, 0.1, 0.04), roughness=0.05)
tin = mk.material(None, name='tin', colour=(0.35, 0.36, 0.38), roughness=0.32, metallic=0.8)
ink_red = mk.material(None, name='ink-pad', colour=(0.45, 0.08, 0.07), roughness=0.6)
# clear reading-glass lenses: pale and mostly see-through (dark ones read as sunglasses, solid pale ones as white discs)
lens = mk.material(None, name='lens', colour=(0.82, 0.86, 0.88), roughness=0.05, metallic=0.0)
lens.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.2
lens.surface_render_method = 'BLENDED'
blotter_ends = mk.material(None, name='blotter-ends', colour=(0.06, 0.11, 0.085), roughness=0.6)
page_a = mk.material(name='typed-page-a', roughness=0.9, picture=typed_page(1))
page_b = mk.material(name='typed-page-b', roughness=0.9, picture=typed_page(2))

rng.random((820, 1024))                                # keeps the book colours as they were
# bookshelf spines: rows of muted cloth bindings with a few gold bands (no titles)
spines = Image.new('RGB', (1024, 256), (20, 16, 14))
draw = ImageDraw.Draw(spines)
x = 0
cloth = [(92, 34, 30), (34, 58, 44), (52, 44, 34), (30, 40, 62), (110, 82, 50), (70, 30, 40), (40, 40, 40)]
while x < 1024:
    width = int(18 + rng.random() * 26)
    colour = cloth[int(rng.random() * len(cloth))]
    shade = 0.75 + rng.random() * 0.35
    top = int(rng.random() * 40)
    draw.rectangle([x, top, x + width - 2, 255], fill=tuple(int(c * shade) for c in colour))
    for band in (top + 18, 220):
        if rng.random() < 0.6: draw.rectangle([x + 2, band, x + width - 4, band + 4], fill=(150, 120, 60))
    x += width
books = mk.material(name='book-spines', roughness=0.8, picture=spines)
shelf_wood = mk.material('wood', name='shelf-wood', roughness=0.5)

# --------------------------------------------------------------------------------------- the desk
TOP_Y = 0.35                                    # the desk top's middle is a little further back than the blotter
soft(mk.box('desk-top', (5.0, 4.2, 0.1), at=(0, TOP_Y, -0.058), material=wood, map_units=(1.0, 1.0)), 0.02, 3, profile=0.6)
soft(mk.box('desk-edge', (5.06, 0.08, 0.06), at=(0, TOP_Y - 2.1, -0.1), material=wood, map_units=(2.5, 1.2)), 0.025, 4)
soft(mk.box('desk-front', (4.9, 0.06, 0.8), at=(0, TOP_Y - 2.05, -0.5), material=wood, map_units=(2.5, 1.2)), 0.01, 2)
mk.plane('blotter', (2.5, 2.0), at=(0, 0.05, -0.004), material=leather)
soft(mk.box('blotter-base', (2.52, 2.02, 0.006), at=(0, 0.05, -0.008), material=mk.material(None, name='blotter-edge', colour=(0.12, 0.1, 0.08), roughness=0.6)), 0.002, 1)
# leather corner pockets (triangles over the blotter's corners, clear of the report's area)
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy, leg = sx * 1.262, 0.05 + sy * 1.012, 0.34
        soft(mk.prism(f'blotter-corner-{sx}{sy}', [(cx, cy), (cx - sx * leg, cy), (cx, cy - sy * leg)], 0.01, at=(0, 0, 0.001),
                      material=blotter_ends, axis='z'), 0.003, 2)

# the banker's lamp, upper left
LX, LY = -0.95, 1.5
SX, SY, SZ = LX + 0.05, LY - 0.14, 0.86              # the shade's axis middle
lathe('lamp-base', [(0, 0), (0.215, 0), (0.222, 0.006), (0.223, 0.022), (0.213, 0.034), (0.19, 0.04), (0.17, 0.042),
                    (0.165, 0.052), (0.15, 0.058), (0.11, 0.064), (0.096, 0.076), (0.07, 0.09), (0.05, 0.1),
                    (0.045, 0.118), (0.03, 0.125), (0, 0.125)], at=(LX, LY, 0), material=brass, steps=40)
lathe('lamp-stem', [(0, 0.12), (0.018, 0.12), (0.018, 0.38), (0.026, 0.39), (0.029, 0.41), (0.026, 0.43),
                    (0.018, 0.44), (0.018, 0.71), (0.023, 0.72), (0.02, 0.735), (0, 0.735)], at=(LX, LY, 0), material=brass, steps=16)
tube('lamp-arm', [(LX, LY, 0.72), (LX, LY, 0.8), (LX + 0.02, LY - 0.02, 0.9), (LX + 0.05, LY - 0.06, 0.96)], 0.015, brass)
# the shade: a half cylinder with thickness, green glass outside and a pale lining inside
bm = bmesh.new()
STEPS, R, HALF = 28, 0.17, 0.355
rows = [[bm.verts.new((x0, R * math.cos(math.pi * k / STEPS), R * math.sin(math.pi * k / STEPS))) for k in range(STEPS + 1)] for x0 in (-HALF, HALF)]
for k in range(STEPS): bm.faces.new([rows[0][k], rows[1][k], rows[1][k + 1], rows[0][k + 1]])
bm.normal_update()
bm.faces.ensure_lookup_table()
if bm.faces[0].normal.dot(bm.faces[0].calc_center_median()) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
shade_obj = _mesh_object('lamp-shade', bm, shade_glass, at=(SX, SY, SZ))
shade_obj.data.materials.append(lining)
s = shade_obj.modifiers.new('thick', 'SOLIDIFY'); s.thickness = 0.006; s.offset = -1; s.material_offset = 1; s.use_even_offset = True
smooth_all(shade_obj); mk.box_map(shade_obj, (1, 1))
for side in (-1, 1):                                  # brass end caps with a rolled edge (half discs)
    lathe(f'shade-cap-{side}', [(0, 0), (0.168, 0), (0.176, 0.002), (0.181, 0.007), (0.176, 0.012), (0.168, 0.014), (0, 0.014)],
          at=(SX + side * (HALF + 0.007) - 0.007, SY, SZ), material=brass, steps=32, rotate=(0, math.pi / 2, 0),
          keep=lambda co: co.x <= 1e-4)
for side in (-1, 1):                                  # rolled brass lips along the shade's lower edges
    tube(f'shade-lip-{side}', [(SX - HALF, SY + side * R, SZ), (SX + HALF, SY + side * R, SZ)], 0.006, brass, smooth_path=False)
mk.cylinder('lamp-bulb', 0.04, 0.5, at=(SX, SY, SZ - 0.04), material=bulb, sides=16, rotate=(0, math.pi / 2, 0))
# the pull chain: small brass beads and a pull at the end, hanging below the shade's front right
bm = bmesh.new()
chain_x, chain_y = SX + 0.26, SY - 0.12
for k in range(13):
    big = k == 12
    ret = bmesh.ops.create_uvsphere(bm, u_segments=10 if big else 8, v_segments=6 if big else 4, radius=0.013 if big else 0.0065)
    bmesh.ops.translate(bm, verts=ret['verts'], vec=(chain_x, chain_y, 0.875 - k * 0.017 - (0.008 if big else 0)))
lamp_chain = _mesh_object('pull-chain', bm, brass); smooth_all(lamp_chain); mk.box_map(lamp_chain, (1, 1))
mk.marker('desk_lamp', (LX + 0.05, LY - 0.14, 0.76))

# the stack of folders, upper right: page edges, bowed covers, tied with a thin red tape and a bow
FX, FY = 0.95, 1.55
COVER = (0.9, 1.12)
bow = lambda u, v: 0.006 * (1 - (2 * u - 1) ** 2) * (1 - (2 * v - 1) ** 4)     # the cover bows over the papers
lift = lambda u, v: bow(u, v) + 0.01 * max(0.0, (u - 0.75) / 0.25) ** 2 * max(0.0, (0.25 - v) / 0.25)  # a corner lifts
for k in range(4):
    turn = math.radians(rng.uniform(-4, 4)) if k < 3 else 0.0
    ox, oy = (rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)) if k < 3 else (0.0, 0.0)
    z = k * 0.042
    at = lambda dz, dx=0.0, dy=0.0: (FX + ox + dx, FY + oy + dy, z + dz)
    sheet(f'folder-back-{k}', COVER, at(0), manila, rotate=(0, 0, turn), segments=(2, 2), thickness=0.003)
    soft(mk.box(f'folder-papers-{k}', (0.84, 1.06, 0.022), at=at(0.014), material=paper_edge, rotate=(0, 0, turn), map_units=(0.3, 0.03)), 0.003, 1)
    for n in range(2):                                # loose sheets peeking out of the folder
        sheet(f'folder-sheet-{k}-{n}', (0.82, 1.04), at(0.025 + n * 0.002, rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04)), loose_sheet,
              rotate=(0, 0, turn + math.radians(rng.uniform(-2.5, 2.5))), segments=(2, 2), thickness=0.0015)
    sheet(f'folder-cover-{k}', COVER, at(0.03), manila, rotate=(0, 0, turn), segments=(8, 8), lift=bow if k < 3 else lift, thickness=0.003)
TOP = 3 * 0.042 + 0.033                                # the top cover's surface (before its bow)
HX, HY = 0.5, 0.6                                      # the tape stands a little off the stack's edges
def tape_path(half, along_bow):
    path = [(-half, 0.0005), (-half, TOP - 0.03), (-half + 0.008, TOP - 0.004)]
    for i in range(1, 12):
        a = -half + 0.03 + (2 * half - 0.06) * i / 12
        path.append((a, TOP + 0.0015 + along_bow(a)))
    return path + [(half - 0.008, TOP - 0.004), (half, TOP - 0.03), (half, 0.0005)]
TAPE_Y, TAPE_X = 0.12, -0.15                           # where the bands cross (in the stack's frame)
uy, ux = (TAPE_Y / COVER[1]) + 0.5, (TAPE_X / COVER[0]) + 0.5
strip('tape-across', tape_path(HX, lambda a: bow(min(1, max(0, a / COVER[0] + 0.5)), uy)), 0.045, tape, at=(FX, FY + TAPE_Y, 0))
strip('tape-along', tape_path(HY, lambda a: bow(ux, min(1, max(0, a / COVER[1] + 0.5))) + 0.0032), 0.045, tape, at=(FX + TAPE_X, FY, 0), axis='x')
KX, KY, KZ = FX + TAPE_X, FY + TAPE_Y, TOP + bow(ux, uy) + 0.008
for side in (-1, 1):                                   # the bow: two flat loops and two tails
    ang = math.radians(25 if side > 0 else 200)
    d = Vector((math.cos(ang), math.sin(ang), 0))
    q = Vector((-d.y, d.x, 0))
    loop = [Vector((KX, KY, KZ)) + d * (0.075 * (1 - math.cos(t)) / 2) + q * (0.032 * math.sin(t)) + Vector((0, 0, 0.006 * math.sin(t / 2)))
            for t in np.linspace(0, 2 * math.pi, 10)[:-1]]
    tube(f'tape-loop-{side}', [tuple(p) for p in loop], 0.007, tape, cyclic=True, squash=(1, 1, 0.45))
    tail_ang = math.radians(-70 if side > 0 else -115)
    e = Vector((math.cos(tail_ang), math.sin(tail_ang), 0))
    tail = [(Vector((KX, KY, KZ - 0.004)) + e * t) for t in (0.0, 0.05, 0.1, 0.14)]
    strip(f'tape-tail-{side}', [(i * 0.047, p.z - 0.002 * i) for i, p in enumerate(tail)], 0.032, tape,
          at=(KX, KY, 0), rotate=(0, 0, tail_ang), thickness=0.0025)
soft(mk.box('tape-knot', (0.04, 0.035, 0.014), at=(KX, KY, KZ), material=tape), 0.005, 2)

# loose typed papers, upper middle (one tucked under the report's top edge would clip: keep clear)
curl_a = lambda u, v: 0.012 * max(0.0, (0.3 - u) / 0.3) ** 2 * max(0.0, (0.45 - v) / 0.45) + 0.002 * (1 - (2 * v - 1) ** 2)  # free corner
curl_b = lambda u, v: 0.016 * max(0.0, (0.3 - u) / 0.3) ** 2 * max(0.0, (0.4 - v) / 0.4) + 0.003 * (1 - (2 * u - 1) ** 2)  # lies over a
sheet('paper-a', (0.62, 0.82), (-0.25, 1.55, 0.002), page_a, rotate=(0, 0, math.radians(8)), segments=(8, 10), lift=curl_a)
sheet('paper-b', (0.62, 0.82), (0.2, 1.62, 0.009), page_b, rotate=(0, 0, math.radians(-5)), segments=(8, 10), lift=curl_b)

# the ink pad, right of the report: a tin with rolled rims, its lid open flat behind on a hinge
IX, IY = 0.98, -0.25
TW, TD = 0.36, 0.26
soft(mk.box('ink-tin', (TW, TD, 0.034), at=(IX, IY, 0.017), material=tin), 0.008, 2)
def rim(name, cx, cy, z):
    c, hw, hd = 0.02, TW / 2 - 0.004, TD / 2 - 0.004
    pts = []
    for (px, py, a0) in ((hw - c, hd - c, 0), (-hw + c, hd - c, 90), (-hw + c, -hd + c, 180), (hw - c, -hd + c, 270)):
        for t in range(4): pts.append((cx + px + c * math.cos(math.radians(a0 + t * 30)), cy + py + c * math.sin(math.radians(a0 + t * 30)), z))
    return tube(name, pts, 0.005, tin, smooth_path=False, cyclic=True)
rim('ink-tin-rim', IX, IY, 0.035)
soft(mk.box('ink-felt', (0.31, 0.21, 0.008), at=(IX, IY, 0.038), material=ink_red), 0.004, 2)
for k in (-1, 0, 1):                                   # hinge knuckles on the back edge
    mk.cylinder(f'ink-hinge-{k}', 0.006, 0.045, at=(IX + k * 0.1, IY + TD / 2 + 0.004, 0.03), material=tin, sides=10, rotate=(0, math.pi / 2, 0))
LIDY = IY + TD + 0.008
soft(mk.box('ink-lid', (TW, TD, 0.014), at=(IX, LIDY, 0.007), material=tin), 0.006, 2)
rim('ink-lid-rim', IX, LIDY, 0.015)
soft(mk.box('ink-lid-panel', (0.3, 0.2, 0.004), at=(IX, LIDY, 0.015), material=mk.material(None, name='tin-inside', colour=(0.55, 0.52, 0.46), roughness=0.4, metallic=0.6)), 0.003, 1)
mk.marker('ink_pad', (IX, IY, 0.05))

# the fountain pen, left of the report (turned: nib, section, barrel, gold band, cap with a clip)
pen_turn = math.radians(-58)
along = (math.sin(pen_turn), -math.cos(pen_turn))     # the pen's length direction on the desk
PEN_AT, PEN_ROT = (-0.95, -0.35, 0.0245), (math.pi / 2, 0, pen_turn)   # local +z runs along the pen, +y up
lathe('pen-nib', [(0, -0.17), (0.003, -0.166), (0.009, -0.14), (0.012, -0.124), (0, -0.124)], at=PEN_AT, material=gold, steps=12, rotate=PEN_ROT)
lathe('pen-barrel', [(0, -0.126), (0.012, -0.126), (0.015, -0.112), (0.016, -0.088), (0.019, -0.078), (0.021, -0.064),
                     (0.021, 0.12), (0, 0.12)], at=PEN_AT, material=black, steps=16, rotate=PEN_ROT)
lathe('pen-cap', [(0, 0.13), (0.0235, 0.13), (0.0245, 0.142), (0.024, 0.3), (0.021, 0.318), (0.013, 0.328), (0, 0.331)],
      at=PEN_AT, material=black, steps=16, rotate=PEN_ROT)
lathe('pen-band', [(0, 0.127), (0.0245, 0.127), (0.0255, 0.134), (0.0245, 0.141), (0, 0.141)], at=PEN_AT, material=gold, steps=16, rotate=PEN_ROT)
tube('pen-clip', [(0, 0.0255, 0.3), (0, 0.0285, 0.26), (0, 0.0285, 0.2), (0, 0.027, 0.175)], 0.0032, gold, at=PEN_AT, rotate=PEN_ROT, squash=(1.8, 0.7, 1))
lathe('pen-clip-ball', [(0, -0.005), (0.0035, -0.004), (0.005, 0), (0.0035, 0.004), (0, 0.005)], at=PEN_AT, material=gold, steps=8,
      rotate=PEN_ROT).location = Vector(PEN_AT) + Vector((along[0], along[1], 0)) * 0.175 + Vector((0, 0, 0.027))

# reading glasses, lower left: dark glass lenses, wire rims, a bridge, hinges, temples towards the camera
GX, GY, GTURN = -0.75, -1.15, math.radians(10)
def g(x, y, z):
    c, s_ = math.cos(GTURN), math.sin(GTURN)
    return (GX + x * c - y * s_, GY + x * s_ + y * c, z)
for side in (-1, 1):
    lx = side * 0.13
    lathe(f'lens-{side}', [(0, 0), (0.104, 0), (0.105, 0.003), (0.07, 0.0068), (0, 0.0085)], at=g(lx, 0, 0.002), material=lens, steps=32)
    tube(f'rim-{side}', [g(lx + 0.109 * math.cos(t), 0.109 * math.sin(t), 0.006) for t in np.linspace(0, 2 * math.pi, 33)[:-1]],
         0.0045, black, smooth_path=False, cyclic=True, res=1)
    soft(mk.box(f'hinge-{side}', (0.026, 0.02, 0.012), at=g(side * 0.245, -0.012, 0.008), material=black, rotate=(0, 0, GTURN)), 0.004, 1)
    tube(f'temple-{side}', [g(side * 0.25, -0.02, 0.009), g(side * 0.255, -0.12, 0.009), g(side * 0.262, -0.3, 0.006),
                            g(side * 0.258, -0.35, 0.004), g(side * 0.24, -0.385, 0.003)], 0.0042, black, res=1)
tube('bridge', [g(-0.024, 0.02, 0.008), g(-0.014, 0.03, 0.022), g(0.014, 0.03, 0.022), g(0.024, 0.02, 0.008)], 0.0045, black, res=1)
for side in (-1, 1):                                   # nose pads
    soft(mk.box(f'nose-pad-{side}', (0.012, 0.022, 0.006), at=g(side * 0.03, -0.02, 0.006), material=lens, rotate=(0, 0, GTURN)), 0.002, 1)

# a cup of tea on its saucer, lower right (turned, with a foot ring, a well, a D handle and the tea)
CX, CY = 0.85, -1.2
lathe('saucer', [(0, 0.004), (0.085, 0.004), (0.088, 0), (0.1, 0), (0.104, 0.005), (0.15, 0.011), (0.2, 0.018), (0.222, 0.025),
                 (0.229, 0.03), (0.224, 0.033), (0.2, 0.026), (0.15, 0.019), (0.112, 0.013), (0.098, 0.009), (0, 0.009)],
      at=(CX, CY, 0), material=china, steps=40, sharp=60)
CUPZ = 0.009
lathe('cup', [(0, 0.012), (0.066, 0.012), (0.07, 0), (0.08, 0), (0.084, 0.01), (0.105, 0.035), (0.124, 0.07), (0.137, 0.11),
              (0.144, 0.138), (0.146, 0.145), (0.142, 0.148), (0.137, 0.142), (0.13, 0.11), (0.117, 0.07), (0.097, 0.038),
              (0.07, 0.024), (0, 0.022)], at=(CX, CY, CUPZ), material=china, steps=40, sharp=60)
lathe('tea', [(0, -0.004), (0.13, -0.004), (0.131, 0.003), (0.124, 0.0012), (0.11, 0), (0, 0)], at=(CX, CY, CUPZ + 0.111), material=tea, steps=40, sharp=60)
tube('cup-handle', [(CX + 0.13, CY, CUPZ + 0.122), (CX + 0.185, CY, CUPZ + 0.125), (CX + 0.218, CY, CUPZ + 0.097),
                    (CX + 0.207, CY, CUPZ + 0.06), (CX + 0.165, CY, CUPZ + 0.045), (CX + 0.115, CY, CUPZ + 0.05)], 0.011, china, squash=(1, 1.35, 1))

# behind the desk: a wall and bookshelves (soft with focus at the top of the frame)
mk.box('wall', (8.0, 0.1, 4.0), at=(0, 3.4, 0.6), material=mk.material(None, name='wall-paint', colour=(0.16, 0.2, 0.19), roughness=0.9))
for row in range(3):
    z = -0.15 + row * 0.62
    soft(mk.box(f'shelf-{row}', (6.0, 0.5, 0.05), at=(0, 3.1, z), material=shelf_wood), 0.006, 2)
    mk.plane(f'books-{row}', (6.0, 0.52), at=(0, 2.9, z + 0.3), material=books, rotate=(math.pi / 2, 0, 0))

join_by_material(skip=('wall', 'books', 'shelf'))
mk.finish(OUT, bake='--no-bake' not in arguments, bake_skip=('wall', 'books', 'shelf'))
