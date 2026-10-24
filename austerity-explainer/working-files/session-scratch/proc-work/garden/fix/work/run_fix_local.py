import bpy, sys, os, time, json
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/fix/stage')
import stage_fix
args = sys.argv[sys.argv.index('--')+1:]
look = args[0]
steps = args[1].split(',') if len(args) > 1 and args[1] != 'all' else None
save = args[2] if len(args) > 2 else None
t = time.time()
rep = stage_fix.apply({'look': look, 'steps': steps})
print('REPORT created', rep['created'])
print('seconds', time.time()-t)
if save:
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=save, compress=True, copy=True)
    print('saved', save, os.path.getsize(save))
