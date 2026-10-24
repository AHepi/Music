import cv2, numpy as np, json
exec(open('measure.py').read().split("print('frame mean")[0])
now=load(NOW); ref=load(REF); old=load(OLD)
G=json.load(open(B+'final/facts/facts.json'))['groups']
M={k:idm(v['colour']) for k,v in G.items()}
L=luma(now); H,W=L.shape
# lantern glass: bright pixels in lantern mask
lm=M['lantern']; g=lm&(L>0.6); stats(now,g,'now lantern glass (luma>0.6)')
yy,xx=np.nonzero(g); print('   at',xx.min()/W,xx.max()/W,yy.min()/H,yy.max()/H)
stats(ref,box(ref,0.795,0.665,0.825,0.705),'ref lantern glass box')
# lamp glass: lamp post mask, rows .13-.23, bright
lp=M['lamp post'].copy(); lp[:int(0.13*H)]=False; lp[int(0.235*H):]=False
gl=lp&(L>0.5); stats(now,gl,'now lamp glass (lamp mask, luma>0.5)')
yy,xx=np.nonzero(gl); print('   glass area % frame',100*gl.sum()/(H*W),'box',xx.min()/W,xx.max()/W,yy.min()/H,yy.max()/H)
nm=M['notice']; print('   notice area % frame',100*nm.sum()/(H*W))
# glass luma column profile (vertical gradient)
for a in np.arange(0.14,0.225,0.01):
    m=gl.copy(); m[:int(a*H)]=False; m[int((a+0.01)*H):]=False
    if m.sum(): print(f'   glass rows {a:.2f}-{a+0.01:.2f} luma {L[m].mean():.3f} sd {L[m].std():.3f}')
print('   ref glass vertical profile:')
Lr=luma(ref)
for a in np.arange(0.16,0.225,0.01):
    m=box(ref,0.755,a,0.825,a+0.01); print(f'   ref rows {a:.2f} luma {Lr[m].mean():.3f} sd {Lr[m].std():.3f}')
# drum inside rim: drum mask top rows
dm=M['drum']; yy,xx=np.nonzero(dm); top=yy.min()
for d0,d1 in [(0,8),(8,20),(20,32),(32,45),(45,60)]:
    m=dm.copy(); m[:top+d0]=False; m[top+d1:]=False
    stats(now,m,f'now drum rows top+{d0}..{d1} ({(top+d0)/H:.3f})')
# chair seat: chair mask rows of seat
cm=M['chair']
for a,b in [(0.722,0.730),(0.730,0.740),(0.740,0.750),(0.750,0.760)]:
    m=cm.copy(); m[:int(a*H)]=False; m[int(b*H):]=False; m[:, :int(0.62*W)]=False; m[:, int(0.86*W):]=False
    stats(now,m,f'now chair rows {a}-{b}')
# board crossbar on top, and planks behind notice
bm=M['board']
m=bm.copy(); m[:int(0.44*H)]=False; m[int(0.475*H):]=False; stats(now,m,'now board top bar/cap (0.44-0.475)')
m=bm.copy(); m[:int(0.475*H)]=False; m[int(0.505*H):]=False; m[:, :int(0.71*W)]=False; m[:, int(0.88*W):]=False; stats(now,m,'now board planks above notice')
m=bm.copy(); m[:int(0.52*H)]=False; m[int(0.66*H):]=False; m[:, :int(0.885*W)]=False; stats(now,m,'now board right of notice')
m=bm.copy(); m[:int(0.52*H)]=False; m[int(0.66*H):]=False; m[:, int(0.708*W):]=False; stats(now,m,'now board left of notice (frame+post)')
m=bm.copy(); m[:int(0.66*H)]=False; stats(now,m,'now board below 0.66 (posts, bottom rail)')
stats(ref,box(ref,0.915,0.45,0.945,0.62),'ref board right of notice')
stats(ref,box(ref,0.76,0.405,0.90,0.45),'ref board planks above notice')
# lamp post base behind chair
m=M['lamp post'].copy(); m[:int(0.66*H)]=False; stats(now,m,'now lamp-post base below board'); yy,xx=np.nonzero(m); print('   box',xx.min()/W,xx.max()/W,yy.min()/H,yy.max()/H,'area%',100*m.sum()/(H*W))
# right wall orange patch
rest=np.ones_like(L,bool)
for k in M: rest&=~M[k]
m=rest.copy(); m[:, :int(0.93*W)]=False; m[:int(0.5*H)]=False; m[int(0.8*H):]=False
hsv=cv2.cvtColor((now*255).astype(np.uint8),cv2.COLOR_RGB2HSV)
warm=m&(L>0.3)&(now[...,0]-now[...,2]>0.25)
yy,xx=np.nonzero(warm); print('right-strip warm patch px',warm.sum(),'box',xx.min()/W,xx.max()/W,yy.min()/H,yy.max()/H)
stats(now,warm,'now right-wall warm patch')
