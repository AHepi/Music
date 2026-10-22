import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import bpy, numpy as np
from collections import Counter
import r_stones
for name in ("Pond edge stone 3","Pond edge stone 10"):
    o=bpy.data.objects[name]
    me=r_stones.give_stone_uv_and_mesh(o,1.0)
    lay=me.uv_layers[0]
    c=Counter(); tot=Counter()
    for p in me.polygons:
        n=p.normal; ax=max(range(3),key=lambda i:abs(n[i])); s=n[ax]>0
        pts=[tuple(lay.data[li].uv) for li in p.loop_indices]
        a=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
        tot[(ax,s)]+=1
        if a<0: c[(ax,s)]+=1
    print(name,{k:(c[k],tot[k]) for k in tot}, "polys",len(me.polygons), "loops per poly", set(len(p.loop_indices) for p in me.polygons))
