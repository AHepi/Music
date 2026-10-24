import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/ground')
from rr import *
items=['class']
for layer,parts in (('dirt',['film','polish','marks','halo','drum','tar','splash','scrub']),('groundcracks',['flag_fine','flag_broken','flag_tilt','flag_chip','kerb_chips','kerb_joints','kerb_scuffs','sett_disturbed','sett_joints']),('groundmoss',['joint_moss','patch_moss','algae','liverwort','far_band'])):
    items+= [f'{layer}:{p}' for p in parts]
plan('t3', items)
