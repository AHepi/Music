# What this does: builds a few loose things for the near foreground of model-set shots (chapter 2,
# pages 3 and 8), as one .glb with separate named groups a page can copy and place: 'barrels' (three
# iron-hooped barrels, one on its side), 'crates' (a stack of timber crates and two sacks), 'lamp-post'
# (a cast-iron gas lamp with a lit head) and 'cart' (a two-wheeled hand cart). Out of focus at the
# bottom of a tall frame they fill the space the research calls the foreground layer.
#
# Run: /home/user/work/blender-env/bin/python build_props.py OUT.glb

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'props.glb'
mk.reset()

barrel_wood = mk.material(None, name='barrel-wood', colour=(0.24, 0.14, 0.07), roughness=0.75)
iron = mk.material(None, name='iron', colour=(0.035, 0.038, 0.04), roughness=0.45, metallic=0.6)
timber = mk.material('planks', name='crate-timber', roughness=0.85)
sacking = mk.material(None, name='sacking', colour=(0.45, 0.38, 0.27), roughness=0.95)
lamp = mk.material(None, name='lamp-glow', colour=(1.0, 0.8, 0.5), glow=(1.0, 0.72, 0.4), glow_strength=3.0, roughness=0.4)
wheel_wood = mk.material(None, name='cart-wood', colour=(0.3, 0.2, 0.12), roughness=0.8)


def barrel(name, at, lying=False):
    parts = []
    rotate = (math.pi / 2, 0, 0.4) if lying else (0, 0, 0)
    z = 0.075 if lying else 0.09
    parts.append(mk.cylinder(f'{name}-body', 0.075, 0.18, at=(at[0], at[1], z), material=barrel_wood, sides=16, rotate=rotate, bevel=0.004))
    for k, offset in enumerate((-0.06, 0.06)):
        if lying:
            dx, dy = offset * math.sin(0.4), -offset * math.cos(0.4)
            parts.append(mk.cylinder(f'{name}-hoop-{k}', 0.078, 0.014, at=(at[0] - dx, at[1] - dy, z), material=iron, sides=16, rotate=rotate))
        else:
            parts.append(mk.cylinder(f'{name}-hoop-{k}', 0.078, 0.014, at=(at[0], at[1], z + offset), material=iron, sides=16))
    return parts


barrels = barrel('barrel-a', (0, 0)) + barrel('barrel-b', (0.17, 0.05)) + barrel('barrel-c', (0.06, -0.19), lying=True)
mk.group('barrels', barrels)

crates = [
    mk.box('crate-a', (0.22, 0.22, 0.22), at=(0, 0, 0.11), material=timber, bevel=0.008),
    mk.box('crate-b', (0.2, 0.2, 0.2), at=(0.24, 0.03, 0.1), material=timber, bevel=0.008, rotate=(0, 0, 0.15)),
    mk.box('crate-c', (0.18, 0.18, 0.18), at=(0.1, 0.02, 0.31), material=timber, bevel=0.008, rotate=(0, 0, -0.1)),
    mk.cylinder('sack-a', 0.08, 0.2, at=(-0.2, -0.05, 0.08), material=sacking, sides=12, rotate=(math.pi / 2, 0, 0.6), bevel=0.02),
    mk.cylinder('sack-b', 0.075, 0.18, at=(-0.17, 0.12, 0.075), material=sacking, sides=12, rotate=(math.pi / 2, 0, -0.3), bevel=0.02),
]
mk.group('crates', crates)

post = [
    mk.cylinder('lamp-foot', 0.05, 0.1, at=(0, 0, 0.05), material=iron, sides=12, radius_top=0.035),
    mk.cylinder('lamp-column', 0.02, 1.1, at=(0, 0, 0.6), material=iron, sides=10, radius_top=0.016),
    mk.box('lamp-crossbar', (0.16, 0.014, 0.014), at=(0, 0, 1.05), material=iron),
    mk.box('lamp-head', (0.07, 0.07, 0.1), at=(0, 0, 1.17), material=lamp, bevel=0.005),
    mk.cylinder('lamp-roof', 0.065, 0.05, at=(0, 0, 1.245), material=iron, sides=4, radius_top=0.012, rotate=(0, 0, math.pi / 4)),
]
mk.group('lamp-post', post)
mk.marker('lamp-post-light', (0, 0, 1.17))

cart = [mk.box('cart-bed', (0.42, 0.26, 0.03), at=(0, 0, 0.16), material=wheel_wood, bevel=0.004, rotate=(0.12, 0, 0))]
for side in (-1, 1):
    cart.append(mk.box(f'cart-side-{side}', (0.42, 0.015, 0.07), at=(0, side * 0.13, 0.2), material=wheel_wood, rotate=(0.12, 0, 0)))
    cart.append(mk.cylinder(f'cart-wheel-{side}', 0.12, 0.02, at=(0.02, side * 0.16, 0.12), material=wheel_wood, sides=20, rotate=(math.pi / 2, 0, 0)))
    cart.append(mk.box(f'cart-handle-{side}', (0.4, 0.015, 0.015), at=(-0.36, side * 0.1, 0.1), material=wheel_wood, rotate=(0, -0.35, 0)))
mk.group('cart', cart)

mk.finish(OUT, bake=True, bake_size=512, bake_samples=24)
