"""Checker's own: does the wet behind painting match the front painting where both show the same ground (not sky, not near the props, not where the two plates differ)?
Ratios of average brightness and blurred difference, by surface; also the raw (before colour match) behind picture, for comparison."""
import numpy as np, cv2
RR='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/'
z=np.load(RR+'behind/work/ground_labels_no_props.npz')
def rd(p): return cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB).astype(np.float32)/255
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
Pa=rd(RR+'plate/lockout_plate_wet_round2.png'); Na=rd(RR+'plate/lockout_plate_wet_round2_no_props.png')
prop=cv2.dilate((np.abs(lum(Pa)-lum(Na))>0.05).astype(np.uint8),np.ones((41,41),np.uint8))>0
cov=cv2.imread(RR+'paint/work/sky/sky_coverage_1536x2730.png',0).astype(np.float32)/255
F=rd(RR+'paint/front_painting_final.png'); B=rd(RR+'paint/behind_painting_final.png'); Braw=rd(RR+'paint/behind_painting_lined_up.png')
LF,LB,LR=lum(F),lum(B),lum(Braw)
common=(cov<0.01)&~prop
zones={'road':z['road'],'gutter+kerb':z['gutter']|z['kerb'],'pavement':z['pavement']}
# walls: not ground, not sky, upper part
ground=z['road']|z['gutter']|z['kerb']|z['pavement']
zones['everything else (walls, roofs ...)']=~ground&(cov<0.01)
bl=lambda x: cv2.GaussianBlur(x,(0,0),6)
print('%-36s %8s %8s | %8s %8s | blurred mean |diff| matched / raw'%('surface','ratio B/F','raw/F','B-F bluemin','raw'))
for n,m in zones.items():
    s=m&common
    s=cv2.erode(s.astype(np.uint8),np.ones((7,7),np.uint8))>0
    r=LB[s].mean()/LF[s].mean(); r2=LR[s].mean()/LF[s].mean()
    bb=(B[...,2]-B[...,0])[s].mean()-(F[...,2]-F[...,0])[s].mean()
    d1=np.abs(bl(LB)-bl(LF))[s].mean(); d2=np.abs(bl(LR)-bl(LF))[s].mean()
    print('%-36s %8.3f %8.3f | %+8.3f %8s | %.3f / %.3f  (dots %d)'%(n,r,r2,bb,'',d1,d2,s.sum()))
