# work script: draws the picture jobs for the showcase pictures (close views, base against kit) and the plan views, on the rented machine. python3 -I pics_jobs.py TAG
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rr
KIT_ALL = 'kit:dirt,groundcracks,groundmoss,iron'
def j(name, cam, look, size=(960, 720, 16), light='A', state='wet', **kw):
    return rr.job(name, cam, look, light=light, state=state, size=size, **kw)
tag = sys.argv[1]
street = []
def trio(cam, looks):
    for lk in looks:
        street.append(j(f'{cam}__{lk.replace(":", "_").replace(",", "-")[:24]}', cam, lk))
trio('flag_close', ['base', 'solo:groundcracks', KIT_ALL])
trio('gutter_close', ['base', 'solo:dirt', 'solo:groundmoss', 'solo:groundcracks', KIT_ALL])
trio('pipe_close', ['base', 'solo:dirt', 'solo:groundmoss', 'solo:iron', KIT_ALL])
trio('close_road', ['base', 'solo:dirt', 'solo:groundcracks', KIT_ALL])
trio('doorstep_close', ['base', 'solo:dirt', KIT_ALL])
trio('wall_lamp', ['base', 'solo:iron', KIT_ALL])
trio('wall_close', ['base', KIT_ALL])
t = time.time()
rr.run(tag + '_street', street, scene='street')
lock = []
for lk in ['base', 'solo:iron', 'solo:dirt', KIT_ALL]:
    lock.append(j(f'drum_close__{lk.replace(":", "_").replace(",", "-")[:24]}', 'drum_close', lk, light='B'))
rr.run(tag + '_lockout', lock, scene='lockout')
print('PICS DONE', round(time.time() - t, 1), flush=True)
