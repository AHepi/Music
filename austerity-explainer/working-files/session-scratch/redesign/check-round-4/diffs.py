# Plain note: prints the mean change between neighbouring film frames in given time windows.
import subprocess, sys, numpy as np
F=sys.argv[1]; start=47.3667
def frames(t0,t1):
    n0=round((t0-start)*30); n1=round((t1-start)*30)
    cmd=['ffmpeg','-v','error','-i',F,'-vf',f'select=between(n\\,{n0}\\,{n1}),scale=270:480','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-']
    raw=subprocess.run(cmd,capture_output=True).stdout
    a=np.frombuffer(raw,np.uint8).reshape(-1,480,270,3).astype(float)
    return n0,a
for w in sys.argv[2:]:
    t0,t1=map(float,w.split(':'))
    n0,a=frames(t0,t1)
    d=[abs(a[i+1]-a[i]).mean() for i in range(len(a)-1)]
    print(w, ' '.join(f'{start+(n0+i+1)/30:.2f}:{x:.2f}' for i,x in enumerate(d)))
