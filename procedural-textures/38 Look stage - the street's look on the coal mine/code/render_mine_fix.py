"""
What this file does: the one fix pass after the judge's numbers. Same scene, same camera, the look stage with
exposure 1.0 instead of 0.5 and window lights twice as strong. Writes mine-C-look-fixed.png.
"""
import json, os, sys, time
import bpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import look_stage
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'mine-as-is.blend'))
scene = bpy.context.scene
report = look_stage.apply_look(scene, samples=32, resolution=(540, 960), exposure=1.0, window_light_scale=2.0, max_glow_lights=48)
print('fix report:', json.dumps({k: v for k, v in report.items() if k != 'added_objects'}, default=str))
scene.render.filepath = os.path.join(HERE, 'mine-C-look-fixed.png')
started = time.time(); bpy.ops.render.render(write_still=True); print('C fixed:', round(time.time() - started, 1), 's')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'mine-C-look-fixed.blend'))
