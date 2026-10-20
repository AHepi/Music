# Plain note: looks at the brick reference colour picture and makes a black-and-white picture of where the mortar is (white = mortar),
# using how grey-brown (low colour strength) a dot is compared with the strongly red/orange bricks. Saves it for checking by eye.
# Run: python3 -I brick_mortar_mask.py OUT_PNG
import sys, numpy as np, cv2
REF = 'proc-work/reference/brick/colour.png'
img = cv2.imread(REF)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
h, s, v = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
# mortar: tan/grey = hue 20..50 deg, saturation lower than the bricks
mortar = ((s < 0.42) & (v > 0.30)).astype(np.uint8)
mortar = cv2.morphologyEx(mortar, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
mortar = cv2.morphologyEx(mortar, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
cv2.imwrite(sys.argv[1], mortar * 255)
print('mortar fraction', mortar.mean())
