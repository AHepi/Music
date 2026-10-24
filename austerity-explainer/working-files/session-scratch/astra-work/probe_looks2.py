# What this does: tries view transforms and looks by name in Blender 5.2.2 and prints which are accepted.
import bpy
v = bpy.context.scene.view_settings
for t in ('AgX', 'Filmic', 'Khronos PBR Neutral', 'Standard'):
    try: v.view_transform = t; print('TRANSFORM OK', t)
    except Exception as e: print('TRANSFORM NO', t)
v.view_transform = 'AgX'
for l in ('AgX - Punchy', 'Punchy', 'AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - High Contrast', 'High Contrast', 'AgX - Golden', 'Golden'):
    try: v.look = l; print('LOOK OK', l)
    except Exception as e: print('LOOK NO', l)
