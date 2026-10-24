"""What this does: a before/after sheet of the Works' plates at phone size (scratch, round 6 set): round 5's plate
above, round 6's below, each 360 pixels wide (about a phone screen's width in its own points), labelled; a plate that
did not exist before shows a grey box above.
Use: python3 before_after.py BEFORE_FOLDER AFTER_FOLDER OUT.jpg NAME [NAME ...]"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
names = sys.argv[4:]
W, H, GAP, LABEL = 360, 640, 12, 34
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
sheet = Image.new('RGB', (len(names) * (W + GAP) + GAP, 2 * (H + LABEL) + 3 * GAP), (245, 245, 240))
draw = ImageDraw.Draw(sheet)
for column, name in enumerate(names):
    x = GAP + column * (W + GAP)
    for row, (folder, when) in enumerate(((before, 'round 5'), (after, 'round 6'))):
        y = GAP + row * (H + LABEL + GAP)
        path = os.path.join(folder, f'{name}.jpg')
        draw.text((x, y + 6), f'{name.replace("works-", "").replace("-plate", "")}: {when}', fill=(20, 20, 20), font=font)
        if os.path.exists(path):
            sheet.paste(Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS), (x, y + LABEL))
        else:
            draw.rectangle((x, y + LABEL, x + W, y + LABEL + H), fill=(200, 200, 200))
            draw.text((x + 20, y + LABEL + H // 2), 'new in round 6', fill=(60, 60, 60), font=font)
sheet.save(out, quality=88)
print('wrote', out, sheet.size)
