# Integrator: runs harness/test_weathering_entry.py on a scene file on the rented machine.   python3 -I run_entry_tests.py SCENE_ID  (street | lockout | courtyard)
import json, os, sys
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from apply import settings as settings_module
from harness import remote
W = os.path.dirname(os.path.abspath(__file__))
which = sys.argv[1]
table = {
    'street': ('pit_village_street', 'sooty_1926', 'street', 'main', 'A', 270, 480, 8),
    'lockout': ('pit_village_street', 'sooty_1926', 'lockout', 'lockout', 'B', 270, 480, 8),
    'courtyard': ('japanese_courtyard', 'mossy_courtyard_kept', 'courtyard', 'photo', 'A', 600, 400, 8),
}
set_id, look, scene_id, camera, light, w, h, samples = table[which]
settings = settings_module.load_set(set_id)
scene = next(s for s in settings.scenes if s['id'] == scene_id)
out = os.path.join(W, 'entry_tests', which)
os.makedirs(out, exist_ok=True)
remote_out = f'/workspace/wk_out/int_entry_{which}'
r = remote.run_script(scene['file'], os.path.join(KIT, 'harness', 'test_weathering_entry.py'), [set_id, look, '{out}/entry_test.json', camera, light, str(w), str(h), str(samples)], remote_out, out)
print(which, r)
