# What this does: downloads the free Poly Haven cloth surfaces (CC0, no sign-in) that the figure builder
# (build_figures.py) dresses its people in: wool coat cloth, tweed for caps, corduroy for trousers,
# leather for boots, knitted wool for mufflers and shawls, and rough linen for bundles. Each surface comes
# at 1k (colour, surface relief and the packed shading/roughness/metal picture) into
# FOLDER/surfaces/<id>/, the same layout the pit-village props use.
#
# Run: python3 -I fetch_cloth_textures.py FOLDER
#      (build_figures.py then reads them from FIGURES_SCRATCH, which should be the same FOLDER)

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pit-village', 'props'))
from download_poly_haven import download_surface  # noqa: E402

CLOTH_SURFACES = [
    'caban',                   # heavy wool coat cloth (melton): the long work coats
    'poly_wool_herringbone',   # tweed: flat caps, a second coat cloth
    'ribbed_corduroy',         # working men's trousers
    'fabric_leather_02',       # boots, a carpet bag
    'knitted_fleece',          # mufflers and the women's shawls
    'rough_linen',             # cloth bundles
]

if __name__ == '__main__':
    folder = sys.argv[1]
    for surface in CLOTH_SURFACES:
        print('surface', surface)
        download_surface(surface, folder)
