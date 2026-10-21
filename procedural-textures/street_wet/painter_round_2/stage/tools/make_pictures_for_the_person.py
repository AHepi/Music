"""What this file does (plain words): makes the pictures for the person from the stage stills (stills/before = the film's stage as it is, stills/after = with the brightness fix), as JPEGs under 400 KB in
"proc-work/24 Wet street painting round 2 - pictures/":
  1. plate view: the painting (cut to the stage's lens) | stage before the fix | stage after the fix
  2. moved view: before | after          3. mid-move (6.0 s of the street move): before | after
  4. the near road at 100 percent in the moved view: before | after (do the joints and the rubbish survive?)
  5. the near road at 100 percent in the plate view: painting | before | after (the same place, so the painting is the true reference)
  6. a chart: what each step of the stage's finish does to the road's brightness, and painted brightness against arriving brightness before and after the fix
Run: python3 -I tools/make_pictures_for_the_person.py
"""
import json, os, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import central, central_mask, masks, er, load01, TEST1, P
OUT = 'proc-work/24 Wet street painting round 2 - pictures/'
os.makedirs(OUT, exist_ok=True)
F = lambda size, bold=False: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else ''), size)
def still(folder, name): return cv2.cvtColor(cv2.imread(P('stills', folder, name, 'still-6.00.jpg')), cv2.COLOR_BGR2RGB)
def labelled(panels, labels, scale=0.5, header=44, gap=8, bg=(24, 26, 30)):
    ims = [cv2.resize(p, (int(p.shape[1] * scale), int(p.shape[0] * scale)), interpolation=cv2.INTER_AREA) if scale != 1 else p for p in panels]
    h = max(i.shape[0] for i in ims); w = sum(i.shape[1] for i in ims) + gap * (len(ims) - 1)
    canvas = Image.new('RGB', (w, h + header), bg); d = ImageDraw.Draw(canvas); x = 0
    for im, lab in zip(ims, labels):
        canvas.paste(Image.fromarray(im), (x, header)); d.text((x + 10, 10), lab, font=F(20, True), fill=(235, 235, 235)); x += im.shape[1] + gap
    return canvas
def save(img, name, q=82):
    path = OUT + name
    for quality in (q, 76, 70, 64, 58):
        img.save(path, quality=quality, optimize=True)
        if os.path.getsize(path) < 400 * 1024: break
    print(name, os.path.getsize(path) // 1024, 'KB')

painting = central(cv2.cvtColor(cv2.imread(P('../paint/front_painting_final.png')), cv2.COLOR_BGR2RGB))
b_proj, a_proj = still('before', 'wet_projector'), still('after', 'wet_projector')
b_mov, a_mov = still('before', 'wet_moved'), still('after', 'wet_moved')
b_mid, a_mid = still('before', 'wet_move'), still('after', 'wet_move')
save(labelled([painting, b_proj, a_proj], ['the painting', 'stage before the fix', 'stage after the fix']), '24 stage - plate view, painting, stage before and after the fix.jpg')
save(labelled([b_mov, a_mov], ['moved view, before the fix', 'moved view, after the fix']), '24 stage - moved view, before and after the fix.jpg')
save(labelled([b_mid, a_mid], ['mid-move (6.0 s), before the fix', 'mid-move (6.0 s), after the fix']), '24 stage - mid-move, before and after the fix.jpg')
# 100 percent crops of the near road
CROP_MOVED = tuple(int(v) for v in os.environ.get('CROP_MOVED', '0,1280,600,1880').split(','))      # x0, y0, x1, y1 in the 1080 x 1920 stage picture
CROP_PLATE = tuple(int(v) for v in os.environ.get('CROP_PLATE', '0,1280,540,1880').split(','))
cm = lambda im, c: im[c[1]:c[3], c[0]:c[2]]
save(labelled([cm(b_mov, CROP_MOVED), cm(a_mov, CROP_MOVED)], ['near road, moved view, before the fix (100 %)', 'near road, moved view, after the fix (100 %)'], scale=1), '24 stage - near road at 100 percent, moved view, before and after the fix.jpg', q=88)
save(labelled([cm(painting, CROP_PLATE), cm(b_proj, CROP_PLATE), cm(a_proj, CROP_PLATE)], ['painting (100 %)', 'stage before the fix', 'stage after the fix'], scale=1), '24 stage - near road at 100 percent, plate view, painting, before and after the fix.jpg', q=88)

# the chart
real = json.load(open(P('numbers/diagnosis_real_stage.json')))
before = json.load(open(P('numbers/stage_measurements_before.json')))['plate_view_stage_against_painting']['new_wet_front_painting']['road_stage_over_painting']
after = json.load(open(P('numbers/stage_measurements_after.json')))['plate_view_stage_against_painting']['new_wet_front_painting']['road_stage_over_painting']
bars = [('painting passed straight through (nothing of the finish)', real['diagnosis/off_all']['road_arrives'], (120, 130, 140)),
        ('only the dark frame edge (vignette 0.30)', real['diagnosis/only_edge']['road_arrives'], (200, 90, 70)),
        ('only the filmic curve', real['diagnosis/only_curve']['road_arrives'], (200, 150, 60)),
        ('only contrast 1.04 and lift 0.015', real['diagnosis/only_cl']['road_arrives'], (120, 130, 140)),
        ('only the cool and warm tint', real['diagnosis/only_tint']['road_arrives'], (120, 130, 140)),
        ('the film\'s look as it is (before the fix)', before, (200, 90, 70)),
        ('after the fix (curve may not darken, edge 0.25)', after, (70, 160, 100))]
W_, H_ = 1500, 1040
img = Image.new('RGB', (W_, H_), (250, 248, 244)); d = ImageDraw.Draw(img)
d.text((30, 18), 'Wet road: how bright it arrives in the stage, as a share of how bright it was painted (1.00 = as painted)', font=F(22, True), fill=(30, 30, 30))
x0, x1, y = 620, 1440, 80
scale = lambda v: x0 + (v - 0.6) / (1.1 - 0.6) * (x1 - x0)
for v in (0.6, 0.7, 0.8, 0.9, 1.0, 1.1):
    d.line([(scale(v), y - 8), (scale(v), y + len(bars) * 50)], fill=(200, 200, 200)); d.text((scale(v) - 14, y - 30), f'{v:.1f}', font=F(16), fill=(90, 90, 90))
d.line([(scale(0.9), y - 8), (scale(0.9), y + len(bars) * 50)], fill=(60, 140, 90), width=3); d.text((scale(0.9) - 60, y + len(bars) * 50 + 4), 'aim: 0.90', font=F(16, True), fill=(60, 140, 90))
for i, (lab, v, col) in enumerate(bars):
    yy = y + i * 50
    d.text((30, yy + 8), lab, font=F(17), fill=(40, 40, 40))
    d.rectangle([scale(0.6), yy + 4, scale(v), yy + 36], fill=col); d.text((scale(v) + 8, yy + 8), f'{v:.3f}', font=F(17, True), fill=(30, 30, 30))
# painted -> arriving curve from the real pictures (road, plate view)
M = masks(TEST1 + 'alignment/facts_surfaces/'); road = er(central_mask(M['road']))
def lum01(rgb): return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)
pl = cv2.GaussianBlur(lum01(painting.astype(np.float32) / 255), (0, 0), 2)
curves = {}
for name, im in (('off_all', still('diagnosis', 'off_all')), ('before', b_proj), ('after', a_proj)):
    L = cv2.GaussianBlur(lum01(im.astype(np.float32) / 255), (0, 0), 2)
    xs = np.arange(0.05, 0.80, 0.05); ys = []
    for lo in xs:
        m = road & (pl >= lo - 0.025) & (pl < lo + 0.025); ys.append(float(L[m].mean()) if m.sum() > 200 else np.nan)
    curves[name] = (xs, np.array(ys))
cx0, cy0, cw, ch = 140, 560, 520, 400
d.text((30, 495), 'Road dots by painted brightness: brightness that arrives', font=F(20, True), fill=(30, 30, 30))
d.rectangle([cx0, cy0, cx0 + cw, cy0 + ch], outline=(150, 150, 150))
for v in np.arange(0, 0.81, 0.1):
    px = cx0 + v / 0.8 * cw; py = cy0 + ch - v / 0.8 * ch
    d.line([(px, cy0), (px, cy0 + ch)], fill=(228, 228, 228)); d.line([(cx0, py), (cx0 + cw, py)], fill=(228, 228, 228))
    d.text((px - 12, cy0 + ch + 6), f'{v:.1f}', font=F(14), fill=(90, 90, 90)); d.text((cx0 - 36, py - 8), f'{v:.1f}', font=F(14), fill=(90, 90, 90))
d.text((cx0 + 90, cy0 + ch + 28), 'painted brightness (road dots, blurred)', font=F(15), fill=(60, 60, 60))
d.line([(cx0, cy0 + ch), (cx0 + cw, cy0)], fill=(150, 150, 150), width=2)
for name, col, lab in (('off_all', (120, 130, 140), 'nothing of the finish'), ('before', (200, 90, 70), 'before the fix'), ('after', (70, 160, 100), 'after the fix')):
    xs, ys = curves[name]; pts = [(cx0 + x / 0.8 * cw, cy0 + ch - y / 0.8 * ch) for x, y in zip(xs, ys) if not np.isnan(y)]
    d.line(pts, fill=col, width=4)
    for p in pts: d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=col)
lx = cx0 + cw + 40
for i, (lab, col) in enumerate((('as painted (the diagonal)', (150, 150, 150)), ('nothing of the finish', (120, 130, 140)), ('before the fix', (200, 90, 70)), ('after the fix', (70, 160, 100)))):
    d.line([(lx, cy0 + 20 + i * 34), (lx + 40, cy0 + 20 + i * 34)], fill=col, width=4); d.text((lx + 50, cy0 + 10 + i * 34), lab, font=F(17), fill=(40, 40, 40))
d.text((lx, cy0 + 170), 'Dark painted dots (under 0.25) arrive far darker\nbefore the fix (a dot painted 0.10 arrives at 0.02);\nafter it they sit close to the straight-through line.\nLight dots still arrive a little darker than painted:\nthat is the dark frame edge (now 0.25, was 0.30).', font=F(15), fill=(60, 60, 60))
save(img, '24 stage - why the road arrives darker, and the fix (chart).jpg', q=88)
json.dump({k: {'painted': [float(a) for a in v[0]], 'arrives': [None if np.isnan(b) else float(b) for b in v[1]]} for k, v in curves.items()}, open(P('numbers/transfer_curve_real_road.json'), 'w'), indent=1)

# old dry behind painting against the new wet one in the moved view (after the fix), with the maps of where each differs from the reference
mp_old = cv2.cvtColor(cv2.imread(P('work/patches_map_old_dry_behind_after.jpg')), cv2.COLOR_BGR2RGB); mp_new = cv2.cvtColor(cv2.imread(P('work/patches_map_new_wet_behind_after.jpg')), cv2.COLOR_BGR2RGB)
sz = lambda im: cv2.resize(im, (405, 720), interpolation=cv2.INTER_AREA)
save(labelled([sz(still('after', 'wetolddry_moved')), sz(mp_old), sz(still('after', 'wet_moved')), sz(mp_new)],
              ['old DRY behind painting', 'where it differs (white)', 'new WET behind painting', 'where it differs (white)'], scale=1), '24 stage - moved view after the fix, old dry behind painting against the new wet one.jpg')
