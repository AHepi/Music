# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the job files that SHOW WHAT EACH CONTROL DOES: (1) the rubbish mask seen from above (plan pictures, colours: red gutter, green wall foot, blue corners and doorsteps, yellow props) for
# many dial settings, in the street copy and in the lockout shot file (which has the props); (2) pictures of the same view with one dial changed at a time (beauty pictures).
# Use: python3 -I jobs_controls.py FOLDER_NAME   (the lockout file's plan pictures are named lockplan_* and lockplantotal_*: both files write into one folder, and the runner skips names that exist)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_jobs as wj
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/work/'
OUT = BASE + sys.argv[1]
PLANS = {
    'default': {}, 'amount_0.5': dict(amount=0.5), 'amount_2': dict(amount=2.0),
    'gutter_only': dict(wall_foot=0, corners=0, props=0), 'wall_foot_only': dict(gutter=0, corners=0, props=0), 'corners_only': dict(gutter=0, wall_foot=0, props=0), 'props_only': dict(gutter=0, wall_foot=0, corners=0),
    'seed_5': dict(seed=5), 'seed_11': dict(seed=11), 'patchiness_0': dict(patchiness=0.0), 'patchiness_1': dict(patchiness=1.0),
    'gutter_width_0.25': dict(gutter_width=0.25), 'gutter_width_1.6_crown_clear_1': dict(gutter_width=1.6), 'gutter_width_1.6_crown_clear_0': dict(gutter_width=1.6, crown_clear=0.0),
    'wall_width_0.4': dict(wall_width=0.4), 'wall_width_1.4': dict(wall_width=1.4), 'props_width_0.4': dict(props_width=0.4), 'props_width_1.2': dict(props_width=1.2),
}


def plan(name, dials, camera, light, prefix='plan_'):
    return dict(name=prefix + name, camera=camera, light=light, state='dry', w=450, h=2100, samples=1, look='rubbish', view='plan', plan=[0.0, 42.0], mode='colours', dials=dials)


def plan_total(name, dials, camera, light, prefix='plantotal_'):
    return dict(name=prefix + name, camera=camera, light=light, state='dry', w=225, h=2100, samples=1, look='rubbish', view='plan', plan=[-12.0, 72.0], mode='total', dials=dials)


KINDS_OFF = {'dust_off': dict(dust=0), 'ash_off': dict(ash=0), 'mud_off': dict(mud=0), 'straw_off': dict(straw=0), 'paper_off': dict(paper=0), 'leaves_off': dict(leaves=0),
             'pieces_off': dict(pieces_density=0), 'amount_0': dict(amount=0), 'amount_2': dict(amount=2.0), 'default': {}, 'dust_only': dict(ash=0, mud=0, straw=0, paper=0, leaves=0, pieces_density=0),
             'pieces_only': dict(dust=0, ash=0, mud=0, straw=0, paper=0, leaves=0, relief=0.0), 'relief_0': dict(relief=0.0), 'grit_size_2': dict(grit_size=2.0), 'grit_size_0.6': dict(grit_size=0.6),
             'wet_look_0': dict(wet_look=0.0), 'dust_darkness_0.3': dict(dust_darkness=0.3), 'dust_darkness_1': dict(dust_darkness=1.0), 'pieces_density_2': dict(pieces_density=2.0), 'piece_size_1.6': dict(piece_size=1.6)}
street = [plan(k, v, 'main', 'A') for k, v in PLANS.items()] + [plan_total('default', {}, 'main', 'A')]
for k, v in KINDS_OFF.items():
    street.append(wj.pic('doorstep', 'D', 'wet', 'rubbish', dials=v, size=(800, 600, 24), name=f'doorstep_{k}', dirt=False))
for k, v in {'default': {}, 'corners_0': dict(corners=0), 'corners_2': dict(corners=2.0), 'wall_foot_0': dict(wall_foot=0), 'wall_foot_2': dict(wall_foot=2.0), 'gutter_0': dict(gutter=0), 'gutter_2': dict(gutter=2.0),
             'patchiness_0': dict(patchiness=0.0), 'patchiness_1': dict(patchiness=1.0), 'seed_5': dict(seed=5), 'seed_11': dict(seed=11)}.items():
    street.append(wj.pic('gutter', 'D', 'wet', 'rubbish', dials=v, size=(800, 600, 24), name=f'gutter_{k}', dirt=False))
print(wj.write(OUT, 'street', street, puddle_masks=False))
lockout = [plan(k, v, 'lockout', 'B', prefix='lockplan_') for k, v in PLANS.items()] + [plan_total('default', {}, 'lockout', 'B', prefix='lockplantotal_')]
for k, v in KINDS_OFF.items():
    lockout.append(wj.pic('drum', 'B', 'wet', 'rubbish', dials=v, size=(800, 600, 24), name=f'drum_{k}', dirt=False))
for k, v in {'props_0': dict(props=0), 'props_2': dict(props=2.0), 'default': {}, 'seed_5': dict(seed=5)}.items():
    lockout.append(wj.pic('drum', 'B', 'wet', 'rubbish', dials=v, size=(800, 600, 24), name=f'drumprops_{k}', dirt=False))
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
