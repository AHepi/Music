import json, math, sys
from PIL import Image, ImageDraw, ImageFont
d = json.load(open(sys.argv[1]))
out = sys.argv[2]
X0, X1, Y0, Y1 = -9, 11, -7, 6.5
S = 60
W, H = int((X1-X0)*S), int((Y1-Y0)*S)
im = Image.new('RGB', (W, H), (235, 232, 220)); dr = ImageDraw.Draw(im)
def P(x, y): return ((x-X0)*S, H-(y-Y0)*S)
# pond outline
POND_C, POND_A, POND_B, POND_ROT = (-3.0, 1.0), 3.3, 2.5, math.radians(10)
pts = []
for i in range(120):
    th = i/120*math.tau
    wob = 1 + 0.10*math.sin(3*th+0.8) + 0.06*math.sin(5*th+2.1) + 0.04*math.sin(2*th)
    u, v = POND_A*math.cos(th)*1.0, POND_B*math.sin(th)
    # outline where pond_radius==1: u/A, v/B scaled by wobble
    uu, vv = u*wob, v*wob
    x = POND_C[0] + uu*math.cos(POND_ROT) - vv*math.sin(POND_ROT); y = POND_C[1] + uu*math.sin(POND_ROT) + vv*math.cos(POND_ROT)
    pts.append(P(x, y))
dr.polygon(pts, fill=(150, 190, 205), outline=(60, 110, 140))
# gravel court
dr.rectangle([*P(0.9, 1.9), *P(9.1, -5.9)], fill=(222, 218, 205), outline=(160, 150, 130))
# hall plinth
dr.rectangle([*P(-5.25, 10.3), *P(5.65, 4.7)], fill=(190, 160, 130))
# path
path = [(4.3,-5.6),(3.2,-3.1),(2.4,-1.0),(2.0,0.9),(2.2,2.8),(2.2,4.6)]
dr.line([P(*p) for p in path], fill=(120, 100, 80), width=3)
# bridge nodes
nodes = [(-0.55,-0.6),(-2.0,1.0),(-3.9,0.15),(-5.95,1.55)]
dr.line([P(*p) for p in nodes], fill=(130, 80, 40), width=10)
f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
for n, v in d.items():
    xy = v['xy']
    # convex hull
    pts = sorted(set((round(a,3), round(b,3)) for a, b in xy))
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0: lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0: upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    col = (120,120,115) if 'Lantern' not in n else (200, 90, 90)
    dr.polygon([P(*p) for p in hull], fill=col, outline=(40,40,40))
    short = n.replace('Pond edge stone ', 'P').replace('Stepping stone ', 'S').replace('Rock ', 'R').replace('Gravel rock ', 'G').replace('Bridge pier ', 'B').replace('Veranda step, lower', 'VL').replace('Veranda step', 'VU').replace('Water basin', 'BASIN').replace('Lantern ', 'L')
    dr.text(P(v['cx']-0.12, v['cy']+0.1), f"{short}", fill=(0,0,0), font=f)
# grid
for x in range(int(X0), int(X1)+1):
    dr.line([P(x, Y0), P(x, Y1)], fill=(200,200,200)); dr.text(P(x+0.02, Y0+0.3), str(x), fill=(90,90,90), font=f)
for y in range(int(Y0), int(Y1)+1):
    dr.line([P(X0, y), P(X1, y)], fill=(200,200,200)); dr.text(P(X0+0.05, y+0.15), str(y), fill=(90,90,90), font=f)
# camera
dr.ellipse([P(-5.2,-5.6)[0]-6, P(-5.2,-5.6)[1]-6, P(-5.2,-5.6)[0]+6, P(-5.2,-5.6)[1]+6], fill=(255,0,0))
dr.text(P(-5.0,-5.4), 'camera', fill=(255,0,0), font=f)
im.save(out)
print(im.size)
