import numpy as np, sys
from PIL import Image
def lum(path):
    a=np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)/255.0
    # sRGB -> linear-ish? the measurement script loads Non-Color pixels of the saved file: i.e. the sRGB-encoded values directly
    return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2], a
def gblur(a,sigma):
    r=int(3*sigma+1); x=np.arange(-r,r+1); k=np.exp(-x*x/(2*sigma*sigma)); k/=k.sum()
    p=np.pad(a,((r,r),(0,0)),mode='reflect'); a=sum(k[i]*p[i:i+a.shape[0]] for i in range(2*r+1))
    p=np.pad(a,((0,0),(r,r)),mode='reflect'); return sum(k[i]*p[:,i:i+a.shape[1]] for i in range(2*r+1))
def ssim_map(la,lb,sb=12.0,sw=6.0):
    A,B=gblur(la,sb),gblur(lb,sb)
    mu_a,mu_b=gblur(A,sw),gblur(B,sw)
    va=gblur(A*A,sw)-mu_a**2; vb=gblur(B*B,sw)-mu_b**2; cab=gblur(A*B,sw)-mu_a*mu_b
    c1,c2=0.01**2,0.03**2
    return ((2*mu_a*mu_b+c1)*(2*cab+c2))/((mu_a**2+mu_b**2+c1)*(va+vb+c2)), A, B
if __name__=='__main__':
    before=sys.argv[1]; new=sys.argv[2]; out=sys.argv[3]; box=[int(v) for v in sys.argv[4:8]]
    lb,_=lum(before); ln,_=lum(new)
    s,A,B=ssim_map(ln,lb)
    print('global ssim', s.mean())
    x0,y0,x1,y1=box
    print('box ssim', s[y0:y1,x0:x1].mean())
    # composite: before blurred, new blurred, diff (new-before) signed, ssim map
    def g(a): return np.clip(a/0.8,0,1)
    d=(B-A)  # new - before (A=blur(new) since first arg is new)
    # NOTE ssim_map(la=new, lb=before): A=blur(new), B=blur(before)
    dd=(A-B)
    sub=lambda z: z[y0:y1,x0:x1]
    h,w=sub(A).shape
    img=np.zeros((h,w*4,3),np.float32)
    img[:,:w]=g(sub(B))[...,None]; img[:,w:2*w]=g(sub(A))[...,None]
    dv=np.clip(sub(dd)/0.25,-1,1)
    img[:,2*w:3*w,0]=np.clip(dv,0,1); img[:,2*w:3*w,2]=np.clip(-dv,0,1); img[:,2*w:3*w,1]=0.15
    sm=np.clip(sub(s),0,1); img[:,3*w:]=sm[...,None]
    im=Image.fromarray((img*255).astype(np.uint8)); im=im.resize((im.width//3,im.height//3)); im.save(out,quality=85)
    print('saved',out,im.size)
