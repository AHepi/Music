import bpy, numpy as np, json
sc=bpy.context.scene
out={}
ml=bpy.data.objects['Maple leaves']; me=ml.data
n=len(me.vertices)
P=np.empty(n*3,np.float32); me.vertices.foreach_get('co',P); P=P.reshape(-1,3)
def attr(name, dim):
    a=me.attributes[name]; buf=np.empty(n*dim,np.float32)
    a.data.foreach_get('value' if dim==1 else 'vector', buf) if dim>0 else None
    return buf.reshape(n,dim) if dim>1 else buf
kind=np.array([a.value for a in me.attributes['leaf_kind'].data],np.int32)
rot=np.array([a.vector[:] for a in me.attributes['leaf_rot'].data],np.float32)
scale=np.array([a.vector[:] for a in me.attributes['leaf_scale'].data],np.float32)
hue=np.array([a.value for a in me.attributes['leaf_hue'].data],np.float32)
tone=np.array([a.value for a in me.attributes['leaf_tone'].data],np.float32)
rank=np.array([a.value for a in me.attributes['leaf_rank'].data],np.float32)
np.savez_compressed('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond/work/old_maple.npz',P=P,kind=kind,rot=rot,scale=scale,hue=hue,tone=tone,rank=rank)
print("leaves",n,"hue mean %.3f std %.3f"%(hue.mean(),hue.std()),"scale mean %.4f"%scale[:,0].mean(),"tone mean %.3f"%tone.mean())
print("hue hist", np.histogram(hue,bins=10,range=(0,1))[0].tolist())
# leaf source widths
for i in range(5):
    s=bpy.data.objects['Maple leaf source %d'%i]; V=np.array([v.co[:] for v in s.data.vertices]); print("leaf src",i,"width",np.ptp(V[:,0]).round(3),"len",np.ptp(V[:,1]).round(3),"verts",len(V))
cams={}
for nm in ('photo','veranda'):
    o=bpy.data.objects[nm]; d=o.data
    cams[nm]=dict(loc=list(o.matrix_world.translation), R=[list(r)[:3] for r in o.matrix_world.to_3x3()], lens=d.lens, sensor=d.sensor_width, fit=d.sensor_fit, res=[sc.render.resolution_x,sc.render.resolution_y], shift=[d.shift_x,d.shift_y])
json.dump(cams,open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond/work/cams.json','w'))
# pine pads centres: from the old function: pad anchors + satellites -> read vertex clusters of pine pads by tri centre? Use limb ends
print("done")
