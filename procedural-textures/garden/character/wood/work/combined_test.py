import sys, os, time, traceback, json
ORDER = sys.argv[sys.argv.index('--') + 1]
W = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/wood'
R = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/roof'
sys.path.insert(0, W); sys.path.insert(1, R)
sys.dont_write_bytecode = True
import bpy
import wood_tests as T
res = {'order': ORDER}
def run(name):
    t = time.time()
    try:
        if name == 'wood':
            import stage_wood
            rep = stage_wood.apply({'cameras': False})
        else:
            import stage_roof
            rep = stage_roof.apply({})
        res[name] = 'ok %.1fs' % (time.time() - t)
    except Exception as e:
        traceback.print_exc()
        res[name] = 'ERROR ' + str(e)[:300]
before = T.snapshot()
for n in ORDER.split('+'):
    run(n)
after = T.snapshot()
names = [o.name for o in bpy.data.objects]
res['objects'] = len(names); res['duplicate_names'] = len(names) - len(set(names))
res['wood_objects_after'] = len([n for n in names if n.startswith('G6 wood')])
print('COMBINED', json.dumps(res))
