# P6 on the plant lists of the final plates: no plant on the crown, the lanes, the doorstep strips, within 1 m of the fire, and none within 5 cm of a litter piece. Also counts plants inside puddles of the
# stamped pack (above_water) and the number of plants per kind.   python3 -I p6.py ROUND_DIR
import json, os, sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.path.insert(0, KIT + '/harness'); sys.dont_write_bytecode = True
import measure_common as mc, measure_zones as mz
rd = os.path.abspath(sys.argv[1])
out = {}
for scene, names in (('street', ['final_main_A_wet_kit']), ('lockout', ['final_lockout_B_wet_kit'])):
    folder = os.path.join(rd, 'plates', scene)
    if not os.path.isdir(folder):
        continue
    gp, manifest = mz.read_gp('pit_village_street', scene)
    out.setdefault('fields', {})[scene] = mz.fields_test(gp)
    for n in names:
        pf = os.path.join(folder, f'pieces_{n}.json')
        if not os.path.exists(pf):
            continue
        d = json.load(open(pf)); rows = d['pieces']; fire = [tuple(p) for p in d.get('fire_points', [])]
        rub = json.load(open(os.path.join(folder, f'rubbish_{n}.json')))
        r = mz.pieces_test(gp, manifest, rows, fire, rub)
        from collections import Counter
        out[n] = dict(count=d['count'], kinds=dict(Counter(x['kind'] for x in rows)), result=r)
json.dump(out, open(os.path.join(rd, 'p6_fix.json'), 'w'), indent=1, default=str)
for k, v in out.items():
    print(k, json.dumps(v, default=str)[:700])
