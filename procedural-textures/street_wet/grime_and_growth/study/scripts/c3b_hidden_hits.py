# What this does (plain words): STUDY ONLY, saves nothing. Repeats the camera-ray count of c3_survey.py but names the exact object hit, to see what the "hidden" family
# (4 % of rays) really is (the roof tiles are copies of a hidden prototype, so rays that hit them name the prototype).
# Run: blender -b --disable-autoexec FILE --python c3b_hidden_hits.py -- OUT.json
import json, math, sys
from collections import Counter
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene; deps = bpy.context.evaluated_depsgraph_get(); cam = scene.camera
W, H = 240, 160
tan_h = math.tan(cam.data.angle_x / 2); tan_v = tan_h * (H / W)
origin = cam.matrix_world.translation; rot = cam.matrix_world.to_quaternion()
c = Counter(); sky = 0; dist_by = {}
for j in range(H):
    for i in range(W):
        d = rot @ Vector((((i + .5) / W * 2 - 1) * tan_h, (1 - (j + .5) / H * 2) * tan_v, -1.0)).normalized()
        hit, loc, nor, idx, ob, mtx = scene.ray_cast(deps, origin, d)
        if not hit: sky += 1; continue
        c[ob.name] += 1
        dist_by.setdefault(ob.name, []).append((loc - origin).length)
tot = W * H
res = {'grid': [W, H], 'sky': sky / tot, 'by_object': {k: {'share': round(v / tot, 4), 'median_distance_m': round(sorted(dist_by[k])[len(dist_by[k]) // 2], 2)} for k, v in c.most_common()}}
json.dump(res, open(out, 'w'), indent=1)
