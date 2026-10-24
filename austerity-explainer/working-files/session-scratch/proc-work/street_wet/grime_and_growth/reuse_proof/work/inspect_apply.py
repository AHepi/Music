# local, no drawing: applies the kit to the courtyard in memory and prints what the report says
import sys, json, time
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
sys.dont_write_bytecode = True
import bpy
import apply_weathering as aw
args = sys.argv[sys.argv.index('--') + 1:]
look = args[0]; out = args[1]
t = time.time()
w = aw.apply('japanese_courtyard', look, state='dry')
print('APPLY SECONDS', round(time.time() - t, 1))
rep = w.report()
json.dump(rep, open(out, 'w'), indent=1, default=str)
print(json.dumps({k: (v if k != 'skipped' else v) for k, v in rep.items()}, default=str)[:6000])
print('PROBLEMS', w.problems)
print('APPLIED', {k: len(v) for k, v in w.applied.items()})
w.remove()
