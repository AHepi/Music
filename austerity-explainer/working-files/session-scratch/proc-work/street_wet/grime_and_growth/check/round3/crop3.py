import sys
from PIL import Image
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/'
P={'base_dry':G+'integrated/plates/street/final_main_A_dry_base.png',
'base_wet':G+'integrated/plates/street/final_main_A_wet_base.png',
'old_dry':G+'integrated/plates/street/final_main_A_dry_kit.png',
'old_wet':G+'integrated/plates/street/final_main_A_wet_kit.png',
'fix_dry':G+'fix/plates/street/final_main_A_dry_kit.png',
'fix_wet':G+'fix/plates/street/final_main_A_wet_kit.png',
'lb_dry':G+'integrated/plates/lockout/final_lockout_B_dry_base.png',
'lb_wet':G+'integrated/plates/lockout/final_lockout_B_wet_base.png',
'lo_dry':G+'integrated/plates/lockout/final_lockout_B_dry_kit.png',
'lo_wet':G+'integrated/plates/lockout/final_lockout_B_wet_kit.png',
'lf_dry':G+'fix/plates/lockout/final_lockout_B_dry_kit.png',
'lf_wet':G+'fix/plates/lockout/final_lockout_B_wet_kit.png'}
def crop(names, box, out, scale=1.0, label=True):
    ims=[]
    for n in names:
        im=Image.open(P[n]).convert('RGB').crop(box)
        if scale!=1.0: im=im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS)
        ims.append(im)
    w=sum(i.width for i in ims)+4*(len(ims)-1); h=max(i.height for i in ims)
    c=Image.new('RGB',(w,h),(255,255,255)); x=0
    for i in ims: c.paste(i,(x,0)); x+=i.width+4
    c.save(out,quality=84)
    print(out,c.size)
if __name__=='__main__':
    names=sys.argv[1].split(','); box=tuple(int(v) for v in sys.argv[2].split(',')); out=sys.argv[3]
    scale=float(sys.argv[4]) if len(sys.argv)>4 else 1.0
    crop(names,box,out,scale)
