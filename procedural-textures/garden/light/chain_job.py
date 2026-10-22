# What this does: EXTRA check, not part of the brief. Runs the other two finished stages (copies in work/chain/) and then draws one picture with render_job.py, so the
# light stage is seen on top of shapes + life. Same arguments as render_job.py; the look comes from --apply-stage.
# Run: blender -b --disable-autoexec courtyard_final.blend -P chain_job.py -- --apply-stage real --camera photo --size 960x640 --samples 128 --out BASE
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE + '/work/chain'); sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index('--') + 1:]
look = argv[argv.index('--apply-stage') + 1]
import stage_shapes, stage_life
stage_shapes.apply({'look': look})
stage_life.apply({'look': look, 'scatter': False})
import render_job
render_job.main()
