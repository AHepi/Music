import sys, json, os, time
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import settings as S
from harness import remote
from growth import jobs_growth
variants=json.loads(sys.argv[2]); out=sys.argv[1]; scene=sys.argv[3] if len(sys.argv)>3 else 'street'
cams=json.loads(sys.argv[4]) if len(sys.argv)>4 else ['main','notice']
st=S.load_set('pit_village_street')
spec=jobs_growth.make(st, scene, 'tune', variants=[(k,v) for k,v in variants.items()], cameras=cams)
os.makedirs(out,exist_ok=True)
p=os.path.join(out,'jobs_tune.json'); json.dump(spec,open(p,'w'),indent=1)
sc=next(s for s in st.scenes if s['id']==scene)
print(remote.run_batch(sc['file'],[p],f'/workspace/wk_out/growth_tune_{os.path.basename(out)}',out,runner_script=KIT+'/growth/runner_growth.py'))
