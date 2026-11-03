"""
What this does: downloads a shelf of free photographed surfaces (Poly Haven, CC0) for builders to use: for each set the
colour picture, the roughness picture and the height picture at 2K, plus a manifest with the real size in metres and the
authors. Run: python3 fetch_surfaces.py   (needs curl and the internet; the builders get the result, not this script).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = {
    # id: what it is for, in plain words
    'brick_wall_02': 'old red brick wall, mortar joints, some staining',
    'dark_brick_wall': 'dark sooty brick, industrial',
    'rusty_corrugated_iron': 'corrugated iron roof or wall, heavily rusted',
    'worn_corrugated_iron': 'corrugated iron, painted and worn, less rust',
    'rusty_metal_02': 'rusted iron sheet, for tanks, drums, bins, gun shields',
    'brown_mud': 'brown mud with stones and twigs, dry-ish',
    'muddy_tracks': 'wet mud with wheel tracks',
    'mud_forest': 'dark wet forest mud',
    'gravel_road': 'gravel road with ruts',
    'worn_plaster_wall': 'plaster, worn, patched, stained',
    'damaged_plaster': 'plaster broken away to the brick beneath',
    'hessian_380': 'sacking (hessian), for sandbags and sacks',
    'rough_linen': 'rough canvas, for tents and tarpaulins',
    'distressed_painted_planks': 'painted planks, paint worn and peeling',
    'old_planks_02': 'old grey planks',
    'old_stone_wall_02': 'old rubble stone wall',
    'cobblestone_floor_01': 'cobbles, worn',
}


def fetch(url, path):
    if os.path.exists(path):
        return
    subprocess.run(['curl', '-sS', '-L', '-m', '300', '-o', path, url], check=True)


def main():
    manifest_path = os.path.join(HERE, 'manifest.json')
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    for set_id, what in SETS.items():
        folder = os.path.join(HERE, set_id)
        os.makedirs(folder, exist_ok=True)
        info = json.loads(subprocess.run(['curl', '-sS', '-m', '60', 'https://api.polyhaven.com/info/' + set_id], capture_output=True, text=True, check=True).stdout)
        files = json.loads(subprocess.run(['curl', '-sS', '-m', '60', 'https://api.polyhaven.com/files/' + set_id], capture_output=True, text=True, check=True).stdout)
        maps = {}
        for key, short in (('Diffuse', 'diff'), ('Rough', 'rough'), ('Displacement', 'disp')):
            if key not in files or '2k' not in files[key] or 'jpg' not in files[key]['2k']:
                continue
            url = files[key]['2k']['jpg']['url']
            name = os.path.basename(url)
            fetch(url, os.path.join(folder, name))
            maps[short] = name
        size = info.get('dimensions') or [1000, 1000]
        manifest[set_id] = {
            'name': info.get('name', set_id),
            'what': what,
            'size_m': [round(size[0] / 1000.0, 2), round(size[1] / 1000.0, 2)],
            'authors': sorted(info.get('authors', {})),
            'maps': maps,
            'source': 'https://polyhaven.com/a/' + set_id,
            'licence': 'CC0 1.0 (public domain)',
        }
        print(set_id, maps, manifest[set_id]['size_m'], file=sys.stderr)
    json.dump(manifest, open(manifest_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
