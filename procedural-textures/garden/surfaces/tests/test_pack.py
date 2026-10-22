import sys, json, bpy
sys.path.insert(0, 'proc-work/garden/surfaces')
import stage_surfaces as ss
rep = ss.apply({'look': 'real', 'weathering': True, 'pack_images': True, 'rebuild_masks': 'never', 'verbose': False})
imgs = [i for i in bpy.data.images if i.source == 'FILE']
print('PACKTEST', json.dumps({'report': rep['packed_images'], 'file_images': len(imgs), 'packed': sum(1 for i in imgs if i.packed_file), 'unpacked': [i.name for i in imgs if not i.packed_file][:10]}))
