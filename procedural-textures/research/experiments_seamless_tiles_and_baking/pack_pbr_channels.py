# What this does: packs separate grey pictures (ambient occlusion, roughness, metallic) into the red, green and blue channels of ONE picture, the way game engines and glTF
# want them, and unpacks them again; also flips a normal map between OpenGL and DirectX. Nothing is colour-converted: the numbers go in and come out unchanged
# (the packed picture is DATA, so it must be loaded as "Non-Color" / with sRGB switched off in the engine).
# Layouts:
#   orm   red = ambient occlusion, green = roughness, blue = metallic      glTF 2.0, Unreal Engine ORM, Poly Haven "arm"
#   unity unity HDRP Mask Map: red = metallic, green = ambient occlusion, blue = detail mask (set to 0.5 grey here), alpha = smoothness (1 - roughness)
# Run (plain Python, needs numpy and cv2):
#   python3 -I pack_pbr_channels.py pack   FOLDER OUT.png [--layout orm|unity]     FOLDER holds ao.png roughness.png metallic.png (missing ones: ao = 1, metallic = 0, roughness = 0.5)
#   python3 -I pack_pbr_channels.py unpack PACKED.png OUT_FOLDER [--layout orm|unity]
#   python3 -I pack_pbr_channels.py flipgreen IN_NORMAL.png OUT_NORMAL.png         OpenGL <-> DirectX (green = 1 - green)
import os
import sys

import cv2
import numpy as np


def read_grey(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    bits = 16 if image.dtype == np.uint16 else 8
    image = image.astype(np.float64) / (65535.0 if bits == 16 else 255.0)
    return (image if image.ndim == 2 else image[..., :3].mean(axis=-1)), bits


def write(array, path, bits):
    top = 65535 if bits == 16 else 255
    cv2.imwrite(path, (np.clip(array, 0, 1) * top + 0.5).astype(np.uint16 if bits == 16 else np.uint8))


def pack(folder, out_path, layout):
    maps, bits = {}, 8
    for name in ('ao', 'roughness', 'metallic'):
        path = os.path.join(folder, name + '.png')
        if os.path.exists(path):
            maps[name], b = read_grey(path)
            bits = max(bits, b)
    shape = next(iter(maps.values())).shape
    ao = maps.get('ao', np.ones(shape))
    roughness = maps.get('roughness', np.full(shape, 0.5))
    metallic = maps.get('metallic', np.zeros(shape))
    if layout == 'orm':
        channels = [ao, roughness, metallic]                                      # R, G, B
        picture = np.stack(channels[::-1], axis=-1)                               # cv2 writes B, G, R
    else:
        # unity HDRP mask map: R metallic, G occlusion, B detail mask, A smoothness
        picture = np.stack([np.full(shape, 0.5), ao, metallic, 1.0 - roughness], axis=-1)   # B, G, R, A
    write(picture, out_path, bits)
    print('wrote', out_path, f'({bits}-bit, layout {layout})')


def unpack(packed_path, out_folder, layout):
    image = cv2.imread(packed_path, cv2.IMREAD_UNCHANGED)
    bits = 16 if image.dtype == np.uint16 else 8
    image = image.astype(np.float64) / (65535.0 if bits == 16 else 255.0)
    os.makedirs(out_folder, exist_ok=True)
    blue, green, red = image[..., 0], image[..., 1], image[..., 2]
    if layout == 'orm':
        parts = {'ao': red, 'roughness': green, 'metallic': blue}
    else:
        parts = {'metallic': red, 'ao': green, 'roughness': 1.0 - image[..., 3]}
    for name, array in parts.items():
        write(array, os.path.join(out_folder, name + '.png'), bits)
    print('wrote', ', '.join(parts), 'to', out_folder)


def flip_green(in_path, out_path):
    image = cv2.imread(in_path, cv2.IMREAD_UNCHANGED)
    top = 65535 if image.dtype == np.uint16 else 255
    flipped = image.copy()
    flipped[..., 1] = top - flipped[..., 1]            # cv2 order is B, G, R: index 1 is green
    cv2.imwrite(out_path, flipped)
    print('wrote', out_path)


def main():
    a = sys.argv[1:]
    layout = a[a.index('--layout') + 1] if '--layout' in a else 'orm'
    if a and a[0] == 'pack':
        pack(a[1], a[2], layout)
    elif a and a[0] == 'unpack':
        unpack(a[1], a[2], layout)
    elif a and a[0] == 'flipgreen':
        flip_green(a[1], a[2])
    else:
        print(__doc__)


main()
