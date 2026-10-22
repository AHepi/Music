# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SMALL STREET WRAPPER round apply_weathering.py: the pit village street's own entry point, for the street copy and for the lockout shot file (the film's own file; both are only
# opened in Blender's memory, never saved). It adds nothing the kit does not have: it names the set and the usual look, puts on, in this order, the three EARLIER layers
# (WETNESS, JOINTS, RUBBISH, the second painter round's pinned copies) and then the kit's eleven layers and the plants, and gives every master dial a plain name.
#
#     blender -b --disable-autoexec <street.blend or lockout.blend> --python-expr "import sys; sys.path.insert(0, '<kit>'); import street_weathering as sw; sw.apply(state='wet')"
#
#     sw.apply(state='wet')                      # the street as drawn for the film: water, joints, litter, then grime, cracks, stains, weeds and moss
#     sw.apply(state='wet', masters={'soot': 0.5, 'growth': 0, 'rubbish': 1})     # any master dial at the start
#     sw.set_master('walls', 0.5)                # the six wall layers together; also 'ground' (dirt, cracks, moss, iron), 'growth', 'earlier' (water, joints, litter), 'all'
#     sw.set_master('soot', 0)                   # or one layer; or 'wetness', 'joints', 'rubbish'
#     sw.remove()                                # all of it off again
# The groups of layers are a convenience of THIS file (which layers belong to which builder); the kit itself only knows layers.
#
# On the HOST (an ordinary python, not Blender) plates() draws the plate pictures of the street and the lockout on the rented machine, with and without the new parts:
#     python3 -I -c "import sys; sys.path.insert(0,'<kit>'); import street_weathering as sw; sw.plates('<out folder>')"
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

SET_ID = 'pit_village_street'
LOOK = 'sooty_1926'
GROUPS = {
    'walls': ('soot', 'runoff', 'foot', 'steps', 'wallcracks', 'wallgrowth', 'paint'),
    'ground': ('dirt', 'groundcracks', 'groundmoss', 'iron'),
    'growth': ('growth',),
    'earlier': ('wetness', 'joints', 'rubbish'),
}


def apply(state='wet', look=LOOK, masters=None, scene_id=None, **kwargs):
    """Puts the street weathering on the open file (the street copy or the lockout shot file). Returns the apply_weathering handle."""
    import apply_weathering as aw
    handle = aw.apply(SET_ID, look, scene_id=scene_id, state=state, **kwargs)
    for name, value in (masters or {}).items():
        set_master(name, value, handle)
    return handle


def set_master(name, amount, handle=None):
    """A master dial by name: 'all', a group ('walls', 'ground', 'growth', 'earlier'), or one layer ('soot', 'iron', 'wetness', 'joints', 'rubbish' ...). 0 = nothing, 1 = the look."""
    import apply_weathering as aw
    handle = handle or aw.current()
    if handle is None:
        raise RuntimeError('the street weathering is not on: call apply() first')
    if name == 'all':
        handle.set_master(amount)
        return
    for key in GROUPS.get(name, (name,)):
        handle.set_master_of(key, amount)


def remove():
    import apply_weathering as aw
    return aw.remove()


def plates(out_folder, looks=('base', 'kit_all'), tag='plates', scenes=None):
    """Host side: draws the plate pictures of the set's test set (main, lockout with and without the props, notice, close road) for each look on the rented machine and
    brings them back under out_folder/<tag>/<scene>/. 'base' = the earlier layers only (the before), 'kit_all' = everything on. Returns {look: {scene: result}}."""
    from apply import settings as settings_module
    from harness import jobs as jobs_module, remote
    settings = settings_module.load_set(SET_ID)
    result = {}
    for look in looks:
        for scene in settings.scenes:
            if scenes and scene['id'] not in scenes:
                continue
            job_dir = os.path.join(out_folder, tag, '_jobs')
            files = jobs_module.write(settings, [look], job_dir, parts=('plates',), scenes=[scene['id']])
            for (scene_id, _), path in files.items():
                local = os.path.join(out_folder, tag, look.replace(':', '_'), scene_id)
                remote_out = f'/workspace/wk_out/{SET_ID}_{look.replace(":", "_")}_{tag}_{scene_id}'
                result.setdefault(look, {})[scene_id] = remote.run_batch(scene['file'], [path], remote_out, local)
    return result
