import sys
from PIL import Image
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/'
REF='/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg'
ims={'v5':Image.open(B+'final/composed-end-5.png').convert('RGB'),
     'v4':Image.open(B+'final/composed-end-4.png').convert('RGB'),
     'ref':Image.open(REF).convert('RGB')}
def crop(im,box,scale=1.0):
    W,H=im.size; x0,y0,x1,y1=box
    c=im.crop((int(x0*W),int(y0*H),int(x1*W),int(y1*H)))
    return c
def side(name, boxes, height=900):
    # boxes: dict key->box
    cs=[]
    for k,b in boxes.items():
        c=crop(ims[k],b); r=height/c.size[1]; cs.append(c.resize((int(c.size[0]*r),height),Image.LANCZOS))
    W=sum(c.size[0] for c in cs)+10*(len(cs)-1)
    out=Image.new('RGB',(W,height),(255,255,255)); x=0
    for c in cs: out.paste(c,(x,0)); x+=c.size[0]+10
    out.save(name)
g=(0.40,0.40,1.0,0.97)
side('group_v4_v5.png',{'v4':g,'v5':g})
side('group_v5_ref.png',{'v5':g,'ref':(0.42,0.40,1.0,0.97)})
l=(0.70,0.17,1.0,0.36)
side('lamp_v4_v5.png',{'v4':(0.75,0.08,1.0,0.27),'v5':l},600)
left=(0.0,0.25,0.5,0.62)
side('left_v4_v5.png',{'v4':left,'v5':left},700)
side('left_v5_ref.png',{'v5':left,'ref':left},700)
w=(0.85,0.45,1.0,0.85)
side('rightwall_v4_v5.png',{'v4':w,'v5':w},800)
d=(0.44,0.61,0.70,0.70)
side('drum_v4_v5.png',{'v4':d,'v5':d},400)
