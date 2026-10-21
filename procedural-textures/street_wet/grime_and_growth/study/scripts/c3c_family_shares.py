# What this does (plain words): turns the per-object camera-ray counts (out/c1/hits_by_object.json) into shares for each family of surfaces. Plain Python, no Blender.
# Run: python3 c3c_family_shares.py HITS.json OUT.json
import json, re, sys
RULES = [
 ('ground (add-on earth and moss ground)', r'^Astra / Courtyard receiving ground$'), ('add-on moss clumps', r'^Astra / moss grouped bodies$'), ('add-on pebbles', r'^Astra / pebbles grouped bodies$'),
 ('raked gravel court', r'^Raked gravel court$'), ('pond and basin water', r'^(Pond water|Basin water)$'),
 ('wood: veranda deck planks', r'^Astra / varied planks(\.00[0-2])?$'), ('wood: bridge planks', r'^Astra / varied planks\.00[3-7]$'),
 ('wood: posts, beams, soffit, shoji lattice', r'^(Hall posts|Hall beams|Eave soffit|Shoji bars)$'), ('paper: shoji screens and open room (glow)', r'^(Shoji paper|Open room back)$'),
 ('plaster walls', r'^(Hall plaster|Back wall, (left|right)|Right wall behind hall)$'), ('wall cap tiles', r' cap$'),
 ('roof tiles (688 copies of one tile) and roof deck', r'^(Hall roof|CT / Ceramic pan prototype)$'),
 ('plain stone: plinth, lantern finial', r'^(Stone plinth|Lantern finial)$'), ('add-on stones: stepping stones', r'^Stepping stone'), ('add-on stones: veranda steps', r'^Veranda step'),
 ('add-on stones: pond edge stones', r'^Pond edge stone'), ('add-on stones: rocks and gravel rocks', r'^(Rock \d|Gravel rock)'), ('add-on stones: lantern body', r'^Lantern (base|post|gallery|firebox|cap)$'),
 ('add-on stones: water basin and bridge piers', r'^(Water basin|Bridge pier)'), ('glow: lantern window', r'^Lantern window glow$'), ('bamboo', r'^Bamboo'), ('bark', r'^(Maple|Pine) (trunk|branch|limb)'),
 ('leaf masses', r'^(Maple leaves|Maple inner mass|Pine pads)$'), ('lily pads and lotus', r'^(Lily pads|Lotus)'), ('fallen leaves', r'^Fallen leaves$'), ('hills and far plain (backdrop)', r'^(Hills,|Dark plain)'),
]
d = json.load(open(sys.argv[1])); out = {}
for name, v in d['by_object'].items():
    fam = next((f for f, rx in RULES if re.search(rx, name)), 'UNSORTED ' + name)
    out[fam] = out.get(fam, 0) + v['share']
out['sky'] = d['sky']
res = {k: round(v, 4) for k, v in sorted(out.items(), key=lambda kv: -kv[1])}
json.dump(res, open(sys.argv[2], 'w'), indent=1)
for k, v in res.items(): print(f'{v*100:5.1f}%  {k}')
print('sum', round(sum(res.values()), 3))
