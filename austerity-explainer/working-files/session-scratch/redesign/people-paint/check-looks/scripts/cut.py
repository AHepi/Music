import numpy as np, cv2
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
z=1.08; s=1080/1536*z
M=np.array([[s,0,540-1536/2*s],[0,s,960-2730/2*s]],np.float32)
mask=np.asarray(Image.open(P+'people-test-painting-state-mask.png').convert('L')).astype(np.float32)
mf=cv2.warpAffine(mask,M,(1080,1920))
print('state mask in film frame: fully on %.1f%%, partly %.1f%%'%(100*(mf>250).mean(),100*((mf>5)&(mf<=250)).mean()))
out=(mf<2)
inside=(mf>250)
def L(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
a=load(D+'pf/f059.png'); b=load(D+'pf/f060.png'); c=load(D+'pf/f061.png'); d=load(D+'pf/f062.png')
for lab,x,y in [('1.933->1.967 (normal)',a,b),('1.967->2.000 (the cut)',b,c),('2.000->2.033 (normal)',c,d)]:
    dd=np.abs(L(y)-L(x))
    print('%-24s change outside mask %.2f, inside mask %.2f; mean L outside %.1f->%.1f inside %.1f->%.1f'%(lab,dd[out].mean(),dd[inside].mean(),L(x)[out].mean(),L(y)[out].mean(),L(x)[inside].mean(),L(y)[inside].mean()))
# outside-mask change after cut, large-scale (blurred) to catch light pool changes
dl=cv2.GaussianBlur(L(c)-L(b),(0,0),15)
o=dl.copy(); o[~out]=0
print('largest blurred brightness change outside mask at the cut: +%.1f / %.1f levels'%(o.max(),o.min()))
ys,xs=np.unravel_index(np.argmax(np.abs(o)),o.shape); print('  at x=%d y=%d'%(xs,ys))
vis=np.clip(128+4*dl,0,255).astype(np.uint8)
vis=cv2.cvtColor(vis,cv2.COLOR_GRAY2RGB); vis[(mf>128)]=(vis[(mf>128)]*0.5+np.array([0,0,120])).astype(np.uint8)
Image.fromarray(vis).resize((360,640)).save(D+'cut-change-map.png')
