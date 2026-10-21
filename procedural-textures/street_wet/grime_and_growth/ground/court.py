# work script: courtyard reuse pictures: python3 -I court.py TAG   (the scene file must already be on the machine: st.py --upload sends it)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rr
tag = sys.argv[1]
jobs = []
for lk in ['base', 'kit:dirt,groundmoss', 'solo:groundmoss', 'solo:dirt']:
    jobs.append(rr.job('photo__' + lk.replace(':', '_').replace(',', '-'), 'photo', lk, light='A', state='dry', size=(1200, 800, 16)))
rr.run(tag, jobs, scene='courtyard', set_id='japanese_courtyard')
