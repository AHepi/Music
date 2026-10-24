import os, sys
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/fix/work')
from fixrun import job, run
jobs=[]
for cam,size,ph in (('notice',(1536,2730,48),2730),('close_road',(1920,1440,48),1440)):
    for state in ('wet','dry'):
        for look in ('base','kit_all'):
            jobs.append(job(f'p_{cam}_{state}_{look}',cam,'A',state,look=look,size=size,plate_height=ph,keep_png=False,group='plate'))
H=os.path.dirname(os.path.abspath(__file__))
run('street',jobs,'other_plates',out_root=H+'/rounds')
