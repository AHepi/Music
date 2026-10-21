# HOW TO USE the weathering kit (for the three builders and the integrator)

Read this once, top to bottom. It says where your code goes, how a layer goes into a material, how to see your masks, how to draw pictures on the rented machine, and how to run the measures that are your pass lines. The plan (`grime_and_growth/design/13 Plan ...md`) says what to build; this says how to plug it in.

KIT = `proc-work/kits/weathering/` (everything below is relative to it).

## 1. The rules that never bend

* Nothing in your code may contain a street, courtyard or object name, a coordinate or a size copied from a set file. Everything about a place comes from `sets/<id>.json`; everything about a look from `presets/<look>.json`. `python3 -I harness/lint_no_set_names.py` must report zero hits over `apply/ masks/ harness/ walls/ ground/ growth/`. Ordinary words for the thing a layer ages (kerb, flag, sett, gutter, step, pipe, wall, iron) are allowed.
* Never edit a mesh or a material slot. Never call the earlier scripts' own `remove()`. Put a layer in with `kit.apply(...)`, take it out with `kit.remove(...)`. The hook (`apply/hook.py`) does the wiring; you never splice nodes into a material yourself.
* No Bevel, Ambient Occlusion or Pointiness nodes. Edges come from the masks `edge_dist`, `piece_gap`, `step_edge`.
* Amount 0 must give exactly the input. Every mix factor is a product that contains the amount; clamp before dividing so nothing is ever NaN.
* Draw pictures only on the rented machine, through `harness/remote.py` (which uses `runpod/render_client_cached.py` and nothing else). Never read or copy anything in `~/.runpod`. Do not stop or end a machine.
* Do not edit `apply/ masks/ harness/ sets/ presets/`. If you need a mask the foundation does not have, make a private one in your own `local_masks.py` and say so. If you want a look value changed, say which in your report (`REQUESTS.md`).

## 2. What a layer is

A layer is ONE node group (a packaged recipe of node boxes) that sits in a material's chain. Copy `apply/layer_template.py` and read its header: it lists every socket and habit.

```python
from apply import layer_template
layer = layer_template.LayerBase('soot', 'WK SOOT', masks=['sheltered', 'drip', 'wall_dist'])
n, g = layer.n, layer.g             # n makes nodes (math, mix, noise ...), g('Amount') reads a group input by name
# ... build with n.math / n.mix_colour ...; masks are g('M Sheltered'), scale is g('Dot Across')
layer.finish(colour=new_colour, mask=my_mask)    # every output you do not give passes its input through
tree = layer.tree
```

The group's inputs are the **bundle** (Colour, Roughness, Specular IOR Level, Coat Weight, Normal, Metallic, Wet Normal), the masks you declare by name (`M <Name>`; the bus wires them; a mask you do not declare costs nothing), `Wet Mask` and `Puddle Mask`, the scale helper's `Dot Across`, `Dot Along`, `Fade Near`, `Far Blend`, and **one input per dial** in Title Case (`Amount`, `Seed`, `Inflate Limit`, `Fade Start`, `Fade End`, `Wet Follow`, then your own). The outputs are the bundle and `Mask` (your layer's own mask, raw, for debug views and the measures).

**Slots.** A = before the wetness layer (grime, soot: the water then sits on top of it), B = after the joints and wetness (cracks that stay dull), C = after the rubbish. A layer placed after the water layer gets `Wet Mask` and `Puddle Mask`; in slot A they read 0.

**Register it:** your `apply_walls.py` (or `apply_ground.py`, `apply_growth.py`) has `register(kit)`:

```python
def register(kit):
    kit.register_layer('soot', lambda key: build_soot(key), slot='A')    # roles come from the set's apply.soot.roles
```

The harness finds `walls.apply_walls`, `ground.apply_ground`, `growth.apply_growth` by itself (`harness/layers.py`), so your layers appear in every look (`kit_all`, `solo:<key>`).

**Dials.** `apply/dial_table.json` lists every dial of every layer (generated from the plan's list). Read a value with `apply.dials.resolve(layer, look, settings, overrides)`; the look file carries the numbers. Sizes are in PLATE DOTS: a 3-dot crack is `3 x Dot Across` metres wide at that point, never thinner than your minimum, never fatter than `Inflate Limit` times its real size (beyond that fade to the layer's average tone, not to clean).

**Per object.** `wk_seed`, `wk_role_id`, `wk_frame_id`, `wk_zmin`, `wk_zmax`, `wk_<flag>`, `wk_<layer>_amount` and `wk_<layer>_<dial>` are custom properties read with an Attribute node (type Object). Use `n.attr('wk_seed')`. Random numbers come from `wk_seed`, your `Seed` dial and position, never from a name.

## 3. The masks (the bus)

`masks/CONTRACT.md` lists every bus name with its meaning, default, frame and the range it has in each scene's pack. The short version: ground plan masks (`GP`, 4 cm per dot) are looked up by world x and y; wall sheets (`WF`, 2 cm) by position in the wall's own frame; texture-space masks (`TX`) by the material's own picture. You only declare `M <Name>`. A mask the set has not made reads its default.

**See a mask:** `kit.show_mask('moss_site')` (plain light, raw numbers; up to three names `a+b+c` go to R, G, B), `kit.hide_mask()`. In a job: view `mask:<name>`, `plan:<name>` (seen from above over the ground bounds), `layer:<key>` (your layer's own Mask output), `class` (a flat number per role), `depth`, `puddles`, `dirt`.

**Two pictures a render must make (fix round).** A set with the earlier water layer and litter layer gets two more pictures after its pack exists: `python3 -I harness/make_plan_pictures.py SET SCENE WORK_DIR [--only puddles|litter] [--state wet]` (rented machine; about 40 s) draws `plan:puddles` and `plan:litter` and calls `masks/stamp_pack.py`, which writes `above_water` (0 inside a puddle, widened by 3 cm: the growth layer grows nothing under water) and `litter_dist` (metres to the nearest litter piece, from the picture AND the pieces' centres; the growth layer's 5 cm clearance reads it instead of asking every piece). Stamping puddles twice only widens them: put `gp_c.png` and `manifest.json` of the pack back first to change the margin. A set without the earlier layers needs neither.

**Packs.** The mask pictures for a scene are in `masks/packs/<set id>/<scene id>/` (manifest.json says where each lives). They are made once by `masks/reader.py` on the scene (a Blender run, 25 to 80 s) and finished by `masks/make_pack.py` (plain Python). You never rebuild a pack to try your layer; if a mask looks wrong, tell the foundation.

## 4. Drawing pictures (on the rented machine)

One command draws a whole look of the test set and brings the pictures back:

```
python3 -I harness/run_testset.py pit_village_street kit_all OUT_FOLDER --tag r1 --layers soot,runoff [--parts t22,close,plates,masks] [--today]
```

* `today` = the scene as it is; `base` = the earlier layers only (the baseline); `kit_all` = base plus every registered kit layer; `kit:a,b` = base plus those layers; `solo:<key>` = base plus one layer.
* `--layers` names the layers whose own mask pictures you want (`layer_<key>_<label>_<state>.png`, and at plate size `layer_<key>_plate_<camera>.png`). Without it you get the beauty pictures, the class, depth and zones pictures only.
* `--maskviews` adds one picture per key mask and camera (`maskview_<mask>_<camera>`); `harness/mask_debug_sheet.py` turns them into the "where each thing may go" sheet, `harness/pack_pictures.py` draws a pack's ground masks, one wall sheet or the habitat fields.
* The runner sorts jobs so `today` is always first; the remote folder is cleared before every run (a stale picture on the machine can never come back); a picture is skipped only when its job hash matches. Pictures come back as JPG (and the PNG a measure needs), with a JSON of seconds.
* The whole test set (street file and lockout file, base look, plates at 1536 x 2730 and 48 samples) takes about 2.5 minutes wall time including the send and return; the Blender part is 45 to 80 s per scene file. Compare with about 75 to 85 s for ONE small picture on this machine.
* If a call says "no answer from the machine", run `remote.status()` once (`python3 -I -c "from harness import remote; print(remote.status())"` from the KIT folder) and try again. "NO CARD FREE" means draw here and say so. Do not stop or end the machine.
* One run per batch. Do not write a job file with many `look` changes inside one scene if you can avoid it: going back to `today` takes everything off from the snapshots, which is fast, but a look that adds growth pieces makes the next draw slower.

To draw something that is not in the test set (a one-off view, a self-test) use `harness/remote.run_script(blend, script, args, remote_out, local_out)`.

## 5. Your pass lines and the script that measures each

| pass line | script | needs |
|---|---|---|
| P1 sett joints still pass | `python3 -I harness/measure_joints.py SET FOLDER... --out x.json`, then `measure_joints.compare_with_base` | the 22 pictures (PNG kept), `jmask_*`, `puddle_*`, `dirt_*` (from the baseline folder), `layer_*` for the kit's own dots |
| P2 the wet look is kept | `harness/measure_wet.py SET FOLDER... --base harness/baseline/numbers.json` | the 22, `class_*`, `puddle_*` |
| P3 readable at the painter's size | `harness/measure_readable.py SET FOLDER` | the plates and `layer_<key>_plate_<camera>`; the table is `readable` in the look file |
| P4 nothing wrong for 1926 | `harness/coverage.py`, `harness/measure_period.py SET KIT_FOLDER BASE_FOLDER` | `layer_*` pictures; `period`, `forbidden`, `hue_allowed` in the look file |
| P5 not one dark mush | `harness/measure_mush.py` (`compare(kit, base, class, depth)`) | the plates; the baseline plates and maps in `harness/baseline/` |
| P6 no weeds or moss where they must not be | `harness/measure_zones.py SET SCENE --folder ... --pieces pieces.json` | the scene's pack, your `pieces.json` |
| P7 the same drawing time within +30 % | `harness/measure_time.py FOLDER...` | three runs |
| P8 amount 0 changes nothing, P9 reuse, P10 deterministic | `harness/selftests.py` (`dial_zero`, `isolation`, `determinism`, `reuse_smoke`) through `harness/run_selftests.py` | |
| P9 lint | `harness/lint_no_set_names.py` | |

The frozen numbers each is compared with are in `harness/baseline/numbers.json`. The baseline pictures (JPG), the plates (PNG), the class and depth maps are beside it.

`python3 -I harness/test_measures.py` runs every measuring script against made-up pictures with known answers (28 checks); run it after you change a measure, never after your layer.

## 6. The self-tests you call

```python
from harness import selftests
selftests.dial_zero(kit, out_dir, camera, 'soot')           # at Amount 0 the picture is identical (16 bit)
selftests.isolation(kit, out_dir, camera, 'soot', roles)    # a layer alone changes only the dots of its roles
selftests.determinism(kit, out_dir, camera)                 # two draws are identical
selftests.reuse_smoke(kit)                                  # every registered layer goes in and out without a crash, materials restored exactly
```

They run inside Blender; `harness/run_selftests.py` wraps them: `blender -b --disable-autoexec SCENE --python harness/run_selftests.py -- SET SCENE OUT TESTS WxH` (tests: hook, remove, nothing, legacy_nothing, dial_zero, isolation, determinism, reuse, lighting).

## 7. Things that already bit someone

* Image rows in Blender are bottom-up; the packs' PNGs are written top-first so the picture's coordinates match the world. Use `pack.read_png`.
* Negative emission clips to 0 in plain-light views; keep debug values positive.
* A Math node `DOT_PRODUCT` returns its answer on `outputs['Value']`, not the first output.
* A mask that looks identical for every view means the other materials stayed bright: the debug views black out every material but yours (`masks/debug.py`).
* Blender's own Python has no `cv2`; the foundation appends the system one (`masks.ensure_cv2()`). Plain Python scripts (the measures) have it.
* An Attribute node on an object with no such property reads 0 (EEVEE and Cycles alike, tested), so a missing `wk_<layer>_amount` silently switches your layer off on that object; run `kit.report()` to see which materials got the layer.
* The earlier layers are pinned in `integrate/legacy_pinned/`; the baseline must not drift if the protected originals change. Never point anything at the originals.
