import sys
sys.path.insert(0, sys.argv[sys.argv.index('--')+1]); sys.dont_write_bytecode=True
import bpy
from apply import kit as km
k = km.Kit.load('japanese_courtyard', scene_id='courtyard', strict=False)
v = k.validation
print('VAL errors', len(v.errors)); [print('  E', e[:300]) for e in v.errors]
print('VAL warnings', len(v.warnings)); [print('  W', e[:200]) for e in v.warnings]
