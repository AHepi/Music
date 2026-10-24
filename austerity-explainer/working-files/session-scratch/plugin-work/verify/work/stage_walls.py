"""What this does: the WALLS AND STEPS part of the canal lock side (owner walls_and_steps): the near and far brick lock walls (made of panels of
different length with a few millimetres of settlement between them), the stone coping on top of each, and a flight of seven stone steps
that goes down a trench in the towpath and through a gap in the near wall to the water, with its cheek walls and back wall.
Built by the verifier from the plugin's stage template. Idempotent. It stands everything on the frozen ground (seat_on_ground) or on the
part below it, and never touches another owner's objects.
A concrete example of use: apply({'seed': 3}) makes the same walls every time for seed 3.
"""
import os
import sys

import bmesh
import bpy
import numpy as np

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402

OWNER = 'walls_and_steps'
WALL_TOP = 0.0
BED_Z = -2.0
WATER_Z = -1.1
NEAR = (-0.49, 0.0)         # y range of the near wall (its inner face stays 1 cm clear of the towpath edge at -0.5)
FAR = (2.4, 2.89)           # y range of the far wall (1 cm clear of the far verge at 2.9)
GAP = (-3.4, -2.2)          # the gap in the near wall where the steps come through


def box_mesh(name, sx, sy, sz, bevel=0.0):
    """A box of the given size; with bevel > 0 its edges are real chamfers of that width (the finishing pass bevels walls and timber itself, not stone)."""
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= sx
        vertex.co.y *= sy
        vertex.co.z *= sz
    if bevel > 0:
        bmesh.ops.bevel(builder, geom=list(builder.edges), offset=min(bevel, min(sx, sy, sz) / 4), offset_type='OFFSET', segments=2, profile=0.5, affect='EDGES')
    builder.to_mesh(mesh)
    builder.free()
    return mesh


def block(role, name, x0, x1, y0, y1, z0, z1, ground=False, bevel=0.0):
    """A box between the given world limits, as one object of this part; with ground=True it is seated on the ground under it."""
    mesh = box_mesh(name, x1 - x0, y1 - y0, z1 - z0, bevel)
    obj = pk.new_part_object(OWNER, role, name, mesh)
    obj.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    if ground:
        pk.seat_on_ground(obj)
    return obj


def lengths_along(total, low, high, rng):
    """Piece lengths between low and high metres that add up to total."""
    pieces, left = [], total
    while left > high:
        piece = float(rng.uniform(low, high))
        pieces.append(piece)
        left -= piece
    if left < low and pieces:
        pieces[-1] += left
    else:
        pieces.append(left)
    return pieces


def wall_run(label, y0, y1, x_start, x_end, rng, settle):
    """Brick wall panels (ground-seated) with coping stones on top, from x_start to x_end."""
    count = 0
    x = x_start
    for length in lengths_along(x_end - x_start, 1.7, 2.6, rng):
        jitter = float(rng.uniform(0.0, settle))                       # settlement shows only on the water face
        panel = block('wall.brick', f'Wall {label} panel {count + 1}', x, x + length, y0, y1 + jitter, BED_Z, WALL_TOP, ground=True)
        count += 1
        x += length
    # coping: fat pale stones lying on the wall top, a hair wider than the wall each side, of different length and thickness
    x = x_start
    index = 0
    for length in lengths_along(x_end - x_start, 0.55, 0.95, rng):
        thick = float(rng.uniform(0.08, 0.11))
        block('stone.footing', f'Coping {label} stone {index + 1}', x + 0.004, x + length - 0.004, y0 - 0.06, y1 + 0.06, WALL_TOP, WALL_TOP + thick, bevel=0.012)
        index += 1
        x += length


def apply(options):
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    rng = np.random.default_rng(int(options.get('seed', 3)))
    # the near wall: two runs with the gap for the steps between them
    wall_run('near west', NEAR[0], NEAR[1], -6.0, GAP[0], rng, 0.005)
    wall_run('near east', NEAR[0], NEAR[1], GAP[1], 6.0, rng, 0.005)
    wall_run('far', FAR[0], FAR[1], -6.0, 6.0, rng, 0.005)
    # the trench for the steps: back wall and two cheek walls on the bed, a core of masonry, and seven stone slabs stacked on it, each one rise thick
    trench_y0, trench_y1 = -2.6, -0.5
    block('stone.footing', 'Trench back wall', -3.6, -2.0, -2.8, -2.6, BED_Z, WALL_TOP, ground=True, bevel=0.012)
    block('stone.footing', 'Trench cheek west', -3.6, -3.4, trench_y0, trench_y1, BED_Z, WALL_TOP, ground=True, bevel=0.012)
    block('stone.footing', 'Trench cheek east', -2.2, -2.0, trench_y0, trench_y1, BED_Z, WALL_TOP, ground=True, bevel=0.012)
    rise = 0.17
    lowest_top = -rise * 7
    core = block('stone.footing', 'Flight core', GAP[0], GAP[1], trench_y0, NEAR[1], BED_Z, lowest_top - rise, ground=True, bevel=0.012)
    for i in range(7):
        top = -rise * (i + 1)
        front = trench_y0 + 0.3 * (i + 1)                              # tread i + 1 ends here; the slab runs back to the trench wall
        block('floor.stone', f'Step {i + 1}', GAP[0], GAP[1], trench_y0, front, top - rise, top, bevel=0.012)
    # the landing in the gap of the wall, level with the lowest step, resting on the core
    block('floor.stone', 'Step landing', GAP[0], GAP[1], trench_y1, NEAR[1], lowest_top - rise, lowest_top, bevel=0.012)
