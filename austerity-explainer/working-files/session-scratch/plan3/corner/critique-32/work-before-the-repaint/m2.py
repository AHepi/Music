exec(open('m1.py').read().split("print('frame mean")[0])
import cv2
# drum mouth: per row inside drum mask from y 0.628 to 0.66, columns profile
dm=mask('drum')
print('--- drum top rows (end 5 vs end 4)')
for y in range(int(0.626*H), int(0.660*H)):
    row=dm[y]; 
    if row.sum()==0: continue
    xs=np.nonzero(row)[0]
    v=im[y,xs]; v4=im4[y,xs]
    print(y, f'{y/H:.4f}', len(xs), 'luma', f'{L(v).mean():.3f}', 'std', f'{L(v).std():.3f}', 'rgb', (v.mean(0)*255).round().astype(int), ' end4', f'{L(v4).mean():.3f}', (v4.mean(0)*255).round().astype(int))
