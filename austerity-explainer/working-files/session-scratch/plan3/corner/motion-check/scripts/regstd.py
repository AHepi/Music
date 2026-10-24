import numpy as np, sys, cv2
W=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3])
regs={"right wall window 0.88,0.40":(930,980,740,800),"gas lamp crossbar 0.80,0.34":(840,900,640,670),"right wall upper 0.95,0.15":(1000,1060,250,330),
"glow disc inside road 0.42,0.62":(430,480,1170,1220),"road outside disc 0.25,0.62":(250,300,1170,1220),"disc edge band 0.335-0.355,0.62":(362,384,1170,1220),
"colliery gate 0.6,0.45":(620,680,840,880),"board left 0.70,0.50":(740,770,940,1000),"left chimneys 0.08,0.17":(60,130,300,360),"sky 0.2,0.25":(150,300,450,520)}
G=[]
for i in range(a,b):
    G.append(cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2))
G=np.array(G)
for n,(x0,x1,y0,y1) in regs.items():
    s=G[:,y0:y1,x0:x1].mean(axis=(1,2))
    print(f"{n:34s} mean {s.mean():6.1f} std {s.std():5.2f} min {s.min():6.1f} max {s.max():6.1f} max frame step {np.abs(np.diff(s)).max():.2f}")
