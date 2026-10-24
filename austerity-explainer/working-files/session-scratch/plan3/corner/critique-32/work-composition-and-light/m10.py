from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
L5=luma(v5)
dr=idm('drum')
# find the mouth: within drum mask, rows 0.625-0.65
for lab,b in [('lip+mouth',(0.44,0.625,0.70,0.650)),('mouth inner (0.47-0.66, 0.634-0.646)',(0.47,0.634,0.66,0.646)),('lip top rows (0.626-0.632)',(0.45,0.626,0.68,0.632))]:
    m=dr&boxm(v5.shape,*b)
    print(stats(v4,m,'v4 '+lab)); print(stats(v5,m,'v5 '+lab))
# texture inside the mouth: local sd after removing gradient
m=dr&boxm(v5.shape,0.48,0.636,0.65,0.645)
for im,l in ((v4,'v4'),(v5,'v5')):
    L=luma(im); hp=L-cv2.GaussianBlur(L,(0,0),4)
    print(l,'mouth fine-texture sd %.4f'%hp[m].std())
dw=dr&boxm(v5.shape,0.47,0.66,0.69,0.80)
print(stats(v5,dw,'v5 drum outer wall')); 
print(stats(ref,boxm(ref.shape,0.515,0.700,0.665,0.790),'ref drum outer wall'))
print(stats(ref,boxm(ref.shape,0.52,0.653,0.67,0.668),'ref drum rim+inside'))
# drum size vs notice size on screen
ys,xs=np.where(dr); print('drum box %.3f-%.3f x %.3f-%.3f, area %.2f%%'%(xs.min()/1080,xs.max()/1080,ys.min()/1920,ys.max()/1920,dr.sum()/dr.size*100))
nm=idm('notice'); print('notice area %.2f%%'%(nm.sum()/nm.size*100))
