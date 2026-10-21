# Integrator step 2a: move the builders' sidecar sections into the set files and the walls builder's tuned values into the look. Plain data moves, no code changes.
import json, os
KIT = 'proc-work/kits/weathering'
def load(p): return json.load(open(os.path.join(KIT, p)))
def save(p, d): open(os.path.join(KIT, p), 'w').write(json.dumps(d, indent=1, ensure_ascii=False))
log = []
# ---- street set
s = load('sets/pit_village_street.json')
s['legacy']['pinned_root'] = 'integrate/legacy_round2/earlier'
s['legacy']['_pinned_note'] = 'which pinned copy of the earlier layers is put on: the second painter round\'s (rubbish and joints fixed). The first set (integrate/legacy_pinned/earlier) is the frozen baseline\'s; WK_LEGACY_PINNED in the environment overrides for one-off comparisons.'
g = load('ground/ground_sets/pit_village_street.json'); s['ground'] = g; log.append('street.ground <- ground_sets/pit_village_street.json')
w = load('growth/growth_sets/pit_village_street.json'); s['growth'] = w; log.append('street.growth <- growth_sets/pit_village_street.json')
rd = s['apply']['soot']['role_dials']
rd.pop('chimney', None); rd.pop('roof.slate', None)     # the soot layer has the class dials stack_mult and roof_mult instead (walls REQUESTS C)
rd['wall.trim'] = {'film_mult': 1.4, 'sheltered_mult': 1.75}
rd['wall.industrial'] = {'film_mult': 1.4}
log.append('apply.soot.role_dials: trims 1.4 / 1.75, industrial 1.4, chimney and roof entries removed (class dials)')
save('sets/pit_village_street.json', s)
# ---- courtyard set
c = load('sets/japanese_courtyard.json')
c['ground'] = load('ground/ground_sets/japanese_courtyard.json'); c['growth'] = load('growth/growth_sets/japanese_courtyard.json')
log.append('courtyard.ground, courtyard.growth moved in')
save('sets/japanese_courtyard.json', c)
# ---- looks
p = load('presets/sooty_1926.json')
L = p['layers']
tuned = {
 'soot': dict(film_mult=0.6, washed_share=0.17, washed_pale=0.8, edge_sharp=0.85, mottle_stretch=3.0, stack_mult=0.8, roof_mult=0.8, shade_wash=0.2, inflate_limit=8.0, grey_pull=0.25, mortar_soot=0.4, sheltered_mult=0.5, washed_mult=1.0),
 'runoff': dict(strength=1.0, stain_value=0.9, inflate_limit=12.0, source_share=0.8, pair_share=0.8),
 'foot': dict(splash_strength=0.9, splash_pale=0.9, salt_bloom=0.02, inflate_limit=8.0),
 'wallgrowth': dict(moss_amount=0.05, moss_value=0.2, saturation=0.5, algae_amount=0.6, algae_strength=0.4, inflate_limit=8.0),
 'wallcracks': dict(crack_amount=0.5, corner_chips=0.5, inflate_limit=8.0),
 'growth': dict(piece_inflate_limit=3.0, colour_gain=1.0),
}
for layer, vals in tuned.items():
    for k, v in vals.items():
        L[layer][k] = v
    log.append(f'sooty_1926.{layer}: ' + ', '.join(f'{k}={v}' for k, v in vals.items()))
save('presets/sooty_1926.json', p)
for name in ('mossy_courtyard_kept', 'mossy_courtyard_neglected'):
    q = load(f'presets/{name}.json')
    q['layers']['growth'].update(piece_inflate_limit=3.0, colour_gain=0.15, colour_sat=1.2, existing_avoid=0.7)
    save(f'presets/{name}.json', q)
    log.append(f'{name}.growth: colour_gain 0.15, colour_sat 1.2, existing_avoid 0.7, piece_inflate_limit 3')
print('\n'.join(log))
