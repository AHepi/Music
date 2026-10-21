"""Checker's own joint measurement (own code; reads only the Blender mask and the pictures).
Mask drawn with the near props hidden: R = joint, G = stone face, B = road.
Joint contrast at a joint dot = (average of the stone-face dots within 8 dots - this dot) / that stone average (1 = black joint, 0 = same as stone).
Three bands by rows (far, middle, near). Dots inside the props' footprint are left out (where plate and props-free plate differ by > 0.06, grown 25 dots)."""
import numpy as np, cv2
R='proc-work/street_wet/'
RR=R+'painter_round_2/'
m=cv2.cvtColor(cv2.imread(RR+'behind/work/joint_mask_no_props_1536x2730.png'),cv2.COLOR_BGR2RGB)
road=m[...,2]>252
joint=(m[...,0]>127)&road
stone=(m[...,1]>229)&road
print('joint dots',joint.sum(),'stone dots',stone.sum())
def lum(p):
    a=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB).astype(np.float32)/255
    return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
P=lum(RR+'plate/lockout_plate_wet_round2.png'); N=lum(RR+'plate/lockout_plate_wet_round2_no_props.png')
prop=cv2.dilate((np.abs(P-N)>0.06).astype(np.uint8),np.ones((25,25),np.uint8))>0
rows=np.where(road.any(axis=1))[0]; top,bot=rows.min(),rows.max()
edges=np.linspace(top,bot+1,4).astype(int)
print('road rows',top,bot,'band edges',edges)
pics=[('plate, props hidden (what the painter saw for the behind)',N),('plate, with props',P),
 ('FRONT painting (final)',lum(RR+'paint/front_painting_final.png')),
 ('BEHIND painting (final)',lum(RR+'paint/behind_painting_final.png')),
 ('first test painting (old wet plate)',lum(R+'painter_test/pictures/wet_painting_lined_up.png'))]
def meas(L, leave_props):
    sm=stone&(~prop if leave_props else True)
    f=sm.astype(np.float32)
    num=cv2.boxFilter(L*f,-1,(17,17),normalize=False); den=cv2.boxFilter(f,-1,(17,17),normalize=False)
    ok=den>8
    local=np.where(ok,num/np.maximum(den,1),np.nan)
    jm=joint&ok&(~prop if leave_props else True)
    c=(local-L)/np.maximum(local,1e-3)
    out=[]
    for i,b in enumerate(('far','mid','near')):
        band=np.zeros_like(joint); band[edges[i]:edges[i+1]]=True
        sel=jm&band
        # stone mottling: mean abs deviation of stone dots from their local stone mean
        sel2=sm&band&ok
        ab=np.abs(local-L)/np.maximum(local,1e-3)
        out.append((float(np.nanmean(ab[sel])), float(np.nanmean(c[sel])), float(np.nanmean(ab[sel2])), int(sel.sum())))
    return out
print('%-58s %s'%('picture','far / mid / near : joint difference from local stone, ABSOLUTE (signed: + = darker) | stone mottling'))
for name,L in pics:
    o=meas(L, True)
    print('%-58s'%name,'  '.join('%s %.2f (%+.2f) | %.2f'%(b,c,d,mt) for b,(c,d,mt,n) in zip(('far','mid','near'),o)))
