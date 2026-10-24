"""What this does: the PROPS part of the canal lock side (owner props): two cast-iron mooring bollards on the towpath edge, a wooden crate, a barrel
with two iron bands, and a coil of rope. Built by the verifier from the plugin's stage template. Idempotent; each prop is seated on the real ground.
A concrete example of use: apply({}) makes seven objects in the collection "Place: props".
"""
import math
import os
import sys

import bmesh
import bpy

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402

OWNER = 'props'


def cylinder_mesh(name, radius, height, sides=24):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cone(builder, cap_ends=True, segments=sides, radius1=radius, radius2=radius, depth=height)
    builder.to_mesh(mesh)
    builder.free()
    return mesh


def box_mesh(name, sx, sy, sz, bevel=0.0):
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


def torus_mesh(name, major, minor, major_segments=32, minor_segments=10):
    mesh = bpy.data.meshes.new(name)
    vertices, faces = [], []
    for i in range(major_segments):
        a = 2 * math.pi * i / major_segments
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major + minor * math.cos(b)
            vertices.append((r * math.cos(a), r * math.sin(a), minor * math.sin(b)))
    for i in range(major_segments):
        for j in range(minor_segments):
            a = i * minor_segments + j
            b = ((i + 1) % major_segments) * minor_segments + j
            c = ((i + 1) % major_segments) * minor_segments + (j + 1) % minor_segments
            d = i * minor_segments + (j + 1) % minor_segments
            faces.append((a, b, c, d))
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def apply(options):
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    # two mooring bollards on the towpath, near the wall (cast iron, painted black once)
    for number, x in enumerate((-0.8, 1.9), start=1):
        bollard = pk.new_part_object(OWNER, 'iron.painted', f'Prop bollard {number}', cylinder_mesh(f'Prop bollard {number}', 0.085, 0.42))
        bollard.location = (x, -0.95, 0.21)
        pk.seat_on_ground(bollard, sink=0.04)
    crate = pk.new_part_object(OWNER, 'prop.crate', 'Prop crate', box_mesh('Prop crate', 0.55, 0.42, 0.38, bevel=0.01))
    crate.location = (-5.0, -1.9, 0.19)
    crate.rotation_euler = (0.0, 0.0, math.radians(14))
    pk.seat_on_ground(crate)
    barrel = pk.new_part_object(OWNER, 'prop.barrel', 'Prop barrel', cylinder_mesh('Prop barrel', 0.28, 0.85, 20))
    barrel.location = (-4.45, -2.05, 0.43)
    pk.seat_on_ground(barrel)
    for number, dz in enumerate((-0.25, 0.25), start=1):
        band = pk.new_part_object(OWNER, 'iron.fitting', f'Prop barrel band {number}', cylinder_mesh(f'Prop barrel band {number}', 0.29, 0.05, 20))
        band.location = (-4.45, -2.05, 0.43 + dz)
    rope = pk.new_part_object(OWNER, 'prop.rope', 'Prop rope coil', torus_mesh('Prop rope coil', 0.22, 0.05))
    rope.location = (-1.6, -1.5, 0.05)
    pk.seat_on_ground(rope)
