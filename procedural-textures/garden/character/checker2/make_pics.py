import json
from PIL import Image, ImageDraw, ImageFont
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/'
O='out/'
F=lambda s,b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''), s)
BG=(32,30,36); FG=(240,232,224)
def save(img, name, q=84):
    img=img.convert('RGB'); img.save(P+name, quality=q, optimize=True)
    import os; print(name, os.path.getsize(P+name)//1024, 'KB', img.size)
def band(w,h,text,size=24,bold=True):
    b=Image.new('RGB',(w,h),BG); d=ImageDraw.Draw(b); d.text((14,(h-size)//2-2),text,fill=FG,font=F(size,bold)); return b
# 1. turn gaps
t1=Image.open(O+'prev/turn_N2.jpg').resize((800,533),Image.LANCZOS)
t2=Image.open(O+'prev/turn_N1.jpg').resize((800,533),Image.LANCZOS)
mid=Image.open(O+'crops/ba_bridge_middle.jpg'); west=Image.open(O+'crops/ba_bridge_west_arm.jpg')
print(mid.size, west.size)
# hero crops of the two turns, new picture only, enlarged 1.6x
c_n1=mid.crop((808+230,40,808+560,270)).resize((800,int(800*230/330)),Image.LANCZOS)
c_n2=west.crop((808+470,100,808+800,330)).resize((800,int(800*230/330)),Image.LANCZOS)
W=1600; H=70+533+40+c_n1.size[1]+20
img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)
d.text((14,12),'Both turns of the bridge leave an open gap in the walking surface',fill=FG,font=F(26,True))
d.text((14,44),'top row: looking straight down at the west turn (left) and the east turn (right), as drawn in the finished scene. bottom row: the same gaps in the hero picture at 100 percent (enlarged 1.6 times)',fill=(200,192,184),font=F(13))
img.paste(t1,(0,70)); img.paste(t2,(800,70))
y=70+533+8; d.text((14,y+8),'hero view, west turn',fill=FG,font=F(15,True)); d.text((814,y+8),'hero view, east turn',fill=FG,font=F(15,True))
y+=32
img.paste(c_n2,(0,y)); img.paste(c_n1,(800,y))
save(img,'31 Checker - the bridge turns have an open gap.jpg')
# 2. stones and posts from the water
ims=[Image.open(O+'prev/%s.jpg'%n).resize((800,533),Image.LANCZOS) for n in ('foot3','foot9','under_mid','post_pegs')]
cap=['footing stone 3, seen from the south-west bank','footing stone 9 at the east bank, with the rock and planks beside it','bridge from the water, low: posts, stringer board, planks','one post close: foot with algae band, two pegs on its face']
img=Image.new('RGB',(1600,2*(533+34)+60),BG); d=ImageDraw.Draw(img)
d.text((14,10),'The posts, stringers and planks read as built; two footing stones hang over air on the slope',fill=FG,font=F(24,True))
for i,(im,c) in enumerate(zip(ims,cap)):
    x=(i%2)*800; y=50+(i//2)*(533+34)
    img.paste(im,(x,y+34)); d.text((x+12,y+8),c,fill=FG,font=F(15,True))
save(img,'31 Checker - posts and footing stones from the water.jpg')
# 3. normal-map direction table
R=json.load(open(O+'nm_dir.json'))
rows=list(R.items())
RH=30; W=1500; H=110+RH*len(rows)+70
img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)
d.text((14,10),'Normal map direction test: does the lit picture follow the map?',fill=FG,font=F(26,True))
d.text((14,48),'Flat plane, low sun (30 degrees) from +X and from +Y, same Image -> Normal Map (tangent) -> Principled chain as the materials. Bars: correlation of the fine detail in the lit picture with the map.',fill=(200,192,184),font=F(13))
d.text((14,70),'green = sun from +X against the red channel, blue = sun from +Y against the green channel (both must be above +0.25). Right column, red: control with the green channel flipped (must go clearly negative).',fill=(200,192,184),font=F(13))
x0=420; scale=300; cx=1230; cs=140
d.line((cx,96,cx,100+RH*len(rows)),fill=(120,120,120))
for j,(name,r) in enumerate(rows):
    y=100+j*RH
    d.text((14,y+6),'%s  %dx%d'%(name[:30],r['size'][0],r['size'][1]),fill=FG,font=F(13))
    d.rectangle((x0,y+4,x0+int(max(r['corr_sunX_with_red'],0)*scale),y+12),fill=(90,200,110))
    d.rectangle((x0,y+16,x0+int(max(r['corr_sunY_with_green'],0)*scale),y+24),fill=(90,150,230))
    d.text((x0+scale+12,y+6),'%.2f / %.2f'%(r['corr_sunX_with_red'],r['corr_sunY_with_green']),fill=FG,font=F(12))
    v=r['control_green_flipped_corr_sunY_with_green']
    col=(220,90,80)
    if v>=0: d.rectangle((cx,y+10,cx+int(v*cs),y+20),fill=col)
    else: d.rectangle((cx-int(-v*cs),y+10,cx,y+20),fill=col)
    d.text((cx+cs+14,y+6),'%+.2f'%v+('  (weak)' if v>-0.5 else ''),fill=(255,190,170) if v>-0.5 else FG,font=F(12))
d.text((14,H-58),'Result: 17 of 17 maps are lit on the sun side (all above +0.25). 14 of 17 also fail the flipped-green control as they should.',fill=FG,font=F(14,True))
d.text((14,H-36),'Swell and ripple (water) hold only 7 and 21 grey levels per channel, and the post-timber map is almost all vertical grain, so their flipped control cannot tell.',fill=(255,200,160),font=F(13))
d.text((14,H-18),'For 8 maps with a known height picture the map was also integrated back to a height: it matches the source at 0.999 or better (raised stays raised).',fill=(255,200,160),font=F(13))
save(img,'31 Checker - normal map direction test.jpg')
