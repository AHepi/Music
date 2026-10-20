# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2: runs the quick "pictures of numbers" checks of round 1 again, all in ONE Blender run (opening the street copy afresh before each, because each check rewires the
# materials to show plain numbers): the puddle sweep (02_puddle_sweep.py: how deep the puddles are on the road and pavements from three cameras), the colour ratios
# (04_colour_ratios.py: how much darker each material gets when wet, no lighting) and the wall masks (03_wall_masks.py: wet band at the foot and streaks under sills and eaves).
# Each takes a few seconds. A second step in plain Python (02b_puddle_fit.py, 04b_colour_ratios.py) turns the pictures into tables.
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/23_calibration_driver.py -- OUT_FOLDER
# Writes OUT_FOLDER/puddles/*, OUT_FOLDER/colour/*, OUT_FOLDER/walls/*
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
ROOT = os.path.abspath(os.path.join(HERE, '..'))
out_folder = os.path.abspath(sys.argv[sys.argv.index('--') + 1])
STREET = os.path.join(ROOT, 'set_copy', 'street.blend')
JOBS = [('02_puddle_sweep.py', os.path.join(out_folder, 'puddles')), ('04_colour_ratios.py', os.path.join(out_folder, 'colour')),
        ('03_wall_masks.py', os.path.join(out_folder, 'walls'))]
import apply_wetness_to_set as aw  # noqa: E402
import wetness_layer as wl  # noqa: E402,F401

for index, (script, folder) in enumerate(JOBS):
    if index:
        bpy.ops.wm.open_mainfile(filepath=STREET)
    aw.APPLIED.clear()
    sys.argv = ['blender', '--', folder]
    print('=== RUNNING', script, flush=True)
    source = open(os.path.join(HERE, script)).read()
    exec(compile(source, script, 'exec'), {'__name__': '__main__', '__file__': os.path.join(HERE, script)})
print('ALL DONE')
