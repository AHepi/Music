import bpy, sys
def short(m):
    nt=m.node_tree
    print("=====MAT",m.name,"users",m.users,"nodes",len(nt.nodes))
    for n in nt.nodes:
        ex=""
        if n.bl_idname=='ShaderNodeGroup': ex=" GROUP="+n.node_tree.name
        if n.bl_idname=='ShaderNodeTexImage' and n.image: ex=" IMG="+n.image.name
        if n.bl_idname=='ShaderNodeBump':
            ex=" strength=%s dist=%s"%(n.inputs['Strength'].default_value,n.inputs['Distance'].default_value)
            ex+=" Height<-%s Normal<-%s"%([l.from_node.name for l in n.inputs['Height'].links],[l.from_node.name for l in n.inputs['Normal'].links])
        if n.bl_idname=='ShaderNodeBsdfPrincipled':
            ex=" "+", ".join("%s<-%s"%(i.name,[l.from_node.name+'.'+l.from_socket.name for l in i.links]) for i in n.inputs if i.is_linked)
            ex+=" | base=%s rough=%s"%(tuple(round(x,3) for x in n.inputs['Base Color'].default_value),round(n.inputs['Roughness'].default_value,2))
            ex+=" emis=%s %s"%(tuple(round(x,3) for x in n.inputs['Emission Color'].default_value),n.inputs['Emission Strength'].default_value)
        if n.bl_idname=='ShaderNodeEmission':
            ex=" color=%s str=%s"%(tuple(round(x,3) for x in n.inputs['Color'].default_value),n.inputs['Strength'].default_value)
        print("  %s [%s]%s"%(n.name,n.bl_idname.replace('ShaderNode',''),ex))
for mn in sys.argv[sys.argv.index('--')+1:]:
    short(bpy.data.materials[mn])
p=bpy.data.objects["CT / Ceramic pan prototype"]
print("PROTO")
for v in p.data.vertices: print(tuple(round(x,3) for x in v.co))
for pl in p.data.polygons: print(list(pl.vertices), pl.material_index, round(pl.normal.z,2))
print("proto attrs",[a.name for a in p.data.attributes])
print("proto rot",p.rotation_euler,p.scale,p.parent)
