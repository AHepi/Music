import bpy, bmesh
import place_kit as pk
OWNER = 'hut'
def box(name, size, loc, role):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for v in builder.verts:
        v.co.x *= size[0]; v.co.y *= size[1]; v.co.z *= size[2]
    builder.to_mesh(mesh); builder.free()
    obj = pk.new_part_object(OWNER, role, name, mesh)
    obj.location = loc
    return obj
def apply(options):
    pk.forget_part(OWNER); pk.begin_part(OWNER)
    wall = box('hut wall', (3, 3, 2.2), (0, 0, 1.1), 'wall.plaster')
    pk.seat_on_ground(wall)
