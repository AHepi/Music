# What this does: downloads each chosen Poly Haven model (glTF with its textures) into its own empty
# folder, plus Poly Haven's info about it (author, real size, polygon count). Free, CC0, no sign-in.
#
# Run: python3 -I download_poly_haven.py DOWNLOAD_FOLDER [surface ...] [--choices FILE] [--textures FOLDER]
#      (also downloads the wood / metal surface textures listed in SURFACES for the scripted props)
#   --choices FILE     another choices list instead of the pit village's (poly_haven_choices.py), such as
#                      chapter 2's (inflation-chapter-2-newcomers/props/chapter_2_choices.py); its own
#                      SURFACES list, if it has one, replaces the one below
#   --textures FOLDER  also fetch the list's SET_SURFACES (surfaces a set's walls wear) into FOLDER, kept
#                      the way the street's are (fetch_street_textures.py): NAME_colour.jpg at the size the
#                      list gives and NAME_normal.jpg (the OpenGL normal map) at 1k, re-saved as JPEG
# Every model and set surface name is looked up on Poly Haven first; one it doesn't know stops the run.

import io
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_haven_choices import load_choices  # noqa: E402

API = 'https://api.polyhaven.com'
HEADERS = {'User-Agent': 'paper-film-props/1.0 (free CC0 download)'}

# surface textures (Poly Haven ids) used by the scripted props, at 1k
SURFACES = ['weathered_planks', 'weathered_brown_planks', 'distressed_painted_planks', 'black_painted_planks',
            'rough_wood', 'wood_planks_grey', 'rusty_metal_02', 'rusty_metal_04', 'rusty_painted_metal',
            'metal_plate', 'rust_coarse_01', 'green_metal_rust', 'dark_rock', 'brown_mud_rocks_01']


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as reply:
        return json.load(reply)


def fetch_bytes(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as reply:
        return reply.read()


def fetch_file(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as reply, open(path, 'wb') as out:
        out.write(reply.read())


def check_names(models, set_surfaces):
    """Stops before downloading anything if Poly Haven doesn't know a model's or a set surface's name,
    or knows it as the wrong kind of thing (a surface asked for as a model). The scripted props'
    surfaces are only skipped with a note, as before."""
    problems = []
    for asset_id, wanted_type in [(m, 2) for m in models] + [(s, 1) for s in set_surfaces]:
        try:
            info = fetch_json(f'{API}/info/{asset_id}')
        except urllib.error.HTTPError as problem:
            problems.append(f'{asset_id}: not on Poly Haven ({problem.code})'); continue
        if info.get('type') != wanted_type:
            problems.append(f'{asset_id}: Poly Haven has it as type {info.get("type")}, not {"model" if wanted_type == 2 else "surface"}')
    if problems:
        sys.exit('download_poly_haven.py: stopped before downloading:\n  ' + '\n  '.join(problems))


def download_model(asset_id, size, folder):
    files = fetch_json(f'{API}/files/{asset_id}')
    gltf = files['gltf'][size]['gltf']
    target = os.path.join(folder, asset_id)
    fetch_file(gltf['url'], os.path.join(target, os.path.basename(gltf['url'])))
    for relative, item in gltf['include'].items():
        fetch_file(item['url'], os.path.join(target, relative))
    info = fetch_json(f'{API}/info/{asset_id}')
    with open(os.path.join(target, 'info.json'), 'w') as out: json.dump(info, out, indent=1)


def download_surface(asset_id, folder):
    try:
        files = fetch_json(f'{API}/files/{asset_id}')
    except Exception as problem:
        print(f'  no surface {asset_id}: {problem}'); return
    target = os.path.join(folder, 'surfaces', asset_id)
    for map_name in ('Diffuse', 'nor_gl', 'Rough', 'arm', 'Displacement'):
        if map_name in files and '1k' in files[map_name]:
            item = files[map_name]['1k'].get('jpg') or files[map_name]['1k'].get('png')
            fetch_file(item['url'], os.path.join(target, f'{map_name}.{os.path.splitext(item["url"])[1][1:]}'))


def download_set_surface(asset_id, colour_size, texture_folder):
    """One set surface, kept as the street's are: NAME_colour.jpg and NAME_normal.jpg."""
    from PIL import Image   # only needed here
    colour_path = os.path.join(texture_folder, f'{asset_id}_colour.jpg')
    normal_path = os.path.join(texture_folder, f'{asset_id}_normal.jpg')
    if os.path.exists(colour_path) and os.path.exists(normal_path):
        return
    os.makedirs(texture_folder, exist_ok=True)
    files = fetch_json(f'{API}/files/{asset_id}')
    Image.open(io.BytesIO(fetch_bytes(files['Diffuse'][colour_size]['jpg']['url']))).convert('RGB').save(colour_path, quality=86)
    Image.open(io.BytesIO(fetch_bytes(files['nor_gl']['1k']['jpg']['url']))).convert('RGB').save(normal_path, quality=92)
    info = fetch_json(f'{API}/info/{asset_id}')
    print(f'  {asset_id}: {colour_size} colour, 1k normal; one picture covers {info["dimensions"][0] / 1000:g} x {info["dimensions"][1] / 1000:g} m; '
          f'by {", ".join(info["authors"])}, CC0')


if __name__ == '__main__':
    arguments = sys.argv[1:]
    settings = {}
    for name in ('--choices', '--textures'):
        if name in arguments:
            at = arguments.index(name); settings[name] = arguments[at + 1]; del arguments[at:at + 2]
    chosen = load_choices(settings.get('--choices'))
    folder = arguments[0]
    surfaces = arguments[1:] or getattr(chosen, 'SURFACES', SURFACES)
    set_surfaces = getattr(chosen, 'SET_SURFACES', {}) if '--textures' in settings else {}
    check_names([asset_id for asset_id, _, _, _ in chosen.CHOICES], list(set_surfaces))
    for asset_id, _, _, size in chosen.CHOICES:
        print('model', asset_id); download_model(asset_id, size, folder)
    for asset_id in surfaces:
        print('surface', asset_id); download_surface(asset_id, folder)
    for asset_id, colour_size in set_surfaces.items():
        print('set surface', asset_id); download_set_surface(asset_id, colour_size, settings['--textures'])
