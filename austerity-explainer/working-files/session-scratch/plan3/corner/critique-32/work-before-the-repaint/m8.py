exec(open('m1.py').read().split("print('frame mean")[0])
bm=mask('board'); dm=mask('drum'); cm=mask('chair'); pm=mask('pail'); lm=mask('lantern')
def prof(yy,x0,x1,masks):
    y=int(yy*H); a,b=int(x0*W),int(x1*W)
    print(f'row {yy} x {x0}-{x1} (px {a}-{b})')
    print('  luma', ' '.join(f'{v:.2f}' for v in lum[y,a:b]))
    for k,m in masks.items(): print(f'  {k:6s}', ''.join(k[0].upper() if v else '.' for v in m[y,a:b]))
print('== board right post vs house'); 
for yy in [0.60,0.68,0.72]: prof(yy,0.90,0.99,{'board':bm})
print('== drum right edge vs board left post')
for yy in [0.64,0.68,0.72,0.76]: prof(yy,0.64,0.72,{'board':bm,'drum':dm,'chair':cm})
