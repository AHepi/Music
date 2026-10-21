# What this does (plain words): opens the saved courtyard scene and only LISTS how the add-on's stone/ceramic material and its shader group are built:
# which boxes, which wires, which inputs a layer could use. It saves nothing.
# Run: blender -b --disable-autoexec FILE --python c2_addon_groups.py -- OUT.txt
import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
L = []
def sock_val(s):
    try:
        v = s.default_value
        return [round(float(x), 3) for x in v] if hasattr(v, '__len__') else round(float(v), 3)
    except Exception:
        return None
def dump_tree(tree, indent=0, seen=None, depth=0):
    seen = seen if seen is not None else set()
    pad = '  ' * indent
    L.append(f'{pad}TREE {tree.name}  ({type(tree).__name__}, users={tree.users})')
    if hasattr(tree, 'interface'):
        for it in tree.interface.items_tree:
            if it.item_type == 'SOCKET':
                dv = getattr(it, 'default_value', None)
                try: dv = [round(float(x), 3) for x in dv] if hasattr(dv, '__len__') else round(float(dv), 3)
                except Exception: pass
                L.append(f'{pad}  iface {it.in_out:6s} {it.socket_type:22s} "{it.name}" default={dv}')
    for n in tree.nodes:
        extra = ''
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree: extra = f' [group {n.node_tree.name}]'
        if n.bl_idname == 'ShaderNodeTexImage' and n.image: extra = f' [image {n.image.name}]'
        if n.bl_idname == 'ShaderNodeAttribute': extra = f' [attr {n.attribute_name} {n.attribute_type}]'
        L.append(f'{pad}  node {n.bl_idname.replace("ShaderNode","")}:{n.name}{extra}')
        for i in n.inputs:
            if i.is_linked:
                lk = i.links[0]; L.append(f'{pad}      in "{i.name}" <- {lk.from_node.name}.{lk.from_socket.name}')
            elif n.bl_idname in ('ShaderNodeBsdfPrincipled', 'ShaderNodeGroup', 'ShaderNodeMapping', 'ShaderNodeBump', 'ShaderNodeTexNoise', 'ShaderNodeValToRGB', 'ShaderNodeMapRange', 'ShaderNodeMix', 'ShaderNodeMath'):
                v = sock_val(i)
                if v is not None and i.enabled: L.append(f'{pad}      in "{i.name}" = {v}')
    for n in tree.nodes:
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree and n.node_tree.name not in seen and depth < 3:
            seen.add(n.node_tree.name); dump_tree(n.node_tree, indent + 1, seen, depth + 1)
names = ['CT / Stone painterly surface', 'CT / Stone painterly surface.001', 'CT / Ceramic painterly surface', 'CT / Ceramic ridge host-local surface', 'Astra / varied planks']
for nm in names:
    m = bpy.data.materials.get(nm)
    if m and m.node_tree:
        L.append('=' * 100); L.append(f'MATERIAL {nm}  users={m.users}  props={ {k: str(m[k])[:60] for k in m.keys()} }')
        dump_tree(m.node_tree, 0, set())
# all FOUNDRY / CT node groups: names and users
L.append('=' * 100); L.append('ALL NODE GROUPS (name, kind, users)')
for g in bpy.data.node_groups:
    L.append(f'{g.name:55s} {type(g).__name__:14s} users={g.users} nodes={len(g.nodes)}')
open(out, 'w').write('\n'.join(L))
