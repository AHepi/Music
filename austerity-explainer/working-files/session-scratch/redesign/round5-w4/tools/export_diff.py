"""What this does (scratch, round 5 W4 helper): compares the Works export before and after a re-export: object and
material names in each .glb (gone, added), works-shot.json (which keys changed, with the old and new values for small
ones) and the camera files (same or not). Use: python3 export_diff.py BEFORE_NAMES.json AFTER_NAMES.json BEFORE_FOLDER AFTER_FOLDER"""
import json
import os
import sys

before_names, after_names = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
before_folder, after_folder = sys.argv[3], sys.argv[4]
print('== object and material names in the .glb files')
for name in sorted(set(before_names) | set(after_names)):
    b, a = before_names.get(name), after_names.get(name)
    if b is None or a is None:
        print(f'{name}: only {"after" if b is None else "before"}')
        continue
    for kind in ('nodes', 'materials'):
        gone = sorted(set(b[kind]) - set(a[kind]))
        added = sorted(set(a[kind]) - set(b[kind]))
        same_count = len(b[kind]) == len(a[kind])
        print(f'{name} {kind}: {len(b[kind])} -> {len(a[kind])}; gone {gone if gone else "none"}; added {added if added else "none"}')
print('== works-shot.json')
old, new = json.load(open(os.path.join(before_folder, 'works-shot.json'))), json.load(open(os.path.join(after_folder, 'works-shot.json')))


def walk(a, b, path):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                print(f'  added {path}{key}')
            elif key not in b:
                print(f'  gone {path}{key}')
            else:
                walk(a[key], b[key], f'{path}{key}.')
    elif a != b:
        text = f'{json.dumps(a)} -> {json.dumps(b)}'
        print(f'  changed {path[:-1]}: {text if len(text) < 300 else text[:300] + " ..."}')


walk(old, new, '')
print('== camera files')
for view in ('w1', 'w2', 'w3', 'w4'):
    a = open(os.path.join(before_folder, f'works-camera-{view}.json')).read()
    b = open(os.path.join(after_folder, f'works-camera-{view}.json')).read()
    print(f'works-camera-{view}.json: {"the same, byte for byte" if a == b else "changed"}')
