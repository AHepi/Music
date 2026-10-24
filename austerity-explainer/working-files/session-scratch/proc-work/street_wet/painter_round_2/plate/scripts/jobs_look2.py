# What this does (plain words): writes the job files for the second look at the round 2 fixes: close views of the gutter, the wall foot, a doorstep and the drum, and the dry and wet lockout plates, so that the new pieces can be seen at 100 %.
# Use: python3 -I jobs_look2.py FOLDER_NAME
import os, sys
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
P = (1536, 2730, 48)
C = (1600, 1200, 48)
street = [wj.pic('main', 'A', 'wet', 'rubbish', size=P, name='plate_main_A_wet_rubbish', dirt=False)]
for cam in ('gutter', 'wall', 'doorstep'):
    street.append(wj.pic(cam, 'A', 'wet', 'rubbish', size=C, name=f'closeup_{cam}_A_wet_rubbish', dirt=False))
lockout = [wj.pic('lockout', 'B', 'dry', 'rubbish', size=P, name='plate_lockout_B_dry_rubbish', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='plate_lockout_B_wet_rubbish', dirt=False),
           wj.pic('drum', 'B', 'wet', 'rubbish', size=C, name='closeup_drum_B_wet_rubbish', dirt=False)]
print(wj.write(OUT, 'street', street, puddle_masks=False))
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
