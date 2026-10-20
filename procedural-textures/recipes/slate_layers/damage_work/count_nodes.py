# What this does (plain words): counts the nodes in the DAMAGE box (and in the other boxes), split by kind, so that the cost of the layer can be understood: every node is evaluated for every sample of every dot.
import collections, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', '..', 'lib')))
import bake_harness as bh
import bpy
recipe = bh.load_recipe(os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'))
extra = {}
for a in sys.argv[sys.argv.index('--') + 1:]:
    k, v = a.split('=')
    extra[k] = float(v)
group = recipe.build_node_group(extra)
for g in bpy.data.node_groups:
    if g.name.split('.')[0] in ('DAMAGE', 'LAYOUT', 'COLOUR AND FADE', 'MOSS', 'OUTLINE AND SHADOW', 'COMBINE'):
        kinds = collections.Counter(n.bl_idname.replace('ShaderNode', '') for n in g.nodes)
        print(g.name, len(g.nodes), dict(kinds.most_common(8)))
