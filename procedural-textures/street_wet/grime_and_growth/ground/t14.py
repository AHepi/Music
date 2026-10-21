import sys; sys.path.insert(0,'proc-work/street_wet/grime_and_growth/ground')
from rr import *
jobs=[job('today_main','main','today',state='wet')]
sz=(1536,2730,48); cam='main'
jobs.append(job('base',cam,'base',size=sz,plate_height=2730,keep_png=True))
jobs.append(job('v1_default',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True))
jobs.append(job('v2_norelief',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'relief':0.0}}))
jobs.append(job('v3_nodull',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'dull':0.0}}))
jobs.append(job('v4_neither',cam,'solo:groundcracks',size=sz,plate_height=2730,keep_png=True,dials={'groundcracks':{'dull':0.0,'relief':0.0}}))
run('t14', jobs)
