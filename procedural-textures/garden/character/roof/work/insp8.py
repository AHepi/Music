import bpy
p=bpy.data.objects["CT / Ceramic pan prototype"]
for a in p.data.attributes: print("ATTR",a.name,a.domain,a.data_type)
rest=p.data.attributes["CT_rest"]
print([tuple(round(x,3) for x in d.vector) for d in rest.data][:6])
for m in bpy.data.materials:
    if m.name.startswith("CT / Ceramic"): print("MAT",m.name,"users",m.users,[ (u.name) for u in bpy.data.objects if m.name in [s.material.name for s in u.material_slots if s.material]])
def scan(nt,path):
    for n in nt.nodes:
        if n.bl_idname in("ShaderNodeAttribute",):
            print(path,"ATTRNODE",n.name,n.attribute_type,n.attribute_name)
        if n.bl_idname=="ShaderNodeGroup" and n.node_tree: 
            if n.node_tree.name not in seen:
                seen.add(n.node_tree.name); scan(n.node_tree,path+">"+n.node_tree.name)
seen=set()
for mn in ("CT / Ceramic painterly surface","Plaster wall","CT / Stone painterly surface.025"):
    scan(bpy.data.materials[mn].node_tree,mn)
# which objects use which of my materials
mine=["Plaster wall","GARDEN wall.garden","Wall cap tile","GARDEN stone.lantern","GARDEN stone.rock","CT / Timber painterly surface","CT / Ceramic ridge host-local surface"]
for mn in mine:
    print("USERS",mn,[o.name for o in bpy.data.objects if any(s.material and s.material.name==mn for s in o.material_slots)])
# collections
for c in bpy.data.collections: print("COLL",c.name,len(c.objects), [ch.name for ch in c.children][:3])
print("G6 exist?", [c.name for c in bpy.data.collections if c.name.startswith("G6")])
# view layer lightgroups
vl=bpy.context.view_layer
print("lightgroups",[lg.name for lg in vl.lightgroups])
for n in ("Hall roof","Rock 0","Lantern post"):
    o=bpy.data.objects[n]; print(n,"lightgroup",o.lightgroup, "visible_shadow",o.visible_shadow, [k for k in o.keys()])
print("images",[(i.name,i.size[:],i.colorspace_settings.name) for i in bpy.data.images][:40])
