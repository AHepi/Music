# What this does (plain words): prints, for a baked picture, how much more or less picture energy it has than the reference at each feature size
# (the radial spectrum texture_compare uses), so that a wear layer can be turned up or down at the right size. Use: python3 -I spectrum_diff.py FOLDER ...
import sys,cv2,numpy as np
sys.path.insert(0,'proc-work/lib')
import texture_compare as tc
def spec(path):
    im=cv2.imread(path); lab=cv2.cvtColor(im,cv2.COLOR_BGR2LAB)[...,0].astype(np.float64)
    if im.shape[0]!=1254: lab=cv2.resize(lab,(1254,1254))
    return tc.radial_log_spectrum(lab)
ref=spec('proc-work/reference/metal/colour.png')
np.set_printoptions(linewidth=220,precision=2,suppress=True)
print('feature size (dots) ',np.geomspace(3,626,31)[:30].round(0))
for n in sys.argv[1:]:
    print(n.split('/')[-1].ljust(10),(spec(n+'/colour.png')-ref))
