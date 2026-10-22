import bpy, sys
def sockval(s):
    try:
        v=s.default_value
        try: v=tuple(round(x,3) for x in v)
        except TypeError:
            if isinstance(v,float): v=round(v,3)
        return v
    except Exception: return None
def dump(nt, indent="", seen=None, depth=0):
    for n in nt.nodes:
        extra=""
        for a in ("data_type","operation","blend_type","interpolation","projection","attribute_type","attribute_name","space","distance"):
            if hasattr(n,a):
                v=getattr(n,a)
                extra+=" %s=%s"%(a,v)
        if n.bl_idname=='ShaderNodeTexImage' and n.image: extra+=" img=%s cs=%s"%(n.image.name,n.image.colorspace_settings.name)
        if n.bl_idname=='ShaderNodeGroup': extra+=" GROUP=%s"%n.node_tree.name
        print(indent+"NODE %s [%s]%s"%(n.name,n.bl_idname.replace('ShaderNode',''),extra))
        for i in n.inputs:
            if i.is_linked:
                print(indent+"    in %s <- %s"%(i.name,[(lk.from_node.name+"."+lk.from_socket.name) for lk in i.links]))
            else:
                v=sockval(i)
                if v is not None and i.enabled and not i.hide_value: print(indent+"    in %s = %s"%(i.name,v))
mats=sys.argv[sys.argv.index('--')+1:]
for mn in mats:
    m=bpy.data.materials[mn]
    print("=====MAT",mn,"users",m.users, "blend", m.blend_method if hasattr(m,'blend_method') else '')
    dump(m.node_tree)
