import bpy, sys, math, numpy as np, mathutils
for n in ["Astra / varied planks.003","Astra / varied planks.004","Astra / varied planks.005","Astra / varied planks.006","Astra / varied planks.007"]:
    o=bpy.data.objects[n]
    P=np.array([(o.matrix_world@v.co)[:] for v in o.data.vertices])
    xy=P[:,:2]; c=xy.mean(0); u,s,vt=np.linalg.svd(xy-c,full_matrices=False)
    ax=vt[0]; ang=math.degrees(math.atan2(ax[1],ax[0]))
    proj=(xy-c)@vt.T
    ext=proj.max(0)-proj.min(0)
    top=P[:,2].max(); bot=P[:,2].min()
    # board count by connected components via vertex grouping: count unique x along main axis clusters
    print("RESULT",n,"centre",tuple(round(v,2) for v in c),"main axis angle deg",round(ang,1),"extent along/across",tuple(round(v,2) for v in ext),"z",round(bot,3),round(top,3))
o=bpy.data.objects["Bridge stringers"]
P=np.array([(o.matrix_world@v.co)[:] for v in o.data.vertices])
for i in range(0,len(P),8):
    b=P[i:i+8]; print("RESULT stringer",i//8,"from",tuple(np.round(b[:4].mean(0),2)),"to",tuple(np.round(b[4:].mean(0),2)),"z",round(b[:,2].min(),2),round(b[:,2].max(),2))
for n in ["Bridge pier 0","Bridge pier 1","Bridge pier 2","Bridge pier 3"]:
    o=bpy.data.objects[n]; P=np.array([(o.matrix_world@v.co)[:] for v in o.data.vertices]); print("RESULT",n,"centre",tuple(np.round(P.mean(0),2)),"size",tuple(np.round(P.max(0)-P.min(0),2)))
# deck runs
for n in ["Astra / varied planks","Astra / varied planks.001","Astra / varied planks.002"]:
    o=bpy.data.objects[n]; P=np.array([(o.matrix_world@v.co)[:] for v in o.data.vertices]); print("RESULT deck",n,"bbox",tuple(np.round(P.min(0),2)),tuple(np.round(P.max(0),2)),"verts",len(P))
# plinth
o=bpy.data.objects["Stone plinth"]; P=np.array([(o.matrix_world@v.co)[:] for v in o.data.vertices]); print("RESULT plinth",np.round(P,2).tolist())
# ground height at the bridge nodes by raycast
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
g=bpy.data.objects["Astra / Courtyard receiving ground"]
for name,(x,y) in {"N3 west bank":(-5.95,1.55),"N2":(-3.9,0.15),"N1":(-2.0,1.0),"N0 east bank":(-0.55,-0.6),"ground west of N3":(-6.8,1.9),"ground east of N0":(0.1,-1.1)}.items():
    hit=bpy.context.scene.ray_cast(dg,mathutils.Vector((x,y,3.0)),mathutils.Vector((0,0,-1)))
    print("RESULT ray",name,(x,y),"hit",hit[0],hit[4].name if hit[4] else None,round(hit[1].z,3) if hit[0] else None)
