import json, numpy as np
base='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test'
stage=open(f'{base}/stages/stage_cottages_north.py').read()
hook=stage+'''

# ---- variation hook wrapper: the variations tool calls apply(variation); the stage's own apply takes the options
_STAGE_APPLY = apply


def apply(variation):
    """Runs inside Blender on a freshly opened copy of the finished scene (never saved): rebuilds the cottages_north part with the variation's numbers."""
    return _STAGE_APPLY(dict(variation.get('args') or {}))
'''
open(f'{base}/work/cottages_north/hooks/north_hook.py','w').write(hook)
rng=np.random.default_rng(4)
keys={'thatch_roll':(0.6,2.0),'chip_amount':(0.7,1.9),'chip_count':(0.4,2.6),'thatch_lump':(0.4,2.2),'sag_cm':(0.7,1.3)}
n=10
cols={}
for k,(lo,hi) in keys.items():
    perm=rng.permutation(n)
    cols[k]=[lo+(hi-lo)*((perm[i]+0.5)/n) for i in range(n)]
vars_=[]
for i in range(n):
    args={k:round(cols[k][i],2) for k in keys}
    nm='v%02d-roll%s-chip%s-n%s-lump%s'%(i+1,args['thatch_roll'],args['chip_amount'],args['chip_count'],args['thatch_lump'])
    vars_.append({'name':nm.replace('.','p'),'script':'hooks/north_hook.py','args':args,'ranges':{k:list(v) for k,v in keys.items()}})
out={'change':'the eave roll, thatch lumps, plaster chips and ridge sag of cottages A and B','scene':'part.blend','settings':'../../plan/place-settings.json','cameras':['View wide','View cottage_close'],'variations':vars_}
json.dump(out,open(f'{base}/work/cottages_north/north-variations.json','w'),indent=1)
print([v['name'] for v in vars_])
