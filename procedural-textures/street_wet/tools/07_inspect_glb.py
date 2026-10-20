# What this does (plain Python, no Blender): opens a .glb file and says what is in it: the size, how many materials, pictures and meshes, which glTF extensions are used, and for every
# material that uses clear coat, specular or a roughness picture, exactly what it carries (which picture, which set of texture coordinates, the plain numbers). It changes nothing.
# Run: python3 -I tools/07_inspect_glb.py FILE.glb [OUT.json]
import json
import os
import struct
import sys

path = sys.argv[1]
with open(path, 'rb') as handle:
    magic, version, length = struct.unpack('<4sII', handle.read(12))
    chunk_length, chunk_type = struct.unpack('<I4s', handle.read(8))
    gltf = json.loads(handle.read(chunk_length))
images = gltf.get('images', [])
textures = gltf.get('textures', [])


def picture(info):
    if info is None:
        return None
    texture = textures[info['index']]
    image = images[texture['source']]
    return {'image': image.get('name', texture['source']), 'mime': image.get('mimeType'), 'texCoord': info.get('texCoord', 0), 'bytes': gltf['bufferViews'][image['bufferView']]['byteLength'] if 'bufferView' in image else None}


summary = {'file': os.path.basename(path), 'bytes': os.path.getsize(path), 'extensionsUsed': gltf.get('extensionsUsed', []), 'materials': len(gltf['materials']), 'images': len(images),
           'meshes': len(gltf['meshes']), 'meshes_with_TEXCOORD_1': sum(1 for m in gltf['meshes'] for p in m['primitives'] if 'TEXCOORD_1' in p['attributes']), 'detail': {}}
for material in gltf['materials']:
    pbr, ext = material.get('pbrMetallicRoughness', {}), material.get('extensions', {})
    row = {'baseColorFactor': [round(v, 3) for v in pbr.get('baseColorFactor', [1, 1, 1, 1])], 'baseColorTexture': picture(pbr.get('baseColorTexture')),
           'metallicFactor': pbr.get('metallicFactor'), 'roughnessFactor': pbr.get('roughnessFactor'), 'metallicRoughnessTexture': picture(pbr.get('metallicRoughnessTexture')),
           'normalTexture': picture(material.get('normalTexture'))}
    if 'KHR_materials_clearcoat' in ext:
        c = ext['KHR_materials_clearcoat']
        row['clearcoat'] = {'factor': c.get('clearcoatFactor'), 'texture': picture(c.get('clearcoatTexture')), 'roughnessFactor': c.get('clearcoatRoughnessFactor'),
                            'roughnessTexture': picture(c.get('clearcoatRoughnessTexture')), 'normalTexture': picture(c.get('clearcoatNormalTexture'))}
    if 'KHR_materials_specular' in ext:
        s = ext['KHR_materials_specular']
        row['specular'] = {'factor': s.get('specularFactor'), 'texture': picture(s.get('specularTexture')), 'colorFactor': s.get('specularColorFactor'), 'colorTexture': picture(s.get('specularColorTexture'))}
    if 'KHR_materials_ior' in ext:
        row['ior'] = ext['KHR_materials_ior'].get('ior')
    if 'KHR_materials_emissive_strength' in ext:
        row['emissive_strength'] = ext['KHR_materials_emissive_strength'].get('emissiveStrength')
    summary['detail'][material.get('name', '?')] = row
print(f"{summary['file']}: {summary['bytes'] / 1e6:.1f} MB, {summary['materials']} materials, {summary['images']} pictures, {summary['meshes']} meshes ({summary['meshes_with_TEXCOORD_1']} with a second set of texture coordinates)")
print('extensions used:', summary['extensionsUsed'])
for name, row in summary['detail'].items():
    if 'clearcoat' in row or 'specular' in row or row.get('metallicRoughnessTexture'):
        print(' ', name)
        for key in ('baseColorFactor', 'roughnessFactor', 'metallicRoughnessTexture', 'clearcoat', 'specular', 'normalTexture'):
            if row.get(key) is not None:
                print('     ', key, row[key])
if len(sys.argv) > 2:
    json.dump(summary, open(sys.argv[2], 'w'), indent=1)
