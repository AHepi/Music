# Measures brightness of named regions in the checkout stills (fractions of frame).
import sys, numpy as np
from PIL import Image
def lum(p):
    a=np.asarray(Image.open(p).convert('RGB')).astype(float)/255
    return a, 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
regions={
 'title band 0.06-0.90 x 0.05-0.22':(0.06,0.90,0.05,0.22),
 'beam slab left 0-0.45 x 0.06-0.12':(0.0,0.45,0.065,0.12),
 'lit tube left 0.03-0.24 x 0.30-0.32':(0.03,0.24,0.300,0.315),
 'bill words 0.52-0.80 x 0.47-0.57':(0.52,0.80,0.47,0.57),
 'bill white bottom 0.52-0.80 x 0.58-0.62':(0.52,0.80,0.58,0.62),
 'checkout sign 0.46-0.80 x 0.28-0.32':(0.46,0.80,0.28,0.32),
 'petrol fascia 0.05-0.50 x 0.40-0.42':(0.05,0.50,0.395,0.425),
 'bottom quarter 0-1 x 0.78-1.0':(0,1,0.78,1.0),
 'belt near 0.42-0.95 x 0.80-1.0':(0.42,0.95,0.8,1.0),
 'whole':(0,1,0,1),
}
for p in sys.argv[1:]:
    a,L=lum(p); h,w=L.shape
    print(p.split('/')[-1], w,h)
    for k,(x0,x1,y0,y1) in regions.items():
        r=L[int(y0*h):int(y1*h), int(x0*w):int(x1*w)]
        print(f'  {k:45s} mean {r.mean():.3f}  p95 {np.percentile(r,95):.3f} max {r.max():.3f}')
