import bpy, bmesh
import place_kit as pk
OWNER = 'roads_and_ground'
def apply(options):
    pk.forget_part(OWNER); pk.begin_part(OWNER)
    mesh = bpy.data.meshes.new('ground mesh')
    builder = bmesh.new()
    bmesh.ops.create_grid(builder, x_segments=24, y_segments=24, size=10.0)
    builder.to_mesh(mesh); builder.free()
    obj = pk.new_part_object(OWNER, 'ground.dirt_road', 'ground', mesh)
