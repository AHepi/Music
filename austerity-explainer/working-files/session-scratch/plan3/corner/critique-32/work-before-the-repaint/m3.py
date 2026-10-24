exec(open('m1.py').read().split("print('frame mean")[0])
dm=mask('drum')
top=box(0.44,0.62,0.70,0.652)&dm
b=im[...,2]; r=im[...,0]
disc=top&(b<40/255)&(r>0.35)
rim=top&(lum>0.6)
rep('drum mouth disc',disc); rep('drum rim (luma>0.6)',rim)
ys,xs=np.nonzero(disc); print('disc box', xs.min()/W, ys.min()/H, xs.max()/W, ys.max()/H, 'frac of frame', disc.sum()/(H*W))
# flatness: local std in 5x5 within the disc
import cv2
g=(lum*255).astype(np.float32)
mu=cv2.blur(g,(7,7)); mu2=cv2.blur(g*g,(7,7)); sd=np.sqrt(np.maximum(mu2-mu*mu,0))/255
inner=cv2.erode(disc.astype(np.uint8),np.ones((7,7),np.uint8)).astype(bool)
print('disc local std (7px) median', np.median(sd[inner]), 'p90', np.percentile(sd[inner],90), 'n', inner.sum())
# luma gradient across disc: left/centre/right, top/bottom
for name,(x0,x1) in {'left':(0.46,0.52),'mid':(0.54,0.60),'right':(0.62,0.67)}.items():
    m=inner&box(x0,0,x1,1); print(name, L(im[m]).mean().round(3), (im[m].mean(0)*255).round())
# compare with a reference brazier mouth: reference image
R=np.array(Image.open('/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg').convert('RGB')).astype(float)/255
print('ref size', R.shape)
# what's near notice: notice paper luma
nm=mask('notice'); rep('notice all', nm)
paper=nm&(lum>0.5); rep('notice paper (luma>.5)', paper)
