from PIL import Image, ImageDraw, ImageFont
import os
R="proc-work/garden/final/renders/"
OUT="proc-work/30 Japanese garden - pictures/"
F=lambda s,b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''),s)
src=[("Original photo (golden hour)","/home/user/Music/japanese-courtyard/01 Japanese courtyard - golden hour photo.png"),("Realistic final",R+'real_hero.png'),("Painted final",R+'painted_hero.png')]
ims=[Image.open(p).convert('RGB') for _,p in src]
regions=[(1250,330,1850,730),(0,980,600,1380),(1500,820,2100,1220)]
cw,ch=470,314
W=3*cw+4*15; H=60+3*(ch+10)+50
im=Image.new('RGB',(W,H),(250,248,244)); d=ImageDraw.Draw(im)
d.text((15,12),'Same three places, same camera: original, realistic, painted (crops scaled to 78 percent)',font=F(22,True),fill=(30,30,30))
for ci,(t,_) in enumerate(src): d.text((15+ci*(cw+15),42),t,font=F(17,True),fill=(30,30,30))
for ri,b in enumerate(regions):
    for ci,img in enumerate(ims):
        c=img.crop(b).resize((cw,ch),Image.LANCZOS); im.paste(c,(15+ci*(cw+15),66+ri*(ch+10)))
d.text((15,H-34),'Rows: roof edge, shoji and pine / bridge and pond rocks / gravel, kerb and stepping stones. The pine pads were round green clouds in the original and are flat plates now. Source: final/renders hero pictures at 2400 x 1600.',font=F(14),fill=(90,90,90))
p=OUT+'30 Checker - original beside realistic beside painted, same three places.jpg'
im.save(p,quality=84,optimize=True); print(os.path.getsize(p)//1024,'KB',im.size)
