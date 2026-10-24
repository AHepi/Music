import sys, json, os
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from growth import run_growth
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/growth/'
cams=[dict(name='spot_right',location=[1.0,10.0,1.05],look_at=[2.55,12.8,0.85],fov_v=42.0),dict(name='spot_left',location=[-1.0,6.0,0.62],look_at=[-2.5,9.0,0.25],fov_v=42.0)]
print(run_growth.run('pit_village_street','street',G+'spots_street','spots',extra=dict(cameras=cams)))
