# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GROUND LAYERS' DOOR INTO THE KIT. The harness (harness/layers.py) finds this file by itself and calls register(kit), so the four layers appear in every look (`kit_all`,
# `solo:dirt` ...). Nothing here splices a material: the kit's hook and chain do that (kit.apply puts each layer into the materials of its roles, in its slot).
#   register(kit)                       makes the four layers known to the kit: dirt (slot A), groundcracks (slot B), groundmoss (slot C), iron (slot A, straight before the
#                                       Principled BSDF on materials without a water layer); adds the extra dials; copies the doorstep shares of the steps layer; reads the
#                                       look's extra dials (ground/looks_ground/<look id>.json); installs the per-object values service (per-role multipliers, rings)
#   apply(kit, look=None, layers=None, overrides=None)    kit.apply for the ground layers (default: all four)
#   remove(kit, layer=None)             takes one ground layer (or all of them) out; the kit restores the chain
#   set_dials(kit, layer, **values)     changes dials of a layer that is in
#   show_mask(kit, name)                a bus mask in plain light (the kit's own view); hide_mask(kit)
#   show_layer(kit, layer, part=None)   a layer's own Mask output (the whole, or one named part, see PARTS) as plain grey light; returns the undo function
#   PARTS                               {layer: {part name: number}} for the show_part debug dial
# All four layers are optional: a layer whose module is missing or fails to build is reported, never hidden (register returns the problems).
import importlib
import os
import sys
import traceback

from apply import dials, kit as kit_module

from . import dials_ground, ground_common as gc

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = {'dirt': 'A', 'groundcracks': 'B', 'groundmoss': 'C', 'iron': 'A'}
MODULES = {'dirt': 'ground.dirt', 'groundcracks': 'ground.groundcracks', 'groundmoss': 'ground.groundmoss', 'iron': 'ground.iron'}
PARTS = gc.PART_NUMBERS


def _builder(module_name, kit):
    def build(key):
        module = importlib.import_module(module_name)
        return module.build(key, kit)
    return build


def register(kit):
    """Makes the ground layers known to the kit. Returns {'registered': [...], 'problems': {...}}."""
    dials_ground.ensure()
    problems = {}
    look_id = ((kit.look or {}).get('id') if isinstance(kit.look, dict) else None) or (kit.settings.default_look() if hasattr(kit.settings, 'default_look') else None)
    # the doorstep shares: the scrubbed strip on the flags reads the same two numbers as the steps layer
    steps = ((kit.look or {}).get('layers', {}) or {}).get('steps', {}) if isinstance(kit.look, dict) else {}
    shares = {}
    for mine, theirs in (('scrub_whitened_share', 'whitened_share'), ('scrub_scrubbed_share', 'scrubbed_share')):
        if theirs in steps:
            shares[mine] = steps[theirs]
        elif 'steps' in dials.TABLE.layers and dials.TABLE.layers['steps'].row(theirs) is not None:
            shares[mine] = dials.TABLE.layers['steps'].row(theirs)['default']
    if shares:
        dials_ground.set_defaults('dirt', shares)
    for layer, values in gc.look_extras(look_id).items():
        if layer in dials.TABLE.layers:
            dials_ground.set_defaults(layer, {k: v for k, v in values.items() if dials.TABLE.layers[layer].row(k) is not None})
    gc.install_service(kit)
    registered = []
    for key, module_name in MODULES.items():
        path = os.path.join(HERE, module_name.split('.')[1] + '.py')
        if not os.path.exists(path):
            problems[key] = 'file not written yet'
            continue
        kit.register_layer(key, _builder(module_name, kit), slot=SLOTS[key])
        registered.append(key)
    return dict(registered=registered, problems=problems)


def apply(kit, look=None, layers=None, overrides=None):
    keys = [k for k in (layers or gc.LAYER_KEYS) if k in kit.registry]
    return kit.apply(look=look, layers=keys, overrides=overrides)


def remove(kit, layer=None):
    if layer is not None:
        return kit.remove(layer)
    for key in gc.LAYER_KEYS:
        kit.remove(key)
    return True


def set_dials(kit, layer, **values):
    return kit.set_dials(layer, **values)


def show_mask(kit, name, **options):
    return kit.show_mask(name, **options)


def hide_mask(kit):
    return kit.hide_mask()


def show_layer(kit, layer, part=None):
    """The layer's own Mask output as plain light on its materials (everything else black). part: a name from PARTS[layer] or a number; None = the whole. Returns undo()."""
    from masks import debug
    number = PARTS[layer][part] if isinstance(part, str) else (part or 0)
    kit.set_dials(layer, show_part=number)
    undo = debug.show_layer(kit, layer)

    def done():
        undo()
        kit.set_dials(layer, show_part=0)
    return done
