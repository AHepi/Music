# What this does (plain words): builds every box of the slate recipe once and counts which kinds of Blender node each one is made of (the "tools" used),
# and how many nodes each box has. This is a copy of integration/count_tools.py that writes node_counts_after_look_fixes.json next to itself, so the old
# integration/tools_used.json (the numbers the guide first quoted) stays as it was. Made after the look fixes because six new controls changed MOSS and OUTLINE AND SHADOW.
# Run: blender -b --python count_nodes.py
import collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slate_recipe  # noqa
import bpy
tree = slate_recipe.build_node_group({})
result = {}
def walk(group, name):
    kinds = collections.Counter()
    for node in group.nodes:
        label = node.bl_idname.replace('ShaderNode', '')
        if node.bl_idname == 'ShaderNodeMath': label = 'Math ' + node.operation
        elif node.bl_idname == 'ShaderNodeVectorMath': label = 'VectorMath ' + node.operation
        elif node.bl_idname == 'ShaderNodeTexNoise': label = 'Noise ' + node.noise_dimensions
        elif node.bl_idname == 'ShaderNodeTexVoronoi': label = 'Voronoi ' + node.voronoi_dimensions + ' ' + node.feature
        elif node.bl_idname == 'ShaderNodeMapRange': label = 'MapRange ' + node.interpolation_type
        elif node.bl_idname == 'ShaderNodeMix': label = 'Mix ' + node.data_type
        kinds[label] += 1
    result[name] = {'nodes': len(group.nodes), 'kinds': dict(kinds.most_common())}
    for node in group.nodes:
        if node.bl_idname == 'ShaderNodeGroup' and node.node_tree is not None:
            walk(node.node_tree, node.label or node.node_tree.name)
walk(tree, 'SLATE (top)')
json.dump(result, open(os.path.join(HERE, 'node_counts_after_look_fixes.json'), 'w'), indent=1)
for k, v in result.items():
    print(k, v['nodes'], list(v['kinds'].items())[:14])
