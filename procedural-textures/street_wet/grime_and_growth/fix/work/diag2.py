import sys
sys.path.insert(0, '.')
from fixrun import job, run, full_dials
touched = [('groundcracks', 'open_joint_share'), ('groundcracks', 'sett_disturb'), ('groundcracks', 'relief'), ('dirt', 'water_marks'), ('dirt', 'film')]
# 'relief' is an extra dial with a kit default of 1.0 (not in the look): give its value in every variant
base = {'groundcracks': {'relief': 1.0}}
variants = {
    'A_now': {},
    'B_noopen': {'groundcracks': {'open_joint_share': 0.0}},
    'C_nosett': {'groundcracks': {'sett_disturb': 0.0}},
    'D_norelief': {'groundcracks': {'relief': 0.0}},
    'E_nomarks': {'dirt': {'water_marks': 0.0}},
    'F_nofilm': {'dirt': {'film': 0.0, 'water_marks': 0.0}},
}
jobs = []
for name, ov in variants.items():
    merged = {}
    for d in (base, ov):
        for l, kv in d.items():
            merged.setdefault(l, {}).update(kv)
    dials = full_dials(touched, merged)
    jobs.append(job(f'cr_{name}', 'close_road', 'A', 'wet', size=(1440, 1080, 32), plate_height=1440, dials=dials))
run('street', jobs, 'diag2')
