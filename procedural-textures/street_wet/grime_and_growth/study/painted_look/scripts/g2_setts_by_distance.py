"""Do the road's sett joints in the plate come back in the painting, and out to what distance?  Strips of the visible road, band-pass correlation plate vs painting."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
# (image row, ground distance ahead m, px per m ALONG the street, px per m ACROSS the street) from g1_footprint.py
rows_ground=[(2730,6.8,135,517),(2600,7.9,98,441),(2500,9.0,74,383),(2400,10.6,53,325),(2300,12.9,36,267),(2200,16.4,22,209),(2100,22.6,12,151),(2000,36.5,4,93)]
def dist_at(r):
    # interpolate ground distance, along px/m, across px/m for a row
    rs=np.array([a[0] for a in rows_ground][::-1],float)
    return [float(np.interp(r,rs,np.array([a[i] for a in rows_ground][::-1],float))) for i in (1,2,3)]
M=lockout_masks()
out={}
for name in ('lockout_dry','lockout_wet','lockout_wet_r2'):
    p,q=PAIRS[name]
    A=lum(load_rgb(p)); B=lum(load_rgb(WORK+f"/{name}_painting_registered.png"))
    road=erode(M['road'],9)
    res=[]
    print("=====",name)
    for y0 in range(2630,1990,-90):
        y1=y0+90
        m=np.zeros_like(road); m[y0:y1]=road[y0:y1]
        if m.sum()<8000: continue
        dist,along,across=dist_at((y0+y1)//2)
        row={'rows':[y0,y1],'ground_distance_m':round(dist,1),'px_per_m_along':round(along),'px_per_m_across':round(across),
             'joint_1p6cm_thickness_px_along':round(0.016*along,2),'joint_1p6cm_width_px_across':round(0.016*across,1)}
        for sg in (1.0,1.6,2.5,4.0):
            da=dog(A,sg); db=dog(B,sg)
            best=-1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    c=np.corrcoef(da[m],np.roll(np.roll(db,dy,0),dx,1)[m])[0,1]; best=max(best,c)
            row[f'corr_sigma{sg}']=round(float(best),2); row[f'rms_ratio_sigma{sg}']=round(float(db[m].std()/da[m].std()),2)
        # joint-grid visibility: vertical profile (along the street) averaged over the centre of the strip, plate vs painting
        sub=slice(y0,y1); cols=slice(500,1000)
        pa=(A[sub,cols]-gauss(A,6)[sub,cols]).mean(axis=1); pb=(B[sub,cols]-gauss(B,6)[sub,cols]).mean(axis=1)
        row['profile_corr_along']=round(float(np.corrcoef(pa,pb)[0,1]),2)
        res.append(row)
        print("rows %4d-%4d  %4.1f m ahead  %4d px/m along  1.6 cm joint = %.1f px thick (along) / %.1f px wide (across) | band corr sigma 1.0: %.2f  1.6: %.2f  2.5: %.2f  4.0: %.2f | along-the-street profile corr %.2f"%(y0,y1,dist,along,0.016*along,0.016*across,row['corr_sigma1.0'],row['corr_sigma1.6'],row['corr_sigma2.5'],row['corr_sigma4.0'],row['profile_corr_along']))
    out[name]=res
json.dump(out,open(NUM+'/g2_setts_by_distance.json','w'),indent=1)
