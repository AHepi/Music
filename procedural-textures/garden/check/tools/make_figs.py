from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import re, datetime, os
R="proc-work/garden/final/renders/"
OUT="proc-work/30 Japanese garden - pictures/"
F=lambda s,b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf'%('-Bold' if b else ''),s)
BG=(250,248,244); INK=(30,30,30); RED=(190,40,40); GRN=(30,120,60); AMB=(190,120,0)
def label(d,xy,text,size=22,fill=INK,bold=False): d.text(xy,text,font=F(size,bold),fill=fill)
def save(im,name,q=84):
    p=OUT+name; im.convert('RGB').save(p,quality=q,optimize=True)
    print(name, os.path.getsize(p)//1024,'KB', im.size)

# ---------- figure 1: painted look and the "no smooth curves" rule ----------
pv=Image.open(R+'painted_veranda.png').convert('RGB')
ph=Image.open(R+'painted_hero.png').convert('RGB')
sky=pv.crop((700,0,2400,640)).resize((850,320))
gr=ImageEnhance.Contrast(ph.crop((1500,1000,2400,1600))).enhance(2.0).resize((640,427))
W=850+640+60; H=60+427+120
im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
label(d,(20,12),'Painted look: two places that break "no rounded smooth curves, only edges and flat planes"',24,INK,True)
im.paste(sky,(20,60)); im.paste(gr,(890,60))
label(d,(20,60+330),'Veranda view, sky (2400 x 1600 final, scaled to half): the rings round the sun are perfect smooth circles.',17,RED)
label(d,(20,60+356),'The ridges below them are flat planes and follow the rule.',17,GRN)
label(d,(890,60+436),'Hero view, lower right (contrast raised x2 so it shows): the brown band and the',17,RED)
label(d,(890,60+460),'green patch have smooth curved outlines, and the ground itself is smooth-shaded.',17,RED)
label(d,(20,H-30),'Rocks, leaves, lily pads, grass blades and hills are faceted and pass. Source: final/renders/painted_veranda.png and painted_hero.png.',15,(90,90,90))
save(im,'30 Checker - painted look, smooth circles in the sky and curved ground patches.jpg')

# ---------- figure 2: realistic, what still gives it away at 100 % ----------
rh=Image.open(R+'real_hero.png').convert('RGB'); rv=Image.open(R+'real_veranda.png').convert('RGB')
a=rh.crop((1580,290,2000,680))
b=rv.crop((340,560,780,980))
c=rh.crop((380,1100,880,1400))
W=a.width+b.width+c.width+80; H=max(a.height,b.height,c.height)+150
im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
label(d,(20,12),'Realistic look at 100 percent: three things a viewer can still see',24,INK,True)
x=20
for img,t1,t2 in ((a,'Pine pads read as flat green plates','with spiky grass on top (hero view)'),(b,'Lichen reads as pale polka dots','on the lantern post (veranda view)'),(c,'White patches on the pond are the lit','paper screens mirrored (also in the original)')):
    im.paste(img,(x,60)); label(d,(x,60+img.height+8),t1,17,RED); label(d,(x,60+img.height+32),t2,17,RED); x+=img.width+20
label(d,(20,H-30),'Source: final/renders/real_hero.png and real_veranda.png, 100 percent crops, no scaling.',15,(90,90,90))
save(im,'30 Checker - realistic look at 100 percent, pine pads, lichen dots, pond patches.jpg')

# ---------- figure 3: workers after the last job ----------
rows=[]
base=datetime.datetime(2026,10,22,0,0,0)
def tsec(s):
    h,m,sec=[int(x) for x in s.split(':')]; return h*3600+m*60+sec
T="proc-work/garden/check/tools/"
rows.append((tsec('00:10:59'),2,1))
for fn in ('health_poll.log','health_poll2.log','health_poll3.log'):
    p=T+fn
    if not os.path.exists(p): continue
    for line in open(p):
        m=re.match(r'(\d\d:\d\d:\d\d) idle (\d+) ready (\d+) running (\d+)',line)
        if m: rows.append((tsec(m.group(1)),int(m.group(2)),int(m.group(4))))
rows=sorted(set(rows))
t0=tsec('00:05:00'); t1=max(r[0] for r in rows)+60
W,H=1300,520; L,Rm,Tp,Bt=90,40,110,90
im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
label(d,(20,12),'RunPod endpoint: workers that are up (idle + running), read-only health calls',24,INK,True)
label(d,(20,48),'The notes promise "a worker stops about 5 seconds after its last job". These stayed up for the whole time I watched.',17,(80,80,80))
def X(t): return L+(t-t0)/(t1-t0)*(W-L-Rm)
def Y(n): return H-Bt-n/3.5*(H-Bt-Tp)
for n in range(4):
    d.line([(L,Y(n)),(W-Rm,Y(n))],fill=(220,216,208)); label(d,(L-30,Y(n)-11),str(n),18)
step=300
for t in range((t0//step)*step,t1+1,step):
    if t>=t0:
        d.line([(X(t),Y(0)),(X(t),Y(0)+6)],fill=INK); label(d,(X(t)-30,Y(0)+10),'%02d:%02d'%(t//3600,(t%3600)//60),16)
pts=[(X(t),Y(i+r)) for t,i,r in rows]
for (x1,y1),(x2,y2) in zip(pts[:-1],pts[1:]):
    d.line([(x1,y1),(x2,y1),(x2,y2)],fill=RED,width=4)
# markers
def mark(t,text,col,dy):
    d.line([(X(t),Tp-10),(X(t),Y(0))],fill=col,width=2); label(d,(X(t)+6,Tp+dy),text,16,col)
mark(tsec('00:08:00'),'last builder jobs (pictures saved ~00:07-00:08)',GRN,0)
mark(tsec('00:19:55'),'my small calls and 1 check job (picked up in 1.2 s, no cold start)',AMB,70)
label(d,(L,H-48),'Workers up (idle + running) over time, UTC. Job counter did not move 00:11-00:19 (692 done), so no other jobs kept them awake.',16,INK)
label(d,(L,H-26),'Whether idle workers are billed cannot be seen from here; the RunPod console (Workers tab, billing) will show it.',16,INK)
save(im,'30 Checker - RunPod workers stay up after the last job.jpg')
