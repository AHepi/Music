import bpy, sys, re
out=[]
def p(*a): out.append(" ".join(str(x) for x in a))
p("NODEGROUPS")
for g in bpy.data.node_groups:
    if not g.name.startswith("CT / Anchored chiseled variation."):
        p("  ",g.name, g.bl_idname, len(g.nodes))
p("UV layers per object stem")
seen=set()
for o in bpy.data.objects:
    if o.type!='MESH': continue
    stem=re.sub(r'[\s_.]*\d+$','',o.name)
    if stem in seen: continue
    seen.add(stem)
    p("  ",stem,"uv",[u.name for u in o.data.uv_layers],"attrs",[a.name for a in o.data.attributes if not a.name.startswith('.')][:8],"verts",len(o.data.vertices))
# roof GN materials
r=bpy.data.objects["Hall roof"]
for m in r.modifiers:
    p("ROOF MOD",m.name,m.type, getattr(m,'node_group',None) and m.node_group.name)
    if m.type=='NODES':
        try:
            for k in m.keys():
                p("   input",k,m[k])
        except Exception as e: p("   (no idprops)")
        ng=m.node_group
        p("   nodes",len(ng.nodes),[n.name for n in ng.nodes if n.bl_idname=='GeometryNodeSetMaterial'][:10])
        for n in ng.nodes:
            if n.bl_idname=='GeometryNodeSetMaterial': p("     setmat",n.name,n.inputs['Material'].default_value.name if n.inputs['Material'].default_value else None)
# Pond water inspection: key BSDF inputs
m=bpy.data.materials["Pond water"]
for n in m.node_tree.nodes:
    if n.bl_idname=='ShaderNodeBsdfPrincipled':
        p("POND bsdf",{i.name:(tuple(round(x,3) for x in i.default_value) if hasattr(i.default_value,'__len__') else round(i.default_value,3)) for i in n.inputs if i.name in('Base Color','Roughness','IOR','Transmission Weight','Alpha','Metallic')})
# Plank mat sample: bump strength
m=bpy.data.materials["Astra / planks tone 0"]
for n in m.node_tree.nodes:
    if n.bl_idname=='ShaderNodeBump': p("PLANK bump strength",n.inputs['Strength'].default_value,n.inputs['Distance'].default_value)
    if n.bl_idname=='ShaderNodeGroup': p("PLANK group",n.node_tree.name)
# collections hide status of source objects
open(sys.argv[-1],"w").write("\n".join(out))
