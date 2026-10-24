from common import *
v5=load(V5); v4=load(V4); L5=luma(v5); L4=luma(v4)
lp=idm('lamp post'); ys,xs=np.where(lp)
print('lamp post visible: lowest pixel %.3f down; pixels below 0.60: %d'%(ys.max()/1920,(ys>0.60*1920).sum()))
low=lp&boxm(v5.shape,0,0.60,1,1); 
if low.sum(): yy,xx=np.where(low); print('  visible low part box %.3f-%.3f across %.3f-%.3f down'%(xx.min()/1080,xx.max()/1080,yy.min()/1920,yy.max()/1920), 'mean L %.3f'%L5[low].mean())
# old black foot region in v4
r=boxm(v5.shape,0.82,0.68,0.89,0.74)
print('old foot region 0.82-0.89,0.68-0.74: v4 L %.3f (%.0f%% <0.07)  v5 L %.3f (%.0f%% <0.07)'%(L4[r].mean(),(L4[r]<0.07).mean()*100,L5[r].mean(),(L5[r]<0.07).mean()*100))
# wall patch
r=boxm(v5.shape,0.93,0.54,1.0,0.80)
print('old wall patch 0.93-1.0,0.54-0.80: v4 L %.3f R-B %+.3f | v5 L %.3f R-B %+.3f'%(L4[r].mean(),rb(v4)[r].mean(),L5[r].mean(),rb(v5)[r].mean()))
# lantern glass
ln=idm('lantern'); g=ln&(L5>0.35)
print(stats(v5,g,'v5 lantern glass (L>0.35)'))
g4=ln&(L4>0.35); print(stats(v4,g4,'v4 lantern bright part'))
fr=ln&(L5<=0.35); print(stats(v5,fr,'v5 lantern frame'))
# seat pool under lantern
seat=idm('chair')&boxm(v5.shape,0.66,0.725,0.85,0.765)
print(stats(v5,seat,'v5 chair seat top'))
# notice vs chair back edge
nm=idm('notice'); ch=idm('chair')
edge_n=nm&(cv2.dilate(ch.astype(np.uint8),np.ones((7,7),np.uint8))>0)&~ch
edge_c=ch&(cv2.dilate(nm.astype(np.uint8),np.ones((7,7),np.uint8))>0)
print('along the chair-notice edge: paper L %.3f RGB %s | chair L %.3f RGB %s'%(L5[edge_n].mean(),tuple(int(x) for x in v5[edge_n].mean(0)*255),L5[edge_c].mean(),tuple(int(x) for x in v5[edge_c].mean(0)*255)))
# handcart / dustbins overlap
hc=idm('handcart'); db=idm('dustbins')
ys,xs=np.where(db); print('dustbins visible box %.3f-%.3f x %.3f-%.3f'%(xs.min()/1080,xs.max()/1080,ys.min()/1920,ys.max()/1920))
ys,xs=np.where(hc); print('handcart visible box %.3f-%.3f x %.3f-%.3f'%(xs.min()/1080,xs.max()/1080,ys.min()/1920,ys.max()/1920))
