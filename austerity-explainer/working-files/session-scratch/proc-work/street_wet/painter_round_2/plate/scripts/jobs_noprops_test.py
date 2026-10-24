# What this does (plain words): writes a job file for a small test of the props-free picture: the lockout wet picture (540 x 960) drawn (A) with everything, (B) with the film's near props hidden, the drum's coals too,
# and (C) with the film's near props hidden but the drum's glowing coals left in. It is to decide whether hiding the drum and its coals changes the lighting of the rest of the street.
# Use: python3 -I jobs_noprops_test.py FOLDER_NAME
import os, sys
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
S = (810, 1440, 24)
lockout = [wj.pic('lockout', 'B', 'wet', 'rubbish', size=S, name='nop_A_everything', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=S, name='nop_B_props_hidden', dirt=False, hide_props=True),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=S, name='nop_C_props_hidden_coals_kept', dirt=False, hide_props=True, keep_coals=True)]
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
