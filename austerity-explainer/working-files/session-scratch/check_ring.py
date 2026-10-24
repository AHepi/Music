import sys, os
WORK='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, WORK+'/lib'); sys.path.insert(0, WORK+'/modules')
import bpy, numpy as np
import mine_common as mc, headframe
mc.clear_scene()
headframe.build('Headframe')
obj = bpy.data.objects['Headframe steel']
mesh = obj.data
centre = np.array([-1.55, -3.4, 16.6])
res = {'outer_ok':0,'outer_bad':0,'inner_ok':0,'inner_bad':0}
for poly in mesh.polygons:
    c = np.array(poly.center); n = np.array(poly.normal)
    rel = c - centre
    if abs(rel[0]) < 0.16:
        r = np.hypot(rel[1], rel[2])
        radial = np.array([0, rel[1], rel[2]])/max(r,1e-9)
        if abs(r-2.30) < 0.01 and abs(np.dot(n,[1,0,0]))<0.2:
            res['outer_ok' if np.dot(n,radial)>0 else 'outer_bad'] += 1
        if abs(r-2.02) < 0.01 and abs(np.dot(n,[1,0,0]))<0.2:
            res['inner_ok' if np.dot(n,radial)<0 else 'inner_bad'] += 1
print('RING CHECK', res)
