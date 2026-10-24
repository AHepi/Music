import sys, json, os
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, place_kit as pk
import place_kit.checks.construction as C
src = open(C.__file__).read()
src = src.replace("    # ---- fold the parts back into their objects", "    global DEBUG_PARTS\n    DEBUG_PARTS = [(p.name, p.role, p.bmin.tolist(), p.bmax.tolist(), facts[i]) for i, p in enumerate(all_parts)]\n    # ---- fold the parts back into their objects")
exec(compile(src, C.__file__, 'exec'), C.__dict__)
settings = pk.read_settings('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/plan/place-settings.json')
res = C.check_construction(settings, owner='cottages_south')
bad = []
for name, role, lo, hi, f in C.DEBUG_PARTS:
    if not name.startswith('Cottage'):
        continue
    flags = []
    if f['floating']: flags.append('FLOAT gap=%s' % f['gap_mm'])
    if f['short_by_mm']: flags.append('short %s' % f['short_by_mm'])
    if f['coplanar_faces']: flags.append('coplanar %s' % f['coplanar_faces'])
    if f['inside_out']: flags.append('inside_out')
    if f['max_span_m'] and f['span_max_m'] > f['max_span_m']: flags.append('span %s>%s' % (f['span_max_m'], f['max_span_m']))
    if f['hung'] and not f['hang_allowed']: flags.append('HUNG')
    if False: flags.append('seat %s' % f['seat_error_m'])
    if f['opening_floor_gap_m'] is not None and f['opening_floor_gap_m'] > 0.3: flags.append('doorgap %s' % f['opening_floor_gap_m'])
    if f['rise_m'] is not None and not (0.12 <= f['rise_m'] <= 0.2): flags.append('rise %s' % f['rise_m'])
    if flags:
        bad.append((name, role, [round(v, 3) for v in lo], [round(v, 3) for v in hi], flags))
for b in bad: print('DBG', b)
print('DBG total', len(bad))
