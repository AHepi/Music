import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_joints
H=os.path.dirname(os.path.abspath(__file__))
W='proc-work/street_wet/grime_and_growth/integrated/work/'
settings=mc.load_set('pit_village_street')
out={}
for scene in sys.argv[1:]:
    kit=H+'/redraw/'+scene; base=H+'/../measure/redraw/'+scene+'_base'; masks=W+'r1/base/'+scene
    for tag,folders in (('kit',[kit,masks]),('base',[base,masks])):
        res=measure_joints.run(settings,folders)
        s=res['summary']
        out.setdefault(scene,{})[tag]=dict(summary=s,pictures={n:dict(official=e['official']['passed'],all=e['all_dots']['passed'],wo=e['without_kit']['passed'],near=e['official']['near'],middle=e['official']['middle'],kit_share=e['official'].get('kit_share')) for n,e in res['pictures'].items() if 'official' in e})
        print(scene,tag,'official',s['official']['passed'],'/',s['official']['of'],s['official']['failing'],'| all dots',s['all_dots']['passed'],s['all_dots']['failing'],'| without kit dots',s['without_kit']['passed'],s['without_kit']['failing'],'| max near contrast',s['max_near_contrast'],'| harsh',s['harsh_grid'],'| missing',s['missing'])
json.dump(out,open(H+'/joints_'+'_'.join(sys.argv[1:])+'.json','w'),indent=0,default=str)
