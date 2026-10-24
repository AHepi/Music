from common import *
s5, s4 = load(S5), load(S4)
d = luma(s5) - luma(s4)
# grid of mean change, 8 across x 12 down
H, W = d.shape
for j in range(12):
    print(f'{j/12:.2f}-{(j+1)/12:.2f}', ' '.join(f'{d[int(j*H/12):int((j+1)*H/12), int(i*W/8):int((i+1)*W/8)].mean():+.3f}' for i in range(8)))
img = np.clip(0.5 + d * 2, 0, 1)
rgb = np.stack([np.clip(-d*4,0,1)*0+np.clip(0.5-d*3,0,1), np.clip(0.5+d*3,0,1), np.clip(0.5+d*3,0,1)], -1)
Image.fromarray((np.stack([img]*3,-1)*255).astype('uint8')).resize((540,960)).save('diff_s5_minus_s4.png')
