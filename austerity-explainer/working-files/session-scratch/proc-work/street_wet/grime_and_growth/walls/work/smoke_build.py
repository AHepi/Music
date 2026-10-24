# local smoke test: builds the walls layers on the street scene and checks wiring (no picture)
import sys, os, json, time, traceback
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
import bpy
from apply import kit as kit_module
from masks import bus as bus_module
from walls import apply_walls, walls_common
args = sys.argv[sys.argv.index('--') + 1:]
set_id, scene_id = args[0], args[1]
layers = args[2].split(',') if len(args) > 2 else None
k = kit_module.Kit.load(set_id, scene_id=scene_id, strict=False)
bus_module.attach(k)
print('registered', apply_walls.register(k))
k.prepare()
t = time.time()
res = k.apply(layers=layers or apply_walls.keys())
print('applied', {a: len(b) for a, b in res.items()}, round(time.time() - t, 2))
print('verify', k.verify()[:5])
for key in (layers or apply_walls.keys()):
    tree = k.registry[key].tree
    print(key, 'nodes/heavy', walls_common.count_nodes(tree), 'forbidden', walls_common.forbidden_nodes(tree))
k.remove()
print('SMOKE OK')
