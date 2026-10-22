import sys, copy, time, json
P0='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond'
sys.path.insert(0,P0); sys.path.insert(0,P0+'/work')
import numpy as np, importlib
import sil, g6p_trees as T
d=np.load(P0+'/work/old_maple.npz'); old_u=d['hue']
W=450
olds={}
for cam in ('photo','veranda'):
    ml0=sil.disc_mask(d['P'], d['scale'][:,0]*1.5*0.5*0.85, cam, W)
    tr=[(-6.7,1.3,-0.05),(-6.65,1.2,0.95),(-6.15,1.05,1.85),(-5.55,1.2,2.6),(-5.0,1.45,3.25)]
    olds[cam]=ml0|sil.tube_mask(tr,[0.2,0.165,0.13,0.095,0.06],cam,W)
def evaluate(pads, seed=31, detail=False):
    new=T.maple_crown(seed=seed, pads=pads, hue_target=(old_u.mean(), old_u.std()), n_total=56000)
    trunk,roots,B=T.maple_skeleton(pads)
    r={}
    for cam in ('photo','veranda'):
        ml=sil.disc_mask(new['P'], new['SIZE']*0.5*0.85, cam, W)
        mb=np.zeros_like(ml)
        vis=[]
        for path in B:
            p=np.array(path); m=sil.tube_mask(p[:,:3],p[:,3],cam,W); mb|=m; vis.append(int((m&~ml).sum()))
        p=np.array(trunk); mt=sil.tube_mask(p[:,:3],p[:,3],cam,W); mb|=mt
        sn=ml|mb
        r[cam]=dict(iou=sil.iou(olds[cam],sn), ratio=sn.sum()/olds[cam].sum(), vis=vis, nvis=sum(v>=100 for v in vis))
    return r
def score(r):
    s=r['photo']['iou']+0.6*r['veranda']['iou']
    s-=4*max(0,abs(r['photo']['ratio']-1.0)-0.07)+2*max(0,abs(r['veranda']['ratio']-1.0)-0.07)
    s+=0.06*min(r['photo']['nvis'],5)+0.09*min(r['veranda']['nvis'],5)
    return s
if __name__=='__main__':
    import os
    pads=json.load(open(P0+'/work/best_pads.json')) if os.path.exists(P0+'/work/best_pads.json') else [list(p) for p in T.MAPLE_PADS]
    best=evaluate(pads); bs=score(best); print("start", round(bs,3), {k:(round(v['iou'],3),round(v['ratio'],3),v['nvis']) for k,v in best.items()})
    rng=np.random.default_rng(5); t0=time.time(); it=0
    while time.time()-t0<float(sys.argv[1]) if len(sys.argv)>1 else 120:
        it+=1
        cand=copy.deepcopy(pads)
        for _ in range(int(rng.integers(1,4))):
            i=int(rng.integers(0,len(cand))); k=int(rng.choice([0,1,2,3,4,5])); 
            step=[0.12,0.12,0.12,0.08,0.08,0.05][k]
            cand[i][k]+=rng.normal(0,step)
            cand[i][3]=float(np.clip(cand[i][3],0.8,1.9)); cand[i][4]=float(np.clip(cand[i][4],0.7,1.6)); cand[i][5]=float(np.clip(cand[i][5],0.40,0.75))
        r=evaluate(cand); sc=score(r)
        if sc>bs:
            pads,bs,best=cand,sc,r; print(it, round(bs,3), {k:(round(v['iou'],3),round(v['ratio'],3),v['nvis']) for k,v in best.items()}, flush=True)
    json.dump(pads,open(P0+'/work/best_pads.json','w'))
    print("final pads"); 
    for p in pads: print([round(float(x),2) if not isinstance(x,int) else x for x in p])
    print(json.dumps({k:dict(iou=round(v['iou'],3),ratio=round(v['ratio'],3),vis=v['vis']) for k,v in best.items()}))
