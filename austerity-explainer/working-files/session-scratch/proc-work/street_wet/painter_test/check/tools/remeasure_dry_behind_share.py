# NOTE (plain words): my own re-measure of "how much of the moved view's road wears the film's dry behind painting" (helper: 71 %, counted as road pixels that differ between two stage renders). I use the stage's own colour map of which picture each pixel wears (yellow = the painting, green = the behind painting, blue = the 3D set's own surface), cut to the road by Blender's road mask for the moved camera. Reads pictures only. Run: python3 -I remeasure_dry_behind_share.py
import cv2, numpy as np, json
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_test'
w=cv2.imread(B+'/stage/stills/wet_weights/still-6.00.jpg')
f=json.load(open(B+'/alignment/facts_surfaces_moved/facts.json'))
ids=cv2.cvtColor(cv2.imread(B+'/alignment/facts_surfaces_moved/ids.png'),cv2.COLOR_BGR2RGB).astype(int)
def m(g): return np.abs(ids-np.array(f['groups'][g]['colour'])).sum(axis=2)<24
road=cv2.erode(m('road').astype(np.uint8),np.ones((4,4),np.uint8))>0
pav=cv2.erode((m('pavement')|m('kerb')).astype(np.uint8),np.ones((3,3),np.uint8))>0
b,g,r=[w[:,:,i].astype(int) for i in range(3)]
cls=np.zeros(b.shape,int)
cls[(g>r+15)&(g>b+15)]=1; cls[(b>r+20)&(b>g+10)]=2; cls[(r>b+40)&(g>b+40)&(abs(r-g)<60)]=3
names={0:'other',1:'green = behind painting',2:'blue = own 3D surface',3:'yellow = painting'}
for nm,mask in (('road',road),('pavement and kerb',pav)):
    print(nm,{names[k]:round(float((cls[mask]==k).mean()),3) for k in names})
print('whole frame',{names[k]:round(float((cls==k).mean()),3) for k in names})
