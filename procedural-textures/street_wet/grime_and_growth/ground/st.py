# work script: run the ground self-tests on the rented machine for one set and scene: python3 -I st.py SET SCENE [layers]
import os, sys, json, time
KIT='proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode=True
from apply import settings as S
from harness import remote
WORK=os.path.dirname(os.path.abspath(__file__))
set_id, scene = sys.argv[1], sys.argv[2]
layers = sys.argv[3] if len(sys.argv)>3 and not sys.argv[3].startswith('--') else None
st=S.load_set(set_id); scn=st.scene(scene)
tag=f'selftest_{set_id}_{scene}'
out_local=os.path.join(WORK,'runs',tag)
os.makedirs(out_local, exist_ok=True)
args=[set_id, scene, '{out}'] + ([layers] if layers else [])
t=time.time()
extra=[scn['file']] if '--upload' in sys.argv else []
res=remote.run_script(scn['file'], os.path.join(KIT,'ground','selftest_ground.py'), args, f'/workspace/wk_out/ground_{tag}', os.path.join(out_local,'out'), extra_roots=extra)
res['wall']=round(time.time()-t,1)
print(tag,res,flush=True)
