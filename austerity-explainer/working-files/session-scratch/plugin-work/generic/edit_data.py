"""What this does: makes the plugin's data files neutral again (step "make the plugin generic again"): removes the entries that only the one village request needed, rewrites the words that leaned to it.
Run once: python3 edit_data.py
"""
import json
import os

DATA = '/home/user/Music/plugins/explainer-film/kit/place-kit/data'


def load(name):
    path = os.path.join(DATA, name)
    text = open(path, encoding='utf-8').read()
    return path, json.loads(text), text.endswith('\n')


def save(path, data, newline):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(json.dumps(data, indent=1, ensure_ascii=True) + ('\n' if newline else ''))


def remove_once(items, value):
    assert value in items, value
    items.remove(value)


# ------------------------------------------------------------------------------------------------ roles.json
path, roles, nl = load('roles.json')
roles['about'] = roles['about'].replace('(thatch, barrel)', '(slate, barrel)')
table = roles['roles']
dirt = table['ground.dirt_road']
dirt['meaning'] = 'a dirt road or track that carts, vehicles or animals use (gets wheel ruts and banks; hoof prints are an option)'
dirt['note'] = 'ruts and banks are shaped by the roads step (hoof prints too, when the settings ask for them)'
remove_once(dirt['name_hints'], '\\blane\\b')
remove_once(table['floor.earth']['name_hints'], 'stall floor')
frame = table['wall.timber_frame']
remove_once(frame['name_hints'], 'wattle')
frame['meaning'] = 'a timber-framed wall with plaster or brick between the timbers'
plaster = table['wall.plaster']
remove_once(plaster['name_hints'], 'daub')
remove_once(plaster['name_hints'], 'cottage')
remove_once(table['prop.furniture']['name_hints'], 'manger')
wicker = table['prop.wicker']
wicker['name_hints'] = ['\\bhurdle' if hint == '\\bwattle (fence|panel)' else hint for hint in wicker['name_hints']]
assert '\\bhurdle' in wicker['name_hints']
cart = table['prop.cart']
remove_once(cart['name_hints'], 'carriage(?! ?wheels?)')
wood = table['prop.wood']
remove_once(wood['name_hints'], 'woodpile')
remove_once(wood['name_hints'], 'chopping')
wood['meaning'] = 'a small wooden prop: a bucket, a ladder, a log pile or a block'
save(path, roles, nl)

# ------------------------------------------------------------------------------------- real_world_facts.json
path, facts, nl = load('real_world_facts.json')
before = [f['id'] for f in facts['facts']]
facts['facts'] = [f for f in facts['facts'] if f['id'] not in ('stall_width', 'manger_height')]
for fact in facts['facts']:
    if fact['id'] == 'cart_height':
        fact['what'] = 'a hand cart or a wagon'
    if fact['id'] == 'cart_gauge':
        fact['source'] = ('the coal mine yard (mine-scene/modules/ground_and_yard.py RUT_GAUGE): its cart roads have wheel ruts 1.24 m apart (measured in the build code); the range around it is from memory '
                          '(confirm for the vehicle and the place)')
        fact['kind'] = 'judged'
print('facts removed:', [i for i in before if i not in [f['id'] for f in facts['facts']]])
save(path, facts, nl)

# ------------------------------------------------------------------------------------------------ species.json
path, species, nl = load('species.json')
assert 'dung' in species['palette'] and 'dung_lump' in species['kinds']
species['palette'] = {('clod_earth' if key == 'dung' else key): value for key, value in species['palette'].items()}
kinds = {}
for key, value in species['kinds'].items():
    if key == 'dung_lump':
        value = dict(value, colours=['clod_earth'], note='a lump of earth or a small stone on or beside a track (never on the crown)')
        kinds['clod'] = value
    else:
        kinds[key] = value
species['kinds'] = kinds
for key, value in species['kinds'].items():
    if key == 'leaf':
        value['note'] = 'single leaves, at wall feet, gutters and road edges'
    if key == 'straw':
        value['note'] = 'a few straws near doors, carts and sacks'
save(path, species, nl)

# ------------------------------------------------------------------------------------------- place_types/village
path, village, nl = load('place_types/village.json')
village['about'] = 'Starting preset for a village or hamlet: houses, a road or two, fences and gardens. It names no one kind of wall, roof, ground or climate more than another. Data only: code never names a place type. new-settings copies the allowed_off entries that fit into the settings as "off" entries.'
village['default_state'] = 'dry'
village['roles_likely'] = ['ground.dirt_road', 'ground.stone_paving', 'ground.grass', 'wall.stone', 'wall.brick', 'wall.plaster', 'wall.timber_frame',
                           'roof.tile', 'roof.slate', 'roof.shingle', 'roof.thatch', 'timber.fence', 'timber.door']
village['facts'] = ['door_height', 'door_width', 'roof_pitch', 'wall_thickness']
village['notes'] = 'walls of stone, brick, plaster or timber under roofs of tile, slate, shingle or thatch; roads paved or unpaved; the person\'s words choose the materials, the climate and the look'
save(path, village, nl)

# ------------------------------------------------------------------------------------------------ surfaces.json
path, surfaces, nl = load('surfaces.json')
for gone in ('wattle_and_daub', 'hay', 'leather'):
    assert gone in surfaces['surfaces'], gone
    del surfaces['surfaces'][gone]
save(path, surfaces, nl)

# ------------------------------------------------------------------------------------------ polyhaven_choices
path, poly, nl = load('polyhaven_choices.json')
poly['about'] = poly['about'].replace('may suit mediaeval and rural places', 'may suit many kinds of places (ground, walls, roofs, wood, stone and a few props)')
poly['about'] = poly['about'].replace('a cart, hay or straw bales, a trough, an anvil, a well, stable stalls, a thatched cottage: script those', 'a cart, hay or straw bales, a trough, an anvil, a well: script those')
poly['models'] = [m for m in poly['models'] if m['slug'] not in ('spinning_wheel_01', 'fir_sapling', 'fir_sapling_medium', 'fir_tree_01')]
poly['not_found'] = [item for item in poly['not_found'] if item not in ('stable stalls', 'thatched cottage')]
save(path, poly, nl)

# ---------------------------------------------------------------------------------- dial_table and treatments
path, dials, nl = load('dial_table.json')
text = json.dumps(dials, indent=1, ensure_ascii=True)
text = text.replace('wall feet and lane edges', 'wall feet and road edges').replace('straw pieces and dung lumps', 'straw pieces and clods')
open(path, 'w', encoding='utf-8').write(text + ('\n' if nl else ''))
path, treatments, nl = load('treatments.json')
text = json.dumps(treatments, indent=1, ensure_ascii=True)
text = text.replace('wall feet and lane edges', 'wall feet and road edges').replace('leaves, sticks, straw, pine needles, dung lumps as small 3D pieces', 'leaves, sticks, straw, pine needles, clods as small 3D pieces')
open(path, 'w', encoding='utf-8').write(text + ('\n' if nl else ''))
print('done')
