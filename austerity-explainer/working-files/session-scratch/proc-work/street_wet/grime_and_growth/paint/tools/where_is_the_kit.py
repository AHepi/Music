"""What this file does (plain words): finds where the weathering kit changed the plate, by comparing the kit's final wet lockout plate with painter round 2's wet plate
(the same street and light WITHOUT the kit: sett joints and rubbish only). Writes a picture of the difference (work/kit_difference.jpg) and prints the busiest
patches as boxes (x0, y0, x1, y1) at the plate size 1536 x 2730, so the close-ups can be chosen from facts, not by eye.
Run: python3 -I tools/where_is_the_kit.py
"""
import numpy as np, cv2, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
kit = cv2.imread(B + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png').astype(np.float32)
base = cv2.imread(B + 'grime_and_growth/integrated/plates/lockout/final_lockout_B_wet_base.png').astype(np.float32)
d = np.abs(kit - base).max(axis=2)
print('share of dots changed by more than 6 / 12 / 24 (of 255):', [round(float((d > t).mean()), 4) for t in (6, 12, 24)])
# ignore the sky (top ~ 0 to 0.2 of the height is where the base has the big pale hill; kit sky differs)
# leave the sky out: Blender's own flat-colour picture of the lockout camera says what is sky (nothing drawn there)
ids = cv2.imread(B + 'painter_test/alignment/facts/ids.png').astype(np.int32)
sky = cv2.resize((ids.sum(axis=2) < 24).astype(np.uint8), (d.shape[1], d.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
sky = cv2.dilate(sky.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
d[sky] = 0
print('sky share of the frame', round(float(sky.mean()), 3))
vis = np.clip(d * 4, 0, 255).astype(np.uint8)
cv2.imwrite(os.path.join(HERE, 'work/kit_difference.jpg'), cv2.resize(vis, (768, 1365), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 80])
# busiest boxes: 128-dot cells
c = 128
H, W = d.shape
cells = []
for y in range(0, H - c + 1, c):
    for x in range(0, W - c + 1, c):
        cells.append((float((d[y:y + c, x:x + c] > 12).mean()), x, y))
cells.sort(reverse=True)
for s, x, y in cells[:25]:
    print(f'cell x {x:4d} y {y:4d}: {100*s:5.1f} % of dots changed over 12')
