import json,re,collections,sys
S=json.load(open('out/fp_start.json')); F=json.load(open('out/fp_final.json'))
def rx(*pats): return re.compile('^(' + '|'.join(pats) + ')$')
OWN = {
 'wood': rx(r'Astra / varied planks(\.00\d)?', r'Astra / Planked run controls(\.00\d)?', r'Bridge pier \d', r'Bridge stringers', r'Veranda step', r'Veranda step, lower', r'Hall posts', r'Hall beams', r'Eave soffit', r'Roof carrying frame', r'Gravel timber edge', r'Shoji bars', r'Stone plinth', r'G6 wood.*'),
 'roof': rx(r'Hall roof', r'CT / Ceramic pan prototype', r'Hall plaster', r'Back wall, left( cap)?', r'Back wall, right( cap)?', r'Right wall behind hall( cap)?', r'Lantern (base|post|gallery|firebox|cap|finial)', r'Water basin', r'Basin (front stone|candle stone|bucket stone|drain pebbles)', r'Rock \d', r'Pond edge stone \d+', r'Shore stones', r'G6 roof.*'),
 'ground': rx(r'Astra / Courtyard receiving ground', r'Courtyard ground source', r'Astra / moss grouped bodies', r'Astra / pebbles grouped bodies', r'Life / moss at feet and damp edges', r'Life / pebble fringe', r'Life / tufts', r'Life / moss sources \d', r'Life / pebble sources \d', r'Life / tuft sources \d', r'Life / shrubs', r'Fix / far hedge', r'Fallen leaves', r'Raked gravel court', r'Gravel kerb', r'Gravel rock \d', r'Stepping stone \d', r'G6 ground.*'),
 'pond': rx(r'Pond water', r'Basin water', r'Life / pond bed', r'Life / pond pebbles', r'Lily pads', r'Lotus blossoms', r'Life / iris clumps', r'Life / lily stems', r'Maple trunk', r'Maple branch(\.0\d\d)?', r'Maple inner mass', r'Maple leaf source \d', r'Maple leaves', r'Pine trunk', r'Pine limb(\.00\d)?', r'Pine pads', r'Bamboo stalks', r'Bamboo leaves', r'Bamboo fence', r'Basin bamboo spout', r'Basin ladle', r'G6 pond.*'),
}
OWNM = {
 'wood': rx(r'Astra / planks tone \d+(\.00\d)?', r'Dark timber', r'Beam timber', r'GARDEN timber\.post', r'Plinth stone', r'CT / Stone painterly surface\.(008|009|039|040|041|042)', r'G6 wood.*'),
 'roof': rx(r'CT / Ceramic painterly surface', r'CT / Ceramic ridge host-local surface', r'CT / Timber painterly surface', r'Plaster wall', r'GARDEN wall\.garden', r'Wall cap tile', r'GARDEN stone\.lantern', r'CT / Stone painterly surface\.(01\d|02\d|033|034|035|036|037|038)', r'GARDEN stone\.rock', r'G6 roof.*'),
 'ground': rx(r'Moss and earth', r'Raked gravel', r'Astra / moss tone \d', r'Astra / pebbles tone \d', r'Life / tuft', r'Life / shrub', r'Fallen leaves', r'CT / Stone painterly surface(\.00[1-7]|\.03[0-2])?', r'G6 ground.*'),
 'pond': rx(r'Pond water', r'Life / pond bed', r'Life / iris blade', r'Life / lily stem', r'Lily pad', r'Lotus blossom', r'Maple leaves', r'Maple inner mass', r'Bark', r'GARDEN bark\.pine', r'Pine needles', r'Bamboo stalk', r'Bamboo leaf colour', r'GARDEN ground\.earth', r'G6 pond.*'),
}
def owner_of(n, table):
    return [k for k, r in table.items() if r.match(n)]
out = {}
so, fo = S['objects'], F['objects']
removed = [n for n in so if n not in fo]
added = [n for n in fo if n not in so]
changed = {}
KEYS = ['type','colls','parent','mw','hide_render','hide_viewport','mods','mats','lightgroup','visible','ll','nv','nf','pos','uv','mesh','attrs','light','cam','splines']
for n in so:
    if n in fo:
        diffs = [k for k in KEYS if so[n].get(k) != fo[n].get(k)]
        if diffs: changed[n] = diffs
print('objects: start', len(so), 'final', len(fo), 'removed', removed, 'added', len(added), 'changed', len(changed))
# who may change what
def classify(names, table):
    res = collections.defaultdict(list); unowned = []
    for n in names:
        o = owner_of(n, table)
        if o: res[o[0]].append(n)
        else: unowned.append(n)
    return res, unowned
cres, cun = classify(changed, OWN)
print('changed objects by owner:', {k: len(v) for k, v in cres.items()})
print('CHANGED OBJECTS NOT IN ANY OWNER LIST:', [(n, changed[n]) for n in cun])
ares, aun = classify(added, OWN)
print('added objects by owner:', {k: len(v) for k, v in ares.items()})
print('ADDED OBJECTS NOT IN ANY OWNER LIST (not G6-named):', aun)
# changed in cross-owner? nothing to check without which stage; report diff keys by owner
bykey = collections.defaultdict(collections.Counter)
for n, d in changed.items():
    o = owner_of(n, OWN)
    for k in d: bykey[o[0] if o else 'NONE'][k] += 1
print('changed keys by owner', {k: dict(v) for k, v in bykey.items()})
# garden_owner labels on new objects
nolabel = [n for n in added if not fo[n].get('owner') or not fo[n].get('role')]
print('added objects without garden_owner or garden_role:', len(nolabel), nolabel[:20])
wrong = [n for n in added if fo[n].get('owner') and owner_of(n, OWN) and fo[n]['owner'] not in owner_of(n, OWN)]
print('added objects whose garden_owner label differs from the owner list', wrong[:10])
notG6 = [n for n in added if not n.startswith('G6 ')]
print('added objects whose name does not start with G6:', notG6)
notcoll = [n for n in added if not any(c.startswith('G6 ') for c in fo[n]['colls'])]
print('added objects not in a G6 collection:', notcoll[:10])
# materials
sm, fm = S['materials'], F['materials']
mrem = [n for n in sm if n not in fm]
madd = [n for n in fm if n not in sm]
mchg = [n for n in sm if n in fm and (sm[n].get('hash') != fm[n].get('hash') or sm[n].get('nodes') != fm[n].get('nodes'))]
print('materials: start', len(sm), 'final', len(fm), 'removed', mrem[:20], 'added', len(madd), 'changed', len(mchg))
mres, mun = classify(mchg, OWNM)
print('changed materials by owner:', {k: len(v) for k, v in mres.items()}, 'NOT IN ANY OWNER LIST:', mun)
# materials in two owners' lists
dbl = [n for n in mchg if len(owner_of(n, OWNM)) > 1]
print('changed materials in more than one owner list:', dbl)
nonG6 = [n for n in madd if not n.startswith('G6 ')]
print('added materials not named G6:', nonG6[:20], len(nonG6))
# node groups
sg, fg = S['node_groups'], F['node_groups']
grem = [n for n in sg if n not in fg]
gadd = [n for n in fg if n not in sg]
gchg = [n for n in sg if n in fg and sg[n].get('hash') != fg[n].get('hash')]
print('node groups: start', len(sg), 'final', len(fg), 'removed', len(grem), 'added', len(gadd), 'changed', len(gchg))
print('  changed node groups:', gchg[:20])
print('  removed node groups (first 60):', grem[:60])
# collections
sc_, fc = S['collections'], F['collections']
print('collections removed', [n for n in sc_ if n not in fc], 'added', [n for n in fc if n not in sc_])
for n in sc_:
    if n in fc:
        a, b = set(sc_[n]['objects']), set(fc[n]['objects'])
        rem = sorted(a - b); add = sorted(b - a)
        if rem or add or sc_[n]['children'] != fc[n]['children']:
            print('  collection', n, 'objects removed', rem[:8], 'added', len(add), add[:4])
# lights / light linking / world / compositor / scene
ls = {n: (so[n].get('light'), so[n].get('ll'), so[n].get('mw')) for n in so if so[n]['type'] == 'LIGHT'}
lf = {n: (fo[n].get('light'), fo[n].get('ll'), fo[n].get('mw')) for n in fo if fo[n]['type'] == 'LIGHT'}
print('lights identical (energy, colour, link, matrix):', ls == lf, len(ls))
print('scene settings identical:', S['scene'] == F['scene'])
if S['scene'] != F['scene']:
    for k in S['scene']:
        if S['scene'][k] != F['scene'].get(k): print('   differs:', k, S['scene'][k], '->', F['scene'].get(k))
# cameras
cs = {n: so[n].get('mw') for n in so if so[n]['type'] == 'CAMERA'}
print('start cameras', list(cs), 'unchanged:', all(fo[n].get('mw') == cs[n] for n in cs))
# renamed? ids in start that vanished and G6 'copies'
print('images start', len(S['images']), 'final', len(F['images']), 'removed', [i for i in S['images'] if i not in F['images']])
