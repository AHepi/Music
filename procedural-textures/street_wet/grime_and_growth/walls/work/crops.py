import sys
from PIL import Image
def montage(paths, box, out, scale=1, labels=None):
    ims=[Image.open(p).convert('RGB').crop(box) for p in paths]
    w,h=ims[0].size
    sheet=Image.new('RGB',(w*len(ims),h))
    for k,i in enumerate(ims): sheet.paste(i,(k*w,0))
    if scale!=1: sheet=sheet.resize((int(sheet.width*scale),int(sheet.height*scale)), Image.LANCZOS)
    sheet.save(out,quality=88)
if __name__=='__main__':
    out=sys.argv[1]; box=tuple(int(v) for v in sys.argv[2].split(',')); scale=float(sys.argv[3]); paths=sys.argv[4:]
    montage(paths,box,out,scale)
