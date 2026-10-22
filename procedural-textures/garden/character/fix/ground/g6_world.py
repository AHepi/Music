"""GROUND builder: questions about the open scene (where is the ground, is a spot free, is it in a camera's view, how far to a rock foot).
Runs inside Blender (bpy, numpy). Built once per stage run from the CURRENT scene, so it follows whatever the other builders did to rocks and stones.
"""
import bpy
import os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

GROUND = 'Astra / Courtyard receiving ground'
SKIP_PREFIX = ('Dark plain', 'Hills', 'Pond water', 'Basin water', 'Courtyard ground source', 'Life /', 'Maple branch', 'Maple leaf', 'Maple inner',
               'Maple leaves', 'Pine limb', 'Pine pads', 'Hall roof', 'Bamboo leaves', 'Lily', 'Lotus', 'Fallen leaves', 'Open room', 'Shoji',
               'Eave', 'Hall beams', 'Roof carrying', 'CT / Ceramic', 'Raked gravel court', 'Astra / Courtyard receiving', 'Fix / ', 'G6 ground')
FOOT_PREFIX = ('Rock ', 'Pond edge stone', 'Gravel rock', 'Stepping stone', 'Stone plinth', 'Lantern base', 'Basin front', 'Basin candle', 'Basin bucket',
               'Veranda step', 'Bridge pier')


def mesh_world(ob, dg):
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    me.calc_loop_triangles()
    nv = len(me.vertices)
    co = np.zeros(nv * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    mw = np.array(ob.matrix_world, dtype=np.float32)
    co = co @ mw[:3, :3].T + mw[:3, 3]
    tris = np.zeros(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get('vertices', tris)
    eo.to_mesh_clear()
    return co, tris.reshape(-1, 3)


class World:
    def __init__(self, maps_dir=None, verbose=True):
        sc = bpy.context.scene
        self.scene = sc
        dg = bpy.context.evaluated_depsgraph_get()
        self.dg = dg
        g = bpy.data.objects[GROUND]
        self.ground_obj = g
        self.gbvh = BVHTree.FromObject(g, dg)
        gco, gtri = mesh_world(g, dg)
        self.gco = gco
        verts, polys, off = [], [], 0
        self.feet = {}              # name -> Nx3 world points at the base of the object
        self.bbox = {}
        used = []
        for ob in bpy.data.objects:
            if ob.type != 'MESH' or ob.hide_render or (ob.get('g6_made') == 1 and ob.get('garden_owner') == 'ground'):
                continue
            n = ob.name
            if ob == g or any(n.startswith(p) for p in SKIP_PREFIX):
                continue
            try:
                co, tri = mesh_world(ob, dg)
            except Exception:
                continue
            if len(co) == 0 or len(tri) == 0:
                continue
            verts.append(co)
            polys.append(tri + off)
            off += len(co)
            used.append(n)
            self.bbox[n] = (co.min(0), co.max(0))
            if any(n.startswith(p) for p in FOOT_PREFIX) or n.startswith('Gravel kerb'):
                self.feet[n] = co
        # the raked gravel court as one slab (its 222 000 triangles are not needed to know where it is)
        c = bpy.data.objects.get('Raked gravel court')
        if c is not None:
            mn = np.array([min(v[0] for v in [c.matrix_world @ Vector(b) for b in c.bound_box]), 0, 0])
            bb = [c.matrix_world @ Vector(b) for b in c.bound_box]
            x0, x1 = min(b.x for b in bb), max(b.x for b in bb)
            y0, y1 = min(b.y for b in bb), max(b.y for b in bb)
            z = max(b.z for b in bb)
            slab = np.array([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]], dtype=np.float32)
            verts.append(slab)
            polys.append(np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32) + off)
            off += 4
            self.court = (x0, x1, y0, y1)
            self.court_z = float(z)
        V = np.concatenate(verts).tolist()
        P = [tuple(t) for t in np.concatenate(polys).tolist()]
        self.obs = BVHTree.FromPolygons(V, P)
        self.n_obstacle_objects = len(used)
        self.n_obstacle_tris = len(P)
        if verbose:
            print('G6 world: obstacle objects', len(used), 'triangles', len(P), 'feet objects', len(self.feet))
        # the hedge blobs are not obstacles for plants, but a camera must not sit inside one
        from mathutils.kdtree import KDTree
        pts = []
        for hn in ('Life / shrubs', 'Fix / far hedge'):
            h = bpy.data.objects.get(hn)
            if h is not None:
                co, _ = mesh_world(h, dg)
                pts.append(co)
        allp = np.concatenate(pts) if pts else np.zeros((0, 3), np.float32)
        self.hedge_kd = KDTree(max(len(allp), 1))
        for i, p in enumerate(allp):
            self.hedge_kd.insert(Vector(p), i)
        self.hedge_kd.balance()
        self.cams = [bpy.data.objects[n] for n in ('photo', 'veranda') if n in bpy.data.objects]
        self.maps_dir = maps_dir
        self._mask = None

    # ------------------------------------------------------------ queries
    def ground_z(self, x, y):
        h = self.gbvh.ray_cast(Vector((x, y, 9.0)), Vector((0, 0, -1)))
        return None if h[0] is None else float(h[0].z)

    def ground_hit(self, x, y):
        h = self.gbvh.ray_cast(Vector((x, y, 9.0)), Vector((0, 0, -1)))
        return (None, None) if h[0] is None else (h[0], h[1])

    def surface(self, x, y):
        """(height, on_gravel): the raked gravel court counts as the surface where it lies."""
        c = getattr(self, 'court', None)
        if c is not None and c[0] <= x <= c[1] and c[2] <= y <= c[3]:
            return self.court_z, True
        return self.ground_z(x, y), False

    def free(self, x, y, r=0.0, zmin=-0.05, zmax=0.6, probes=4, gravel_ok=False):
        pts = [(0.0, 0.0)]
        if r > 0:
            for k in range(probes):
                a = 6.2831853 * k / probes
                pts.append((r * np.cos(a), r * np.sin(a)))
        for dx, dy in pts:
            if gravel_ok:
                gz, _ = self.surface(x + dx, y + dy)
            else:
                gz = self.ground_z(x + dx, y + dy)
            if gz is None or gz < zmin or gz > zmax:
                return False
            h = self.obs.ray_cast(Vector((x + dx, y + dy, gz + 0.30)), Vector((0, 0, -1)), 0.5)
            if h[0] is not None and h[0].z > gz + 0.012:
                return False
        return True

    def near_hedge(self, p, r=1.0):
        co, idx, d = self.hedge_kd.find(Vector(p))
        return d < r

    def visible(self, x, y, z=0.2, margin=0.04):
        for cam in self.cams:
            c = world_to_camera_view(self.scene, cam, Vector((x, y, z)))
            if c.z > 0 and -margin <= c.x <= 1 + margin and -margin <= c.y <= 1 + margin:
                return True
        return False

    def view_xy(self, cam_name, x, y, z=0.1):
        cam = bpy.data.objects[cam_name]
        c = world_to_camera_view(self.scene, cam, Vector((x, y, z)))
        return c.x, c.y, c.z

    # ------------------------------------------------------------ the worn-path mask (red channel)
    def path_mask(self):
        if self._mask is None:
            p = os.path.join(self.maps_dir, 'path_mask.png')
            img = bpy.data.images.load(p, check_existing=False)
            img.colorspace_settings.name = 'Non-Color'
            w, h = img.size
            a = np.zeros(w * h * 4, dtype=np.float32)
            img.pixels.foreach_get(a)
            a = a.reshape(h, w, 4)[::-1]            # bpy rows start at the bottom: flip so row 0 = top = +y
            self._mask = a[::2, ::2, 0].copy()
            bpy.data.images.remove(img)
        return self._mask

    def mask_at(self, x, y):
        m = self.path_mask()
        n = m.shape[0]
        c = int(np.clip((x - (-11.0)) / 22.0 * n, 0, n - 1))
        r = int(np.clip((1.0 - (y - (-8.5)) / 21.0) * n, 0, n - 1))
        return float(m[r, c])

    # ------------------------------------------------------------ distance fields on a 0.1 m grid
    def grid(self):
        xs = np.arange(-10.0, 10.0, 0.1) + 0.05
        ys = np.arange(-8.0, 12.0, 0.1) + 0.05
        return xs, ys

    def dist_field(self, pts_xy, cap=3.0):
        xs, ys = self.grid()
        X, Y = np.meshgrid(xs, ys)
        cells = np.stack([X.ravel(), Y.ravel()], axis=1).astype(np.float32)
        if len(pts_xy) == 0:
            return np.full((len(ys), len(xs)), cap, np.float32)
        P = np.asarray(pts_xy, dtype=np.float32)
        if len(P) > 3000:
            P = P[np.random.default_rng(1).choice(len(P), 3000, replace=False)]
        d = np.full(len(cells), cap, np.float32)
        for i in range(0, len(cells), 4000):
            c = cells[i:i + 4000]
            dd = np.sqrt(((c[:, None, :] - P[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
            d[i:i + 4000] = np.minimum(d[i:i + 4000], dd)
        return d.reshape(len(ys), len(xs))

    def feature_points(self):
        """world xy points for: rock feet, water edge, kerb, path edge, plinth and wall foot."""
        out = {}
        rock, plinth, kerb = [], [], []
        for n, co in self.feet.items():
            if n.startswith('Stone plinth') or n.startswith('Veranda step'):
                sel = co[(co[:, 2] < 0.12)]
                plinth.append(sel[:, :2])
                continue
            if n.startswith('Gravel kerb'):
                kerb.append(co[co[:, 2] < 0.1][:, :2])
                continue
            # rock foot: vertices close to the ground under them
            low = []
            for p in co[co[:, 2] < 0.45]:
                gz = self.ground_z(p[0], p[1])
                if gz is not None and p[2] < gz + 0.14:
                    low.append(p[:2])
            if low:
                rock.append(np.array(low, dtype=np.float32))
        out['rock'] = np.concatenate(rock) if rock else np.zeros((0, 2), np.float32)
        out['plinth'] = np.concatenate(plinth) if plinth else np.zeros((0, 2), np.float32)
        out['kerb'] = np.concatenate(kerb) if kerb else np.zeros((0, 2), np.float32)
        # water edge: ground heights between the waterline and the bank top
        wx = np.arange(-8.0, 1.6, 0.08)
        wy = np.arange(-3.6, 5.2, 0.08)
        pts = []
        for x in wx[::1]:
            for y in wy:
                z = self.ground_z(float(x), float(y))
                if z is not None and -0.10 < z < -0.02:
                    pts.append((x, y))
        out['water'] = np.array(pts, dtype=np.float32) if pts else np.zeros((0, 2), np.float32)
        # path edge from the mask
        m = self.path_mask()
        n = m.shape[0]
        rr, cc = np.where((m > 0.25) & (m < 0.55))
        sel = np.random.default_rng(3).choice(len(rr), min(len(rr), 2500), replace=False) if len(rr) else np.array([], int)
        px = -11.0 + (cc[sel] + 0.5) / n * 22.0
        py = -8.5 + (1.0 - (rr[sel] + 0.5) / n) * 21.0
        out['pathedge'] = np.stack([px, py], axis=1).astype(np.float32) if len(sel) else np.zeros((0, 2), np.float32)
        return out
