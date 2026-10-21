import sys; sys.path.insert(0,'scripts')
from common import *
from stage_curve import *
from PIL import Image, ImageDraw, ImageFont
import json
F=ImageFont.truetype("DejaVuSans.ttf",14); FB=ImageFont.truetype("DejaVuSans-Bold.ttf",16); FS=ImageFont.truetype("DejaVuSans.ttf",12)
Wd,Hd=1000,640; L,T,R_,B=70,50,970,470
im=Image.new('RGB',(Wd,Hd),(250,250,250)); d=ImageDraw.Draw(im)
xmax=0.6; ymax=0.7
def X(v): return L+(R_-L)*v/xmax
def Y(v): return B-(B-T)*v/ymax
# crush zone
d.rectangle([X(0),T,X(0.10),B],fill=(255,225,225)); d.rectangle([X(0.10),T,X(0.13),B],fill=(255,243,214))
d.text((X(0.003),T+4),"film",fill=(150,0,0),font=FS); d.text((X(0.003),T+18),"black",fill=(150,0,0),font=FS)
d.text((X(0.101),T+4),"thin",fill=(150,100,0),font=FS)
for v in np.arange(0,0.61,0.1):
    d.line([X(v),B,X(v),B+5],fill=(0,0,0)); d.text((X(v)-12,B+8),f"{v:.1f}",fill=(0,0,0),font=F)
for v in np.arange(0,0.71,0.1):
    d.line([L-5,Y(v),L,Y(v)],fill=(0,0,0)); d.text((L-38,Y(v)-8),f"{v:.1f}",fill=(0,0,0),font=F)
d.rectangle([L,T,R_,B],outline=(0,0,0))
d.line([X(0),Y(0),X(0.6),Y(0.6)],fill=(190,190,190),width=1)
d.text((X(0.46),Y(0.47)),"no change",fill=(150,150,150),font=FS)
xs=np.linspace(0.0,0.6,200)
ys=[float(stage_grey(v)) for v in xs]
pts=[(X(a),Y(b)) for a,b in zip(xs,ys)]; d.line(pts,fill=(30,60,160),width=3)
emp=json.load(open(NUM+'/b4_stage_curve_check.json'))
for k,col in (('dry',(20,140,60)),('wet',(200,80,20))):
    for r in emp[k]:
        x,y=X(r['painted']),Y(r['stage']); d.ellipse([x-4,y-4,x+4,y+4],fill=col)
d.text((L+10,B-30),"blue line = the film's finishing step written out (cinema-stage.js)",fill=(30,60,160),font=FS)
d.ellipse([L+10,B-60,L+18,B-52],fill=(20,140,60)); d.text((L+24,B-62),"measured, film's dry painting",fill=(20,140,60),font=FS)
d.ellipse([L+250,B-60,L+258,B-52],fill=(200,80,20)); d.text((L+264,B-62),"measured, wet painting",fill=(200,80,20),font=FS)
d.text((L,12),"How the film darkens the painting: painted brightness (across) -> brightness on the film (up)",fill=(0,0,0),font=FB)
d.text((L+330,B+30),"painted brightness (0 = black, 1 = white)",fill=(0,0,0),font=F)
# strip
for i,v in enumerate([0.05,0.08,0.10,0.12,0.14,0.17,0.20,0.25,0.30]):
    x0=L+i*98; 
    g=int(round(float(lin_to_srgb(srgb_to_lin(v)))*255)) if False else int(round(v*255))
    d.rectangle([x0,B+55,x0+90,B+85],fill=(g,g,g)); 
    fv=float(stage_grey(v)); g2=int(round(min(1,fv+0.02)*255))
    d.rectangle([x0,B+85,x0+90,B+115],fill=(g2,g2,g2))
    d.text((x0+4,B+60),f"{v:.2f}",fill=(255,255,255) if v<0.2 else (0,0,0),font=FS)
    d.text((x0+4,B+90),f"{fv+0.02:.2f}",fill=(255,255,255) if fv<0.2 else (0,0,0),font=FS)
d.text((L-62,B+62),"painted",fill=(0,0,0),font=FS); d.text((L-62,B+92),"on film",fill=(0,0,0),font=FS)
im.save(CROPS+"/12-fig5-film-curve-darks.jpg",quality=90); print(im.size)
