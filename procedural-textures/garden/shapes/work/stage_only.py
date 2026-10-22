# usage: blender -b START.blend -P stage_only.py -- LOOK     (applies the stage and saves nothing)
import sys, os
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stage_shapes
look = sys.argv[sys.argv.index('--') + 1]
rep = stage_shapes.apply({'look': look})
print('STAGE_OK', look, len(rep['created']), 'created', len(rep['changed']), 'changed')
