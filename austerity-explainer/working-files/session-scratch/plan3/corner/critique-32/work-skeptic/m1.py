from common import *
s5, s4 = load(S5), load(S4)
ref = load(REF, (1080, 1920))
for name, a in (('s5', s5), ('s4', s4), ('ref', ref)):
    L = luma(a)
    h = L.shape[0]
    print(name, 'frame', L.mean().round(3), 'thirds', [L[int(i*h/3):int((i+1)*h/3)].mean().round(3) for i in range(3)],
          'left/right', L[:, :540].mean().round(3), L[:, 540:].mean().round(3),
          'bottom third L/R', L[1280:, :540].mean().round(3), L[1280:, 540:].mean().round(3))
