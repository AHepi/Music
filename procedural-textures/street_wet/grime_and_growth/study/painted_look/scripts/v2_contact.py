import sys; sys.path.insert(0,'scripts')
from paths import *
from PIL import Image, ImageDraw
import glob, os
files=[]
for d in ["austerity-chapter-1","inflation-chapter-2"]:
    files+=sorted(glob.glob(f"{FILM}/paintings/{d}/*.jpg")+glob.glob(f"{FILM}/paintings/{d}/*.png"))
bg=[f for f in files if any(k in os.path.basename(f) for k in ["bg-","pithead","glasgow-square","council","farmland","mine-small","crowd","dole"]) ]
print(len(bg))
tw=300
ims=[]
for f in bg:
    im=Image.open(f).convert('RGB'); h=int(im.size[1]*tw/im.size[0]); th=min(h,420)
    ims.append((os.path.basename(f),im.resize((tw,h),Image.LANCZOS).crop((0,0,tw,th))))
cols=6; rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(cols*(tw+6),rows*(430)),(30,30,30)); d=ImageDraw.Draw(sheet)
for i,(n,im) in enumerate(ims):
    x=(i%cols)*(tw+6); y=(i//cols)*430
    sheet.paste(im,(x,y)); d.text((x+3,y+th+2 if False else y+412),n[:40],fill=(255,255,255))
sheet.save(WORK+"/contact_bg.jpg",quality=82); print(sheet.size)
