import bpy
def dump(mname, deep=True):
    m = bpy.data.materials.get(mname)
    if not m: print("NOMAT", mname); return
    print("=== MAT", mname, "users", m.users, "blend", m.surface_render_method if hasattr(m,'surface_render_method') else '')
    nt = m.node_tree
    for n in nt.nodes:
        ins = []
        for i in n.inputs:
            if i.is_linked: ins.append(f"{i.name}<-{i.links[0].from_node.name}.{i.links[0].from_socket.name}")
            elif hasattr(i,'default_value') and not i.hide and i.enabled:
                v = i.default_value
                try: v = tuple(round(x,3) for x in v)
                except TypeError:
                    v = round(v,3) if isinstance(v,float) else v
                ins.append(f"{i.name}={v}")
        extra=""
        if n.bl_idname=='ShaderNodeValToRGB':
            extra = " RAMP " + str([(round(e.position,3), tuple(round(c,3) for c in e.color)) for e in n.color_ramp.elements])
        if n.bl_idname=='ShaderNodeTexNoise': extra=f" noise {n.noise_dimensions} {n.noise_type}"
        if n.bl_idname=='ShaderNodeGroup': extra=f" GROUP {n.node_tree.name}"
        if n.bl_idname=='ShaderNodeTexImage': extra=f" IMG {n.image.name if n.image else None}"
        print(f"  {n.name} [{n.bl_idname}]{extra} :: " + "; ".join(ins))
for nm in ['Pond water','Life / pond bed','Lily pad','Lotus blossom','Life / lily stem','Life / iris blade','Maple inner mass','GARDEN ground.earth','Pine needles']:
    dump(nm)
