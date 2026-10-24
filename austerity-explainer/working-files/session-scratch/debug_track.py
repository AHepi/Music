# debug helper: print info about the built objects
import sys, os
WORK='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, WORK+'/lib'); sys.path.insert(0, WORK+'/modules')
import bpy, numpy as np
import mine_common as mc
import track_and_carts as tc
mc.clear_scene()
r = tc.build('Mine')
for name in r['objects']:
    o = bpy.data.objects[name]
    co = np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1,3)
    print(name, len(o.data.polygons), co.min(axis=0).round(2), co.max(axis=0).round(2), [m.type for m in o.modifiers])
# sleepers near s=3
o = bpy.data.objects['Track sleepers']
co = np.empty(len(o.data.vertices)*3); o.data.vertices.foreach_get('co', co); co = co.reshape(-1,3)
sel = co[(abs(co[:,0]-0.0)<2)&(abs(co[:,1]+3)<0.5)]
print(sel[:12].round(3))
path = tc.TrackPath()
print('length', path.length, 'start', path.start_s, 'bed at 0,5,10', [round(path.bed_height(s),3) for s in (0,5,10,20)])
