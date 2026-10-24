import sys, numpy as np, cv2, collections
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
import measure_readable as mr
p=sys.argv[1]
m=cv2.imread(p+'layer_growth_plate_main.png',cv2.IMREAD_UNCHANGED)
mk=m[...,2]>127
print('mask dots', int(mk.sum()))
ring=(cv2.dilate(mk.astype(np.uint8),np.ones((11,11),np.uint8))>0)&~mk
for name in sorted(f[:-4] for f in __import__('os').listdir(p) if f.endswith('.png') and f.startswith('gain') ):
    png=p+name+'.png'
    summary,rows=mr.check_element(png, mk, 0.45)
    rgb,k=mr.pdc.load_plate(png); A=mr.pdc.lum(rgb)
    print(name, 'lum mask %.3f surround %.3f' % (A[mk].mean(), A[ring].mean()), {k:summary[k] for k in ('marks','good','risky','lost','crushed','share_good','share_lost','share_crushed')})
