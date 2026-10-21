# The weathering kit (one page)

A reusable way to age a painted-film set: soot and grime, wall-foot damp, cracks, stains, rust, weeds and moss. Built for the 1926 County Durham pit-village street, kept free of that street so the Japanese courtyard (and any next set) uses the same code with its own two files.

**How it is split.** Three kinds of file, and only the first two know about a place:

1. `sets/<id>.json` is the **set file**: which objects play which role (road, kerb, wall, iron ...), where the ground is, the cameras and lights, the test set, the earlier layers it already has, and what to leave alone. `sets/pit_village_street.json`, `sets/japanese_courtyard.json`.
2. `presets/<look>.json` is the **look**: how much of each thing (dial values), plus the numbers the measures check it against. `sooty_1926`, `mossy_courtyard_kept`, `mossy_courtyard_neglected`.
3. Everything else is **generic code**: it must pass `harness/lint_no_set_names.py` (zero hits).

**What each folder is.**

| folder | what it holds |
|---|---|
| `apply/` | the core: settings loader, role finder, dials, per-object values, the **hook** that puts a layer into any material without touching meshes or slots, the **chain** that keeps layers in order, the adapter for add-on shaders, the layer template, the `Kit` you talk to |
| `masks/` | the **where-pictures**: ground plan, wall sheets, drip and shelter, shade, dampness, foot traffic, the places moss and weeds may grow, texture space; the packs (`masks/packs/<set>/<scene>/`), the **bus** that hands every layer its masks by name, the scale helper that turns plate dots into metres. `CONTRACT.md` lists every name; `NOT_DONE.md` lists what is missing |
| `harness/` | cameras, lighting rigs A to E as data, the test set (22 lighting pictures, 5 close views, plates), the job writer, the runner (Blender side), `remote.py` (the rented machine, only through `render_client_cached.py`), the measuring scripts for the pass lines, the self-tests, the lint, sheets, and `baseline/` (the frozen numbers and pictures) |
| `integrate/` | the three earlier layers (wetness, joints, rubbish) pinned as copies with hashes, so the baseline cannot drift |

**Use it.**

```python
from apply import kit as wk
k = wk.Kit.load('pit_village_street', scene_id='street')   # reads and checks; changes nothing
k.prepare()                                                  # per-object values and a snapshot of every material; still no picture changes
k.apply(look='sooty_1926', layers=['soot'])                  # a layer goes into the materials of its roles
k.set_dials('soot', film_mult=0.5); k.set_master(0.8)
k.show_mask('moss_site')                                     # see a mask in plain light
k.remove()                                                   # everything off, exactly as it was
```

Drawing pictures: `python3 -I harness/run_testset.py SET LOOK OUT --tag r1 --today` (on the rented machine; a whole look of the test set is about 2.5 minutes). Details, pass lines and what already bit someone: `HOW TO USE.md`.

**The one door (integrator).** `apply_weathering.py` puts the whole thing on any set in one call and `remove()` takes it all off again: `import apply_weathering as aw; w = aw.apply('<set id>', '<look id>', state='wet'); w.set_master(0.8); w.set_layer_master('soot', 0.5); w.remove()`. It puts on the set's earlier layers if the set has them, then the kit's layers in their slots, then the plants. `street_weathering.py` is the pit village street's small wrapper (plain group names: walls, ground, growth, earlier). The recipe that ties it together (every dial, the order, how to switch each thing off, how to add a new set, every measured number) is `15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made.md` in this folder. `integrate/tune_log.md` lists every dial the integrator changed and why. The street uses the second painter round's fixed earlier layers (`integrate/legacy_round2`).

**What the foundation promises.** With no layer on, the picture is identical to the scene as it is (tested on three scenes). With layers on and every master dial at 0, the same. A layer alone changes only its own roles. Taking layers off in any order, or twice, leaves the materials exactly as they were. Two draws of one picture are identical.

**What it does not do.** Nothing is drawn locally (the rented machine draws). Meshes and material slots are never edited. Lichen, graffiti, road lines and other modern things have no layer. See `masks/NOT_DONE.md` for the honest list of what is approximate or missing.
