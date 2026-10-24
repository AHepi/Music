# Rebuilds the mask pack that ships inside ./kit from the STARTING file (so a stand-alone run on the starting file finds a pack that matches it).
import sys, json
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces')
import weathering_stage as ws
d, lamp = ws.sun_direction()
print('REBUILD', lamp, d, ws.rebuild_masks(d), 's')
