import sys
print('PY', sys.version)
try:
    import cv2; print('CV2', cv2.__version__)
except Exception as e: print('NOCV2', e)
try:
    import numpy; print('NUMPY', numpy.__version__)
except Exception as e: print('NONUMPY', e)
try:
    import scipy; print('SCIPY')
except Exception as e: print('NOSCIPY')
try:
    import PIL; print('PIL')
except Exception as e: print('NOPIL')
