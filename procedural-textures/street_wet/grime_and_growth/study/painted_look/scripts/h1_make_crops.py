"""Pictures for the report: plate | painting pairs at 100 %, with labels."""
import sys; sys.path.insert(0,'scripts')
from common import *
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype("DejaVuSans.ttf",15); FONTB=ImageFont.truetype("DejaVuSans-Bold.ttf",16) if True else FONT
def reg_img(name):
    return cv2.cvtColor(cv2.imread(WORK+f"/{name}_painting_registered.png"),cv2.COLOR_BGR2RGB)
def plate_img(name):
    return cv2.cvtColor(cv2.imread(PAIRS[name][0]),cv2.COLOR_BGR2RGB)
def panel(name,box,label_left,label_right,scale=1):
    a=plate_img(name); b=reg_img(name); x0,y0,x1,y1=box
    ca=a[y0:y1,x0:x1]; cb=b[y0:y1,x0:x1]
    if scale!=1:
        ca=cv2.resize(ca,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST); cb=cv2.resize(cb,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    h,w=ca.shape[:2]
    im=Image.new('RGB',(w*2+8,h+24),(20,20,20)); d=ImageDraw.Draw(im)
    im.paste(Image.fromarray(ca),(0,24)); im.paste(Image.fromarray(cb),(w+8,24))
    d.text((4,3),label_left,fill=(255,255,255),font=FONT); d.text((w+12,3),label_right,fill=(255,255,255),font=FONT)
    return im
def stack(ims,gap=8,bg=(20,20,20)):
    W_=max(i.size[0] for i in ims); H_=sum(i.size[1] for i in ims)+gap*(len(ims)-1)
    out=Image.new('RGB',(W_,H_),bg); y=0
    for i in ims: out.paste(i,(0,y)); y+=i.size[1]+gap
    return out
if __name__=='__main__':
    # 1. cracks, pale stains and specks on pavement flags (corner pair, full-size plate sent)
    p1=panel('corner_dry',(900,2150,1300,2450),"PLATE: hairline cracks, pale stain, specks (100 %)","PAINTING: cracks inked, stain a bold white stroke")
    p1.save(CROPS+"/12-fig1-flags-cracks-stains-specks.jpg",quality=88)
    # 2. soot ring round the drum (lockout dry pair)
    p2=panel('lockout_dry',(900,2020,1400,2330),"PLATE: soft soot round the drum foot","PAINTING: hard flat patch + flecks + splatter")
    p2.save(CROPS+"/12-fig2-soot-ring-round-the-drum.jpg",quality=88)
    # 3. rubbish chips, joints and gutter debris at half-size input (round 2)
    p3=panel('lockout_wet_r2',(820,2060,1320,2400),"ROUND 2 PLATE (sent at 0.53): cinders, chips, joints","ROUND 2 PAINTING")
    p3b=panel('lockout_wet_r2',(120,1960,620,2300),"ROUND 2 PLATE: cart foot, grit, damp","ROUND 2 PAINTING")
    stack([p3,p3b]).save(CROPS+"/12-fig3-round2-rubbish-chips-and-joints.jpg",quality=88)
    print("ok")
