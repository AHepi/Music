# Checks Blender's light linking from a script: two planes under one light, one left out of the light's reach.
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 200, 100
bpy.ops.mesh.primitive_plane_add(size=1, location=(-0.6, 0, 0)); kept = bpy.context.active_object
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.6, 0, 0)); left_out = bpy.context.active_object
bpy.ops.object.light_add(type='POINT', location=(0, 0, 1)); light = bpy.context.active_object; light.data.energy = 300
receivers = bpy.data.collections.new('receivers')
receivers.objects.link(left_out)
light.light_linking.receiver_collection = receivers
for item in receivers.collection_objects:
    item.light_linking.link_state = 'EXCLUDE'
bpy.ops.object.camera_add(location=(0, 0, 3)); scene.camera = bpy.context.active_object
scene.camera.data.type = 'ORTHO'; scene.camera.data.ortho_scale = 2.4
scene.render.filepath = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/light-link-trial/trial.png'
bpy.ops.render.render(write_still=True)
import numpy as np
px = np.array(bpy.data.images.load(scene.render.filepath).pixels[:]).reshape(100, 200, 4)
print('kept plane brightness', round(float(px[50, 50, 0]), 3), 'left-out plane', round(float(px[50, 150, 0]), 3))
