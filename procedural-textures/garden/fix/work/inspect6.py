import bpy
for nm in ['Astra / moss tone 1','Astra / pebbles tone 0']:
    m = bpy.data.materials[nm]
    print('MAT', nm)
    for n in m.node_tree.nodes:
        if n.bl_idname=='ShaderNodeGroup' and n.node_tree and n.node_tree.name.startswith('WK'):
            print('  ', n.name, n.node_tree.name)
            for s in n.inputs:
                if not s.is_linked and hasattr(s,'default_value'):
                    try: v = tuple(round(x,3) for x in s.default_value)
                    except TypeError: v = round(float(s.default_value),3) if isinstance(s.default_value,(int,float)) else s.default_value
                    print('       ', s.name, v)
