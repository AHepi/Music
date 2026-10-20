# ROUND 2 copy of 13_stage_numbers.py: the same, reading the round 2 stage pictures in work/s06 (the wet glb baked again with the round 2 layer; the stand-in painting is the round 2 EEVEE wet
# picture) and writing sheets/stage_*_round2.jpg and work/s06/stage_numbers.json.
# What this does (plain Python, no Blender): reads the pictures the stage test drew (work/s05, made by stage_test/run_stage_test.mjs) and makes the sheets and numbers of the stage check.
# The projected pictures are written by the film's own projection code as plain linear light (the film's finishing step does the colour encoding afterwards), so this script encodes them
# (linear to sRGB) before showing them or comparing them with the painting.
# Writes sheets/stage_maps_ablation_round2.jpg, sheets/stage_projection_round2.jpg, work/s05/stage_numbers.json. Run: python3 -I tools/13_stage_numbers.py
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
S = f'{ROOT}/work/s06'
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)


def encode(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)


def load(name, encoded=False):
    array = np.asarray(Image.open(f'{S}/{name}.png').convert('RGB')).astype(float) / 255
    return encode(array) if encoded else array


def sheet(images, labels, out, w=540, h=960):
    canvas = Image.new('RGB', (len(images) * (w + 8) + 8, h + 34), (18, 18, 20))
    draw = ImageDraw.Draw(canvas)
    for i, (array, label) in enumerate(zip(images, labels)):
        canvas.paste(Image.fromarray((np.clip(array, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((w, h)), (8 + i * (w + 8), 34))
        draw.text((10 + i * (w + 8), 6), label, font=F, fill=(240, 220, 160))
    canvas.save(out, quality=86)
    print('wrote', out, canvas.size)


ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/main_id.png').convert('RGB'))[..., 0].astype(int)
road = id_map == ids['street_setts']
luma = lambda p: 0.2126 * p[..., 0] + 0.7152 * p[..., 1] + 0.0722 * p[..., 2]  # noqa: E731
result = {'ablation': {}}
names = ['still_0_today', 'still_1_wet_glb_no_maps', 'still_2_roughness_map', 'still_3_plus_clearcoat_maps', 'still_4_plus_specularity_map']
labels = ['0 street.glb as the film has it', '1 street-wet.glb, all maps off', '2 + roughness map', '3 + clear coat maps', '4 + specularity map = all']
pictures = [load(n) for n in names]
previous = None
for name, picture in zip(names, pictures):
    l = luma(picture)
    row = {'road_mean_brightness': round(float(l[road].mean()), 3), 'road_brightest_1_percent': round(float(np.percentile(l[road], 99)), 3)}
    if previous is not None:
        row['road_mean_abs_difference_from_previous_step'] = round(float(np.abs(l - previous)[road].mean()), 4)
    result['ablation'][name] = row
    previous = l
    print(name, row)
sheet(pictures, labels, f'{ROOT}/sheets/stage_maps_ablation_round2.jpg')
plate = np.asarray(Image.open(f'{ROOT}/stage_test/kit/assets/models/pit-village/plate-wet.png').convert('RGB')).astype(float) / 255
proj_names = ['proj_a_today_glb_matte_projector', 'proj_b_today_glb_matte_moved', 'proj_c_wet_glb_matte_moved', 'proj_d_wet_glb_matteoff_moved', 'proj_e_wet_glb_matte_weights', 'proj_f_wet_glb_matteoff_weights']
proj = {n: load(n, encoded=True) for n in proj_names}
sheet(list(proj.values()), ['a today glb, the plate view', 'b today glb, moved', 'c wet glb, matte ON (film today), moved', 'd wet glb, matte OFF, moved', 'e weights, matte on', 'f weights, matte off'],
      f'{ROOT}/sheets/stage_projection_round2.jpg')
a, b, c, d, e, f = (proj[n] for n in proj_names)
result['projection'] = {
    'plate_view_vs_painting_mean_abs_difference_on_road': round(float(np.abs(a - plate)[road].mean()), 4),
    'plate_view_vs_painting_mean_abs_difference_whole_picture_sky_differs': round(float(np.abs(a - plate).mean()), 4),
    'moved_today_glb_vs_wet_glb_matte_on': round(float(np.abs(b - c).mean()), 4),
    'moved_wet_glb_matte_on_vs_off': round(float(np.abs(c - d).mean()), 4),
    'moved_wet_glb_matte_on_vs_off_on_road': round(float(np.abs(c - d)[road].mean()), 4),
    'share_of_moved_picture_wearing_glb_own_surface_matte_on': round(float(((e[..., 2] > e[..., 0] * 1.6) & (e[..., 2] > 0.18)).mean()), 4),
    'share_of_moved_picture_wearing_glb_own_surface_matte_off': round(float(((f[..., 2] > f[..., 0] * 1.6) & (f[..., 2] > 0.18)).mean()), 4)}
print(json.dumps(result['projection'], indent=1))
json.dump(result, open(f'{S}/stage_numbers.json', 'w'), indent=1)
