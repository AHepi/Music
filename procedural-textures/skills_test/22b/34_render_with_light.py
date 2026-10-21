# Trial 22b: sets the energy of the one extra "lookdev_key" light in memory (nothing saved), then runs the street's own EEVEE tool 22_render_eevee.py unchanged.
# Run: blender -b --disable-autoexec FILE.blend --python 34_render_with_light.py -- WATTS OUT_FOLDER CAMERA STATES W H SAMPLES [key=value ...]
import runpy
import sys

import bpy

sys.dont_write_bytecode = True
i = sys.argv.index('--')
watts = float(sys.argv[i + 1])
sys.argv = sys.argv[:i + 1] + sys.argv[i + 2:]
bpy.data.lights['lookdev_key'].energy = watts
runpy.run_path('proc-work/street_wet/tools/22_render_eevee.py', run_name='__main__')
