import bpy, json, numpy as np
from mathutils import Vector
sc = bpy.context.scene
cams = [('Place props cam 1', (-31.0, 0.6, 2.1), (-31.2, 7.2, 0.7), 24), ('Place props cam 2', (-26.0, -19.5, 2.6), (-33.0, -12.8, 1.2), 30), ('Place props cam 3', (-6.0, 19.5, 2.0), (-6.0, 13.5, 0.7), 28)]
for name, loc, tgt, lens in cams:
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 1500
    co = bpy.data.objects.new(name, cd); sc.collection.objects.link(co)
    co.location = Vector(loc); co.rotation_euler = (Vector(tgt) - co.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/props/batch.blend', compress=True)
