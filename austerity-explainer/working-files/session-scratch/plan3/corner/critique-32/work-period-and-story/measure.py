import numpy as np, json
from PIL import Image
F='../../final/'
im=np.asarray(Image.open(F+'composed-end-5.png').convert('RGB')).astype(np.float32)/255
ids=np.asarray(Image.open(F+'facts5/ids.png').convert('RGB'))
facts=json.load(open(F+'facts5/facts.json'))
H,W,_=im.shape
print('ids size', ids.shape, 'img', im.shape)
lum=lambda a: 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def sat(a):
    mx=a.max(-1); mn=a.min(-1); return np.where(mx>0,(mx-mn)/np.maximum(mx,1e-6),0)
def hue(rgb):
    import colorsys; return colorsys.rgb_to_hsv(*rgb)[0]*360
def region(name,x0,y0,x1,y1,mask=None):
    r=im[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
    m=np.ones(r.shape[:2],bool) if mask is None else mask[int(y0*H):int(y1*H), int(x0*W):int(x1*W)]
    px=r[m]
    if len(px)==0: print(name,'empty'); return
    L=lum(px); s=sat(px)
    mean=px.mean(0)
    print(f'{name}: n={len(px)} lum mean {L.mean():.3f} p10 {np.percentile(L,10):.3f} p90 {np.percentile(L,90):.3f} max {L.max():.3f} rgb {tuple((mean*255).astype(int))} sat {s.mean():.2f} hue {hue(mean):.0f} R-B {(px[:,0]-px[:,2]).mean():+.2f}')
    return px
def idmask(group):
    c=facts['groups'][group]['colour']
    return np.all(ids==np.array(c),axis=-1)
print('frame mean lum', lum(im).mean())
# notice
region('notice paper (mask)',0,0,1,1,idmask('notice'))
# corner lamp glass: find rows
lp=idmask('lamp post')
region('lamp post all',0,0,1,1,lp)
# corner lamp glass region, bright part of lamp post mask in top
m=lp.copy(); m[int(0.30*H):]=False
px=region('lamp head (mask, top 0.30)',0,0,1,1,m)
# row profile of lamp glass bright pixels
for y in np.arange(0.20,0.30,0.01):
    r=im[int(y*H):int((y+0.01)*H), int(0.78*W):int(0.92*W)]
    mm=m[int(y*H):int((y+0.01)*H), int(0.78*W):int(0.92*W)]
    p=r[mm]; 
    if len(p): 
        L=lum(p); b=p[L>0.25]
        if len(b): print(f'  row {y:.2f}: bright n={len(b)} lum {lum(b).mean():.3f} sd {lum(b).std():.3f} rgb {tuple((b.mean(0)*255).astype(int))} sat {sat(b).mean():.2f}')
ll=idmask('left lamp'); region('left lamp (mask)',0,0,1,1,ll)
mb=ll & (lum(im)>0.3); region('left lamp bright part',0,0,1,1,mb)
# street lamp 3 at 0.419,0.41: not a group; take bright pixels in a box
box=np.zeros((H,W),bool); box[int(0.395*H):int(0.425*H), int(0.405*W):int(0.435*W)]=True
region('gas_lamp_3 bright',0,0,1,1,box & (lum(im)>0.3))
# lantern
lt=idmask('lantern'); region('lantern (mask)',0,0,1,1,lt)
region('lantern bright part (>0.45)',0,0,1,1,lt&(lum(im)>0.45))
# chair
ch=idmask('chair'); region('chair (mask)',0,0,1,1,ch)
# drum mouth
dm=idmask('drum'); mouth=dm.copy(); mouth[:int(0.625*H)]=False; mouth[int(0.66*H):]=False
region('drum top band 0.625-0.66 (mask)',0,0,1,1,mouth)
mouth2=dm.copy(); mouth2[:int(0.632*H)]=False; mouth2[int(0.648*H):]=False; mouth2[:, :int(0.47*W)]=False; mouth2[:, int(0.66*W):]=False
region('drum mouth inside 0.632-0.648',0,0,1,1,mouth2)
region('drum body',0,0,1,1,dm & (np.arange(H)[:,None]>0.67*H))
# sacks
region('sacks (mask)',0,0,1,1,idmask('sacks'))
region('handcart (mask)',0,0,1,1,idmask('handcart'))
region('dustbins (mask)',0,0,1,1,idmask('dustbins'))
region('gates (mask)',0,0,1,1,idmask('gates'))
region('doorway behind gates',0.575,0.415,0.635,0.465)
# left terrace brick
region('left terrace brick sample',0.09,0.40,0.18,0.48)
region('left near house brick',0.0,0.55,0.07,0.70)
region('sky top', 0.1,0.02,0.6,0.12)
region('sky low', 0.1,0.15,0.4,0.25)
