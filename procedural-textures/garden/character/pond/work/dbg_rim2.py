import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond')
import bpy, numpy as np
import g6p_common as C
pw=bpy.data.objects['Pond water']; P=np.array([v.co[:] for v in pw.data.vertices]); d=np.array([a.value for a in pw.data.attributes['depth'].data])
wet=P[d>0.02][:,:2]
print("wet water verts", len(wet))
for nm in C.POND_STONES:
    ob=bpy.data.objects[nm]
    me=ob.data; co=np.array([ (ob.matrix_world@v.co)[:] for v in me.vertices])
    # vertices near the waterline (z between -0.2 and -0.05)
    sel=co[(co[:,2]>-0.2)&(co[:,2]<-0.05)][:,:2]
    if len(sel)==0: print(nm,"no verts near waterline"); continue
    dmin=np.min(np.hypot(sel[:,None,0]-wet[None,::3,0], sel[:,None,1]-wet[None,::3,1]))
    print("%-18s waterline verts %5d  min dist to wet water %.3f"%(nm,len(sel),dmin))
