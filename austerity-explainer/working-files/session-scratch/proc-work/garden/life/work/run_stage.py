# Test harness: open start file, apply stage, save a compressed test file, print report. Args after '--': look steps(comma|all) outname [quick]
import bpy, sys, os, time, json, importlib
argv=sys.argv[sys.argv.index('--')+1:]
look=argv[0]; steps=None if argv[1]=='all' else argv[1].split(','); outname=argv[2]; quick='quick' in argv
HERE='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life'
sys.path.insert(0,HERE); sys.path.insert(0,'/home/user/Music/japanese-courtyard')
import stage_life; importlib.reload(stage_life)
bpy.context.preferences.filepaths.save_version=0
t=time.time()
rep=stage_life.apply({'look':look,'steps':steps,'quick':quick})
print('STAGE SECONDS',round(time.time()-t,1))
if outname!='none':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'out',outname),compress=True,copy=True)
