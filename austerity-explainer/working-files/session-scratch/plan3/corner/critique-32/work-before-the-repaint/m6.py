exec(open('m1.py').read().split("print('frame mean")[0])
bm=mask('board'); ys,xs=np.nonzero(bm)
print('board box', xs.min(), ys.min(), xs.max(), ys.max(), '->', xs.min()/W, ys.min()/H, xs.max()/W, ys.max()/H)
# top-left corner of board: leftmost x on rows near top
for y in range(ys.min(), ys.min()+40, 4):
    r=np.nonzero(bm[y])[0]
    if len(r): print(' row', y, f'{y/H:.4f}', 'board left x', r.min(), f'{r.min()/W:.4f}')
# doorway right edge: on rows 0.42-0.46, find the column where luma jumps from <0.05 to >0.1, between x 0.60 and 0.66
for yy in [0.425,0.435,0.445,0.455,0.462]:
    y=int(yy*H); row=lum[y, int(0.60*W):int(0.70*W)]
    s=' '.join(f'{v:.2f}' for v in row)
    print(f'row {yy}: ', s[:600])
