# Blender script: render Noise Texture (4D, FBM, normalized) fields for a few detail/roughness settings and print their quantiles (for placing thresholds).
import bpy, sys, json, os, numpy as np
out=sys.argv[sys.argv.index('--')+1]
os.makedirs(out,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'
sc.render.resolution_x=sc.render.resolution_y=1024
sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='BW'; sc.render.image_settings.color_depth='16'
sc.view_settings.view_transform='Raw'; sc.view_settings.look='None'
sc.eevee.taa_render_samples=1
bpy.ops.mesh.primitive_plane_add(size=200)
plane=bpy.context.object
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=200
co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); co.location=(0,0,10); sc.camera=co
mat=bpy.data.materials.new('m'); mat.use_nodes=True; plane.data.materials.append(mat)
t=mat.node_tree; t.nodes.clear()
noise=t.nodes.new('ShaderNodeTexNoise'); noise.noise_dimensions='4D'; noise.noise_type='FBM'; noise.normalize=True
geo=t.nodes.new('ShaderNodeNewGeometry'); em=t.nodes.new('ShaderNodeEmission'); o=t.nodes.new('ShaderNodeOutputMaterial')
t.links.new(geo.outputs['Position'],noise.inputs['Vector']); t.links.new(noise.outputs['Fac'],em.inputs['Color']); t.links.new(em.outputs[0],o.inputs['Surface'])
res={}
for detail in (0.0,1.0,2.0,3.0):
    for rough in (0.5,0.55):
        noise.inputs['Detail'].default_value=detail; noise.inputs['Roughness'].default_value=rough
        noise.inputs['Scale'].default_value=1.0/4.0   # features about 4 m across; the plane is 200 m: many features
        noise.inputs['W'].default_value=3.0
        sc.render.filepath=f'{out}/n.png'
        bpy.ops.render.render(write_still=True)
        img=bpy.data.images.load(f'{out}/n.png'); a=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)[:,0]; bpy.data.images.remove(img)
        q=np.quantile(a,[0.01,0.05,0.1,0.25,0.5,0.75,0.9,0.95,0.99])
        res[f'd{detail}_r{rough}']=dict(mean=float(a.mean()),sd=float(a.std()),q=[round(float(v),3) for v in q])
        print('NOISE',detail,rough,res[f'd{detail}_r{rough}'],flush=True)
json.dump(res,open(f'{out}/noise_stats.json','w'),indent=1)
