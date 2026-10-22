import bpy, numpy as np
ob = bpy.data.objects['Raked gravel court']
me = ob.data
co = np.empty(len(me.vertices)*3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1,3)
z = co[:,2] + ob.location.z
print('loc', tuple(ob.location), 'scale', tuple(ob.scale))
print('z pct', np.percentile(z,[0,1,5,25,50,75,95,99,100]).round(4))
h,e = np.histogram(z, bins=20); print(h); print(e.round(4))
# z along one x-line
sel = np.abs(co[:,1]+2.0)<0.02
xs = co[sel]; xs = xs[np.argsort(xs[:,1])]
print('profile along y (x~mid)')
m = np.abs(co[:,0]-5.0)<0.02
pr = co[m]; pr = pr[np.argsort(pr[:,1])]
print(np.round(pr[:60,1],3)); print(np.round(pr[:60,2],4))
