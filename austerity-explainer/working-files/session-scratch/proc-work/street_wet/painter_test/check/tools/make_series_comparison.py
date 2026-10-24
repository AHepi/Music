# NOTE (plain words): makes one picture with four paintings side by side, each shrunk to 560 wide, so I can judge by eye whether the new wet painting is in the same hand as the series. Reads only; writes JPEG into the check folder.
import sys
from PIL import Image
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_test'
P='/home/user/Music/austerity-explainer/film-kit/assets'
files=[(P+'/paintings/inflation-chapter-2/403-bg-glasgow-tenements.png','STYLE: Glasgow ch2'),
 (P+'/models/pit-village/notice-corner-painted.jpg','notice corner'),
 (P+'/models/pit-village/lockout-painted.jpg','dry lockout'),
 (B+'/pictures/wet_painting_lined_up.png','NEW WET')]
from PIL import ImageDraw
W=560
ims=[]
for f,l in files:
    im=Image.open(f).convert('RGB'); h=round(im.height*W/im.width); im=im.resize((W,h),Image.LANCZOS)
    d=ImageDraw.Draw(im); d.rectangle([0,0,W,22],fill=(0,0,0)); d.text((4,5),l,fill=(255,255,255)); ims.append(im)
H=max(i.height for i in ims)
out=Image.new('RGB',(W*4+9,H),(255,255,255))
for k,i in enumerate(ims): out.paste(i,(k*(W+3),0))
out.save(sys.argv[1],quality=88)
