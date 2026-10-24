# What this does: builds the sheets for the person from the full-size pictures (labelled panels side by side, JPG under 400 KB each, written to the pictures folder).
import os, sys
from PIL import Image, ImageDraw, ImageFont
R = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final/renders/'
ORIG = '/home/user/Music/japanese-courtyard/01 Japanese courtyard - golden hour photo.png'
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/30 Japanese garden - pictures/'
try:
    FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
except Exception:
    FONT = ImageFont.load_default()

def panel_sheet(name, panels, pw, ph, cols, quality):
    rows = (len(panels) + cols - 1) // cols
    bar = 30
    gap = 6
    W = cols * pw + (cols - 1) * gap
    H = rows * (ph + bar) + (rows - 1) * gap
    sheet = Image.new('RGB', (W, H), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    for k, (label, path) in enumerate(panels):
        im = Image.open(path).convert('RGB').resize((pw, ph), Image.LANCZOS)
        x, y = (k % cols) * (pw + gap), (k // cols) * (ph + bar + gap)
        sheet.paste(im, (x, y + bar))
        d.text((x + 8, y + 5), label, fill=(240, 240, 240), font=FONT)
    out = P + name
    q = quality
    while True:
        sheet.save(out, quality=q, optimize=True, progressive=True)
        kb = os.path.getsize(out) / 1024
        if kb < 390 or q < 50:
            break
        q -= 4
    print(name, sheet.size, round(kb), 'KB, quality', q)

panel_sheet('30 Before and after - the original photo and the realistic garden.jpg',
            [('Before: the original golden-hour picture (18 October)', ORIG), ('After: the realistic garden (Cycles, 512 samples, 2400 x 1600)', R + 'real_hero.png')], 1000, 667, 2, 82)
panel_sheet('30 Side by side - realistic and painted.jpg',
            [('Realistic look (photographed surfaces, weathering, soft stones)', R + 'real_hero.png'), ('Painted look (flat planes, broad colour passages, no smooth curves)', R + 'painted_hero.png')], 1000, 667, 2, 82)
panel_sheet('30 Veranda view.jpg',
            [('Veranda view, realistic', R + 'real_veranda.png'), ('Veranda view, painted', R + 'painted_veranda.png')], 1000, 667, 2, 82)
panel_sheet('30 Blue evening - lantern lit.jpg',
            [('Blue evening from the original view (realistic, lantern lit)', R + 'evening_hero.png'), ('Blue evening from the veranda (realistic)', R + 'evening_veranda.png')], 1000, 667, 2, 82)
