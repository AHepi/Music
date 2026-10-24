import numpy as np
from PIL import Image
im=Image.open('/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg').convert('L')
W,H=im.size
im=np.asarray(im.resize((1080,int(H*1080/W)))).astype(np.float32)/255
H=im.shape[0]; print('scaled height',H)
x0,x1=int(0.765*1080),int(0.895*1080)
y0,y1=int(0.45*H),int(0.66*H)
band=im[y0:y1,x0:x1]
paper=np.percentile(band,80)
dark=(band<paper*0.55).mean(1)
on=False
for i,v in enumerate(dark):
    if v>0.06 and not on: s=i; on=True
    if v<=0.06 and on:
        on=False
        if i-s>=3: print(f'row {(s+y0)/H:.4f}-{(i+y0)/H:.4f}: {i-s} px (frame height {H}); ink {dark[s:i].mean():.2f}')
