# What this does (plain words): an early look-at-it script: smooths the brightness of the mud ground (stones and water painted over) so the broad dark wheel ruts can be seen by eye before the rut finder was written. Writes a picture into /tmp (the scratch folder is deleted at the end). Analysis only.
import cv2, numpy as np
labels = np.load('labels_k16.npy')
img = cv2.imread('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reference/mud/colour.png')
grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
stone = np.isin(labels, [10, 12, 13, 15, 5, 8]).astype(np.uint8)
stone = cv2.dilate(stone, np.ones((5, 5), np.uint8))
# earth-only darkness: replace stone/water with local earth value
earth = grey.copy()
mask = stone > 0
earth[mask] = np.nan
pad = np.pad(earth, 40, mode='wrap')
valid = (~np.isnan(pad)).astype(np.float32)
num = cv2.GaussianBlur(np.nan_to_num(pad), (0, 0), 7); den = cv2.GaussianBlur(valid, (0, 0), 7)
smooth = (num / np.maximum(den, 1e-3))[40:-40, 40:-40]
v = np.clip((smooth - 30) / (120 - 30), 0, 1)
cv2.imwrite('/tmp/mudscratch/earth_dark.png', cv2.resize((v * 255).astype(np.uint8), (900, 900)))
