import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
cam='close_road'; sz=(960,720,24)
jobs.append(job('base',cam,'base',size=sz))
jobs.append(job('def',cam,'solo:groundcracks',size=sz))
jobs.append(job('nosett',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'sett_disturb':0.0}}))
jobs.append(job('nosett_nokerb',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'sett_disturb':0.0,'kerb_chips':0.0}}))
jobs.append(job('alloff',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'sett_disturb':0.0,'kerb_chips':0.0,'flag_cracks':0.0}}))
for k in (3,8,9):
    jobs.append(job(f'part{k}',cam,'solo:groundcracks',size=(960,720,1),view='layer:groundcracks',dials={'groundcracks':{'show_part':k}}))
run('t7', jobs)
