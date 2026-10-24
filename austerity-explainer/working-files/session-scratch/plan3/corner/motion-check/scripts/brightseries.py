import numpy as np, sys, cv2
W=sys.argv[1]
regs={"notice top":(820,920,1000,1030),"notice bottom":(800,860,1190,1220),"board left dark":(735,760,1000,1100),"road left of drum":(250,400,1150,1250),"sky":(100,400,250,400),"right wall":(1000,1070,700,900),"lantern":(800,830,1360,1400)}
names=list(regs)
print("frame t "+" | ".join(names))
vals=[]
for i in range(255,365):
    a=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
    v=[a[y0:y1,x0:x1].mean() for (x0,x1,y0,y1) in regs.values()]
    vals.append(v)
vals=np.array(vals)
for k,n in enumerate(names):
    s=vals[:,k]; d=np.abs(np.diff(s))
    print(f"{n:18s} mean {s.mean():6.1f} range {s.min():6.1f}-{s.max():6.1f}  mean|step| {d.mean():.2f} max|step| {d.max():.2f}")
