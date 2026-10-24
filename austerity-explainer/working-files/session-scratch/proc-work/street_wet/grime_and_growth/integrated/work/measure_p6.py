# Integrator: P6 (no plants on the crown, lanes, doorstep strips, near the fire) on the plant lists of a round.   python3 -I measure_p6.py ROUND_DIR [kit]
import json, os, sys
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.path.insert(0, KIT + '/harness')
import measure_common as mc, measure_zones as mz
rd = os.path.abspath(sys.argv[1]); kit = sys.argv[2] if len(sys.argv) > 2 else 'kit'
settings = mc.load_set('pit_village_street')
out = {}
for scene, names in (('street', ['plate_main_A_wet', 'plate_notice_A_wet', 'plate_close_road_A_wet']), ('lockout', ['plate_lockout_B_wet'])):
    gp, manifest = mz.read_gp('pit_village_street', scene)
    out.setdefault('fields', {})[scene] = mz.fields_test(gp)
    for n in names:
        pf = os.path.join(rd, kit, scene, f'pieces_{n}.json')
        if not os.path.exists(pf):
            continue
        d = json.load(open(pf)); rows = d['pieces']; fire = [tuple(p) for p in d.get('fire_points', [])]
        rub = json.load(open(os.path.join(rd, kit, scene, f'rubbish_{n}.json')))
        r = mz.pieces_test(gp, manifest, rows, fire, rub)
        out[n] = dict(count=d['count'], result=r)
    mk = mz.marks_test(settings, os.path.join(rd, kit, scene), json.load(open(os.path.join(KIT, 'presets', 'sooty_1926.json'))))
    out.setdefault('marks', {})[scene] = mk
json.dump(out, open(os.path.join(rd, f'p6_{kit}.json'), 'w'), indent=1, default=str)
for k, v in out.items():
    print(k, json.dumps(v, default=str)[:600])
