import sys
WORK='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, WORK+'/lib'); sys.path.insert(0, WORK+'/modules')
import numpy as np, bpy
import mine_common as mc
import track_and_carts as tc
mc.clear_scene()
r = tc.build('Mine')
legs = [(sx*3.1, -3.4+sy*2.7) for sx in (-1,1) for sy in (-1,1)]
for name in r['objects']:
    o = bpy.data.objects[name]
    co = np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    best=1e9
    for lx,ly in legs:
        d = np.maximum(abs(co[:,0]-lx), abs(co[:,1]-ly)).min()
        best=min(best,d)
    print('CLEAR %-28s min square-distance to a leg centre: %.2f m' % (name, best))
