# NOTE (plain words): my own test of "the painter did not move or stretch anything". I cut the plate and the painting into 3 columns x 5 rows of tiles, turn each into an edge picture, and ask a standard method (phase correlation: it finds how far one picture must slide to match the other) how many pixels (at 1080 wide) each tile has slid. If all tiles say about 0, nothing moved. Done for the painting as returned (just resized) and for the helper's lined-up painting, and for the existing dry painting as a yardstick. Reads pictures only.
import cv2, numpy as np
B='proc-work/street_wet/painter_test'
SW='proc-work/street_wet/work/r35/main_wet_plate.png'
W,H=1080,1920
def g(p):
    im=cv2.resize(cv2.imread(p),(W,H),interpolation=cv2.INTER_AREA); return cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
def edges(a):
    a=cv2.GaussianBlur(a,(0,0),1.5); gx=cv2.Sobel(a,cv2.CV_32F,1,0); gy=cv2.Sobel(a,cv2.CV_32F,0,1); e=np.sqrt(gx**2+gy**2); return cv2.GaussianBlur(e,(0,0),2)
plate=edges(g(SW))
def run(name,path):
    e=edges(g(path)); rows=[]
    tw,th=W//3,H//5
    print(name)
    for j in range(5):
        row=[]
        for i in range(3):
            a=plate[j*th:(j+1)*th,i*tw:(i+1)*tw]; b=e[j*th:(j+1)*th,i*tw:(i+1)*tw]
            win=cv2.createHanningWindow(a.shape[::-1],cv2.CV_32F)
            (dx,dy),resp=cv2.phaseCorrelate(a,b,win)
            row.append('(%+.1f,%+.1f r=%.2f)'%(dx,dy,resp))
        print('  row',j,' '.join(row))
# as returned (1520x2704), simply resized to the plate frame
run('painting as returned, just resized',B+'/pictures/wet_painting_as_returned.png')
run('painting lined up by the helper',B+'/pictures/wet_painting_lined_up.png')
run('existing dry lockout painting (yardstick)','/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg')
