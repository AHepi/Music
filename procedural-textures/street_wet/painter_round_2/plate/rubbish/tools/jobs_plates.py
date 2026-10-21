# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the job files for the FULL-SIZE pictures (what the painter would be given): plate size 1536 x 2730 for the street and lockout cameras and 1920 x 1440 for the low close view, 64 samples,
# EEVEE with the round 2 plate settings (ray tracing on, shadow rays 4, steps 16); each with the looks joints (the setts' round) and rubbish; plus their measuring masks; plus the three close
# views (gutter, wall foot, doorstep) at 1600 x 1200 for the 100 % close-ups; plus THE final lockout plate (wet, setts and rubbish), whose PNG is kept (name starts with final_).
# Use: python3 -I jobs_plates.py FOLDER_NAME
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_jobs as wj
BASE = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/'
OUT = BASE + sys.argv[1]
SAMPLES = 64
P = {'main': (1536, 2730, SAMPLES), 'close': (1920, 1440, SAMPLES), 'lockout': (1536, 2730, SAMPLES)}
street, lockout = [], []
for label, light, state in (('main', 'A', 'dry'), ('main', 'A', 'wet'), ('main', 'E', 'wet'), ('close', 'A', 'dry'), ('close', 'A', 'wet'), ('close', 'E', 'wet')):
    for look in ('round2', 'joints', 'rubbish'):
        street.append(wj.pic(label, light, state, look, size=P[label], name=f'plate_{label}_{light}_{state}_{look}'))
for cam in ('gutter', 'wall', 'doorstep'):
    for look in ('joints', 'rubbish'):
        street.append(wj.pic(cam, 'A', 'wet', look, size=(1600, 1200, SAMPLES), name=f'closeup_{cam}_A_wet_{look}', dirt=False))
for state in ('dry', 'wet', 'heavy'):
    for look in ('round2', 'joints', 'rubbish'):
        lockout.append(wj.pic('lockout', 'B', state, look, size=P['lockout'], name=f'plate_lockout_B_{state}_{look}'))
lockout.append(wj.pic('drum', 'B', 'wet', 'joints', size=(1600, 1200, SAMPLES), name='closeup_drum_B_wet_joints', dirt=False))
lockout.append(wj.pic('drum', 'B', 'wet', 'rubbish', size=(1600, 1200, SAMPLES), name='closeup_drum_B_wet_rubbish', dirt=False))
lockout.append(wj.pic('lockout', 'B', 'wet', 'rubbish', size=(1536, 2730, SAMPLES), name='final_lockout_plate_wet_setts_and_rubbish', dirt=False))
print(wj.write(OUT, 'street', street, joint_masks=[('main', 1536, 2730), ('close', 1920, 1440)], ground_masks=[('main', 1536, 2730), ('close', 1920, 1440)]))
print(wj.write(OUT, 'lockout', lockout, joint_masks=[('lockout', 1536, 2730)], ground_masks=[('lockout', 1536, 2730)]))
