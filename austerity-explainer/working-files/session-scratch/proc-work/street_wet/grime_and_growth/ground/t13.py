import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/ground')
from rr import *
tag=sys.argv[1]
jobs=[job('today_main','main','today',state='wet')]
for cam,sz in (('main',(1536,2730,48)),('close_road',(1920,1440,48))):
    jobs.append(job(f'base_{cam}',cam,'base',size=sz,plate_height=sz[1],keep_png=True))
    for layer in ('dirt','groundcracks','groundmoss'):
        jobs.append(job(f'{layer}_{cam}',cam,f'solo:{layer}',size=sz,plate_height=sz[1],keep_png=True))
run(tag, jobs)
