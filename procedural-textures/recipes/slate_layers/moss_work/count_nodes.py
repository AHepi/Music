# What this does (plain words): counts the nodes inside the MOSS box (and says how many of them are noise or cell textures, the slow kind), so the cost of the layer is known.
# Use: blender -b --python count_nodes.py
import os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'layers')))
import moss
tree = moss.build_group({})
kinds = collections.Counter(n.bl_idname for n in tree.nodes)
print('MOSS nodes:', len(tree.nodes))
for k, v in kinds.most_common(12):
    print(' ', k, v)
slow = sum(v for k, v in kinds.items() if k in ('ShaderNodeTexNoise', 'ShaderNodeTexVoronoi', 'ShaderNodeTexWhiteNoise')) + kinds.get('ShaderNodeGroup', 0)
print('texture nodes (noise, cells, white noise, seamless-noise boxes):', slow)
