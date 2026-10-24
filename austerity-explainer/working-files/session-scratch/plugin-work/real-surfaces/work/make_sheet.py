# What this does: puts the proof scene's two pictures (finished by the plugin 1.4.0 kit, then by the 1.5.0 kit; both drawn with EEVEE on a rented card, 900 x 600)
# side by side with a plain label over each and a 100 percent crop of the road edge under each, into one JPG under 400 KB.
# Run: python3 make_sheet.py BEFORE.jpg AFTER.jpg OUT.jpg
import sys
from PIL import Image, ImageDraw, ImageFont

before_path, after_path, out_path = sys.argv[1:4]
before, after = Image.open(before_path).convert('RGB'), Image.open(after_path).convert('RGB')
width, height = before.size
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 19)
labels = [
    ('BEFORE: plugin 1.4.0', ['surfaces made in code (flat colours, a soft lumpy road)', '6,657 weeds and 9,349 litter pieces spread evenly', 'no stones, no standing water']),
    ('AFTER: plugin 1.5.0', ['7 of 7 surfaces from free Poly Haven scans', '2,331 weeds, 54% at verges, wall feet, fences, between ruts;', '1,565 stones on bare ground; 80 small puddles in the ruts (damp)']),
]
crop_box = (300, 330, 600, 480)          # the road's edge and the near ruts, at 100 percent
crop_scale = 2
top = 100
crop_h = (crop_box[3] - crop_box[1]) * crop_scale
gap = 12
sheet = Image.new('RGB', (width * 2 + gap * 3, top + height + gap + crop_h + gap + 28), (24, 24, 24))
draw = ImageDraw.Draw(sheet)
for index, (picture, (title, lines)) in enumerate(zip((before, after), labels)):
    x = gap + index * (width + gap)
    draw.text((x, 8), title, font=bold, fill=(240, 240, 240))
    for row, line in enumerate(lines):
        draw.text((x, 32 + row * 20), line, font=font, fill=(205, 205, 205))
    sheet.paste(picture, (x, top))
    crop = picture.crop(crop_box).resize(((crop_box[2] - crop_box[0]) * crop_scale, crop_h), Image.NEAREST)
    sheet.paste(crop, (x, top + height + gap))
    draw.rectangle([crop_box[0] + x, crop_box[1] + top, crop_box[2] + x, crop_box[3] + top], outline=(255, 210, 60), width=2)
    draw.text((x + crop.size[0] + 12, top + height + gap + 4), 'the yellow box,\nmade twice as big', font=font, fill=(205, 205, 205))
draw.text((gap, sheet.size[1] - 24), 'The same small scene of plain boxes, finished once by each kit with the same settings (neglected, damp), drawn with EEVEE on a rented card.',
          font=font, fill=(170, 170, 170))
for quality in (88, 82, 76, 70):
    sheet.save(out_path, quality=quality, optimize=True)
    import os
    if os.path.getsize(out_path) < 400_000:
        break
print(out_path, sheet.size, os.path.getsize(out_path), 'bytes, quality', quality)
