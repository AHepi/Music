# Checker: wet-over-dry brightness of road, pavement and walls, before (base) and after (kit), from the saved JPGs and class pictures.
import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT+'/harness'); sys.path.insert(0,KIT); sys.dont_write_bytecode=True
import numpy as np, measure_common as mc
W='proc-work/street_wet/grime_and_growth/integrated/work/'
S=mc.load_set('pit_village_street'); cls=mc.classes(S)
rows=[]
for scene,(label_list) in (('street',['main','close']),('lockout',['lockout'])):
    for label in label_list:
        for light in 'ACDE':
            try: w,h=mc.size_of(S,label)
            except Exception: continue
            cam=mc.camera_of(S,label)
            cp=W+f'r1/base/{scene}/class_{cam}_{w}x{h}.png'
            if not os.path.exists(cp): continue
            cm=mc.read_class(cp)
            for kind in ('base','kit'):
                folder=W+('r1/base/' if kind=='base' else 'r5/kit/')+scene
                pass
            def L(kind,state):
                folder=W+('r1/base/' if kind=='base' else 'r5/kit/')+scene
                p=mc.pic(folder,f'{label}_{light}_{state}')
                return mc.read_lum(p) if p else None
            for state in ('wet','heavy'):
                d={}
                ok=True
                for kind in ('base','kit'):
                    Lw=L(kind,state); Ld=L(kind,'dry')
                    if Lw is None or Ld is None: ok=False; break
                    for c in ('road','pavement','walls'):
                        m=mc.class_mask(cm,cls[c])
                        d[(kind,c)]=Lw[m].mean()/Ld[m].mean()
                if not ok: continue
                row=dict(pic=f'{label}_{light}_{state}')
                for c in ('road','pavement','walls'):
                    row[c]=(round(d[('base',c)],3),round(d[('kit',c)],3),round(d[('kit',c)]-d[('base',c)],3))
                rows.append(row)
bad=0
for r in rows:
    flag=[c for c in ('road','pavement','walls') if abs(r[c][2])>0.05]
    bad+=len(flag)>0
    print('%-18s road base %.3f kit %.3f (%+.3f) | pave %.3f %.3f (%+.3f) | walls %.3f %.3f (%+.3f) %s'%((r['pic'],)+r['road']+r['pavement']+r['walls']+('<-- over 0.05: '+','.join(flag) if flag else '',)))
print(len(rows),'pairs;',bad,'with a class off by more than 0.05')
json.dump(rows,open('wet_rerun.json','w'),indent=0)
