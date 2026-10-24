from proj import *
import itertools
def line_err(c):
    e=0; out={}
    for n,(lx,hz) in {'left roofline':(-4.3,6.44),'left kerb':(-2.5,0.13),'right kerb':(2.5,0.13)}.items():
        a,b=line_img(c,lx,hz,c[1]+4,c[1]+60)
        s=np.array(STARTS[n])*np.array([W,H]); m=MEET*np.array([W,H])
        al=(b-a)/np.linalg.norm(b-a); ac=np.array([-al[1],al[0]])
        d=[(p-a)@ac for p in (s,m)]
        out[n]=[round(float(x),1) for x in d]; e+=sum(x*x for x in d)
    return e,out
best=None
for x in np.arange(2.80,3.60,0.02):
  for eye in np.arange(1.5,2.5,0.02):
    for yaw in np.arange(6.5,8.5,0.1):
      c=cam(x=x,eye=eye,yaw=yaw); e,_=line_err(c)
      if best is None or e<best[0]: best=(e,x,eye,yaw)
print('best x, eye, yaw:',[round(v,3) for v in best[1:]],'rms px',round((best[0]/6)**.5,1))
print('current:',line_err(cam())[1])
print('best   :',line_err(cam(x=best[1],eye=best[2],yaw=best[3]))[1])
c=cam(x=best[1],eye=best[2],yaw=best[3])
vp,_=project(c,(0,17.85+1e5,1e5*R)); print('VP best', vp/np.array([W,H]))
# same with yaw only change
for yaw in (7.5,7.7,7.9):
  print('yaw only',yaw,line_err(cam(yaw=yaw))[1])
