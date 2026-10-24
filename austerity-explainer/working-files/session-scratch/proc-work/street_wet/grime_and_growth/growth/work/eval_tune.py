import sys, os, numpy as np, cv2
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
import measure_readable as mr, measure_common as mc
p=sys.argv[1]
cams=sys.argv[2].split(',') if len(sys.argv)>2 else ['main','notice']
for cam in cams:
    m=cv2.imread(p+f'layer_growth_plate_{cam}.png',cv2.IMREAD_UNCHANGED); mask=m[...,2]>127
    depth=mc.read_depth(p+f'depth_{cam}.png'); mask&=depth<=15
    ring=(cv2.dilate(mask.astype(np.uint8),np.ones((11,11),np.uint8))>0)&~mask
    for f in sorted(x for x in os.listdir(p) if x.startswith('tune_') and x.endswith(f'_{cam}.png')):
        s,rows=mr.check_element(p+f,mask,0.45)
        im=cv2.cvtColor(cv2.imread(p+f).astype(np.float32)/255,cv2.COLOR_BGR2RGB); A=mr.pdc.lum(im)
        hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV); bg=((hsv[...,1]>=0.6)&(hsv[...,2]>=0.6)&(hsv[...,0]>=75)&(hsv[...,0]<=160))[mask].sum()
        print(cam, f[5:-4-len(cam)], 'lum %.3f/%.3f'%(A[mask].mean(),A[ring].mean()), 'marks',s['marks'],'good %.2f lost %.2f crushed %.2f'%(s['share_good'],s['share_lost'],s['share_crushed']), 'good#',s['good'], 'brightgreen',int(bg))
