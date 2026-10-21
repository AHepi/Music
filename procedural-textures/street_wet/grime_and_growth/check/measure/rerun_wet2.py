# Checker: the kit's wet-look measure (P2) on my own redrawn PNG pictures: kit against base, both mine.
import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_wet
H=os.path.dirname(os.path.abspath(__file__))
W='proc-work/street_wet/grime_and_growth/integrated/work/'
S=mc.load_set('pit_village_street')
scene=sys.argv[1]
masks=W+'r1/base/'+scene
b=measure_wet.run(S,[H+'/redraw/'+scene+'_base',masks])
k=measure_wet.run(S,[H+'/redraw/'+scene,masks],b)
ok,fails=measure_wet.judge(k,b)
n_el=sum(1 for f in fails if f.startswith('element'))
print(scene,'P2 judge ok',ok,'failures',len(fails),'of which element lines',n_el)
for f in fails:
    if not f.startswith('element'): print('   ',f)
print('wet/dry road/pavement/walls base -> kit:')
for n in b['wet_to_dry']:
    if n in k['wet_to_dry']:
        r=lambda c:'%.3f->%.3f (%+.3f)'%(b['wet_to_dry'][n][c],k['wet_to_dry'][n][c],k['wet_to_dry'][n][c]-b['wet_to_dry'][n][c])
        print('  %-16s road %s | pave %s | walls %s'%(n,r('road'),r('pavement'),r('walls')))
print('puddle cover base vs kit', {n:(b['puddle_cover'].get(n),k['puddle_cover'].get(n)) for n in k['puddle_cover']})
print('speckle', b['speckle'], k['speckle'])
print('element lines above 1.0:', sorted((x,v) for x,v in k['element_wet_dry'].items() if v>1.0)[:5], '... count', n_el, 'of', len(k['element_wet_dry']))
json.dump(dict(base=b,kit=k,fails=fails),open(H+f'/wet2_{scene}.json','w'),indent=0,default=str)
