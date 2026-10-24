# What this file does (plain words): writes the job files of a LOOK run: the rubbish at bigger sizes (the street's main view at 1080 x 1920, the three close views at 1280 x 960 and the lockout shot at
# the full plate size 1536 x 2730), wet and dry, to judge the look by eye. Use: python3 -I jobs_look.py FOLDER_NAME [dial=value ...]   (dials given are used for all the rubbish pictures)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_jobs as wj
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/work/'
name = sys.argv[1]
dials = {k: float(v) for k, v in (a.split('=') for a in sys.argv[2:])}
OUT = BASE + name
big = (1280, 960, 32)
street = [wj.pic('main', 'A', 'wet', 'rubbish', dials=dials, size=(1080, 1920, 24)), wj.pic('main', 'A', 'dry', 'rubbish', dials=dials, size=(1080, 1920, 24)),
          wj.pic('gutter', 'A', 'wet', 'rubbish', dials=dials, size=big), wj.pic('wall', 'A', 'wet', 'rubbish', dials=dials, size=big), wj.pic('doorstep', 'A', 'wet', 'rubbish', dials=dials, size=big),
          wj.pic('doorstep', 'A', 'dry', 'rubbish', dials=dials, size=big), wj.pic('gutter', 'A', 'dry', 'rubbish', dials=dials, size=big)]
print(wj.write(OUT, 'street', street, puddle_masks=False))
lockout = [wj.pic('lockout', 'B', 'wet', 'rubbish', dials=dials, size=(1536, 2730, 48), name='plate_lockout_wet_rubbish'), wj.pic('lockout', 'B', 'dry', 'rubbish', dials=dials, size=(1536, 2730, 48), name='plate_lockout_dry_rubbish')]
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
