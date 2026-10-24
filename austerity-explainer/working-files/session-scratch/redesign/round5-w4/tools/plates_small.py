"""What this does (scratch, round 5 W4 helper): runs an assemble_works.py text (for example an earlier copy) as if it
stood in the works folder, then draws chosen plates from their plate cameras at a smaller size, so two versions of
the script can be compared picture by picture.
Use: blender -b works-lane.blend --python plates_small.py -- --script TEXT.py --as REAL/assemble_works.py --out FOLDER
     [--only works-w1-plate,...] [--width 768] [--samples 16]"""
import os
import sys

argv = sys.argv[sys.argv.index('--') + 1:]
def option(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
script, real, out = option('--script'), option('--as'), option('--out')
os.makedirs(out, exist_ok=True)
g = {'__name__': '__main__', '__file__': real}
exec(compile(open(script).read(), real, 'exec'), g)
width = int(option('--width', '768'))
height = round(width * 2730 / 1536)
only = option('--only', '').split(',') if option('--only') else list(g['PLATES'])
for picture in only:
    view, state, men_2, what = g['PLATES'][picture]
    g['set_state'](state, plate=True, men_2_in_plate=men_2)
    g['put_camera'](view, 'plate', g['PLATE_FOV'])
    g['render'](os.path.join(out, f'{picture}.png'), width, height, int(option('--samples', '16')))
    print('plates_small: drew', picture, flush=True)
