import bpy, sys, os, time
sys.dont_write_bytecode=True
t=time.time()
bpy.ops.wm.open_mainfile(filepath="/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/direction/start/garden_real_fixed.blend")
print("PROBE objects",len(bpy.data.objects),"materials",len(bpy.data.materials),"open seconds",round(time.time()-t,1))
print("PROBE hero camera",bpy.data.objects['photo'].location[:],"veranda",bpy.data.objects['veranda'].location[:])
sys.path.insert(0,"/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/direction/shared")
import numpy
print("PROBE numpy",numpy.__version__)
import normal_tools
r=normal_tools.check_direction(verbose=False)
print("PROBE",r['line'])
