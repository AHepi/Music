# What this does (plain words): writes a job file that draws the lockout plate (dry and wet) at Rubbish Amount 2 (the heaviest), to look for white flat scraps that read as plastic.
import sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
OUT = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/' + sys.argv[1]
P = (1536, 2730, 48)
lockout = [wj.pic('lockout', 'B', 'dry', 'rubbish', size=P, name='amount2_lockout_B_dry', dials={'amount': 2.0}, dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='amount2_lockout_B_wet', dials={'amount': 2.0}, dirt=False)]
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
