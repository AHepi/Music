# NOTE (plain words): draws the outlines that Blender computed for the props (drum, notice board, sacks, handcart, lamps, ladder, dustbin, coal heap, pail, spade, wheels, chimney, gates) on top of the new wet painting, in thin red, so a person can SEE whether the painter moved any prop. Also makes the same for the film's dry painting. Reads pictures only; writes JPEGs into the check folder.
import cv2, numpy as np, glob, os
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_test'
C=B+'/check'
W,H=1080,1920
masks={os.path.basename(f)[:-4]:cv2.imread(f).max(axis=2)>100 for f in glob.glob(B+'/alignment/facts/solo/*.png')}
print(list(masks))
def draw(path,name):
    im=cv2.resize(cv2.imread(path),(W,H),interpolation=cv2.INTER_AREA)
    for k,m in masks.items():
        cs,_=cv2.findContours(m.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(im,cs,-1,(0,0,255),1)
    return im
wet=draw(B+'/pictures/wet_painting_lined_up.png','wet')
dry=draw('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg','dry')
# crops: lower middle (cart, sacks, drum, board) and the far end (gates, lamps)
def crop(im,y0,y1,x0,x1,s=1.0):
    c=im[y0:y1,x0:x1]; return cv2.resize(c,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC) if s!=1 else c
near_w=crop(wet,950,1500,0,1080); near_d=crop(dry,950,1500,0,1080)
cv2.imwrite(C+'/pictures/outlines_near_wet_over_dry.jpg',np.vstack([near_w,near_d]),[cv2.IMWRITE_JPEG_QUALITY,88])
far_w=crop(wet,640,1020,0,1080); far_d=crop(dry,640,1020,0,1080)
cv2.imwrite(C+'/pictures/outlines_far_wet_over_dry.jpg',np.vstack([far_w,far_d]),[cv2.IMWRITE_JPEG_QUALITY,88])
