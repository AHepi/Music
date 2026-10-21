"""What this file does (plain words): makes what is sent to the painter for the grime-kit painter test, the SAME WAY as painter round 2:
sent/image_1_kit_wet_plate_810x1440.png (the kit's final wet lockout plate, 1536 x 2730, shrunk to 810 x 1440 with the same filter),
sent/image_2_style_504x896.jpg (a plain byte-for-byte copy of the series' style picture used in the first test and round 2),
and briefs/brief_kit_test.txt = round 2's front-painting brief with ONE sentence added (the person's words about grime, streaks, stains, cracks, weeds and moss).
Run: python3 -I tools/make_pictures_and_brief.py
"""
from PIL import Image
import os, shutil, hashlib
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'proc-work/street_wet/'
plate = B + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png'
Image.open(plate).convert('RGB').resize((810, 1440), Image.LANCZOS).save(os.path.join(HERE, 'sent/image_1_kit_wet_plate_810x1440.png'))
shutil.copyfile(B + 'painter_test/sent/image_2_style_504x896.jpg', os.path.join(HERE, 'sent/image_2_style_504x896.jpg'))
same = hashlib.sha256(open(os.path.join(HERE, 'sent/image_2_style_504x896.jpg'), 'rb').read()).hexdigest() == hashlib.sha256(open(B + 'painter_round_2/paint/sent/image_2_style_504x896.jpg', 'rb').read()).hexdigest()
print('style picture identical to round 2 sent file:', same)
r2 = open(B + 'painter_round_2/paint/briefs/brief_round2.txt', encoding='utf-8').read()
head, body = r2.split('==========\n', 1)
body = body.strip()
anchor = 'add no writing, print or modern litter.'
add = " Keep the soot grime, run-off streaks, stains, cracks, weeds and moss where image 1 has them, at the same size and strength, painted in image 2's hand."
assert body.count(anchor) == 1
new = body.replace(anchor, anchor + add)
note = ("NOTE (plain words): this file is the painter brief for the GRIME-KIT PAINTER TEST (21 October 2026), exactly as it is sent: one paragraph, after the line of equals signs.\n"
        "It is painter round 2's front-painting brief (painter_round_2/paint/briefs/brief_round2.txt) with ONE sentence added, right after the sentence about the small rubbish:\n"
        "<<" + add.strip() + ">>\n")
open(os.path.join(HERE, 'briefs/brief_kit_test.txt'), 'w', encoding='utf-8').write(note + '==========\n' + new + '\n')
# the exact prompt that is sent is the text after the line of equals signs
open(os.path.join(HERE, 'briefs/prompt_sent.txt'), 'w', encoding='utf-8').write(new)
print('prompt characters:', len(new), ' round 2 prompt characters:', len(body))
for f in sorted(os.listdir(os.path.join(HERE, 'sent'))):
    p = os.path.join(HERE, 'sent', f); im = Image.open(p); print(f, im.size, os.path.getsize(p), 'bytes', round(im.size[0] * im.size[1] / 1e6, 3), 'MP')
