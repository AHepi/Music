# What this does: turns each downloaded Poly Haven model (see poly_haven_choices.py) into one film
# prop .glb: imports the glTF, makes it stand on the ground centred on the origin, thins it out if it
# is over the triangle limit, checks its size is real-world metres, and writes it with its index.json
# line (source and CC0 licence included).
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
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_library as library  # noqa: E402
from poly_haven_choices import load_choices  # noqa: E402


def convert(asset_id, file_name, description, size, triangle_limit):
    folder = os.path.join(library.DOWNLOADS, asset_id)
    gltf = [f for f in os.listdir(folder) if f.endswith('.gltf')][0]
    with open(os.path.join(folder, 'info.json')) as f: info = json.load(f)
    library.empty_scene()
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
    library.save_prop(file_name, description,
                      source=f'Poly Haven "{info["name"]}" (https://polyhaven.com/a/{asset_id}) by {authors}, {size} textures',
                      licence='CC0 1.0 (public domain)',
                      extra={'triangles_before_thinning': before} if after < before else None)


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
        convert(asset_id, file_name, description, size, getattr(chosen, 'TRIANGLE_LIMIT', 30000))
