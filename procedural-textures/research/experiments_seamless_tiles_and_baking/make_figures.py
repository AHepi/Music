# What this does: builds the labelled before/after pictures used in the guide "02 Research - seamless tiles and baking.md" from the experiment outputs in out/.
# Each figure is one PNG in out/figures/. Run after the experiments (plain Python):  python3 -I make_figures.py
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
FIG = os.path.join(OUT, 'figures')
os.makedirs(FIG, exist_ok=True)


def read(path, cell=None, grey_to_bgr=True, nearest=False):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(path)
    if image.dtype == np.uint16:
        image = (image / 257.0).astype(np.uint8)
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if cell:
        image = cv2.resize(image, (cell, cell), interpolation=cv2.INTER_NEAREST if nearest else cv2.INTER_AREA)
    return image[..., :3]


def banner(width, text, lines=1):
    canvas = np.full((22 * lines + 6, width, 3), 245, np.uint8)
    for i, part in enumerate(text.split('\n')):
        cv2.putText(canvas, part, (4, 17 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
    return canvas


def row_of(images, labels):
    tiles = [np.vstack([banner(image.shape[1], label, label.count('\n') + 1), image]) for image, label in zip(images, labels)]
    height = max(t.shape[0] for t in tiles)
    tiles = [np.vstack([t, np.full((height - t.shape[0], t.shape[1], 3), 255, np.uint8)]) if t.shape[0] < height else t for t in tiles]
    return np.hstack(tiles)


def save(name, rows):
    width = max(r.shape[1] for r in rows)
    rows = [np.hstack([r, np.full((r.shape[0], width - r.shape[1], 3), 255, np.uint8)]) if r.shape[1] < width else r for r in rows]
    cv2.imwrite(os.path.join(FIG, name), np.vstack(rows))
    print('wrote', name)


def shifted(image):
    return np.roll(image, (image.shape[0] // 2, image.shape[1] // 2), axis=(0, 1))


# 1 ------------------------------------------------------------------ four ways to make noise tile (shifted by half so a seam is a cross in the middle)
P = os.path.join(OUT, 'patterns')
names = ['noise_raw3d', 'noise_donut4d', 'noise_crossfade_linear', 'noise_crossfade_power', 'noise_mirror']
labels = ['raw 3D noise\n(seam)', '4D donut\n(seamless)', 'cross-fade, linear\n(faded middle)', 'cross-fade, cos/sin\n(keeps contrast)', 'mirror tiling\n(seamless, symmetric)']
images = [shifted(read(os.path.join(P, n + '.png'), 230)) for n in names]
# stretch contrast so the pictures are readable
images = [cv2.normalize(i, None, 0, 255, cv2.NORM_MINMAX) for i in images]
save('fig1_noise_tiling_methods.png', [row_of(images, labels)])

# 2 ------------------------------------------------------------------ bricks: node with whole and broken scale, colour wrapped by hand
names = ['brick_color_scale4', 'brick_color_scale4p3', 'brick_factor_scale4', 'brick_factor_squash_ok', 'brick_factor_squash_whole', 'brick_wrapped_hash']
labels = ['Brick node colour, Scale 4\n(mortar tiles, colours break)', 'Scale 4.3\n(everything breaks)', 'Brick node Factor, Scale 4\n(mortar mask tiles)',
          'Squash 0.62 every 3rd row\n(rows break)', 'Squash 0.75, Scale 3\n(whole bricks: tiles)', 'hand-made bricks, wrapped hash\n(colours tile too)']
images = [shifted(read(os.path.join(P, n + '.png'), 230)) for n in names]
save('fig2_brick_tiling.png', [row_of(images[:3], labels[:3]), row_of(images[3:], labels[3:])])

# 3 ------------------------------------------------------------------ checker/wave/magic/gradient/gabor rules
names = ['checker_even8', 'checker_odd7', 'wave_bands_scale3', 'wave_bands_whole_k3', 'wave_bands_whole_k3_distortion2', 'wave_bands_whole_k3_tileable_warp',
         'magic_scale2', 'magic_whole_k2', 'gradient_linear', 'gradient_linear_pingpong', 'gabor_raw', 'gabor_crossfade_power']
labels = ['Checker Scale 8', 'Checker Scale 7', 'Wave Scale 3', 'Wave Scale 3*pi/10', 'Wave + Distortion 2', 'Wave + tileable warp',
          'Magic Scale 2', 'Magic Scale 2*2pi/5', 'Gradient Linear', 'Gradient + PingPong', 'Gabor raw', 'Gabor cross-fade']
images = [shifted(read(os.path.join(P, n + '.png'), 170)) for n in names]
save('fig3_other_patterns.png', [row_of(images[i:i + 6], labels[i:i + 6]) for i in range(0, 12, 6)])

# 4 ------------------------------------------------------------------ repairs of pictures that do not tile
R = os.path.join(OUT, 'repair')
rows = []
for name in ('noise_raw3d', 'brick_color_scale4p3'):
    strip = cv2.imread(os.path.join(R, f'{name}__strip.png'))
    rows.append(strip)
save('fig4_picture_repairs.png', rows)

# 5 ------------------------------------------------------------------ bake routes
B = os.path.join(OUT, 'bake')
images = [read(os.path.join(B, f), 230) for f in ('photo_colour.png', 'bake_diffuse_color_only.png', 'bake_emit_colour.png', 'photo_metallic.png')]
labels = ['photograph (emission)', 'Cycles Bake: Diffuse, colour only\n(metal turns black)', 'Cycles Bake: Emit with the\nemission trick', 'metallic mask (white = metal)']
row1 = row_of(images, labels)
images = [read(os.path.join(B, f), 230) for f in ('photo_normal_bumpnode.png', 'bake_normal.png', 'photo_roughness.png', 'q6_roughness_float_srgb.png')]
labels = ['photographed Bump-node normal', 'Cycles Bake: Normal', 'roughness (correct)', 'roughness baked into an sRGB image\n(too bright)']
row2 = row_of(images, labels)
save('fig5_bake_routes.png', [row1, row2])

# 6 ------------------------------------------------------------------ edges: filter and samples
C = os.path.join(OUT, 'colour_space')
names = ['q4_edge_blackmanharris1p5_s4', 'q4_edge_box1p0_s1', 'q4_edge_box1p0_s4', 'q4_edge_box1p0_s16', 'q4_edge_box1p0_s64', 'q4_edge_gaussian1p5_s64']
labels = ['Blackman-Harris 1.5 px, 4 samples\n(the new-scene default)', 'Box 1 px, 1 sample', 'Box 1 px, 4 samples', 'Box 1 px, 16 samples', 'Box 1 px, 64 samples', 'Gaussian 1.5 px, 64 samples']
images = []
for n in names:
    image = cv2.imread(os.path.join(C, n + '.png'), cv2.IMREAD_UNCHANGED)
    image = (image / 257.0).astype(np.uint8)[24:40, 24:40, :3]
    images.append(cv2.resize(image, (176, 176), interpolation=cv2.INTER_NEAREST))
save('fig6_edge_quality.png', [row_of(images[:3], labels[:3]), row_of(images[3:], labels[3:])])

# 7 ------------------------------------------------------------------ geometry routes
G = os.path.join(OUT, 'geometry')
names = ['exact_normal', 'route1_normal_v256_margin0.0625', 'route2_normal_selected_to_active', 'route3_gn_material_slot.png' if False else 'route3_gn_material_slot.png']
files = ['exact_normal.png', 'route1_normal_v64_margin0.0.png', 'route1_normal_v256_margin0.0625.png', 'route2_normal_selected_to_active.png', 'ao_on_bumpy_geometry.png']
labels = ['exact normal map\n(from the formula)', 'photographed geometry,\n64 vertices across', 'photographed geometry,\n256 vertices across', 'Cycles Bake high -> low\n(selected to active)', 'Cycles Bake AO on the\nbumpy geometry']
images = [read(os.path.join(G, f), 230) for f in files]
images[-1] = cv2.normalize(images[-1], None, 0, 255, cv2.NORM_MINMAX)         # AO only spans about 0.84..1.0, stretch it so it can be seen
labels[-1] += '\n(contrast stretched)'
save('fig7_geometry_routes.png', [row_of(images, labels)])

# 8 ------------------------------------------------------------------ height bit depth and the normal map (red channel, stretched so the steps show)
import sys
sys.path.insert(0, HERE)
import normal_map_tools as nm
N = os.path.join(OUT, 'normal')
height16, _ = nm.load_unit_picture(os.path.join(N, 'A_height_512.png'))
height16 = height16 if height16.ndim == 2 else height16[..., 0]
panels = []
for bits in (8, 16):
    quantised = np.round(height16 * (255 if bits == 8 else 65535)) / (255.0 if bits == 8 else 65535.0)
    red = nm.sobel_normal(quantised, 30.0)[..., 0][180:300, 180:300]
    low, high = np.percentile(red, [1, 99])
    stretched = np.clip((red - low) / (high - low), 0, 1)
    panels.append(cv2.resize((stretched * 255).astype(np.uint8), (300, 300), interpolation=cv2.INTER_NEAREST))
panels = [cv2.cvtColor(p, cv2.COLOR_GRAY2BGR) for p in panels]
save('fig8_height_bit_depth.png', [row_of(panels, ['red channel of the normal map from an 8-bit height\n(Sobel strength 30, 120 px crop enlarged x2.5)', 'the same from a 16-bit height'])])

# 9 ------------------------------------------------------------------ bump normal maps from heights: distance & filter width
files = ['B_bump_filter0.1.png', 'B_bump_filter1.0.png', 'B_bump_filter2.0.png']
labels = ['Bump Filter Width 0.1 (default)', 'Filter Width 1.0', 'Filter Width 2.0']
images = [read(os.path.join(N, f), 230) for f in files]
save('fig9_bump_filter_width.png', [row_of(images, labels)])
