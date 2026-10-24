import sys, bpy, bmesh
sys.dont_write_bytecode = True
names = ["headframe_lattice","winding_wheel_left","winding_wheel_right","engine_house_trim","road_setts" ]
res = {}
for n in names:
    o = bpy.data.objects.get(n)
    if o is None or o.type != 'MESH':
        res[n] = "missing"; continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    # loose parts by BFS over faces' verts
    seen=set(); parts=[]
    verts_to_faces={}
    for f in bm.faces:
        for v in f.verts: verts_to_faces.setdefault(v.index,[]).append(f)
    fseen=set()
    for f0 in bm.faces:
        if f0.index in fseen: continue
        stack=[f0]; fseen.add(f0.index); comp=[]
        while stack:
            f=stack.pop(); comp.append(f)
            for v in f.verts:
                for g in verts_to_faces[v.index]:
                    if g.index not in fseen: fseen.add(g.index); stack.append(g)
        parts.append(comp)
    neg=0; pos=0; open_=0
    for comp in parts:
        # closed? every edge has 2 faces within comp
        ec={}
        for f in comp:
            for e in f.edges: ec[e.index]=ec.get(e.index,0)+1
        if any(c!=2 for c in ec.values()): open_+=1; continue
        vol=0.0
        for f in comp:
            vs=[v.co for v in f.verts]
            for i in range(1,len(vs)-1):
                vol+=vs[0].dot(vs[i].cross(vs[i+1]))/6.0
        if vol<0: neg+=1
        else: pos+=1
    res[n]=dict(parts=len(parts), closed_outward=pos, closed_inward=neg, open=open_, mats=[m.name+':'+str(getattr(m,'use_backface_culling',None)) for m in o.data.materials][:5])
    bm.free()
bc=[m.name for m in bpy.data.materials if m.use_backface_culling]
res['materials_with_backface_culling']=bc
res['n_materials']=len(bpy.data.materials)
print("RESULT", res)
