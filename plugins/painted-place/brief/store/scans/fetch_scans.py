"""
What this does: downloads the store's scanned models (Poly Haven, CC0): real plants and branches photographed and
measured, each in glTF at 1K (the model, its pictures, and a manifest of what it is and who made it). The grass and
litter tools use them when they are here. Run: python3 fetch_scans.py   (needs curl and the internet).
"""
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SCANS = {
    # id: (what it is, in plain words; which tool uses it, for what)
    'grass_medium_01': ('clumps of meadow grass, several shapes', 'grass: turf and tussocks'),
    'grass_medium_02': ('clumps of longer meadow grass, several shapes', 'grass: tussocks'),
    'nettle_plant': ('a stinging nettle plant', 'grass: weeds'),
    'dandelion_01': ('dandelion plants, leaves and stalks', 'grass: weeds'),
    'dry_branches_medium_01': ('dry fallen branches and twigs', 'litter: twigs'),
}


def _ask(url):
    for attempt in range(4):
        answer = subprocess.run(['curl', '-sS', '-m', '60', url], capture_output=True, text=True).stdout
        try:
            return json.loads(answer)
        except ValueError:
            time.sleep(3 + 4 * attempt)
    raise RuntimeError('no answer from ' + url)


def _fetch(url, path):
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(['curl', '-sS', '-L', '-m', '300', '-o', path, url], check=True)


def main():
    manifest_path = os.path.join(HERE, 'manifest.json')
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    for scan_id, (what, use) in SCANS.items():
        info = _ask('https://api.polyhaven.com/info/' + scan_id)
        files = _ask('https://api.polyhaven.com/files/' + scan_id)
        model = files['gltf']['1k']['gltf']
        folder = os.path.join(HERE, scan_id)
        _fetch(model['url'], os.path.join(folder, os.path.basename(model['url'])))
        for relative, part in (model.get('include') or {}).items():
            _fetch(part['url'], os.path.join(folder, relative))
        manifest[scan_id] = {'name': info.get('name', scan_id), 'what': what, 'use': use, 'file': os.path.basename(model['url']),
                             'authors': sorted(info.get('authors', {})), 'source': 'https://polyhaven.com/a/' + scan_id,
                             'licence': 'CC0 1.0 (public domain)'}
        print(scan_id, manifest[scan_id]['file'])
    json.dump(manifest, open(manifest_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
