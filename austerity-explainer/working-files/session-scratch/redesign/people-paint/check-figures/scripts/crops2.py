import numpy as np, sys
from PIL import Image, ImageDraw
A='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
imgs={'plate':A+'people-test-plate.jpg','painting':A+'people-test-painting.png','behind':A+'people-test-painting-behind.jpg','state':A+'people-test-painting-state.png'}
def stack(box,scale,name,keys=('plate','painting','behind'),vertical=True):
    x0,y0,x1,y1=box
    tiles=[]
    for k in keys:
        im=Image.open(imgs[k]).convert('RGB').crop(box)
        im=im.resize((int((x1-x0)*scale),int((y1-y0)*scale)),Image.LANCZOS)
        d=ImageDraw.Draw(im); d.rectangle([0,0,90,20],fill=(0,0,0)); d.text((5,4),k,fill=(255,255,255))
        tiles.append(im)
    if vertical:
        W=tiles[0].width; H=sum(t.height for t in tiles)+8*(len(tiles)-1)
        out=Image.new('RGB',(W,H),(255,255,255)); y=0
        for t in tiles: out.paste(t,(0,y)); y+=t.height+8
    else:
        W=sum(t.width for t in tiles)+8*(len(tiles)-1); H=tiles[0].height
        out=Image.new('RGB',(W,H),(255,255,255)); x=0
        for t in tiles: out.paste(t,(x,0)); x+=t.width+8
    out.save(O+name, quality=92)
if __name__=='__main__':
    stack((630,1190,1010,1330),3.5,'walkers-x3.5.jpg')
    stack((180,1220,640,1880),1.0,'near-left.jpg',vertical=False)
    stack((700,1180,1230,1800),1.0,'near-right.jpg',vertical=False)
