# What this does: makes two small example texture sets (256 x 256) from the experiment pictures so that check_texture_set.py can be tried:
#   out/example_good_set    colour, roughness, metallic, height (16-bit), normal (OpenGL) - all from one seamless recipe photographed by Blender
#   out/example_broken_set  the same surface spoiled on purpose: a colour with a seam, a DirectX normal map, an 8-bit clipped height,
#                           a plain-white ambient-occlusion picture and a metallic map full of grey
# Run (plain Python):  python3 -I make_example_sets.py
import os
import shutil

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
good, broken = os.path.join(OUT, 'example_good_set'), os.path.join(OUT, 'example_broken_set')
for folder in (good, broken):
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder)
B = os.path.join(OUT, 'bake')
for source, target in (('photo_colour.png', 'colour.png'), ('photo_roughness.png', 'roughness.png'), ('photo_metallic.png', 'metallic.png'),
                       ('photo_height.png', 'height.png'), ('bake_normal.png', 'normal.png')):
    shutil.copy(os.path.join(B, source), os.path.join(good, target))

# the broken set
noise = cv2.imread(os.path.join(OUT, 'patterns', 'noise_raw3d.png'), cv2.IMREAD_UNCHANGED)       # raw 3D noise: does not tile
noise = cv2.resize(noise, (256, 256), interpolation=cv2.INTER_AREA).astype(np.float64) / 65535.0
tinted = np.clip(noise[..., :3] * 3.0 - 0.8, 0, 1) * np.array([0.9, 0.6, 0.4])[::-1]               # a brown-ish colour picture with a seam
cv2.imwrite(os.path.join(broken, 'colour.png'), (tinted * 255).astype(np.uint8))
normal = cv2.imread(os.path.join(good, 'normal.png'), cv2.IMREAD_UNCHANGED)
normal[..., 1] = 65535 - normal[..., 1]                                                           # flip green: DirectX
cv2.imwrite(os.path.join(broken, 'normal.png'), normal)
height = cv2.imread(os.path.join(good, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
height8 = (np.clip((height - 0.5) * 5.0 + 0.5, 0, 1) * 255).astype(np.uint8)                       # over-stretched (clipped) and only 8 bits
cv2.imwrite(os.path.join(broken, 'height.png'), height8)
cv2.imwrite(os.path.join(broken, 'ao.png'), np.full((256, 256, 3), 255, np.uint8))
metal = cv2.imread(os.path.join(good, 'metallic.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
cv2.imwrite(os.path.join(broken, 'metallic.png'), (np.clip(metal * 0.5 + 0.25, 0, 1) * 255).astype(np.uint8))
rough = cv2.imread(os.path.join(good, 'roughness.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
srgb = np.where(rough <= 0.0031308, rough * 12.92, 1.055 * np.power(rough, 1 / 2.4) - 0.055)       # the sRGB mistake
cv2.imwrite(os.path.join(broken, 'roughness.png'), (srgb * 255).astype(np.uint8))
print('wrote', good, broken)
