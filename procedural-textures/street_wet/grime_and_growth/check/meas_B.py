import numpy as np, cv2, json, colorsys
P='proc-work/street_wet/grime_and_growth/integrated/plates/'
def load(p): return cv2.imread(p)[...,::-1].astype(np.float32)/255
out={}
for scene,names in [('street',['final_main_A_dry','final_main_A_wet']),('lockout',['final_lockout_B_dry','final_lockout_B_wet'])]:
    for n in names:
        b=load(P+f'{scene}/{n}_base.png'); k=load(P+f'{scene}/{n}_kit.png')
        hsv=cv2.cvtColor((k*255).astype(np.uint8),cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
        H=hsv[...,0]/255*360; S=hsv[...,1]/255; V=hsv[...,2]/255
        d=np.abs(k-b).max(axis=2)
        # green plant dots: green clearly dominant over red and blue in the kit picture, saturation >=0.35, and changed vs base
        green=(k[...,1]>k[...,0]*1.08)&(k[...,1]>k[...,2]*1.15)&(S>0.3)&(d>0.04)&(H>60)&(H<170)
        # exclude sky (top 40%) and teal wall tint: only keep lower 45% of plate for street ground, whole for lockout lower half
        h=k.shape[0]
        ground=np.zeros_like(green); ground[int(h*0.55):]=True
        g=green&ground
        res=dict(green_dots=int(g.sum()),share_of_ground=round(float(g.sum()/ground.sum()),5))
        if g.sum()>50:
            res.update(H_med=round(float(np.median(H[g])),1),H_p10=round(float(np.percentile(H[g],10)),1),H_p90=round(float(np.percentile(H[g],90)),1),
                S_med=round(float(np.median(S[g])),3),V_med=round(float(np.median(V[g])),3),V_p90=round(float(np.percentile(V[g],90)),3))
            # surround brightness: dilate and take ring
            m=g.astype(np.uint8); ring=cv2.dilate(m,np.ones((15,15),np.uint8))-cv2.dilate(m,np.ones((5,5),np.uint8))
            Lb=0.2126*b[...,0]+0.7152*b[...,1]+0.0722*b[...,2]
            res['ring_V_med_base']=round(float(np.median(Lb[ring>0])),3)
            Lk=0.2126*k[...,0]+0.7152*k[...,1]+0.0722*k[...,2]
            res['plant_lum_med']=round(float(np.median(Lk[g])),3)
            res['plant_over_ring']=round(float(np.median(Lk[g])/np.median(Lb[ring>0])),2)
            # lime: high saturation & bright
            res['share_V_over_0.45']=round(float((V[g]>0.45).mean()),3)
            res['share_S_over_0.6']=round(float((S[g]>0.6).mean()),3)
        out[f'{scene}_{n}']=res
print(json.dumps(out,indent=1)); json.dump(out,open('meas_B.json','w'),indent=1)
