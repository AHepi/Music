import sys, types, json, numpy as np, cv2
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/paper-film/tools')
import check_shot
K='/home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/'
cases=[('notice',K+'notice-corner/notice-corner-shot-check.json','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/plate-facts-3'),
       ('people',K+'people-test/people-test-shot-check.json','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts')]
for name,chk,facts in cases:
    shot=check_shot.Shot(types.SimpleNamespace(check=chk,facts=facts,picture=None,out='/tmp',title='',render_log=None))
    W,H=shot.width,shot.height
    print('==',name, W,H, 'core',shot.core,'pairs_also',shot.check.get('pairs_also'))
    for g in shot.facts['groups']:
        a=shot.alone[g]; v=shot.visible[g]
        if not a.any(): print(' ',g,'no pixels'); continue
        thin_a=a&~check_shot.without_wires(a,W); thin_v=v&~check_shot.without_wires(v,W)
        print(f'  {g:16s} share {v.mean()*100:6.2f}%  dist {shot.info(g)["distance"]:6.1f}  thin(alone) {thin_a.sum()/max(1,a.sum()):.3f} thin(visible) {thin_v.sum()/max(1,v.sum()):.3f}')
print('--- intrinsic thin (thin in the whole prop, counted where it shows)')
for name,chk,facts in cases:
    shot=check_shot.Shot(types.SimpleNamespace(check=chk,facts=facts,picture=None,out='/tmp',title='',render_log=None))
    W=shot.width
    out=[]
    for g in shot.facts['groups']:
        a=shot.alone[g]; v=shot.visible[g]
        if not v.any(): continue
        t=v&a&~check_shot.without_wires(a,W)
        out.append(f'{g}:{t.sum()/v.sum():.3f}')
    print(name,' '.join(out))
