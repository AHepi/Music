import bpy, numpy as np, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sc=bpy.context.scene
dg=bpy.context.evaluated_depsgraph_get()
def vis_map(camname, x0=-6.0, x1=0.6, y0=-1.6, y1=3.4, step=0.2):
    cam=bpy.data.objects[camname]; sc.camera=cam
    cl=cam.location
    xs=np.arange(x0,x1+1e-6,step); ys=np.arange(y1,y0-1e-6,-step)
    print("camera", camname, "visibility map of water surface points (V visible, . occluded, o outside frame); columns x from", x0, "to", x1, "rows y from", y1, "down to", y0)
    pix={}
    for y in ys:
        row=""
        for x in xs:
            p=Vector((x,y,-0.10))
            co=world_to_camera_view(sc,cam,p)
            if not (0<=co.x<=1 and 0<=co.y<=1) or co.z<=0: row+="o"; continue
            d=(p-cl); L=d.length; d.normalize()
            ok,loc,n,i,ob,m=sc.ray_cast(dg, cl, d, distance=L-0.02)
            row+= "." if ok else "V"
            if not ok: pix[(round(x,2),round(y,2))]=(round(co.x*2400),round((1-co.y)*1600))
        print("%5.1f %s"%(y,row))
    return pix
pix=vis_map('photo')
for pt in [(-3.86,1.52),(-3.2,2.68),(-2.1,2.84),(-0.5,2.07),(-1.87,-0.68),(-2.54,2.07),(-4.36,2.34),(-3.22,1.9),(-0.46,0.76),(-4.02,-0.85),(-1.38,2.68),(-3.24,-0.88),(-4.7,-0.6),(-1.31,1.87),(-2.44,-0.16),(-5.15,2.2),(-2.4,-0.4),(-3.5,-0.3)]:
    cam=bpy.data.objects['photo']; co=world_to_camera_view(sc,cam,Vector((pt[0],pt[1],-0.1))); print("photo px", pt, round(co.x*2400), round((1-co.y)*1600))
vis_map('veranda')
cam=bpy.data.objects['veranda']
for pt in [(-3.86,1.52),(-3.2,2.68),(-2.1,2.84),(-0.5,2.07),(-1.87,-0.68),(-2.44,-0.16),(-2.4,-0.4),(-5.0,1.0)]:
    co=world_to_camera_view(sc,cam,Vector((pt[0],pt[1],-0.1))); print("veranda px", pt, round(co.x*2400), round((1-co.y)*1600))
# trunk + maple projections in photo
cam=bpy.data.objects['photo']
for nm,p in [("trunk base",(-6.7,1.3,0)),("trunk z1",(-6.65,1.2,0.95)),("trunk z2",(-6.15,1.05,1.85)),("trunk top",(-5.0,1.45,3.25)),("crown min",(-8.0,0,2)),("crown max",(-2.4,3.3,4.1)),("branch0 end",(-3.3,0.6,2.5)),("branch1 end",(-7.2,2.4,3.45)),("pine base",(7.6,4.6,0)),("pine top",(7.85,4.6,3.9))]:
    co=world_to_camera_view(sc,cam,Vector(p)); print("photo px", nm, p, round(co.x*2400), round((1-co.y)*1600), "depth", round(co.z,2))
