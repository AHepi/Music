import bpy, numpy as np
for nm in ('Bamboo stalks','Bamboo leaves','Bamboo fence','Basin bamboo spout','Basin ladle'):
    ob=bpy.data.objects[nm]; me=ob.data
    n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    nl=len(me.loops); vi=np.empty(nl,np.int32); me.loops.foreach_get('vertex_index',vi)
    polys=[(p.loop_start,p.loop_total) for p in me.polygons]
    parent=list(range(n))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for ls,lt in polys:
        v=vi[ls:ls+lt]
        for k in range(1,lt):
            ra,rb=find(v[0]),find(v[k])
            if ra!=rb: parent[rb]=ra
    roots=np.array([find(i) for i in range(n)])
    u,cnt=np.unique(roots,return_counts=True)
    print(nm,"verts",n,"faces",len(polys),"components",len(u),"tri/quad counts",np.unique([lt for _,lt in polys],return_counts=True), "mats",[m.name for m in me.materials])
    if nm in ('Bamboo stalks','Bamboo fence'):
        for r,c in list(zip(u,cnt))[:6]:
            P=co[roots==r]; ext=P.max(0)-P.min(0)
            print("   comp verts",c,"extent",ext.round(3),"min",P.min(0).round(2))
