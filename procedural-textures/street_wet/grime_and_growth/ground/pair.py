import sys, cv2, numpy as np
def sheet(paths, out, labels=None, width=None, cols=None, crop=None):
    ims=[]
    for i,p in enumerate(paths):
        im=cv2.imread(p)
        if im is None: im=np.zeros((100,100,3),np.uint8)
        if crop: x0,y0,x1,y1=crop; im=im[y0:y1,x0:x1]
        if width: im=cv2.resize(im,(width,int(im.shape[0]*width/im.shape[1])),interpolation=cv2.INTER_AREA)
        if labels: cv2.putText(im,labels[i],(4,16),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),1,cv2.LINE_AA)
        ims.append(im)
    cols=cols or len(ims)
    rows=[]
    for r in range(0,len(ims),cols):
        row=ims[r:r+cols]
        h=max(i.shape[0] for i in row)
        row=[cv2.copyMakeBorder(i,0,h-i.shape[0],0,2,cv2.BORDER_CONSTANT,value=(30,30,30)) for i in row]
        rows.append(np.hstack(row))
    w=max(r.shape[1] for r in rows)
    rows=[cv2.copyMakeBorder(r,0,2,0,w-r.shape[1],cv2.BORDER_CONSTANT,value=(30,30,30)) for r in rows]
    cv2.imwrite(out,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,88])
if __name__=='__main__':
    out=sys.argv[1]; paths=sys.argv[2:]
    sheet(paths,out,labels=[p.split('/')[-1] for p in paths])
