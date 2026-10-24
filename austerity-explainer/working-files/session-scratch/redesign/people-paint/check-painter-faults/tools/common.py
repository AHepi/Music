import numpy as np
from PIL import Image, ImageDraw
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test'
S='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint'
O=S+'/check-painter-faults'
def load(name, mode='RGB'):
    return np.array(Image.open(P+'/'+name).convert(mode))
def imgs():
    return dict(plate=load('people-test-plate.jpg'), helper=load('people-test-helper-plate.jpg'),
                paint=load('people-test-painting.png'), behind=load('people-test-painting-behind.jpg'),
                state=load('people-test-painting-state.png'), mask=load('people-test-painting-state-mask.png','L'))
def box_px(b, shape):
    H,W=shape[:2]
    return int(b[0]*W), int(b[1]*H), int(b[2]*W), int(b[3]*H)
def crop_row(arrs, b, out, scale=1.0, labels=None, gap=8):
    ims=[]
    for a in arrs:
        x0,y0,x1,y1=box_px(b,a.shape)
        im=Image.fromarray(a[y0:y1,x0:x1])
        if scale!=1.0: im=im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS)
        ims.append(im)
    W=sum(i.width for i in ims)+gap*(len(ims)-1); H=max(i.height for i in ims)+ (18 if labels else 0)
    C=Image.new('RGB',(W,H),'white'); x=0; d=ImageDraw.Draw(C)
    for k,i in enumerate(ims):
        C.paste(i,(x,18 if labels else 0))
        if labels: d.text((x+3,3),labels[k],fill=(0,0,0))
        x+=i.width+gap
    C.save(out, quality=92)
    return C.size
import json as _json
def group_masks():
    F=_json.load(open(S+'/plate-facts/facts.json'))
    ids=np.array(Image.open(S+'/plate-facts/ids.png').convert('RGB').resize((1536,2730),Image.NEAREST)).astype(int)
    out={}
    for g,v in F['groups'].items():
        out[g]=np.all(np.abs(ids-np.array(v['colour']))<=3,-1)
    return out
