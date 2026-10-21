from PIL import Image, ImageDraw, ImageFont
import os
def font(size=18):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
def panel(path, size, label=None, crop=None):
    im=Image.open(path).convert('RGB')
    if crop: im=im.crop(crop)
    im=im.resize(size, Image.LANCZOS)
    if label:
        d=ImageDraw.Draw(im); f=font(max(14,size[0]//28))
        w=d.textlength(label,font=f)+10
        d.rectangle([0,0,w,f.size+8],fill=(0,0,0)); d.text((5,3),label,fill=(255,255,255),font=f)
    return im
def grid(items, cols, size, out, title=None, quality=84, gap=4):
    rows=(len(items)+cols-1)//cols
    th=36 if title else 0
    sheet=Image.new('RGB',(cols*size[0]+(cols-1)*gap, rows*size[1]+(rows-1)*gap+th),(18,18,18))
    if title:
        d=ImageDraw.Draw(sheet); d.text((8,6),title,fill=(235,235,235),font=font(20))
    for k,it in enumerate(items):
        p,label=it[0],it[1]; crop=it[2] if len(it)>2 else None
        sheet.paste(panel(p,size,label,crop),((k%cols)*(size[0]+gap),th+(k//cols)*(size[1]+gap)))
    sheet.save(out,quality=quality,optimize=True)
    return os.path.getsize(out)
