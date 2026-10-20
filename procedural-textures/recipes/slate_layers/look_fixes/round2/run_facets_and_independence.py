# What this does (plain words): one Blender run that does two small jobs one after the other, so that only ONE Blender process is used:
#   1. bakes the test variants given (look_fixes/bake_variants.py), and
#   2. bakes the pictures for the round-2 independence re-test of MOSS and OUTLINE AND SHADOW (look_fixes/independence_two_layers_bake.py).
# Use: blender -b --disable-autoexec -t 2 --python run_facets_and_independence.py -- VARIANT_OUT SIZE 'JSON variants' INDEPENDENCE_OUT INDEPENDENCE_SIZE
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOOK = os.path.dirname(HERE)
arguments = sys.argv[sys.argv.index('--') + 1:]
first, second = sys.argv[:sys.argv.index('--') + 1], None
sys.argv = first + arguments[0:3]
runpy.run_path(os.path.join(LOOK, 'bake_variants.py'), run_name='__main__')
sys.argv = first + arguments[3:5]
runpy.run_path(os.path.join(LOOK, 'independence_two_layers_bake.py'), run_name='__main__')
