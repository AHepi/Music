import sys, importlib.util, numpy as np, cv2
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
import measure_readable as mr
p='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/growth/pilot1/'
m=cv2.imread(p+'layer_growth_plate_main.png',cv2.IMREAD_UNCHANGED)
mk=m[...,2]>127
summary,rows=mr.check_element(p+'plate_main_growth.jpg', mk, 0.45)
print(summary)
import collections
print(collections.Counter(r['verdict'] for r in rows))
for r in sorted(rows,key=lambda r:-r['width_px'])[:12]: print({k:r[k] for k in ('kind','width_px','contrast','surround','sign','p_back','verdict')})
rgb,k=mr.pdc.load_plate(p+'plate_main_growth.jpg'); A=mr.pdc.lum(rgb)
print('lum in mask mean', A[mk].mean(), 'p10/90', np.percentile(A[mk],[10,90]))
ring=cv2.dilate(mk.astype(np.uint8),np.ones((9,9),np.uint8))>0
ring&=~mk
print('surround mean',A[ring].mean())
