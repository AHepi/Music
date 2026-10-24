# Checker: draws the integrator's OWN saved round-5 job files again, unchanged (same jobs, same order), into check/measure/r5redo/kit/<scene>, so its measuring scripts can be run on fresh pictures.
import json, os, sys, shutil
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode=True
from apply import settings as sm
from harness import remote
H=os.path.dirname(os.path.abspath(__file__))
S=sm.load_set('pit_village_street')
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/integrated/work/r5/kit/_jobs/'
for scene_id in sys.argv[1:]:
    scene=next(s for s in S.scenes if s['id']==scene_id)
    jd=os.path.join(H,'r5redo','_jobs'); os.makedirs(jd,exist_ok=True)
    src=W+f'jobs_{scene_id}_kit_all.json'; dst=jd+f'/jobs_{scene_id}_kit_all.json'; shutil.copy(src,dst)
    n=len(json.load(open(dst))['jobs'])
    print(scene_id,n,'jobs (the integrator\'s own list)',flush=True)
    res=remote.run_batch(scene['file'],[dst],f'/workspace/wk_out/chk_r5redo_{scene_id}',os.path.join(H,'r5redo','kit',scene_id),runner_script=os.path.join(KIT,'growth','runner_growth.py'))
    print(scene_id,res,flush=True)
