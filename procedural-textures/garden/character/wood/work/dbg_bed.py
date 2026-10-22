import sys, os
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/wood')
import bpy, stage_wood, wood_bridge as wb, numpy as np
bed = stage_wood.make_bed_fn()
L = wb.layout(7, bed_fn=bed)
for p in L['sup']['posts']:
    print("POSTBED", p['kind'], p.get('bearer', {}) and (p['bearer'].get('kind'), p['bearer'].get('arm'), round(p['bearer'].get('s', -1), 2)), np.round(p['xy'], 2), "bed z", round(bed(*p['xy']), 3))
for a in L['arms']:
    # ground along the axis and lateral +-0.62 every 0.25 m
    for s in np.arange(0, a['L'] + 0.01, 0.4):
        c = a['A'] + a['d'] * s
        print("ARM", a['k'], round(s, 2), [round(bed(*(c + a['n'] * u)), 2) for u in (-0.9, -0.62, 0, 0.62, 0.9)])
