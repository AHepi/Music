import numpy as np
from PIL import Image
import cv2
class ndi:
  @staticmethod
  def binary_dilation(m,iterations=1): return cv2.dilate(m.astype(np.uint8),np.ones((3,3),np.uint8),iterations=iterations)>0
  @staticmethod
  def binary_erosion(m,iterations=1): return cv2.erode(m.astype(np.uint8),np.ones((3,3),np.uint8),iterations=iterations)>0
  @staticmethod
  def binary_opening(m,iterations=1): return ndi.binary_dilation(ndi.binary_erosion(m,iterations),iterations)
  @staticmethod
  def label(m):
    k,lab=cv2.connectedComponents(m.astype(np.uint8)); return lab,k-1
  @staticmethod
  def sum(m,lab,idx): return np.bincount(lab.ravel(),weights=m.ravel().astype(float),minlength=max(idx)+1)[list(idx)]

P='/home/user/work/paper-pop-up-film-kit/assets/reliefs/'
L=lambda f: np.asarray(Image.open(f).convert('RGB'),float)
paint=np.asarray(Image.open(P+'inflation-chapter-2/409-bg-petrol-station-1973.jpg').convert('RGB').resize((1080,1920),Image.LANCZOS),float)
clean=np.asarray(Image.open(P+'sam-3d-test/409-petrol-station-clean.jpg').convert('RGB').resize((1080,1920),Image.LANCZOS),float)
A=L('render-a/original/still-190.00.jpg'); F=L('render-f/painting/still-190.00.jpg')
masks=[np.asarray(Image.open(P+f'sam-3d-test/mask-{i}.png').resize((1080,1920),Image.BILINEAR))>127 for i in range(1,6)]
allm=np.any(masks,0)
outside=~ndi.binary_dilation(allm,iterations=40)
print('outside-mask mean |F-A|', np.abs(F-A)[outside].mean().round(2), ' |A-paint|',np.abs(A-paint)[outside].mean().round(2))
# fit per-channel linear map paint->A outside masks
M=np.zeros((3,2))
for c in range(3):
  x=paint[...,c][outside]; y=A[...,c][outside]
  M[c]=np.polyfit(x,y,1)
pred=np.stack([np.clip(clean[...,c]*M[c,0]+M[c,1],0,255) for c in range(3)],-1)
print('grade fit',M.round(3), ' resid', np.abs(np.stack([paint[...,c]*M[c,0]+M[c,1] for c in range(3)],-1)-A)[outside].mean().round(2))
diff=np.abs(F-pred).mean(-1)
model=ndi.binary_opening(diff>28,iterations=2)
names=['red car','teal car','pump L','pump M','pump R']
def bbox(m):
  ys,xs=np.nonzero(m); return xs.min(),ys.min(),xs.max(),ys.max(), xs.mean(), ys.mean()
for i,(n,m) in enumerate(zip(names,masks)):
  b=bbox(m)
  reg=ndi.binary_dilation(m,iterations=60)
  mm=model&reg
  lab,k=ndi.label(mm)
  # take components overlapping dilated mask
  if k:
    sizes=ndi.sum(mm,lab,range(1,k+1)); keep=np.isin(lab,np.nonzero(sizes>200)[0]+1); mm=keep
  bm=bbox(mm)
  inter=(mm&m).sum(); iou=inter/(mm|m).sum()
  print(f'{n}: mask bbox x{b[0]}-{b[2]} y{b[1]}-{b[3]} centroid ({b[4]:.0f},{b[5]:.0f}); model-diff bbox x{bm[0]}-{bm[2]} y{bm[1]}-{bm[3]} centroid ({bm[4]:.0f},{bm[5]:.0f}); dx {bm[4]-b[4]:+.0f} dy {bm[5]-b[5]:+.0f}; bottom dy {bm[3]-b[3]:+d}; IoU {iou:.2f}')
  core=ndi.binary_erosion(m,iterations=3)
  ma=A[core].mean(0); mf=F[core].mean(0); mp=paint[core].mean(0)
  print(f'   mean RGB in mask: original still {ma.round(0)}, model still {mf.round(0)}, diff {(mf-ma).round(0)}, painting file {mp.round(0)}')
  # also on intersection only
  both=core&mm
  print(f'   on model∩mask ({both.sum()} px): orig {A[both].mean(0).round(0)} model {F[both].mean(0).round(0)}')
Image.fromarray((model*255).astype(np.uint8)).save('../chk/modelmask.png')
ov=F.copy().astype(np.uint8)
for m in masks:
  edge=m^ndi.binary_erosion(m,iterations=2); ov[edge]=[255,255,0]
edge=model^ndi.binary_erosion(model,iterations=2); ov[edge]=[255,0,255]
Image.fromarray(ov).save('../chk/overlay.png')
