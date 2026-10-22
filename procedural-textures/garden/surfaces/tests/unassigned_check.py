import sys, bpy
sys.path.insert(0, 'proc-work/garden/surfaces/kit')
sys.dont_write_bytecode = True
from apply import kit as kit_module
k = kit_module.Kit.load('japanese_courtyard', scene_id='courtyard', strict=False)
print('UNASSIGNED', k.role_map.unassigned)
print('NEVER', sorted(k.role_map.never_objects)[:30])
