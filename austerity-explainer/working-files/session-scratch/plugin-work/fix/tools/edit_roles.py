"""Scratch helper (not part of the plugin): edits kit/place-kit/data/roles.json (meanings, name hints, the new stone.step role). Safe to run twice."""
import json

PATH = '/home/user/Music/plugins/explainer-film/kit/place-kit/data/roles.json'
data = json.loads(open(PATH, encoding='utf-8').read())
roles = data['roles']

MEANING = {
    'ground.dirt_road': 'a dirt lane or track that carts and horses drive on (gets ruts, banks, hoof prints)',
    'ground.mud': 'wet mud, a churned gateway or a puddled yard',
    'ground.forest_floor': 'leaf litter, moss and roots under trees',
    'ground.stone_paving': 'cobbles, setts, flagstones or a paved quay or square outdoors',
    'ground.gravel': 'a gravel path, towpath or drive',
    'ground.sand': 'a beach, dune or sandy floor',
    'ground.snow': 'snow lying on the ground',
    'ground.tarmac': 'a tarmac or asphalt road or yard',
    'ground.concrete': 'a concrete yard, slab or apron outdoors',
    'ground.rock': 'bare rock ground or a quarry floor',
    'ground.grass': 'a lawn, meadow or pasture',
    'ground.earth': 'plain ground, soil, a bank, a seabed or a stream bed',
    'floor.earth': 'a beaten earth floor inside a building',
    'floor.planks': 'a plank floor inside a building',
    'floor.tile': 'a tiled floor inside a building',
    'floor.stone': 'a flagstone floor (inside or on a patio; steps are stone.step, not this)',
    'floor.concrete': 'a concrete floor inside a building',
    'floor.carpet': 'a carpet or rug',
    'wall.timber_frame': 'a timber-framed wall with infill (a cottage wall)',
    'wall.log': 'a wall of stacked logs (a log cabin wall)',
    'wall.stone': 'a stone wall: house, garden, quay, canal, retaining or boundary wall',
    'wall.brick': 'a brick wall',
    'wall.cob': 'a cob or clay wall',
    'wall.concrete': 'a concrete wall',
    'wall.metal_sheet': 'a corrugated or sheet-metal wall',
    'wall.interior': 'an inside wall or partition',
    'wall.plaster': 'a plastered or whitewashed wall (the general wall)',
    'roof.thatch': 'a thatched roof (straw or reed)',
    'roof.shingle': 'a wooden shingle roof',
    'roof.tile': 'a clay tile roof',
    'roof.slate': 'a slate roof',
    'roof.metal': 'a tin or metal roof',
    'timber.post': 'a post, pile, mast, pillar or upright',
    'timber.beam': 'a beam, lintel, rafter or joist (a long piece resting on or tenoned into supports)',
    'timber.floor': 'a floor plank or a floor board in a loft or deck',
    'timber.plank': 'a plank or board (cladding, a bridge deck, a door board)',
    'timber.door': 'a door or gate leaf (may hang from hinges)',
    'timber.shutter': 'a window shutter (may hang from hinges)',
    'timber.fence': 'a fence, rail, railing, palisade or gate frame (may hang)',
    'timber.generic': 'any other wood: a frame, a weir, a wheel, a flume, a gutter',
    'stone.footing': 'a footing, plinth or foundation stone',
    'stone.chimney': 'a chimney stack',
    'stone.well': 'a well, trough or stone sink',
    'stone.rock': 'a rock, boulder, millstone or loose stone',
    'stone.step': 'a stone step, stair or tread (the rise from one step to the next is size-checked)',
    'iron.sheet': 'sheet or plate iron and steel',
    'iron.painted': 'painted metal: railings, signs, doors',
    'iron.fitting': 'ironwork: hinges, bands, hooks, chains, bollards, cleats, rings (may hang)',
    'prop.barrel': 'a barrel, cask or keg',
    'prop.crate': 'a crate, box or chest',
    'prop.cart': 'a cart or wagon body',
    'prop.wheel': 'a cart wheel',
    'prop.boat': 'a boat or hull',
    'prop.furniture': 'a table, bench, stool, chair or bed',
    'prop.wicker': 'wicker, a basket, a fish trap or a woven hurdle',
    'prop.cloth': 'a sack, cloth, canvas or awning',
    'prop.rope': 'rope, net or cable (may hang)',
    'prop.ceramic': 'a pot, jug, bowl or urn',
    'prop.straw': 'straw, hay, a bale or a haystack',
    'prop.imported': 'a downloaded or imported prop that carries its own maps',
    'prop.wood': 'a small wooden prop: a bucket, a ladder, a woodpile, a chopping block',
    'prop.generic': 'a prop nobody could name (a grey fallback; give it a real role)',
    'tree.bark': 'a tree trunk, log, branch or stump',
    'plant.foliage': 'leaves, bushes, hedges, ferns, reeds and rushes',
    'water.still': 'still water: a pond, puddle, pool, stream or river',
    'water.sea': 'sea or harbour water',
    'glass.window': 'glass: a window pane or lantern glass (may hang)',
    'never.sky': 'sky, backdrop or horizon: no surface pass',
    'never.glow': 'a glowing thing (a lit window, a flame, a lantern flame): its own light',
    'never.light': 'a lamp or sun object',
    'never.helper': 'a helper, guide, preview or empty that is not part of the place',
    'never.scatter': 'plants and litter the kit scatters itself',
}
missing = [r for r in roles if r not in MEANING and r != 'stone.step']
if missing:
    raise SystemExit('no meaning for ' + ', '.join(missing))

# the new step role goes after stone.rock
if 'stone.step' not in roles:
    rebuilt = {}
    for key, value in roles.items():
        if key == 'stone.rock':
            rebuilt['stone.step'] = {'class': 'stone', 'surface': 'stone_dressed', 'displace': False, 'may_hang': False, 'needs_support': 'part', 'max_span_metres': None, 'scale': ['step_rise'],
                                     'dials': {'moss_and_algae': 1.1, 'dirt': 1.2}, 'name_hints': [], 'exempt': {}, 'kind': 'invented',
                                     'source': 'plugin 1.4.0 fix round (23 October 2026): steps had no role of their own and fell under floor.stone, whose indoor skip switched off moss, weathering, wetness, plants and litter on outdoor steps'}
        rebuilt[key] = value
    data['roles'] = roles = rebuilt
# stone.step must come before stone.rock in the table (first match wins, and "Stone steps" holds the word stone)
order = list(roles)
if order.index('stone.step') > order.index('stone.rock'):
    step = roles.pop('stone.step')
    rebuilt = {}
    for key, value in roles.items():
        if key == 'stone.rock':
            rebuilt['stone.step'] = step
        rebuilt[key] = value
    data['roles'] = roles = rebuilt
roles['stone.step']['name_hints'] = ['\\bstairs?\\b', 'staircase', '\\btreads?\\b', '\\brisers?\\b', '\\bsteps? ?\\d', '\\b(stone|garden|front|entrance|back|canal|flight of) steps?\\b', '\\bstep$']

for key, text in MEANING.items():
    roles[key]['meaning'] = text


def hints(role, add=(), replace=None):
    current = list(roles[role]['name_hints'])
    for old, new in (replace or {}).items():
        current = [new if h == old else h for h in current]
    for h in add:
        if h not in current:
            current.append(h)
    roles[role]['name_hints'] = current


hints('timber.post', add=['\\bpiles?\\b', 'piling', '\\bmast\\b', 'stake'])
hints('timber.generic', add=['water ?wheel', 'mill ?wheel', '\\bweir\\b', 'launder', '\\bflume\\b', 'sluice', 'gutter'])
hints('stone.chimney', replace={'stack\\b': 'chimney ?stack'})
hints('prop.straw', add=['hay ?stack', 'haystack', '\\brick\\b'])
hints('roof.thatch', replace={'\\breed\\b': 'reed ?(roof|thatch)'}, add=['reed-thatch'])
hints('plant.foliage', add=['\\breeds?\\b', '\\brushes\\b'])
hints('prop.furniture', replace={'\\bbed\\b': '(?<!reed )(?<!flower )\\bbed\\b'})
hints('tree.bark', add=['willow', '\\balder\\b', '\\bbirch\\b'])
hints('ground.concrete', replace={'\\bslab\\b': 'concrete slab'})
roles['ground.concrete']['name_hints'] = [h for h in roles['ground.concrete']['name_hints'] if h != 'apron']
hints('ground.stone_paving', add=['apron', 'slipway', '\\bquay(side)? ?(floor|surface)'])
hints('ground.earth', add=['sea ?bed', 'river ?bed', 'stream ?bed'])
hints('wall.stone', add=['\\b(quay|harbou?r|sea|retaining|canal|lock|boundary|garden|yard|castle|town|city) walls?\\b', 'quay ?side wall'])
hints('prop.wicker', add=['lobster ?pot', 'crab ?pot', 'fish ?trap', 'creel'])
hints('iron.fitting', add=['bollard', 'cleat', 'mooring ring', 'iron ring'])
hints('stone.rock', add=['millstone', 'quern', 'grindstone', 'gravestone', 'headstone'])

data['about'] = data['about'].replace('and name_hints (regular expressions', 'a meaning (one plain line: what the role is for; `explainer-film-place roles --list` prints them all) and name_hints (regular expressions') \
    if 'a meaning' not in data['about'] else data['about']
open(PATH, 'w', encoding='utf-8').write(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
print('roles.json written:', len(roles), 'roles')
