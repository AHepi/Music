import sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
sys.dont_write_bytecode = True
from place_kit import roles as R
table = json.load(open('/home/user/Music/plugins/explainer-film/kit/place-kit/data/roles.json'))
tests = [('Sleeper 12', ['Place: track_and_signals']), ('Sleeper 12', ['Place: rails_and_signals']), ('Platform deck', ['Place: ground_and_platforms']),
         ('Buffer stop', ['Place: goods_yard']), ('Crane jib', ['Place: goods_yard']), ('Water column', ['Place: water_tower']),
         ('Platform seat', ['Place: station_props']), ('Wagon body', ['Place: wagons']), ('Name board', ['Place: signs_and_lamps']),
         ('Goods shed wall', ['Place: goods_shed']), ('Canopy post', ['Place: station_building'])]
for name, cols in tests:
    print('%-18s in %-32s -> %s' % (name, cols[0], R.hint_role(table, {'name': name, 'collections': cols, 'materials': []})))
