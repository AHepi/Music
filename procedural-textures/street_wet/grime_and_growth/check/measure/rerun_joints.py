# Checker: re-run the kit's joint measure on the integrator's round-5 pictures, from the saved files only.
import sys, json, os, time
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc, measure_joints
W='proc-work/street_wet/grime_and_growth/integrated/work/'
settings=mc.load_set('pit_village_street')
kit=[W+'r5/kit/street',W+'r5/kit/lockout']; base=[W+'r1/base/street',W+'r1/base/lockout']
t=time.time()
res=measure_joints.run(settings, kit+base)
cache=json.load(open(W+'r1/base/base_measures.json'))['joints']
print('seconds',round(time.time()-t))
print('KIT summary', json.dumps(res['summary'],default=str))
print('BASE (cached) summary', json.dumps(cache['summary'],default=str))
print('compare', json.dumps(measure_joints.compare_with_base(res,cache),default=str)[:600])
rows={}
for n,e in res['pictures'].items():
    if 'official' in e:
        rows[n]=dict(near=e['official']['near'],middle=e['official']['middle'],official=e['official']['passed'],all=e['all_dots']['passed'],wo=e['without_kit']['passed'],kit_share=e['official'].get('kit_share'))
json.dump(rows,open('joints_rerun.json','w'),indent=0,default=str)
for n,r in rows.items():
    print('%-22s off %-5s all %-5s wo_kit %-5s kit_share %s'%(n,r['official'],r['all'],r['wo'],r['kit_share']))
