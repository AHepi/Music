"""What this file does (plain words): makes the two small copies of pictures that are sent to the painter:
sent/image_1_wet_plate_810x1440.png (the wet plate) and sent/image_2_style_504x896.jpg (the series' style picture,
the chapter 2 Glasgow tenements painting). They are smaller than in earlier paintings (plate 1536x2730 and style 768x1368)
ON PURPOSE: the painter's price is per megapixel and it is not known whether pictures sent are charged as well as the
one returned, so they are kept small enough that even then the whole job stays under the US$0.30 limit.
Run: python3 -I tools/make_pictures_to_send.py
"""
from PIL import Image
import os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/work/r35/main_wet_plate.png'
STYLE = '/home/user/Music/austerity-explainer/film-kit/assets/paintings/inflation-chapter-2/403-bg-glasgow-tenements.png'
Image.open(S).convert('RGB').resize((810, 1440), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_1_wet_plate_810x1440.png'))
Image.open(STYLE).convert('RGB').resize((504, 896), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_2_style_504x896.jpg'), quality=94)
for f in os.listdir(os.path.join(HERE, 'sent')):
    p = os.path.join(HERE, 'sent', f); im = Image.open(p); print(f, im.size, os.path.getsize(p), 'bytes', round(im.size[0]*im.size[1]/1e6, 3), 'MP')
