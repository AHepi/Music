import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
tag=sys.argv[1]
L='kit:dirt,groundcracks,groundmoss,iron'
jobs=[job('today_main','main','today',state='wet')]
for cam,sz in (('main',(1536,2730,48)),('notice',(1536,2730,48))):
    jobs.append(job(f'plate_base_{cam}',cam,'base',size=sz,plate_height=2730,keep_png=True))
    jobs.append(job(f'plate_all_{cam}',cam,L,size=sz,plate_height=2730,keep_png=True))
run(tag, jobs)
