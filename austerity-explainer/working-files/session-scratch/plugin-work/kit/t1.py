import bpy, sys, numpy
print('PY', sys.version.split()[0], 'numpy', numpy.__version__)
print('BL', bpy.app.version_string)
try:
    import PIL; print('PIL yes')
except Exception as e: print('PIL no', e)
try:
    import cv2; print('cv2 yes')
except Exception as e: print('cv2 no')
sys.exit(3)
