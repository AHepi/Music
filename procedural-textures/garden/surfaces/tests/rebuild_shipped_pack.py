# Rebuilds the mask pack that ships inside ./kit from the STARTING file (so a stand-alone run on the starting file finds a pack that matches it).
import sys, json
sys.path.insert(0, 'proc-work/garden/surfaces')
import weathering_stage as ws
d, lamp = ws.sun_direction()
print('REBUILD', lamp, d, ws.rebuild_masks(d), 's')
