# What this file does (plain words)
# ----------------------------------------------------------------------------------------------------------------------------------
# Draws Blender's exact SKY MASK for the lockout camera, large and with smooth (anti-aliased) edges, so that a plain dark sky can be put into a
# painting with a clean soft edge along the roof lines, the chimney, the winding wheels' spokes and the rope.
# It opens the film's lockout.blend (read only; nothing is saved), hides the sky dome (the same way the film's shot_facts.py does), draws everything
# else as flat white with the Workbench engine at 32 samples with a see-through background, and saves the picture. In the picture the opacity (alpha)
# is 1 where something other than sky is seen and 0 where only sky is seen. Size 3072 x 5460 (twice the plate), to be shrunk to 1536 x 2730.
# Run (on the rented machine):
#   /workspace/blender/blender -b --disable-autoexec LOCKOUT.blend --python make_sky_mask_blender.py -- OUT.png [WIDTH HEIGHT]
import fnmatch
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
width, height = (int(args[1]), int(args[2])) if len(args) >= 3 else (3072, 5460)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
shading = scene.display.shading
shading.light = 'FLAT'
shading.color_type = 'SINGLE'
shading.single_color = (1.0, 1.0, 1.0)
shading.show_shadows = False
shading.show_cavity = False
shading.show_object_outline = False
shading.show_specular_highlight = False
shading.show_xray = False
scene.display.render_aa = '32'
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = width, height, 100
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
hidden = []
for o in scene.objects:
    if fnmatch.fnmatch(o.name, 'sky_dome*'):
        o.hide_render = True
        hidden.append(o.name)
print('sky_mask: hidden sky objects:', hidden, '; camera:', scene.camera.name if scene.camera else None)
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print('sky_mask: saved', out)
