import json, re, sys
look = sys.argv[1]
S = json.load(open('fp_start.json')); F = json.load(open(f'fp_{look}.json'))
OWN = [  # (regex, owner) from plan section 7 (existing objects) plus what the stages themselves report
 (r'^Astra / varied planks|^Astra / Planked run controls', 'shapes'), (r'^Bridge pier \d', 'shapes'), (r'^Veranda step', 'shapes'),
 (r'^Stone plinth$|^Hall posts$|^Hall beams$|^Hall plaster$|^Eave soffit$|^Hall roof$|^Shoji bars$', 'shapes'),
 (r'^(Back wall, left|Back wall, right|Right wall behind hall)( cap)?$', 'shapes'),
 (r'^Rock \d|^Gravel rock \d|^Pond edge stone \d|^Stepping stone \d|^Lantern (base|post|gallery|firebox|cap|finial|window glow)$', 'shapes'),
 (r'^Water basin$|^Basin water$|^Raked gravel court$', 'shapes'),
 (r'^Maple |^Pine |^Bamboo|^Fallen leaves$|^Lily pads$|^Lotus blossoms$|^Pond water$|^Astra / moss grouped bodies$|^Astra / Courtyard receiving ground$|^Astra / pebbles grouped bodies$', 'life'),
 (r'^Hills, |^Dark plain$|^Focus$|^Camera$|^Golden hour sun$|^Cool sky fill$|^Lantern light$|^Hall glow|^Shoji paper|^Open room back$', 'light'),
]
def owner(n):
    for rx, o in OWN:
        if re.search(rx, n): return o
    return '?'
print(f'===== {look}: start {S["counts"]} -> final {F["counts"]}')
so, fo = S['objects'], F['objects']
removed = [n for n in so if n not in fo]
added = [n for n in fo if n not in so]
print('objects removed:', removed)
print('objects added:', len(added), 'by garden_owner:', {k: sum(1 for n in added if fo[n].get('owner') == k) for k in set(fo[n].get('owner') for n in added)})
noowner = [n for n in added if not fo[n].get('owner')]
print('added with no garden_owner tag:', noowner)
norole = [n for n in added if fo[n]['type'] in ('MESH',) and not fo[n].get('role')]
print('added meshes with no garden_role tag:', norole)
chg = {}
for n in so:
    if n not in fo: continue
    a, b = so[n], fo[n]
    kinds = []
    if a.get('geom') != b.get('geom') or a.get('nverts') != b.get('nverts'): kinds.append('geometry')
    if a['loc'] != b['loc'] or a['rot'] != b['rot'] or a['scl'] != b['scl']: kinds.append('transform')
    if a['mods'] != b['mods'] or a['mod_names'] != b['mod_names']: kinds.append('modifiers')
    if a['slots'] != b['slots']: kinds.append('material slots')
    if (a['hide_render'], a['hide_viewport']) != (b['hide_render'], b['hide_viewport']): kinds.append('visibility')
    if a['collections'] != b['collections']: kinds.append('collections')
    if a['parent'] != b['parent']: kinds.append('parent')
    if a.get('smooth') != b.get('smooth') and 'geometry' not in kinds: kinds.append('shading')
    if kinds: chg[n] = kinds
print('existing objects changed:', len(chg), 'of', len(so))
byowner = {}
for n, k in chg.items(): byowner.setdefault(owner(n), []).append((n, k))
for o in ('shapes', 'life', 'light', '?'):
    items = byowner.get(o, [])
    kinds = {}
    for n, k in items:
        for x in k: kinds[x] = kinds.get(x, 0) + 1
    print(f'  owner {o:6}: {len(items):3} objects  {kinds}')
# violations: geometry/transform/modifier changes on objects that are not shapes/life (except light for hills) 
viol = []
for n, k in chg.items():
    o = owner(n)
    for x in k:
        if x in ('geometry', 'transform', 'modifiers', 'visibility', 'parent', 'shading'):
            ok = (o == 'shapes') or (o == 'life') or (o == 'light' and n.startswith(('Hills', 'Dark plain', 'Camera', 'Focus', 'Golden', 'Cool', 'Lantern light', 'Hall glow')))
            if not ok: viol.append((n, o, x))
print('geometry/transform/modifier changes on objects outside shapes/life/light:', viol)
print('  slot changes (surfaces stage allowed):', sum(1 for n, k in chg.items() if 'material slots' in k))
print('  unowned (?) objects with ANY change:', byowner.get('?', []))
# life objects that shapes owns, and vice versa, changed in geometry?
cross = [(n, owner(n)) for n, k in chg.items() if 'geometry' in k]
# materials
sm, fm = S['materials'], F['materials']
mchg = [n for n in sm if n in fm and sm[n]['sig'] != fm[n]['sig']]
mrem = [n for n in sm if n not in fm]
madd = [n for n in fm if n not in sm]
print(f'materials: start {len(sm)} final {len(fm)}; rebuilt/changed {len(mchg)}; removed {mrem}; added {len(madd)}')
print('  not rebuilt (same signature):', sorted(n for n in sm if n in fm and sm[n]['sig'] == fm[n]['sig']))
# materials changed that belong to non-surfaces stuff: check each changed material's users
users = {}
for n, e in fo.items():
    for s in e['slots']:
        if s: users.setdefault(s, set()).add(n)
mc_by_owner = {}
for m in mchg:
    us = users.get(m, set())
    ow = sorted(set(owner(u) if not fo[u].get('owner') else fo[u]['owner'] for u in us)) or ['(no users)']
    mc_by_owner.setdefault(','.join(ow), []).append(m)
for k, v in mc_by_owner.items(): print('   changed materials used by', k, ':', len(v), v[:6])
# lights / camera / world / render
for sec in ('lights', 'cameras', 'world'):
    d = {n: (S[sec].get(n), F[sec].get(n)) for n in set(S[sec]) | set(F[sec]) if S[sec].get(n) != F[sec].get(n)}
    print(sec, 'changed/added/removed:', {n: ('NEW' if v[0] is None else ('REMOVED' if v[1] is None else 'changed')) for n, v in d.items()})
rd = {k: (S['render'][k], F['render'][k]) for k in S['render'] if S['render'][k] != F['render'][k]}
print('render settings changed:', json.dumps(rd)[:900])
