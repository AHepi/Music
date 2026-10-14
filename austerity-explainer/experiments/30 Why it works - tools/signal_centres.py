"""What this does: finds where a picture's strongest signals sit, as fractions of its width and height:
the centre of its brightest 3% (after a light blur) and the centre of its clearly warm, bright pixels.
Input: picture paths. Output: one line of numbers per picture."""
import sys
import cv2
import numpy as np
for picture_path in sys.argv[1:]:
    picture = cv2.imread(picture_path)
    height, width = picture.shape[:2]
    grey = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    blurred = cv2.GaussianBlur(grey, (0, 0), width * 0.01)
    brightest = blurred >= np.percentile(blurred, 97)
    ys, xs = np.nonzero(brightest)
    blue, green, red = [channel.astype(np.float32) for channel in cv2.split(picture)]
    warm = (np.clip((red - blue) / 255.0, 0, 1) * grey) > 0.18
    wy, wx = np.nonzero(warm)
    top_row = [round(float(grey[:height // 3, a:b].mean()), 3) for a, b in ((0, width // 3), (width // 3, 2 * width // 3), (2 * width // 3, width))]
    print(picture_path, 'brightest 3% centre', round(xs.mean() / width, 3), round(ys.mean() / height, 3),
          '| warm centre', round(wx.mean() / width, 3), round(wy.mean() / height, 3),
          '| top row brightness', top_row, '| brightest 3% in top third %', round(100 * float((ys < height / 3).mean()), 1))
