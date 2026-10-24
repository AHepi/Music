# Small driver: build a job file and draw it on the rented machine through the kit's remote runner (which uses only render_client_cached.py).
import json, os, sys, time
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode=True
from apply import settings as S
from harness import remote
WORK=os.path.dirname(os.path.abspath(__file__))
SET='pit_village_street'
FEATURE_DIRS=[WORK]

def job(name, camera, look, light='A', state='wet', size=(540,960,16), view='beauty', dials=None, keep_png=False, plate_height=None, hide_roles=None, master=1.0):
    j=dict(name=name, camera=camera, light=light, state=state, look=look, view=view, size=list(size), group='x')
    if dials: j['dials']=dials
    if keep_png: j['keep_png']=True
    if plate_height: j['plate_height']=plate_height
    if hide_roles: j['hide_roles']=hide_roles
    if master!=1.0: j['master']=master
    return j

def run(tag, jobs, scene='street', set_id=SET):
    st=S.load_set(set_id)
    scn=st.scene(scene)
    out_local=os.path.join(WORK,'runs',tag)
    os.makedirs(out_local, exist_ok=True)
    spec=dict(set=set_id, scene=scene, pack=True, feature_dirs=FEATURE_DIRS, jobs=jobs)
    jf=os.path.join(out_local,'jobs.json')
    json.dump(spec, open(jf,'w'), indent=1)
    remote_out=f'/workspace/wk_out/ground_{tag}'
    t=time.time()
    res=remote.run_batch(scn['file'], [jf], remote_out, os.path.join(out_local,'out'))
    res['wall']=round(time.time()-t,1)
    print(tag, res, flush=True)
    return res

def plan(tag, items, look='kit:dirt,groundcracks,groundmoss,iron', scene='street', set_id=SET, size='450x4200', env=None):
    """Plan views of layer masks seen from above (ground/plan_views.py on the rented machine)."""
    st=S.load_set(set_id); scn=st.scene(scene)
    out_local=os.path.join(WORK,'runs',tag)
    os.makedirs(out_local, exist_ok=True)
    script=os.path.join(KIT,'ground','plan_views.py')
    remote_out=f'/workspace/wk_out/ground_{tag}'
    t=time.time()
    res=remote.run_script(scn['file'], script, [set_id, scene, '{out}', look, ','.join(items), size], remote_out, os.path.join(out_local,'out'))
    res['wall']=round(time.time()-t,1)
    print(tag, res, flush=True)
    return res
