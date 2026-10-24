"""Checker's own: how much do the sett joints survive the stage (plate view, first frame)? Same measure as check_joints.py, at the stage's 1080 x 1920, central crop of the plate (stage lens)."""
import numpy as np, cv2
R='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
RR=R+'painter_round_2/'
k=np.tan(np.radians(20))/np.tan(np.radians(22))
def central(img, interp):
    h,w=img.shape[:2]; ch,cw=int(round(h*k)),int(round(w*k)); y0,x0=(h-ch)//2,(w-cw)//2
    return cv2.resize(img[y0:y0+ch,x0:x0+cw],(1080,1920),interpolation=interp)
m=cv2.cvtColor(cv2.imread(RR+'behind/work/joint_mask_no_props_1536x2730.png'),cv2.COLOR_BGR2RGB).astype(np.float32)/255
mc=central(m,cv2.INTER_AREA)
road=mc[...,2]>0.99
joint=(mc[...,0]>0.5)&road
stone=(mc[...,1]>0.9)&road
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def rd(p): return cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB).astype(np.float32)/255
P=central(rd(RR+'plate/lockout_plate_wet_round2.png'),cv2.INTER_AREA); N=central(rd(RR+'plate/lockout_plate_wet_round2_no_props.png'),cv2.INTER_AREA)
prop=cv2.dilate((np.abs(lum(P)-lum(N))>0.06).astype(np.uint8),np.ones((25,25),np.uint8))>0
rows=np.where(road.any(axis=1))[0]; edges=np.linspace(rows.min(),rows.max()+1,4).astype(int)
def meas(L):
    sm=stone&~prop; f=sm.astype(np.float32)
    num=cv2.boxFilter(L*f,-1,(13,13),normalize=False); den=cv2.boxFilter(f,-1,(13,13),normalize=False)
    ok=den>6; local=num/np.maximum(den,1)
    jm=joint&ok&~prop
    ab=np.abs(local-L)/np.maximum(local,1e-3)
    o=[]
    for i in range(3):
        band=np.zeros_like(joint); band[edges[i]:edges[i+1]]=True
        o.append((float(ab[jm&band].mean()), float(ab[sm&ok&band].mean())))
    return o
pics=[('plate (central crop)',lum(P)),
      ('front painting (central crop)',lum(central(rd(RR+'paint/front_painting_final.png'),cv2.INTER_AREA))),
      ('stage BEFORE fix',lum(rd(RR+'stage/stills/before/wet_projector/still-6.00.jpg'))),
      ('stage AFTER fix',lum(rd(RR+'stage/stills/after/wet_projector/still-6.00.jpg')))]
print('joint dots',joint.sum(),'(far, mid, near) joint-vs-stone difference | stone mottling')
for n,L in pics:
    o=meas(L); print('%-32s'%n,'  '.join('%s %.3f | %.3f'%(b,a,c) for b,(a,c) in zip(('far','mid','near'),o)))
