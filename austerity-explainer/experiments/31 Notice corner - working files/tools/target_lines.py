"""What this does: draws the liked picture's street lines (the yellow lines of "30 Why it works - do the
strongest things agree") on a test picture at the same places, beside the liked picture, so you can
see whether the test picture's own lines follow them. Input: test picture, liked picture, output."""
import sys
from PIL import Image, ImageDraw
test_path, liked_path, output_path = sys.argv[1:4]
MEET = (0.7064, 0.4241)
STARTS = [(0.0, 0.1806), (0.0, 0.6014), (0.5794, 0.6177)]   # left roofline, left kerb, right kerb
def draw(image):
    image = image.convert('RGB').resize((540, 960))
    d = ImageDraw.Draw(image)
    for x, y in STARTS:
        d.line([(x * 540, y * 960), (MEET[0] * 540, MEET[1] * 960)], fill=(255, 225, 0), width=3)
    r = 22
    d.ellipse([MEET[0] * 540 - r, MEET[1] * 960 - r, MEET[0] * 540 + r, MEET[1] * 960 + r], outline=(255, 40, 40), width=4)
    return image
sheet = Image.new('RGB', (1090, 960), (20, 20, 24))
sheet.paste(draw(Image.open(liked_path)), (0, 0))
sheet.paste(draw(Image.open(test_path)), (550, 0))
sheet.save(output_path, quality=88)
