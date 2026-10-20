# What this does (plain words): writes EVERY description of the wood ladder (the "rate-distortion" ladder: how much accuracy each extra layer / extra kilobyte buys):
#   S0  layout only                        (boards, gaps, long cracks, knots, splatter clouds, pebbles; flat colour per board)           under 8 KB
#   S1  S0 + invented paint (stamps) + grain                                                                                          under 8 KB
#   M1, M2, M3  traced patches, about 20, 40 and 62 KB                                                                                 under 64 KB
#   L1, L2, L3  traced patches, about 150, 300 and 480 KB                                                                              under 512 KB
# into ../description/, runs the description audit on each and prints sizes. The traced classes are the "tracing the picture" end (analysis read the reference).
# Plain Python (python3 -I). Run: python3 -I make_ladder.py
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import describe_tools as dt
import make_descriptions as md
DESC = os.path.join(HERE, '..', 'description')
palette, palette_lab = md.make_s_palette()
fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
cracks = json.load(open(os.path.join(HERE, 'cracks_fitted.json')))
model = json.load(open(os.path.join(HERE, 'paint_model.json')))
tuned = json.load(open(os.path.join(HERE, 'tuned_settings.json')))
stamp_model = {k: model[k] for k in ('classes', 'class_group', 'child_classes', 'zone', 'child')}
report = {}
SUFFIX = os.environ.get('LADDER_SUFFIX', '')
def audit(path, limit):
    r = subprocess.run(['python3', '-I', os.path.join(HERE, '..', '..', '..', 'lib', 'description_audit.py'), path, '--limit-kilobytes', str(limit)], capture_output=True, text=True)
    return json.loads(r.stdout)
# S0
d = md.base_description(palette, 'S0: layout only (plank rows with wave-form gaps, long cracks, knots, splatter clouds, pebbles); flat colour per board; no paint')
d['layers'] = md.layout_layers(fit, cracks, palette_lab, crack_count=25, cloud_count=30)
if not SUFFIX: md.write(d, os.path.join(DESC, 'S0_layout_only.json'))
# S1
d = md.base_description(palette, 'S1: S0 + invented paint (zones and strips from a fitted model) + fine dry-brush grain; invented paint of the measured kind, not the reference paint')
d['maps'] = dict(d['maps'], grain=tuned['grain'])
stamps = {'type': 'stamps', 'seed': 21, 'model': stamp_model, 'rate_scale': [tuned['rate']] * 8, 'zone_amp': tuned['zone_amp'], 'child_amp': tuned['child_amp'], 'paint_min_l': 16.0}
d['layers'] = md.layout_layers(fit, cracks, palette_lab, crack_count=20, cloud_count=25, with_stamps=stamps)
if not SUFFIX: md.write(d, os.path.join(DESC, 'S1_layout_paint_grain.json'))
# traced classes
bgr = dt.load_reference(); state = dt.load_merge_state(bgr, wrap=True)       # patches may join across the tile edge: no colour seam
for name, n, rule, pal in [('M1_trace_20k', 45, (2.5, 7.0, 0.55), 24), ('M2_trace_40k', 140, (2.5, 7.0, 0.55), 32), ('M3_trace_62k', 340, (2.5, 7.0, 0.55), 32),
                           ('L1_trace_150k', 900, (1.5, 5.0, 0.35), 48), ('L2_trace_300k', 1500, (0.9, 3.0, 0.2), 64), ('L3_trace_480k', 3500, (0.9, 3.0, 0.2), 96)]:
    regions, pal_rgb = dt.traced_regions(bgr, state, n, pal, rule)
    desc = dt.traced_description(regions, pal_rgb, f'{name}: traced flat patches (about {n}), outlines looser on fat patches (rule {rule}), {pal} colours')
    size = dt.write_description(desc, os.path.join(DESC, name + SUFFIX + '.json'))
    print(name, round(size / 1024, 1), 'KB', len(regions), 'patches', flush=True)
for name, limit in [('S0_layout_only', 8), ('S1_layout_paint_grain', 8), ('M1_trace_20k', 64), ('M2_trace_40k', 64), ('M3_trace_62k', 64), ('L1_trace_150k', 512), ('L2_trace_300k', 512), ('L3_trace_480k', 512)]:
    if SUFFIX and name[0] == 'S':
        continue
    a = audit(os.path.join(DESC, name + (SUFFIX if name[0] in 'ML' else '') + '.json'), limit)
    report[name] = {'bytes': a['bytes'], 'numbers': a['numbers'], 'problems': a['problems'], 'limit_kb': limit}
    print(name, a['bytes'], 'bytes, problems:', a['problems'])
json.dump(report, open(os.path.join(HERE, '..', 'scores', 'description_audits.json'), 'w'), indent=1)
