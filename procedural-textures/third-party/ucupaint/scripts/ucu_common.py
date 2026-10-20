"""Plain note: small helper (our own) used by the Ucupaint test scripts. It turns Ucupaint on in headless Blender and
builds one test plane with a material, so each test script can focus on one question."""
import bpy, addon_utils, sys, time
MOD = 'bl_ext.user_default.ucupaint'

def enable():
    addon_utils.enable(MOD, default_set=True, persistent=False)
    assert MOD in bpy.context.preferences.addons

def fresh_scene(name='UcuTest'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    enable()
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    obj = bpy.context.active_object
    obj.name = name
    mat = bpy.data.materials.new('Material')
    mat.use_nodes = True
    obj.data.materials.append(mat)
    return obj, mat

def get_yp(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'GROUP' and n.node_tree and n.node_tree.yp.is_ypaint_node:
            return n.node_tree.yp, n
    return None, None

def ui_override():
    """Context override giving Ucupaint a (never drawn) 3D viewport area, window and screen. Background Blender has none
    by default, and Ucupaint's bake code asks for bpy.context.space_data, .screen, .window and .area."""
    wm = bpy.context.window_manager
    if not wm.windows:
        return None
    win = wm.windows[0]
    scr = win.screen
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            region = [r for r in area.regions if r.type == 'WINDOW'][0]
            return dict(window=win, screen=scr, area=area, region=region)
    return dict(window=win, screen=scr)
