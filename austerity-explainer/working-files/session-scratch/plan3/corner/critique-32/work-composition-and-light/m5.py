from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
R={
 'sky top-left (0-0.4, 0-0.2)':(0,0,0.4,0.2),
 'left houses (0-0.45, 0.2-0.5)':(0,0.2,0.45,0.5),
 'left road far (0-0.45,0.5-0.62)':(0,0.5,0.45,0.62),
 'road beside drum (0.25-0.45,0.62-0.78)':(0.25,0.62,0.45,0.78),
 'near-left road (0-0.33,0.83-1)':(0,0.83,0.33,1.0),
 'fg pavement (0.45-1,0.88-1)':(0.45,0.88,1.0,1.0),
 'right wall strip (0.92-1,0.3-0.7)':(0.92,0.3,1.0,0.7),
 'colliery doorway (0.57-0.64,0.41-0.47)':(0.57,0.41,0.64,0.47),
}
REFR=dict(R)
REFR['colliery doorway (0.57-0.64,0.41-0.47)']=(0.565,0.40,0.645,0.47)
for k,b in R.items():
    print('--',k)
    print('  ',stats(v4,boxm(v4.shape,*b),'v4'))
    print('  ',stats(v5,boxm(v5.shape,*b),'v5'))
    print('  ',stats(ref,boxm(ref.shape,*REFR[k]),'ref'))
for im,l in ((v4,'v4'),(v5,'v5'),(ref,'ref')):
    H=im.shape[0]; low=im[H//2:]
    cool=(low[...,2]>low[...,0]).mean()*100
    print(f'{l}: below mid-frame, {cool:.1f}% of pixels bluer than red; mean R-B {(low[...,0]-low[...,2]).mean():+.3f}')
