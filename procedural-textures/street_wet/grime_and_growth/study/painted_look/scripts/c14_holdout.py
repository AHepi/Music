"""Honest test of the fit: fit on everything EXCEPT round 2 (the newest painting), then predict round 2's marks and compare with what really happened."""
import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
from c11_logistic import irls
import json
a=json.load(__import__('gzip').open(NUM+'/c7_marks.json.gz'))
train=[k for k in a if 'round 2' not in k]; test=[k for k in a if 'round 2' in k]
def rows_of(keys):
    out=[]
    for k in keys: out+=a[k]
    return out
def prep(rows):
    ok,ch=C.judge(rows)
    W_=np.array([r['width'] for r in rows]); E_=np.array([r['elong'] for r in rows]); S_=np.array([r['plate'] for r in rows])
    return ok,W_,E_,S_
okT,WT,ET,ST=prep(rows_of(train)); okH,WH,EH,SH=prep(rows_of(test))
# training: the small-input marks of round 1 only for 'small' (the only other 0.53 painting); full-size ones are not mixed in
small_train=[k for k in train if 'small input' in k]
okS,WS,ES,SS=prep(rows_of(small_train))
res={}
for kind,selT,selH in (('speck',ES<2.5,EH<2.5),('line',ES>=4,EH>=4)):
    s=selT&(SS>=0.02)&(SS<0.3)&(WS>=1)&(WS<30)
    X=np.column_stack([np.ones(s.sum()),np.log(WS[s]),np.log(SS[s])]); b=irls(X,okS[s].astype(float))
    h=selH&(SH>=0.02)&(SH<0.3)&(WH>=1)&(WH<30)
    pred=1/(1+np.exp(-(b[0]+b[1]*np.log(WH[h])+b[2]*np.log(SH[h])))); obs=okH[h]
    print(f"{kind}: trained on round 1 wet only (n={s.sum()}), tested on round 2 (n={h.sum()}); coefficients {np.round(b,2)}")
    for lo,hi in [(0,0.2),(0.2,0.4),(0.4,0.6),(0.6,0.8),(0.8,1.01)]:
        m=(pred>=lo)&(pred<hi)
        if m.sum()>=10: print("   predicted %.1f-%.1f: n=%4d  predicted mean %.2f  really came back %.2f"%(lo,hi,m.sum(),pred[m].mean(),obs[m].mean()))
    verdict=np.where(pred>=0.8,'GOOD',np.where(pred>=0.5,'RISKY','LOST'))
    for v in ('GOOD','RISKY','LOST'):
        m=verdict==v
        if m.sum(): print("   verdict %-5s n=%4d  really came back %.0f%%"%(v,m.sum(),100*obs[m].mean()))
    res[kind]=dict(b=b.tolist(),n_train=int(s.sum()),n_test=int(h.sum()))
json.dump(res,open(NUM+'/c14_holdout.json','w'),indent=1)
