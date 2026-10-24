exec(open('m1.py').read().split("print('frame mean")[0])
lm=mask('lantern')
gl=lm&(lum>0.45)
rep('lantern bright part (glass)',gl); rep('  same px in end4',gl,im4)
ys,xs=np.nonzero(gl); print('glass box', xs.min()/W, ys.min()/H, xs.max()/W, ys.max()/H)
# brightest pixels in lantern
v=lum[lm]; print('lantern max luma', v.max())
# corner lamp glass: lamp post mask in head region
lp=mask('lamp post')&box(0.74,0.19,0.90,0.30)
g2=lp&(lum>0.35); rep('corner lamp glass', g2); rep('  end4 (lamp was elsewhere)', g2, im4)
ys,xs=np.nonzero(g2); print('lamp glass box', xs.min()/W, ys.min()/H, xs.max()/W, ys.max()/H, 'frac', g2.sum()/(H*W))
# per row luma of lamp glass
for yy in range(ys.min(), ys.max()+1, 8):
    row=g2[yy]; 
    if row.sum(): print(f'  {yy/H:.3f}', L(im[yy,row]).mean().round(3), L(im[yy,row]).std().round(3))
# far lamps
for nm_,bx in {'left lamp head (y45)':(0.33,0.37,0.39,0.42),'street lamp gas_lamp_3 (y53)':(0.39,0.38,0.44,0.43)}.items():
    m=box(*bx)&(lum>0.35); rep(nm_, m)
    ys,xs=np.nonzero(m); 
    if len(xs): print('   box', xs.min()/W, ys.min()/H, xs.max()/W, ys.max()/H)
# doorway
door=box(0.575,0.415,0.64,0.468)
rep('colliery doorway', door); rep('  end4', door, im4)
rep('gates mask', mask('gates'))
