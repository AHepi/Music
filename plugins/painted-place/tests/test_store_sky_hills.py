"""
What this file does: checks what the closer pass of the Japanese garden (build 58) added to the sky and the far hills.
The low sun: its sun light shines from the bearing and height asked (bearing counted as far_hills' facing), its colour
reddens the lower it stands, the sky glows round it and warms along the horizon either side of it more than above it,
the cloud deck overhead shows only when asked and is lit warmer near the sun than away from it, and the deck needs no
camera far limit (it is in the sky). The mist's light: the lights named are kept out of the mist and still light the
rest, the mist's own light covers the box's top and nothing but the mist sees it, and in a drawn picture a wall behind
sunlit mist comes out darker and bluer once it is used. The far hills: exactly as before unless asked; with
true_height each ridge's highest point stands at the height asked; a saddle dips the ridges at its bearing and leaves
them whole beyond its width; skyline() measures what it says from the eye given; the far limit reaches every hill.
The dusk sky and the haze box are exactly as before. Both tools answer --help.
    python3 tests/test_store_sky_hills.py
"""
import math
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import TOOLS, check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

# the tools' output before this pass (measured on the tools as they were, 6 November 2026): far_hills' (points, the sum
# of their places and hazes) for three calls, and the dusk sky's and the haze's (nodes, links, length of their settings)
BEFORE = {
    'hills default': (10268, 3852562.464), 'hills turned': (2567, -301804.209), 'hills builder': (10268, 4913730.319),
    'sky': (13, 15, 887), 'haze': (5, 4, 295),
}
BUILDER_CALL = dict(centre=(1.0, 20.0), facing=-4, distance=(110, 480), layers=4, height=(100, 340), haze=800,
                    haze_colour=(0.15, 0.165, 0.185), haze_strength=0.32, mist=0.35, trees=1.0, base=0.0, seed=5)


def points(obj):
    bpy.context.view_layer.update()
    co = numpy.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    matrix = numpy.array(obj.matrix_world)
    return co.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]


def refused(call, error=ValueError):
    try:
        call()
    except error:
        return True
    return False


def tree_print(tree):
    values = []
    for node in sorted(tree.nodes, key=lambda n: n.name):
        values.append(node.bl_idname)
        for socket in node.inputs:
            if hasattr(socket, 'default_value'):
                try:
                    values.append(str(tuple(round(v, 4) for v in socket.default_value)))
                except TypeError:
                    value = socket.default_value
                    values.append(str(round(value, 4)) if isinstance(value, float) else str(value))
    return len(tree.nodes), len(tree.links), sum(len(v) for v in values)


def hills_print(made):
    total, count = 0.0, 0
    for obj in made:
        world = points(obj)
        haze = numpy.zeros(len(obj.data.vertices))
        obj.data.attributes['hill_haze'].data.foreach_get('value', haze)
        total += float(world.sum()) + float(haze.sum())
        count += len(world)
    return count, round(total, 3)


def draw(scene, location, bearing, height, size=24, samples=4, lens=24.0):
    """A small picture from `location` looking at a bearing (counted as facing) and height; returns its linear RGB."""
    data = bpy.data.cameras.new('test camera')
    data.lens = lens
    data.clip_end = 5000.0
    camera = bpy.data.objects.new('test camera', data)
    scene.collection.objects.link(camera)
    camera.location = location
    b, h = math.radians(bearing), math.radians(height)
    way = Vector((-math.sin(b) * math.cos(h), math.cos(b) * math.cos(h), math.sin(h)))
    camera.rotation_euler = way.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera                     # the test's own camera (the tools never read one)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'Standard'
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    path = os.path.join(tempfile.mkdtemp(), 'draw.exr')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path)
    pixels = numpy.array(image.pixels[:]).reshape(size, size, 4)[::-1, :, :3]
    bpy.data.images.remove(image)
    bpy.data.objects.remove(camera)
    return pixels


def warmth(pixels):
    mean = pixels.reshape(-1, 3).mean(axis=0)
    return mean[0] / max(mean[2], 1e-6)


# ------------------------------------------------------------------------------------------------ the low sun

def test_low_sun():
    import sky_and_haze
    scene = fresh_scene()
    made = sky_and_haze.low_sun(scene, bearing=30.0, height=10.0, strength=3.0, deck_height=500.0, seed=1)
    check(scene.world is made['world'] and set(made) >= {'world', 'sun', 'direction', 'colour', 'deck_height', 'far_limit'},
          'low_sun did not make the world or return what it made: %s' % (sorted(made),))
    sun = made['sun']
    check(sun.type == 'LIGHT' and sun.data.type == 'SUN' and abs(sun.data.energy - 3.0) < 1e-6, 'the sun light is not a sun of strength 3')
    bpy.context.view_layer.update()
    shines = sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))
    expected = Vector((-math.sin(math.radians(30)) * math.cos(math.radians(10)), math.cos(math.radians(30)) * math.cos(math.radians(10)), math.sin(math.radians(10))))
    check((shines + expected).length < 1e-4 and (made['direction'] - expected).length < 1e-6,
          'the sun does not shine from bearing 30, 10 degrees up: it shines along %s' % (tuple(shines),))
    check(sky_and_haze.sun_direction(90, 0).x < -0.99, 'bearing 90 is not towards -X, as far_hills facing 90 is')
    check(made['far_limit'] == 0.0 and made['deck_height'] == 500.0 and not [o for o in bpy.data.objects if o.type == 'MESH'],
          'the deck is not in the sky itself (a mesh was made, or a far limit is asked)')
    reds = [sky_and_haze.sun_colour(h) for h in (25, 15, 8, 3)]
    check(all(a[1] > b[1] and a[2] > b[2] for a, b in zip(reds, reds[1:])) and all(c[0] == 1.0 for c in reds),
          'the sun does not redden as it sinks: %s' % (reds,))
    check(0.65 < reds[0][1] < 0.85 and reds[-1][1] < 0.3, 'the sun at 25 and 3 degrees is not golden and red: %s' % (reds,))
    check(all(abs(a - b) < 1e-4 for a, b in zip(sun.data.color, made['colour'])), 'the sun light is not the sun\'s colour')
    given = sky_and_haze.low_sun(scene, colour=(1.0, 0.8, 0.6))
    check(tuple(round(c, 4) for c in given['sun'].data.color) == (1.0, 0.8, 0.6), 'a colour given was not used')
    check(refused(lambda: sky_and_haze.low_sun(scene, height=80)) and refused(lambda: sky_and_haze.low_sun(scene, clouds=2))
          and refused(lambda: sky_and_haze.low_sun(scene, deck_height=0)), 'low_sun took a wrong option')
    print('PASS low_sun: the world and a sun light shining from the bearing and height asked, its colour reddening as it sinks, '
          'the deck in the sky with no far limit asked; wrong options refused')


def test_low_sun_drawn():
    """The sky drawn small, looking every way: the glow, the band along the horizon, the deck."""
    import sky_and_haze
    scene = fresh_scene()
    sky_and_haze.low_sun(scene, bearing=0.0, height=6.0, clouds=0.0, seed=0)
    eye = (0.0, 0.0, 1.7)
    at_sun = draw(scene, eye, 0.0, 6.0, lens=50)[8:16, 8:16]       # the middle of each picture: round the sun, and behind
    behind = draw(scene, eye, 180.0, 6.0, lens=50)[8:16, 8:16]
    check(at_sun.mean() > 2.0 * behind.mean() and warmth(at_sun) > 1.5 * warmth(behind),
          'the sky round the sun is not brighter and warmer than behind (%.3f %.2f against %.3f %.2f)' % (at_sun.mean(), warmth(at_sun), behind.mean(), warmth(behind)))
    beside = draw(scene, eye, 32.0, 2.0, lens=50)          # 32 degrees along the horizon from the sun
    above = draw(scene, eye, 0.0, 38.0, lens=50)           # 32 degrees above it
    check(warmth(beside) > warmth(above) * 1.15, 'the glow is not wider along the horizon than upwards (warmth %.2f beside, %.2f above)' % (warmth(beside), warmth(above)))
    plain = draw(scene, eye, 0.0, 70.0, lens=35)
    cloudy_scene = fresh_scene()
    sky_and_haze.low_sun(cloudy_scene, bearing=0.0, height=6.0, clouds=0.6, cloud_size=120.0, seed=3)
    cloudy = draw(cloudy_scene, eye, 0.0, 70.0, lens=35)
    def broken(pixels):                     # how much the sky changes from one dot to the next (a smooth sky hardly does)
        light = pixels.mean(axis=2)
        return numpy.abs(numpy.diff(light, axis=0)).mean() + numpy.abs(numpy.diff(light, axis=1)).mean()
    check(broken(cloudy) > 3.0 * broken(plain) + 1e-5,
          'no cloud deck overhead when asked, or one when not (%.4f against %.4f)' % (broken(cloudy), broken(plain)))
    near = draw(cloudy_scene, eye, 0.0, 22.0, lens=50)
    away = draw(cloudy_scene, eye, 180.0, 22.0, lens=50)
    check(warmth(near) > 1.3 * warmth(away), 'the clouds near the sun are not lit warmer than away from it (%.2f against %.2f)' % (warmth(near), warmth(away)))
    runs = []
    for wind in (0.0, 90.0):                 # straight up, the picture's x is the world's X: the clouds run along the wind
        windy = fresh_scene()
        sky_and_haze.low_sun(windy, bearing=0.0, height=10.0, clouds=0.6, cloud_size=150.0, wind=wind, seed=1)
        light = draw(windy, eye, 0.0, 90.0, size=48, samples=2, lens=20).mean(axis=2)
        runs.append(numpy.abs(numpy.diff(light, axis=1)).mean() / numpy.abs(numpy.diff(light, axis=0)).mean())
    check(runs[0] > 1.2 and runs[1] < 1 / 1.2, 'the clouds do not run along the wind (change across X over Y: %.2f at wind 0, %.2f at 90)' % tuple(runs))
    print('PASS low_sun drawn: brighter and warmer round the sun than behind (%.1f times), the glow wider along the horizon than '
          'upwards, a cloud deck overhead only when asked, drawn out along the wind, warmer near the sun than away from it' % (at_sun.mean() / behind.mean()))


# ------------------------------------------------------------------------------------------------ the mist's own light

def test_mist_light():
    import sky_and_haze
    scene = fresh_scene()
    box = sky_and_haze.haze(low=(-20.0, 5.0, -1.0), high=(30.0, 45.0, 12.0), density=0.007)
    sun = sky_and_haze.low_sun(scene, bearing=0, height=12)['sun']
    fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'AREA'))
    fill.data.energy = 900.0
    scene.collection.objects.link(fill)
    made = sky_and_haze.mist_light(box, keep_out=[sun, fill], strength=1.5, share=0.1)
    light = made['light']
    check(not sun.visible_volume_scatter and not fill.visible_volume_scatter, 'the lights named still light the mist')
    check(all(getattr(o, f) for o in (sun, fill) for f in ('visible_diffuse', 'visible_glossy', 'visible_transmission')),
          'keeping a light out of the mist took it away from the rest')
    check(light.data.type == 'AREA' and light.data.shape == 'RECTANGLE' and abs(light.data.size - 50.0) < 1e-4 and abs(light.data.size_y - 40.0) < 1e-4,
          'the mist light does not cover the box (%s %.1f x %.1f)' % (light.data.shape, light.data.size, light.data.size_y))
    check((Vector(light.location) - Vector((5.0, 25.0, 12.0))).length < 1e-4 and abs(light.data.energy - 1.5 * 50 * 40) < 1e-3,
          'the mist light is not at the box\'s top middle with 1.5 W on each square metre (%s, %.0f W)' % (tuple(light.location), light.data.energy))
    check(light.visible_volume_scatter and not any(getattr(light, f) for f in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission')),
          'something besides the mist sees the mist light')
    check(len(made['twins']) == 2 and all(t.visible_volume_scatter and not t.visible_diffuse for t in made['twins'])
          and abs(made['twins'][0].data.energy - sun.data.energy * 0.1) < 1e-5 and abs(sun.data.energy - 2.4) < 1e-5,
          'share did not leave each light a weak copy only the mist sees (or changed the light itself)')
    plain = sky_and_haze.mist_light(box, keep_out=[sun])
    check(plain['twins'] == [] and abs(plain['light'].data.energy - 50 * 40) < 1e-3, 'by default no copies, and 1 W a square metre')
    check(refused(lambda: sky_and_haze.mist_light(sun)) and refused(lambda: sky_and_haze.mist_light(box, keep_out=[box]))
          and refused(lambda: sky_and_haze.mist_light(box, share=2.0)), 'mist_light took a wrong option')
    print('PASS mist_light: the lights named kept out of the mist only, its own light over the box\'s top that only the mist sees, '
          'weak copies when asked; wrong options refused')


def test_mist_light_drawn():
    """A dark wall behind sunlit mist, drawn small: with the mist's own light it comes out darker and bluer (unveiled)."""
    import sky_and_haze
    pictures = []
    for use in (False, True):
        scene = fresh_scene()
        world = bpy.data.worlds.new('dark')
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.01, 0.012, 0.016, 1.0)
        scene.world = world
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 60.0, 4.0), rotation=(math.radians(90), 0.0, 0.0))
        wall = bpy.context.object
        wall.scale = (80.0, 20.0, 1.0)
        material = bpy.data.materials.new('dark wall')
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.01, 0.012, 0.01, 1.0)
        wall.data.materials.append(material)
        wall.visible_shadow = False           # like the far hills: the sun reaches the mist in front of it
        box = sky_and_haze.haze(low=(-30.0, 3.0, -1.0), high=(30.0, 50.0, 12.0), density=0.01)
        sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
        sun.data.energy = 3.0
        sun.rotation_euler = (-sky_and_haze.sun_direction(0.0, 8.0)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(sun)
        if use:
            sky_and_haze.mist_light(box, keep_out=[sun])
        scene.cycles.volume_step_rate = 4.0
        pictures.append(draw(scene, (0.0, 0.0, 1.7), 0.0, 2.0, size=24, samples=8, lens=50))
    veiled, clear = pictures
    check(clear.mean() < 0.7 * veiled.mean() and warmth(clear) < warmth(veiled),
          'the wall behind the mist is not darker and bluer with the mist\'s own light (%.4f %.2f against %.4f %.2f)'
          % (clear.mean(), warmth(clear), veiled.mean(), warmth(veiled)))
    print('PASS mist_light drawn: behind sunlit mist a dark wall reads %.0f%% as bright, and bluer, once the sun is kept out '
          'of the mist and the mist has its own light' % (100.0 * clear.mean() / veiled.mean()))


# ------------------------------------------------------------------------------------------------ the far hills

def test_far_hills_as_before():
    import far_hills
    import sky_and_haze
    for key, call in (('hills default', dict(seed=2)), ('hills turned', dict(facing=90, layers=1, seed=2)), ('hills builder', BUILDER_CALL)):
        fresh_scene()
        found = hills_print(far_hills.lay(**call)['hills'])
        check(found == BEFORE[key], '%s changed: %s, not %s' % (key, found, BEFORE[key]))
    scene = fresh_scene()
    check(tree_print(sky_and_haze.sky(scene).node_tree) == BEFORE['sky'], 'the dusk sky changed')
    check(tree_print(sky_and_haze.haze(low=(-20.0, -5.0, 0.0), high=(20.0, 60.0, 15.0)).data.materials[0].node_tree) == BEFORE['haze'], 'the haze changed')
    print('PASS far_hills, the dusk sky and the haze are exactly as before unless asked (three calls of the hills, point for point)')


def test_true_height():
    import far_hills
    worst = []
    for seed in range(5):
        fresh_scene()
        made = far_hills.lay(distance=(120, 450), layers=4, height=(60, 220), base=2.0, seed=seed, true_height=True)['hills']
        for k, obj in enumerate(made):
            asked = 60 + (220 - 60) * k / 3.0
            worst.append((points(obj)[:, 2].max() - 2.0) / asked)
    check(min(worst) > 0.99 and max(worst) < 1.01, 'with true_height the ridges stand at %.2f to %.2f of the height asked' % (min(worst), max(worst)))
    fresh_scene()
    old = [points(o)[:, 2].max() / (60 + 160 * k / 3.0) for k, o in enumerate(far_hills.lay(seed=0)['hills'])]
    print('PASS true_height: every ridge\'s highest point stands at %.2f to %.2f of the height asked over five seeds (as before: %s)'
          % (min(worst), max(worst), ', '.join('%.2f' % v for v in old)))


def test_saddle_and_skyline():
    import far_hills
    eye = (0.0, -1.0, 1.7)
    fresh_scene()
    whole = far_hills.lay(facing=0, distance=(150, 150), layers=1, height=(120, 120), seed=4, eye=eye)
    dipped = far_hills.lay(facing=0, distance=(150, 150), layers=1, height=(120, 120), seed=4, eye=eye, saddle=10.0, saddle_width=20.0, saddle_depth=0.4)
    rows_whole = {r['bearing']: r for r in far_hills.skyline(whole, eye, step=2.0, bearings=(-40, 40))}
    rows_dipped = {r['bearing']: r for r in far_hills.skyline(dipped, eye, step=2.0, bearings=(-40, 40))}
    middle = rows_dipped[11.0]['above_eye'] / rows_whole[11.0]['above_eye']
    check(0.5 < middle < 0.72, 'at the saddle the ridge stands at %.2f of its height without it, not about 0.6' % middle)
    outside = [rows_dipped[b]['above_eye'] / rows_whole[b]['above_eye'] for b in (-31.0, -25.0, 35.0, 39.0)]
    check(all(abs(v - 1.0) < 0.02 for v in outside), 'beyond the saddle\'s width the ridge changed: %s' % (outside,))
    check(rows_dipped[11.0]['elevation'] < min(rows_dipped[-25.0]['elevation'], rows_dipped[35.0]['elevation']),
          'the skyline does not rise either side of the saddle')
    reach = max(numpy.hypot(*(points(o)[:, :2] - numpy.array(eye[:2])).T).max() for o in whole['hills'])
    check(reach <= whole['far_limit'] <= 1.3 * reach + 50, 'far_limit %.0f does not reach the hills (%.0f m away)' % (whole['far_limit'], reach))
    fresh_scene()
    exact = far_hills.lay(facing=0, distance=(150, 150), layers=1, height=(120, 120), seed=4, eye=eye, saddle=10.0, true_height=True)
    check(abs(points(exact['hills'][0])[:, 2].max() / 120.0 - 1.0) < 0.01, 'with a saddle and true_height the highest peak is not the height asked')
    # skyline says what a direct measure says, from the eye given, with bearings counted as facing
    rows = far_hills.skyline(exact, eye, step=1.0)
    world = points(exact['hills'][0]) - numpy.array(eye)
    elevation = numpy.degrees(numpy.arctan2(world[:, 2], numpy.hypot(world[:, 0], world[:, 1])))
    check(abs(max(r['elevation'] for r in rows) - elevation.max()) < 0.01 and [r['bearing'] for r in rows] == sorted(r['bearing'] for r in rows),
          'skyline\'s highest elevation %.2f is not the hills\' own %.2f, or its rows are out of order' % (max(r['elevation'] for r in rows), elevation.max()))
    at = far_hills.ridge_height(exact, eye, 10.0)
    near_rows = [r['elevation'] for r in far_hills.skyline(exact, eye, step=1.0, bearings=(9.5, 10.5))]
    check(abs(at - near_rows[0]) < 1e-6 and refused(lambda: far_hills.ridge_height(exact, eye, 170.0)),
          'ridge_height is not the skyline at its bearing, or answered where no hill stands')
    fresh_scene()
    turned = far_hills.lay(facing=90, distance=(200, 200), layers=1, seed=1)
    middle_row = min(far_hills.skyline(turned, (0, 0, 1.7)), key=lambda r: abs(r['bearing'] - 90))
    check(abs(middle_row['bearing'] - 90) < 2.0, 'hills facing 90 are not at bearing 90 in skyline')
    reach = max(numpy.hypot(*points(o)[:, :2].T).max() for o in turned['hills'])
    check(reach <= turned['far_limit'] <= 1.3 * reach + 50, 'far_limit %.0f does not reach the hills (%.0f m away)' % (turned['far_limit'], reach))
    check(refused(lambda: far_hills.lay(saddle=0, saddle_width=0)) and refused(lambda: far_hills.lay(saddle=0, saddle_depth=1.0))
          and refused(lambda: far_hills.skyline([], eye)), 'far_hills took a wrong option')
    print('PASS saddle and skyline: the ridge dips to %.2f at the saddle and is unchanged beyond its width, the skyline rises either '
          'side; skyline measures what a direct measure does, from the eye given, and ridge_height reads it at one bearing; far_limit reaches every hill' % middle)


def test_help():
    for name in ('sky_and_haze', 'far_hills'):
        result = subprocess.run([sys.executable, os.path.join(TOOLS, name + '.py'), '--help'], capture_output=True, text=True, timeout=120)
        check(result.returncode == 0 and 'usage' in result.stdout.lower(), '%s --help failed: %s' % (name, (result.stderr or result.stdout)[-300:]))
    print('PASS sky_and_haze and far_hills answer --help')


def main():
    failed = False
    for test in (test_low_sun, test_low_sun_drawn, test_mist_light, test_mist_light_drawn, test_far_hills_as_before,
                 test_true_height, test_saddle_and_skyline, test_help):
        try:
            test()
        except AssertionError as problem:
            print('FAIL %s: %s' % (test.__name__, problem))
            failed = True
    if failed:
        sys.exit(1)
    print('PASS test_store_sky_hills')


if __name__ == '__main__':
    main()
