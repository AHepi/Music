import bpy, json, sys, numpy as np
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import scene_read
out={'trunks':[], 'crowns':[], 'small':[], 'cams':{}}
for o in bpy.data.objects:
    if o.get('place_owner')!='forest' or o.type!='MESH': continue
    me=o.data; n=len(me.vertices)
    co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
    m=np.array(o.matrix_world); w=co@m[:3,:3].T+m[:3,3]
    labels,k=scene_read.loose_part_labels(me)
    role=o.get('place_role')
    for i in range(k):
        v=w[labels==i]
        rec=[o.name, role, float(v[:,0].mean()), float(v[:,1].mean()), float(v[:,2].min()), float(v[:,2].max()), float(v[:,0].max()-v[:,0].min()), float(v[:,1].max()-v[:,1].min())]
        if role=='tree.bark' and o.name.startswith('Tree'): out['trunks'].append(rec)
        elif role=='plant.foliage' and o.name.startswith('Tree'): out['crowns'].append(rec)
        else: out['small'].append(rec)
for c in bpy.data.objects:
    if c.type=='CAMERA':
        m=c.matrix_world; out['cams'][c.name]=[float(m.translation.x),float(m.translation.y),float(m.translation.z),float((m.to_3x3()@__import__('mathutils').Vector((0,0,-1))).x),float((m.to_3x3()@__import__('mathutils').Vector((0,0,-1))).y)]
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest/layout.json','w'))
print('dumped', len(out['trunks']), len(out['crowns']), len(out['small']))
