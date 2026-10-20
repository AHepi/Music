# What this does: prints how big the jump is across the left/right and top/bottom tile edges compared with the usual jump between
# neighbouring pixel columns/rows (about 1.0 = invisible seam). Use: python3 -I check_seams.py FOLDER_WITH_colour.png
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1] + '/colour.png').astype(float)
nu = np.abs(im[:, 1:] - im[:, :-1]).mean(); nv = np.abs(im[1:] - im[:-1]).mean()
su = np.abs(im[:, 0] - im[:, -1]).mean(); sv = np.abs(im[0] - im[-1]).mean()
print(f'left-right seam {su:.2f} vs neighbours {nu:.2f}  ratio {su/nu:.2f}')
print(f'top-bottom seam {sv:.2f} vs neighbours {nv:.2f}  ratio {sv/nv:.2f}')
# where along the seam is it worst
col = np.abs(im[:, 0] - im[:, -1]).mean(axis=1); row = np.abs(im[0] - im[-1]).mean(axis=1)
print('worst rows on the left-right seam:', np.argsort(col)[-6:][::-1].tolist(), ' worst columns on top-bottom seam:', np.argsort(row)[-6:][::-1].tolist())
