import sys
sys.path.append('/usr/local/lib/python3.13/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')
import numpy
print('NUMPY', numpy.__version__, numpy.__file__)
try:
    import cv2; print('CV2', cv2.__version__, cv2.__file__)
    import numpy as np
    a = np.zeros((50,50), np.uint8); a[25,25]=1
    d = cv2.distanceTransform((1-a).astype(np.uint8), cv2.DIST_L2, 5); print('DT ok', d.max())
    print('BLUR ok', cv2.GaussianBlur(np.random.rand(40,40).astype(np.float32),(5,5),1.0).shape)
except Exception as e: print('NOCV2', repr(e))
