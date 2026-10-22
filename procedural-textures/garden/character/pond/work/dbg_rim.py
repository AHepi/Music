import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond')
import bpy, numpy as np
import g6p_common as C, g6p_water as W
class X: pass
ctx=X(); ctx.ground=C.Ground(); ctx.rng_rim=np.random.default_rng(1)
rng=np.random.default_rng(2)
for i,nm in enumerate(C.POND_STONES):
    ob=bpy.data.objects[nm]
    dg=bpy.context.evaluated_depsgraph_get(); eo=ob.evaluated_get(dg); me=eo.to_mesh()
    n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); P=co.reshape(-1,3)
    mw=np.array(eo.matrix_world); P=P@mw[:3,:3].T+mw[:3,3]
    zmin,zmax=P[:,2].min(),P[:,2].max()
    # ground z at stone centre
    cx,cy=P[:,0].mean(),P[:,1].mean()
    res=W.stone_contour_rim(ob,ctx,rng)
    print(nm,"z %.2f..%.2f"%(zmin,zmax),"centre (%.2f,%.2f) ground z %.2f pond_r %.2f"%(cx,cy,ctx.ground.z(cx,cy),C.pond_radius(cx,cy)),"rim" if res else "NO RIM", ob.matrix_world.translation[:])
    eo.to_mesh_clear()
