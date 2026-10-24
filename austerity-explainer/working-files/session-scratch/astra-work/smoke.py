# What this does: smoke test of the Astra add-on in Blender 5.2.2: makes one roof, one stone, one plank run and a small
# landscape, then prints their sizes. Use: blender -b --disable-autoexec --python smoke.py -- ADDON_FOLDER
import sys, math, bpy
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from astra_loader import load_astra, apply_blender_52_shim
folder = sys.argv[sys.argv.index('--') + 1]
api = load_astra(folder)
print('SHIM APPLIED', apply_blender_52_shim(api))
print('ASTRA API LOADED', api.VERSION)
bpy.ops.wm.read_factory_settings(use_empty=True)
dg = lambda: bpy.context.evaluated_depsgraph_get()

def bbox(obj):
    bpy.context.view_layer.update()
    ev = obj.evaluated_get(dg()); me = ev.to_mesh()
    vs = [obj.matrix_world @ v.co for v in me.vertices]
    ev.to_mesh_clear()
    if not vs: return None
    lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
    return [round(x, 3) for x in lo], [round(x, 3) for x in hi], len(vs)

roof = api.create_roof('test roof', api.RoofSpec(width=6.0, half_depth=1.8, rise=0.8), location=(0, 0, 0))
print('ROOF', roof.type, bbox(roof), dict(roof.items()).get('ct_spec'))
stone = api.create_stone('test stone', api.StoneSpec(length=0.7, width=0.55, height=0.25), location=(10, 0, 0))
print('STONE', bbox(stone))
planks = api.create_planks(length=3.0, width=1.0, count=12, location=(20, 0, 0))
for c in planks.children_recursive: print('PLANKS child', c.name, bbox(c))
print('PLANK root', planks.name, list(planks.keys()))
# landscape on a small heightfield
import bmesh
me = bpy.data.meshes.new('ground src'); bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=40, y_segments=30, size=0.25)   # size is half? check below
bm.to_mesh(me); bm.free()
src = bpy.data.objects.new('ground src', me); bpy.context.scene.collection.objects.link(src); src.location = (30, 0, 0)
print('GROUND', bbox(src))
spec = api.default_spec(bounds=(-5, -3.75, 5, 3.75), seed=7)
root = api.create_landscape(src, spec, name='test land')
print('LAND root', type(root), getattr(root, 'name', root))
