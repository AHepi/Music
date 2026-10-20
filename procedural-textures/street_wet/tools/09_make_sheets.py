# What this does (plain Python, no Blender): puts the pictures side by side with labels, as JPEG sheets for looking at.
#   sheets/street_dry_wet.jpg   A | B | C | D : the main camera view, A = the street as it is today, B = the new materials dry, C = wet, D = wet with heavier rain
#   sheets/wet_closeups.jpg     the setts (top) and the foot of a wall beside a gas lamp (bottom), dry (left) and wet (right)
# Run: python3 -I tools/09_make_sheets.py
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BOLD = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)


def labelled(images, labels, notes, path, columns, gap=8, header=0, title=None):
    cell_w, cell_h = images[0].size
    rows = (len(images) + columns - 1) // columns
    title_h = 40 if title else 0
    sheet = Image.new('RGB', (columns * cell_w + (columns + 1) * gap, title_h + rows * (cell_h + 62) + gap), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)
    if title:
        draw.text((gap, 8), title, font=BOLD, fill=(235, 235, 235))
    for index, (image, label, note) in enumerate(zip(images, labels, notes)):
        x = gap + (index % columns) * (cell_w + gap)
        y = title_h + (index // columns) * (cell_h + 62)
        sheet.paste(image.convert('RGB'), (x, y + 56))
        draw.text((x + 2, y + 2), label, font=BOLD, fill=(240, 220, 160))
        draw.text((x + 2, y + 31), note, font=SMALL, fill=(190, 190, 195))
    sheet.save(path, quality=88)
    print('wrote', path, sheet.size, os.path.getsize(path) // 1024, 'KB')


def load(name):
    return Image.open(os.path.join(ROOT, 'work', name))


main = [load(f'r07/main_{state}.png') for state in ('today', 'dry', 'wet', 'heavy')]
labelled(main, ['A  today', 'B  new materials, dry', 'C  wet', 'D  wet, heavier rain'],
         ['the street as the film has it', 'real roughness + height pictures, layer at 0', 'wetness 0.85, puddles 0.5', 'wetness 1.0, puddles 0.8'],
         os.path.join(ROOT, 'sheets', 'street_dry_wet.jpg'), 4, title='Main camera, Cycles, 540 x 960, 32 samples, same lights in all four')
if all(os.path.exists(os.path.join(ROOT, 'work', f'r08/{c}_{s}.png')) for c in ('close_road', 'wall_lamp') for s in ('dry', 'wet')):
    pics = [load(f'r08/{c}_{s}.png') for c in ('close_road', 'wall_lamp') for s in ('dry', 'wet')]
    labelled(pics, ['setts, dry', 'setts, wet', 'wall foot by the first gas lamp, dry', 'wall foot by the first gas lamp, wet'],
             ['new materials, layer at 0', 'wetness 0.85, puddles 0.5', 'new materials, layer at 0', 'wetness 0.85, puddles 0.5'],
             os.path.join(ROOT, 'sheets', 'wet_closeups.jpg'), 2, title='Close-ups, Cycles, same lights, dry against wet')
