# What this file does (plain words): the checker's own list of pictures to draw (written for rubbish_runner.py of the builders). It only writes two job files, run_a (street copy) and run_b (lockout shot file).
# Different from the builders' own runs: seed 5 for the rubbish where a plate is drawn (they used seed 0), different picture sizes (1080 x 1920) and plate sizes with 48 samples.
import os, sys
sys.path.insert(0, 'proc-work/street_wet/relief_and_rubbish/rubbish/tools')
import write_jobs as wj
B = 'proc-work/street_wet/relief_and_rubbish/check_round_1/'
S5 = {'seed': 5.0}
street = []
# the hard ones at the test-set size (540 x 960), three looks each
for (label, light, state) in (('main', 'D', 'wet'), ('main', 'E', 'heavy'), ('main', 'A', 'wet')):
    for look in ('round2', 'joints', 'rubbish'):
        street.append(wj.pic(label, light, state, look, name=f'chk_{label}_{light}_{state}_{look}'))
# double-size flat overhead light, wet
for look in ('joints', 'rubbish'):
    street.append(wj.pic('main', 'D', 'wet', look, size=(1080, 1920, 32), name=f'chk2x_main_D_wet_{look}', dials=S5 if look == 'rubbish' else None))
# plate size
for look in ('round2', 'rubbish'):
    street.append(wj.pic('main', 'A', 'wet', look, size=(1536, 2730, 48), name=f'plate_main_A_wet_{look}', dials=S5 if look == 'rubbish' else None))
street.append(wj.pic('main', 'A', 'heavy', 'rubbish', size=(1536, 2730, 48), name='plate_main_A_heavy_rubbish', dials=S5))
street.append(wj.pic('main', 'D', 'wet', 'rubbish', size=(1536, 2730, 48), name='plate_main_D_wet_rubbish', dials=S5))
street.append(wj.pic('close', 'E', 'wet', 'rubbish', size=(1920, 1440, 48), name='plate_close_E_wet_rubbish', dials=S5))
street.append(wj.pic('close', 'D', 'wet', 'rubbish', size=(1920, 1440, 48), name='plate_close_D_wet_rubbish', dials=S5))
# gutter, wall foot and doorstep close views, dial values 0.5 / 1 / 2
for cam in ('gutter', 'wall', 'doorstep'):
    for amt in (0.5, 1.0, 2.0):
        street.append(wj.pic(cam, 'A', 'wet', 'rubbish', size=(1200, 900, 32), name=f'close_{cam}_amount{amt}', dials={'seed': 5.0, 'amount': amt}, dirt=False))
street.append(wj.pic('gutter', 'A', 'dry', 'rubbish', size=(1200, 900, 32), name='close_gutter_dry', dials=S5, dirt=False))
street.append(wj.pic('wall', 'A', 'dry', 'rubbish', size=(1200, 900, 32), name='close_wall_dry', dials=S5, dirt=False))
print(wj.write(B + 'run_a', 'street', street, joint_masks=[('main', 540, 960), ('main', 1080, 1920), ('main', 1536, 2730), ('close', 1920, 1440)], ground_masks=[('main', 540, 960), ('main', 1080, 1920), ('main', 1536, 2730), ('close', 1920, 1440)]))

lockout = []
for (light, state) in (('B', 'wet'), ('B', 'heavy'), ('D', 'wet')):
    for look in ('round2', 'joints', 'rubbish'):
        lockout.append(wj.pic('lockout', light, state, look, name=f'chk_lockout_{light}_{state}_{look}'))
for look in ('round2', 'joints', 'rubbish'):
    lockout.append(wj.pic('lockout', 'B', 'wet', look, size=(1536, 2730, 48), name=f'plate_lockout_B_wet_{look}', dials=S5 if look == 'rubbish' else None))
lockout.append(wj.pic('lockout', 'B', 'dry', 'rubbish', size=(1536, 2730, 48), name='plate_lockout_B_dry_rubbish', dials=S5))
lockout.append(wj.pic('lockout', 'B', 'wet', 'rubbish', size=(1536, 2730, 48), name='plate_lockout_B_wet_rubbish_amount2', dials={'seed': 5.0, 'amount': 2.0}, dirt=False))
lockout.append(wj.pic('lockout', 'B', 'wet', 'rubbish', size=(1536, 2730, 48), name='plate_lockout_B_wet_rubbish_amount05', dials={'seed': 5.0, 'amount': 0.5}, dirt=False))
print(wj.write(B + 'run_b', 'lockout', lockout, joint_masks=[('lockout', 540, 960), ('lockout', 1536, 2730)], ground_masks=[('lockout', 540, 960), ('lockout', 1536, 2730)]))
