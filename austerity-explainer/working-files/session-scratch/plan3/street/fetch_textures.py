# Downloads the Poly Haven (CC0) texture maps the pit village street uses: colour, normal (OpenGL) and roughness.
import json, os, sys, urllib.request, subprocess
OUT = sys.argv[1]
WANTED = {  # name: resolution
    'red_brick': '2k', 'castle_brick_02_red': '1k', 'stone_brick_wall_001': '2k', 'square_cobblestone': '2k',
    'large_grey_tiles': '1k', 'large_sandstone_blocks': '1k', 'rock_surface': '1k', 'roof_slates_03': '2k',
    'grey_plaster_02': '1k', 'green_rough_planks': '1k', 'distressed_painted_planks': '1k', 'blue_painted_planks': '1k',
    'rusty_metal_02': '1k', 'rocks_ground_02': '1k', 'muddy_tracks': '1k',
}
os.makedirs(OUT, exist_ok=True)
for name, res in WANTED.items():
    files = json.loads(subprocess.check_output(['curl', '-sS', f'https://api.polyhaven.com/files/{name}']))
    for key, short in (('Diffuse', 'diff'), ('nor_gl', 'nor_gl'), ('Rough', 'rough')):
        url = files[key][res]['jpg']['url']
        path = os.path.join(OUT, f'{name}_{short}_{res}.jpg')
        if not os.path.exists(path):
            subprocess.check_call(['curl', '-sS', '-o', path, url])
        print(path)
