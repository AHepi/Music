import sys, numpy as np, cv2, os
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
import measure_readable as mr
p=sys.argv[1]
m=cv2.imread(p+'layer_growth_plate_main.png',cv2.IMREAD_UNCHANGED); mk=m[...,2]>127
ring=(cv2.dilate(mk.astype(np.uint8),np.ones((11,11),np.uint8))>0)&~mk
for name in sorted(f[:-4] for f in os.listdir(p) if f.endswith('.png') and f.startswith('sat')):
    png=p+name+'.png'
    summary,rows=mr.check_element(png, mk, 0.45)
    im=cv2.cvtColor(cv2.imread(png).astype(np.float32)/255,cv2.COLOR_BGR2RGB)
    hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV); S=hsv[...,1][mk]; V=hsv[...,2][mk]; H=hsv[...,0][mk]
    A=mr.pdc.lum(im)
    bright=((S>=0.6)&(V>=0.6)).mean()
    print(name,'lum %.3f/%.3f'%(A[mk].mean(),A[ring].mean()),'hue med %.0f S med %.2f V med %.2f V p90 %.2f'%(np.median(H),np.median(S),np.median(V),np.percentile(V,90)),'bright-green share %.3f'%bright, 'good %.2f lost %.2f'%(summary['share_good'],summary['share_lost']))
