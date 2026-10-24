import numpy as np, cv2, json
from PIL import Image
A='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
pt=cv2.cvtColor(cv2.imread(A+'people-test-painting.png'),cv2.COLOR_BGR2GRAY)
pl=cv2.cvtColor(cv2.imread(A+'people-test-plate.jpg'),cv2.COLOR_BGR2GRAY)
# painting ink lines: dark thin lines -> blackhat to get dark lines, plus canny
ept=cv2.Canny(cv2.GaussianBlur(pt,(0,0),1.5),20,50)
epl=cv2.Canny(cv2.GaussianBlur(pl,(0,0),1.5),8,24)
dt_pt=cv2.distanceTransform((ept==0).astype(np.uint8),cv2.DIST_L2,5)
dt_pl=cv2.distanceTransform((epl==0).astype(np.uint8),cv2.DIST_L2,5)
names=['man facing','man arms folded','man stooped','man hand on bar','man leaning']+['walker %d'%i for i in range(1,6)]
res={}
print('distance (px at 1536 wide) from the plate figure outline to the nearest edge in the painting; plate-to-plate baseline in brackets')
for n in names:
    m=(np.array(Image.open(O+'masks/'+n.replace(' ','-')+'-visible.png'))>127).astype(np.uint8)
    cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
    pts=np.concatenate([c.reshape(-1,2) for c in cnts])
    # drop points on image border
    d1=dt_pt[pts[:,1],pts[:,0]]; d0=dt_pl[pts[:,1],pts[:,0]]
    h=m.any(1).sum()
    r=dict(points=len(pts),median=float(np.median(d1)),p90=float(np.percentile(d1,90)),within3=float((d1<=3).mean()),within6=float((d1<=6).mean()),base_median=float(np.median(d0)),base_within3=float((d0<=3).mean()),height_px=int(h))
    res[n]=r
    print(f"{n:16s} h={h:4d}  median={r['median']:.1f} p90={r['p90']:.1f}  within 3px={r['within3']*100:.0f}%  within 6px={r['within6']*100:.0f}%   [plate itself: median {r['base_median']:.1f}, within 3px {r['base_within3']*100:.0f}%]")
json.dump(res,open(O+'outline-chamfer.json','w'),indent=1)
