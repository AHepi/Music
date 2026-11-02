# What this does: makes the pictures for the owner to judge: each variation with its letter stamped in a corner,
# saved under "45 Brushstrokes - <letter> - <what it is>.png", plus one sheet of close-ups of the tea house's front.
import os
import sys
from PIL import Image, ImageDraw, ImageFont

out_folder = sys.argv[1]
base = '/home/claude/blind-test-2/plugin-build/round-2.png'
variations = '/home/claude/brushstroke-trial/out/variations'
entries = [('A', 'no strokes', base)]
for name in sorted(os.listdir(variations)):
    if name.endswith('.png') and ' - strokes only' not in name and name[1] == ' ':
        entries.append((name[0], name[2:-4], os.path.join(variations, name)))
font_paths = ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
font = next((ImageFont.truetype(p, 40) for p in font_paths if os.path.exists(p)), ImageFont.load_default())
small = next((ImageFont.truetype(p, 22) for p in font_paths if os.path.exists(p)), ImageFont.load_default())
os.makedirs(out_folder, exist_ok=True)
crops = []
for letter, what, path in entries:
    picture = Image.open(path).convert('RGB')
    stamped = picture.copy()
    draw = ImageDraw.Draw(stamped)
    draw.text((16, 12), letter, font=font, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    stamped.save(os.path.join(out_folder, '45 Brushstrokes - %s - %s.png' % (letter, what)))
    crop = picture.crop((105, 165, 435, 615)).resize((330 * 2 // 2, 450 * 2 // 2), Image.LANCZOS)
    crop = picture.crop((105, 165, 435, 615))
    crop_draw = ImageDraw.Draw(crop)
    crop_draw.text((10, 6), letter, font=font, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0))
    crops.append(crop)
columns = 2
rows = (len(crops) + columns - 1) // columns
sheet = Image.new('RGB', (columns * 330 + (columns - 1) * 6, rows * 450 + (rows - 1) * 6), (20, 20, 20))
for k, crop in enumerate(crops):
    sheet.paste(crop, ((k % columns) * 336, (k // columns) * 456))
sheet.save(os.path.join(out_folder, '45 Brushstrokes - close-ups of the tea house front.png'))
print('\n'.join('%s  %s' % (l, w) for l, w, p in entries))
