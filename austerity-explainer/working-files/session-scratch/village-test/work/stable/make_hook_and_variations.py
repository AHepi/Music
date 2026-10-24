import json, numpy as np
R='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
W=R+'/work/stable'
stage=open(R+'/stages/stage_stable.py').read()
wrapper='''

# ---- variation hook wrapper: the variations tool calls apply(variation); the stage's own apply takes the options
_STAGE_APPLY = apply


def apply(variation):
    """Runs inside Blender on a freshly opened copy of the built scene (never saved): rebuilds the stable with the variation's numbers."""
    return _STAGE_APPLY(dict(variation.get('args') or {}))
'''
open(W+'/hooks/stable_hook.py','w').write(stage+wrapper)
ranges={'sag_deg':[0.0,5.0],'fresh':[0.2,1.6],'gaps':[0.3,3.0],'moss':[0.0,2.0],'open_deg':[30.0,95.0]}
keys=list(ranges)
rng=np.random.default_rng(23)
n=10
cols={}
for k in keys:
    lo,hi=ranges[k]
    pts=(np.arange(n)+rng.random(n)*0.6+0.2)/n      # one point in each tenth of the range
    rng.shuffle(pts)
    cols[k]=lo+pts*(hi-lo)
vs=[]
for i in range(n):
    args={k: round(float(cols[k][i]),2) for k in keys}
    name=f"v{i+1:02d}-sag{args['sag_deg']:.1f}-moss{args['moss']:.1f}-gap{args['gaps']:.1f}".replace('.','p')
    vs.append({'name':name,'script':'hooks/stable_hook.py','args':args,'ranges':ranges})
doc={'change':'door leaf sag and opening, board colours of the replaced boards, shingle gaps and moss of the stable','scene':'scene.blend','settings':'../../plan/place-settings.json','cameras':['View stable_close','View wide'],'variations':vs}
json.dump(doc,open(W+'/stable-variations.json','w'),indent=1)
print(json.dumps([v['args'] for v in vs]))
