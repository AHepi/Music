"""test_run.py - runs the wood builder's own checks on the staged scene (no picture is drawn).
   blender -b --disable-autoexec START.blend --python test_run.py -- OUT.json"""
import sys, os, json, time, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import numpy as np
import bpy
import stage_wood, wood_tests as T

out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(HERE, 'work', 'tests.json')
res = []
def add(r):
    res.append(r)
    print('WOODTEST', r['name'], r['result'], json.dumps({k: v for k, v in r.items() if k not in ('name', 'result')}, default=str)[:3000], flush=True)

before = T.snapshot()
t0 = time.time()
rep = stage_wood.apply({})
ctx = stage_wood.LAST_CTX
bed = None
try:
    bed = stage_wood.make_bed_fn()
except Exception:
    traceback.print_exc()
mid = T.snapshot()
for fn, args in ((T.test9, (ctx, bed)), (T.test10, (ctx,)), (T.test11, (ctx,)), (T.test12, (ctx,))):
    try:
        add(fn(*args))
    except Exception as e:
        traceback.print_exc()
        add(dict(name=fn.__name__, result='ERROR', error=str(e)))
mats = ['G6 wood / plank top', 'G6 wood / plank side', 'G6 wood / plank end grain', 'G6 wood / deck top', 'G6 wood / deck side', 'G6 wood / deck end grain',
        'G6 wood / post timber', 'G6 wood / footing stone', 'Dark timber', 'Beam timber', 'GARDEN timber.post', 'Plinth stone'] + ['CT / Stone painterly surface.%s' % s for s in ('008', '009', '039', '040', '041', '042')]
try:
    add(T.test20_22(mats))
except Exception as e:
    traceback.print_exc(); add(dict(name='test 20', result='ERROR', error=str(e)))
try:
    add(T.uv_hygiene(stage_wood.OWN_OBJECTS + ['G6 wood / bridge posts', 'G6 wood / bridge bearers', 'G6 wood / bridge footings']))
except Exception as e:
    traceback.print_exc(); add(dict(name='test 22', result='ERROR', error=str(e)))
own_objs = set(stage_wood.OWN_OBJECTS)
own_mats = set(stage_wood.OWN_MATS_EXISTING)
try:
    add(T.ownership_diff(before, mid, own_objs, own_mats))
except Exception as e:
    traceback.print_exc(); add(dict(name='test 23', result='ERROR', error=str(e)))
# idempotence: apply a second time and compare
n_obj1 = len(bpy.data.objects); n_mat1 = len([m for m in bpy.data.materials if m.name.startswith('G6 wood / ')]); v1 = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
rep2 = stage_wood.apply({})
n_obj2 = len(bpy.data.objects); n_mat2 = len([m for m in bpy.data.materials if m.name.startswith('G6 wood / ')]); v2 = sum(len(o.data.vertices) for o in bpy.data.objects if o.type == 'MESH')
second = T.snapshot()
same = (n_obj1 == n_obj2 and n_mat1 == n_mat2 and v1 == v2)
d2 = []
for n, d in mid['objects'].items():
    if n in second['objects'] and second['objects'][n] != d:
        d2.append(n)
add(dict(name='test 23b idempotence (apply twice)', result='PASS' if same and not d2 else 'FAIL', objects=[n_obj1, n_obj2], g6_materials=[n_mat1, n_mat2], vertices=[v1, v2], objects_that_differ=d2[:10]))
json.dump(res, open(out, 'w'), indent=1, default=str)
print('TESTS DONE', round(time.time() - t0, 1), 's')
