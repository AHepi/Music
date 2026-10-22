# chain test: shapes (copy) -> life; saves test file. Args: look outname [life steps]
import bpy, sys, os, time, importlib
argv=sys.argv[sys.argv.index('--')+1:]
look=argv[0]; outname=argv[1]
HERE='proc-work/garden/life'
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/work')
bpy.context.preferences.filepaths.save_version=0
import stage_shapes_copy as stage_shapes
t=time.time(); r1=stage_shapes.apply({'look':look}); print('SHAPES SECONDS',round(time.time()-t,1))
import stage_life
t=time.time(); r2=stage_life.apply({'look':look}); print('LIFE SECONDS',round(time.time()-t,1))
if outname!='none':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'out',outname),compress=True,copy=True)
