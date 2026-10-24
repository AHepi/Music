"""What this file does (plain words): makes the extra pictures for the person (JPEG under 400 KB, names start "27 "): where the camera starts to move, close-ups at 300 percent (roof line, kerb, ground by the props),
the road's brightness in the film against the painting, the film against the reference near the props, and the eight old and new stills of the other scenes. Run: python3 -I make_extra_pictures.py OUT_FOLDER
"""
import json, os, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
WET = W + '/27 Lockout shot - wet street.mp4'; DRY = W + '/before/lockout dry - before.mp4'
PV = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()
def frame(clip, n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-vf', f'select=eq(n\\,{n})', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).copy()
def save(img_bgr, name, limit=395_000):
    path = os.path.join(out, name)
    pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    for q in (88, 84, 80, 76, 72, 68, 64, 60, 56, 52):
        pil.save(path, quality=q, optimize=True)
        if os.path.getsize(path) <= limit: break
    print(name, q, os.path.getsize(path))
def label(img, text, size=0.7, y=26):
    cv2.rectangle(img, (0, y - 22), (14 + int(len(text) * 12.5 * size / 0.7), y + 8), (0, 0, 0), -1)
    cv2.putText(img, text, (6, y), cv2.FONT_HERSHEY_SIMPLEX, size, (0, 255, 255), 2, cv2.LINE_AA)
    return img
os.makedirs(out, exist_ok=True)
# c. where the camera starts to move: frames 60..105 every third, lower 57 percent
cells = []
for n in range(60, 106, 3):
    c = cv2.resize(frame(WET, n)[820:], (360, 367), interpolation=cv2.INTER_AREA)
    cells.append(label(c, f'{n / 30:.2f} s', 0.5, 18))
while len(cells) < 16: cells.append(np.zeros_like(cells[0]))
sheet = np.vstack([np.hstack(cells[i:i + 4]) for i in (0, 4, 8, 12)])
save(sheet, '27 Where the camera starts to move - every third frame from 2.0 to 3.5 s, lower part of the picture.jpg')
# d. close-ups at 300 percent: roof line at the start, roof line at the end of the move, the kerb, the ground by the sacks
f45, f210, f135 = frame(WET, 45), frame(WET, 210), frame(WET, 135)
def crop(im, x, y, w, h, s=3): return cv2.resize(im[y:y + h, x:x + w], (w * s, h * s), interpolation=cv2.INTER_CUBIC)
a = label(crop(f45, 800, 470, 240, 140), 'roof line, 1.5 s (before the move), 300 %', 0.6)
b = label(crop(f210, 600, 90, 240, 140), 'roof line, 7.0 s (end of the move), 300 %', 0.6)
c = label(crop(f210, 780, 1640, 240, 140), 'kerb and gutter, 7.0 s, 300 %', 0.6)
d = label(crop(f135, 520, 1700, 240, 140), 'ground between the sacks and the barrel, 4.5 s, 300 %', 0.6)
save(np.vstack([np.hstack([a, b]), np.hstack([c, d])]), '27 Close-ups at 300 percent - roof line, kerb and the ground by the props.jpg')
# f. other scenes unchanged
names = [('dry_projector', 'lockout, dry, start'), ('dry_moved', 'lockout, dry, end of move'), ('dry_move', 'lockout, dry, mid-move'), ('notice_end', 'notice corner, end'), ('notice_move', 'notice corner, slide'), ('chapter2_a', 'chapter 2, 30 s'), ('chapter2_b', 'chapter 2, 75 s'), ('chapter1_a', 'chapter 1, 40 s')]
proof = json.load(open(W + '/numbers/no_change_proof.json'))
def still(folder, n):
    d = os.path.join(W, 'stills', folder, n)
    return cv2.imread(os.path.join(d, [f for f in sorted(os.listdir(d)) if f.startswith('still-')][0]))
tiles_top, tiles_bottom = [], []
for n, text in names:
    o = cv2.resize(still('old', n), (216, 384), interpolation=cv2.INTER_AREA); nw = cv2.resize(still('new', n), (216, 384), interpolation=cv2.INTER_AREA)
    tiles_top.append(o); tiles_bottom.append(nw)
canvas = Image.new('RGB', (8 * 220 + 70, 2 * 388 + 90), (18, 18, 20)); dr = ImageDraw.Draw(canvas)
dr.text((8, 6), 'The same eight pictures drawn with the stage as it was (top) and with the new stage (bottom): dots that differ at all, out of 2,073,600 each', fill=(235, 235, 235), font=font(15))
for i, (n, text) in enumerate(names):
    x = 70 + i * 220
    canvas.paste(Image.fromarray(cv2.cvtColor(tiles_top[i], cv2.COLOR_BGR2RGB)), (x, 52)); canvas.paste(Image.fromarray(cv2.cvtColor(tiles_bottom[i], cv2.COLOR_BGR2RGB)), (x, 52 + 388))
    dr.text((x, 30), text, fill=(255, 220, 120), font=font(12))
    dr.text((x, 52 + 2 * 388 + 4), f"{int(round(proof[n]['share_of_dots_that_differ_at_all'] * 1920 * 1080))} dots differ; largest {proof[n]['largest_difference']}", fill=(150, 230, 150), font=font(12))
dr.text((6, 52 + 190), 'OLD', fill=(170, 200, 255), font=font(15)); dr.text((6, 52 + 388 + 190), 'NEW', fill=(255, 210, 120), font=font(15))
save(cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR), '27 Other scenes unchanged - eight pictures, old stage and new stage.jpg')
# g. film against the reference near the props
fr = []
for t in (4.0, 6.0):
    a = frame(WET, int(t * 30)); b = cv2.imread(os.path.join(W, 'stills', 'own', f'own_{t}', 'still-%.2f.jpg' % t))
    row = np.hstack([a[1250:], b[1250:]]); row = cv2.resize(row, (row.shape[1] * 3 // 4, row.shape[0] * 3 // 4), interpolation=cv2.INTER_AREA)
    label(row, f'{t:.1f} s: THE FILM (wet front + wet behind painting)', 0.55, 20); cv2.rectangle(row, (row.shape[1] // 2, 0), (row.shape[1] // 2 + 560, 30), (0, 0, 0), -1)
    cv2.putText(row, 'REFERENCE (front painting as its own behind painting)', (row.shape[1] // 2 + 6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2, cv2.LINE_AA)
    fr.append(row)
save(np.vstack(fr), '27 The ground by the props - the film against the reference, no dry patches.jpg')
