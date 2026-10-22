from PIL import Image, ImageDraw, ImageFont
import os
H = 'proc-work/garden/shapes/out/preview3'
OUT = 'proc-work/30 Japanese garden - pictures'
F = lambda s, b=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if b else ''), s)
def load(look, name, size):
    return Image.open(os.path.join(H, f'rp_{look}_{name}.jpg')).convert('RGB').resize(size, Image.LANCZOS)
# 1: hero, real beside painted
W, Hh, bar = 720, 480, 30
sheet = Image.new('RGB', (W * 2 + 6, Hh + bar + 44), (28, 28, 30)); d = ImageDraw.Draw(sheet)
for i, (look, cap) in enumerate((('real', 'REALISTIC: rocks softened and weathered, smooth shading'), ('painted', 'PAINTED: rocks keep many unequal flat planes, no smoothing'))):
    x = i * (W + 6)
    d.text((x + 8, 7), cap, font=F(13, True), fill=(255, 215, 130) if i == 0 else (150, 230, 160))
    sheet.paste(load(look, 'hero', (W, Hh)), (x, bar))
d.text((8, bar + Hh + 5), 'Shapes stage only (builder 1): repairs, new lantern, rocks, raked gravel with kerb, stepping stones, walls and caps, basin set, shore stones.', font=F(12), fill=(225, 225, 225))
d.text((8, bar + Hh + 24), 'Surfaces, plants, sky and light are still the old ones (other builders). EEVEE preview 960 x 640 drawn on RunPod, shown at 75 percent.', font=F(12), fill=(225, 225, 225))
p1 = os.path.join(OUT, '30 Shapes - the garden after the shapes stage, realistic beside painted.jpg')
sheet.save(p1, quality=84)
# 2: close-ups
names = [('lantern', 'Lantern'), ('rocks', 'Rocks and shore'), ('gravel', 'Raked gravel and kerb'), ('basin', 'Water-basin set')]
w, h, bar = 460, 307, 24
sheet = Image.new('RGB', (w * 4 + 9, (h + bar) * 2 + 30), (28, 28, 30)); d = ImageDraw.Draw(sheet)
d.text((8, 7), 'Close-ups of the new shapes (EEVEE previews, grey and brown tones are the old placeholder surfaces). Top: realistic. Bottom: painted.', font=F(13, True), fill=(235, 235, 235))
for r, look in enumerate(('real', 'painted')):
    for c, (n, cap) in enumerate(names):
        x, y = c * (w + 3), 30 + r * (h + bar)
        d.text((x + 6, y + 5), ('REAL  ' if r == 0 else 'PAINTED  ') + cap, font=F(12, True), fill=(255, 215, 130) if r == 0 else (150, 230, 160))
        sheet.paste(load(look, n, (w, h)), (x, y + bar))
p2 = os.path.join(OUT, '30 Shapes - close-ups lantern rocks gravel basin, realistic and painted.jpg')
sheet.save(p2, quality=80)
for p in (p1, p2):
    print(os.path.basename(p), os.path.getsize(p) // 1024, 'KB', Image.open(p).size)
