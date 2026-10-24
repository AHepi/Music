import numpy as np, json
from PIL import Image
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/'
OUT=P+'check-figures/'
ids=np.array(Image.open(P+'plate-facts/ids.png').convert('RGB')).astype(int)
facts=json.load(open(P+'plate-facts/facts.json'))
names=['man facing','man arms folded','man stooped','man hand on bar','man leaning']+['walker %d'%i for i in range(1,7)]
W,H=1536,2730
res={}
for n in names:
    col=np.array(facts['groups'][n]['colour'])
    m=(np.abs(ids-col).sum(2)<12)
    mi=Image.fromarray((m*255).astype(np.uint8)).resize((W,H),Image.BILINEAR)
    ma=np.array(mi)>127
    s=np.array(Image.open(P+'plate-facts/solo/'+n+'.png').convert('L'))
    si=np.array(Image.fromarray(((s>10)*255).astype(np.uint8)).resize((W,H),Image.BILINEAR))>127
    ys,xs=np.nonzero(si)
    fbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
    vis=int(ma.sum()); full=int(si.sum())
    res[n]={'full_box_plate_px':fbox,'full_area_px':full,'visible_area_px':vis,'visible_fraction':round(vis/full,3),'h_px':fbox[3]-fbox[1]+1,'w_px':fbox[2]-fbox[0]+1}
    mi.save(OUT+'masks/'+n.replace(' ','-')+'-visible.png')
    Image.fromarray((si*255).astype(np.uint8)).save(OUT+'masks/'+n.replace(' ','-')+'-full.png')
    print(n, res[n])
json.dump(res,open(OUT+'figure-boxes.json','w'),indent=1)
