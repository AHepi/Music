import bpy, bmesh, numpy as np
from mathutils import Vector
for n in ["Hall plaster","Back wall, left","Back wall, right","Right wall behind hall"]:
    o=bpy.data.objects[n]
    vs=sorted([tuple(round(c,3) for c in v.co) for v in o.data.vertices])
    print(n,"mw_ident",o.matrix_world==o.matrix_world.Identity(4) if hasattr(o.matrix_world,'Identity') else '', "verts",vs if len(vs)<=12 else (vs[:3],"...",len(vs)))
    print("   normals",sorted(set((round(p.normal.x),round(p.normal.y),round(p.normal.z)) for p in o.data.polygons)))
for n in ["Back wall, left cap","Back wall, right cap","Right wall behind hall cap"]:
    o=bpy.data.objects[n]
    bm=bmesh.new(); bm.from_mesh(o.data)
    # islands
    seen=set(); isl=[]
    for v in bm.verts:
        if v.index in seen: continue
        stack=[v]; comp=[]
        seen.add(v.index)
        while stack:
            a=stack.pop(); comp.append(a)
            for e in a.link_edges:
                b=e.other_vert(a)
                if b.index not in seen: seen.add(b.index); stack.append(b)
        isl.append(comp)
    print(n,"islands",len(isl),"sizes",sorted(set(len(c) for c in isl)))
    bb=[]
    for c in isl[:3]:
        co=np.array([v.co[:] for v in c]); print("   isl bbox",co.min(0).round(3),co.max(0).round(3),len(c))
    allco=np.array([v.co[:] for v in bm.verts]); print("   total bbox",allco.min(0).round(3),allco.max(0).round(3))
    bm.free()
print("cap attrs",[a.name for a in bpy.data.objects["Back wall, left cap"].data.attributes])
for n in ["Lantern base","Lantern post","Lantern gallery","Lantern firebox","Lantern cap","Lantern finial"]:
    o=bpy.data.objects[n]
    co=np.array([v.co[:] for v in o.data.vertices]); print(n,"local bbox",co.min(0).round(3),co.max(0).round(3),"loc",tuple(round(x,3) for x in o.location),"rot",tuple(round(x,3) for x in o.rotation_euler),"scale",tuple(round(x,3) for x in o.scale), "attrs",[a.name for a in o.data.attributes if not a.name.startswith('.')])
for n in ["Rock 0","Pond edge stone 3","Water basin","Shore stones"]:
    o=bpy.data.objects[n]
    print(n,"loc",tuple(round(x,3) for x in o.location),"rot",tuple(round(x,3) for x in o.rotation_euler),"scale",tuple(round(x,3) for x in o.scale),"attrs",[a.name for a in o.data.attributes if not a.name.startswith('.')], "mods",[m.name for m in o.modifiers])
