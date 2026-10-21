from PIL import Image, ImageDraw, ImageFont
import sys, os
D = '../remote_out/r4/'
OUT = sys.argv[1]
quality = int(sys.argv[2]) if len(sys.argv) > 2 else 82
def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default(size=size)
rows = [('photo', '1  The courtyard camera'), ('lantern_rocks', '2  Close view: stone lantern and pond rocks'),
        ('hall_posts', '3  Close view: hall posts, veranda and plinth foot'), ('roof_edge', '4  Extra view: the front roof edge (shows what the kit could not reach)')]
CW, CH, M, CAP = 600, 400, 12, 28
W = 2 * CW + 3 * M
HEAD, FOOT = 74, 150
H = HEAD + len(rows) * (CH + CAP + M) + FOOT
bg = (28, 30, 28)
sheet = Image.new('RGB', (W, H), bg)
d = ImageDraw.Draw(sheet)
d.text((M, 10), 'The same weathering kit on the Japanese courtyard: one call, one settings file', font=font(21), fill=(240, 236, 225))
d.text((M, 40), 'First rough pass, dry, drawn small on the rented machine. Nothing was painted. Left = the scene as the add-on built it. Right = after.', font=font(14), fill=(190, 188, 178))
y = HEAD
for view, title in rows:
    d.text((M, y), title, font=font(15), fill=(235, 220, 170))
    d.text((M + CW + M, y), 'after', font=font(13), fill=(150, 200, 150))
    d.text((M + CW - 40, y + 2), 'before', font=font(13), fill=(170, 170, 170))
    for i, kind in enumerate(('before', 'after')):
        im = Image.open(D + f'r4_{view}_{kind}.jpg').convert('RGB').resize((CW, CH), Image.LANCZOS)
        sheet.paste(im, (M + i * (CW + M), y + CAP))
    y += CH + CAP + M
lines = [
    'Done by the settings file and one look file alone (no kit code changed): moss on the stones, lantern and the wall-cap tiles; a damp green band at the garden wall foot;',
    'water and splash marks at the plinth and stone feet; streaky film on plaster and timber; cracks and chips in stone and plaster; weeds at the gravel edge, between the',
    'stepping stones and in the roof-tile rows. The painter has not seen any of this: how much survives the repaint is unknown.',
    'Could NOT be done by settings alone (written down in the report): run-off streaks under the wall cap on the long garden wall (its wall sheet cannot be made), paint-layer',
    'moss on the roof tiles and deck (the roof sits in no object slot the kit can see), and lichen dots kept off plaster but on stone (per-material dials only work for soot).',
]
yy = y + 4
for ln in lines:
    d.text((M, yy), ln, font=font(13), fill=(205, 203, 192))
    yy += 22
sheet.save(OUT, quality=quality, optimize=True, progressive=True)
print(os.path.getsize(OUT), sheet.size)
