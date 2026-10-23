# What this file does: puts the plugin village's pictures and the no-plugin
# village's pictures next to each other, one row per view, with plain labels,
# and saves one JPG sheet.
import sys
from PIL import Image, ImageDraw, ImageFont

scratch = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad"
output_path = sys.argv[1]
rows = [
    ("Whole village from above", "village-test/rebuild/wide.jpg", "village-control/pictures/01_village_from_above.jpg"),
    ("Road at eye level", "village-test/rebuild/road_eye.jpg", "village-control/pictures/02_road_at_eye_level.jpg"),
    ("Stable close", "village-test/rebuild/stable_close.jpg", "village-control/pictures/03_stable_close.jpg"),
    ("Cottage close", "village-test/rebuild/cottage_close.jpg", "village-control/pictures/04_cottage_close.jpg"),
    ("Road surface close-up", "village-test/rebuild/ground_closeup.jpg", "village-control/pictures/05_road_surface_closeup.jpg"),
]
picture_width = 960
picture_height = 540
label_height = 44
header_height = 70
gap = 12
sheet_width = picture_width * 2 + gap * 3
sheet_height = header_height + len(rows) * (label_height + picture_height + gap) + gap
sheet = Image.new("RGB", (sheet_width, sheet_height), (24, 24, 24))
draw = ImageDraw.Draw(sheet)
try:
    big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except OSError:
    big_font = small_font = ImageFont.load_default()
draw.text((gap, 18), "LEFT: with the plugin (1.5.0 rebuild)", fill=(240, 220, 160), font=big_font)
draw.text((picture_width + gap * 2, 18), "RIGHT: no plugin (Sonnet on its own)", fill=(160, 220, 240), font=big_font)
y = header_height
for label, left_path, right_path in rows:
    draw.text((gap, y + 8), label, fill=(230, 230, 230), font=small_font)
    y += label_height
    for column, path in enumerate((left_path, right_path)):
        picture = Image.open(f"{scratch}/{path}").convert("RGB")
        picture.thumbnail((picture_width, picture_height))
        x = gap + column * (picture_width + gap) + (picture_width - picture.width) // 2
        sheet.paste(picture, (x, y + (picture_height - picture.height) // 2))
    y += picture_height + gap
sheet.save(output_path, quality=88)
print(output_path, sheet.size)
