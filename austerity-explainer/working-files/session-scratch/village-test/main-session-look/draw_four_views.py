# What this does: opens the village run's finished scene (round 3) and draws its four view cameras as JPG pictures with EEVEE,
# for the person to look at while the plugin's own audit gate still holds the run's pictures back. Run on a rented card:
#   /workspace/blender/blender -b --disable-autoexec FINISHED.blend -P draw_four_views.py -- OUTPUT_FOLDER
import os, sys, time
import bpy

output_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(output_folder, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 800, 100
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 88
camera_names = ['View wide', 'View road_eye', 'View stable_close', 'View cottage_close']
for name in camera_names:
    camera = bpy.data.objects.get(name)
    if camera is None:
        print('NO CAMERA', name)
        continue
    scene.camera = camera
    scene.render.filepath = os.path.join(output_folder, name.replace(' ', '_') + '.jpg')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    print('DREW', name, round(time.time() - started, 1), 's')
