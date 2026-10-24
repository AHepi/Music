# What this does: draws the proof scene's view camera with EEVEE (the renderer the film owner's rule picks for a place lit only by the sun) as a small JPG, for the
# before-and-after picture of the plugin 1.5.0 surfaces and weeds. Run on a rented card:
#   /workspace/blender/blender -b --disable-autoexec SCENE.blend -P draw_proof.py -- OUT.jpg WIDTH HEIGHT
import sys
import time
import bpy

out_path, width, height = sys.argv[sys.argv.index('--') + 1:][:3]
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = int(width), int(height), 100
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90
scene.camera = bpy.data.objects['View road']
scene.render.filepath = out_path
started = time.time()
bpy.ops.render.render(write_still=True)
print('DREW', out_path, round(time.time() - started, 1), 's')
