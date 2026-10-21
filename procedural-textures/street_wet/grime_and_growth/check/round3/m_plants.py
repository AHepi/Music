import sys, json, numpy as np, cv2
G='proc-work/street_wet/grime_and_growth/'
B='proc-work/kits/weathering/harness/baseline/maps/'
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED)
    if a.dtype==np.uint16: a=a.astype(np.float32)/65535
    else: a=a.astype(np.float32)/255
    return a[...,:3][...,::-1]   # RGB
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
res={}
for state in ('dry','wet'):
    base=rd(G+f'integrated/plates/street/final_main_A_{state}_base.png')
    for tag,p in (('old',G+f'integrated/plates/street/final_main_A_{state}_kit.png'),('fix',G+f'fix/plates/street/final_main_A_{state}_kit.png')):
        k=rd(p); h,w=k.shape[:2]
        hsv=cv2.cvtColor((k*255).astype(np.uint8),cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
        H,S,V=hsv[...,0]/255*360,hsv[...,1]/255,hsv[...,2]/255
        d=np.abs(k-base).max(axis=2)
        changed=d>0.03
        # any visible change from base outside walls: 'plants' = changed & ground part & greenish or cream
        green=(k[...,1]>k[...,0]*1.08)&(k[...,1]>k[...,2]*1.15)&(S>0.3)&(d>0.04)&(H>60)&(H<170)
        green[:int(h*0.55)]=False
        n,lab,st,cen=cv2.connectedComponentsWithStats(green.astype(np.uint8),connectivity=8)
        # merge near blobs: dilate to cluster plants
        gd=cv2.dilate(green.astype(np.uint8),np.ones((9,9),np.uint8))
        n2,lab2,st2,cen2=cv2.connectedComponentsWithStats(gd,connectivity=8)
        clusters=[i for i in range(1,n2) if (green&(lab2==i)).sum()>=20]
        L=lum(k)
        r=dict(green_dots=int(green.sum()),clusters=len(clusters),plant_lum_med=float(np.median(L[green])),plant_lum_p90=float(np.percentile(L[green],90)),
               share_lum_over_0p3=float((L[green]>0.3).mean()),hue_med=float(np.median(H[green])),sat_med=float(np.median(S[green])))
        if state=='wet':
            pud=cv2.imread(B+'puddle_main_wet.png',cv2.IMREAD_UNCHANGED)[...,2]>32768
            pud=cv2.resize(pud.astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)>0
            # root = lowest green pixel of the cluster; test the pixel just below/at root and a 9x9 neighbourhood
            inroot=0; incentre=0; inany=0
            pudd=cv2.dilate(pud.astype(np.uint8),np.ones((9,9),np.uint8))>0
            for i in clusters:
                ys,xs=np.where(lab2==i); m=(green&(lab2==i)); ys2,xs2=np.where(m)
                yr=ys2.max(); xr=int(np.median(xs2[ys2>=yr-3]))
                cy,cx=int(ys2.mean()),int(xs2.mean())
                if pud[min(h-1,yr+4),xr]: inroot+=1
                if pud[cy,cx]: incentre+=1
                if (m&pudd).any(): inany+=1
            r.update(cl=len(clusters),root_in_puddle=inroot,centre_in_puddle=incentre,touching_puddle_9px=inany,green_dots_in_puddle=float((green&pud).sum()/max(green.sum(),1)),puddle_share_ground=float(pud[int(h*0.55):].mean()))
        res[f'{state}_{tag}']=r
        print(state,tag,json.dumps({a:(round(b,3) if isinstance(b,float) else b) for a,b in r.items()}))
json.dump(res,open(G+'check/round3/m_plants.json','w'),indent=1)
