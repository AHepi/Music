# What this file does (plain words): writes the job files for the LAST pictures the sheets need: the rubbish mask drawn on the ground seen from the film's cameras (with the film's own colours so the street can
# be seen: red = gutter, green = wall foot, blue = corners and doorsteps, yellow = props), and the dial demonstrations of the doorstep and gutter views under the low side light C (bright enough to see).
# Use: python3 -I jobs_extras.py FOLDER_NAME
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_jobs as wj
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/work/'
OUT = BASE + sys.argv[1]
S = (960, 720, 32)
KINDS = {'amount_0': dict(amount=0), 'default': {}, 'amount_2': dict(amount=2.0), 'dust_off': dict(dust=0), 'ash_off': dict(ash=0), 'mud_off': dict(mud=0), 'straw_off': dict(straw=0), 'paper_off': dict(paper=0),
         'leaves_off': dict(leaves=0), 'pieces_off': dict(pieces_density=0), 'dust_only': dict(ash=0, mud=0, straw=0, paper=0, leaves=0, pieces_density=0), 'pieces_only': dict(dust=0, ash=0, mud=0, straw=0, paper=0, leaves=0, relief=0.0),
         'relief_0': dict(relief=0.0), 'grit_size_2': dict(grit_size=2.0), 'grit_size_0.6': dict(grit_size=0.6), 'wet_look_0': dict(wet_look=0.0), 'dust_darkness_0.3': dict(dust_darkness=0.3),
         'dust_darkness_1': dict(dust_darkness=1.0), 'pieces_density_2': dict(pieces_density=2.0), 'piece_size_1.6': dict(piece_size=1.6)}
PLACES = {'default': {}, 'corners_0': dict(corners=0), 'corners_2': dict(corners=2.0), 'wall_foot_0': dict(wall_foot=0), 'wall_foot_2': dict(wall_foot=2.0), 'gutter_0': dict(gutter=0), 'gutter_2': dict(gutter=2.0),
          'patchiness_0': dict(patchiness=0.0), 'patchiness_1': dict(patchiness=1.0), 'seed_5': dict(seed=5), 'seed_11': dict(seed=11), 'wall_width_1.4': dict(wall_width=1.4), 'gutter_width_1': dict(gutter_width=1.0)}
street = [wj.pic('main', 'A', 'wet', 'rubbish', view='mask_colours', name='maskview_main_A_wet', film_look=True, size=(1080, 1920, 16)),
          wj.pic('gutter', 'A', 'wet', 'rubbish', view='mask_colours', name='maskview_gutter_A_wet', film_look=True, size=(960, 720, 16)),
          wj.pic('doorstep', 'A', 'wet', 'rubbish', view='mask_colours', name='maskview_doorstep_A_wet', film_look=True, size=(960, 720, 16))]
for k, v in KINDS.items():
    street.append(wj.pic('doorstep', 'C', 'wet', 'rubbish', dials=v, size=S, name=f'doorstepC_{k}', dirt=False))
for k, v in PLACES.items():
    street.append(wj.pic('gutter', 'C', 'wet', 'rubbish', dials=v, size=S, name=f'gutterC_{k}', dirt=False))
    street.append(wj.pic('wall', 'C', 'wet', 'rubbish', dials=v, size=S, name=f'wallC_{k}', dirt=False))
print(wj.write(OUT, 'street', street, puddle_masks=False))
lockout = [wj.pic('lockout', 'B', 'wet', 'rubbish', view='mask_colours', name='maskview_lockout_B_wet', film_look=True, size=(1536, 2730, 16)),
           wj.pic('drum', 'B', 'wet', 'rubbish', view='mask_colours', name='maskview_drum_B_wet', film_look=True, size=(960, 720, 16))]
print(wj.write(OUT, 'lockout', lockout, puddle_masks=False))
