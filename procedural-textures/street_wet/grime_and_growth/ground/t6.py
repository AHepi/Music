import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
for cam in ('close_road','gutter_close'):
    jobs.append(job(f'base_{cam}',cam,'base',size=(960,720,24)))
    for layer in ('dirt','groundcracks','groundmoss'):
        jobs.append(job(f'{layer}_{cam}',cam,f'solo:{layer}',size=(960,720,24)))
run('t6', jobs)
