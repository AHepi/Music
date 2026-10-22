import sys, json
sys.path.insert(0, 'proc-work/garden/surfaces')
import stage_surfaces as ss
r = ss.apply({'look': 'real', 'weathering': True, 'rebuild_masks': 'always', 'verbose': False})
w = r['weathering']
print('SMOKE', json.dumps({'seconds': r['seconds'], 'mask': w['mask_pack'], 'mask_s': w.get('mask_seconds'), 'layers': w['materials_per_layer'], 'problems': w['problems'], 'unassigned': w['unassigned_objects']}))
