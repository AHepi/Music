# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Finds the layer builders that exist and registers them with a kit. The foundation has only the do-nothing template layers (for tests: 'template_a', 'template_b',
# 'template_c' in slots A, B, C, each able to tint on request); the three builders each add an apply_*.py with register(kit) in their own folder (walls/, ground/, growth/).
# A builder's module is imported if its folder exists; a failure is reported, never hidden.
import importlib
import os
import sys
import traceback

from . import KIT_ROOT

BUILDER_MODULES = ('walls.apply_walls', 'ground.apply_ground', 'growth.apply_growth')


def register_templates(kit):
    from apply import layer_template
    for key, slot in (('template_a', 'A'), ('template_b', 'B'), ('template_c', 'C')):
        kit.register_layer(key, lambda k: layer_template.build_template(k), slot=slot, roles='all')
    return ['template_a', 'template_b', 'template_c']


def register_builders(kit):
    """Imports each builder's apply module that exists and calls its register(kit). Returns ({module: [layer keys]}, {module: error text})."""
    if KIT_ROOT not in sys.path:
        sys.path.insert(0, KIT_ROOT)
    found, errors = {}, {}
    for name in BUILDER_MODULES:
        folder = name.split('.')[0]
        if not os.path.isdir(os.path.join(KIT_ROOT, folder)):
            continue
        before = set(kit.registry)
        try:
            module = importlib.import_module(name)
            module.register(kit)
            found[name] = sorted(set(kit.registry) - before)
        except Exception:
            errors[name] = traceback.format_exc()
    return found, errors
