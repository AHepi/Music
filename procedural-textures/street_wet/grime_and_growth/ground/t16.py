import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
L='kit:dirt,groundcracks,groundmoss,iron'
jobs=[job('today_main','main','today',state='wet')]
for cam in ('pipe_close','wall_lamp'):
    jobs.append(job(f'base_{cam}',cam,'base',size=(960,720,24)))
    jobs.append(job(f'iron_{cam}',cam,'solo:iron',size=(960,720,24)))
run('t16', jobs)
jobs=[job('today_lockout','lockout','today',state='wet')]
jobs.append(job('base_drum','drum_close','base',size=(960,720,24),light='B'))
jobs.append(job('all_drum','drum_close',L,size=(960,720,24),light='B'))
jobs.append(job('iron_drum','drum_close','solo:iron',size=(960,720,24),light='B'))
for k in range(1,8):
    jobs.append(job(f'ip{k}','drum_close','solo:iron',size=(480,360,1),light='B',view='layer:iron',dials={'iron':{'show_part':k}}))
jobs.append(job('dp5','drum_close','solo:dirt',size=(480,360,1),light='B',view='layer:dirt',dials={'dirt':{'show_part':5}}))
run('t16b', jobs, scene='lockout')
