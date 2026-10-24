# What this does: makes the three small review pictures for the report (plain Python + Pillow, no Blender): the photo with ranked weak spots marked,
#   the four delivery-check close-ups with captions, and the veranda preview with a caption bar. Reads only files named below.
from PIL import Image, ImageDraw, ImageFont
import os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/29 Japanese garden - pictures'
F = lambda s, b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
photo = Image.open('/home/user/Music/japanese-courtyard/01 Japanese courtyard - golden hour photo.png').convert('RGB').resize((1200, 800), Image.LANCZOS)

# ---- 1: ranked weak spots
marks = [(1, [(230, 235), (110, 330)], 'Maple: flat paper stars, too big, all one orange (10 % of the picture)'),
         (2, [(150, 470), (320, 455), (690, 640)], 'Rocks: 43 stones of 50 to 72 flat faces each, visible facets (9 %)'),
         (3, [(330, 75), (1000, 190)], 'Sky and hills: sky is ONE colour; hills are flat cut-outs (22 %)'),
         (4, [(900, 720)], 'Ground: blotchy noise carpet, no grass or moss detail (16 %)'),
         (5, [(960, 520)], 'Gravel court: pink-brown, lowest contrast, hard edge (7 %)'),
         (6, [(300, 665), (520, 565)], 'Bridge: identical smooth boards, corner boards stick out, hover (6 %)'),
         (7, [(885, 255)], 'Pine: lime grape-like blobs (2 %)'),
         (8, [(1010, 345)], 'Plaster wall: clean cream, no stains or damp foot (4 %)'),
         (9, [(420, 735)], 'Water: opaque dark teal, no depth, odd white screen reflections (6 %)'),
         (10, [(742, 425)], 'Lantern: glow box buried in the stone; lozenge stack (1 %)'),
         (11, [(560, 190)], 'Roof: the best part; only too uniform and crushed black (5 %)')]
d = ImageDraw.Draw(photo)
for n, pts, _ in marks:
    for (x, y) in pts:
        col = (40, 160, 70) if n == 11 else (215, 30, 40)
        d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=col, outline=(255, 255, 255), width=3)
        tw = d.textlength(str(n), font=F(20, True)); d.text((x - tw / 2, y - 12), str(n), font=F(20, True), fill=(255, 255, 255))
legend_h = 6 * 34 + 24
canvas = Image.new('RGB', (1200, 800 + legend_h), (28, 28, 30)); canvas.paste(photo, (0, 0))
d = ImageDraw.Draw(canvas)
d.text((14, 800 + 6), 'Weakest first (share of the picture). Red = weak, green = fine.   Measured on the final 2400 x 1600 photo.', font=F(15, True), fill=(235, 235, 235))
for i, (n, _, text) in enumerate(marks):
    col, row = divmod(i, 6)
    x = 14 + col * 600; y = 800 + 34 + row * 34
    c = (40, 160, 70) if n == 11 else (215, 30, 40)
    d.ellipse((x, y, x + 24, y + 24), fill=c); tw = d.textlength(str(n), font=F(14, True)); d.text((x + 12 - tw / 2, y + 4), str(n), font=F(14, True), fill=(255, 255, 255))
    d.text((x + 32, y + 3), text, font=F(14), fill=(235, 235, 235))
canvas.save(os.path.join(OUT, '29 Scene - the weakest spots ranked on the photo.jpg'), quality=80)

# ---- 2: delivery-check close-ups
names = [('p1_bridge_side', '1  Bridge from the side: boards (brown) hover 2.5 to 7 cm above their pier (blue)'),
         ('p2_step_side', '2  Veranda step (top yellow) floats 23 cm above the ground, touches nothing'),
         ('p3_lantern_front', '3  Lantern: a stack of lozenges; the glow box (red) is buried in the stone'),
         ('p4_wallcap_low', '4  Wall cap seen from 1.85 m: sky shows through the 6.5 cm gap under it')]
ims = [Image.open(os.path.join(HERE, 'out', n + '.png')).convert('RGB') for n, _ in names]
W, H = ims[0].size; bar = 34
sheet = Image.new('RGB', (W * 2, (H + bar) * 2), (28, 28, 30)); d = ImageDraw.Draw(sheet)
for i, (im, (_, cap)) in enumerate(zip(ims, names)):
    x, y = (i % 2) * W, (i // 2) * (H + bar)
    sheet.paste(im, (x, y + bar)); d.text((x + 8, y + 8), cap, font=F(13, True), fill=(240, 240, 240))
sheet.save(os.path.join(OUT, '29 Scene - delivery check close-ups (bridge, veranda step, lantern, wall cap).jpg'), quality=80)

# ---- 3: veranda preview
v = Image.open(os.path.join(HERE, 'out', 'veranda_a.png')).convert('RGB')
vc = Image.new('RGB', (v.width, v.height + 58), (28, 28, 30)); vc.paste(v, (0, 0)); d = ImageDraw.Draw(vc)
d.text((8, v.height + 6), 'Veranda view with today\'s scene (EEVEE preview, 640 wide, camera 3.6, 5.3, 1.55 m).', font=F(13, True), fill=(240, 240, 240))
d.text((8, v.height + 28), 'Behind the pond: one flat orange sky and a dark band. The hills only exist on the hall side; the ground ends at y = -8.5 m.', font=F(12), fill=(225, 225, 225))
vc.save(os.path.join(OUT, '29 Scene - veranda view with today scene, EEVEE preview.jpg'), quality=82)
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, 'KB')
