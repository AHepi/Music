exec(open('m1.py').read().split("print('frame mean")[0])
import cv2
# near-white: luma > 0.8 or all channels > 0.85
nw=(lum>0.80)
n,lab,st,cen=cv2.connectedComponentsWithStats(nw.astype(np.uint8),8)
print('near-white (luma>0.80) total px', nw.sum(), 'frac', nw.sum()/(H*W))
names={tuple(v):k for k,v in cols.items()}
def who(m):
    c=ids[m]; out={}
    for k,v in cols.items():
        s=(np.abs(c-np.array(v)).max(-1)<=2).sum()
        if s: out[k]=int(s)
    return out
for i in np.argsort(-st[:,4])[:15]:
    if i==0: continue
    x,y,w,h,a=st[i]
    if a<3: continue
    print(f'  comp area={a:5d} box=({x/W:.3f},{y/H:.3f})-({(x+w)/W:.3f},{(y+h)/H:.3f}) maxluma={lum[lab==i].max():.3f} on={who(lab==i)}')
# brightest 0.5% outside notice
nm=mask('notice')
thr=np.percentile(lum[~nm],99.5); print('99.5 pct outside notice', thr)
# very dark masses: luma<0.05, blurred
dk=(cv2.blur(lum,(9,9))<0.05)
n,lab,st,cen=cv2.connectedComponentsWithStats(dk.astype(np.uint8),8)
print('dark (blur9 luma<0.05) total frac', dk.sum()/(H*W))
for i in np.argsort(-st[:,4])[:10]:
    if i==0: continue
    x,y,w,h,a=st[i]
    print(f'  dark comp area={a/(H*W)*100:.2f}% box=({x/W:.3f},{y/H:.3f})-({(x+w)/W:.3f},{(y+h)/H:.3f}) mean={lum[lab==i].mean():.3f} on={who(lab==i)}')
# right wall leak region
rep('wall right of board 0.93-1.0,0.54-0.80', box(0.93,0.54,1.0,0.80)&~mask('board'))
rep('  same in end4', box(0.93,0.54,1.0,0.80)&~mask('board'), im4)
