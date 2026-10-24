import json
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
path = KIT + '/sets/japanese_courtyard.json'
s = json.load(open(path))
a = s['apply']
# role_dials of the walls layers are only read by the soot layer (film_mult, sheltered_mult): the ones I wrote for foot and wallgrowth do nothing, so they are taken out again
a['foot'].pop('role_dials', None)
a['wallgrowth'].pop('role_dials', None)
a['wallgrowth'].pop('role_dials_why', None)
a['foot']['_why'] = "round 1: stone.natural added (damp splash band at the foot of every stone)."
# trial: moss cushions on the roof tiles (the roof is the one thing the paint layers cannot reach, see the finding about the roof's materials)
if 'roof.tile' not in a['growth']['targets']:
    a['growth']['targets'].append('roof.tile')
if 'roof.tile' not in s['growth']['targets']['roles']:
    s['growth']['targets']['roles'].append('roof.tile')
json.dump(s, open(path, 'w'), indent=1)
