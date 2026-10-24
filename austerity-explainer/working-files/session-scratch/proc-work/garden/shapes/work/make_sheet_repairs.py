from PIL import Image, ImageDraw, ImageFont
import os
H = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/shapes/work'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/30 Japanese garden - pictures'
F = lambda s, b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
names = [('p1_bridge_side', 'Bridge from the side'), ('p2_step_side', 'Veranda steps from the side'), ('p3_lantern_front', 'Lantern from the front'), ('p4_wallcap_low', 'Wall cap seen from the veranda')]
W, Hh = 480, 320
bar = 26
sheet = Image.new('RGB', (W * 4, (Hh + bar) * 2 + 34), (28, 28, 30)); d = ImageDraw.Draw(sheet)
d.text((8, 8), 'Repairs, before (top) and after (bottom). Flat-colour check pictures: blue = piers, brown = boards and stringers, red or yellow = steps, red = cap, orange glow box.', font=F(13, True), fill=(235, 235, 235))
for row, folder in enumerate(('cu_before', 'cu_after')):
    for col, (n, cap) in enumerate(names):
        im = Image.open(os.path.join(H, folder, n + '.png')).convert('RGB').resize((W, Hh), Image.LANCZOS)
        x, y = col * W, 34 + row * (Hh + bar)
        sheet.paste(im, (x, y + bar))
        d.text((x + 6, y + 5), ('BEFORE  ' if row == 0 else 'AFTER  ') + cap, font=F(12, True), fill=(255, 210, 120) if row == 0 else (150, 230, 150))
sheet.save(os.path.join(OUT, '30 Shapes - repairs before and after (bridge, steps, lantern, wall cap).jpg'), quality=82)
print(os.path.getsize(os.path.join(OUT, '30 Shapes - repairs before and after (bridge, steps, lantern, wall cap).jpg')) // 1024, 'KB')
