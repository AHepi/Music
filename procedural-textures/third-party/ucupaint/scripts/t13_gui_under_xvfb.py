"""Plain note: our own test. Runs INSIDE a real (not background) Blender window on a virtual screen with software drawing (no GPU).
It builds a small Ucupaint stack, calls the bake the normal way (no workaround), shows the Shader Editor with Ucupaint's sidebar, saves a
screenshot, and quits."""
import sys, os, time, importlib
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from ucu_common import *
OUT = os.environ['UCU_OUT']; os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'gui_log.txt'), 'w')
def say(*a):
    print(*a); print(*a, file=log); log.flush()
def run():
    try:
        say('GPU backend:', bpy.app.build_options if False else '', 'window count', len(bpy.context.window_manager.windows))
        enable()
        for o in list(bpy.data.objects): bpy.data.objects.remove(o)
        mesh = bpy.data.meshes.new('plane'); mesh.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)])
        uv = mesh.uv_layers.new(name='UVMap')
        for loop, c in zip(mesh.loops, [(0,0),(1,0),(1,1),(0,1)]): uv.data[loop.index].uv = c
        obj = bpy.data.objects.new('UcuTest', mesh); bpy.context.scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj; obj.select_set(True)
        mat = bpy.data.materials.new('Material'); mat.use_nodes = True; obj.data.materials.append(mat)
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')
        bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.55,0.25,0.12), uv_map='UVMap')
        bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap')
        yp, grp = get_yp(mat)
        win = bpy.context.window_manager.windows[0]
        # turn the 3D view area into a Shader Editor and open its sidebar on the Ucupaint tab
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.type = 'NODE_EDITOR'; area.ui_type = 'ShaderNodeTree'
                sp = area.spaces[0]; sp.show_region_ui = True
                for r in area.regions:
                    if r.type == 'UI':
                        try: r.active_panel_category = 'Ucupaint'
                        except Exception as e: say('cannot set tab', repr(e)[:100])
                break
        # now the bake the normal way (the pop-up skipped by the add-on's own preference)
        bpy.context.preferences.addons[MOD].preferences.skip_property_popups = True
        t = time.time()
        r = bpy.ops.wm.y_bake_channels('INVOKE_DEFAULT', width=512, height=512, samples=1, margin=0, fxaa=False, uv_map='UVMap')
        say('normal-way bake (no workaround):', r, '%.2fs' % (time.time()-t))
        say('images:', [(i.name, tuple(i.size)) for i in bpy.data.images])
    except Exception as e:
        import traceback; say('FAILED', repr(e)); say(traceback.format_exc())
    bpy.app.timers.register(shot, first_interval=1.5)
def quit_now():
    bpy.ops.wm.quit_blender()
    return None
def shot():
    try:
        bpy.ops.screen.screenshot(filepath=os.path.join(OUT, 'gui_screenshot.png'), check_existing=False)
        say('screenshot saved')
    except Exception as e: say('screenshot failed', repr(e)[:200])
    bpy.app.timers.register(quit_now, first_interval=1.0)
bpy.app.timers.register(run, first_interval=2.0)
