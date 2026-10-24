import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
cams=(('main',(540,960,16)),('close_road',(640,480,24)),('gutter_close',(960,720,24)),('doorstep_close',(960,720,24)),('pipe_close',(960,720,24)),('flag_close',(960,720,24)),('wall_close',(960,720,24)))
for cam,sz in cams:
    jobs.append(job(f'base_{cam}',cam,'base',size=sz))
    jobs.append(job(f'all_{cam}',cam,'kit:dirt,groundcracks,groundmoss,iron',size=sz))
for layer,nparts in (('dirt',8),('groundcracks',9),('groundmoss',5),('iron',7)):
    for k in range(1,nparts+1):
        jobs.append(job(f'p_{layer}_{k}','main','kit:dirt,groundcracks,groundmoss,iron',size=(540,960,1),view=f'layer:{layer}',dials={layer:{'show_part':k}}))
run('t2', jobs)
