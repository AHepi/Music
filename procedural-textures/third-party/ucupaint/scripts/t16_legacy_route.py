"""Plain note: our own test. Tries the OLD way of installing an add-on (a folder in the user 'scripts/addons' folder instead of the new
'extensions' system) to see if Blender 5.2.2 still loads Ucupaint that way."""
import bpy, addon_utils
print('legacy addon paths:', addon_utils.paths())
mods = [m.__name__ for m in addon_utils.modules()]
print('ucupaint-like modules found:', [m for m in mods if 'ucupaint' in m])
try:
    m = addon_utils.enable('ucupaint', default_set=True, persistent=False)
    print('enable result:', m)
    print('operators:', len([n for n in dir(bpy.ops.wm) if n.startswith('y_')]))
except Exception as e:
    print('ENABLE FAILED', repr(e))
