import bpy, sys
from mathutils import Vector
cam = bpy.data.objects['veranda']; sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
TR,BR,BL,TL = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]
o = cam.matrix_world.translation
for (px,py) in [(420,585),(360,610),(500,570),(990,330)]:
    u=px/1200; v=1-py/800
    pt = BL+(BR-BL)*u+(TL-BL)*v
    d=(pt-o).normalized()
    hit, loc, nrm, idx, ob, mat = sc.ray_cast(dg, o, d)
    print((px,py), hit, ob.name if ob else None, tuple(round(x,2) for x in loc), [s.material.name for s in ob.material_slots] if ob else None)
