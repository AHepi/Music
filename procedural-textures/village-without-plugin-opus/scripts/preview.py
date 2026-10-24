"""Preview scene for checking library assets in isolation."""
import bpy
import math
from mathutils import Vector
import common as C


def preview_scene():
    sc = bpy.data.scenes.get("Preview")
    if sc is None:
        sc = bpy.data.scenes.new("Preview")
    main = bpy.data.scenes["Scene"]
    sc.world = main.world
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1200
    sc.render.resolution_y = 800
    sc.render.resolution_percentage = 50
    sc.view_settings.view_transform = main.view_settings.view_transform
    sc.view_settings.look = main.view_settings.look
    sc.render.image_settings.file_format = 'JPEG'
    for ob in list(sc.collection.objects):
        sc.collection.objects.unlink(ob)
    for ch in list(sc.collection.children):
        sc.collection.children.unlink(ch)
    return sc


def lineup(objs, spacing=0.6, cam_dist=None, cam_h=None, lens=50, out="/tmp/x.jpg", ground=True, row=8, target_z=None, scales=None, samples=24):
    sc = preview_scene()
    col = bpy.data.collections.get("PreviewItems") or bpy.data.collections.new("PreviewItems")
    for o in list(col.objects):
        if o.name.startswith("pv_"):
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            col.objects.unlink(o)
    sc.collection.children.link(col)
    lc = bpy.data.collections.get("Lighting")
    if lc is not None and lc.name not in sc.collection.children:
        sc.collection.children.link(lc)
    xs = []
    maxh = 0.1
    for i, src in enumerate(objs):
        r = i // row
        c = i % row
        inst = bpy.data.objects.new("pv_" + src.name, src.data)
        inst.location = (c * spacing, r * spacing * 1.2, 0)
        if scales is not None:
            inst.scale = (scales[i],) * 3
        col.objects.link(inst)
        maxh = max(maxh, src.dimensions.z * (scales[i] if scales is not None else 1.0))
    if ground:
        me = bpy.data.meshes.get("pv_ground") or bpy.data.meshes.new("pv_ground")
        if len(me.vertices) == 0:
            me.from_pydata([(-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)], [], [(0, 1, 2, 3)])
            m = bpy.data.materials.get("pv_ground_mat") or bpy.data.materials.new("pv_ground_mat")
            m.use_nodes = True
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.06, 0.045, 1)
            me.materials.append(m)
        g = bpy.data.objects.new("pv_ground", me)
        col.objects.link(g)
    ncol = min(len(objs), row)
    nrow = (len(objs) + row - 1) // row
    cx = (ncol - 1) * spacing / 2
    cy = (nrow - 1) * spacing * 1.2 / 2
    dist = cam_dist or max(ncol * spacing, maxh * 2.0) * 1.1
    h = cam_h if cam_h is not None else maxh * 0.9
    camd = bpy.data.cameras.get("pv_cam") or bpy.data.cameras.new("pv_cam")
    camd.lens = lens
    cam = bpy.data.objects.new("pv_cam", camd)
    if cam.name not in col.objects:
        col.objects.link(cam)
    cam.location = (cx, cy - dist, h)
    tz = target_z if target_z is not None else maxh * 0.45
    d = Vector((cx, cy, tz)) - Vector(cam.location)
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    sc.camera = cam
    sc.cycles.samples = samples
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True, scene=sc.name)
    return out
