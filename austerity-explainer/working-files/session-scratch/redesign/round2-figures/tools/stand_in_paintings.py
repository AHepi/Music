"""What this does (scratch test): makes two stand-in "paintings" from the plate and the helper plate with two
different filters (different smoothing, edge strength and a small colour shift), so the state picture step can be
tried for free on two pictures whose brushwork differs everywhere, as two Flux paintings would.
Use: python3 -I stand_in_paintings.py PLATE HELPER_PLATE OUT_A OUT_B"""
import sys
import cv2
import numpy as np
plate_path, helper_path, out_a, out_b = sys.argv[1:5]
plate, helper = cv2.imread(plate_path), cv2.imread(helper_path)
a = cv2.stylization(plate, sigma_s=25, sigma_r=0.20).astype(np.float32)
b = cv2.edgePreservingFilter(helper, flags=cv2.RECURS_FILTER, sigma_s=70, sigma_r=0.45).astype(np.float32)
b = cv2.detailEnhance(np.clip(b, 0, 255).astype(np.uint8), sigma_s=8, sigma_r=0.2).astype(np.float32)
b = b * np.array([0.97, 1.0, 1.05], np.float32) + 3   # a little warmer and lighter, as a second painting might be
cv2.imwrite(out_a, np.clip(a, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
cv2.imwrite(out_b, np.clip(b, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 93])
d = np.abs(a - b).max(axis=2)
print('stand-in paintings differ by', round(float(d.mean()), 1), 'levels on average over the whole frame')
