# What this does (plain words): STUDY ONLY, saves only a small label grid. Same rays as s6_view_shares.py for the main camera of the street copy, but keeps WHAT each ray hit (material name and
# family) in a file, so a picture drawn from the same camera can be measured surface by surface.
import json, math, re, sys
import bpy
import numpy as np
from mathutils import Vector
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
out = sys.argv[sys.argv.index('--') + 1]
cam = scene.camera
W, H = 90, 160
tan_v = math.tan(cam.data.angle_y / 2)
tan_h = tan_v * (1536 / 2730)
origin = cam.matrix_world.translation
rot = cam.matrix_world.to_quaternion()
labels = []
for j in range(H):
    row = []
    for i in range(W):
        sx = ((i + 0.5) / W * 2 - 1) * tan_h
        sy = (1 - (j + 0.5) / H * 2) * tan_v
        d = rot @ Vector((sx, sy, -1.0)).normalized()
        hit, loc, nor, idx, obj, mtx = scene.ray_cast(deps, origin, d)
        mat = None
        if hit and obj.type == 'MESH' and idx < len(obj.data.polygons):
            mi = obj.data.polygons[idx].material_index
            if mi < len(obj.material_slots) and obj.material_slots[mi].material:
                mat = obj.material_slots[mi].material.name
        row.append([mat, obj.name if hit else None, round(loc.z, 2) if hit else None, round(abs(nor.z), 2) if hit else None])
    labels.append(row)
json.dump(labels, open(out, 'w'))
