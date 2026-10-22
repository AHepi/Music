# usage: blender -b FILE -P dump_roles.py -- KITDIR SETID SCENEID OUT.json
import sys, json, os
args = sys.argv[sys.argv.index('--')+1:]
kitdir, set_id, scene_id, out = args
sys.path.insert(0, kitdir); sys.dont_write_bytecode = True
import bpy
from apply import kit as kit_module, roles as roles_module
k = kit_module.Kit.load(set_id, scene_id=scene_id, strict=False)
rm = k.role_map
objs = roles_module.describe_scene(None)
data = {
  'objects': {o.name: list(o.materials) for o in objs},
  'primary': rm.primary,
  'material_roles': {m: dict(r) for m, r in sorted(rm.material_roles.items())},
  'members': {r: sorted(v) for r, v in rm.members.items()},
  'unassigned': sorted(rm.unassigned),
  'never_materials': sorted(rm.never_materials),
}
json.dump(data, open(out, 'w'), indent=1, sort_keys=True)
print('DUMPED', out, len(objs), 'objects', len(data['material_roles']), 'materials with a role')
