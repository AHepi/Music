# Checker: redraws, on the rented machine, the 22 lighting pictures (base and everything on), the kit's own mark pictures,
# three timed plates each, and the dial-at-zero pictures, then brings them back to check/measure/redraw/<scene>/.
import json, os, sys, time
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode=True
from apply import settings as sm
from harness import testset, remote
HERE=os.path.dirname(os.path.abspath(__file__))
S=sm.load_set('pit_village_street')
look=json.load(open(KIT+'/presets/sooty_1926.json'))
LAYERS=list(look['layers'])
ref=json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/integrated/work/r5/kit/_jobs/jobs_street_kit_all.json'))
fdirs=ref['feature_dirs']
scene_id=sys.argv[1]
part=sys.argv[2] if len(sys.argv)>2 else 'main'
scene=next(s for s in S.scenes if s['id']==scene_id)
ts=S.get('test_set')
cam_time, light_time = (('main','A') if scene_id=='street' else ('lockout','B'))
jobs=[]
today_cam=scene.get('default_camera')
jobs.append(dict(name=f'today_{scene_id}',camera=today_cam,light='A',state='wet',look='today',view='beauty',size=[540,960,16],group='today',scene=scene_id))
base_t22=testset.make_jobs(S,'base',scene_id,('t22',))
if part=='base':
    jobs += base_t22
else:
    pass
if part=='base':
    jd=os.path.join(HERE,'redraw','_jobs'); os.makedirs(jd,exist_ok=True)
    path=os.path.join(jd,f'jobs_{scene_id}_base.json'); json.dump(dict(set='pit_village_street',scene=scene_id,pack=True,feature_dirs=fdirs,jobs=jobs),open(path,'w'),indent=1)
    print(scene_id,'base',len(jobs),'jobs',flush=True)
    res=remote.run_batch(scene['file'],[path],f'/workspace/wk_out/chk3_{scene_id}_base',os.path.join(HERE,'redraw',scene_id+'_base'),runner_script=os.path.join(KIT,'growth','runner_growth.py'))
    print(scene_id,res,flush=True)
    sys.exit(0)
for r in range(3):
    jobs.append(dict(name=f'time_base_{r+1}',camera=cam_time,light=light_time,state='wet',look='base',view='beauty',size=[1536,2730,48],group='time',plate_height=2730))
kit_jobs=testset.make_jobs(S,'kit_all',scene_id,('t22','masks'),layer_keys=LAYERS)
kit_jobs=[j for j in kit_jobs if j['group']=='t22' or (j['name'].startswith('layer_') and '_plate_' not in j['name'])]
jobs += kit_jobs
for r in range(3):
    jobs.append(dict(name=f'time_kit_all_{r+1}',camera=cam_time,light=light_time,state='wet',look='kit_all',view='beauty',size=[1536,2730,48],group='time',plate_height=2730))
# dial-at-zero pictures, same size and samples as the t22 picture of the same name
lab=[j for j in base_t22 if j['group']=='t22' and j['look']=='base' and j['light']==light_time and j['state']=='wet'][0]
basej=dict(camera=lab['camera'],light=lab['light'],state='wet',view='beauty',size=lab['size'],group='zero',keep_png=True)
jobs.append(dict(basej,name='zero_base_again',look='base'))
jobs.append(dict(basej,name='zero_kit_master0',look='kit_all',master=0.0))
jobs.append(dict(basej,name='zero_kit_all_amounts0',look='kit_all',dials={k:{'amount':0.0} for k in LAYERS}))
for k in LAYERS:
    jobs.append(dict(basej,name=f'zero_solo_{k}_amount0',look=f'solo:{k}',dials={k:{'amount':0.0}}))
    jobs.append(dict(basej,name=f'on_solo_{k}',look=f'solo:{k}'))
spec=dict(set='pit_village_street',scene=scene_id,pack=True,feature_dirs=fdirs,jobs=jobs)
jd=os.path.join(HERE,'redraw','_jobs'); os.makedirs(jd,exist_ok=True)
path=os.path.join(jd,f'jobs_{scene_id}.json'); json.dump(spec,open(path,'w'),indent=1)
print(scene_id,len(jobs),'jobs',flush=True)
res=remote.run_batch(scene['file'],[path],f'/workspace/wk_out/chk3_{scene_id}',os.path.join(HERE,'redraw',scene_id),runner_script=os.path.join(KIT,'growth','runner_growth.py'))
print(scene_id,res,flush=True)
