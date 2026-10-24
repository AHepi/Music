# What this does: a quick layout picture (Blender's Workbench, textures, flat studio light) of the scene camera that
# the assembly script left on a view's composed spot. Scratch tool for round 4.
# Run after assemble_works.py: ... --python assemble_works.py --python quick_view.py -- --view w1 --quick OUT.png [--quick-width 540] [--plate]
import bpy, sys, math
args = sys.argv[sys.argv.index('--') + 1:]
out = args[args.index('--quick') + 1]
width = int(args[args.index('--quick-width') + 1]) if '--quick-width' in args else 540
scene = bpy.context.scene
if '--plate' in args:
    view = args[args.index('--view') + 1]
    cam = bpy.data.objects[f'camera-{view}']
    import json, os
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_shadows = False
scene.display.shading.show_cavity = False
scene.render.resolution_x, scene.render.resolution_y = width, round(width * 16 / 9)
scene.render.resolution_percentage = 100
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print('quick view written', out)
