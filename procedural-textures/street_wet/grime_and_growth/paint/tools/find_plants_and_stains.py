"""What this file does (plain words): finds, in the kit's wet plate, (1) the green plants (weeds and moss) by colour, only where the kit added them (not in painter round 2's plate),
and (2) the same in the painting, so the two can be compared. Prints the plants' boxes at the plate size (1536 x 2730) and how many of them have a green patch in the painting
within 12 dots. Writes work/plants.json.
Run: python3 -I tools/find_plants_and_stains.py
"""
import numpy as np, cv2, os, json
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = 'proc-work/street_wet/'
kit = cv2.imread(B + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png').astype(np.int32)
base = cv2.imread(B + 'grime_and_growth/integrated/plates/lockout/final_lockout_B_wet_base.png').astype(np.int32)
paint = cv2.imread(os.path.join(HERE, 'pictures/kit_painting_lined_up.png')).astype(np.int32)
def green(im):   # b, g, r order
    return im[:, :, 1] - np.maximum(im[:, :, 0], im[:, :, 2])
gk, gb, gp = green(kit), green(base), green(paint)
ids = cv2.imread(B + 'painter_test/alignment/facts/ids.png').astype(np.int32)
sky = cv2.resize((ids.sum(axis=2) < 24).astype(np.uint8), (kit.shape[1], kit.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
sky = cv2.dilate(sky.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
for thr in (6, 10, 16):
    m = (gk > thr) & ~sky
    mb = (gb > thr) & ~sky
    mp = (gp > thr) & ~sky
    print(f'green over {thr}: kit plate {m.sum()} dots, no-kit plate {mb.sum()} dots, painting {mp.sum()} dots (non-sky)')
m = ((gk > 8) & ~sky).astype(np.uint8)
m = cv2.dilate(m, np.ones((5, 5), np.uint8))
n, lab, st, cen = cv2.connectedComponentsWithStats(m)
plants = []
mp = ((gp > 8) & ~sky).astype(np.uint8); mp = cv2.dilate(mp, np.ones((25, 25), np.uint8))
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 40: continue
    cx, cy = cen[i]
    plants.append(dict(x=int(x), y=int(y), w=int(w), h=int(h), area=int(a), cx=int(cx), cy=int(cy), painting_has_green=bool(mp[int(cy), int(cx)] > 0)))
plants.sort(key=lambda p: -p['area'])
print(len(plants), 'green patches of 40 dots or more in the kit plate;', sum(p['painting_has_green'] for p in plants), 'have green within about 12 dots in the painting')
for p in plants[:40]: print(p)
json.dump(plants, open(os.path.join(HERE, 'work/plants.json'), 'w'), indent=1)
