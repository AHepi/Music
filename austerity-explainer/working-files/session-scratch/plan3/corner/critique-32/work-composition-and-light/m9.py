from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
def conspicuity(im):
    # Itti-Koch-lite at phone scale: work on a 270x480 copy
    small=cv2.resize(im,(270,480),interpolation=cv2.INTER_AREA)
    L=luma(small); rg=small[...,0]-small[...,1]; by=small[...,2]-(small[...,0]+small[...,1])/2
    maps=[]
    for ch,wt in ((L,1.0),(rg,0.5),(by,0.5)):
        acc=np.zeros_like(L)
        for c,s in ((2,8),(2,16),(4,16),(4,32)):
            a=cv2.GaussianBlur(ch,(0,0),c); b=cv2.GaussianBlur(ch,(0,0),s)
            acc+=np.abs(a-b)
        acc/=acc.max()+1e-9; maps.append(wt*acc)
    S=sum(maps); S=cv2.GaussianBlur(S,(0,0),3)
    return cv2.resize(S,(im.shape[1],im.shape[0]))
def peaks(S,label,n=6):
    s=S.copy(); H,W=s.shape; out=[]
    for i in range(n):
        y,x=np.unravel_index(s.argmax(),s.shape); out.append((x/W,y/H,s[y,x]))
        cv2.circle(s,(x,y),int(0.07*W),0,-1)
    print(label,'peaks (across, down, strength):',' | '.join(f'{a:.2f},{b:.2f} {c:.2f}' for a,b,c in out))
    return out
for im,l in ((v4,'v4'),(v5,'v5'),(ref,'ref')):
    S=conspicuity(im); peaks(S,l)
    if l!='ref':
        tot=S.sum()
        res={k:S[idm(k)].sum()/tot*100 for k in ['notice','board','drum','chair','lantern','pail','lamp post','left lamp','handcart','winding wheels','gates','chimney']}
        print('   share of conspicuity:',', '.join(f'{k} {v:.1f}%' for k,v in sorted(res.items(),key=lambda t:-t[1])))
        print('   per-pixel mean (x frame mean):',', '.join(f'{k} {S[idm(k)].mean()/S.mean():.2f}' for k in ['notice','drum','chair','lantern','lamp post','pail','left lamp','gates']))
    cv2.imwrite(f'conspicuity_{l}.png',(np.clip(S/S.max(),0,1)*255).astype(np.uint8)[::4,::4])
