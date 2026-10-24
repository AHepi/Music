import sys,subprocess,numpy as np
f=sys.argv[1]; w,h=270,480
p=subprocess.run(['ffmpeg','-v','error','-i',f,'-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True)
a=np.frombuffer(p.stdout,np.uint8).reshape(-1,h,w,3).astype(np.int16)
np.save(sys.argv[2],a)
d=np.abs(np.diff(a,axis=0)).mean(axis=(1,2,3))
lum=a.mean(axis=(1,2,3))
for i,x in enumerate(d):
    loc=d[max(0,i-3):i+4]; med=np.median(np.r_[d[max(0,i-3):i],d[i+1:i+4]]) if i>0 else 0
    if x>1.0 and x>3*med+0.3: print(f"SPIKE frame {i}->{i+1} t={(i+1)/30:.2f}s diff={x:.2f} med={med:.2f}")
np.savetxt(sys.argv[2]+'.txt',np.c_[np.r_[0,d],lum],fmt='%.3f')
