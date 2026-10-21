import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_joints
settings=mc.load_set('pit_village_street')
kit='/workspace/wk_out/chk3_street'; masks='/workspace/wk_out/chk3_masks_street'
res=measure_joints.run(settings,[kit,masks])
s=res['summary']
out=dict(summary=s,pictures={n:dict(official=e['official']['passed'],all=e['all_dots']['passed'],wo=e['without_kit']['passed'],near=e['official']['near'],middle=e['official']['middle'],kit_share=e['official'].get('kit_share'),puddle=e['official'].get('puddle_share'),reasons=e['official']['reasons']) for n,e in res['pictures'].items() if 'official' in e})
json.dump(out,open('/workspace/wk_out/chk3_joints_street.json','w'),default=str,indent=0)
print('official',s['official'],'| all',s['all_dots'],'| without kit',s['without_kit'],'| maxnear',s['max_near_contrast'],'harsh',s['harsh_grid'])
