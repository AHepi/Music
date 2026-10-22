import bpy, re, statistics, json
dg = bpy.context.evaluated_depsgraph_get()
def stats(o):
    e = o.evaluated_get(dg); me = e.to_mesh()
    n = len(me.polygons); sm = sum(1 for p in me.polygons if p.use_smooth)
    areas = sorted(p.area for p in me.polygons)
    r = None
    if areas:
        q = lambda f: areas[int(f * (len(areas) - 1))]
        r = round(q(0.9) / max(q(0.1), 1e-9), 1)
    e.to_mesh_clear(); return n, sm, r
rows = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    n = o.name
    if re.match(r'^(Rock|Gravel rock|Pond edge stone|Stepping stone) \d+$', n) or n in ('Astra / Courtyard receiving ground', 'Raked gravel court', 'Gravel kerb', 'Fix / far hedge', 'Pine pads', 'Lantern cap', 'Lantern base', 'Basin stones'):
        rows[n] = stats(o)
grp = {}
for n, (c, s, r) in rows.items():
    k = re.sub(r' \d+$', '', n)
    g = grp.setdefault(k, [0, 0, []]); g[0] += c; g[1] += s; g[2].append(r)
for k, (c, s, r) in grp.items():
    print('FACET', k, 'faces', c, 'smooth-shaded %', round(100 * s / max(c, 1), 1), 'unequal-size ratio p90/p10 median', statistics.median([x for x in r if x]) if any(r) else None)
