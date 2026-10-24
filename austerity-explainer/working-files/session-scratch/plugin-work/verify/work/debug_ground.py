import bpy, sys
from mathutils import Vector
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import place_kit as pk
from place_kit import scene_read
for n in ['Wall near east panel 4','Wall far panel 5','Trench back wall','Wall far panel 1']:
    o=bpy.data.objects[n]
    lo,hi=scene_read.world_bounds(o)
    c=((lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
    pts=[c,(lo[0],lo[1]),(hi[0],hi[1])]
    print('DBG', n, [round(float(v),4) for v in (lo[0],lo[1],hi[0],hi[1])], [round(pk.ground_height_at(*p),3) for p in pts])
