# work script: composes the showcase pictures from the final round's pictures. python3 -I make_pictures.py ROUND_TAG PICS_TAG
import glob, os, sys, shutil
import cv2, numpy as np
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
from harness import sheets
WG = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(WG))), '25 Street grime, cracks, stains, weeds and moss - pictures')
round_tag, pics_tag = sys.argv[1], sys.argv[2]
R = os.path.join(WG, 'rounds', round_tag, 'street')
PS = os.path.join(WG, 'runs', pics_tag + '_street', 'out')
PL = os.path.join(WG, 'runs', pics_tag + '_lockout', 'out')
SC = os.path.join(WG, 'runs', 'show_r6', 'out')
AL = os.path.join(WG, 'runs', 'alg_r7', 'out')
CT = os.path.join(WG, 'runs', 'court_r6', 'out')
BASE = os.path.join(KIT, 'harness', 'baseline', 'plates')

def pic(folder, prefix):
    f = sorted(glob.glob(os.path.join(folder, prefix + '*.jpg')) + glob.glob(os.path.join(folder, prefix + '*.png')))
    return cv2.imread(f[0]) if f else np.full((360, 480, 3), 40, np.uint8)

def label(im, text):
    im = im.copy()
    (w, h), b = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(im, (0, 0), (w + 10, h + b + 8), (0, 0, 0), -1)
    cv2.putText(im, text, (5, h + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (235, 235, 235), 1, cv2.LINE_AA)
    return im

def fit(im, w):
    return cv2.resize(im, (w, int(im.shape[0] * w / im.shape[1])), interpolation=cv2.INTER_AREA)

def grid(rows, w):
    lines = []
    for row in rows:
        cells = [label(fit(im, w), t) for im, t in row]
        h = max(c.shape[0] for c in cells)
        cells = [cv2.copyMakeBorder(c, 0, h - c.shape[0], 0, 4, cv2.BORDER_CONSTANT, value=(24, 24, 24)) for c in cells]
        lines.append(np.hstack(cells))
        lines.append(np.full((4, lines[-1].shape[1], 3), 24, np.uint8))
    return np.vstack(lines[:-1])

def save(im, name):
    r = sheets.save_under_limit(im, os.path.join(OUT, name))
    print(name, r)

def plate(folder, name):
    return cv2.imread(os.path.join(folder, name + '.png')) if os.path.exists(os.path.join(folder, name + '.png')) else cv2.imread(os.path.join(folder, name + '.jpg'))

def densest_window(mask, size):
    k = cv2.boxFilter(mask.astype(np.float32), -1, (size, size), normalize=False)
    y, x = np.unravel_index(np.argmax(k), k.shape)
    return int(max(0, min(mask.shape[0] - size, y - size // 2))), int(max(0, min(mask.shape[1] - size, x - size // 2)))

def part(folder, name):
    f = os.path.join(folder, name + '.png')
    a = cv2.imread(f, cv2.IMREAD_UNCHANGED)
    return a[..., 0].astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0) if a is not None else None

# 1 cracks: the crack close view, then a plate crop at the densest crack window of the plate, base against kit
rows = [[(pic(SC, 'sc_crack__base'), 'flag, close: before'), (pic(SC, 'sc_crack__solo_groundcracks'), 'flag crack: cracks layer only')],
        [(pic(SC, 'sc_kerb__base'), 'kerb, close: before'), (pic(SC, 'sc_kerb__solo_groundcracks'), 'kerb chips and open joint: cracks layer only')]]
top = grid(rows, 480)
kit_plate = plate(R, 'plate_notice_A_wet'); base_plate = cv2.imread(os.path.join(BASE, 'plate_notice_A_wet.png'))
m = None
for p in ('flag_fine', 'flag_broken', 'flag_tilt', 'kerb_chips'):
    a = part(R, f'part_groundcracks_{p}_notice')
    if a is not None:
        m = (a > 0.4) if m is None else (m | (a > 0.4))
y, x = densest_window(m, 420) if m is not None else (1800, 600)
crop = lambda im: im[y:y + 420, x:x + 420]
bottom = grid([[(crop(base_plate), 'plate crop: before'), (crop(kit_plate), 'plate crop: with the ground layers')]], 480)
save(np.vstack([top, np.full((6, top.shape[1], 3), 24, np.uint8), bottom[:, :top.shape[1]] if bottom.shape[1] >= top.shape[1] else cv2.copyMakeBorder(bottom, 0, 0, 0, top.shape[1] - bottom.shape[1], cv2.BORDER_CONSTANT, value=(24, 24, 24))]), '25 Ground - cracks, kerb chips and tilted flags (close and plate crop).jpg')

# 2 dirt
tar = part(R, 'part_dirt_tar_notice')
ty, tx_ = densest_window(tar > 0.5, 420)
tcrop = lambda im: im[ty:ty + 420, tx_:tx_ + 420]
rows = [[(tcrop(base_plate), 'plate crop with a tar patch: before'), (tcrop(kit_plate), 'plate crop: with the dirt layer (and the others)')],
        [(pic(PS, 'pipe_close__base'), 'pipe foot: before'), (pic(PS, 'pipe_close__solo_dirt'), 'rust halo and water marks: dirt layer only')],
        [(pic(PS, 'doorstep_close__base'), 'doorstep: before'), (pic(PS, 'doorstep_close__solo_dirt'), 'scrubbed strip, polish: dirt layer only')]]
save(grid(rows, 480), '25 Ground - tar, rust halos, polish and water marks.jpg')

# 3 moss
rows = [[(pic(SC, 'sc_moss__base'), 'gutter joints, close: before'), (pic(SC, 'sc_moss__solo_groundmoss'), 'moss in the gutter joints: moss layer only')],
        [(pic(AL, 'sc_alg0__base'), 'lamp post foot: before'), (pic(AL, 'sc_alg0__solo_groundmoss'), 'algae fan placed here on the plan pictures; not visible in the picture (see the recipe)')]]
save(grid(rows, 480), '25 Ground - moss in the gutter joints and algae under the downpipe (close).jpg')

# 4 iron
rows = [[(pic(PS, 'wall_lamp__base'), 'lamp post: before'), (pic(PS, 'wall_lamp__solo_iron'), 'lamp post: iron layer only')],
        [(pic(PS, 'pipe_close__base'), 'downpipe: before'), (pic(PS, 'pipe_close__solo_iron'), 'downpipe: iron layer only')],
        [(pic(PL, 'drum_close__base'), 'fire drum: before'), (pic(PL, 'drum_close__solo_iron'), 'fire drum: iron layer only')]]
save(grid(rows, 480), '25 Ground - the iron: lamp posts, downpipes, the fire drum.jpg')

# 5 the road middle stays clean: plate lower half with the ground layers' marks in red, and the plain plate
kit_main = plate(R, 'plate_main_A_wet')
union = np.zeros(kit_main.shape[:2], np.float32)
for layer in ('dirt', 'groundcracks', 'groundmoss'):
    a = part(R, f'layer_{layer}_plate_main')
    if a is not None:
        union = np.maximum(union, a)
over = kit_main.copy().astype(np.float32)
red = np.zeros_like(over); red[..., 2] = 255
w = np.clip(union * 1.0, 0, 1)[..., None]
over = (over * (1 - 0.7 * w) + red * 0.7 * w).astype(np.uint8)
y0 = 1500
rows = [[(kit_main[y0:], 'plate with the ground layers'), (over[y0:], 'marks in red: no moss and no dirt on the crown; sunk setts do sit in the wheel lanes')]]
save(grid(rows, 600), '25 Ground - the road middle stays clean (crown and lanes).jpg')

# 6 before and after
base_main = cv2.imread(os.path.join(BASE, 'plate_main_A_wet.png'))
y1 = 1900
rows = [[(base_main[y1:], 'before (plate, lower part)'), (kit_main[y1:], 'after (plate, lower part)')]]
save(grid(rows, 640), '25 ground - before and after.jpg')
# the dial sheet
src = os.path.join(WG, 'dial_sheet_small.jpg')
if os.path.exists(src):
    shutil.copy(src, os.path.join(OUT, '25 Ground - what each main dial does.jpg'))
    print('dial sheet copied', os.path.getsize(src))

# 7 the courtyard
rows = [[(pic(CT, 'photo__base'), 'courtyard: before'), (pic(CT, 'photo__kit_dirt-groundmoss'), 'courtyard: the dirt and moss layers (nothing else changed)')]]
save(grid(rows, 600), '25 Ground - the same layers on the Japanese courtyard (dirt and moss only).jpg')
