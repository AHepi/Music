import sys, os, json
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ['WALLS_WORK'] = HERE
from walls import remote_walls
set_ref, scene, cfg, tag = sys.argv[1:5]
res = remote_walls.run_script(set_ref, scene, os.path.join(KIT, 'walls', 'sheet_walls.py'), [set_ref, scene, '{out}', cfg], os.path.join(HERE, '..', 'out'), tag=tag, extra_roots=[cfg])
print(json.dumps(res))
