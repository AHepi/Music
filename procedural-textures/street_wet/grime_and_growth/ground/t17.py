import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet'), job('base_main','main','base',size=(540,960,16))]
jobs.append(job('kit_main','main','kit:dirt,groundcracks,groundmoss,iron',size=(540,960,16)))
jobs.append(job('kit_main2','main','kit:dirt,groundcracks,groundmoss,iron',size=(540,960,16),state='dry'))
for layer in ('dirt','groundcracks','groundmoss','iron'):
    jobs.append(job(f'solo_{layer}','main',f'solo:{layer}',size=(540,960,16)))
run('t17', jobs)
