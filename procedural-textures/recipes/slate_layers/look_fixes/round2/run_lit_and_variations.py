# What this does (plain words): one Blender run that does two jobs one after the other, so that only ONE Blender process is used:
#   1. the raking-light pictures of the reference, the old default and the new default (look_fixes/lit_several.py), and
#   2. a small colour-only bake of the eight settings variations on the new default (look_fixes/bake_variants.py), so they can be LOOKED at.
# Use: blender -b --disable-autoexec -t 2 --python run_lit_and_variations.py -- 'LIT JOBS JSON' VARIANT_OUT SIZE 'JSON variants'
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOOK = os.path.dirname(HERE)
arguments = sys.argv[sys.argv.index('--') + 1:]
first = sys.argv[:sys.argv.index('--') + 1]
sys.argv = first + arguments[0:1]
runpy.run_path(os.path.join(LOOK, 'lit_several.py'), run_name='__main__')
sys.argv = first + arguments[1:4]
runpy.run_path(os.path.join(LOOK, 'bake_variants.py'), run_name='__main__')
