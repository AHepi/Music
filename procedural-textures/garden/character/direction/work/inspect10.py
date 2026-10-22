import bpy, sys, mathutils, numpy as np
g=bpy.data.objects["Astra / Courtyard receiving ground"]; bed=bpy.data.objects["Life / pond bed"]; peb=bpy.data.objects["Life / pond pebbles"]; wat=bpy.data.objects["Pond water"]
def zhit(o,x,y):
    inv=o.matrix_world.inverted()
    org=inv@mathutils.Vector((x,y,3)); d=(inv.to_3x3()@mathutils.Vector((0,0,-1))).normalized()
    ok,loc,n,i=o.ray_cast(org,d)
    return (o.matrix_world@loc).z if ok else None
# water outline: vertices boundary
P=np.array([(wat.matrix_world@v.co)[:2] for v in wat.data.vertices])
print("RESULT water xy range",P.min(0).round(2),P.max(0).round(2))
# depth attribute stats
att=wat.data.attributes.get('depth')
if att:
    d=np.array([a.value for a in att.data]); print("RESULT depth attr min/max/mean",d.min().round(3),d.max().round(3),d.mean().round(3))
rows=[]
for y in np.arange(-1.2,3.2,0.5):
    row=[]
    for x in np.arange(-5.6,0.3,0.6):
        zg=zhit(g,x,y); zb=zhit(bed,x,y)
        row.append("%s/%s"%(("%.2f"%zg) if zg is not None else " -- ",("%.2f"%zb) if zb is not None else " -- "))
    print("RESULT y=%.1f"%y," ".join(row))
print("RESULT columns x=",[round(x,1) for x in np.arange(-5.6,0.3,0.6)], "(ground z / bed z)")
