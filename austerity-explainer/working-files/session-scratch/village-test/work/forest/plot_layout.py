import json, math
from PIL import Image, ImageDraw
d=json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest/layout.json'))
S=4.0; W,H=int(310*S),int(190*S)
def P(x,y): return ((x+155)*S, (95-y)*S)
im=Image.new('RGB',(W,H),(60,52,40)); dr=ImageDraw.Draw(im)
x0,y0,x1,y1=-50,-32,60,50
dr.rectangle([*P(x0,y1),*P(x1,y0)],fill=(100,125,70))
road=[(-140,-34),(-110,-18),(-80,-6),(-45,-1.5),(-12,0.5),(20,2),(52,-2.5),(85,-10),(115,-19),(140,-33)]
lane=[(20,2),(20.5,10),(22,18),(24,26),(24.3,34.2)]
dr.line([P(*p) for p in road],fill=(190,150,100),width=int(5*S)); dr.line([P(*p) for p in lane],fill=(190,150,100),width=int(3.4*S))
for cx,cy,sx,sy in [(-32,10,11.1,4.8),(-6,9.5,6.4,4.6),(-26,-10.5,7.4,4.6),(4,-8,3.7,4.4),(24,39,9.8,6)]:
    dr.rectangle([*P(cx-sx/2,cy+sy/2),*P(cx+sx/2,cy-sy/2)],fill=(210,200,170)); 
    dr.ellipse([*P(cx-14.8,cy+14.8),*P(cx+14.8,cy-14.8)],outline=(255,120,120))
cols={}
for n,role,x,y,z0,z1,wx,wy in d['crowns']:
    r=max(wx,wy)/2; px,py=P(x,y); dr.ellipse([px-r*S,py-r*S,px+r*S,py+r*S],outline=(30,70,30))
for n,role,x,y,z0,z1,wx,wy in d['trunks']:
    px,py=P(x,y); c=(250,230,60) if n.find('hero')>0 else (120,60,30); dr.ellipse([px-2,py-2,px+2,py+2],fill=c)
for n,role,x,y,z0,z1,wx,wy in d['small']:
    px,py=P(x,y); c={'stone.rock':(200,200,200),'plant.foliage':(60,200,60),'tree.bark':(255,150,0)}[role]; dr.ellipse([px-2,py-2,px+2,py+2],fill=c)
for name,(x,y,z,fx,fy) in d['cams'].items():
    px,py=P(x,y); dr.ellipse([px-4,py-4,px+4,py+4],fill=(255,0,255)); dr.line([px,py,px+fx*40*S,py-fy*40*S],fill=(255,0,255),width=1)
im.save('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest/pics/layout.png')
