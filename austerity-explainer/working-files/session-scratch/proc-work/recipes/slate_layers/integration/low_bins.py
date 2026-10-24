# What this does (plain words): shows how much of a picture's brightness variation sits at the LARGEST sizes (3 to about 30 repeats across the
# tile), in the same bins the "same kind" tool uses, for the reference and for baked pictures (any size). The reference has little power at the
# very largest sizes; too much there means big smooth patches (drift, bleach, damp, moss areas) are too strong. Measurement for hand-tuning only.
# Use: python3 -I low_bins.py PICTURE ...
import sys, cv2, numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
def low(path, nbins=14):
    img = cv2.imread(path); img = cv2.resize(img, (627, 627), interpolation=cv2.INTER_AREA)
    L = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)[..., 0] * 100 / 255
    c = L - L.mean(); P = np.abs(np.fft.fftshift(np.fft.fft2(c))) ** 2
    s = 627; y, x = np.indices(P.shape); r = np.hypot(x - s // 2, y - s // 2) * (1254 / 627) / 2.0 * 2.0 / 2.0  # cycles per 1254 tile = 2 x cycles per 627 -> keep same units as the tool
    r = np.hypot(x - s // 2, y - s // 2)                       # cycles per tile (frequency index is the same for any resolution)
    edges = np.geomspace(3.0, 1254 / 2.0 - 1, 31)
    tot = np.abs(np.fft.fftshift(np.fft.fft2(c))) ** 2
    # normalise by the same total the tool uses (sum of ring means over 30 bins is not available at 627, so report share of the ring means among the first bins instead)
    curve = [P[(r >= edges[i]) & (r < edges[i + 1])].mean() for i in range(nbins)]
    return np.array(curve) / curve[0]
ref = low(PROC + '/reference/slate/colour.png')
print('bins (cycles per tile):', [round(float(v), 1) for v in np.geomspace(3.0, 1254 / 2.0 - 1, 31)[:14]])
print('reference (relative to bin 0):', np.round(np.log10(ref), 2).tolist())
for p in sys.argv[1:]:
    c = low(p); print(p.split('/')[-1][:24].ljust(24), np.round(np.log10(c) - np.log10(ref), 2).tolist(), ' (difference from reference)')
