import sys
sys.path.insert(0, '.')
from fixrun import job, run, full_dials
from v1 import V0_NEW, V1, V2, R1, touched, merged
T = touched(V0_NEW, V1, V2, R1)
dNow = full_dials(T, merged(V0_NEW))
dV2 = full_dials(T, merged(V0_NEW, V2))
dV2R = full_dials(T, merged(V0_NEW, V2, R1))
jobs = []
jobs.append(job('ro_layer_now', 'main', 'A', 'dry', view='layer:runoff', size=(768, 1365, 1), plate_height=2730, dials=dNow, jpg=True))
jobs.append(job('ro_layer_R1', 'main', 'A', 'dry', view='layer:runoff', size=(768, 1365, 1), plate_height=2730, dials=dV2R, jpg=True))
jobs.append(job('main_A_dry_V2', 'main', 'A', 'dry', dials=dV2))
jobs.append(job('main_A_dry_V2R1', 'main', 'A', 'dry', dials=dV2R))
jobs.append(job('main_A_wet_V2R1', 'main', 'A', 'wet', dials=dV2R))
jobs.append(job('doorstep_dry_V2R1', 'doorstep_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=dV2R))
jobs.append(job('pipe_dry_V2R1', 'pipe_close', 'A', 'dry', size=(960, 720, 24), plate_height=2730, dials=dV2R))
run('street', jobs, 'diag4')
