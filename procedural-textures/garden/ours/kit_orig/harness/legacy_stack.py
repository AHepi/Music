# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Puts the three EARLIER layers (WETNESS: water, JOINTS: dark dull sett joints, RUBBISH: litter) on a scene with their own scripts, using the PINNED COPIES in
# integrate/legacy_pinned/ (so the baseline cannot drift), and REGISTERS them with the kit's chains as stages. The kit never calls their own remove(); Kit.remove() restores
# the snapshots instead.
#   stack = LegacyStack(kit);  stack.apply()          # water layer, joints (road), rubbish with its 3D pieces; dials at the earlier defaults
#   stack.set_state(0.85, 0.5)                        # wetness and puddles for every part (also the rubbish pieces, which the water layer's own set_state does not reach)
#   stack.rubbish_dials(amount=0)                     # change the rubbish dials; stack.pieces(False) hides the separate 3D pieces
# Which parts a set has comes from its legacy block (legacy.order); a set without one (legacy null) has nothing to put on and apply() does nothing.
import os
import sys

import bpy

from . import KIT_ROOT

PINNED_ROOT = os.path.join(KIT_ROOT, 'integrate', 'legacy_pinned', 'earlier')        # the first set of copies (the frozen baseline's)
_MODULES = {}
_ROOT_USED = []


def root_for(settings=None):
    """Which pinned copy of the earlier layers a set uses: the environment variable WK_LEGACY_PINNED (a folder under the kit, for a one-off comparison), else the set's
    legacy.pinned_root (relative to the kit folder; a set that wants the second painter round's fixed copies names integrate/legacy_round2/earlier), else the first set (integrate/legacy_pinned/earlier)."""
    env = os.environ.get('WK_LEGACY_PINNED')
    if env:
        return os.path.join(KIT_ROOT, env)
    legacy = settings.legacy() if settings is not None else None
    if legacy and legacy.get('pinned_root'):
        return os.path.join(KIT_ROOT, legacy['pinned_root'])
    return PINNED_ROOT


def modules(root=None):
    """Imports the pinned copies once (their folders are put on sys.path) and returns {'aw', 'aj', 'ar', 'rl', 'rp', 'jl', 'wl', 'lv'}. Only the first call chooses the folder
    (the earlier scripts keep module-level state), later calls give the same modules."""
    if _MODULES:
        return _MODULES
    PINNED = root or PINNED_ROOT
    _ROOT_USED.append(PINNED)
    for rel in ('tools', 'relief_and_rubbish/setts/tools', 'relief_and_rubbish/rubbish/tools', 'relief_and_rubbish/study/tools'):
        path = os.path.join(PINNED, rel)
        if path not in sys.path:
            sys.path.insert(0, path)
    import apply_wetness_to_set as aw
    import wetness_layer as wl
    import joint_layer as jl
    import apply_joints_to_set as aj
    import rubbish_layer as rl
    import rubbish_pieces as rp
    import apply_rubbish_to_set as ar
    import b02_lighting_and_variants as lv
    _MODULES.update(aw=aw, wl=wl, jl=jl, aj=aj, rl=rl, rp=rp, ar=ar, lv=lv)
    return _MODULES


class LegacyStack:
    def __init__(self, kit):
        self.kit = kit
        self.m = modules(root_for(kit.settings))
        self.applied = False
        self.places = None
        self.state = (0.0, 0.0)
        self.piece_default_dials = {}

    def present(self):
        legacy = self.kit.settings.legacy()
        return bool(legacy and legacy.get('order'))

    def apply(self, pieces=True, rubbish_amount=None):
        """Applies the earlier layers in the set's order (wetness, joints, rubbish), registering each with the kit's chains right after it is on."""
        if not self.present() or self.applied:
            return
        kit, m = self.kit, self.m
        if not kit.prepared:
            kit.prepare()
        scene_entry = kit.settings.scene(kit.scene_id)
        self.places = scene_entry['legacy_places']
        order = kit.settings.legacy()['order']
        for stage in order:
            if stage == 'wetness':
                m['aw'].apply(wetness=0.0, puddles=0.0)
            elif stage == 'joints':
                m['aj'].apply()
            elif stage == 'rubbish':
                m['ar'].apply(places=self.places, pieces=pieces, **({} if rubbish_amount is None else {'amount': rubbish_amount}))
                self.piece_default_dials = dict(m['rl'].DEFAULTS)
                self.piece_default_dials.update(m['rp'].PIECE_DEFAULTS)
            kit.register_legacy()
        kit.add_state_hook(self.set_state)
        self.applied = True

    # ---------------------------------------------------------------- dials and state of the earlier layers
    def set_state(self, wetness, puddles):
        if not self.applied:
            return
        self.state = (wetness, puddles)
        self.m['aw'].set_state(wetness, puddles)
        if 'rubbish' in self.kit.settings.legacy()['order']:
            self.m['ar'].set_state(wetness)

    def joints_dials(self, **dials):
        self.m['aj'].set_dials(**dials)

    def rubbish_dials(self, **dials):
        """The rubbish dials by short name (the earlier defaults for everything not named)."""
        values = dict(self.piece_default_dials)
        values.update(dials)
        self.m['ar'].set_dials(**values)

    def pieces(self, visible):
        self.m['ar'].pieces(visible)

    def look(self, name):
        """The earlier runner's three looks: 'round2' (water only), 'joints' (water and joints), 'rubbish' (all three at the earlier defaults)."""
        if name == 'round2':
            self.m['aj'].set_dials(strength=0.0)
            self.rubbish_dials(amount=0.0)
            self.pieces(False)
        elif name == 'joints':
            self.m['aj'].set_dials(strength=1.0)
            self.rubbish_dials(amount=0.0)
            self.pieces(False)
        else:
            self.m['aj'].set_dials(strength=1.0)
            self.rubbish_dials()
            self.pieces(self.piece_default_dials.get('pieces_density', 1.0) > 0)

    def reset(self):
        """Forgets the earlier scripts' module state after Kit.remove() has put the materials back (their own remove() is never called). The scatter host object is deleted."""
        m = self.m
        host = m['ar']._STATE.get('host')
        if host is not None and host.name in bpy.data.objects:
            bpy.data.objects.remove(host)
        m['ar']._STATE.update({'nodes': {}, 'undos': {}, 'host': None, 'places': None})
        m['aj']._STATE.clear()
        m['aw'].APPLIED.clear()
        self.applied = False

    def piece_count(self):
        return self.m['ar'].piece_count()
