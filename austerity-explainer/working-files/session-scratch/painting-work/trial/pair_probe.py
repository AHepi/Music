import sys, types, json, math, numpy as np, cv2
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/paper-film/tools')
import check_shot
exec(open('thin_probe.py').read().split('for name,chk,facts in cases:')[0].split('import check_shot')[1])
def signed(shot,a,b):
    W=shot.width
    sa,sb=check_shot.without_wires(shot.alone[a],W),check_shot.without_wires(shot.alone[b],W)
    both=sa&sb
    if both.any():
        showing=both&(shot.visible[a]|shot.visible[b])
        if showing.any():
            depth=float(max(check_shot.distance_inside(sa)[showing].max(),check_shot.distance_inside(sb)[showing].max()))
            return -depth
    va,vb=shot.visible[a],shot.visible[b]
    if not(va.any() and vb.any()): return None
    return float(np.where(vb,check_shot.distance_outside(va),np.inf).min())
for name,chk,facts in cases:
    shot=check_shot.Shot(types.SimpleNamespace(check=chk,facts=facts,picture=None,out='/tmp',title='',render_log=None))
    s=shot.width/1536; ov,gap=math.ceil(20*s),math.ceil(25*s)
    names=[g for g in dict.fromkeys(shot.core+shot.check.get('pairs_also',[])) if shot.visible[g].any()]
    print('==',name,'band',-2*ov,2*gap)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            d=signed(shot,a,b)
            if d is None: continue
            if -2*ov<d<2*gap: print(f'   {a} / {b}: {d:.1f}')
