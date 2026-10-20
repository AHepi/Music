# What this does: finds every node type that can really be added to a shader node tree and to a Geometry Nodes tree in Blender 5.2.2
# (tries to add each one; the ones Blender refuses are left out). Writes addable_nodes.txt next to this file.
import bpy, os
OUT = os.path.dirname(os.path.abspath(__file__))
def subclasses(cls):
    seen = set()
    stack = [cls]
    while stack:
        c = stack.pop()
        for s in c.__subclasses__():
            if s not in seen:
                seen.add(s); stack.append(s)
    return seen
all_ids = []
for n in dir(bpy.types):
    c = getattr(bpy.types, n)
    try:
        if isinstance(c, type) and issubclass(c, bpy.types.Node) and c is not bpy.types.Node:
            all_ids.append(n)
    except Exception:
        pass
all_ids = sorted(all_ids)
lines = []
for tree_type in ('ShaderNodeTree', 'GeometryNodeTree'):
    tree = bpy.data.node_groups.new('probe_' + tree_type, tree_type)
    good = []
    for name in all_ids:
        try:
            node = tree.nodes.new(name)
            good.append((name, node.bl_label))
            tree.nodes.remove(node)
        except Exception:
            pass
    lines.append(f'== {tree_type}: {len(good)} node types can be added')
    for name, label in good:
        lines.append(f'   {name}  "{label}"')
open(os.path.join(OUT, 'addable_nodes.txt'), 'w').write('\n'.join(lines))
print(len(all_ids), 'node classes; written')
