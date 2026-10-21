# What this does (plain words): writes the job files for the first look at the round 2 fixes: a small and a full-size street picture and the lockout picture, so that the new pieces can be seen at 100 %.
# Use: python3 -I jobs_look1.py FOLDER_NAME
import os, sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
BASE = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
P = (1536, 2730, 48)
street = [wj.pic('main', 'A', 'wet', 'rubbish', size=(540, 960, 16), name='small_main_A_wet_rubbish', dirt=False),
          wj.pic('main', 'A', 'wet', 'rubbish', size=P, name='plate_main_A_wet_rubbish', dirt=False)]
lockout = [wj.pic('lockout', 'B', 'wet', 'rubbish', size=(540, 960, 16), name='small_lockout_B_wet_rubbish', dirt=False),
           wj.pic('lockout', 'B', 'dry', 'rubbish', size=P, name='plate_lockout_B_dry_rubbish', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='plate_lockout_B_wet_rubbish', dirt=False)]
print(wj.write(OUT, 'street', street, puddle_masks=False))
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
