# COLOUR AND FADE - layer tests (written by layer_tests.py)

Size 512 dots per base tile (2 x 2 area: 1024).

## tiling, tiles_across 1
* colour: shifted vs rolled: {'mean difference (of 255)': 1.417, 'share of dots over 40 (%)': 0.016}
* colour: WRONG roll (control): {'mean difference (of 255)': 18.526, 'share of dots over 40 (%)': 8.596}
* fade strength: shifted vs rolled: {'mean difference (of 255)': 4.602, 'share of dots over 40 (%)': 1.7315}
* colour: share of dots over 10/255 inside the 6-dot band along the old tile edge vs elsewhere (%): [1.081, 1.257]

## tiling, tiles_across 2
* colour: shifted vs rolled: {'mean difference (of 255)': 1.398, 'share of dots over 40 (%)': 0.014}
* colour: WRONG roll (control): {'mean difference (of 255)': 18.248, 'share of dots over 40 (%)': 7.8866}
* fade strength: shifted vs rolled: {'mean difference (of 255)': 4.664, 'share of dots over 40 (%)': 1.7579}
* colour: share of dots over 10/255 inside the 6-dot band along the old tile edge vs elsewhere (%): [0.775, 1.154]

## new content in the 2 x 2 area
* picture vs itself rolled by one base tile (a repeat would be near 0.9): {'mean difference (of 255)': 18.325, 'share of dots over 40 (%)': 8.2678}

## independence
* this layer seed 11 -> 12 (colour): {'changed inside slates (% of slate dots)': 91.8, 'changed in joints (% of joint dots)': 0.0}
* this layer seed 11 -> 12 (height, exact 16 bit): changed in joints (% of joint dots, > 0.0005): 0.0
* layout seed 1 -> 2 (the slates move): colour changed in joints (% of the old joint dots): 51.0265
* the layer's own tone relief inside slates (height): lowest / highest / spread: [-0.323, 0.367, 0.11]
* amount 0: height minus layout height, largest absolute value (must be 0): 0.0
* amount 0: roughness, lowest / highest (must both be the base 0.8; the 8-bit picture has a dither of plus or minus 1/255): [0.7961, 0.8039]
* amount 1: roughness inside slates, lowest / highest: [0.639, 0.984]
* amount 0: fade strength picture, largest value (must be 0; 8-bit dither 0.004): 0.0039
* amount 0 (colour): % of slate dots that are not the single flat middle tone: 0.0
