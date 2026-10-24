import numpy as np, cv2, json
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
NC='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p,size=None):
    im=Image.open(p).convert('RGB')
    if size: im=im.resize(size,Image.LANCZOS)
    return np.asarray(im).astype(np.float32)
W,H=1080,1920
z=1.08; s=1080/1536*z
M=np.array([[s,0,540-1536/2*s],[0,s,960-2730/2*s]],np.float32)
def tofilm(a): return cv2.warpAffine(a,M,(1080,1920))
ims={'plate':tofilm(load(P+'people-test-plate.jpg')),'painting':tofilm(load(P+'people-test-painting.png')),'state picture':tofilm(load(P+'people-test-painting-state.png')),
     'painted film 1.0 s':load(D+'pf/f031.png'),'painted film 3.0 s':load(D+'pf/f091.png'),'silhouette film 1.0 s':load(D+'sf/f031.png'),'notice corner painting':load(NC+'notice-corner-painted.jpg',(1080,1920))}
std=Image.open('/home/user/Music/austerity-explainer/experiments/32 Notice corner - film frames at 1, 4.5 and 9.5 seconds.jpg').convert('RGB')
w,h=std.size; ims['notice corner film 1 s (small copy)']=np.asarray(std.crop((0,0,w//3-2,h)).resize((1080,1920),Image.LANCZOS)).astype(np.float32)
# ground = lower 45% of the frame
ground=np.zeros((H,W),bool); ground[int(0.55*H):,:]=True
for n,a in ims.items():
    R,G,B=a[...,0],a[...,1],a[...,2]; Lm=0.2126*R+0.7152*G+0.0722*B
    warm=(R-B>18)&(Lm>45)
    hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV)
    print('%-36s warm-lit share of frame %.1f%%, of ground %.1f%%; brightest 1%% L %.0f; mean L %.1f; blue minus red overall %.1f'%(n,100*warm.mean(),100*warm[ground].mean(),np.percentile(Lm,99),Lm.mean(),(B-R).mean()))
    vis=np.where(warm[...,None],a,a*0.25).clip(0,255).astype(np.uint8)
    Image.fromarray(vis).resize((270,480)).save(D+'warm-%s.png'%n.replace(' ','-').replace('(','').replace(')',''))
