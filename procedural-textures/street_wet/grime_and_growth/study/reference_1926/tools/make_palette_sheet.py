import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".")
from palette import PALETTE
cols = 3
rows = (len(PALETTE)+cols-1)//cols
cw, ch = 520, 64
W, H = cols*cw+20, rows*ch+70
im = Image.new("RGB",(W,H),(236,232,224))
d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
except Exception:
    f = fb = ImageFont.load_default()
d.text((10,8),"Reference swatches for the 1926 pit-village street: left square dry, right square wet (sRGB)",font=fb,fill=(30,30,30))
d.text((10,34),"Only the swatch marked 'measured' comes from a photograph; the rest are my estimates of a typical look.",font=f,fill=(60,60,60))
for i,(name,dry,wet,basis) in enumerate(PALETTE):
    c, r = i % cols, i // cols
    x0, y0 = 10+c*cw, 62+r*ch
    d.rectangle([x0,y0,x0+56,y0+ch-8],fill=dry,outline=(90,90,90))
    d.rectangle([x0+56,y0,x0+112,y0+ch-8],fill=wet,outline=(90,90,90))
    d.text((x0+120,y0+2),name,font=f,fill=(20,20,20))
    d.text((x0+120,y0+22),"dry %s  wet %s"%(dry,wet),font=f,fill=(70,70,70))
    d.text((x0+120,y0+40),basis,font=f,fill=(120,60,40) if basis.startswith("measured") else (110,110,110))
out = sys.argv[1]
im.save(out, quality=88)
print(out, im.size)
