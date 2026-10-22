# Idempotency: apply the stage twice (and a third time in the other look) and compare object / material / node group counts and key numbers.
import bpy, sys, json
HERE = 'proc-work/garden/life'
sys.path.insert(0, HERE)
import stage_life
def counts():
    return {'objects': len(bpy.data.objects), 'meshes': len(bpy.data.meshes), 'materials': len(bpy.data.materials), 'node_groups': len(bpy.data.node_groups),
            'collections': len(bpy.data.collections), 'curves': len(bpy.data.curves)}
c0 = counts()
r1 = stage_life.apply({'look': 'real'}); c1 = counts()
r2 = stage_life.apply({'look': 'real'}); c2 = counts()
r3 = stage_life.apply({'look': 'painted'}); c3 = counts()
r4 = stage_life.apply({'look': 'real'}); c4 = counts()
same = lambda a, b: {k: (a[k], b[k]) for k in a if a[k] != b[k]}
res = {'start': c0, 'real1': c1, 'real2_minus_real1': same(c1, c2), 'painted_minus_real': same(c2, c3), 'real_again_minus_real1': same(c1, c4),
       'maple_leaves_equal': r1['numbers']['maple_leaves'] == r2['numbers']['maple_leaves'] == r4['numbers']['maple_leaves'],
       'scatter_equal': [r1['numbers'][k] == r2['numbers'][k] == r4['numbers'][k] for k in ('scatter_moss', 'scatter_tuft', 'scatter_pebble')],
       'objects_added_equal': r1['objects_added'] == r2['objects_added'] == r4['objects_added']}
print('RERUN', json.dumps(res))
json.dump(res, open(HERE + '/out/rerun_test.json', 'w'), indent=1)
