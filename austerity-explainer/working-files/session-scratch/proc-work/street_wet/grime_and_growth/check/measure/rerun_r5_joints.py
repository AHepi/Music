import sys, json, os
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_joints
H=os.path.dirname(os.path.abspath(__file__))
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/integrated/work/'
S=mc.load_set('pit_village_street')
scenes=sys.argv[1:]
folders=[]
for sc in scenes: folders += [H+'/r5redo/kit/'+sc, W+'r1/base/'+sc]
res=measure_joints.run(S,folders)
base=json.load(open(W+'r1/base/base_measures.json'))['joints']
s=res['summary']
print('scenes',scenes)
print('REDRAWN kit: official',s['official']['passed'],'of',s['official']['of'],s['official']['failing'],'| all dots',s['all_dots']['passed'],s['all_dots']['failing'],'| kit dots left out too',s['without_kit']['passed'],s['without_kit']['failing'])
print('             max near contrast',s['max_near_contrast'],'harsh',s['harsh_grid'],'missing',s['missing'])
b=base['summary']
print('BASE (integrator, cached): official',b['official']['passed'],b['official']['failing'],'| all dots',b['all_dots']['passed'],b['all_dots']['failing'],'| without kit',b['without_kit']['passed'])
old=json.load(open(W+'r5/measures_kit.json'))['p1']
print('INTEGRATOR r5 saved: summary official',old['summary']['official']['passed'],old['summary']['official']['failing'],'all dots',old['summary']['all_dots']['passed'],old['summary']['all_dots']['failing'],'without kit',old['summary']['without_kit']['passed'],old['summary']['without_kit']['failing'])
for n,e in sorted(res['pictures'].items()):
    if 'official' in e:
        o=old['pictures'].get(n,{})
        print('  %-16s off %-5s (saved %-5s) all %-5s (saved %-5s) wo-kit %-5s (saved %-5s) kit share %.2f (saved %s)'%(n,e['official']['passed'],o.get('passed'),e['all_dots']['passed'],o.get('all_dots'),e['without_kit']['passed'],o.get('without_kit'),e['official']['kit_share'],o.get('kit_share')))
json.dump({n:dict(official=e['official']['passed'],all=e['all_dots']['passed'],wo=e['without_kit']['passed']) for n,e in res['pictures'].items() if 'official' in e},open(H+'/r5_joints_'+'_'.join(scenes)+'.json','w'))
