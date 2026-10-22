import json, re
d = json.load(open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/out/build_A_report.json'))
S = d['stages']
print({k: list(v.keys()) for k, v in S.items()}['wood'])
def rx(*pats): return re.compile('^(' + '|'.join(pats) + ')$')
OWN_OBJ = {
 'wood': rx(r'Astra / varied planks(\.00\d)?', r'Astra / Planked run controls(\.00\d)?', r'Bridge pier \d', r'Bridge stringers', r'Veranda step', r'Veranda step, lower', r'Hall posts', r'Hall beams', r'Eave soffit', r'Roof carrying frame', r'Gravel timber edge', r'Shoji bars', r'Stone plinth', r'G6 wood.*'),
 'roof': rx(r'Hall roof', r'CT / Ceramic pan prototype', r'Hall plaster', r'Back wall, left( cap)?', r'Back wall, right( cap)?', r'Right wall behind hall( cap)?', r'Lantern (base|post|gallery|firebox|cap|finial)', r'Water basin', r'Basin (front stone|candle stone|bucket stone|drain pebbles)', r'Rock \d', r'Pond edge stone \d+', r'Shore stones', r'G6 roof.*'),
 'ground': rx(r'Astra / Courtyard receiving ground', r'Courtyard ground source', r'Astra / moss grouped bodies', r'Astra / pebbles grouped bodies', r'Life / moss at feet and damp edges', r'Life / pebble fringe', r'Life / tufts', r'Life / moss sources \d', r'Life / pebble sources \d', r'Life / tuft sources \d', r'Life / shrubs', r'Fix / far hedge', r'Fallen leaves', r'Raked gravel court', r'Gravel kerb', r'Gravel rock \d', r'Stepping stone \d', r'G6 ground.*'),
 'pond': rx(r'Pond water', r'Basin water', r'Life / pond bed', r'Life / pond pebbles', r'Lily pads', r'Lotus blossoms', r'Life / iris clumps', r'Life / lily stems', r'Maple trunk', r'Maple branch(\.0\d\d)?', r'Maple inner mass', r'Maple leaf source \d', r'Maple leaves', r'Pine trunk', r'Pine limb(\.00\d)?', r'Pine pads', r'Bamboo stalks', r'Bamboo leaves', r'Bamboo fence', r'Basin bamboo spout', r'Basin ladle', r'G6 pond.*'),
}
OWN_MAT = {
 'wood': rx(r'Astra / planks tone \d+(\.00\d)?', r'Dark timber', r'Beam timber', r'GARDEN timber\.post', r'Plinth stone', r'CT / Stone painterly surface\.(008|009|039|040|041|042)', r'G6 wood.*'),
 'roof': rx(r'CT / Ceramic painterly surface', r'CT / Ceramic ridge host-local surface', r'CT / Timber painterly surface', r'Plaster wall', r'GARDEN wall\.garden', r'Wall cap tile', r'GARDEN stone\.lantern', r'CT / Stone painterly surface\.(01\d|02\d|033|034|035|036|037|038)', r'GARDEN stone\.rock', r'G6 roof.*'),
 'ground': rx(r'Moss and earth', r'Raked gravel', r'Astra / moss tone \d', r'Astra / pebbles tone \d', r'Life / tuft', r'Life / shrub', r'Fallen leaves', r'CT / Stone painterly surface(\.00[1-7]|\.03[0-2])?', r'G6 ground.*'),
 'pond': rx(r'Pond water', r'Life / pond bed', r'Life / iris blade', r'Life / lily stem', r'Lily pad', r'Lotus blossom', r'Maple leaves', r'Maple inner mass', r'Bark', r'GARDEN bark\.pine', r'Pine needles', r'Bamboo stalk', r'Bamboo leaf colour', r'GARDEN ground\.earth', r'G6 pond.*'),
}
tot = 0
for st, v in S.items():
    if st == 'final': 
        print('final', {k: v[k] for k in v if k in ('objects', 'materials', 'changed_objects', 'changed_materials', 'violations')})
        continue
    keys = v.keys()
    co = v.get('changed_objects', []); ao = v.get('added_objects', []); cm = v.get('changed_materials', []); am = v.get('added_materials', []); cg = v.get('changed_groups', []); ag = v.get('added_groups', [])
    out_o = [n for n in co + ao if not OWN_OBJ[st].match(n)]
    out_m = [n for n in cm if not OWN_MAT[st].match(n)]
    # added materials should be G6 <stage>
    out_am = [n for n in am if not n.startswith('G6 ' + st)]
    # also check against other stages
    cross_o = [n for n in co if not OWN_OBJ[st].match(n) and any(OWN_OBJ[o].match(n) for o in OWN_OBJ if o != st)]
    print(st, 'violations', v['violations'], '| changed objs', len(co), 'added', len(ao), '| outside own list:', out_o[:10], '| changed mats', len(cm), 'outside own:', out_m[:10], '| added mats not G6:', out_am[:10], '| groups changed', cg[:5], 'added', len(ag))
