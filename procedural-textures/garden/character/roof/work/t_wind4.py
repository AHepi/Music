import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import bpy, numpy as np
import r_stones, r_common
for name in ("Pond edge stone 3","Pond edge stone 10"):
    o=bpy.data.objects[name]
    me=o.data.copy()
    print(name,"copy signed volume",r_common.signed_volume(me), "orig",r_common.signed_volume(o.data))
    fn=r_common.box_uv_fn(1.0,off=(0,0),world=o.matrix_world,inside_out=r_common.signed_volume(me)<0)
    # test a +x face
    for p in me.polygons:
        if p.normal[0]>0.9:
            co=me.vertices[me.loops[p.loop_indices[0]].vertex_index].co
            print("  face n",tuple(round(x,2) for x in p.normal),"uv",fn(co,p.normal)); break
    print("  inside_out", r_common.signed_volume(me)<0)
