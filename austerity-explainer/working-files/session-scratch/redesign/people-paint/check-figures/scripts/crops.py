import numpy as np, sys
from PIL import Image, ImageDraw, ImageFont
A='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
imgs={'plate':A+'people-test-plate.jpg','painting':A+'people-test-painting.png','behind':A+'people-test-painting-behind.jpg','state':A+'people-test-painting-state.png'}
def strip(box,scale,name,keys=('plate','painting','behind')):
    x0,y0,x1,y1=box
    tiles=[]
    for k in keys:
        im=Image.open(imgs[k]).convert('RGB').crop(box)
        im=im.resize((int((x1-x0)*scale),int((y1-y0)*scale)),Image.LANCZOS)
        d=ImageDraw.Draw(im); d.rectangle([0,0,140,28],fill=(0,0,0)); d.text((6,6),k,fill=(255,255,255))
        tiles.append(im)
    W=sum(t.width for t in tiles)+10*(len(tiles)-1); H=tiles[0].height
    out=Image.new('RGB',(W,H),(255,255,255)); x=0
    for t in tiles: out.paste(t,(x,0)); x+=t.width+10
    out.save(O+name)
strip((620,1180,1010,1340),3,'walkers-x3.jpg')
strip((180,1220,640,1880),1.2,'near-left-x1.2.jpg')
strip((700,1180,1230,1800),1.2,'near-right-x1.2.jpg')
