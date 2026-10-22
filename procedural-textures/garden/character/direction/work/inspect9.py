import bpy, sys, mathutils
def bb(o):
    cs=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
    return tuple(round(min(c[i] for c in cs),2) for i in range(3)), tuple(round(max(c[i] for c in cs),2) for i in range(3))
for n in ("Maple trunk","Maple leaves","Maple inner mass","Pine trunk","Pine pads","Lily pads","Lotus blossoms","Life / iris clumps","Life / pond pebbles","Fallen leaves","Raked gravel court","Lantern base","Water basin","Bamboo stalks","Bamboo fence","Rock 0","Rock 1","Rock 2","Rock 3","Rock 4","Back wall, left","Back wall, right","Right wall behind hall","Life / tufts"):
    o=bpy.data.objects[n]; print("RESULT",n,o.type,bb(o))
# Maple branch count & pine limb count, pads count (separate pieces?)
import bmesh
o=bpy.data.objects["Pine pads"]
bm=bmesh.new(); bm.from_mesh(o.data)
# count loose parts
seen=set(); parts=0
for v in bm.verts:
    if v.index in seen: continue
    parts+=1; stack=[v]
    while stack:
        a=stack.pop()
        if a.index in seen: continue
        seen.add(a.index)
        for e in a.link_edges: stack.append(e.other_vert(a))
print("RESULT pine pad parts",parts)
# lily pads parts
o=bpy.data.objects["Lily pads"]; print("RESULT lily pad centres prop", o.get('life_pad_centres'))
