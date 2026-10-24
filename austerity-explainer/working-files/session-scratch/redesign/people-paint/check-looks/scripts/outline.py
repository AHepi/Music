import numpy as np, cv2, json
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/'
def L(p):
    a=np.asarray(Image.open(p).convert('RGB')).astype(np.float32); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
pt=L(P+'people-test-painting.png'); pl=L(P+'people-test-plate.jpg')
H,W=pt.shape
facts=json.load(open(F+'facts.json'))
ids=np.asarray(Image.open(F+'ids.png').convert('RGB').resize((W,H),Image.NEAREST)).astype(int)
def gmask(n):
    c=np.array(facts['groups'][n]['colour']); return (np.abs(ids-c).sum(-1)<=6)
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21))
bh=cv2.morphologyEx(pt,cv2.MORPH_BLACKHAT,k)
ink=((bh>15)&(pt<40)).astype(np.uint8)
inkn=cv2.dilate(ink,np.ones((7,7),np.uint8)).astype(bool)
for n in ['man facing','man arms folded','man stooped','man hand on bar','man leaning','brazier','lamp post']:
    m=gmask(n).astype(np.uint8)
    edge=(m-cv2.erode(m,np.ones((3,3),np.uint8))).astype(bool)
    print('%-16s outline pixels %5d, share of the outline with an ink line within 3 px: %.0f%%'%(n,edge.sum(),100*inkn[edge].mean()))
