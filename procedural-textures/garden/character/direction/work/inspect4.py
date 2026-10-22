import bpy, sys
out=[]
def p(*a): out.append(" ".join(str(x) for x in a))
r=bpy.data.objects["Hall roof"]
for m in r.modifiers:
    ng=m.node_group
    p("MOD",m.name,ng.name)
    for it in ng.interface.items_tree:
        if it.item_type=='SOCKET':
            key=it.identifier
            try: val=m[key]
            except Exception: val=None
            try: val=tuple(val)
            except Exception: pass
            p("   ",it.in_out,it.name,it.socket_type,"=",val)
    for n in ng.nodes:
        p("   node",n.name,n.bl_idname, getattr(n,'node_tree',None) and n.node_tree.name)
for gname in ("CT / Roof bank 1 local mechanism",):
    g=bpy.data.node_groups[gname]
    mats=[]
    for n in g.nodes:
        if n.bl_idname=='GeometryNodeSetMaterial':
            mm=n.inputs['Material'].default_value
            mats.append(mm.name if mm else None)
        if n.bl_idname=='GeometryNodeGroup': pass
    p("BANK1 setmats",mats)
    p("BANK1 node types",sorted({n.bl_idname.replace('GeometryNode','') for n in g.nodes}))
    for it in g.interface.items_tree:
        if it.item_type=='SOCKET' and it.in_out=='INPUT': p("   in",it.name,it.socket_type)
# Count roof instances
dg=bpy.context.evaluated_depsgraph_get()
ev=r.evaluated_get(dg)
me=ev.to_mesh()
p("ROOF EVAL verts",len(me.vertices),"faces",len(me.polygons), "attrs",[a.name for a in me.attributes][:12], "uv", [u.name for u in me.uv_layers])
# instance count
n=0
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original==r: n+=1
p("ROOF instances (depsgraph)",n)
open(sys.argv[-1],"w").write("\n".join(out))
