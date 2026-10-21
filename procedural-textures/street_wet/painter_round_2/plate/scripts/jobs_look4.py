# What this does (plain words): job file for a third look at the pieces (rougher coal and cinder, sharper creases): the lockout wet plate and the drum close view.
import sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
OUT = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/' + sys.argv[1]
lockout = [wj.pic('lockout', 'B', 'wet', 'rubbish', size=(1536, 2730, 48), name='plate_lockout_B_wet_rubbish', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=(1536, 2730, 48), name='plate_lockout_B_wet_noprops', dirt=False, hide_props=True),
           wj.pic('drum', 'B', 'wet', 'rubbish', size=(1600, 1200, 48), name='closeup_drum_B_wet_rubbish', dirt=False)]
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
