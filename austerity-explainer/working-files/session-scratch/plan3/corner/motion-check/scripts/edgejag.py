import numpy as np, sys, cv2
W=sys.argv[1]
res=[]
prev_r=None
for i in range(30,390):
    g=cv2.cvtColor(cv2.imread(f"{W}/all/f{i:03d}.png"),cv2.COLOR_BGR2GRAY).astype(np.float32)
    out=[]
    for side,(xa,xb) in (("L",(740,820)),("R",(900,980))):
        rows=range(1010,1110)
        xs=[]
        for y in rows:
            line=g[y,xa:xb]
            thr=(line.max()+line.min())/2
            if side=="L":
                # first crossing dark->light going right
                idx=np.where((line[:-1]<thr)&(line[1:]>=thr))[0]
            else:
                idx=np.where((line[:-1]>=thr)&(line[1:]<thr))[0]
                idx=idx[::-1]
            if len(idx)==0: xs.append(np.nan); continue
            k=idx[0]; a,b=line[k],line[k+1]
            xs.append(xa+k+(thr-a)/(b-a+1e-6))
        xs=np.array(xs); ys=np.array(list(rows)); m=~np.isnan(xs)
        p=np.polyfit(ys[m],xs[m],1); r=xs[m]-np.polyval(p,ys[m])
        r=r[np.abs(r)<5]
        out.append((side,np.std(r),np.mean(np.abs(np.diff(r)))))
    res.append((i,out))
for i,out in res:
    if i%3==0 or i in (100,101,102,103,104,105):
        print(f"{i:3d} t={i/30:5.2f} "+" ".join(f"{s}: wobble={a:.2f}px step={b:.2f}" for s,a,b in out))
