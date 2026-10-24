# What this does: a quick test of whether bmesh gives a new face its normal straight away (for the piers' stripes)
import bmesh
bm = bmesh.new()
x0, y0, z0, x1, y1, z1 = 0, 0, 0, 0.9, 0.6, 4.0
corners = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
verts = [bm.verts.new(c) for c in corners]
quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
faces = [bm.faces.new([verts[i] for i in q]) for q in quads]
print('NORMALS', [tuple(round(v, 2) for v in f.normal) for f in faces])
