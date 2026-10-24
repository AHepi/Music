import numpy as np, cv2, json
K='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
B=K+'kits/weathering/harness/baseline/maps/'
P=K+'street_wet/grime_and_growth/integrated/plates/street/'
def load(p): return cv2.imread(p)[...,::-1].astype(np.float32)/255
b=load(P+'final_main_A_wet_base.png'); k=load(P+'final_main_A_wet_kit.png')
hsv=cv2.cvtColor((k*255).astype(np.uint8),cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
H=hsv[...,0]/255*360; S=hsv[...,1]/255
d=np.abs(k-b).max(axis=2)
green=(k[...,1]>k[...,0]*1.08)&(k[...,1]>k[...,2]*1.15)&(S>0.3)&(d>0.04)&(H>60)&(H<170)
h,w=green.shape; green[:int(h*0.55)]=False
puddle=cv2.imread(B+'puddle_main_wet.png',cv2.IMREAD_UNCHANGED)[...,2]>32768
puddle=cv2.resize(puddle.astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)>0
# green blobs -> connected components
n,lab,stats,cent=cv2.connectedComponentsWithStats(green.astype(np.uint8),connectivity=8)
blobs=[(i,stats[i,4],cent[i]) for i in range(1,n) if stats[i,4]>=25]
inp=0
for i,a,c in blobs:
    x,y=int(c[0]),int(c[1])
    if puddle[min(h-1,y),min(w-1,x)]: inp+=1
# puddle share of road area in the lower 45% (ground), road = approx all ground
ground=np.zeros((h,w),bool); ground[int(h*0.55):]=True
print('plants (blobs>=25 dots):',len(blobs),'centres inside a puddle:',inp, round(inp/len(blobs),3))
print('puddle share of lower plate ground:',round(float(puddle[ground].mean()),3))
print('green dots inside puddle',int((green&puddle).sum()),'of',int(green.sum()), round(float((green&puddle).sum()/green.sum()),3))
# lane/crown: zones map. red channel crown? print zone share of green dots
Z=cv2.imread(B+'zones_main_540x960.png',cv2.IMREAD_UNCHANGED)
Zr=cv2.resize(Z,(w,h),interpolation=cv2.INTER_NEAREST)
for c,name in [(2,'R'),(1,'G'),(0,'B')]:
    m=Zr[...,c]>32768
    print('zones channel',name,'share of ground',round(float(m[ground].mean()),3),'green dots in it',round(float((green&m).sum()/green.sum()),3))
print('--- plant blob centres against the zones with the kit limits (footfall>=0.6, crown>=0.7, keepclear>=0.5)')
lim={2:('footfall',0.6),1:('crown',0.7),0:('keepclear',0.5)}
Zf=Zr.astype(np.float32)/65535
for c,(nm,l) in lim.items():
    m=Zf[...,c]>=l
    inz=sum(1 for i,a,cc in blobs if m[min(h-1,int(cc[1])),min(w-1,int(cc[0]))])
    dots=int((green&m).sum())
    print(nm,'zone share of ground',round(float(m[ground].mean()),3),'| blob centres inside',inz,'of',len(blobs),'| green dots inside',dots,round(dots/green.sum(),3))
