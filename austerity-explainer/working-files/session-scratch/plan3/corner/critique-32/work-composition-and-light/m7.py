from common import *
v5=load(V5); ref=load(REF)
L=luma(v5); S=sat(v5)
# lamp glass: pixels in lamp post mask in head region that are bright (glass)
lm=idm('lamp post')&boxm(v5.shape,0.74,0.20,0.88,0.30)
glass=lm&(L>0.3)
ys,xs=np.where(glass); print('glass box %.3f-%.3f across %.3f-%.3f down, %.3f%% of frame'%(xs.min()/1080,xs.max()/1080,ys.min()/1920,ys.max()/1920,glass.sum()/L.size*100))
print(stats(v5,glass,'v5 lamp glass'))
for y in range(ys.min(),ys.max()+1,12):
    row=glass[y:y+12]
    if row.sum()<20: continue
    l=L[y:y+12][row]
    print('  rows %.3f down: mean %.3f  sd %.3f  min %.3f max %.3f'%(y/1920,l.mean(),l.std(),l.min(),l.max()))
h=cv2.cvtColor((v5*255).astype(np.uint8),cv2.COLOR_RGB2HSV)
print('lamp glass hue (deg) %.0f'%(h[...,0][glass].mean()*2))
nm=idm('notice'); print('notice hue %.0f'%(h[...,0][nm & (L>0.6)].mean()*2))
# ref lamp glass
rg=boxm(ref.shape,0.745,0.165,0.83,0.225)&(luma(ref)>0.4)
print(stats(ref,rg,'ref lamp glass'))
# left lamps glass
ll=idm('left lamp')&(L>0.3); print(stats(v5,ll,'v5 new left lamp glass'))
g3=boxm(v5.shape,0.405,0.395,0.43,0.425)&(L>0.3); print(stats(v5,g3,'v5 street lamp 3 glass'))
ys,xs=np.where(idm('left lamp')); print('new left lamp box %.3f-%.3f across, %.3f-%.3f down'%(xs.min()/1080,xs.max()/1080,ys.min()/1920,ys.max()/1920))
ys,xs=np.where(g3|(boxm(v5.shape,0.40,0.38,0.44,0.50)&(L<0.06))); 
rl=boxm(ref.shape,0.20,0.345,0.27,0.41)&(luma(ref)>0.45); print(stats(ref,rl,'ref left lamp glass'))
