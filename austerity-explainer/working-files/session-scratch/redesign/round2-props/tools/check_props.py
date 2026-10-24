# What this does: checks a prop library's .glb files against its index.json, reading the files themselves
# (no Blender): each file has exactly one root, named after the file; the size in index.json matches the
# model's own size; named parts' measurements (the jacket's nails, the chain's loop) match the index; the
# only digits in any lettering are "No. 1" and "No. 2"; and each prop's licence names only fonts it uses.
# Run: python3 -I check_props.py LIBRARY_FOLDER
import json
import math
import os
import re
import struct
import sys

import numpy as np

folder = sys.argv[1]
index = {entry['file']: entry for entry in json.load(open(os.path.join(folder, 'index.json')))}
problems = []


def read_glb(path):
    data = open(path, 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    return gltf, data, 20 + length + 8


def accessor(gltf, data, start, number):
    item = gltf['accessors'][number]
    view = gltf['bufferViews'][item['bufferView']]
    count = item['count']
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
    kind = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[item['componentType']]
    offset = start + view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride')
    size = np.dtype(kind).itemsize * width
    if stride and stride != size:
        raw = np.frombuffer(data, np.uint8, stride * count, offset).reshape(count, stride)[:, :size]
        return np.frombuffer(raw.tobytes(), kind).reshape(count, width)
    return np.frombuffer(data, kind, count * width, offset).reshape(count, width)


def matrix_of(node):
    if 'matrix' in node:
        return np.array(node['matrix']).reshape(4, 4).T
    translation = np.array(node.get('translation', [0, 0, 0]))
    x, y, z, w = node.get('rotation', [0, 0, 0, 1])
    rotation = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    scale = np.diag(node.get('scale', [1, 1, 1]))
    result = np.eye(4)
    result[:3, :3] = rotation @ scale
    result[:3, 3] = translation
    return result


for name in sorted(os.listdir(folder)):
    if not name.endswith('.glb'):
        continue
    stem = name[:-4]
    gltf, data, start = read_glb(os.path.join(folder, name))
    scene = gltf['scenes'][gltf.get('scene', 0)]
    roots = [gltf['nodes'][number].get('name') for number in scene['nodes']]
    if roots != [stem]:
        problems.append(f'{name}: roots {roots}, wanted exactly ["{stem}"]')
    parts = {}

    def walk(number, parent_matrix):
        node = gltf['nodes'][number]
        world = parent_matrix @ matrix_of(node)
        if 'mesh' in node:
            points = []
            for primitive in gltf['meshes'][node['mesh']]['primitives']:
                local = accessor(gltf, data, start, primitive['attributes']['POSITION']).astype(np.float64)
                points.append((np.c_[local, np.ones(len(local))] @ world.T)[:, :3])
            parts[node.get('name')] = np.concatenate(points)
        for child in node.get('children', []):
            walk(child, world)

    for number in scene['nodes']:
        walk(number, np.eye(4))
    every = np.concatenate(list(parts.values()))
    low, high = every.min(0), every.max(0)
    # glTF is y-up: Blender's (x, y, z) is glTF's (x, -z, y)
    size = {'width_x': high[0] - low[0], 'depth': high[2] - low[2], 'height': high[1] - low[1]}
    entry = index.get(name)
    if not entry:
        problems.append(f'{name}: no line in index.json')
        continue
    for key, value in size.items():
        if abs(entry['size_metres'][key] - value) > 0.0015:
            problems.append(f'{name}: index {key} {entry["size_metres"][key]}, model {value:.4f}')
    if abs(low[1]) > 0.0005:
        problems.append(f'{name}: lowest point at {low[1]:.4f} m, not on the ground')
    duplicates = [part for part in parts if part == stem]
    if duplicates:
        problems.append(f'{name}: a part also carries the prop name')
    # the prop's own measurements
    if stem == 'jacket-and-cap-on-nail':
        for nail, key in (('jacket-nail', 'jacket_nail_metres'), ('cap-nail', 'cap_nail_metres')):
            points = parts[nail]
            middle = (points.min(0) + points.max(0)) / 2
            stated = entry[key]
            if abs(middle[0] - stated['x']) > 0.0015 or abs(middle[1] - stated['height_above_base']) > 0.0015:
                problems.append(f'{name}: {nail} at x {middle[0]:.4f}, height {middle[1]:.4f}; index says {stated}')
        jacket = parts['jacket']; cap = parts['cap']
        print(f'  {stem}: jacket {jacket[:, 0].max() - jacket[:, 0].min():.3f} m wide, top {jacket[:, 1].max():.3f}; '
              f'cap from x {cap[:, 0].min():.3f} to {cap[:, 0].max():.3f}, top {cap[:, 1].max():.3f} (jacket right edge {jacket[:, 0].max():.3f})')
        if cap[:, 1].max() > jacket[:, 1].max() - 0.08 or cap[:, 0].min() < jacket[:, 0].max():
            problems.append(f'{name}: the cap is above the collar or overlaps the jacket')
    if stem.startswith('gate-board'):
        letters_low, letters_high = entry['letters_from_base_metres']
        for joint in entry['plank_joints_from_base_metres']:
            if letters_low - 0.01 < joint < letters_high + 0.01:
                problems.append(f'{name}: a joint at {joint} m runs through the letters')
    print(f'{name}: roots {roots}, parts {sorted(parts)}, size {size["width_x"]:.3f} x {size["depth"]:.3f} x {size["height"]:.3f}')
    # digits and fonts
    for words in entry.get('lettering', []):
        digits = re.sub(r'No\. [12]', '', words)
        if re.search(r'\d', digits):
            problems.append(f'{name}: a digit in the lettering "{words}"')
    fonts_named = [font for font in ('Ultra', 'Abril Fatface', 'Old Standard', 'DejaVu', 'Alfa Slab One') if font in entry['licence']]
    if len(fonts_named) > 1 or (fonts_named and not entry.get('lettering')):
        problems.append(f'{name}: licence names fonts {fonts_named}')
    print('   licence:', entry['licence'])
print()
print('PROBLEMS:' if problems else 'no problems found')
for problem in problems:
    print(' -', problem)
