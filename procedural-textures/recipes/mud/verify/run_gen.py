# verifier: starts the builder's mud_generator.py exactly as it is, but with byte-code writing switched off so that nothing is written outside verify/.
# Use: blender -b --disable-autoexec -t 2 --python verify/run_gen.py -- DESCRIPTION.json OUT_FOLDER [--size N] [--samples N] [--shift a b]
import os, runpy, sys
sys.dont_write_bytecode = True
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generator', 'mud_generator.py'), run_name='__main__')
