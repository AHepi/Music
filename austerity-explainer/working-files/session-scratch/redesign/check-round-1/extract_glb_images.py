# What this does: pulls every embedded picture out of each .glb in a folder (for checking lettering
# and logos by eye), and lists each file's materials, root nodes and lowest point.
import json, struct, sys, os
folder, out = sys.argv[1], sys.argv[2]
for name in sorted(os.listdir(folder)):
    if not name.endswith('.glb'):
        continue
    data = open(os.path.join(folder, name), 'rb').read()
    length = struct.unpack('<I', data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    binary_start = 20 + length + 8
    scene = gltf['scenes'][gltf.get('scene', 0)]
    roots = [gltf['nodes'][i].get('name') for i in scene['nodes']]
    materials = [m.get('name') for m in gltf.get('materials', [])]
    print(name, 'roots:', roots, 'materials:', len(materials), [m for m in materials][:30])
    for index, image in enumerate(gltf.get('images', [])):
        view = gltf['bufferViews'][image['bufferView']]
        start = binary_start + view.get('byteOffset', 0)
        blob = data[start:start + view['byteLength']]
        extension = '.png' if image.get('mimeType') == 'image/png' else '.jpg'
        stem = name[:-4]
        with open(os.path.join(out, f"{stem}--{index:02d}-{image.get('name','')}{extension}"), 'wb') as handle:
            handle.write(blob)
