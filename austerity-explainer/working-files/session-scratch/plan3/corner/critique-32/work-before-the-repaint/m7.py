exec(open('m1.py').read().split("print('frame mean")[0])
lp=mask('lamp post')
def rowprof(yy,x0,x1,label):
    y=int(yy*H); a,b=int(x0*W),int(x1*W)
    print(f'{label} row {yy}: x {x0}-{x1}')
    print('  luma', ' '.join(f'{v:.2f}' for v in lum[y,a:b]))
    print('  lamp', ''.join('L' if v else '.' for v in lp[y,a:b]))
    print('  R-B ', ' '.join(f'{v:+.1f}' for v in (im[y,a:b,0]-im[y,a:b,2])))
for yy in [0.22,0.25,0.28]:
    rowprof(yy,0.83,0.90,'lamp glass right edge')
