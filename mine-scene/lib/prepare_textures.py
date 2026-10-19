# What this does: turns the uploaded colour pictures and the uploaded normal/displacement maps into the exact files the mine
# scene reads. It (1) flips the green channel of every normal map, because the uploaded maps point their green "up/down"
# the other way round from the way Blender reads them (checked by measuring the maps against each other), (2) turns each
# displacement map into a smoother 16-bit height picture so real surface displacement does not show 256-step stair banding,
# (3) copies the colour pictures across, and (4) makes two extra maps of my own: how shiny each spot is (puddles shine,
# dry mud does not) and how metallic (paint-scraped steel is, rust is not).
# Use: python3 -I prepare_textures.py COLOUR_FOLDER MAPS_FOLDER OUTPUT_FOLDER
import json
import os
import sys

import numpy as np
from PIL import Image

SURFACE_NAMES = {
    'brick': ('brick_wall_colour.png', 'brick_wall'),
    'slate': ('roof_slate_colour.png', 'roof_slate'),
    'wood': ('aged_wood_colour.png', 'aged_wood'),
    'metal': ('rusted_metal_colour.png', 'rusted_metal'),
    'mud': ('ground_mud_colour_blue_puddles.png', 'ground_mud'),
    'gravel': ('gravel_ballast_colour.png', 'gravel_ballast'),
}


def blur_with_wraparound(values, sigma):
    """Soft blur that wraps round the edges, because every one of these pictures is a seamless tile."""
    radius = int(3 * sigma) + 1
    offsets = np.arange(-radius, radius + 1)
    weights = np.exp(-(offsets ** 2) / (2 * sigma ** 2))
    weights /= weights.sum()
    for axis in (0, 1):
        blurred = np.zeros_like(values)
        for offset, weight in zip(offsets, weights):
            blurred += weight * np.roll(values, offset, axis=axis)
        values = blurred
    return values


def smoothstep(low, high, values):
    t = np.clip((values - low) / (high - low), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def save_16_bit_grey(values_0_to_1, path):
    Image.fromarray((np.clip(values_0_to_1, 0, 1) * 65535).astype(np.uint16)).save(path)


def save_8_bit_grey(values_0_to_1, path):
    Image.fromarray((np.clip(values_0_to_1, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(path)


def main(colour_folder, maps_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    report = {}
    for surface, (colour_file, map_prefix) in SURFACE_NAMES.items():
        colour = np.array(Image.open(os.path.join(colour_folder, colour_file)).convert('RGB'))
        Image.fromarray(colour).save(os.path.join(output_folder, f'{surface}_colour.png'))

        normal = np.array(Image.open(os.path.join(maps_folder, f'{map_prefix}_normal.png')).convert('RGB'))
        normal_for_blender = normal.copy()
        normal_for_blender[..., 1] = 255 - normal[..., 1]
        Image.fromarray(normal_for_blender).save(os.path.join(output_folder, f'{surface}_normal.png'))

        height = np.array(Image.open(os.path.join(maps_folder, f'{map_prefix}_displacement.png')).convert('L')).astype(np.float64) / 255.0
        smooth_height = blur_with_wraparound(height, 0.8)
        low, high = np.percentile(smooth_height, 0.5), np.percentile(smooth_height, 99.5)
        smooth_height = np.clip((smooth_height - low) / (high - low), 0, 1)
        save_16_bit_grey(smooth_height, os.path.join(output_folder, f'{surface}_height.png'))

        red, green, blue = [colour[..., i].astype(np.float64) for i in range(3)]
        if surface == 'mud':
            # puddles are the blue-grey patches (blue above red); dry mud is brown (red well above blue)
            puddle = blur_with_wraparound(smoothstep(-25.0, 15.0, blue - red), 1.0)
            wet_sheen = smoothstep(0.55, 0.15, smooth_height) * 0.4
            rough = np.clip(0.92 - 0.87 * puddle - wet_sheen * (1 - puddle), 0.05, 1.0)
            save_8_bit_grey(rough, os.path.join(output_folder, f'{surface}_roughness.png'))
            save_8_bit_grey(puddle, os.path.join(output_folder, f'{surface}_puddle_mask.png'))
            report[surface] = {'puddle_share_of_tile': float(puddle.mean())}
        elif surface == 'metal':
            rust = blur_with_wraparound(smoothstep(10.0, 70.0, red - blue), 1.0)
            rough = 0.45 + 0.4 * rust
            metallic = 0.55 * (1 - rust)
            save_8_bit_grey(rough, os.path.join(output_folder, f'{surface}_roughness.png'))
            save_8_bit_grey(metallic, os.path.join(output_folder, f'{surface}_metallic.png'))
            report[surface] = {'rust_share_of_tile': float(rust.mean())}
        report.setdefault(surface, {})['height_percentiles_used'] = [float(low), float(high)]
    with open(os.path.join(output_folder, 'prepared.json'), 'w') as handle:
        json.dump(report, handle, indent=1)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:4])
