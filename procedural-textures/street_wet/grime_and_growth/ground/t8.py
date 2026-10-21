import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
sz=(960,720,24)
for cam in ('flag_close','gutter_close','doorstep_close'):
    jobs.append(job(f'base_{cam}',cam,'base',size=sz))
    jobs.append(job(f'crk_{cam}',cam,'solo:groundcracks',size=sz))
    jobs.append(job(f'crkS_{cam}',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'flag_fine_share':0.5,'flag_broken_share':0.2,'flag_tilt_share':0.2,'corner_chip_share':0.5,'kerb_chip_share':0.5}}))
run('t8', jobs)
