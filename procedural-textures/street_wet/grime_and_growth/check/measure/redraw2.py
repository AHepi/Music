# Checker: second batch on the street file: the five close views (dry and wet, light A) and the notice and close-road plates, base and everything on, PNG kept.
import json, os, sys
KIT='proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode=True
from apply import settings as sm
from harness import testset, remote
HERE=os.path.dirname(os.path.abspath(__file__))
S=sm.load_set('pit_village_street')
ref=json.load(open('proc-work/street_wet/grime_and_growth/integrated/work/r5/kit/_jobs/jobs_street_kit_all.json'))
scene=next(s for s in S.scenes if s['id']=='street')
jobs=[dict(name='today_street',camera='main',light='A',state='wet',look='today',view='beauty',size=[540,960,16],group='today',scene='street')]
ts=S.get('test_set')
for look in ('base','kit_all'):
    for v in ts['close_views']:
        for state in ('dry','wet'):
            jobs.append(dict(name=f'c_{look}_{v}_A_{state}',camera=v,light='A',state=state,look=look,view='beauty',size=[960,720,24],group='close',label=v,keep_png=True))
    for camera,w,h in (('notice',1536,2730),('close_road',1920,1440)):
        jobs.append(dict(name=f'p_{look}_{camera}_A_wet',camera=camera,light='A',state='wet',look=look,view='beauty',size=[w,h,48],group='plate',plate_height=h,label=camera,keep_png=True,pieces_json=(look=='kit_all')))
spec=dict(set='pit_village_street',scene='street',pack=True,feature_dirs=ref['feature_dirs'],jobs=jobs)
jd=os.path.join(HERE,'redraw2','_jobs'); os.makedirs(jd,exist_ok=True)
path=os.path.join(jd,'jobs_street2.json'); json.dump(spec,open(path,'w'),indent=1)
print(len(jobs),'jobs',[j['name'] for j in jobs][:8],flush=True)
res=remote.run_batch(scene['file'],[path],'/workspace/wk_out/chk_street2',os.path.join(HERE,'redraw2','street'),runner_script=os.path.join(KIT,'growth','runner_growth.py'))
print(res,flush=True)
