# What this does: builds a small tea-room corner to look at the 0.5.0 additions by eye: a plaster wall with a lit
# window and a dark one, a brass urn, a copper kettle and a china teapot with cups on a counter, a camera close by.
import sys
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
def box(name, centre, size):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    obj = bpy.context.object; obj.name = name; obj.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return obj
box('tea room back wall plaster', (0, 4.15, 2.0), (6, 0.3, 4))
box('window lit 1', (-1.2, 3.98, 2.0), (1.0, 0.04, 1.4))
box('window dark 2', (1.4, 3.98, 2.0), (1.0, 0.04, 1.4))
box('tea room floor boards', (0, 2.0, -0.05), (6, 5, 0.1))
box('counter wood', (0, 2.6, 0.5), (2.4, 0.6, 1.0))
for name, location, radius in (('tea urn brass', (-0.6, 2.6, 1.25), 0.22), ('copper kettle', (0.15, 2.6, 1.12), 0.12), ('teapot', (0.6, 2.55, 1.10), 0.10)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=32, ring_count=16)
    bpy.context.object.name = name
    bpy.ops.object.shade_smooth()
for k in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.07, location=(0.85 + 0.12 * k, 2.45, 1.035), vertices=24)
    bpy.context.object.name = 'teacup %d' % k
bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.6, location=(-0.6, 2.6, 1.6), vertices=16)
bpy.context.object.name = 'urn tap brass'
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(0.4, 3.2, 3.2))
bpy.context.object.name = 'lamp glass'
camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
scene.collection.objects.link(camera)
camera.location = (0.3, -1.2, 1.6)
camera.rotation_euler = (Vector((0.0, 3.0, 1.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 32
scene.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
