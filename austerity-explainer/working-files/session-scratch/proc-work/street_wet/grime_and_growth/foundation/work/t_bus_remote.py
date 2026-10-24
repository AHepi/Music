import sys, json
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
from harness import remote
F = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/foundation'
which = sys.argv[1]; tests = sys.argv[2]
blends = {'street': '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/set_copy/street.blend',
          'lockout': '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend',
          'courtyard': '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work/out/courtyard_final.blend'}
sets = {'street': 'pit_village_street', 'lockout': 'pit_village_street', 'courtyard': 'japanese_courtyard'}
res = remote.run_script(blends[which], KIT + '/harness/run_bus_tests.py', [sets[which], which, '{out}', tests], F + f'/work/remote_out/bus_{which}', F + f'/work/out_bus_{which}')
print(json.dumps(res))
d = json.load(open(F + f'/work/out_bus_{which}/bus_tests_{which}.json'))
for k, v in d['results'].items():
    print(k, v.get('passed'), {kk: vv for kk, vv in v.items() if kk in ('worst','error','worst_error_vs_arithmetic','worst_error_vs_table','found','note')})
    if k=='ground': print('   per mask', v.get('per_mask'))
    if k=='dots': print('   rows', json.dumps(v.get('rows')), v.get('debug'))
    if k=='walls': print('   walls', json.dumps(v.get('per_sheet'))[:1500])
