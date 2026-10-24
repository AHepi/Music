from PIL import Image, ImageDraw
im = Image.open('../../compose/results/nano-free-camera.jpg').convert('RGB')
W,H = im.size
d = ImageDraw.Draw(im)
for x,col in ((930,(80,160,255)),(1240,(255,230,80))):
    d.line([(x,0),(x,H)], fill=col, width=5)
# thirds
for x in (W/3, 2*W/3): d.line([(x,0),(x,H)], fill=(255,255,255), width=2)
for y in (H/3, 2*H/3): d.line([(0,y),(W,y)], fill=(255,255,255), width=2)
# flame triangle
pts=[(1204,523),(901,1775),(1238,1906)]
d.line(pts+[pts[0]], fill=(255,80,0), width=4)
d.line([(0,1185),(W,1185)], fill=(0,255,0), width=3)
im.resize((W//2,H//2)).save('cols_check.jpg', quality=88)
