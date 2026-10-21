"""Plate pixels per metre on the ground for the lockout camera (own maths, checked against the earlier study's Blender numbers)."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
w,x,y,z=0.65516,0.753675,-0.039498,-0.034335
n=np.sqrt(w*w+x*x+y*y+z*z); w,x,y,z=w/n,x/n,y/n,z/n
R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
C=np.array([-1.0,1.2,1.69709])
f=(2730/2)/np.tan(np.radians(22.0))
def project(P):
    d=np.asarray(P,float)-C
    cam=R.T@d            # camera coords (x right, y up, -z forward)
    zc=-cam[2]
    return 768+f*cam[0]/zc, 1365-f*cam[1]/zc, zc
def ground_point(px,py,gz=0.0):
    # ray through pixel -> ground plane z=gz
    cx=(px-768)/f; cy=-(py-1365)/f
    dirc=np.array([cx,cy,-1.0]); dw=R@dirc
    t=(gz-C[2])/dw[2]; return C+t*dw
rows=[]
for rowpx in [2730,2600,2500,2400,2300,2200,2100,2000,1900,1800,1700,1600,1500,1400,1350,1300,1250,1200]:
    P=ground_point(768,rowpx)
    if not np.isfinite(P).all(): continue
    dist=float(np.linalg.norm(P-C)); alongx=float(P[1]-C[1])
    a=np.array(project(P)); b=np.array(project(P+np.array([0,0.01,0]))); c=np.array(project(P+np.array([0.01,0,0])))
    along=abs(b[1]-a[1])/0.01; across=abs(c[0]-a[0])/0.01
    rows.append(dict(row=rowpx,ground_dist_m=round(float(P[1]-C[1]),2),slant_m=round(dist,2),px_per_m_across=round(across),px_per_m_along=round(along)))
    print("image row %4d  ground distance ahead %5.1f m (slant %5.1f m): across the street %5.0f px/m (1 px = %5.1f mm), along the street %5.0f px/m (1 px = %6.1f mm)"%(rowpx,P[1]-C[1],dist,across,1000/across,along,1000/along))
json.dump(rows,open(NUM+'/g1_footprint.json','w'),indent=1)
