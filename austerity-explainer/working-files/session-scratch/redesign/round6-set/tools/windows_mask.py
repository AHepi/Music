"""What this does (scratch, round 5 W4 helper): the mask for page 12's windows-only slowed state picture. It finds where
W2's main plate and its slowed helper plate differ (the same test as make_state_picture.py: over 6 levels, or over 3
levels blurred a lot, cleared of specks), then keeps only the patches that touch No. 2's window outlines (measured
by shot_facts.py at W2's plate camera), less anything within 48 pixels (at 1536 wide) of the eight waiting men's
outlines or the lathe man's in the doorway, so the picture swaps the windows going dark and nothing else (the men and
the press man go at the "workers" cut).
Use: python3 -I windows_mask.py MAIN_PLATE SLOWED_PLATE FACTS_FOLDER OUT_MASK.png LOOK.jpg"""
import json
import os
import sys

import cv2
import numpy as np

main_path, slowed_path, facts_folder, out_path, look_path = sys.argv[1:6]
plate, helper = cv2.imread(main_path), cv2.imread(slowed_path)
height, width = plate.shape[:2]
unit = width / 1536


def disc(radius):
    radius = max(1, int(round(radius)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1, 2 * radius + 1))


blur = lambda picture, sigma: cv2.GaussianBlur(picture.astype(np.float32), (0, 0), sigma * unit)
difference = np.abs(blur(plate, 2) - blur(helper, 2)).max(axis=2)
smooth = np.abs(blur(plate, 10) - blur(helper, 10)).max(axis=2)
found = ((difference > 6) | (smooth > 3)).astype(np.uint8)
found = cv2.morphologyEx(found, cv2.MORPH_OPEN, disc(1.5 * unit))
count, labels, stats, _ = cv2.connectedComponentsWithStats(found, connectivity=8)
keep = np.zeros(count, np.uint8)
keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 60 * unit * unit
changed = cv2.morphologyEx(keep[labels], cv2.MORPH_CLOSE, disc(6 * unit)) > 0

facts = json.load(open(os.path.join(facts_folder, 'facts.json')))
ids = cv2.cvtColor(cv2.imread(os.path.join(facts_folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)


def outline(names):
    shown = np.zeros(ids.shape[:2], np.uint8)
    for group in names:
        shown |= (np.abs(ids - np.array(facts['groups'][group]['colour'])).sum(axis=2) < 24).astype(np.uint8)
    return cv2.resize(shown * 255, (width, height), interpolation=cv2.INTER_NEAREST) > 127


windows = outline([g for g in facts['groups'] if g.startswith('no-2 windows')])
people = outline([g for g in facts['groups'] if g.startswith('man ') or g.startswith('worker')])
near_people = cv2.dilate(people.astype(np.uint8), disc(48 * unit)) > 0   # wider than the state tool's widening and softening (about 25)
near_windows = cv2.dilate(windows.astype(np.uint8), disc(6 * unit)) > 0
count, labels = cv2.connectedComponents(changed.astype(np.uint8), connectivity=8)
mask = np.zeros_like(changed)
for k in range(1, count):
    patch = labels == k
    touches_windows = (patch & near_windows).any()
    touches_people = (patch & near_people).any()
    print(f'windows_mask: patch {k}: {patch.mean():.2%} of the frame, rows {np.nonzero(patch)[0].min() / height:.2f} to '
          f'{np.nonzero(patch)[0].max() / height:.2f} down; touches the windows {touches_windows}, the people {touches_people}')
    # a patch of the windows' change joined to the people's (a window strip just above a man's head) keeps only its
    # part clear of them
    if touches_windows:
        mask |= patch & ~near_people
cv2.imwrite(out_path, mask.astype(np.uint8) * 255)
print(f'windows_mask: the windows\' change covers {mask.mean():.2%} of the frame; all the change {changed.mean():.2%}; '
      f'left for the "workers" cut {(changed & ~mask).mean():.2%}')
look = plate.astype(np.float32) * 0.45
look[changed & ~mask] = look[changed & ~mask] * 0.5 + np.array([60, 60, 220], np.float32) * 0.5     # red: left for the cut
look[mask] = look[mask] * 0.5 + np.array([40, 140, 255], np.float32) * 0.5                          # orange: the windows
look[windows] = look[windows] * 0.6 + np.array([255, 160, 60], np.float32) * 0.4                     # blue: the window outlines
cv2.imwrite(look_path, np.clip(look, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 88])
