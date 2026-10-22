import bpy, sys
out=[]
def p(*a): out.append(" ".join(str(x) for x in a))
for c in bpy.data.collections:
    if c.name.startswith(("G4","G5","G1","G2")):
        p("COLL",c.name,[o.name for o in c.objects][:40])
for l in bpy.data.objects:
    if l.type=='LIGHT':
        ll=l.light_linking
        p("LIGHTLINK",l.name,"recv",ll.receiver_collection.name if ll.receiver_collection else None,"blocker",ll.blocker_collection.name if ll.blocker_collection else None, "lightgroup", l.lightgroup)
vl=bpy.context.view_layer
p("lightgroups",[g.name for g in vl.lightgroups])
p("view layers",[v.name for v in bpy.context.scene.view_layers])
# objects with lightgroup set
for o in bpy.data.objects:
    if getattr(o,'lightgroup',''): p("OBJ lightgroup",o.name,o.lightgroup)
# water level facts
for n in ("Pond water","Life / pond bed"):
    o=bpy.data.objects[n]; p(n,"mats",[s.material.name for s in o.material_slots])
# visibility flags of bridge planks
o=bpy.data.objects["Astra / varied planks.003"]
p("visible_camera",o.visible_camera,"cast shadow",o.visible_shadow)
open(sys.argv[-1],"w").write("\n".join(out))
