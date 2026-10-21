import sys, json
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT)
from harness import remote
F = 'proc-work/street_wet/grime_and_growth/foundation'
which = sys.argv[1]; size = sys.argv[2]; tests = sys.argv[3]
blends = {'street': 'proc-work/street_wet/set_copy/street.blend',
          'lockout': '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend',
          'courtyard': 'scratchpad/astra-work/out/courtyard_final.blend'}
sets = {'street': 'pit_village_street', 'lockout': 'pit_village_street', 'courtyard': 'japanese_courtyard'}
res = remote.run_script(blends[which], KIT + '/harness/run_selftests.py', [sets[which], which, '{out}', tests, size], F + f'/work/remote_out/self_{which}_{size}', F + f'/work/out_self_{which}_{size}')
print(json.dumps(res))
