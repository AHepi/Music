# driver: draws jobs on the rented machine for the walls layers. usage: python3 drive.py TAG JOBSPEC.json [scene]
import sys, os, json, time
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
os.environ['WALLS_WORK'] = os.path.dirname(os.path.abspath(__file__))
from walls import remote_walls
tag, spec_path = sys.argv[1], sys.argv[2]
scene = sys.argv[3] if len(sys.argv) > 3 else 'street'
setid = sys.argv[4] if len(sys.argv) > 4 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tuned', 'street_set.json')
spec = json.load(open(spec_path))
jobs, cams = (spec['jobs'], spec.get('extra_cameras')) if isinstance(spec, dict) else (spec, None)
OUT = 'proc-work/street_wet/grime_and_growth/walls/out'
t = time.time()
res = remote_walls.run(setid, scene, jobs, OUT, tag=tag, extra_cameras=cams, extra_roots=[os.path.abspath(os.path.join(os.path.dirname(__file__), 'tuned'))])
print(json.dumps(res), round(time.time() - t, 1), 's')
