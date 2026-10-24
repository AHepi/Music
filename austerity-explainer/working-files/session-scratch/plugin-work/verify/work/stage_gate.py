"""What this does: the LOCK GATE part of the canal lock side (owner lock_gate): two timber gate leaves that meet in a V pointing at the
higher water. Each leaf is a heel post and a mitre post standing on the bed, five rails between them, vertical boards of different width fixed
to the rails on the downstream face, iron straps round the heel post, and a long balance beam lying on the heel post and reaching back over the wall.
Built by the verifier from the plugin's stage template. Idempotent.
A concrete example of use: apply({'angle_degrees': 20}) makes a gate whose leaves lean 20 degrees from straight across the channel.
"""
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402

OWNER = 'lock_gate'
GATE_X = 3.5                 # where the heel posts stand along the canal
CHANNEL_WIDTH = 2.4
POST_SIDE = 0.30
RAIL_HEIGHT = 0.18
LEAF_TOP = 0.30
HEEL_SETBACK = 0.30          # the heel post's centre stands this far from the wall face, clear of the coping's overhang


def box_mesh(name, sx, sy, sz, bevel=0.0):
    """A box of the given size; with bevel > 0 its edges are real chamfers (the finishing pass bevels timber itself, not iron)."""
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


def part(role, name, size, local_centre, frame, bevel=0.0):
    """A box of the given size whose centre sits at local_centre (u along the leaf, v across it, z up) in the leaf's own frame."""
    obj = pk.new_part_object(OWNER, role, name, box_mesh(name, *size, bevel=bevel))
    obj.matrix_world = frame @ Matrix.Translation(Vector(local_centre))
    return obj


def build_leaf(side, angle_degrees, rng):
    """One gate leaf. side is +1 for the near wall's leaf (heel at the low y) and -1 for the far one."""
    label = 'near' if side > 0 else 'far'
    heel_y = HEEL_SETBACK if side > 0 else CHANNEL_WIDTH - HEEL_SETBACK
    theta = math.radians(angle_degrees)
    # the leaf's own direction: toward the middle of the channel and a little toward the higher water (+x)
    direction = Vector((math.sin(theta), side * math.cos(theta), 0.0))
    rotation = math.atan2(direction.y, direction.x)
    bed = pk.ground_height_at(GATE_X, heel_y)
    length = (CHANNEL_WIDTH / 2 - HEEL_SETBACK) / math.cos(theta) - 0.06    # heel centre to the mitre end (6 cm short so the two mitre posts do not cut into each other)
    frame = Matrix.Translation(Vector((GATE_X, heel_y, bed))) @ Matrix.Rotation(rotation, 4, 'Z')
    # local frame: u along the leaf from the heel, v across it, z up from the bed. The downstream (low water, -x) face is at v = side * positive.
    top_local = LEAF_TOP - bed                 # leaf height above the bed
    post_height = 0.62 - bed                   # the heel post is taller: the balance beam lies on it
    heel_post = part('timber.post', f'Gate {label} heel post', (POST_SIDE, POST_SIDE, post_height), (0.0, 0.0, post_height / 2), frame)
    pk.seat_on_ground(heel_post)
    mitre_u = length - 0.11
    mitre_post = part('timber.post', f'Gate {label} mitre post', (0.22, 0.26, top_local), (mitre_u, 0.0, top_local / 2), frame)
    pk.seat_on_ground(mitre_post)
    # rails run from the heel post to the mitre post and 5 cm into each (the tenons in the mortices), so each is joined to both
    rail_u0, rail_u1 = POST_SIDE / 2, mitre_u - 0.11
    first, last = top_local - 0.10, 0.14
    for k in range(5):
        zc = first + (last - first) * k / 4
        part('timber.fence', f'Gate {label} rail {k + 1}', (rail_u1 - rail_u0 + 0.10, 0.22, RAIL_HEIGHT), ((rail_u0 + rail_u1) / 2, 0.0, zc), frame)
    # vertical boards on the downstream face: different widths and a little different heights
    u = rail_u0
    index = 0
    while u < rail_u1 - 0.09:
        width = min(float(rng.uniform(0.13, 0.17)), rail_u1 - u)
        top = top_local - float(rng.uniform(0.0, 0.015))
        bottom = 0.0                     # the boards stand on the bed, so each is carried by the ground
        part('timber.plank', f'Gate {label} board {index + 1}', (width - 0.006, 0.05, top - bottom), (u + width / 2, side * 0.135, (top + bottom) / 2), frame)
        u += width
        index += 1
    # two iron straps round the heel post, a centimetre proud
    for number, zc in enumerate((top_local - 0.5, top_local - 1.5), start=1):
        part('iron.fitting', f'Gate {label} heel strap {number}', (POST_SIDE + 0.02, POST_SIDE + 0.02, 0.07), (0.0, 0.0, zc), frame, bevel=0.008)
    # the balance beam: on top of the heel post, running back along the leaf over the wall (u negative)
    beam_length = 2.2
    part('timber.beam', f'Gate {label} balance beam', (beam_length, 0.20, 0.22), (POST_SIDE / 2 - beam_length / 2, 0.0, post_height + 0.11), frame)


def apply(options):
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    rng = np.random.default_rng(int(options.get('seed', 11)))
    angle = float(options.get('angle_degrees', 20))
    build_leaf(+1, angle, rng)
    build_leaf(-1, angle, rng)
