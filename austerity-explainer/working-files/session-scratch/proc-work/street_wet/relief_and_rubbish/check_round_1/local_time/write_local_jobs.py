# What this file does (plain words): writes two small job files for a LOCAL timing and memory check on THIS machine (4 cores, 16 GB): the lockout plate at full size, 8 samples, once with the setts layer only (joints) and once with the rubbish too.
import sys, json
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/tools')
import write_jobs as wj
B = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/check_round_1/local_time/'
for look in ('joints', 'rubbish'):
    pics = [wj.pic('lockout', 'B', 'wet', look, size=(1536, 2730, 8), name=f'local_plate_lockout_B_wet_{look}', dirt=False)]
    import os
    os.makedirs(B + look, exist_ok=True)
    print(wj.write(B + look, 'lockout', pics, puddle_masks=False))
