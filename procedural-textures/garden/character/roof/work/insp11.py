import bpy
for n in ("CT / Ceramic pan prototype","Hall roof","Hall plaster","Rock 0","Lantern post","Back wall, left cap"):
    o=bpy.data.objects[n]
    print(n,{k:(round(o[k],3) if isinstance(o[k],float) else o[k]) for k in o.keys() if k.startswith('wk_')})
