import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
tag=sys.argv[1] if len(sys.argv)>1 else 't5'
L='kit:dirt,groundcracks,groundmoss,iron'
jobs=[job('today_main','main','today',state='wet')]
jobs.append(job('plate_base','main','base',size=(1536,2730,48),plate_height=2730,keep_png=True))
jobs.append(job('plate_all','main','kit:dirt,groundcracks,groundmoss,iron',size=(1536,2730,48),plate_height=2730,keep_png=True))
for cam,sz in (('close_road',(1920,1440,48)),):
    jobs.append(job(f'plate_base_{cam}',cam,'base',size=sz,plate_height=sz[1],keep_png=True))
    jobs.append(job(f'plate_all_{cam}',cam,L,size=sz,plate_height=sz[1],keep_png=True))
for cam in ('gutter_close','flag_close','doorstep_close','pipe_close','wall_close'):
    jobs.append(job(f'base_{cam}',cam,'base',size=(960,720,24)))
    jobs.append(job(f'all_{cam}',cam,L,size=(960,720,24)))
run(tag, jobs)
