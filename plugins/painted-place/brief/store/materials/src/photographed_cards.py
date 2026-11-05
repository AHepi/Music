"""
What this file does: draws the cards of the photographed materials (decision 80) that card.py cannot draw, under the
store's card light (card.py's stage: one amber key, a blue fill, a rim), 360 x 220 like every material card:
  - an atlas material (BRICK • / ASHLAR •): a small panel of bricks or blocks, each mapped to one unit of its atlas
    through the UV map pp_atlas (some turned half round), each with its own pp_piece, with mortar behind
    (SURFACE • rough_plasterbrick_05). card.py's sphere and cube have no pp_atlas and would show one blurred corner;
  - a plain surface laid in pieces (setts, flags): pieces each with their own pp_piece, so each shows its own part.
    python3 photographed_cards.py                      every card below (CARDS), into store/cards/materials/
    python3 photographed_cards.py -- atlas "BRICK • brick_wall_02" OUT.png
    python3 photographed_cards.py -- pieces "SURFACE • dark_rock_02" OUT.png setts|flags
Draw one card per run (each run starts a fresh scene).
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'tools')
sys.path.insert(0, TOOLS)
import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

import card  # noqa: E402
import store  # noqa: E402

MATERIALS = os.path.join(os.path.dirname(TOOLS), 'materials')


def box_faces(bm, low, high):
    """A box from low to high; returns its faces as a dict by side (front is -Y)."""
    (x0, y0, z0), (x1, y1, z1) = low, high
    v = [bm.verts.new(p) for p in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
    sides = {
        'front': (v[0], v[1], v[5], v[4]), 'back': (v[2], v[3], v[7], v[6]),
        'left': (v[3], v[0], v[4], v[7]), 'right': (v[1], v[2], v[6], v[5]),
        'bottom': (v[3], v[2], v[1], v[0]), 'top': (v[4], v[5], v[6], v[7]),
    }
    return {side: bm.faces.new(corners) for side, corners in sides.items()}


def atlas_panel(material_name, rng):
    """Bricks or blocks standing in a panel facing -Y, each its own unit; returns the panel and its mortar backing."""
    material = store.material(material_name)
    atlas = json.load(open(os.path.join(MATERIALS, material['store_atlas'])))
    units = atlas['units']
    width_m, height_m = atlas['picture_size_m']
    brick = material_name.startswith('BRICK')
    joint = 0.010 if brick else 0.008
    panel_w, panel_h = (1.25, 0.82) if brick else (1.7, 1.08)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('pp_atlas')
    piece = bm.faces.layers.float.new('pp_piece')
    z = 0.004
    row = 0
    sizes = [((u1 - u0) * width_m, (v1 - v0) * height_m) for u0, v0, u1, v1 in units]
    course_h = 0.065 if brick else 0.33
    while z + course_h <= 0.004 + panel_h + 1e-6:
        x = -panel_w / 2 - (0.11 if (brick and row % 2) else (0.21 * (row % 2) if not brick else 0.0))
        while x < panel_w / 2:
            if brick:
                index = rng.randrange(len(units))
                length = 0.215
            else:
                fitting = [i for i, (w, h) in enumerate(sizes) if abs(h - course_h) < 0.06] or list(range(len(units)))
                index = rng.choice(fitting)
                length = min(sizes[index][0] * (course_h / max(sizes[index][1], 1e-3)), 0.9)
            x0, x1 = max(x, -panel_w / 2), min(x + length, panel_w / 2)
            if x1 - x0 > 0.03:
                faces = box_faces(bm, (x0, -0.1, z), (x1, 0.0, z + course_h))
                u0, v0, u1, v1 = units[index]
                # a unit cut by the panel's end shows the matching part of its rectangle
                cu0 = u0 + (u1 - u0) * (x0 - x) / length
                cu1 = u0 + (u1 - u0) * (x1 - x) / length
                turned = rng.random() < 0.3
                number = rng.random()
                strip_u, strip_v = 0.12 * (cu1 - cu0), 0.12 * (v1 - v0)
                rects = {
                    'front': (cu0, v0, cu1, v1), 'back': (cu0, v0, cu1, v1),
                    'top': (cu0, v1 - strip_v, cu1, v1), 'bottom': (cu0, v0, cu1, v0 + strip_v),
                    'left': (cu0, v0, cu0 + strip_u, v1), 'right': (cu1 - strip_u, v0, cu1, v1),
                }
                for side, face in faces.items():
                    a0, b0, a1, b1 = rects[side]
                    corners = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
                    if turned:
                        corners = [(a1, b1), (a0, b1), (a0, b0), (a1, b0)]
                    for loop, corner in zip(face.loops, corners):
                        loop[uv].uv = corner
                    face[piece] = number
            x += length + joint
        z += course_h + joint
        row += 1
    mesh = bpy.data.meshes.new('atlas panel')
    bm.to_mesh(mesh)
    bm.free()
    panel = bpy.data.objects.new('atlas panel', mesh)
    bpy.context.scene.collection.objects.link(panel)
    panel.data.materials.append(material)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.03, (panel_h + 0.01) / 2))
    backing = bpy.context.object
    backing.scale = (panel_w, 0.08, panel_h + 0.01)
    store.use_material(backing, 'SURFACE • rough_plasterbrick_05', ground=0.0)
    return panel, backing


def pieces_row(material_name, kind, rng):
    """Pieces lying on the ground (setts, flags) or standing (blocks), each with its own pp_piece, in one mesh."""
    material = store.material(material_name)
    bm = bmesh.new()
    piece = bm.faces.layers.float.new('pp_piece')
    if kind == 'setts':
        size, gap, columns, rows = (0.2, 0.1, 0.12), 0.015, 7, 9
    else:
        size, gap, columns, rows = (0.6, 0.45, 0.06), 0.012, 3, 3
    total_w = columns * (size[0] + gap)
    total_d = rows * (size[1] + gap)
    for r in range(rows):
        for c in range(columns):
            x = -total_w / 2 + c * (size[0] + gap) + (size[0] / 2 if (kind == 'setts' and r % 2) else 0.0)
            y = -total_d / 2 + r * (size[1] + gap)
            faces = box_faces(bm, (x, y, 0.0), (x + size[0], y + size[1], size[2]))
            number = rng.random()
            for face in faces.values():
                face[piece] = number
    mesh = bpy.data.meshes.new('pieces')
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new('pieces', mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj.location = (0.0, 0.0, 0.0)
    obj['pp_ground'] = 0.0
    return obj


CARDS = [('atlas', 'BRICK • brick_wall_02', None), ('atlas', 'BRICK • brick_wall_10', None),
         ('atlas', 'ASHLAR • sandstone_blocks_05', None), ('pieces', 'SURFACE • dark_rock_02', 'setts'),
         ('pieces', 'SURFACE • worn_rock_natural_01', 'flags')]


def every_card():
    import subprocess
    for what, name, kind in CARDS:
        out = os.path.join(card.CARDS, 'materials', card.file_name(name) + '.png')
        subprocess.run([sys.executable, os.path.abspath(__file__), '--', what, name, out] + ([kind] if kind else []), check=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not argv:
        return every_card()
    what, name, out = argv[0], argv[1], argv[2]
    rng = random.Random(5)
    scene = card._empty_scene()
    centre = Vector((0.0, 0.05, 0.5))
    if what == 'atlas':
        panel, backing = atlas_panel(name, rng)
        panel.rotation_euler = (0, 0, math.radians(14))
        backing.rotation_euler = (0, 0, math.radians(14))
        centre = Vector((0.0, 0.0, 0.47 if name.startswith('BRICK') else 0.6))
        card._stage(scene, centre, 0.9)
        camera_location = (0.3, -2.75, 0.95) if name.startswith('BRICK') else (0.35, -3.6, 1.05)
    else:
        kind = argv[3] if len(argv) > 3 else 'setts'
        obj = pieces_row(name, kind, rng)
        obj.rotation_euler = (0, 0, math.radians(12))
        centre = Vector((0.0, 0.0, 0.1))
        card._stage(scene, centre, 0.9)
        camera_location = (0.3, -2.6, 2.3) if kind == 'setts' else (0.4, -3.4, 2.9)
    data = bpy.data.cameras.new('card camera')
    data.lens = 50
    camera = bpy.data.objects.new('card camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = camera_location
    camera.rotation_euler = (centre - camera.location).to_track_quat('-Z', 'Y').to_euler()
    store.prepare_for_render(scene)
    width, height = (360, 220)
    card._render(scene, out, width, height, 24)
    print('drew', out)


if __name__ == '__main__':
    main()
