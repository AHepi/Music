# What this does: checks a finished set of texture pictures (colour, normal, height, roughness, metallic, ambient occlusion, or a packed ORM picture) in plain words.
# It prints one line per check, starting with PASS (fine), WARN (look at this) or FAIL (this is broken), and says what to do. It also saves three pictures
# you can look at with your own eyes, because a number can be fooled and eyes are the final judge:
#   tile_check_2x2.png        the colour picture repeated 2 x 2
#   tile_check_shifted.png    the colour picture moved by half a tile, so any seam shows as a cross in the middle
#   tile_check_normal_shifted.png  the same for the normal map
# Run (plain Python, needs numpy and cv2):
#   python3 -I check_texture_set.py FOLDER [--map normal=PATH ...] [--report report.json] [--tiny]
# FOLDER holds files named colour.png, normal.png, height.png, roughness.png, metallic.png, ao.png (also accepted: color, diffuse, albedo, normal_gl, displacement, disp,
# rough, metalness, ao, occlusion, orm or arm). Use --map NAME=PATH to point at a file with another name, for example --map normal=normal_as_uploaded_directx.png
# The thresholds are the ones tested in experiments_seamless_tiles_and_baking (see the guide, section "Is my texture really seamless and correct").
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normal_map_tools as nm  # noqa: E402

ALIASES = {
    'colour': ['colour', 'color', 'diffuse', 'albedo', 'basecolor', 'base_color', 'diff'],
    'normal': ['normal', 'normal_gl', 'normalgl', 'nor_gl', 'normal_opengl'],
    'height': ['height', 'displacement', 'disp', 'bump'],
    'roughness': ['roughness', 'rough'],
    'metallic': ['metallic', 'metalness', 'metal'],
    'ao': ['ao', 'ambientocclusion', 'occlusion'],
    'orm': ['orm', 'arm'],
}
EXTENSIONS = ['.png', '.jpg', '.jpeg', '.tif', '.tiff']
lines = []
counts = {'PASS': 0, 'WARN': 0, 'FAIL': 0, 'INFO': 0}
report = {}


def say(level, text, key=None, value=None):
    counts[level] += 1
    lines.append(f'{level:5s} {text}')
    if key:
        report[key] = {'level': level, 'text': text, 'value': value}


def find_files(folder, overrides):
    found = {}
    for kind, names in ALIASES.items():
        for name in names:
            for extension in EXTENSIONS:
                path = os.path.join(folder, name + extension)
                if os.path.exists(path):
                    found[kind] = path
                    break
            if kind in found:
                break
    for name, path in overrides.items():
        found[name] = path
    return found


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(path)
    bits = 16 if image.dtype == np.uint16 else 8
    channels = 1 if image.ndim == 2 else image.shape[2]
    picture = image.astype(np.float64) / (65535.0 if bits == 16 else 255.0)
    if picture.ndim == 3 and picture.shape[2] >= 3:
        picture = picture[..., [2, 1, 0] + list(range(3, picture.shape[2]))]       # BGR -> RGB (alpha stays last)
    return picture, bits, channels


def seam_ratio(grey):
    """Same formula as lib/texture_compare.py seam_ratio: jump across the wrap-around edge divided by the usual jump between neighbouring pixels (1.0 = seamless)."""
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2.0
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2.0
    return float(wrap / max(inner, 1e-9))


def seam_peak(grey):
    eps = 1e-9
    ix, iy = np.abs(np.diff(grey, axis=1)), np.abs(np.diff(grey, axis=0))
    wx, wy = np.abs(grey[:, 0] - grey[:, -1]), np.abs(grey[0, :] - grey[-1, :])
    return float(max(np.percentile(wx, 95) / max(np.percentile(ix, 95), eps), np.percentile(wy, 95) / max(np.percentile(iy, 95), eps)))


def as_grey(picture):
    return picture if picture.ndim == 2 else picture[..., :3].mean(axis=-1)


def check_seam(name, picture):
    channels = [as_grey(picture)] if name not in ('normal', 'colour') else [picture[..., k] for k in range(3)] if picture.ndim == 3 else [picture]
    if name == 'normal':
        channels = [picture[..., 0], picture[..., 1]]
    if name == 'colour':
        channels = [as_grey(picture)]
    ratios = [seam_ratio(c) for c in channels]
    peaks = [seam_peak(c) for c in channels]
    ratio, peak = max(ratios), max(peaks)
    text = f'{name}: tiling seam ratio {ratio:.2f} (1.0 means no seam), peak {peak:.2f}'
    if ratio <= 1.5 and peak <= 2.0:
        say('PASS', text + '. The left edge continues into the right edge and the top into the bottom.', f'seam_{name}', ratio)
    elif ratio <= 3.0 and peak <= 3.5:
        say('WARN', text + '. Borderline. The project reference tiles, which do tile, score 1.1 to 2.5 because they have hard painted edges, so this may be fine. Look at tile_check_shifted.png: a cross in the middle means a real seam.', f'seam_{name}', ratio)
    else:
        say('FAIL', text + '. A visible seam: the picture does not wrap. Make the pattern tile at the source (see the guide) instead of fixing the picture afterwards.', f'seam_{name}', ratio)


def check_bits(name, bits, want16):
    if bits == 16:
        say('PASS', f'{name}: saved with 16 bits per channel.', f'bits_{name}', bits)
    elif want16 and name == 'height':
        say('WARN', f'{name}: only 8 bits per channel (256 levels). Smooth slopes get stair steps in the normal map and in real displacement. Save height maps with 16 bits.', f'bits_{name}', bits)
    elif want16:
        say('INFO', f'{name}: 8 bits per channel. Fine for most uses (the reference normal maps are 8-bit); 16 bits avoids faint banding on very smooth surfaces.', f'bits_{name}', bits)
    else:
        say('INFO', f'{name}: 8 bits per channel, which is normal for this kind of picture.', f'bits_{name}', bits)


def check_colour(picture, bits, channels):
    rgb = picture[..., :3]
    if channels == 4:
        alpha = picture[..., 3]
        if alpha.min() < 0.999:
            say('WARN', 'colour: has an alpha (transparency) channel that is not fully opaque. A tile for walls and floors should be opaque.', 'colour_alpha', float(alpha.min()))
        else:
            say('INFO', 'colour: has an alpha channel but it is fully opaque.')
    spread = float(np.abs(rgb[..., 0] - rgb[..., 1]).mean() + np.abs(rgb[..., 1] - rgb[..., 2]).mean())
    if spread < 0.004:
        say('WARN', 'colour: the picture is pure grey (red, green and blue are equal). Fine for a mask, odd for a colour map.', 'colour_grey', spread)
    black = float((rgb.max(axis=-1) < 0.01).mean())
    white = float((rgb.min(axis=-1) > 0.99).mean())
    if black > 0.05 or white > 0.05:
        say('WARN', f'colour: {black * 100:.1f}% of the pixels are pure black and {white * 100:.1f}% pure white. Real surfaces are rarely that extreme; the picture may be clipped or contain baked lighting.', 'colour_clipped', [black, white])
    else:
        say('PASS', f'colour: only {black * 100:.1f}% pure black and {white * 100:.1f}% pure white pixels (no clipping).', 'colour_clipped', [black, white])
    lightness = float(rgb.mean())
    say('INFO', f'colour: average brightness {lightness:.2f} (0 = black, 1 = white). Surfaces in the real world sit roughly between 0.1 and 0.7; check by eye that it is not lit by a lamp or shadowed.', 'colour_brightness', lightness)


def check_normal(picture, bits, height, label='normal'):
    rgb = picture[..., :3]
    n = nm.decode_normal(rgb)
    length = np.linalg.norm(n, axis=-1)
    mean_length = float(length.mean())
    if 0.97 <= mean_length <= 1.03:
        say('PASS', f'{label}: the arrows have length {mean_length:.3f} (should be 1.0).', 'normal_length', mean_length)
    elif 0.9 <= mean_length <= 1.1:
        say('WARN', f'{label}: the arrows have length {mean_length:.3f}; fine for 8-bit rounding, a little off otherwise.', 'normal_length', mean_length)
    else:
        say('FAIL', f'{label}: the arrows have length {mean_length:.3f} (should be 1.0). Probably saved in the wrong colour space (sRGB instead of Non-Color) or not normalised.', 'normal_length', mean_length)
    mean = rgb.reshape(-1, 3).mean(axis=0)
    if abs(mean[0] - 0.5) < 0.03 and abs(mean[1] - 0.5) < 0.03 and mean[2] > 0.75:
        say('PASS', f'{label}: the average colour is {tuple(float(round(x, 3)) for x in mean)}, the flat-surface blue-violet (0.5, 0.5, 1.0) as it should be.', 'normal_mean', mean.tolist())
    else:
        say('WARN', f'{label}: the average colour is {tuple(float(round(x, 3)) for x in mean)}. A good normal map averages (0.5, 0.5, close to 1.0). If red or green is far from 0.5 the whole surface leans one way; if blue is low the map is very strong or the wrong colour space.', 'normal_mean', mean.tolist())
    tilt = np.degrees(np.arccos(np.clip(n[..., 2] / np.maximum(length, 1e-9), -1, 1)))
    p50, p99 = float(np.percentile(tilt, 50)), float(np.percentile(tilt, 99))
    if p99 < 2.0:
        say('FAIL', f'{label}: almost flat (99% of pixels tilt less than {p99:.1f} degrees). The strength is far too low, or the map was saved in the wrong colour space.', 'normal_tilt', [p50, p99])
    elif p99 > 75.0:
        say('WARN', f'{label}: extremely steep (1% of pixels tilt more than {p99:.0f} degrees). The strength may be too high.', 'normal_tilt', [p50, p99])
    else:
        say('PASS', f'{label}: tilt of the surface arrows is {p50:.1f} degrees in the middle and {p99:.1f} degrees at the 99th percentile.', 'normal_tilt', [p50, p99])
    verdict, score = nm.convention_from_the_map_alone(rgb)
    if label == 'normal_dx':
        if verdict.startswith('DirectX'):
            say('PASS', f'{label}: green points DOWN the picture = DirectX, as the name says (map-alone score {score:.2f}).', 'normal_dx_convention', verdict)
        else:
            say('WARN', f'{label}: is named DirectX but the map reads as: {verdict} (score {score:.2f}). Check which convention the file really has.', 'normal_dx_convention', verdict)
    elif verdict.startswith('OpenGL'):
        say('PASS', f'{label}: green points UP the picture = OpenGL, the Blender convention (map-alone score {score:.2f}; -1 is perfect OpenGL).', 'normal_convention', verdict)
    elif verdict.startswith('DirectX'):
        say('WARN', f'{label}: green points DOWN the picture = DirectX (map-alone score {score:.2f}). Blender expects OpenGL: flip the green channel (1 minus green), or set the Normal Map node Convention to DirectX.', 'normal_convention', verdict)
    else:
        say('INFO', f'{label}: could not tell OpenGL from DirectX from the map alone (score {score:.2f}); the map is too flat or too noisy. Compare with the height map, or look at a raised feature: in OpenGL its top edge is light green.', 'normal_convention', verdict)
    if height is not None:
        v2, green_corr, red_corr = nm.convention_from_height(rgb, height)
        if abs(green_corr) > 0.5 and red_corr < -0.5:
            side = 'OpenGL' if green_corr > 0 else 'DirectX'
            say('PASS' if (side == 'OpenGL') != (label == 'normal_dx') else 'WARN', f'{label}: agrees with the height map ({side}); green follows the height slope with correlation {green_corr:+.2f}, red with {red_corr:+.2f}.', 'normal_vs_height', [green_corr, red_corr])
        else:
            say('WARN', f'{label}: does not agree well with the height map (green {green_corr:+.2f}, red {red_corr:+.2f}; a good match is green about +0.9 and red about -0.9 for OpenGL). The two maps may come from different sources, or the red channel is also flipped.', 'normal_vs_height', [green_corr, red_corr])
        s_red, s_green, _, _ = nm.sobel_strength_that_matches(rgb, height, opengl=(green_corr > 0))
        say('INFO', f'{label}: the Sobel strength that would rebuild this normal map from the height is about {(s_red + s_green) / 2:.1f} per pixel step (height 0..1).', 'normal_strength', (s_red + s_green) / 2)


def check_height(picture, bits):
    grey = as_grey(picture)
    check_bits('height', bits, True)
    low, high = float(grey.min()), float(grey.max())
    if high - low < 0.5:
        say('WARN', f'height: only uses {low:.2f} to {high:.2f} of the 0 to 1 range. Poly Haven asks for heights stretched to the full 0 to 1 range, and an unused range wastes grey levels.', 'height_range', [low, high])
    else:
        say('PASS', f'height: uses {low:.2f} to {high:.2f} of the 0 to 1 range.', 'height_range', [low, high])
    top, bottom = float((grey >= 0.999).mean()), float((grey <= 0.001).mean())
    if top > 0.01 or bottom > 0.02:
        say('WARN', f'height: {bottom * 100:.1f}% of the pixels are exactly black and {top * 100:.1f}% exactly white. Flat clipped plateaus lose detail.', 'height_clipped', [bottom, top])
    else:
        say('PASS', f'height: little clipping ({bottom * 100:.1f}% black, {top * 100:.1f}% white).', 'height_clipped', [bottom, top])
    scale = 255 if bits == 8 else 65535
    levels = int(len(np.unique(np.round(grey * scale))))
    dx = np.abs(np.roll(grey, -1, axis=1) - grey)
    flat = float((dx < 0.5 / scale).mean())
    if flat > 0.10 and levels < 600:
        say('WARN', f'height: only {levels} different grey levels and {flat * 100:.0f}% of neighbouring pixels are exactly equal: expect terraces (stair steps) in the normal map and in displacement.', 'height_levels', [levels, flat])
    else:
        say('PASS', f'height: {levels} different grey levels; {flat * 100:.0f}% of neighbouring pixels exactly equal (flat areas).', 'height_levels', [levels, flat])


def check_roughness(picture, bits):
    grey = as_grey(picture)
    mean, spread = float(grey.mean()), float(grey.std())
    if spread < 0.01:
        say('WARN', f'roughness: practically constant ({mean:.2f}). A single number is fine for a one-material surface, but a texture usually has some variation.', 'roughness_spread', spread)
    else:
        say('PASS', f'roughness: average {mean:.2f}, spread {spread:.2f}.', 'roughness_spread', spread)
    say('INFO', 'roughness: remember it is DATA. In Blender the Image Texture node must be set to Non-Color; if a baked roughness looks much lighter than it should (average 0.5 turned into 0.74), it was baked into an sRGB image.', 'roughness_note')


def check_metallic(picture):
    grey = as_grey(picture)
    in_between = float(((grey > 0.05) & (grey < 0.95)).mean())
    metal = float((grey >= 0.95).mean())
    if float(grey.max()) < 0.05:
        say('INFO', 'metallic: no metal anywhere (all black). That is correct for stone, wood, brick.', 'metallic_fraction', metal)
    elif in_between > 0.25:
        say('WARN', f'metallic: {in_between * 100:.0f}% of the pixels are grey (neither 0 nor 1). Real surfaces are either metal or not; grey is allowed only at rust or paint edges.', 'metallic_grey', in_between)
    else:
        say('PASS', f'metallic: {metal * 100:.0f}% metal, {in_between * 100:.0f}% grey; mostly 0 or 1 as it should be.', 'metallic_fraction', metal)


def check_ao(picture):
    grey = as_grey(picture)
    if grey.min() > 0.995:
        say('FAIL', 'ao: the picture is plain white. Ambient occlusion cannot see a Bump node or a normal map; it needs real geometry (displaced mesh, high-poly).', 'ao_range', [float(grey.min()), float(grey.mean())])
    else:
        say('PASS', f'ao: darkest {grey.min():.2f}, average {grey.mean():.2f}.', 'ao_range', [float(grey.min()), float(grey.mean())])


def check_orm(picture):
    for index, name in enumerate(('red = ambient occlusion', 'green = roughness', 'blue = metallic')):
        channel = picture[..., index]
        say('INFO', f'orm: {name}: from {channel.min():.2f} to {channel.max():.2f}, average {channel.mean():.2f}.')


def main():
    arguments = sys.argv[1:]
    if not arguments:
        print(__doc__)
        return
    folder = arguments[0]
    overrides = {}
    for i, a in enumerate(arguments):
        if a == '--map':
            name, path = arguments[i + 1].split('=', 1)
            overrides[name] = path if os.path.isabs(path) else os.path.join(folder, path)
    report_path = arguments[arguments.index('--report') + 1] if '--report' in arguments else None
    files = find_files(folder, overrides)
    if not files:
        print('No texture pictures found in', folder)
        return
    pictures = {}
    for kind, path in files.items():
        pictures[kind] = load(path)
        say('INFO', f'found {kind}: {os.path.basename(path)}  {pictures[kind][0].shape[1]} x {pictures[kind][0].shape[0]}, {pictures[kind][1]}-bit, {pictures[kind][2]} channel(s)')
    sizes = {(p[0].shape[0], p[0].shape[1]) for p in pictures.values()}
    if len(sizes) > 1:
        say('FAIL', f'the pictures do not all have the same size: {sorted(sizes)}. All maps of one surface must be exactly the same size.', 'sizes', sorted(sizes))
    else:
        h, w = next(iter(sizes))
        power = (w & (w - 1) == 0) and w == h
        say('PASS' if w == h else 'WARN', f'all pictures are {w} x {h}' + ('' if w == h else ' (not square)') + ('; a power of two, which game engines like.' if power else '; not a power of two (1024, 2048, 4096...): fine for Blender, some game engines resize it.'), 'sizes', [h, w])
    height = as_grey(pictures['height'][0]) if 'height' in pictures else None
    for kind in ('colour', 'normal', 'height', 'roughness', 'metallic', 'ao'):
        if kind in pictures:
            check_seam(kind, pictures[kind][0])
    if 'colour' in pictures:
        check_colour(*pictures['colour'])
    if 'normal' in pictures:
        check_bits('normal', pictures['normal'][1], True)
        check_normal(pictures['normal'][0], pictures['normal'][1], height)
    if 'normal_dx' in pictures:
        check_normal(pictures['normal_dx'][0], pictures['normal_dx'][1], height, label='normal_dx')
    if 'height' in pictures:
        check_height(*pictures['height'][:2])
    if 'roughness' in pictures:
        check_roughness(pictures['roughness'][0], pictures['roughness'][1])
    if 'metallic' in pictures:
        check_metallic(pictures['metallic'][0])
    if 'ao' in pictures:
        check_ao(pictures['ao'][0])
    if 'orm' in pictures:
        check_orm(pictures['orm'][0])
    if 'colour' in pictures and height is not None:
        lightness = as_grey(pictures['colour'][0])
        correlation = float(np.corrcoef(lightness.ravel(), height.ravel())[0, 1])
        say('INFO', f'colour and height agree with correlation {correlation:+.2f} (stone, brick and rust usually sit between +0.3 and +0.99: darker is lower).', 'colour_height_link', correlation)
    # pictures to look at
    if 'colour' in pictures:
        colour = (np.clip(pictures['colour'][0][..., :3], 0, 1) * 255).astype(np.uint8)[..., ::-1]
        small = cv2.resize(colour, (512, 512), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(folder, 'tile_check_2x2.png'), np.vstack([np.hstack([small, small]), np.hstack([small, small])]))
        cv2.imwrite(os.path.join(folder, 'tile_check_shifted.png'), np.roll(small, (256, 256), axis=(0, 1)))
    if 'normal' in pictures:
        normal = (np.clip(pictures['normal'][0][..., :3], 0, 1) * 255).astype(np.uint8)[..., ::-1]
        cv2.imwrite(os.path.join(folder, 'tile_check_normal_shifted.png'), np.roll(cv2.resize(normal, (512, 512), interpolation=cv2.INTER_AREA), (256, 256), axis=(0, 1)))
        say('INFO', 'pictures to look at were saved: tile_check_2x2.png, tile_check_shifted.png, tile_check_normal_shifted.png (a visible cross in the middle of a shifted picture = a seam).')
    print('\n'.join(lines))
    print(f"\nSummary: {counts['PASS']} pass, {counts['WARN']} warn, {counts['FAIL']} fail.")
    if report_path:
        json.dump({'folder': folder, 'counts': counts, 'checks': report}, open(report_path, 'w'), indent=1, default=float)


main()
