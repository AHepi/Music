from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
L5=luma(v5); L4=luma(v4)
ch=idm('chair'); nm=idm('notice'); bd=idm('board'); dr=idm('drum'); pl=idm('pail'); ln=idm('lantern')
props=ch|nm|bd|dr|pl|ln|idm('lamp post')
ring=(cv2.dilate(ch.astype(np.uint8),np.ones((25,25),np.uint8))>0)&~ch
for name,sub in [('chair back over notice',boxm(v5.shape,0.70,0.60,0.89,0.66)),('chair seat',boxm(v5.shape,0.61,0.715,0.86,0.77)),('chair legs',boxm(v5.shape,0.60,0.77,0.90,0.88))]:
    m=ch&sub; r=ring&sub
    for im,L,l in ((v4,L4,'v4'),(v5,L5,'v5')):
        print(f'{l} {name:24s} chair L {L[m].mean():.3f} (p95 {np.percentile(L[m],95):.3f}) | what is right around it L {L[r].mean():.3f} | ratio {L[m].mean()/L[r].mean():.2f}  chair RGB {tuple(int(x) for x in v5[m].mean(0)*255) if l=="v5" else tuple(int(x) for x in v4[m].mean(0)*255)} around RGB {tuple(int(x) for x in (v5 if l=="v5" else v4)[r].mean(0)*255)}')
# chair's brightest 5% vs paper median
print('v5 chair p95 %.3f, notice paper median %.3f'%(np.percentile(L5[ch],95), np.median(L5[nm&~ch])))
# ref chair vs surroundings
rc=boxm(ref.shape,0.71,0.70,0.93,0.745)&(luma(ref)>0.5)
print(stats(ref,rc,'ref chair seat (bright part)'))
rleg=boxm(ref.shape,0.72,0.76,0.92,0.83); Lr=luma(ref)
print('ref chair legs region L mean %.3f p95 %.3f'%(Lr[rleg].mean(),np.percentile(Lr[rleg],95)))
