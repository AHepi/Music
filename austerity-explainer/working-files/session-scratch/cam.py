import bpy
from mathutils import Vector
P = open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/campos.txt').read().split()
loc = Vector([float(x) for x in P[0:3]]); look = Vector([float(x) for x in P[3:6]])
cam = bpy.context.scene.camera; cam.location = loc
cam.rotation_euler = (look - loc).to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = float(P[6]) if len(P) > 6 else 35
result = 'ok'
