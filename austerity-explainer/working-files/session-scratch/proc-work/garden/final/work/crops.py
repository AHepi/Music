# What this does: cuts 100 percent crops (native pixels, no resizing) out of the 2400 x 1600 hero pictures and puts them on one sheet: real on the first row of each pair, painted below.
# usage: python3 -I crops.py OUT.jpg TILEW TILEH QUALITY   (regions are in the REGIONS list)
import sys
from PIL import Image, ImageDraw
out, tw, th, q = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
R = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final/renders/'
REGIONS = [('maple leaves', 520, 560), ('ground and tufts', 1850, 1380), ('gravel and stepping stones', 1900, 1010), ('rock feet and moss', 700, 1010),
           ('lantern', 1483, 800), ('bridge boards', 860, 1190), ('roof edge', 1250, 430), ('long wall', 2000, 650)]
cols = 4
rows = (len(REGIONS) + cols - 1) // cols
lab = 16
sheet = Image.new('RGB', (cols * tw, rows * (2 * th + 2 * lab)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
ims = {k: Image.open(R + k + '_hero.png').convert('RGB') for k in ('real', 'painted')}
for i, (name, cx, cy) in enumerate(REGIONS):
    x0 = min(max(cx - tw // 2, 0), 2400 - tw); y0 = min(max(cy - th // 2, 0), 1600 - th)
    gx, gy = (i % cols) * tw, (i // cols) * (2 * th + 2 * lab)
    for j, k in enumerate(('real', 'painted')):
        crop = ims[k].crop((x0, y0, x0 + tw, y0 + th))
        sheet.paste(crop, (gx, gy + j * (th + lab) + lab))
        d.text((gx + 4, gy + j * (th + lab) + 2), f'{k}: {name} (100 percent, from x {x0} y {y0})', fill=(235, 235, 235))
sheet.save(out, quality=q)
import os
print(out, sheet.size, os.path.getsize(out) // 1024, 'KB')
