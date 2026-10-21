# What this does (plain words): inside Blender (street copy open), puts on the layers, lays the separate rubbish pieces with two sets of dials (the round 1 settings and the round 2 defaults), counts the pieces
# by kind and by where they lie across the street (road middle, outer road strip, gutter and kerb, pavement, foot of the wall) between 0 and 45 m along the street, and writes a JSON file.
# Run: blender -b --disable-autoexec street.blend --python count_pieces_by_zone.py -- OUT_JSON
import json, os, sys, time
import bpy
HERE = 'proc-work/street_wet/painter_round_2/plate'
sys.path.insert(0, 'proc-work/street_wet/tools'); sys.path.insert(0, HERE + '/rubbish/tools'); sys.path.insert(0, HERE + '/setts/tools'); sys.path.insert(0, HERE + '/study/tools')
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw, apply_joints_to_set as aj, apply_rubbish_to_set as ar, rubbish_pieces as rp
out = sys.argv[sys.argv.index('--') + 1]
aw.apply(wetness=0.85, puddles=0.5); aj.apply(); ar.apply(places='street')
ar.set_state(0.85)
ZONES = [('road middle |x| < 1.3', 0, 1.3), ('road outer strip 1.3 - 2.2', 1.3, 2.2), ('gutter and kerb foot 2.2 - 2.75', 2.2, 2.75), ('pavement near the kerb 2.75 - 3.05', 2.75, 3.05), ('pavement middle 3.05 - 3.5', 3.05, 3.5), ('wall foot 3.5 - 4.4', 3.5, 4.4)]
def kind_of(name):
    for k in ('cinder', 'clinker', 'china', 'stick', 'coal', 'ash_heap', 'paper', 'clump', 'speck', 'leaf', 'straw'):
        if name.startswith(k):
            return k
    return 'other'
SETS = {'round1_dials': dict(amount=1.0, patchiness=0.55, pieces_gather=0.0, wall_width=0.75), 'round2_defaults': dict(amount=1.4, patchiness=0.7, pieces_gather=1.0, wall_width=0.6)}
result = {}
for label, dials in SETS.items():
    ar.set_dials(**dials)
    ar.pieces(True)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    counts = {}
    total = 0
    for inst in dg.object_instances:
        if not inst.is_instance or not inst.parent or inst.parent.name != 'rubbish_scatter':
            continue
        p = inst.matrix_world.translation
        if not (0.0 <= p.y <= 45.0):
            continue
        total += 1
        zone = next((z for z, lo, hi in ZONES if lo <= abs(p.x) < hi), 'beyond 4.4')
        k = kind_of(inst.object.name)
        counts.setdefault(zone, {}).setdefault(k, 0)
        counts[zone][k] += 1
    result[label] = dict(total=total, dials=dials, zones=counts)
    print(label, total, flush=True)
json.dump(result, open(out, 'w'), indent=1)
