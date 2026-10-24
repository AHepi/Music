import bpy, sys, math, json
import numpy as np
HERE='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life'
sys.path.insert(0,HERE)
import stage_life as SL
for look in ('real','painted'):
    st=SL.Stage({'look':look}); SL._STAGE_REF['st']=st
    SL.apply({'look':look})
    sc=SL.scene_context(st); gx0,gy0,gx1,gy1=sc['gravel']
    V=SL.world_vertices(bpy.data.objects['Fallen leaves'])
    # leaves are separate islands of equal vertex count (leaf unit): group by 1 leaf = n verts
    nv=len(SL.leaf_mesh_arrays(look,0,7)[0])
    cen=V.reshape(-1,nv,3).mean(axis=1)
    mx=bpy.data.objects['Maple trunk'].data.splines[0].points[0].co
    under=np.hypot(cen[:,0]-(mx.x+1.7),cen[:,1]-(mx.y-0.3))<3.0
    ingr=((cen[:,0]>gx0)&(cen[:,0]<gx1)&(cen[:,1]>gy0)&(cen[:,1]<gy1))
    onw=np.array([c[2] for c in cen])<=SL.WATER_Z+0.02
    gap=[]
    for c in cen:
        gz=max(st.ground_z(c[0],c[1]),SL.WATER_Z)
        gap.append(c[2]-gz)
    wid=[(V.reshape(-1,nv,3)[i][:,0].max()-V.reshape(-1,nv,3)[i][:,0].min()) for i in range(len(cen))]
    print('LITTER',look,json.dumps({'leaves':len(cen),'under_maple_within_3m':int(under.sum()),'inside_gravel_court':int(ingr.sum()),'on_water':int(onw.sum()),
          'height_over_ground_mm_min_max':[round(min(gap)*1000,1),round(max(gap)*1000,1)],'width_cm_median':round(float(np.median(wid))*100,1)}))
    break
