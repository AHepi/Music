import sys; sys.path.insert(0,'scripts')
from common import *
from PIL import Image, ImageDraw, ImageFont
import json
fit=json.load(open(NUM+'/c11_logistic.json'))
F=ImageFont.truetype("DejaVuSans.ttf",13); FB=ImageFont.truetype("DejaVuSans-Bold.ttf",15); FS=ImageFont.truetype("DejaVuSans.ttf",11)
widths=[2,3,4,5,6,8,10,12,16]; conts=[0.20,0.16,0.12,0.10,0.08,0.06,0.05,0.04,0.03,0.02]
def p(kind,which,w,c):
    b=fit[f'{which}|{kind}']['b']; return 1/(1+np.exp(-(b[0]+b[1]*np.log(w)+b[2]*np.log(c))))
def colour(v):
    # red (0) -> amber (0.5) -> green (1)
    if v<0.5: t=v/0.5; return (int(215-20*t),int(60+120*t),int(50+10*t))
    t=(v-0.5)/0.5; return (int(195-135*t),int(180+20*t),int(60+20*t))
cw,ch=46,30; ox,oy=70,70
panelW=ox+cw*len(widths)+20; panelH=oy+ch*len(conts)+50
im=Image.new('RGB',(panelW*2,panelH*2+56),(250,250,250)); d=ImageDraw.Draw(im)
d.text((10,6),"Share of marks that come back in the painting, by width and contrast in the plate (fitted to the street's plate/painting pairs)",fill=(0,0,0),font=FB)
titles=[("small","speck","Plate sent at 0.53 size - specks, chips, moss dots, weed tufts"),("small","line","Plate sent at 0.53 size - lines: cracks, drips, thin streaks"),
        ("full","speck","Plate sent full size (the old dry paintings) - specks"),("full","line","Plate sent full size - lines")]
for k,(which,kind,t) in enumerate(titles):
    px=(k%2)*panelW; py=(k//2)*panelH+36
    d.text((px+10,py+4),t,fill=(0,0,0),font=F)
    d.text((px+4,py+oy-18),"contrast",fill=(0,0,0),font=FS)
    for j,c in enumerate(conts):
        d.text((px+8,py+oy+j*ch+8),f"{c:.2f}",fill=(0,0,0),font=FS)
        for i,w in enumerate(widths):
            v=p(kind,which,w,c); x0=px+ox+i*cw; y0=py+oy+j*ch
            d.rectangle([x0,y0,x0+cw-2,y0+ch-2],fill=colour(v))
            d.text((x0+9,y0+8),f"{v*100:.0f}",fill=(255,255,255) if (v<0.25 or v>0.85) else (0,0,0),font=FS)
    for i,w in enumerate(widths): d.text((px+ox+i*cw+12,py+oy+len(conts)*ch+4),f"{w}",fill=(0,0,0),font=FS)
    d.text((px+ox,py+oy+len(conts)*ch+22),"width in plate pixels at 1536 wide",fill=(0,0,0),font=FS)
d.text((10,panelH*2+16),"numbers = per cent that come back. green 80 or more, amber about 50, red under 30.",fill=(60,60,60),font=FS)
d.text((10,panelH*2+32),"Outside the measured range (width under 2 px or over 16 px, contrast over 0.14) the fit is a straight-line guess.",fill=(60,60,60),font=FS)
im.save(CROPS+"/12-fig6-survival-map-width-by-contrast.jpg",quality=90); print(im.size)
