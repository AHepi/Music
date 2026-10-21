import sys; sys.path.insert(0,'scripts')
from paths import *
from PIL import Image
P=FILM+"/paintings/"
jobs={
 "s109_wall_gate":(P+"austerity-chapter-1/109-bg-factory-gate.jpg",(0,500,1000,1300)),
 "s109_street_foot":(P+"austerity-chapter-1/109-bg-factory-gate.jpg",(300,1700,1300,2500)),
 "s108_walls":(P+"austerity-chapter-1/108-bg-kitchen.jpg",(0,700,1000,1500)),
 "s104_street":(P+"austerity-chapter-1/104-bg-turin-street.jpg",(0,1900,1000,2700)),
 "s403_road":(P+"inflation-chapter-2/403-bg-glasgow-tenements.png",(0,1900,1000,2700)),
 "s403_walls":(P+"inflation-chapter-2/403-bg-glasgow-tenements.png",(0,700,1000,1500)),
}
for k,(f,box) in jobs.items():
    im=Image.open(f).convert('RGB'); print(k,im.size)
    im.crop(box).save(WORK+f"/{k}.jpg",quality=88)
