import json
KIT = 'proc-work/kits/weathering'
path = KIT + '/sets/japanese_courtyard.json'
s = json.load(open(path))
if not any(c['name'] == 'roof_edge' for c in s['cameras']):
    s['cameras'].append({"name": "roof_edge", "location": [-2.4, -0.2, 2.5], "look_at": [0.4, 5.0, 3.6], "fov_v": 40.0, "photo_px": [1800, 1200],
                         "_note": "close view of the front roof edge and the eave: where moss and the drip stains of the roof show; added by the reuse proof"})
a = s['apply']
a['wallgrowth']['role_dials'] = {"wall.plaster": {"lichen_amount": 0.15, "algae_amount": 0.7}, "stone.dressed": {"lichen_amount": 0.4}, "timber.deck": {"moss_amount": 0.5, "lichen_amount": 0.0},
                                  "roof.tile": {"moss_amount": 1.2, "lichen_amount": 0.8}}
a['wallgrowth']['role_dials_why'] = "round 2: lichen speckle looked like a rash on the pale plaster (15 percent of the look's value there), planks hardly mossy"
a['soot']['role_dials'] = {"wall.plaster": {"film_mult": 0.9}, "stone.dressed": {"film_mult": 0.9}}
json.dump(s, open(path, 'w'), indent=1)
print('set r2 written')
