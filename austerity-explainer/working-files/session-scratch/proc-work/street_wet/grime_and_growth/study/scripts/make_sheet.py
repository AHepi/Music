# What this does (plain words): makes the one look-at sheet of the pipeline study: (1) the street's main view coloured by what each dot is (so you see what weathering can go on and how much of the
# picture each family takes), (2) the run-off mask the wetness layer already holds on the dry walls, (3) the sky-openness map I made from the geometry (the first of the missing masks).
# Plain Python (numpy, OpenCV, Pillow); not Blender. Writes one JPEG into the pictures folder.
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/25 Pipeline study - what the street can tell the new layers.jpg'
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/study/out/'
lab = json.load(open(HERE + 's6b_labels_main.json'))
H, W = len(lab), len(lab[0])
GROUPS = [
    ('road setts', ['street_setts'], (230, 170, 60)),
    ('gutter and kerb stones', ['channel_stones', 'kerb_stone'], (240, 120, 40)),
    ('pavement flags', ['pavement_flags'], (250, 220, 90)),
    ('house walls (brick, stone)', ['cottage_brick', 'cottage_stone', 'interior_dark'], (70, 140, 230)),
    ('stone trim: steps, plinths, sills', ['dressed_stone', 'dark_dressed_stone'], (120, 90, 200)),
    ('cast iron: pipes, gutters, lamp posts', ['cast_iron', 'brass'], (230, 60, 60)),
    ('colliery brick and headframe', ['colliery_brick', 'headframe_steel', 'wheel_iron', 'wire_rope', 'boarded_blue', 'boarded_green'], (60, 190, 150)),
    ('roofs and chimneys', ['roof_slate', 'ridge_clay', 'chimney_pot_clay', 'chimney_pot_sooted', 'plaster_dark'], (160, 200, 80)),
    ('painted doors, windows, fascia', ['paint_cream', 'paint_black', 'paint_bottle_green', 'paint_brown', 'paint_maroon', 'paint_navy', 'fascia_board'], (240, 130, 200)),
    ('spoil heap, yard, moor', ['spoil_heap', 'colliery_yard', 'moor'], (150, 110, 70)),
]
idx = {}
for gi, (name, mats, col) in enumerate(GROUPS):
    for m in mats:
        idx[m] = gi
label = np.full((H, W), -1, int)
for j in range(H):
    for i in range(W):
        m = lab[j][i][0]
        if m in idx:
            label[j, i] = idx[m]
share = [float((label == gi).mean()) for gi in range(len(GROUPS))]
PW, PH = 306, 544
plate = cv2.imread(HERE + 'rented_timing/small/main_today.jpg')
plate = cv2.resize(plate, (PW, PH), interpolation=cv2.INTER_AREA)
up = cv2.resize(label.astype(np.int16), (PW, PH), interpolation=cv2.INTER_NEAREST)
over = plate.copy().astype(float)
for gi, (name, mats, col) in enumerate(GROUPS):
    m = up == gi
    over[m] = 0.35 * over[m] + 0.65 * np.array(col[::-1])
over = over.astype(np.uint8)
streak = cv2.resize(cv2.imread(HERE + 's12/streak_mask_dry_main.png'), (PW, PH), interpolation=cv2.INTER_AREA)
opp = np.load(HERE + 's3/openness_top_down_0p1m.npy')
img8 = (np.clip(np.flipud(opp), 0, 1) * 255 / 0.7).clip(0, 255).astype(np.uint8)
opp_big = cv2.applyColorMap(cv2.resize(img8, (int(90 * PH / 300), PH), interpolation=cv2.INTER_NEAREST), cv2.COLORMAP_VIRIDIS)
canvas_w = PW * 2 + opp_big.shape[1] + 5 * 12 + 330
canvas = Image.new('RGB', (canvas_w, PH + 150), (24, 24, 26))
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
d = ImageDraw.Draw(canvas)
x = 12
for title, sub, pic in (('1. What each dot is', 'colour = family (shares at right)', over),
                        ('2. Run-off mask, already there', 'dry walls: white = run-off lines', streak),
                        ('3. Sky openness, new', 'from above, y 0-30 m', opp_big)):
    d.text((x, 10), title, font=bold, fill=(240, 240, 240))
    d.text((x, 30), sub, font=font, fill=(170, 170, 170))
    canvas.paste(Image.fromarray(pic[..., ::-1]), (x, 56))
    x += pic.shape[1] + 12
# legend
y = 62
d.text((x, 56 - 4), 'share of the main view', font=bold, fill=(240, 240, 240))
sky = float(np.mean([1 for j in range(H) for i in range(W) if lab[j][i][0] == 'sky_dome_glow'])) if False else sum(1 for j in range(H) for i in range(W) if lab[j][i][0] == 'sky_dome_glow') / (H * W)
for gi, (name, mats, col) in enumerate(GROUPS):
    yy = 80 + gi * 34
    d.rectangle([x, yy, x + 16, yy + 16], fill=col)
    d.text((x + 24, yy - 1), f'{share[gi] * 100:4.1f} %  {name}', font=font, fill=(225, 225, 225))
yy = 80 + len(GROUPS) * 34
d.rectangle([x, yy, x + 16, yy + 16], fill=(60, 60, 64))
d.text((x + 24, yy - 1), f'{sky * 100:4.1f} %  sky (not weathered)', font=font, fill=(225, 225, 225))
note = ('Main camera of the street copy, 90 x 160 rays. Panel 2 is Blender drawing the wetness layer\'s own Streak Mask at wetness 0, so it exists without any wetness. Panel 3 is a study prototype: 48 rays over the sky hemisphere per dot, 10 cm dots, 21 s for 27,000 dots. Cottage steps and lamp posts show as dark holes. The road runs 0.40 to 0.56 open, so the street is a fairly even, dim canyon.')
import textwrap
wrapped = '\n'.join(textwrap.fill(par, 150) for par in note.split('\n'))
d.multiline_text((12, PH + 70), wrapped, font=font, fill=(190, 190, 190), spacing=4)
canvas.save(OUT, quality=85)
import os
print(OUT, os.path.getsize(OUT) // 1024, 'KB', canvas.size)
