# What this does: puts pictures into one contact sheet. usage: python3 -I sheet.py OUT.jpg COLS CELLW CELLH label=path label=path ...   (JPG quality 82)
import sys
from PIL import Image, ImageDraw, ImageFont
out, cols, cw, ch = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
items = [a.split('=', 1) for a in sys.argv[5:]]
rows = (len(items) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cw, rows * (ch + 18)), (24, 24, 24))
d = ImageDraw.Draw(sheet)
for k, (label, path) in enumerate(items):
    im = Image.open(path).convert('RGB').resize((cw, ch), Image.LANCZOS)
    x, y = (k % cols) * cw, (k // cols) * (ch + 18)
    sheet.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), label, fill=(235, 235, 235))
sheet.save(out, quality=82)
print(out, sheet.size)
