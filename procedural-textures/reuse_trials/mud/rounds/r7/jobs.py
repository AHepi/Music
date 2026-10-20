import json
b = {'colour_and_fade.streak_width': 0.0065, 'colour_and_fade.fade_length': 0.0065, 'colour_and_fade.speck_size': 0.004, 'colour_and_fade.edge_ragged': 0.006,
     'colour_and_fade.streak_bend': 0.012, 'colour_and_fade.grain_amount': 0.07}
c = dict(b, **{'damage.pit_amount': 0.3, 'damage.pit_size': 0.0025, 'damage.break_colour': '#3a271f', 'damage.break_colour_dark': '#1f1411'})
w1, w2 = [0.42, 0.5, 0.4], [0.3, 0.78, 0.4]
jobs = {'A_base': {'params': {}, 'channel': 'Colour', 'window': w1}, 'B_finer': {'params': b, 'channel': 'Colour', 'window': w1},
        'C_pits': {'params': c, 'channel': 'Colour', 'window': w1}, 'D_finer_rut_puddle': {'params': b, 'channel': 'Colour', 'window': w2}}
print(json.dumps(jobs))
