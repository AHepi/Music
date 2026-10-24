import numpy as np
from PIL import Image
im=np.asarray(Image.open('../../final/composed-end-5.png').convert('L')).astype(np.float32)/255
# notice box 0.708-0.885 across, 0.508-0.647 down; take central column band and find dark text rows
x0,x1=int(0.73*1080),int(0.86*1080)
y0,y1=int(0.505*1920),int(0.66*1920)
band=im[y0:y1,x0:x1]
paper=np.percentile(band,80)
dark=(band<paper*0.55).mean(1)
rows=[]
on=False
for i,v in enumerate(dark):
    if v>0.04 and not on: start=i; on=True
    if v<=0.04 and on: rows.append((start+y0,i+y0)); on=False
for a,b in rows: print(f'text row {a/1920:.4f}-{b/1920:.4f} down: {b-a} px tall, ink share {dark[a-y0:b-y0].mean():.2f}')
