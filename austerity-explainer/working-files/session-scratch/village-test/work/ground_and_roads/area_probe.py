import sys, numpy as np, bpy, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit.growth import scatter
from place_kit import house_numbers
ground = [o for o in bpy.data.objects if o.type == 'MESH' and (o.get('place_role') or '').startswith('ground.')]
a = scatter.ground_area(ground)
mn_p = house_numbers.value('place_audit.plants_min_per_100_square_metres'); mn_l = house_numbers.value('place_audit.litter_min_per_100_square_metres')
cap = house_numbers.value('place_audit.scatter_pieces_max')
print('GROUNDAREA', json.dumps({'area_m2': round(a), 'plants_needed': int(np.ceil(mn_p * a / 100)), 'litter_needed': int(np.ceil(mn_l * a / 100)), 'cap': cap}))
