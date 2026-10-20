# What this does (plain words): finds every rivet in the reference colour picture by sliding a picture of one rivet over the whole tile
# (wrapping round the edges) and keeping the places where it fits best. Analysis only: it reads the reference. Writes rivets_found.json
# (centre x, centre y, match score) and an overlay picture for checking by eye.
import cv2, numpy as np, json
PROC='proc-work'
c=cv2.imread(PROC+'/reference/metal/colour.png')
H,W=c.shape[:2]
P=64
cp=cv2.copyMakeBorder(c,P,P,P,P,cv2.BORDER_WRAP)
g=cv2.cvtColor(cp,cv2.COLOR_BGR2GRAY)
def lap(img): 
    return cv2.GaussianBlur(img.astype(np.float32),(0,0),1.0)
gf=lap(g)
cx,cy=113,223
R=26
tmpl=gf[cy+P-R:cy+P+R+1,cx+P-R:cx+P+R+1]
# circular weight so that the surroundings (rust, plate) matter less than the rivet disc
yy,xx=np.mgrid[-R:R+1,-R:R+1]
mask=((xx**2+yy**2)<=22**2).astype(np.float32)
res=cv2.matchTemplate(gf,tmpl,cv2.TM_CCORR_NORMED,mask=mask) if False else cv2.matchTemplate(gf,tmpl,cv2.TM_CCOEFF_NORMED)
pts=[]
r2=res.copy()
while True:
    mn,mx,mnl,mxl=cv2.minMaxLoc(r2)
    if mx<0.45: break
    x,y=mxl
    px,py=x+R-P,y+R-P
    pts.append((px,py,float(mx)))
    cv2.circle(r2,(x,y),30,-1,-1)
# keep those with centre inside the tile range [-10, W+10], then fold into 0..W
out=[]
for px,py,s in pts:
    if -R<=px<W+R and -R<=py<H+R:
        out.append((px,py,s))
# deduplicate wrapped copies: fold to 0..W and merge if within 6 px
folded=[]
for px,py,s in out:
    fx,fy=px%W,py%H
    if any(min(abs(fx-a),W-abs(fx-a))<8 and min(abs(fy-b),H-abs(fy-b))<8 for a,b,_ in folded): continue
    folded.append((fx,fy,s))
print(len(folded))
vis=c.copy()
for x,y,s in folded:
    for dx in (-W,0,W):
        for dy in (-H,0,H):
            cv2.circle(vis,(int(x+dx),int(y+dy)),21,(0,255,0),2)
    cv2.putText(vis,'%.2f'%s,(int(x)-14,int(y)-24),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
cv2.imwrite('rivets_overlay.png',cv2.resize(vis,(1000,1000),interpolation=cv2.INTER_AREA))
json.dump([[round(x,1),round(y,1),round(s,3)] for x,y,s in sorted(folded,key=lambda t:(t[0],t[1]))],open('rivets_found.json','w'))
for x,y,s in sorted(folded,key=lambda t:(t[0],t[1])): print(round(x),round(y),round(s,2))
