"""Smooth version of the 'does the mark come back' tables: a logistic fit  logit p = b0 + b1*ln(width px) + b2*ln(contrast)  per kind (specks / lines) and plate-size sent."""
import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
import json
a=json.load(__import__('gzip').open(NUM+'/c7_marks.json.gz'))
FULL=[k for k in a if 'full-size' in k]; SMALL=[k for k in a if 'small input' in k]
def rows_of(keys):
    out=[]
    for k in keys: out+=a[k]
    return out
def irls(X,y,iters=60,ridge=1e-4):
    b=np.zeros(X.shape[1])
    for _ in range(iters):
        z=X@b; p=1/(1+np.exp(-z)); w=np.clip(p*(1-p),1e-6,None)
        g=X.T@(y-p)-ridge*b; Hh=(X.T*w)@X+ridge*np.eye(X.shape[1])
        step=np.linalg.solve(Hh,g); b+=step
        if np.abs(step).max()<1e-8: break
    return b
out={}
for label,keys in (('full',FULL),('small',SMALL)):
    R=rows_of(keys); ok,ch=C.judge(R)
    W_=np.array([r['width'] for r in R]); E_=np.array([r['elong'] for r in R]); S_=np.array([r['plate'] for r in R])
    for kind,sel0 in (('speck',E_<2.5),('line',E_>=4)):
        s=sel0&(S_>=0.02)&(S_<0.30)&(W_>=1.0)&(W_<30)
        X=np.column_stack([np.ones(s.sum()),np.log(W_[s]),np.log(S_[s])]); y=ok[s].astype(float)
        b=irls(X,y)
        out[f'{label}|{kind}']=dict(b=b.tolist(),n=int(s.sum()),base_rate=float(y.mean()))
        print(f"{label:5s} {kind:5s}  n={s.sum():6d}  p(back) = logistic({b[0]:.2f} + {b[1]:.2f}*ln(width) + {b[2]:.2f}*ln(contrast))")
        # contrast needed for p = 0.5 and 0.8 at several widths
        for pt in (0.5,0.8):
            lg=np.log(pt/(1-pt)); row=[]
            for w in (2,3,4,5,8,12,16):
                c=np.exp((lg-b[0]-b[1]*np.log(w))/b[2]); row.append("%d px: %.3f"%(w,c))
            print(f"      contrast needed for {int(pt*100)}% : "+"   ".join(row))
        # check vs binned
        for (wlo,whi) in [(1,2.5),(2.5,4.5),(4.5,8),(8,16)]:
            for (clo,chi) in [(0.03,0.05),(0.05,0.08),(0.08,0.14)]:
                m=s&(W_>=wlo)&(W_<whi)&(S_>=clo)&(S_<chi)
                if m.sum()>=15:
                    wm=np.exp(np.log(W_[m]).mean()); cm=np.exp(np.log(S_[m]).mean())
                    pf=1/(1+np.exp(-(b[0]+b[1]*np.log(wm)+b[2]*np.log(cm))))
                    print(f"        check width {wlo}-{whi}, contrast {clo}-{chi}: observed {ok[m].mean():.2f}  fitted {pf:.2f}  (n={m.sum()})")
json.dump(out,open(NUM+'/c11_logistic.json','w'),indent=1)
