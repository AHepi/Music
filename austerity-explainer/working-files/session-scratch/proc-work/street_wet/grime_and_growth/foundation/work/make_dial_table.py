# One-off: turns the design helper's dial list (design/work/make_dials.py, read only) into the kit's data file apply/dial_table.json
import importlib.util, json, re, sys
spec = importlib.util.spec_from_file_location('make_dials', '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/design/work/make_dials.py')
md = importlib.util.module_from_spec(spec); spec.loader.exec_module(md)
def parse_range(text):
    m = re.match(r'\s*(-?[\d.]+)\s+to\s+(-?[\d.]+)\s*(.*)$', text)
    return float(m.group(1)), float(m.group(2)), m.group(3).strip()
def row(r):
    short, rng, kit, sooty, court, meaning = r
    lo, hi, unit = parse_range(rng)
    return dict(name=short, lo=lo, hi=hi, unit=unit, default=kit, doc=meaning)
out = {'schema': 'weathering-dials/1', 'note': 'Generated from the design helper\'s list (design/work/make_dials.py). Builders may add finer dials with dials.register_layer().',
       'common': [row(r) for r in md.COMMON], 'layers': {}}
for owner, key, group, prio, roles, masks, rows in md.LAYERS:
    out['layers'][key] = dict(owner=owner, group=group, priority=prio, roles=roles, masks=masks, dials=[row(r) for r in rows])
json.dump(out, open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/apply/dial_table.json', 'w'), indent=1)
print(len(out['layers']), 'layers', sum(len(v['dials']) for v in out['layers'].values()), 'rows')
