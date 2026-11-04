"""
What this does: downloads the store's photographed skies (Poly Haven, CC0): whole skies photographed all round, with no
ground in them, for sky_and_haze.photo_sky(). Each at 2K (enough for lighting and a soft sky behind a place), with a
manifest of what each is and who made it. Run: python3 fetch_skies.py   (needs curl and the internet).
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SKIES = {
    # id: what it is, in plain words
    'mud_road_puresky': 'a flat grey overcast sky, soft even daylight (midday, low contrast)',
    'overcast_soil_puresky': 'a heavy grey sky of rolling rain clouds, a paler band low down (morning or afternoon)',
    'kloofendal_48d_partly_cloudy_puresky': ('a blue sky with fair-weather clouds and the sun about 48 degrees up: a bright day '
                                             'with hard shadows (midday, high contrast)'),
}


def _ask(url):
    """Poly Haven's answer for a URL, as data; asked again up to three times if an answer comes back empty."""
    import time
    for attempt in range(4):
        answer = subprocess.run(['curl', '-sS', '-m', '60', url], capture_output=True, text=True).stdout
        try:
            return json.loads(answer)
        except ValueError:
            time.sleep(3 + 4 * attempt)
    raise RuntimeError('no answer from ' + url)


def main():
    manifest_path = os.path.join(HERE, 'manifest.json')
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}
    for sky_id, what in SKIES.items():
        info = _ask('https://api.polyhaven.com/info/' + sky_id)
        files = _ask('https://api.polyhaven.com/files/' + sky_id)
        url = files['hdri']['2k']['hdr']['url']
        name = os.path.basename(url)
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            subprocess.run(['curl', '-sS', '-L', '-m', '300', '-o', path, url], check=True)
        manifest[sky_id] = {'name': info.get('name', sky_id), 'what': what, 'file': name, 'authors': sorted(info.get('authors', {})),
                            'source': 'https://polyhaven.com/a/' + sky_id, 'licence': 'CC0 1.0 (public domain)'}
        print(sky_id, name)
    json.dump(manifest, open(manifest_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
