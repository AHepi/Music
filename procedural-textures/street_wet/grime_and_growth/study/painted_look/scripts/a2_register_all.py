import sys; sys.path.insert(0,'scripts')
from reg import *
import json
res={}
for name,(p,q) in PAIRS.items():
    A=load_rgb(p); B=load_rgb(q)
    Bw,(fx,fy,g)=register_pair(A,B)
    # residual check: same shift estimate again
    fx2,fy2,g2=shift_field(lum(A),lum(Bw))
    print(name,"global",np.round(g,2),"field dx range",np.round([fx.min(),fx.max()],1),"dy range",np.round([fy.min(),fy.max()],1),"| residual median",np.round(g2,2),"residual p90 abs",np.round(np.percentile(np.hypot(fx2,fy2),90),2))
    cv2.imwrite(WORK+f"/{name}_painting_registered.png",cv2.cvtColor((Bw*255+0.5).astype(np.uint8),cv2.COLOR_RGB2BGR))
    res[name]={'global_shift_px':g,'dx_range':[float(fx.min()),float(fx.max())],'dy_range':[float(fy.min()),float(fy.max())],'residual_p90':float(np.percentile(np.hypot(fx2,fy2),90))}
json.dump(res,open(NUM+'/a2_registration_local.json','w'),indent=1)
