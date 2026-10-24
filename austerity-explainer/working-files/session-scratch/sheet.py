import sys
from PIL import Image
d, p, out = sys.argv[1:4]
ims=[Image.open(f'{d}/{p}-{n}.png') for n in ('overview','cart','barrels','crates','lamp')]
ims=[i.resize((i.width*2//3, i.height*2//3)) for i in ims]
w=sum(i.width for i in ims); h=max(i.height for i in ims)
o=Image.new('RGB',(w,h)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width
o.save(out)
