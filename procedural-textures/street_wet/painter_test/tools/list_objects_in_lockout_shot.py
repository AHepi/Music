"""What this file does (plain words): opens the film's lockout shot file (read-only: it never saves anything) and writes the names of
the top-level objects, with their children counts and where they stand, to work/lockout_object_names.txt, so a shot check file for the
lockout can be written. Run: blender -b --disable-autoexec -t 2 LOCKOUT.blend --python tools/list_objects_in_lockout_shot.py -- OUT.txt
"""
import sys, bpy
out = sys.argv[sys.argv.index('--') + 1]
lines = []
cam = bpy.context.scene.camera
lines.append(f'scene camera: {cam.name if cam else None}')
if cam: lines.append(f'  camera location {tuple(round(v,3) for v in cam.location)} rotation {tuple(round(v,4) for v in cam.rotation_euler)} lens fov {cam.data.angle:.4f} rad sensor_fit {cam.data.sensor_fit}')
lines.append(f'render size {bpy.context.scene.render.resolution_x} x {bpy.context.scene.render.resolution_y}')
for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.parent is None:
        n = sum(1 for _ in o.children_recursive)
        lines.append(f'{o.name}\t{o.type}\tchildren={n}\tat {tuple(round(v,2) for v in o.matrix_world.translation)}\tcollections={[c.name for c in o.users_collection]}')
open(out, 'w').write('\n'.join(lines))
