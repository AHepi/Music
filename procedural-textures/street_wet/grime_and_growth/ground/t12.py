import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
sz=(1536,2730,1)
for k in (8,9):
    jobs.append(job(f'part{k}','main','solo:groundcracks',size=sz,plate_height=2730,view='layer:groundcracks',dials={'groundcracks':{'show_part':k}}))
run('t12', jobs)
