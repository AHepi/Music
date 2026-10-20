# What this does (plain words): sorts every dot of a colour picture into four plain kinds by simple colour rules, and prints the share of
# each, so a person can set how MUCH rust, pale chipped paint and dark stain a tile has by hand (look, change one setting, look again).
#   rust   = clearly orange-brown (red well above blue, and above green)
#   pale   = light dots that are not rust (bare steel, dusty paint, lit edges)
#   dark   = very dark dots (creases, stains, shadows)
#   steel  = everything else (the blue-grey paint)
# The same rule is used on the reference (as a GUIDE, measured once: general character only, no positions) and on the trial's pictures.
# It also prints the mean colour of the steel and rust dots. Use: python3 -I colour_shares.py PICTURE.png [PICTURE.png ...]
import sys

import cv2
import numpy as np


def shares(path):
    image = cv2.imread(path)[..., ::-1].astype(np.float64)
    red, green, blue = image[..., 0], image[..., 1], image[..., 2]
    mean = image.mean(axis=2)
    rust = (red > blue + 22) & (red > green + 10) & (red > 50)
    pale = (~rust) & (mean > 78)
    dark = (~rust) & (~pale) & (mean < 36)
    steel = ~(rust | pale | dark)
    result = {kind: round(100.0 * float(mask.mean()), 1) for kind, mask in (('rust', rust), ('pale', pale), ('dark', dark), ('steel', steel))}
    result['steel colour'] = [round(float(image[..., c][steel].mean())) for c in range(3)]
    result['rust colour'] = [round(float(image[..., c][rust].mean())) for c in range(3)] if rust.any() else None
    result['mean brightness'] = round(float(mean.mean()), 1)
    return result


for picture in sys.argv[1:]:
    print(picture.split('proc-work/')[-1], shares(picture))
