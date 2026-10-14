# What this does: downloads each chosen Poly Haven model (glTF with its textures) into its own empty
# folder, plus Poly Haven's info about it (author, real size, polygon count). Free, CC0, no sign-in.
#
# Run: python3 -I download_poly_haven.py DOWNLOAD_FOLDER
#      (also downloads the wood / metal surface textures listed in SURFACES for the scripted props)

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_haven_choices import CHOICES  # noqa: E402

API = 'https://api.polyhaven.com'
HEADERS = {'User-Agent': 'paper-film-props/1.0 (free CC0 download)'}

# surface textures (Poly Haven ids) used by the scripted props, at 1k
SURFACES = ['weathered_planks', 'weathered_brown_planks', 'distressed_painted_planks', 'black_painted_planks',
            'rough_wood', 'wood_planks_grey', 'rusty_metal_02', 'rusty_metal_04', 'rusty_painted_metal',
            'metal_plate', 'rust_coarse_01', 'green_metal_rust', 'dark_rock', 'brown_mud_rocks_01']


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as reply:
        return json.load(reply)


def fetch_file(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)) as reply, open(path, 'wb') as out:
        out.write(reply.read())


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


if __name__ == '__main__':
    folder = sys.argv[1]
    surfaces = sys.argv[2:] or SURFACES
    for asset_id, _, _, size in CHOICES:
        print('model', asset_id); download_model(asset_id, size, folder)
    for asset_id in surfaces:
        print('surface', asset_id); download_surface(asset_id, folder)
