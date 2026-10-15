# What this does: turns each downloaded Poly Haven model (see poly_haven_choices.py) into one film
# prop .glb: imports the glTF, makes it stand on the ground centred on the origin, thins it out if it
# is over the triangle limit, checks its size is real-world metres, and writes it with its index.json
# line (source and CC0 licence included).
#
# A model whose pictures carry something the film must not show (a maker's printed label, say) is
# patched first, if its choices list says so in PAINT_OUT: the download is copied into the scratch
# folder (painted-out/), each named box of every picture in the copy's textures folder (colour,
# roughness and relief alike) is covered with a patch of the same surface from just beside it, with
# soft edges, and saved as PNG (so nothing outside the boxes changes), and the model is imported from
# the copy; the download itself is left as it came. The index.json line then says what was painted out
# ("painted_out").
#
# Run (after download_poly_haven.py):
#   blender -b --python convert_poly_haven.py              (every choice)
#   blender -b --python convert_poly_haven.py -- Lantern_01 (just some)
# Settings, after "--" (without them it works on the pit village's list and library, as before):
#   --choices FILE             another choices list (chapter 2's: inflation-chapter-2-newcomers/props/chapter_2_choices.py);
#                              its props go to the library the list names (LIBRARY), with their own index.json
#   --library NAME_OR_FOLDER   the prop library to write to, if not the list's own
#   --scratch FOLDER           where the downloads are (FOLDER/downloads), instead of PIT_VILLAGE_SCRATCH

import json
import os
import shutil
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_library as library  # noqa: E402
from poly_haven_choices import load_choices  # noqa: E402


def paint_out_boxes(path, patches, feather=4):
    """Covers boxes of one picture, each with the patch of the same size found a little way off, blending
    over `feather` pixels at its edges, and saves the result beside it as a PNG (no second JPEG squeeze:
    the roughness picture keeps three separate measures in its three colours, which JPEG smudges). Each
    patch's box: (left, top, right, bottom) and its 'from': (across, down), as fractions of the picture's
    width and height from its top left corner as a picture viewer shows it. Returns the PNG's path."""
    image = bpy.data.images.load(path)
    width, height = image.size
    channels = image.channels
    pixels = np.empty(width * height * channels, np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(height, width, channels)[::-1].copy()   # Blender keeps the bottom row first
    for patch in patches:
        box, source_offset = patch['box'], patch['from']
        left, top, right, bottom = (int(round(box[0] * width)), int(round(box[1] * height)),
                                    int(round(box[2] * width)), int(round(box[3] * height)))
        across, down = int(round(source_offset[0] * width)), int(round(source_offset[1] * height))
        if not (0 <= left + across and right + across <= width and 0 <= top + down and bottom + down <= height):
            raise SystemExit(f'paint_out_boxes: the patch for {os.path.basename(path)} would come from outside the picture')
        cover = pixels[top + down:bottom + down, left + across:right + across].copy()
        rows = np.minimum(np.arange(bottom - top), np.arange(bottom - top)[::-1])[:, None]
        columns = np.minimum(np.arange(right - left), np.arange(right - left)[::-1])[None, :]
        weight = np.clip(np.minimum(rows, columns) / feather, 0, 1)[..., None]
        pixels[top:bottom, left:right] = cover * weight + pixels[top:bottom, left:right] * (1 - weight)
    image.pixels.foreach_set(pixels[::-1].ravel())
    png = os.path.splitext(path)[0] + '.png'
    image.file_format = 'PNG'
    image.filepath_raw = png
    image.save()
    bpy.data.images.remove(image)
    return png


def painted_out_copy(asset_id, folder, patches):
    """A copy of a model's download in the scratch folder with every picture in its textures folder
    patched as PAINT_OUT says (see paint_out_boxes) and saved as PNG, its .gltf pointed at the PNGs.
    Returns the copy's folder."""
    copy = os.path.join(library.SCRATCH, 'painted-out', asset_id)
    if os.path.isdir(copy):
        shutil.rmtree(copy)
    shutil.copytree(folder, copy)
    renamed = {}
    pictures = os.path.join(copy, 'textures')
    for picture in sorted(os.listdir(pictures)):
        if not picture.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        png = paint_out_boxes(os.path.join(pictures, picture), patches)
        renamed[f'textures/{picture}'] = f'textures/{os.path.basename(png)}'
        if os.path.basename(png) != picture:
            os.remove(os.path.join(pictures, picture))
        print(f'painted out {len(patches)} box(es) in {picture}, saved as {os.path.basename(png)}')
    for gltf_file in [f for f in os.listdir(copy) if f.endswith('.gltf')]:
        with open(os.path.join(copy, gltf_file)) as handle:
            description = json.load(handle)
        for image in description.get('images', []):
            if image.get('uri') in renamed:
                image['uri'] = renamed[image['uri']]
                image['mimeType'] = 'image/png'
        with open(os.path.join(copy, gltf_file), 'w') as handle:
            json.dump(description, handle)
    return copy


def convert(asset_id, file_name, description, size, triangle_limit, patches=None):
    folder = os.path.join(library.DOWNLOADS, asset_id)
    gltf = [f for f in os.listdir(folder) if f.endswith('.gltf')][0]
    with open(os.path.join(folder, 'info.json')) as f: info = json.load(f)
    library.empty_scene()
    if patches:
        folder = painted_out_copy(asset_id, folder, patches)
    bpy.ops.import_scene.gltf(filepath=os.path.join(folder, gltf))
    library.stand_on_ground(file_name)
    before = library.count_triangles()
    after = library.reduce_triangles(triangle_limit - 2000)
    # Poly Haven gives real size in millimetres; compare with what we imported (metres)
    low, high = library.bounds()
    expected_height = info['dimensions'][2] / 1000
    measured_height = high.z - low.z
    if abs(measured_height - expected_height) > 0.05 * expected_height + 0.01:
        print(f'WARNING {asset_id}: height {measured_height:.3f} m, Poly Haven says {expected_height:.3f} m')
    authors = ', '.join(info['authors'])
    extra = {}
    if after < before:
        extra['triangles_before_thinning'] = before
    if patches:
        extra['painted_out'] = [patch['what'] for patch in patches]
    library.save_prop(file_name, description,
                      source=f'Poly Haven "{info["name"]}" (https://polyhaven.com/a/{asset_id}) by {authors}, {size} textures',
                      licence='CC0 1.0 (public domain)',
                      extra=extra or None)


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    choices_file = None
    if '--choices' in arguments:
        at = arguments.index('--choices'); choices_file = arguments[at + 1]; del arguments[at:at + 2]
    chosen = load_choices(choices_file)
    if getattr(chosen, 'LIBRARY', None):
        library.use_library(chosen.LIBRARY)
    wanted = library.take_folder_settings(arguments)   # --library here overrides the list's own
    print('writing props to', library.PROPS_FOLDER)
    for asset_id, file_name, description, size in chosen.CHOICES:
        if wanted and asset_id not in wanted: continue
        convert(asset_id, file_name, description, size, getattr(chosen, 'TRIANGLE_LIMIT', 30000),
                getattr(chosen, 'PAINT_OUT', {}).get(asset_id))
