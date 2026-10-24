# What this file does: puts the four forest villages side by side, one row per
# view (plugin village, Sonnet alone, Opus alone first and second pass), with
# plain labels, and saves one JPG sheet.
import sys
from PIL import Image, ImageDraw, ImageFont

scratch = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad"
output_path = sys.argv[1]
column_titles = [
    ("With the plugin", (240, 220, 160)),
    ("Sonnet alone", (160, 220, 240)),
    ("Opus alone, first pass", (200, 240, 170)),
    ("Opus alone, second pass", (255, 190, 150)),
]
rows = [
    ("Whole village from above", ["village-test/rebuild/wide.jpg", "village-control/pictures/01_village_from_above.jpg", "village-control-opus/pictures_pass1/01_village_from_above.jpg", "village-control-opus/pictures/01_village_from_above.jpg"]),
    ("Road at eye level", ["village-test/rebuild/road_eye.jpg", "village-control/pictures/02_road_at_eye_level.jpg", "village-control-opus/pictures_pass1/02_road_at_eye_height.jpg", "village-control-opus/pictures/02_road_at_eye_height.jpg"]),
    ("Stable close", ["village-test/rebuild/stable_close.jpg", "village-control/pictures/03_stable_close.jpg", "village-control-opus/pictures_pass1/03_stable_close.jpg", "village-control-opus/pictures/03_stable_close.jpg"]),
    ("Cottage close", ["village-test/rebuild/cottage_close.jpg", "village-control/pictures/04_cottage_close.jpg", "village-control-opus/pictures_pass1/04_cottage_close.jpg", "village-control-opus/pictures/04_cottage_close.jpg"]),
    ("Road surface close-up", ["village-test/rebuild/ground_closeup.jpg", "village-control/pictures/05_road_surface_closeup.jpg", "village-control-opus/pictures_pass1/05_road_surface_closeup.jpg", "village-control-opus/pictures/05_road_surface_closeup.jpg"]),
]
picture_width = 690
picture_height = 460
label_height = 40
header_height = 64
gap = 12
sheet_width = picture_width * 4 + gap * 5
sheet_height = header_height + len(rows) * (label_height + picture_height + gap) + gap
sheet = Image.new("RGB", (sheet_width, sheet_height), (24, 24, 24))
draw = ImageDraw.Draw(sheet)
try:
    big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
except OSError:
    big_font = small_font = ImageFont.load_default()
for column, (title, colour) in enumerate(column_titles):
    draw.text((gap + column * (picture_width + gap), 18), title, fill=colour, font=big_font)
y = header_height
for label, paths in rows:
    draw.text((gap, y + 8), label, fill=(230, 230, 230), font=small_font)
    y += label_height
    for column, path in enumerate(paths):
        picture = Image.open(f"{scratch}/{path}").convert("RGB")
        picture.thumbnail((picture_width, picture_height))
        x = gap + column * (picture_width + gap) + (picture_width - picture.width) // 2
        sheet.paste(picture, (x, y + (picture_height - picture.height) // 2))
    y += picture_height + gap
sheet.save(output_path, quality=88)
print(output_path, sheet.size)
