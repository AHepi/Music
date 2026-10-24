import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
for cam,sz in (('main',(540,960,16)),('close_road',(640,480,24)),('gutter_close',(960,720,24)),('doorstep_close',(960,720,24)),('pipe_close',(960,720,24))):
    jobs.append(job(f'base_{cam}',cam,'base',size=sz))
    jobs.append(job(f'dirt_{cam}',cam,'solo:dirt',size=sz))
for k in range(1,9):
    jobs.append(job(f'part{k}_main','main','solo:dirt',size=(540,960,1),view='layer:dirt',dials={'dirt':{'show_part':k}}))
run('t1', jobs)
