"""What this does (plain words): makes the one picture about the ninth comparison (the house sample at 20 s): the picture drawn with the old stage, with the new
stage, with the old stage plus ONE added space (which changes nothing in the maths), and the difference between the old one and the one-space one, made 36
times stronger so that it can be seen. Run: python3 -I make_ninth_picture.py"""
import cv2, numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/wet_lockout_film/grain_check/out/'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/27 Wet lockout shot in the film - pictures/27 The ninth picture - the house sample, a faint speckle from one added space.jpg'
im = {n: cv2.imread(G + n + '/still-20.00.jpg') for n in ('old', 'new', 'oldspace')}
diff = np.abs(im['old'].astype(int) - im['oldspace'].astype(int))
amplified = np.clip(diff * 36, 0, 255).astype(np.uint8)
W, H = 360, 640
def small(a): return cv2.resize(a, (W, H), interpolation=cv2.INTER_AREA)
amp_small = amplified[1000:1000 + H, 300:300 + W].copy()   # a true-size piece (1 dot = 1 dot) of the difference, rows 1000 to 1640, columns 300 to 660
panels = [small(im['old']), small(im['new']), small(im['oldspace']), amp_small]
captions = [('OLD stage', 'the film as it was'),
            ('NEW stage (toe added)', 'same as old, in my drawing'),
            ('OLD stage + one space', 'a space changes no maths'),
            ('Old vs old + space, x36 stronger', 'true-size piece; 7.7% of dots, at most 7 of 255')]
head = 56
canvas = np.full((H + head, W * 4 + 18, 3), 18, np.uint8)
for i, (p, (a, b)) in enumerate(zip(panels, captions)):
    x = i * (W + 6)
    canvas[head:head + H, x:x + W] = p
    cv2.putText(canvas, a, (x + 4, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(canvas, b, (x + 4, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (230, 230, 230), 1, cv2.LINE_AA)
cv2.imwrite(OUT, canvas, [cv2.IMWRITE_JPEG_QUALITY, 82])
import os; print(os.path.getsize(OUT), 'bytes', canvas.shape)
