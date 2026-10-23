"""What this does: the SKELETON of a stage file, the way one builder makes its part of a place. Copy it to stage_<owner>.py (for example stage_huts.py), change OWNER, put the
building code in apply(options), and run it alone or with the other builders' stage files:
    explainer-film-place combine --scene start.blend --stages stage_roads.py stage_huts.py --owners ownership.json --order both
A stage file must be IDEMPOTENT (running it twice leaves the same scene): it removes what an earlier run of the SAME owner made, then makes its part again. It must change nothing
that another owner made: no moving of their objects, no change to a shared material or node group, no change to the camera, lights, world or render settings. Every object it makes
gets the owner and exactly one role (new_part_object does both), and is seated on the real ground (seat_on_ground) so nothing floats.
It runs inside Blender. A concrete example of use: apply({'seed': 3}) makes the part with seed 3; apply({'seed': 3}) again gives the same part.
"""
import sys

import bpy
import bmesh

# the place kit's folder is named by the launcher; a stage run by hand finds it from EXPLAINER_FILM_KIT
import os
KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402

OWNER = 'example_part'          # the name of this builder's part: the collection becomes "Place: example_part"


def box_mesh(name, width, depth, height):
    """A plain box (replace it with the real shape: planks, a roof that overhangs, a door in a frame)."""
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= width
        vertex.co.y *= depth
        vertex.co.z *= height
    builder.to_mesh(mesh)
    builder.free()
    return mesh


def apply(options):
    """Makes this builder's part. `options` is a dict from the combine command (--options '{"seed": 3}'); read what you need with options.get(...)."""
    pk.forget_part(OWNER)                       # idempotent: remove what an earlier run made (objects, meshes, collection contents)
    pk.begin_part(OWNER)                        # the collection "Place: <owner>"
    count = int(options.get('count', 2))
    for index in range(count):
        wall = pk.new_part_object(OWNER, 'wall.plaster', f'{OWNER} wall {index + 1}', box_mesh(f'{OWNER} wall {index + 1}', 4.0, 0.3, 2.4))
        wall.location = (index * 6.0, 0.0, 1.2)          # a position in metres; then:
        pk.seat_on_ground(wall)                          # its lowest point rests on the ground under it (a floating wall is a construction failure)
