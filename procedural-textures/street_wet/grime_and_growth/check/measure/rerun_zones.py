# Checker: independent look at where plants stand relative to the crown, wheel lanes and keep-clear pictures of the pack, from the saved plant lists.
import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import numpy as np, measure_common as mc, measure_zones as mz
W='proc-work/street_wet/grime_and_growth/integrated/work/r5/kit/'
out={}
for scene,names in (('street',['plate_main_A_wet','plate_notice_A_wet','plate_close_road_A_wet']),('lockout',['plate_lockout_B_wet'])):
    gp,man=mz.read_gp('pit_village_street',scene)
    print(scene,'gp masks:',sorted(gp)[:40])
    # field check, own version: max of moss_site and weed_site wherever the zones say so
    fo,cr,kc=gp['footfall'],gp['crown'],gp['keepclear']
    zone=(fo>=0.6)|(cr>=0.7)|(kc>=0.5)
    ground=np.ones_like(fo,bool)
    # ground area inside bounds that exists: use height picture non-null if present
    print('  zone share of the ground-plan grid: %.3f ; footfall>=0.6 %.3f crown>=0.7 %.3f keepclear>=0.5 %.3f'%(zone.mean(),(fo>=0.6).mean(),(cr>=0.7).mean(),(kc>=0.5).mean()))
    for f in ('moss_site','weed_site','algae_site','lichen_site'):
        if f in gp:
            v=gp[f]
            print('  %-11s max in zone %.4f ; mean outside zone %.3f ; share outside zone >0.05: %.3f'%(f,v[zone].max(),v[~zone].mean(),(v[~zone]>0.05).mean()))
    for n in names:
        d=json.load(open(W+scene+'/pieces_'+n+'.json'))
        rows=d['pieces']
        xs=np.array([p['x'] for p in rows]); ys=np.array([p['y'] for p in rows])
        vals=[]
        for p in rows:
            ix,iy=mz.to_cell(man,p['x'],p['y'])
            h,w=fo.shape
            if 0<=ix<w and 0<=iy<h: vals.append((fo[iy,ix],cr[iy,ix],kc[iy,ix]))
        v=np.array(vals)
        kinds={}
        for p in rows: kinds[p.get('kind')]=kinds.get(p.get('kind'),0)+1
        print(' ',n,'plants',len(rows),'| |x| percentiles 5/50/95: %.2f %.2f %.2f'%tuple(np.percentile(np.abs(xs),[5,50,95])),'| y range %.1f..%.1f'%(ys.min(),ys.max()))
        print('     footfall at plants: max %.3f mean %.3f ; crown max %.3f ; keepclear max %.3f ; share with footfall>0.3: %.3f ; >0.5: %.3f'%(v[:,0].max(),v[:,0].mean(),v[:,1].max(),v[:,2].max(),(v[:,0]>0.3).mean(),(v[:,0]>0.5).mean()))
        print('     kinds',kinds)
        out[n]=dict(plants=len(rows),footfall_max=float(v[:,0].max()),crown_max=float(v[:,1].max()),keepclear_max=float(v[:,2].max()),near_lane=float((v[:,0]>0.3).mean()))
        for k in ('pieces',):
            pass
json.dump(out,open('zones_rerun.json','w'),indent=0)
