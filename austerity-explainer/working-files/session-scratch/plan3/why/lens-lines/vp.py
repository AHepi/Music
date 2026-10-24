from PIL import Image, ImageDraw
im = Image.open('../../compose/results/nano-free-camera.jpg').convert('RGB')
W,H = im.size
d = ImageDraw.Draw(im)
def ext(p,q,col,w=4):
    (x1,y1),(x2,y2)=p,q
    # extend to the vanishing area and back to frame edge
    pts=[]
    for t in (-3,3):
        pts.append((x1+(x2-x1)*t, y1+(y2-y1)*t))
    d.line(pts, fill=col, width=w)
lines = {
 'eaves L':((100,560),(700,940)),
 'kerb L':((0,1650),(800,1305)),
 'kerb R':((1030,1300),(920,1680)),
}
for k,(p,q) in lines.items(): ext(p,q,(255,60,60))
# horizon guess
d.line([(0,1185),(W,1185)], fill=(0,255,0), width=3)
im.resize((W//2,H//2)).save('vp_check.jpg', quality=88)
im.crop((700,900,1300,1500)).save('vp_zoom.jpg', quality=90)
