# What this file does (plain words): writes the job files for the FULL-SIZE pictures of this step (1536 x 2730 for the street and lockout cameras, 1600 x 1200 for the close views; 64 samples; EEVEE with the round 2 plate settings:
# ray tracing on, shadow rays 4, steps 16; wet 0.85 / puddles 0.5; JOINTS at strength 1; the rubbish at the new defaults):
#   street copy: the main street camera wet and dry (for the before / after pictures), the gutter, wall foot and doorstep close views (wet);
#   lockout file: the lockout plate dry and wet (with their rubbish masks, to measure the joints), the drum close view, THE FINAL PLATE (name starts with final_, so its PNG is kept) and THE PROPS-FREE PLATE (same, with the film's near props hidden).
# Use: python3 -I jobs_plates_round2.py FOLDER_NAME
import os, sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
BASE = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
P = (1536, 2730, 64)
C = (1600, 1200, 64)
street = [wj.pic('main', 'A', 'wet', 'rubbish', size=P, name='plate_main_A_wet_rubbish'), wj.pic('main', 'A', 'dry', 'rubbish', size=P, name='plate_main_A_dry_rubbish')]
for cam in ('gutter', 'wall', 'doorstep'):
    street.append(wj.pic(cam, 'A', 'wet', 'rubbish', size=C, name=f'closeup_{cam}_A_wet_rubbish', dirt=False))
lockout = [wj.pic('lockout', 'B', 'dry', 'rubbish', size=P, name='plate_lockout_B_dry_rubbish'), wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='plate_lockout_B_wet_rubbish'),
           wj.pic('drum', 'B', 'wet', 'rubbish', size=C, name='closeup_drum_B_wet_rubbish', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='final_lockout_plate_wet_round2', dirt=False),
           wj.pic('lockout', 'B', 'wet', 'rubbish', size=P, name='final_lockout_plate_wet_round2_no_props', dirt=False, hide_props=True)]
print(wj.write(OUT, 'street', street, joint_masks=[('main', 1536, 2730)], ground_masks=[('main', 1536, 2730)]))
print(wj.write(OUT, 'lockout', lockout, joint_masks=[('lockout', 1536, 2730)], ground_masks=[('lockout', 1536, 2730)]))
