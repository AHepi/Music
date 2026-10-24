import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2, json
I=imgs()
F=json.load(open(S+'/plate-facts/facts.json'))
ids=np.array(Image.open(S+'/plate-facts/ids.png').convert('RGB').resize((1536,2730),Image.NEAREST))
def gm(name):
    c=F['groups'][name]['colour']; return np.all(ids==np.array(c),-1)
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
Lp,Lq,Lb=L(I['plate']),L(I['paint']),L(I['behind'])
def reg(b):
    m=np.zeros(Lp.shape,bool); x0,y0,x1,y1=box_px(b,Lp.shape); m[y0:y1,x0:x1]=True; return m
R={}
for g in F['groups']:
    m=gm(g)
    R[g]=m
R['sky (upper left)']=reg((0.0,0.0,0.35,0.12))
R['left near house wall']=reg((0.03,0.25,0.11,0.40))
R['right near stone wall']=reg((0.86,0.30,0.96,0.70))
R['road setts left middle']=reg((0.0,0.70,0.15,0.85))
R['pavement near (bottom)']=reg((0.45,0.80,0.70,0.90))
R['step risers']=reg((0.76,0.89,0.94,0.93))
print('%-26s %8s %8s %8s %8s'%('region','pixels','plate L','paint L','change'))
for k,m in R.items():
    print('%-26s %8d %8.1f %8.1f %+8.1f'%(k,m.sum(),Lp[m].mean(),Lq[m].mean(),Lq[m].mean()-Lp[m].mean()))
print('whole frame %.1f %.1f'%(Lp.mean(),Lq.mean()))
