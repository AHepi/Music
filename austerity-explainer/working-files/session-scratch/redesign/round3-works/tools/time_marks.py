# Prints the time since Blender started, to find slow steps (run after the scene script).
import time, bpy
print('TIME-MARK end of scripts', round(time.time(), 1))
