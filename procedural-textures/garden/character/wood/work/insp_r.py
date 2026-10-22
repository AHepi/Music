import bpy, mathutils, numpy as np
dg = bpy.context.evaluated_depsgraph_get()
names = ["Life / pond bed", "Astra / Courtyard receiving ground", "Life / pond pebbles"]
def cast(o, x, y):
    ev = o.evaluated_get(dg)
    mw = ev.matrix_world; inv = mw.inverted()
    org = inv @ mathutils.Vector((x, y, 2.0)); d = (inv.to_3x3() @ mathutils.Vector((0,0,-1))).normalized()
    ok, loc, nrm, idx = ev.ray_cast(org, d)
    return (mw @ loc).z if ok else None
for (x,y,tag) in [(-5.95,1.55,"N3"),(-3.9,0.15,"N2"),(-2.0,1.0,"N1"),(-0.55,-0.6,"N0"),(-6.3,1.8,"W bank beyond"),(-0.2,-0.9,"E bank beyond"),(-5.2,1.1,"arm0 m"),(-4.9,0.9,"arm0 m2"),(-2.9,0.55,"arm1 m"),(-1.3,0.2,"arm2 m"),(-3.9,-0.45,"N2 -0.6 side"),(-3.9,0.75,"N2 +0.6 side"),(-2.0,0.4,"N1 side"),(-2.0,1.6,"N1 other")]:
    print("CAST", tag, (x,y), {n[:14]: (None if (r:=cast(bpy.data.objects[n],x,y)) is None else round(r,3)) for n in names})
for n in names:
    o = bpy.data.objects[n]; print("OBJ", n, "verts", len(o.data.vertices), "mats", [m.name for m in o.data.materials], "hide", o.hide_render)
w = bpy.data.objects["Pond water"]; print("WATER", w.location[:], [m.name for m in w.data.materials])
# materials of water, bed
for mn in ["Pond water", "Life / pond bed"]:
    m = bpy.data.materials.get(mn); 
    if m: print("MATN", mn, [(n.name, n.bl_idname) for n in m.node_tree.nodes][:30])
# hall posts boxes
import itertools
for oname in ["Hall posts","Hall beams","Eave soffit","Stone plinth","Gravel timber edge"]:
    o = bpy.data.objects[oname]; me = o.data
    # connected components by edge adjacency
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me)
    seen=set(); comps=[]
    for v in bm.verts:
        if v.index in seen: continue
        stack=[v]; comp=[]
        while stack:
            a=stack.pop()
            if a.index in seen: continue
            seen.add(a.index); comp.append(a)
            for e in a.link_edges: stack.append(e.other_vert(a))
        comps.append(comp)
    print("COMPS", oname, len(comps))
    for c in comps[:30]:
        P=np.array([v.co[:] for v in c]); print("   box", len(c), np.round(P.min(0),3).tolist(), np.round(P.max(0),3).tolist())
    bm.free()
