import numpy as np, cv2, json
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p): a=np.asarray(Image.open(p).convert('RGB')).astype(np.float32); return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
z=1.08; s=1080/1536*z
M=np.array([[s,0,540-1536/2*s],[0,s,960-2730/2*s]],np.float32)
pt=cv2.warpAffine(load(P+'people-test-painting.png'),M,(1080,1920))
facts=json.load(open(F+'facts.json'))
ids=np.asarray(Image.open(F+'ids.png').convert('RGB').resize((1536,2730),Image.NEAREST)).astype(np.uint8)
idsf=cv2.warpAffine(ids,M,(1080,1920),flags=cv2.INTER_NEAREST).astype(int)
allm=np.load(D+'allmen_film.npy')
f1=load(D+'pf/f031.png'); s1=load(D+'sf/f031.png')
m8=allm.astype(np.uint8)
def ringband(a,b):
    return cv2.dilate(m8,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*b+1,2*b+1))).astype(bool)&~cv2.dilate(m8,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*a+1,2*a+1))).astype(bool)
print('luminance in bands outside the men (px from the 3D outline): ')
for lab,img in [('painting',pt),('painted film',f1),('silhouette film',s1)]:
    vals=[img[ringband(a,b)].mean() for a,b in [(0,2),(2,4),(4,7),(7,12),(12,20),(20,35)]]
    print('  %-16s'%lab,'  '.join('%d-%dpx %.1f'%(a,b,v) for (a,b),v in zip([(0,2),(2,4),(4,7),(7,12),(12,20),(20,35)],vals)))
