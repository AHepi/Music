import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
sz=(1536,2730,48)
cam='main'
jobs.append(job('base',cam,'base',size=sz,plate_height=2730,keep_png=True))
jobs.append(job('v1_default',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True))
jobs.append(job('v2_nojoint',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'open_joint_share':0.0}}))
jobs.append(job('v3_nodist',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'sett_disturbed_share':0.0,'missing_share':0.0}}))
jobs.append(job('v4_none',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'sett_disturb':0.0}}))
run('t11', jobs)
