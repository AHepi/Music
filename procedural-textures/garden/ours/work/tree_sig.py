# usage: blender -b -P tree_sig.py -- KITDIR SETID SCENEID OUT.json [SETFILE_OVERRIDE]
import sys, json, collections
args = sys.argv[sys.argv.index('--')+1:]
kitdir, set_id, scene_id, out = args[:4]
setref = args[4] if len(args) > 4 else set_id
sys.path.insert(0, kitdir); sys.dont_write_bytecode = True
import bpy
from apply import kit as km, dials
from harness import layers as layers_module
k = km.Kit.load(setref, scene_id=scene_id, strict=False)
if hasattr(dials, 'note_role_dials'):
    dials.note_role_dials(k.settings)
found, errors = layers_module.register_builders(k)
res = {}
def sig(tree):
    c = collections.Counter()
    for n in tree.nodes:
        key = n.bl_idname
        for attr in ('operation', 'blend_type', 'data_type', 'noise_type', 'feature', 'interpolation_type', 'attribute_type'):
            if hasattr(n, attr):
                key += '|' + str(getattr(n, attr))
        if n.bl_idname == 'ShaderNodeAttribute':
            key += '|' + n.attribute_name
        c[key] += 1
    return {'nodes': len(tree.nodes), 'links': len(tree.links), 'kinds': dict(sorted(c.items()))}
for key in sorted(k.registry):
    if key in ('growth',): continue
    try:
        tree = k.registry[key].builder(key)
        res[key] = sig(tree)
    except Exception as e:
        res[key] = {'error': repr(e)[:200]}
json.dump(res, open(out, 'w'), indent=1, sort_keys=True)
print('SIG', out, {key: (v.get('nodes'), v.get('links')) for key, v in res.items()})
print('ERRORS', errors)
