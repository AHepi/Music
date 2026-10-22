import sys, time
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof')
import numpy as np, bpy
import r_maps
t=time.time()
res=r_maps.all_normals({'glaze':512,'plaster':512,'stone':512,'moss':512})
for k,(n,s) in res.items():
    rgb=n*0.5+0.5
    print(k,"strength",round(s,3),"mean rgb",rgb.reshape(-1,3).mean(0).round(3),"min nz",n[...,2].min().round(3), "t",round(time.time()-t,1))
b=r_maps.plaster_blotch('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof/maps/sw_plaster.jpg',256)
print("blotch",b.shape,b.mean((0,1)).round(3),b.min().round(3),b.max().round(3))
