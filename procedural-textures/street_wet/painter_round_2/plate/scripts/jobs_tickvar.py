# What this does (plain words): writes a job file that draws the main wet plate several times with different "fade of the groove slope with distance" settings, to find the one that removes the short bright ticks on the vertical joints in the middle distance.
# Use: python3 -I jobs_tickvar.py FOLDER_NAME
import os, sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
BASE = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
V = {'f03_s4_e20': {}, 'f03_s3_e9': dict(far_share=0.03, fade_start=3.0, fade_end=9.0), 'f00_s3_e8': dict(far_share=0.0, fade_start=3.0, fade_end=8.0),
     'f10_s5_e20_round1': dict(far_share=0.10, fade_start=5.0, fade_end=20.0), 'f03_s3_e12': dict(far_share=0.03, fade_start=3.0, fade_end=12.0)}
street = []
for name, jd in V.items():
    street.append(wj.pic('main', 'A', 'wet', 'rubbish', size=(1536, 2730, 48), name='tick_main_A_wet_' + name, dirt=False, joint_dials=jd))
print(wj.write(OUT, 'street', street, puddle_masks=False))
