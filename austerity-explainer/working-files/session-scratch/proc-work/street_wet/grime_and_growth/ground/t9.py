import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
sz=(960,720,24)
cam='flag_close'
jobs.append(job('base',cam,'base',size=sz))
jobs.append(job('zero',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'amount':0.0}}))
jobs.append(job('nomarks',cam,'solo:groundcracks',size=sz,dials={'groundcracks':{'flag_fine_share':0.0,'flag_broken_share':0.0,'flag_tilt_share':0.0,'corner_chip_share':0.0,'kerb_chip_share':0.0,'kerb_break_share':0.0,'kerb_scuffs':0.0,'open_joint_share':0.0,'sett_disturbed_share':0.0,'missing_share':0.0}}))
for k in range(1,10):
    jobs.append(job(f'part{k}',cam,'solo:groundcracks',size=(480,360,1),view='layer:groundcracks',dials={'groundcracks':{'show_part':k}}))
jobs.append(job('whole',cam,'solo:groundcracks',size=(480,360,1),view='layer:groundcracks'))
run('t9', jobs)
