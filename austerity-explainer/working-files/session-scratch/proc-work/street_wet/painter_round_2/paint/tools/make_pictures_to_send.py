"""What this file does (plain words): makes the two small pictures that are sent to the painter for the round 2 front painting, the SAME WAY as the first test:
sent/image_1_round2_wet_plate_810x1440.png (the new wet plate shrunk from 1536 x 2730 to 810 x 1440) and sent/image_2_style_504x896.jpg
(a plain copy of the first test's style picture, the chapter 2 Glasgow tenements painting; not re-made, so it is byte for byte the same).
They are small on purpose: the painter's price is per megapixel and it is not known whether pictures sent are charged as well as the one returned.
Run: python3 -I tools/make_pictures_to_send.py
"""
from PIL import Image
import os, shutil
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
Image.open(B + 'painter_round_2/plate/lockout_plate_wet_round2.png').convert('RGB').resize((810, 1440), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_1_round2_wet_plate_810x1440.png'))
shutil.copyfile(B + 'painter_test/sent/image_2_style_504x896.jpg', os.path.join(HERE, 'sent/image_2_style_504x896.jpg'))
for f in sorted(os.listdir(os.path.join(HERE, 'sent'))):
    p = os.path.join(HERE, 'sent', f); im = Image.open(p); print(f, im.size, os.path.getsize(p), 'bytes', round(im.size[0] * im.size[1] / 1e6, 3), 'MP')
