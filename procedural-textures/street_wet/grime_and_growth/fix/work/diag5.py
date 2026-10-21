import sys
sys.path.insert(0, '.')
from fixrun import job, run, full_dials
from v1 import V0_NEW, V1, V2, V3, touched, merged
T = touched(V0_NEW, V1, V2, V3)
d = full_dials(T, merged(V0_NEW, V3))
jobs = []
jobs.append(job('main_A_dry_V3', 'main', 'A', 'dry', dials=d))
jobs.append(job('main_A_wet_V3', 'main', 'A', 'wet', dials=d))
jobs.append(job('close_road_wet_V3', 'close_road', 'A', 'wet', size=(1920, 1440, 32), plate_height=1440, dials=d))
jobs.append(job('flag_wet_V3', 'flag_close', 'A', 'wet', size=(960, 720, 24), plate_height=2730, dials=d))
jobs.append(job('gutter_dry_V3', 'gutter_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=d))
jobs.append(job('doorstep_wet_V3', 'doorstep_close', 'A', 'wet', size=(960, 720, 24), plate_height=2730, dials=d))
jobs.append(job('wall_dry_V3', 'wall_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=d))
run('street', jobs, 'diag5')
