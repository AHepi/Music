# Checker: the kit's joint measure on my own redrawn pictures (PNG), kit pictures against base pictures, masks from the integrator's base folder.
import sys, json, os, time
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_joints
H=os.path.dirname(os.path.abspath(__file__))
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/integrated/work/'
settings=mc.load_set('pit_village_street')
scenes=sys.argv[1:]
out={}
for scene in scenes:
    kit=H+'/redraw/'+scene; base=H+'/redraw/'+scene+'_base'; masks=W+'r1/base/'+scene
    for tag,folders in (('kit',[kit,masks]),('base',[base,masks])):
        res=measure_joints.run(settings,folders)
        res_s={k:v for k,v in res['summary'].items()}
        # keep only this scene's pictures
        out.setdefault(scene,{})[tag]=dict(summary=res_s,pictures={n:dict(official=e['official']['passed'],all=e['all_dots']['passed'],wo=e['without_kit']['passed'],near=e['official']['near'],middle=e['official']['middle'],kit_share=e['official'].get('kit_share')) for n,e in res['pictures'].items() if 'official' in e})
        s=res['summary']
        print(scene,tag,'official',s['official']['passed'],'/',s['official']['of'],s['official']['failing'],'| all dots',s['all_dots']['passed'],s['all_dots']['failing'],'| without kit dots',s['without_kit']['passed'],s['without_kit']['failing'],'| max near contrast',s['max_near_contrast'],'| harsh',s['harsh_grid'],'| missing',len(s['missing']))
json.dump(out,open(H+'/joints_rerun_'+'_'.join(scenes)+'.json','w'),indent=0,default=str)
