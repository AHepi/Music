# What this does: makes the fresh checker's side-by-side sheet: the first village on the left and the rebuilt village on the right in the same four
# views (wide, road_eye, stable_close, cottage_close), then the road close-up of each village next to a crop of the coal mine's ground of the same
# size in pixels (540 x 360 from each full picture, all shrunk by the same amount). It saves a JPG under 400 KB.
# Use: python3 make_sheet.py OUT.jpg MEASURES.json
import io
import json
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/'
MINE = '/home/user/Music/mine-scene/01 Coal mine - dusk photo 1080x1920.png'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
BOLD = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
output_path, measures_path = sys.argv[1], sys.argv[2]
measures = json.load(open(measures_path))['crops']
WIDTH = 1200
VIEW = (600, 400)
LABEL = 26
VIEWS = [('wide', 'View_wide.jpg', 'wide.jpg'), ('road_eye', 'View_road_eye.jpg', 'road_eye.jpg'),
         ('stable_close', 'View_stable_close.jpg', 'stable_close.jpg'), ('cottage_close', 'View_cottage_close.jpg', 'cottage_close.jpg')]
CROP = 400                    # each 540 x 360 crop is shown 400 x 267 (the same shrink for all three)
crop_height = round(360 * CROP / 540)
height = 44 + len(VIEWS) * (VIEW[1] + LABEL) + 34 + LABEL + crop_height + 3 * 22 + 10
sheet = Image.new('RGB', (WIDTH, height), (245, 245, 242))
draw = ImageDraw.Draw(sheet)
draw.text((10, 10), 'First village (plugin 1.4.0)', font=BOLD, fill=(20, 20, 20))
draw.text((610, 10), 'Rebuilt village (plugin 1.5.0)', font=BOLD, fill=(20, 20, 20))
y = 44
for name, before, after in VIEWS:
    sheet.paste(Image.open(BASE + 'main-session-look/out/' + before).convert('RGB').resize(VIEW, Image.LANCZOS), (0, y))
    sheet.paste(Image.open(BASE + 'rebuild/' + after).convert('RGB').resize(VIEW, Image.LANCZOS), (600, y))
    draw.text((10, y + VIEW[1] + 3), f'{name} (same camera both sides)', font=FONT, fill=(40, 40, 40))
    y += VIEW[1] + LABEL
draw.text((10, y + 6), 'Road close-up, same camera, and the coal mine\'s ground: crops of the same size (540 x 360 pixels each)', font=BOLD, fill=(20, 20, 20))
y += 34
crops = [('First village road', BASE + 'verify/work/before-closeup/ground_ruts_preview.jpg', (330, 440, 870, 800), 'road close-up, first village'),
         ('Rebuilt village road', BASE + 'rebuild/ground_closeup.jpg', (330, 440, 870, 800), 'road close-up, rebuilt village'),
         ("Coal mine's ground", MINE, (0, 1520, 540, 1880), "coal mine's ground")]
for index, (title, path, box, key) in enumerate(crops):
    x = index * CROP
    draw.text((x + 8, y), title, font=FONT, fill=(40, 40, 40))
    sheet.paste(Image.open(path).convert('RGB').crop(box).resize((CROP, crop_height), Image.LANCZOS), (x, y + LABEL))
    m = measures[key]
    lines = [f"fine grain {m['fine_detail']:.2f}, middle {m['middle_detail']:.2f}",
             f"large shapes {m['coarse_detail']:.2f}, lumps {m['lumps']}",
             f"colour spread {m['colour_spread_lab']:.1f}"]
    for row, text in enumerate(lines):
        draw.text((x + 8, y + LABEL + crop_height + 2 + row * 22), text, font=FONT, fill=(40, 40, 40))
for quality in (85, 80, 75, 70, 65, 60):
    buffer = io.BytesIO()
    sheet.save(buffer, 'JPEG', quality=quality, optimize=True)
    if buffer.tell() < 400_000:
        break
with open(output_path, 'wb') as handle:
    handle.write(buffer.getvalue())
print(output_path, sheet.size, buffer.tell(), 'bytes, quality', quality)
