import sys
sys.path.insert(0, '.')
from fixrun import job, run
jobs = [job(f'rb_{v}', 'main', 'A', 'dry', size=(768, 1365, 16), plate_height=2730, dials={'iron': {'rust_bright': v}}) for v in (1.0, 1.4, 1.7, 3.0)]
run('street', jobs, 'diag7')
