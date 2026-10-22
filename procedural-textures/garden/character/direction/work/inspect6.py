import bpy, sys, collections
c=collections.Counter(); bump=0; strengths=[]
def scan(nt, tag):
    for n in nt.nodes:
        c[n.bl_idname]+=1
        if n.bl_idname=='ShaderNodeBump':
            strengths.append(round(n.inputs['Strength'].default_value,2))
        if n.bl_idname=='ShaderNodeGroup' and n.node_tree: pass
for m in bpy.data.materials:
    if m.node_tree: scan(m.node_tree,m.name)
for g in bpy.data.node_groups:
    if g.bl_idname=='ShaderNodeTree': scan(g,g.name)
print("RESULT NormalMap nodes:",c['ShaderNodeNormalMap'],"| Bump nodes:",c['ShaderNodeBump'],"| Displacement nodes:",c['ShaderNodeDisplacement'],"| Image Texture nodes:",c['ShaderNodeTexImage'])
print("RESULT bump strengths:",sorted(collections.Counter(strengths).items()))
mats_with_disp=[m.name for m in bpy.data.materials if m.node_tree and any(n.bl_idname=='ShaderNodeDisplacement' for n in m.node_tree.nodes)]
print("RESULT materials with real displacement output:",len(mats_with_disp), "cycles displacement settings:",[ (m.name,m.displacement_method) for m in bpy.data.materials if m.displacement_method!='BUMP'][:5])
print("RESULT mesh objects:",sum(1 for o in bpy.data.objects if o.type=='MESH'),"with UV:",sum(1 for o in bpy.data.objects if o.type=='MESH' and o.data.uv_layers))
