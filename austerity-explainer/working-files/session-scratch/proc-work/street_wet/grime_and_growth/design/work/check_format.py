import json, re, sys
base='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/'
S=json.load(open(base+'sets/pit_village_street.json')); C=json.load(open(base+'sets/japanese_courtyard.json'))
ks, kc = set(S), set(C)
print('only street:', sorted(ks-kc)); print('only courtyard:', sorted(kc-ks))
# every regex compiles
def walk(o, path=''):
    if isinstance(o, dict):
        for k,v in o.items(): yield from walk(v, path+'/'+k)
    elif isinstance(o, list):
        for i,v in enumerate(o): yield from walk(v, path+'/%d'%i)
    else: yield path, o
bad=0
for name,d in (('street',S),('courtyard',C)):
    for p,v in walk(d):
        if isinstance(v,str) and v.startswith('^') :
            try: re.compile(v)
            except Exception as e: print('BAD REGEX', name, p, v, e); bad+=1
print('bad regexes', bad)
# apply layers all exist in presets
P=json.load(open(base+'presets/sooty_1926.json'))
for name,d in (('street',S),('courtyard',C)):
    miss=[k for k in d['apply'] if not k.startswith('_') and k not in P['layers']]
    print(name,'apply keys not in a look:', miss)
# street objects: do the regexes match the real names?
names=[l.split()[0] for l in open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/work/objects_street.txt') if l.strip()]
for role,spec in S['roles'].items():
    if role.startswith('_'): continue
    pats=spec.get('objects',[])
    n=sum(1 for nm in names if any(re.match(p,nm) for p in pats))
    print(f'{role:18s} objects matched in street list: {n}')
