import sys; sys.path.insert(0,'scripts')
from paths import *
from PIL import Image
import numpy as np
for name,(p,q) in PAIRS.items():
    a=Image.open(p).convert('RGB'); b=Image.open(q).convert('RGB')
    print(name,a.size,b.size)
    w=500; h=int(a.size[1]*w/a.size[0])
    sheet=Image.new('RGB',(w*2+10,h),(255,255,255))
    sheet.paste(a.resize((w,h),Image.LANCZOS),(0,0)); sheet.paste(b.resize((w,h),Image.LANCZOS),(w+10,0))
    sheet.save(WORK+f"/ov_{name}.jpg",quality=85)
