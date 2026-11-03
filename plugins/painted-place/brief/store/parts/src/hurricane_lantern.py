"""
hurricane_lantern: a 1914-18 tubular hurricane lantern (the kind hung in tents and stood on crates): a squat fuel
tank with its filler cap, two air tubes up the sides curving into the vented top, a glass globe on a brass burner
inside a wire guard, a wick knob, a wire bail handle raised over the top.

Options:
  lit    (default True) a glowing flame on the wick, the globe glowing faintly, and a small warm point light inside
         the glass (in the part's collection, so it moves with the lantern); False: a cold, sooty globe, no light
  seed   small differences: the bail's angle, the globe's soot

About 0.16 m across, 0.29 m high with the bail up. The wick knob and filler cap face -Y. Foot at z = 0.

Made for the store from the lanterns in '50 first pass - render_final.py' and '50 second pass - render_final.py'
(lamp_base, lamp_flame, lamp_cap, lamp_hoop near line 669 / 816, with their glow and `halo`), rebuilt as a whole
lantern with its globe, guard and tubes.
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402,F401
from mathutils import Vector  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'hurricane_lantern',
    'what': 'a tubular hurricane lantern: tank, side tubes, glass globe in a wire guard, bail; lit with a flame and a light',
    'size_m': (0.16, 0.16, 0.29),
    'options': {
        'lit': 'a glowing flame, a faintly glowing globe and a small warm point light inside (default True)',
        'seed': "the bail's angle, the globe's soot (default 0)",
    },
    'materials': ['IRON • soot-black lamp posts', 'MADE • old brass', 'LAMP • honey flame glow',
                  'PART • hurricane_lantern: lit globe glass', 'PART • hurricane_lantern: cold globe glass', 'RUST • rain-aged iron'],
    'source': "the lanterns in '50 first pass' and '50 second pass - render_final.py' (lamp_base, lamp_flame, lamp_cap, "
              "lamp_hoop; lines 669 / 816) and their glow",
    'views': 'reads from every side',
    'trap': "The light is 25 W: in a big scene turn it up (the object 'hurricane_lantern light'); the globe casts no shadow so the light gets out.",
}

PART = 'hurricane_lantern'


def globe_glass(lit):
    """Thin clear glass: mostly see-through, a little gloss; lit, it glows faintly amber from the flame."""
    name = 'PART • %s: %s' % (PART, 'lit globe glass' if lit else 'cold globe glass')
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    out = nodes.get('Material Output')
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.02, 0.018, 0.015, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.12
    clear = nodes.new('ShaderNodeBsdfTransparent')
    clear.inputs['Color'].default_value = (0.95, 0.86, 0.72, 1.0) if lit else (0.62, 0.58, 0.52, 1.0)
    mix = nodes.new('ShaderNodeMixShader')
    facing = nodes.new('ShaderNodeLayerWeight')
    facing.inputs['Blend'].default_value = 0.35
    ramp = nodes.new('ShaderNodeMapRange')
    links.new(facing.outputs['Facing'], ramp.inputs['Value'])
    ramp.inputs['To Min'].default_value = 0.12
    ramp.inputs['To Max'].default_value = 0.7
    links.new(ramp.outputs['Result'], mix.inputs['Fac'])
    links.new(clear.outputs['BSDF'], mix.inputs[1])
    links.new(bsdf.outputs['BSDF'], mix.inputs[2])
    shader = mix.outputs['Shader']
    if lit:
        glow = nodes.new('ShaderNodeEmission')
        glow.inputs['Color'].default_value = (1.0, 0.45, 0.12, 1.0)
        glow.inputs['Strength'].default_value = 1.4
        add = nodes.new('ShaderNodeAddShader')
        links.new(shader, add.inputs[0])
        links.new(glow.outputs['Emission'], add.inputs[1])
        shader = add.outputs['Shader']
    links.new(shader, out.inputs['Surface'])
    mat.diffuse_color = (0.9, 0.55, 0.25, 0.4) if lit else (0.3, 0.3, 0.3, 0.4)
    return mat


def build(collection, seed=0, lit=True, **_ignored):
    rnd = sh.rand(seed, PART)
    body = sh.Builder('hurricane_lantern body', 'IRON • soot-black lamp posts', smooth=True)
    brass = sh.Builder('hurricane_lantern burner', 'MADE • old brass', smooth=True)
    rust = sh.Builder('hurricane_lantern rust', 'RUST • rain-aged iron', smooth=True)

    # tank (fount), its filler cap at the front
    sh.lathe(body.bm, [(0.06, 0.0), (0.074, 0.004), (0.078, 0.012), (0.078, 0.044), (0.072, 0.054), (0.05, 0.061), (0.034, 0.064)],
             segments=28, close_bottom=True, close_top=True)
    sh.lathe(rust.bm, [(0.0785, 0.006), (0.0786, 0.018)], segments=28, close_bottom=False, close_top=False)
    sh.cylinder(body.bm, (0.03, -0.06, 0.05), (0.03, -0.068, 0.062), 0.012, segments=10)
    sh.cylinder(body.bm, (0.03, -0.066, 0.062), (0.03, -0.068, 0.068), 0.014, segments=10)
    # burner, wick knob, globe seat
    sh.lathe(brass.bm, [(0.032, 0.062), (0.03, 0.075), (0.026, 0.082), (0.012, 0.09)], segments=18)
    sh.cylinder(brass.bm, (0.012, -0.024, 0.074), (0.012, -0.05, 0.074), 0.004, segments=6)
    sh.cylinder(brass.bm, (0.012, -0.05, 0.074), (0.012, -0.056, 0.074), 0.012, segments=12)
    sh.lathe(body.bm, [(0.034, 0.076), (0.05, 0.08), (0.05, 0.084), (0.036, 0.084)], segments=24, close_bottom=False, close_top=False)

    # globe, open top and bottom
    glass = sh.Builder('hurricane_lantern globe', globe_glass(lit), smooth=True)
    sh.lathe(glass.bm, [(0.036, 0.084), (0.047, 0.1), (0.054, 0.125), (0.054, 0.15), (0.047, 0.175), (0.034, 0.198)], segments=24,
             close_bottom=False, close_top=False)
    # wire guard round the globe
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0.0))
        pts = [d * r + Vector((0, 0, z)) for r, z in ((0.05, 0.084), (0.062, 0.11), (0.066, 0.14), (0.062, 0.172), (0.048, 0.2))]
        sh.tube(body.bm, pts, 0.0022, sides=5)
    for z, r in ((0.112, 0.0625), (0.168, 0.0625)):
        sh.torus(body.bm, (0, 0, z), (0, 0, 1), r, 0.0022, segments=24, sides=4)
    # vented top (the hood) and its cap
    sh.lathe(body.bm, [(0.034, 0.198), (0.062, 0.207), (0.068, 0.214), (0.062, 0.222), (0.04, 0.238), (0.024, 0.246)], segments=28,
             close_bottom=True, close_top=False)
    sh.lathe(body.bm, [(0.026, 0.244), (0.03, 0.25), (0.03, 0.258), (0.016, 0.263), (0.002, 0.264)], segments=20)
    for k in range(8):
        a = 2 * math.pi * k / 8
        p = Vector((math.cos(a) * 0.052, math.sin(a) * 0.052, 0.226))
        sh.cylinder(rust.bm, p, p + Vector((math.cos(a), math.sin(a), 0.6)) * 0.004, 0.005, segments=6)
    # two air tubes up the sides into the top, a brace between them under the hood
    for side in (-1, 1):
        x = side * 0.07
        pts = [Vector((x, 0, 0.048)), Vector((x * 1.02, 0, 0.12)), Vector((x * 1.02, 0, 0.2)), Vector((x * 0.93, 0, 0.222)), Vector((x * 0.72, 0, 0.236))]
        sh.tube(body.bm, pts, 0.0075, sides=8)
        sh.cylinder(body.bm, (x * 1.02, -0.008, 0.215), (x * 1.02, 0.008, 0.215), 0.005, segments=6)
    # the bail: a wire loop hinged on the tubes, raised over the top, a little to one side
    tilt = rnd.uniform(-0.35, 0.35)
    pts = []
    for k in range(17):
        a = math.pi * k / 16
        p = Vector((-math.cos(a) * 0.074, 0.0, math.sin(a) * 0.07))
        p = Vector((p.x, -math.sin(tilt) * p.z, math.cos(tilt) * p.z)) + Vector((0, 0, 0.215))
        pts.append(p)
    sh.tube(body.bm, pts, 0.0024, sides=5)

    made = []
    for builder in (body, brass, rust, glass):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    for obj in made:
        if obj.name.startswith('hurricane_lantern globe'):
            obj.visible_shadow = False
    if lit:
        flame = sh.Builder('hurricane_lantern flame', 'LAMP • honey flame glow', smooth=True)
        sh.lathe(flame.bm, [(0.002, 0.091), (0.008, 0.098), (0.009, 0.106), (0.006, 0.117), (0.002, 0.126), (0.0005, 0.13)], segments=12)
        obj = flame.finish(collection)
        obj.visible_shadow = False
        made.append(obj)
        made.append(sh.point_light('hurricane_lantern light', collection, (0.0, 0.0, 0.11), 25.0, (1.0, 0.55, 0.22), 0.012))
    else:
        wick = sh.Builder('hurricane_lantern wick', 'RECESSES • near-black blue')
        sh.box(wick.bm, (-0.008, -0.002, 0.088), (0.008, 0.002, 0.095))
        made.append(wick.finish(collection))
    return made
