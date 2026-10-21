# What this does: lists the glTF exporter's options that mention meshopt, compression, quantization or image quality (so an override can be found). Changes nothing.
import bpy
rna = bpy.ops.export_scene.gltf.get_rna_type()
for p in rna.properties:
    t = (p.identifier + ' ' + p.name + ' ' + p.description).lower()
    if any(k in t for k in ('meshopt', 'compress', 'quantiz', 'quality', 'draco', 'webp', 'bits', 'precision', 'gpu_inst', 'instanc', 'gn_mesh', 'light', 'camera')):
        dv = getattr(p, 'default', None)
        print('OPT', p.identifier, '|', p.name, '| default', dv, '|', p.description[:110])
