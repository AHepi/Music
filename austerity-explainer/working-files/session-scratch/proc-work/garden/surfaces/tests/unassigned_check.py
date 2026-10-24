import sys, bpy
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/kit')
sys.dont_write_bytecode = True
from apply import kit as kit_module
k = kit_module.Kit.load('japanese_courtyard', scene_id='courtyard', strict=False)
print('UNASSIGNED', k.role_map.unassigned)
print('NEVER', sorted(k.role_map.never_objects)[:30])
