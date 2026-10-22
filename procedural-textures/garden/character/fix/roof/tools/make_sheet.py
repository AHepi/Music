import sys, os
from PIL import Image, ImageDraw, ImageFont
D = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof'
C = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/concept/gen/'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/31 Fix - roof - before and after.jpg'
CW = int(sys.argv[1]) if len(sys.argv) > 1 else 470
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 78
def im(path, crop=None):
    i = Image.open(path).convert('RGB')
    if crop: i = i.crop(crop)
    return i
ROWS = [
 ('Hero view', im('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/out/finals/small/final_hero_1200.jpg'),
  im(D + '/out/finals5/fix_hero_1200.jpg'), im(C + 'hero_V3_nb2.jpg')),
 ('Veranda view', im('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/out/finals/small/final_veranda_1200.jpg'),
  im(D + '/out/finals5/fix_veranda_1200.jpg'), im(C + 'veranda_V2_nb2.jpg')),
 ('Roof, hero camera, 100 percent: tile glaze, moss cushions at eave and ridge, drip discs, slipped tiles', im(D + '/out/finals5/fix_hero_crop_roof_before.jpg'),
  im(D + '/out/finals5/fix_hero_crop_roof.jpg'), im(C + 'sheet_roof.jpg', (360, 250, 1960, 800))),
 ('Lantern cap from above: moss', im(D + '/out/before2/capA.jpg'), im(D + '/out/finals5/capA.jpg'), im(C + 'sheet_lantern.jpg', (120, 30, 960, 590))),
 ('Rocks up close: stripes and green lines', im(D + '/out/before2/lanternC.jpg'), im(D + '/out/finals5/lanternC.jpg'), im(C + 'sheet_pond.jpg', (700, 150, 1900, 900))),
 ('Wall cracks, hero camera, 100 percent', im(D + '/out/finals5/fix_hero_crop_wall_before.jpg'), im(D + '/out/finals5/fix_hero_crop_wall.jpg'), im(C + 'hero_V3_nb2.jpg', (1560, 380, 2528, 760))),
]
HEAD = ['Integrated final now', 'After the roof fix', 'The concept I followed']
font = ImageFont.load_default()
gap = 6; cap_h = 16
cells = []
total_h = 24
for (cap, a, b, c) in ROWS:
    ims = []
    for x in (a, b, c):
        h = int(x.height * CW / x.width)
        ims.append(x.resize((CW, h), Image.LANCZOS))
    rh = max(i.height for i in ims)
    cells.append((cap, ims, rh))
    total_h += rh + cap_h + gap
W = 3 * CW + 2 * gap
sheet = Image.new('RGB', (W, total_h), (24, 24, 24))
d = ImageDraw.Draw(sheet)
for k, t in enumerate(HEAD):
    d.text((k * (CW + gap) + 6, 6), t, fill=(255, 255, 255), font=font)
y = 24
for cap, ims, rh in cells:
    d.text((6, y + 2), cap, fill=(230, 210, 150), font=font)
    y += cap_h
    for k, i in enumerate(ims):
        sheet.paste(i, (k * (CW + gap), y))
    y += rh + gap
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sheet.save(OUT, quality=Q, optimize=True)
print(OUT, sheet.size, os.path.getsize(OUT))
