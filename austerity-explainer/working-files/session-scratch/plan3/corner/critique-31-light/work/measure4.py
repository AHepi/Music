import cv2, numpy as np
exec(open('measure.py').read().split("print('frame mean")[0])
IM={'ref':load(REF),'old':load(OLD),'now':load(NOW)}
print('grid of mean luma / (R-B), rows = down bands, cols = across thirds')
for k,im in IM.items():
    L=luma(im); h,w=L.shape
    print(k)
    for a,b in [(0,.33),(.33,.5),(.5,.67),(.67,.83),(.83,1)]:
        row=[]
        for c,d in [(0,.33),(.33,.5),(.5,.67),(.67,.9),(.9,1)]:
            s=(slice(int(a*h),int(b*h)),slice(int(c*w),int(d*w)))
            row.append(f'{L[s].mean():.2f}/{(im[s][...,0]-im[s][...,2]).mean():+.2f}')
        print(f'  down {a:.2f}-{b:.2f}: '+'  '.join(row))
    # share of frame strongly warm & lit
    warm=(im[...,0]-im[...,2]>0.25)&(L>0.35)
    cool=(im[...,2]-im[...,0]>0.02)
    print(f'  strongly warm & lit (R-B>0.25, luma>0.35): {100*warm.mean():.1f}% ; cooler-than-neutral pixels (B>R): {100*cool.mean():.1f}% ; below the sky (down>0.5) B>R: {100*cool[int(.5*h):].mean():.1f}%')
