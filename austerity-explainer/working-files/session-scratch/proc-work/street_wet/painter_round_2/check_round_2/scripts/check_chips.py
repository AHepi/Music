"""Checker's own: are the plate's small dark rubbish chips still there in the painting? Own blob finder: dots much darker than their surroundings
(local median over 41 dots), area 6 to 400 dots, on road/gutter/pavement ground (ground labels drawn with props hidden), props' footprint left out.
A plate chip counts as kept if a painting chip centre lies within 7 dots. Chance level = the same test with the painting's chips shifted 40 dots sideways."""
import numpy as np, cv2
RR='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/'
z=np.load(RR+'behind/work/ground_labels_no_props.npz')
ground=z['road']|z['gutter']|z['kerb']|z['pavement']
def lum(p):
    a=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB).astype(np.float32)/255
    return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
P=lum(RR+'plate/lockout_plate_wet_round2.png'); N=lum(RR+'plate/lockout_plate_wet_round2_no_props.png')
prop=cv2.dilate((np.abs(P-N)>0.06).astype(np.uint8),np.ones((31,31),np.uint8))>0
zone=ground&~prop
zone[:1750]=False                      # lower picture only, where chips are big enough to see
zone=cv2.erode(zone.astype(np.uint8),np.ones((9,9),np.uint8))>0
def chips(L):
    med=cv2.medianBlur((np.clip(L,0,1)*255).astype(np.uint8),41).astype(np.float32)/255
    m=((med-L)>0.10)&(L<0.2)&zone
    n,lab,st,cen=cv2.connectedComponentsWithStats(m.astype(np.uint8),connectivity=8)
    keep=[i for i in range(1,n) if 6<=st[i,cv2.CC_STAT_AREA]<=400]
    return np.array([cen[i] for i in keep])
cp=chips(P)
print('plate chips',len(cp))
for name,path in (('front painting','paint/front_painting_final.png'),('first test','../painter_test/pictures/wet_painting_lined_up.png')):
    cf=chips(lum(RR+path))
    def share(a,b,r=7,shift=0):
        if len(a)==0 or len(b)==0: return 0
        b2=b+np.array([shift,0])
        d=np.sqrt(((a[:,None,:]-b2[None,:,:])**2).sum(axis=2)).min(axis=1)
        return float((d<=r).mean())
    print('%-16s chips %4d | plate chips with a painting chip within 7 dots: %.2f | chance (shifted 40 dots): %.2f | painting chips with no plate chip near: %.2f'%(name,len(cf),share(cp,cf),share(cp,cf,shift=40),1-share(cf,cp)))
