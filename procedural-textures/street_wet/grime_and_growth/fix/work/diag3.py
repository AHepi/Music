import sys
sys.path.insert(0, '.')
from fixrun import job, run, full_dials
from v1 import V0_NEW, V1, touched, merged
T = touched(V0_NEW, V1)
dV1 = full_dials(T, merged(V0_NEW, V1))
jobs = []
for tag, d in (('V1', dV1),):
    jobs.append(job(f'main_A_dry_{tag}', 'main', 'A', 'dry', dials=d))
    jobs.append(job(f'main_A_wet_{tag}', 'main', 'A', 'wet', dials=d))
    jobs.append(job(f'close_road_wet_{tag}', 'close_road', 'A', 'wet', size=(1920, 1440, 32), plate_height=1440, dials=d))
    jobs.append(job(f'doorstep_dry_{tag}', 'doorstep_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=d))
    jobs.append(job(f'gutter_dry_{tag}', 'gutter_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=d))
run('street', jobs, 'diag3')
