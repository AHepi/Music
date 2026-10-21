"""What this file does (plain words): makes the two small pictures that are sent to the painter for the WET BEHIND PAINTING, the same way as for the front painting:
sent/image_1_behind_plate_810x1440.png = the wet plate with the near props hidden (plate/lockout_plate_wet_round2_no_props.png, 1536 x 2730) shrunk to 810 x 1440
(the same size the front painting's plate was sent at), and sent/image_2_front_painting_504x896.jpg = the finished front painting (paint/front_painting_final.png)
shrunk to 504 x 896 (the same size the first style picture was sent at). They are small on purpose: the painter's price is per megapixel and it is not known
whether pictures sent are charged as well as the one returned.
Run: python3 -I tools/make_pictures_to_send.py
"""
from PIL import Image
import os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'proc-work/street_wet/painter_round_2/'
Image.open(B + 'plate/lockout_plate_wet_round2_no_props.png').convert('RGB').resize((810, 1440), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_1_behind_plate_810x1440.png'))
Image.open(B + 'paint/front_painting_final.png').convert('RGB').resize((504, 896), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_2_front_painting_504x896.jpg'), quality=92)
for f in sorted(os.listdir(os.path.join(HERE, 'sent'))):
    p = os.path.join(HERE, 'sent', f); im = Image.open(p); print(f, im.size, os.path.getsize(p), 'bytes', round(im.size[0] * im.size[1] / 1e6, 3), 'MP')
