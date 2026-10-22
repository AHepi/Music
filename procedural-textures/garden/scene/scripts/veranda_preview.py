# What this does: a small EEVEE preview (not Cycles) of the courtyard from the veranda, looking out over the pond: the story's next-step "veranda view".
#   In-memory copy only; saves one PNG. Arguments: OUT.png CAMX CAMY CAMZ TARGX TARGY TARGZ [LENS] [WIDTH]
import bpy, sys, math, time
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; cx, cy, cz, tx, ty, tz = [float(v) for v in a[1:7]]
lens = float(a[7]) if len(a) > 7 else 24.0; width = int(a[8]) if len(a) > 8 else 800
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 16; sc.eevee.use_raytracing = True
except Exception as e: print('eevee settings', e)
sc.render.resolution_x = width; sc.render.resolution_y = int(width * 2 / 3); sc.render.resolution_percentage = 100
cam = sc.camera; cd = cam.data; cd.dof.use_dof = False; cd.lens = lens
cam.location = (cx, cy, cz); cam.rotation_euler = (Vector((tx, ty, tz)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print('EEVEE_SECONDS', round(time.time() - t, 1))
