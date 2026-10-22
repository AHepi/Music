import bpy
def sockval(s):
    try:
        v=s.default_value
        try: v=tuple(round(x,4) for x in v)
        except TypeError:
            if isinstance(v,float): v=round(v,4)
        return v
    except Exception: return None
def dump_group(nt, indent=""):
    for n in nt.nodes:
        extra=""
        for a in ("data_type","operation","domain","mode","transform_space","distribution","input_type","object","node_tree","blend_type"):
            if hasattr(n,a):
                v=getattr(n,a)
                if hasattr(v,'name'): v=v.name
                extra+=" %s=%s"%(a,v)
        print(indent+"NODE %s [%s]%s loc=(%d,%d)"%(n.name,n.bl_idname,extra,n.location.x,n.location.y))
        for i in n.inputs:
            if i.is_linked: 
                l=[ (lk.from_node.name+"."+lk.from_socket.name) for lk in i.links]
                print(indent+"    in %s <- %s"%(i.name,l))
            else:
                v=sockval(i)
                if v is not None and i.enabled: print(indent+"    in %s = %s"%(i.name,v))
for gname in ["CT / Complete two-bank ceramic roof","CT / Roof bank 1 local mechanism","CT / Roof bank 2 local mechanism"]:
    g=bpy.data.node_groups[gname]
    print("=== GROUP",gname, "users",g.users)
    dump_group(g)
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
print("MOD",m.name,m.node_group.name,[ (k,m[k]) for k in m.keys()])
p=bpy.data.objects["CT / Ceramic pan prototype"]
print("PROTO verts")
for v in p.data.vertices: print(tuple(round(x,3) for x in v.co))
for pl in p.data.polygons: print(list(pl.vertices), pl.material_index)
print("proto attrs",[a.name for a in p.data.attributes])
