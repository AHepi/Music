import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import bpy, numpy as np
import r_stones
for name in ("Pond edge stone 3","Pond edge stone 10"):
    o=bpy.data.objects[name]
    print(name,"mw translation",tuple(round(x,2) for x in o.matrix_world.translation),"signed vol", r_stones.signed_volume(o.data))
    me=r_stones.give_stone_uv_and_mesh(o,1.0)
    lay=me.uv_layers[0]; k=0
    for p in me.polygons:
        n=p.normal
        if abs(n[0])>0.9 and k<2:
            k+=1
            vs=[tuple(round(c,3) for c in me.vertices[me.loops[li].vertex_index].co) for li in p.loop_indices]
            uvs=[tuple(round(c,3) for c in lay.data[li].uv) for li in p.loop_indices]
            print("  n",tuple(round(x,2) for x in n),"verts(y,z)",[(v[1],v[2]) for v in vs],"uv",uvs)
