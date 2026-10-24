# 13 Plan - grime, cracks, stains, weeds and moss for the street (built as a reusable weathering kit)

Written 21 October 2026 by the design helper. **This is a plan only.** Nothing in it has been built or drawn, no painter call was made, nothing was paid, nothing in the film project or in any protected folder was written.
What I did write: this plan; the two settings files (`kits/weathering/sets/pit_village_street.json`, `kits/weathering/sets/japanese_courtyard.json`); three look files (`kits/weathering/presets/*.json`); and three small scripts in `design/work/` (one probe of the street copy, one that made the look files and the dial tables from one list, one that checked that both settings files load and use the same keys).

It is built from four studies, all in this folder tree (`street_wet/grime_and_growth/study/`):
* the period study (what a 1926 County Durham pit village looks like: rules G, C, S, W, M, L; text only, its report file was refused, its rule list is `study/reference_1926/tools/rules_data.py`),
* `11 Pipeline - where new layers hook into the street.md`,
* `12 Painted look - what survives the painter.md` (with the measuring script `painted_look/tool/plate_detail_check.py`),
* `12b Second set - the Japanese courtyard.md` (and its draft `out/c1/japanese_courtyard.draft.json`).

---

## 0. Words used (one line each)

* **Set**: one place built in Blender (the pit village street, the Japanese courtyard). **Scene file**: one saved Blender file of a set (the street copy, the lockout shot file, the courtyard).
* **Plate**: the one picture drawn from the set's camera that the painter repaints. **Painter**: the image model (Flux 3 edit on fal) that repaints it. **Stage**: the film's three.js viewer that projects the painting back onto the 3D set. The audience sees the painting, so a mark only counts if it reads in the plate **and** survives the repaint.
* **Layer**: one packaged weathering recipe made of Blender node boxes (Blender calls it a node group). It sits inside a material and changes colour, shine and relief.
* **Mask**: a grey picture saying *where* something happens (0 nowhere, 1 fully). A **where-picture** is a mask made from the real 3D shapes. **Bus**: the one standard set of named masks every layer reads, so a layer never needs to know which set it is in.
* **Role**: a kind of surface (`wall.masonry`, `ground.flag`, `iron` ...). The settings file says which objects and materials have which role; the kit code only ever says roles.
* **Settings file**: the small file with everything that belongs to one set. **Look** (preset): a file that holds only dial values: "a sooty 1926 coal town", "a kept mossy courtyard". Same code, different settings and looks.
* **Dial**: one named number of a layer. Every layer has a master dial `amount`; 0 means the surface is exactly as it was before.
* **Chain**: the ordered list of layers inside one material, from the photo to the Principled BSDF (Blender's all-purpose surface shader). **Slot**: a named place in the chain (A, B, C; section 5).
* **Plate dot**: one dot of the 1536 x 2730 plate. **Painter dot**: one dot of the picture the painter receives (the plate shrunk to 0.4 to 0.5, so one painter dot is about 2.2 plate dots). **All mark sizes in this plan and in the kit are in plate dots**, the unit the painted-look study measured in.
* **Baseline** (`base`): the street as it is today with WETNESS, JOINTS and RUBBISH on and no new layer. Every comparison is against it.
* **Foundation, builders, integrator**: the five helpers of the shape of the work (section 11).
* **Rented machine**: the RunPod card that draws pictures 50 to 100 times faster than this computer, used only through `runpod/render_client_cached.py`.

---

## 1. The plan on one page

**What we make.** A *weathering kit*: eleven layers that dirty and age surfaces (soot and dust films, run-off streaks, wall-foot splash and damp, whitened or worn doorsteps, painted moss, algae and lichen on walls, cracks, tar, rust, polish, moss in joints) plus one scatter of small 3D weeds and moss cushions. The pit village street is the first user; the Japanese courtyard is next. The code is the same for both; everything that belongs to one set is in a small settings file, and the look (sooty coal town, mossy temple) is a file of dial values.

**How the work runs.** A *foundation* helper first builds what every layer shares: the settings loader and role finder, the hook that puts a layer into any material, the chain that keeps layers in order, the "where-pictures" made from the real geometry (ground plan, wall sheets, drip and shelter, shade, dampness, foot traffic, and the places where moss and weeds may grow), a scale helper that turns plate dots into metres, and the test rig (cameras, the 22-picture lighting set, runner, measuring scripts, sheet maker). Then three *builders* work in parallel in separate folders: **walls** (walls, trims, doorsteps, roofs, chimneys, doors), **ground** (road, flags, kerbs, gutter stones, and all iron), **growth** (3D weeds and moss cushions). Then an *integrator* puts everything into one chain with WETNESS, JOINTS and RUBBISH on the street copy and the lockout file, tunes it against the pass lines, and draws the plates.

**The ten decisions that matter most** (reasons in section 2):
1. Every mark is sized in plate dots and the kit turns that into metres from the camera. A crack is never thinner than 3 dots; a streak never thinner than about 8; anything that would have to be drawn more than six times wider than real fades into an average tone instead.
2. On the street's walls (80 to 90 % of the dots are already under the brightness the film crushes) the pattern is built from **pale and coloured marks**: washed stripes, salt, whitened steps, rust runs, moss lighter than the stone. Dark soot may not push a dot below 0.30 of its clean colour.
3. Chain order: dirt, stains and growth that are a *different dry colour* go **before** the water layer, so the water layer wets them; cracks go **after** water and joints and make themselves dull; painted moss goes after the cracks; RUBBISH stays last (litter lies on top of plants).
4. Every layer reads only the standard masks. Masks are pictures made once from the real shapes (ground plan seen from above, one sheet per wall mesh, photo-space pictures for joints and mortar), never vertex data and never EEVEE's screen-space tricks.
5. Moss and weeds share one "where may it grow" field made in the foundation. The rules *"never on the road crown, never in the traffic lanes, never near the fire, never on the doorstep strip"* live inside that field, so no layer can forget them.
6. Weeds may grow through thin rubbish but not on heaps; moss is smothered a little earlier.
7. The street is lit by dusk lamps with no sun path, so which side of the street is damp and shaded is **declared** in the settings; dampness (water line, low ground, drip lines, wall feet) is the second driver.
8. Nothing street-specific is in kit code. A lint test fails the build if a street name, coordinate or size appears in the code.
9. Every layer has a master dial; 0 gives a picture identical to before (proved by a test, not by hope). Every layer can be switched on and off alone.
10. Pass lines are numbers (section 10): sett joints still 21 of 22; the wet look kept; each element readable at painter size; nothing modern or wrong for 1926; the street not turned into mush (mean brightness of any surface down at most 12 %, no more than 25 % of a surface darkened by a third); no weeds or moss on the crown or lanes (zero); drawing time within +30 %.

**What I could not settle, and say so plainly:** whether the painter keeps moss green (no plate has ever had green); the real 1926 amounts (every "how much" is judgement); which side of the street is shaded (declared, to confirm); whether whitened steps were done in Durham pit rows (medium confidence). Section 13 lists all of it.

---

## 2. Decisions and why

Where the four studies disagreed or left a gap I decided, and here is each decision with its reason.

| # | Decision | Why |
|---|---|---|
| D1 | **One unit: the plate dot (1536 wide).** All dial widths are in plate dots; widths are widened by 0.5 / painter_scale (x1.11 at 0.45, x1.25 at 0.40). The 540 x 960 test pictures use the *plate's* dot angle, so a mark has the same physical size in a small test picture as in the plate. | The painted-look study measured survival in plate dots from real painting pairs. The pipeline study counted "painter dots" (2.2 plate dots) and the period study's table is in painter-size pixels. I checked the three against each other (at 9 m a plate dot is 2.4 mm across the road; a painter dot 5.3 mm; both studies agree once the unit is named). Plate dots are the one calibrated against real paintings. |
| D2 | **Pale-first on dark surfaces.** On walls, stone trim, iron and roofs, marks are pale or coloured; the dark side of soot has a floor of 0.30 of the clean colour (`floor_mult`); the dial `base_lift` exists as a last resort and may only be used if the integrator proves it is needed and says so in the report. | 80 to 90 % of wall, trim, colliery-brick and iron dots are under plate 0.13 (lockout walls 57 to 83 %); the film turns painted 0.10 into 0.015 to 0.03. Dark grime on dark disappears whatever is drawn. Only the wet road (0.195) and pavement (0.20) have room for dark marks. |
| D3 | **Three slots and a fixed order** (section 5): A (before WETNESS), B (cracks, after WETNESS and JOINTS), C (painted growth, after B), RUBBISH last. | Pipeline study 3.4: water must wet a stain; a crack is a narrow dark line the water layer washes out unless it comes after and dulls itself (the joints round proved it: 6 of 22 lightings passed before JOINTS, 21 after); litter lies on plants. |
| D4 | **One chain per material, rebuilt from a snapshot.** The kit records each material's original wiring once, finds its own nodes by a tag (not by remembered references), and always rebuilds from the snapshot in the list's order. The three earlier layers are registered as stages, not edited. Application order equals chain order. | Taking layers off in the wrong order silently cut RUBBISH out of the chain in the pipeline test; wall materials are copied per door layout by the wetness script, so remembered references go stale. |
| D5 | **The mask bus**: pictures from real geometry, three frames (ground plan from above; one sheet per wall mesh; photo space), plus a few per-object attributes. No vertex colours, no EEVEE Ambient Occlusion or Bevel nodes (both fail in EEVEE). | Walls are 32-face boxes with holes (no vertex density); four wall meshes serve 28 houses (a sheet per mesh serves seven houses each); flags and setts exist only in their photos. |
| D6 | **Habitat fields** `moss_site`, `weed_site`, `algae_site`, `lichen_site` are made once in the foundation from the other masks and read by the painted-moss layers (walls and ground) **and** by the 3D pieces. The exclusion rules are inside them. | Moss ribbons painted in joints and moss cushions standing on them must land in the same places; and the pass line "no weeds or moss on the crown or lanes" can then be tested on the field itself (must be zero) as well as on pictures. |
| D7 | **Shade is declared for the street** (`shade.mode: declared`, a direction toward the sun in the settings) and combined with measured sky openness; **dampness** is the second driver. The courtyard uses `year_sun_and_openness` (latitude and north). | The street's two lights are dusk lamps with no north-facing signal; the street is an even dim canyon (openness 0.17 to 0.56), so shade alone would spread moss uniformly. The courtyard has a real sun but shade is weak there too (8.7 % of land under 35 % of the year's sun). |
| D8 | **Who owns what.** Walls: wall, trim, steps, roofs, chimneys, doors and frames, and *painted* moss/algae/lichen on all of these. Ground: road, flags, kerbs, gutter stones, ground-side stains and halos, flat painted moss in joints, tar, polish, and **all iron** (pipes, lamp posts, fire drum, gratings). Growth: the 3D pieces and the scatter engine. | Iron stands on the ground and rusts into it; it shares the drip and height masks. Painted moss on walls was assigned to walls in the brief; painted moss in joints to ground. |
| D9 | **No doubling with RUBBISH.** Ash, coal dust, cinders, mud, straw, paper, leaves and their pieces stay in RUBBISH. The ground layer's grime is a broad, soft film and traffic polish; `film_near_walls` lowers it where RUBBISH already works (wall foot, gutter strip). The integrator measures the total. | Period study: "ash and coal-dust stains are already in the rubbish layer: do not double them"; pipeline study: the rubbish mask covers 30 % of the ground already. |
| D10 | **Weeds and rubbish.** Weeds grow at full density through rubbish thinner than mask value 0.45, thin out to zero at 0.75; moss is smothered between 0.30 and 0.60. The rubbish mask seen from above is made once per scene (`rubbish_heap`). | A seedling can push through a layer of dust and straw but not through a heap of ash or sacks; moss is smothered sooner. The thresholds are my judgement and are dials. |
| D11 | **Period choices.** Lichen: none (coal smoke killed it; `lichen.enabled: false`). Tar patches: yes, capped at 3 % of the road. Whitened or scrubbed doorsteps: 55 % (medium confidence, flagged in the report). Stepped mining cracks: two houses, flagged by name (low confidence). Limewash (S7), bird lime (S9), the roof soot fan (G6 fan): **not built this round** (nothing in the street to put S7 on; S9 and the fan are low value). Never: graffiti, road lines, studs, modern litter, car oil, straight-edged trench patches, buddleia, flower boxes. | Period study priorities and confidence levels. |
| D12 | **Distance behaviour.** Fine detail fades to the layer's *average tone*, never to clean (a wall must not turn clean at 30 m); marks are widened with distance up to `inflate_limit` and then fade; 3D pieces stop at `growth_distance` (18 m) with a 5 m fade, and a painted **far band** (a slightly greener, darker strip along gutter and wall foot) takes over. | Painted-look study: single blades and hairlines are lost; in the far third of the road the painter makes up its own texture, so nothing is planted there. The period study: beyond 15 to 20 m use a band, not plants. |
| D13 | **Amounts are shares of a named surface in the world** (for example "10 % of the joint length in the gutter-side strip"), checked from three cameras, never "a dial value fitted on one camera". | The puddle dial gave 8 % of the road in the main view and 32 % in the notice-corner view. |
| D14 | **The kit never edits meshes or material slots.** Per-object values (`wk_seed`, `wk_frame_id`, role multipliers) are written as custom properties on the objects and read by the shaders. | The courtyard rule (the add-on rebuilds meshes and keeps undo handles); the street's own wall-material copies are made by the wetness script and are not the kit's business. |
| D15 | **Time budget** (all measured in one run on the rented machine, same card, three repeats, best of three): the whole kit may add at most **+30 %** to the plate drawing time of the baseline; shares: walls +8, ground +8, growth +10, foundation overhead (bus, scale) +4. Growth is also capped at 2,500 pieces in one picture. | Pipeline: a plate costs 1.4 to 1.9 s; the existing rubbish pieces already cost about 2 s for 6,400 to 7,200 pieces. |
| D16 | **Plate only and deterministic.** Layers are a pure function of position, object seed and dials; nothing is baked into the glb; the "behind" plate (props hidden) must carry identical weathering outside the props. | The stage shows the painted behind-plate where props hid the ground (71 % of the road in the first wet test). |
| D17 | **Reuse is proven now, not later.** Both settings files already exist in the same format; the foundation runs its reader and hook on the courtyard scene with the draft file; each builder runs its self-test with the courtyard look on the courtyard scene (no crash, dial 0 identical). | "Reusable" is the requirement; the courtyard is the next job. |
| D18 | **Disk and hygiene.** Foundation folder at most 150 MB, each builder 120 MB, integrator 200 MB; pictures as JPG; stop and report if free space falls under 0.9 GB. Rented machine only through the cached client. States start with `today`. | Free disk was 1.9 GB shared by three jobs. |
| D19 | **The painter hand-off is prepared, not run.** The integrator makes the plates and a **chart plate** (a grid of widths and contrasts in grey, rust and green) and the brief sentences below; the paid Paint step decides what to send. | The one cheap test the painted-look study asks for would settle moss and weed colour survival. |

The brief sentences to offer the Paint step (the wording that worked for rubbish in round 2): *"Keep the green moss and the small weeds where image 1 has them: green, not grey-blue, same size and strength. Old sooty brick, no lichen, no flowers, no bright new paint. Keep the pale scrubbed doorsteps and the thin dark lines between the setts where image 1 has them."*

---

## 3. The kit's folder layout

All code in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/`. Plain Python 3 for the reading and measuring, Blender Python for everything that touches Blender. Folder names are the ones in the briefs.

```
kits/weathering/
  README.md                one page, plain words: what the kit is, how to run it on a new set        (foundation, integrator updates)
  apply/                   the core: settings, roles, hook, chain, dials, seeds, public API          (foundation)
    kit.py                 load(set_file, scene_id) -> Kit; Kit.apply(look, layers), set_dials, set_state, show_mask, report, remove
    settings.py            reads and checks a settings file and a look file (unknown role = error; a regex that matches nothing = warning)
    roles.py               finds the objects and materials of every role (name, collection, material, custom property)
    hook.py                puts a layer into ANY material: "wire or plain number" splice, Metallic included, skip lists, glow skip
    adapters.py            the adapter for materials made of shader groups with no Principled box (the add-on's stones and roof)
    chain.py               one ordered list per material, snapshot, rebuild, slots A B C, stages of earlier layers, find-by-tag
    dials.py               dial registry (name, range, default, master), look files -> values, role multipliers
    seed.py                writes wk_seed, wk_role_id, wk_frame_id on objects (stable: from rounded position, not from the name)
  masks/                   the where-pictures and the bus                                              (foundation)
    reader.py              run once per scene: writes the pack (pictures + manifest.json); plain Python + Blender
    ground_plan.py, wall_sheets.py, ledges.py, shade.py, footfall.py, habitat.py, texture_space.py, pack.py
    bus.py                 builds the node group WK MASKS and attaches it to a material (one per material)
    scale.py               builds the node group WK SCALE (plate dots -> metres, distance fade, far blend)
    debug.py               show_mask(name) in a material, plan(name) as a picture from above
    CONTRACT.md            the list of bus names, what each means, its default when a set has none
    NOT_DONE.md            written at the end: anything missing, so the builders can design around it
  harness/                 the test rig                                                                (foundation)
    cameras.py, lighting.py, testset.py, jobs.py, runner.py (Blender side), remote.py (rented machine)
    class_pass.py          draws a flat colour per role so any measure can mask a surface
    legacy_stack.py        puts today's WETNESS, JOINTS, RUBBISH on a scene (pinned copies) and registers them as chain stages
    measure_joints.py, measure_wet.py, measure_readable.py (+ plate_detail_check.py, painter_survival_fit.json), measure_mush.py,
    measure_zones.py, measure_period.py, measure_time.py, coverage.py
    selftests.py           dial_zero(layer), isolation(layer), determinism(), reuse_smoke(layer, set)
    lint_no_set_names.py   fails if kit code names a street/courtyard object, material, coordinate or size
    sheets.py              contact sheets, before/after pairs, mask sheets
    baseline/              the fixed baseline pictures and numbers (JPG + JSON)
  walls/                   builder 1: soot.py runoff.py foot.py steps.py wallgrowth.py wallcracks.py paint.py, walls_common.py, dials_walls.py, apply_walls.py, selftest_walls.py, sheet_walls.py
  ground/                  builder 2: dirt.py groundcracks.py groundmoss.py iron.py, ground_common.py, dials_ground.py, apply_ground.py, selftest_ground.py, sheet_ground.py
  growth/                  builder 3: pieces.py (the piece library), scatter.py (the generic engine), species.json (sizes, kinds, colours as data), dials_growth.py, apply_growth.py, report_growth.py, selftest_growth.py, sheet_growth.py
  integrate/               the integrator: legacy_adapters.py street_run.py plates.py check_pack.py, legacy_pinned.json, tune_log.md
  sets/                    pit_village_street.json   japanese_courtyard.json                            (written in this plan)
  presets/                 sooty_1926.json   mossy_courtyard_kept.json   mossy_courtyard_neglected.json   (written in this plan)
```

Rules for the folders: **a builder writes only inside its own folder** (`walls/`, `ground/`, `growth/`) and its own work folder under `street_wet/grime_and_growth/<name>/`; it never edits `apply/`, `masks/`, `harness/`, `sets/` or `presets/`. If a builder needs a mask that is missing it makes a private one in its own folder (`<part>/local_masks.py`) and says so in its report so the integrator can promote it. A builder may *add rows* to its own look values by sending them to the integrator in its report; the integrator edits `presets/`.

The kit's **work folders** (pictures, notes, scratch) are separate from the code: `street_wet/grime_and_growth/foundation/`, `walls/`, `ground/`, `growth/`, `integrator/`.

---

## 4. The settings file format

One JSON file per set, `sets/<set_id>.json`. **Both real files exist and load**: `pit_village_street.json` (filled in from the measured facts of studies 11 and 12) and `japanese_courtyard.json` (a first draft from study 12b, every guess marked). They use the same keys (the courtyard also carries an optional `palette_from_the_scene`). Notes inside a file are keys that start with an underscore.

| key | holds | street | courtyard |
|---|---|---|---|
| `scenes` | the saved Blender files of the set (id, path, read-only, default camera, extra roles) | the street copy and the lockout shot file | the saved final courtyard |
| `plate` | plate size, painter scale, engine, samples, shadow settings | 1536 x 2730, 0.45 | the same (a guess) |
| `detail` | fade start and end, growth distance, far-band handover (metres) | 12 / 40 / 18 | 14 / 45 / 25 |
| `roles` | the kinds of surface, each found by object name regex, collection, material regex or custom property | 19 roles (ground x5, wall x3, chimney, roof, paint, iron x3, fire, prop, sign, doorway, post) | 14 roles (earth, gravel, existing growth, natural stone, dressed stone, deck, frame, roof tile, roof deck, plaster, cap, bamboo, bark, doorway) |
| `never` | objects and materials no layer may touch (glow and sky are skipped automatically) | windows, glow, sky, interior, moor, notice and sign materials, brass | shoji, glow, hills, leaf masses, lilies, water (own layer later) |
| `apply` | which roles each layer goes on; per-role dial multipliers | e.g. soot on walls, trims, chimneys, roofs; growth on the four ground roles | e.g. soot (as dust film) on plaster, stone, frame, tile; growth on earth, stone, gravel |
| `geometry` | ground roles and picture bounds; which roles are solid; steps; wall-sheet frames; ledge finder settings; water; lowness scale | bounds x -4.5..4.5, y -12..72 (same as the places pictures); 4 cm dots | x -11..11, y -8.5..12.5; water entry (level z -0.12, shore from the ground height) |
| `footfall`, `keep_clear` | shapes (lines, bands, rectangles, polylines, "door to the nearest kerb", "around a role"); weight, width, feather; what each keeps clear | crown and horse walk, wheel tracks, door to kerb, pavement walk; doorstep strip, fire, carts and sacks | stepping-stone path, bridge, veranda front; the raked gravel (no footfall but plants and moss raked out) |
| `shade`, `dampness`, `habitat` | how shade is made (`declared`, `openness`, `year_sun`, or a mix), weights of the dampness parts, weights of the four habitat fields, lichen on or off | declared sun from -x; lichen off | year sun at 35 degrees, north +y (assumption to confirm); lichen on, rough stone only |
| `texture_maps` | the photo pictures of materials (for cavity, joint and cell pictures) and their repeat | setts 2 m, flags 3 m, brick, stone wall | none (the add-on's own Wear Mask is used) |
| `flags` | per-object facts a picture cannot know | two houses with stepped cracks | none |
| `existing_growth` | objects already carrying growth, never doubled | none | the add-on's moss and pebbles |
| `existing_layers`, `legacy` | which earlier layers exist, where their code is, their ports (what they take and give), the states | WETNESS, JOINTS, RUBBISH (pinned copies) | none |
| `hook` | skip rules, adapters for shader-group materials, how seeds are written | none needed | adapter for the add-on's stone and wood groups |
| `cameras`, `lighting`, `test_set` | the cameras (by numbers or "look at"), the five lighting rigs as data, the picture list and the joint pass line | 12 cameras, rigs A to E, the 22-picture set + 5 close views | the photo camera; rigs to be written in the courtyard job |
| `scale`, `plate_brightness_measured` | typical sizes; measured plate brightness per role (so dark or pale marks are chosen from data) | house and kerb sizes; walls 0.08, road 0.195 | gravel 0.41, plaster 0.64, roof tile 0.14 |
| `looks` | the default look and the allowed ones, per-set dial overrides | `sooty_1926` | `mossy_courtyard_kept`, `mossy_courtyard_neglected` |
| `expect` | numbers the kit's own tests check against | crown 8 cm, kerb top 13 cm, ledge heights of cottage 01, 28 doorways, joints 21 of 22 | object and material counts |

**The test that proves the format covers both sets** (the foundation runs it): `settings.validate(both files)`, `roles.find(both)` on both scenes (street: 28 walls, 28 trims, 28 doorways, 5 posts, 1 each of the four ground objects; courtyard: 88 meshes sorted into roles, no object in two roles), and the geometry reader on the courtyard scene with the draft file (ground height, shade from year sun, water edge, existing-growth density) without a single street name in the code. The topics of study 12b section 8 (surface kinds, material hook, many material copies, coordinate frames, ground, water, who walks where, shade, run-off sources, existing growth, colour direction, mark size, litter, seeds, engine, rebuilds) each have a key above; none needed a new code path.

**Looks (presets).** A look file holds only dial values, layer by layer (`presets/sooty_1926.json`). The set names its default look and may override single dials. The dial tables in Appendix A were generated from one list together with the three look files, so they cannot disagree. Presets can be reused by another set: a second mining town would use `sooty_1926` with its own settings file.

---

## 5. The chain: layer order on each material, and how a layer goes in

### 5.1 The bundle, the stages and the three slots

Every surface is described to the Principled BSDF by six values, the **bundle**: Colour, Roughness, Specular IOR Level, Coat Weight, Normal and **Metallic** (rust has to lower Metallic on cast iron 0.6, steel 0.5, brass 0.9; the earlier layers never touched it). Two more things travel beside the bundle where a wetness layer exists: Wet Mask and Puddle Mask.

A **stage** is one layer in the chain. It has a *descriptor* (in the settings, `legacy.stage_ports`, or built into a kit layer): which bundle values it takes, which it gives, which masks it provides. Kit layers take and give all six. WETNESS takes Colour, Roughness, Normal and Wet Normal and gives five (Metallic goes around it). JOINTS and RUBBISH take and give five (Metallic goes around). The chain wires Metallic around any stage that does not carry it.

The slots, with the reason each one sits where it does:

| slot | holds | why there |
|---|---|---|
| **A: before WETNESS** | everything that is a *different dry colour of the same stone*: soot and dust film, run-off streaks, wall-foot splash and damp, doorstep whitening, ground film, polish, water marks, rust marks, tar | Water darkens by the surface's own porosity rule, so a wet street is consistent with no extra "wet look" dial. A layers may change Colour, Roughness and the relief Normal; WETNESS reads all three. |
| **WETNESS** (earlier layer) | water, shine, puddles | unchanged |
| **JOINTS** (earlier layer, road only) | dark dull sett joints that survive wet light | unchanged |
| **B: after WETNESS and JOINTS** | cracks and chips (walls and ground) | A crack is a narrow dark line; water washes narrow dark lines out unless the crack comes after the water layer and makes itself dull (roughness back to 0.9, shine cut 35 %, water film cut 45 %, a real slope the water cannot smooth) |
| **C: after B** | painted moss, algae and lichen; moss ribbons in joints | plants lie on the stone and in its cracks; they follow the Wet Mask themselves (darker, richer green when wet) |
| **RUBBISH** (earlier layer) | litter | litter lies on top of plants |
| the 3D pieces (growth) | not in the chain | separate objects, drawn on top of everything, with their own wet value |

### 5.2 What each family of material gets

Street (the courtyard has no WETNESS, JOINTS or RUBBISH, so A, B and C sit side by side there):

| family (street materials) | chain, in order |
|---|---|
| road setts | `dirt` (A) - WETNESS - JOINTS - `groundcracks` (B) - `groundmoss` (C) - RUBBISH |
| flags, gutter stones, kerbs | `dirt` (A) - WETNESS - `groundcracks` (B) - `groundmoss` (C) - RUBBISH |
| house walls, brick and stone (the four per-layout copies) | `soot`, `runoff`, `foot` (A) - WETNESS - `wallcracks` (B) - `wallgrowth` (C) |
| dressed stone trims (two materials) | `soot`, `runoff`, `foot`, `steps` (A) - WETNESS - `wallcracks` (B) - `wallgrowth` (C) |
| colliery brick, chimneys, slate roof, ridge clay, chimney pots | `soot` (and `foot` on colliery brick) (A) - WETNESS where it has it |
| cast iron, wheel iron, headframe steel, wire rope; lockout iron props and the fire drum | `iron` only, straight before the Principled BSDF (no WETNESS there; the Wet Mask input is 0) |
| painted doors, window frames, fascia | `paint` only, straight before the Principled BSDF |
| yard (WETNESS only), moor, spoil heaps | nothing from the kit |
| glow, glass, sky, interior, brass, the lockout's notice and sign materials | skipped (the `never` list; anything with emission above 0 is skipped automatically) |

Courtyard (first draft): plaster `soot` (as the dust and algae film) - `runoff` - `foot` - `wallcracks` - `wallgrowth`; natural stone through the **adapter** (below) with `runoff`, `wallcracks`, `groundmoss`, `wallgrowth`; gravel and earth `dirt`, `groundmoss`; roof tile `soot`, `wallgrowth`; timber `foot`, `wallcracks`, `wallgrowth`. Glow and leaf materials skipped.

### 5.3 How a layer goes into a material (the hook)

1. Find the Principled BSDF that feeds the Material Output (through a Mix Shader if one follows it). If there is none (the add-on's 46 stone, tile and timber materials are shader groups with no Principled box on the surface), use the **adapter**: build one Principled BSDF from the group's own Albedo, Roughness and Normal outputs, copy its plain numbers (Specular IOR Level 0.4, IOR 1.5 ...) from the Principled box *inside* the group, and carry on. The study proved this on 46 of 46 add-on materials (picture identical in Cycles; one step of 255 on 0.8 % of dots in EEVEE).
2. Skip the material if its emission strength is above 0, it is in the `never` list, or the layer's roles do not include a role of the material.
3. Take a **snapshot** once: for each of the six plugs, what feeds it (a wire) or its plain number, and the names of all nodes that exist. Everything the kit adds afterwards can be removed, and the original wiring restored, from this snapshot alone.
4. For each plug take the wire, **or** make a Value or RGB node holding the plain number (for Normal with no wire: the Geometry node's Normal). This is what lets the hook work on all 41 street materials, all 85 lockout materials and 75 + 46 of the courtyard's 134 (the old hook worked on none of the 41: it looked for a wire on all five plugs and the street leaves Roughness, Specular and Coat as plain numbers).
5. Put the layer's group node in the chain at its slot; wire the stage before it into it and it into the next stage; the last stage into the Principled BSDF.
6. One shared **bus node** (`WK MASKS`) and one **scale node** (`WK SCALE`) per material feed every kit layer in that material; each layer's mask inputs (named `M Sheltered`, `M Drip` ...) are wired by name from the bus.
7. Tag every added node (`node['wk'] = layer`, `node['wk_slot'] = 'A'`). The kit finds its nodes by tag, so copies of a material (the wetness script copies the wall materials per door layout) are found too.
8. Set dial values from the look and write the per-object values (section 5.5).

**Proof, required of the foundation before the builders start:** a do-nothing layer put in slots A, B and C of every non-skipped material of the street copy draws a picture identical to `base` (the pipeline study did it for one slot on all 41 materials: largest difference 0.0 on 32,400 dots), and removing the layers in any order, or twice, leaves the chain correct (the pipeline study found that removing JOINTS first silently cut RUBBISH out).

### 5.4 The order of work inside one Blender run on the street (the integrator's script)

1. Open the scene read-only (never saved); load the settings and look; write the per-object values; load the mask pack.
2. Hook every non-skipped material (constants become nodes) and take snapshots.
3. Apply the earlier WETNESS with its own script (pinned copy). This makes the per-layout wall copies. Register it as a stage.
4. Insert the **A** layers before each WETNESS node (and before the Principled BSDF on materials without one).
5. Apply the earlier JOINTS (road). Register it.
6. Insert **B** then **C** layers before the Principled BSDF (after JOINTS or WETNESS).
7. Apply the earlier RUBBISH last. Register it. (It reads the Wet Mask from the WETNESS node.)
8. Add the growth pieces (a hidden host object with Geometry Nodes). Set the state: `kit.set_state(wetness, puddles)` reaches WETNESS, RUBBISH's pieces and the growth pieces together (the earlier `aw.set_state` does not reach the pieces).
9. To change anything: `kit.remove()` restores every snapshot and deletes every kit and earlier-layer node, then apply again. The earlier scripts' own `remove()` is never called.

States start with `today` (the street exactly as it is). The earlier runner never takes the layers off again, so `today` must come first.

### 5.5 Dials, looks, seeds

* **Master dial.** Every layer has `amount` (0 to 2, default 1). Inside the layer every effect strength is multiplied by it and every mix factor is exactly 0 at 0, with no path that can produce a NaN (NaN times 0 is NaN), so the outputs equal the inputs. The foundation's `selftests.dial_zero(layer)` proves it two ways: on a baked list of 64 sample points in float (must be exactly 0.0 difference), and on an EEVEE picture (identical, or at most one step of 255 on at most 1 % of dots, the courtyard study's measured EEVEE noise floor).
* **Switching.** `Kit.layer_off(key)` removes the stage (same result as `amount = 0`, faster); `Kit.layer_on(key)` puts it back at its slot.
* **Looks.** `Kit.apply(look='sooty_1926')` reads `presets/sooty_1926.json` (dial values per layer), then the set's `looks.overrides`, then any overrides in the call.
* **Per-role values.** The few dials a set varies by role (`apply.<layer>.role_dials`, for example the soot multiple on trims or roofs) are written as object custom properties `wk_<layer>_<dial>` (a multiplier, default 1) and read by the layer through an Attribute node. Material slots are never touched, so a material shared by walls and chimneys stays shared.
* **Seeds.** `wk_seed` = a hash of the object's rounded world position and role, written on every object, so renamed objects (`.001`) and add-on rebuilds do not reshuffle; the earlier layers' name-based Object Info Random is not used. (Whether an Attribute node reads an object custom property equally in EEVEE and Cycles is the first thing the foundation tests; fallback: a hash of the object's origin from the Object Info node.)
* **Cost rules for layer groups** (EEVEE compiles every material variant): at most about 150 nodes per layer, at most three noise or Voronoi nodes per layer, image lookups with Linear interpolation only, no Bevel, Ambient Occlusion or Pointiness nodes (they fail or differ in EEVEE), and relief only as a Bump on the incoming Normal (never a normal map and a height on the same surface).

---

## 6. The masks (the bus)

### 6.1 Three kinds of pictures and a few object values

* **Ground plan (GP).** One set of pictures per scene, seen from above, world x and y, covering the set's ground bounds (the street: x -4.5..4.5, y -12..72, the same as the earlier places pictures, so old and new line up). Normal dots are 4 cm; "fine" pictures 2 cm (edges, steps, which need to be sharp); "coarse" pictures 16 cm (shade, dampness, which are smooth). **Any object can read the ground plan by its own world x and y** (a wall foot reads the ground picture beside it; a lamp post reads the ground it stands on).
* **Wall sheets (WF).** One sheet per wall mesh (meshes shared by many houses share one sheet: four sheets serve the street's 28 houses), in the mesh's own frame: `u` across the front, `v` up from the floor, 50 dots a metre, packed into one atlas. The trim of a cottage reads the sheet of its own walls (`geometry.frames.share_sheet_with`). The shader uses the sheet only where the surface faces the frame (within 25 degrees); elsewhere `frame_valid` is 0 and the bus falls back to the ground-plan and shader versions (gable ends, chimneys, roofs).
* **Texture space (TX).** Pictures in the material's own picture coordinates, made from the photo height pictures the street's materials already use (`texture_maps` in the settings): `tx_cavity` (mortar and stone gaps), `tx_joint` and `tx_cell` (joint lines and a random number per sett, flag or brick). The road's joint picture already exists (`sett_joints_clean.png`); the flags' is new (the flags' joints are only in the photo).
* **Object values.** `wk_seed`, `wk_frame_id` (which sheet), `wk_role_id`, `wk_zmin` and `wk_zmax` (the object's height range, for iron), `wk_stepped` (the per-house flag).
* All pictures are PNG, 8-bit (16-bit for heights), read as Non-Color data, never colour-managed. A scene's whole pack is at most 40 MB and is made by `masks/reader.py`, once per scene (the street and the lockout file each have their own: the lockout adds props). The reader may take up to 15 minutes on this computer; nothing in it is run per picture.

### 6.2 The bus: every mask, in words

A layer reads a mask by **one name** whichever frame supplies it (`Sheltered` is the wall sheet's on a wall and the ground plan's on the ground). Where a set has nothing for a mask the bus gives the default shown.

| name | what it says, in words | made from | frame, size | default | check (the foundation must pass it) |
|---|---|---|---|---|---|
| `ground_height` (internal) | height of the top of the ground at each dot, found by dropping a ray from above onto the ground roles | the evaluated ground geometry | GP, 4 cm, 16-bit | 0 | street: crown 8 cm (+-1) above the channel line at the middle; channel dip 2.5 cm (+-1); kerb top 13 cm (+-1); ground slope 4 degrees (+-0.3) |
| `height` | height of a surface point above the ground: its z minus the ground height at its x and y (wall sheets carry the baked value) | `ground_height` | shader / WF 16-bit | 0 | cottage 01's ground sill reads 0.85 m (+-3 cm) above its pavement |
| `slope` | 0 flat, 1 at 30 degrees: the angle of the ground's gradient over 8 cm | `ground_height` | GP | 0 | street mean about 0.13 |
| `lowness` | how much lower this dot is than the ground within `lowness.radius_m`, over `lowness.scale_m`, clamped 0..1 (1 = the bottom of a gutter or dip: water gathers) | `ground_height` | GP | 0.5 | gutter stones at least 0.7 on 95 % of dots; road middle at most 0.2 |
| `crown` | for the roles the settings name (`geometry.crown.roles`: the street's road), how much higher a dot is than the lowest ground of the same role within `crown.reach_m` (2.6 m), less a 3 cm allowance, over `crown.scale_m` (5 cm), clamped 0..1; 0 on other roles (pavements are raised on purpose) | `ground_height` | GP | 0 | road dots within 1 m of the middle line: at least 0.6 on 90 %; road dots farther than 1.8 m from it: 0.0 on 95 %; none on pavement, kerb or gutter dots |
| `wall_dist` | distance (0 to `wall_reach_m` = 1.275 m) from the dot, 3 cm above the ground, to the nearest surface of the solid roles | BVH queries | GP 4 cm | 1 (far) | equals `places_street_a.png` red within 3 levels on 99 % of dots |
| `prop_dist` | the same to the nearest prop or fire | BVH | GP | 1 | equals places A green (lockout) |
| `inside_corner`, `step_foot`, `vertical_foot` | where things catch: inside corners (many of 12 short sideways rays blocked although the wall is far); the foot of every step; the feet of pipes, posts and standing iron | as the earlier places pictures | GP | 0 | equals places B within 3 levels on 99 % |
| `step_top`, `step_edge` | 1 on a step tread; distance from the tread's outer edge, 0 at the nosing to 1 at 25 cm in | up-facing faces of the step source roles at least 5 cm above the ground within `steps.within_m` of a doorway | GP 2 cm | 0 / 1 | all 28 doors have steps; cottage 01's steps found 0.18 and 0.48 m out |
| `edge_dist` | distance (0 to 0.3 m) to the nearest sharp, outward-pointing edge (angle over 35 degrees) of ground, kerb and step surfaces | mesh edges | GP 2 cm | 1 | at least 95 % of the kerb's top-edge dots under 0.05 |
| `piece_gap` | distance to the boundary between two separate stones of one role (kerb ends, copings) | connected pieces of the mesh | GP 2 cm | 1 | 187 kerb stones found, median 0.92 m |
| `seam_dist` | distance to the line where two ground roles meet (road and gutter, gutter and kerb, kerb and pavement) | a picture of role ids | GP 4 cm | 1 | seams at the known x positions +-4 cm |
| `cover_dist` | distance to the nearest iron cover or grating; 1 if the set has none | role `iron.cover` | GP | 1 | street: all 1 (none modelled) |
| `water_dist`, `above_water` | distance to the water line (0 to 1.5 m); height above the water level | water entry; ground height | GP | 1 / 1 | courtyard: shore where the ground crosses z -0.12 |
| `sheltered` | 0 to 1, rain cannot reach this dot: the share of 24 short rays within 35 degrees of straight up that hit something within reach (1.2 m on wall sheets; `3.5` m in the ground plan, to see under eaves) | ray casts | WF 2 cm; GP 8 cm | 0 | under cottage 01's two sills 0.8 or more; on the sill tops 0.1 or less |
| `drip`, `drip_dist`, `drip_kind` | where run-off lines: `drip` is 1 at a source and falls to 0 across the source's half width plus a margin; `drip_dist` is how far (0 to 1.5 m) below the nearest source; `drip_kind` is which kind (ledge, pipe joint, pipe foot, gutter end, eave, cap, kasa) | the ledge finder (up-facing faces at least 25 cm wide within 0.8 m in front or 0.6 m behind a wall face), the pipe mesh with a collar every `pipe_joint_spacing_m`, roof lowest edges | WF 2 cm; GP for drip lines on the ground under eaves | 0 / 1.5 / 0 | cottage 01: sills 0.85 and 3.55, string course 3.1, eaves course 5.9, lintels 2.68, 2.88, 5.18, steps 0.18 and 0.48 out, pipe at 2.0 across and 0.18 proud (all within 5 cm); then the same finder on all 28 cottages, differences listed |
| `corner`, `reveal` | distance (0 to 0.4 m) to a vertical outward wall corner or an opening's edge; how deep inside an opening's reveal the dot is | edge-angle test; ray depth | WF 2 cm | 1 / 0 | all four edges of every window and door reveal found on cottage 01 |
| `shade` | 1 = deep shade or facing away from the sun; the mix named in `shade.mode`: declared sun direction, sky openness (48 cosine-weighted rays, 40 m), year sun at a latitude, or a weighted mix; openness is stretched over the scene's own min to max so differences show | rays; settings | WF 8 cm; GP 16 cm | 0.5 | street: the declared shaded row's fronts exceed the other row's by at least 0.2 |
| `dampness` | how long a spot stays wet: weights (settings `dampness.weights`) of closeness to a wall foot, drip zone, water, lowness and shade, as a weighted sum clamped 0..1 | the masks above | WF 8 cm; GP 16 cm | 0.3 | wall feet and pipe feet above 0.6; the road middle below 0.2 |
| `footfall` | 0 to 1 how trodden: the settings' shapes (bands, lines, rectangles, polylines, door-to-kerb lines from the doorway empties, wheel tracks) with weight, width and feather | settings; doorway empties | GP 4 cm | 0 | crown and wheel tracks at least 0.8; door-to-kerb lines at least 0.7 from every door; the 28 doors all have one |
| `keepclear` | hard "no plants here": the settings' keep-clear shapes (fire 1 m, doorstep strip 0.5 m, carts and sacks) and where `footfall` is over 0.5 to 0.7; edge 0.2 m | settings; `footfall` | GP 4 cm | 0 | 1 inside 1 m of the fire drum (lockout), on every doorstep strip, in the middle of the road |
| `entry_rand` | a random number 0..1 per entrance, painted over a disc of 1.4 m round each doorway; 0.5 elsewhere | doorway empties | GP 4 cm | 0.5 | one value per door; steps and flags in front of one door agree |
| `existing_growth` | density of growth the set already has (blurred 15 cm) | settings `existing_growth` objects | GP | 0 | courtyard: the add-on's seven moss patches found |
| `rubbish_heap` | the rubbish mask seen from above (0 clean, 1 heap): where litter lies, so growth can avoid it | the earlier runner's `plan` view of the RUBBISH mask | GP 4 cm | 0 | present only for the street and the lockout; made by the foundation's `legacy_stack` |
| `moss_site`, `weed_site`, `algae_site`, `lichen_site` | where each may grow (6.3) | the masks above | WF / GP | 0 | zero wherever `footfall` is 0.6 or more, `crown` 0.7 or more, `keepclear` 0.5 or more (exactly 0.0) |
| `tx_cavity` | hollows of the photo's own relief: a blurred copy of the height picture minus the height, 0..1 (mortar, stone gaps, sett joints) | the photo height pictures | TX | 0 | mortar lines of the brick show; sett joints equal `sett_joints_clean.png` cavity within 0.1 |
| `tx_joint`, `tx_cell` | joint centre-lines; a random number per sett, flag or brick | photo; labelled parts | TX | 0 / 0.5 | flags: 90 % of flags in the photo get their own cell number |
| `frame_valid` | 1 where the wall sheet applies to this dot | the shader | - | 0 | |

### 6.3 The habitat fields (where moss, weeds, algae and lichen may live)

The weights are the settings' `habitat` block. In words:

* `edge_affinity` = the larger of "close to a wall foot" (1 - `wall_dist` / `edge_reach_m`), "close to a seam where a kerb or gutter meets the ground" (1 - `seam_dist` / half that reach) and "close to a stone's foot".
* `footfall_gate` = smoothstep of `footfall` from 0.3 to 0.6; `crown_gate` = smoothstep of `crown` from 0.4 to 0.7; `smother` = smoothstep of `rubbish_heap` between the settings' `rubbish_smother_from` and `_to`; `heap_gate` the same for weeds between `rubbish_thin_max` and `rubbish_heap_min`.
* `moss_site` = (0.45 x `dampness` + 0.30 x `shade` + 0.25 x `edge_affinity`) x (1 - `footfall_gate`) x (1 - `keepclear`) x (1 - `smother`).
* `weed_site` = (0.55 x `edge_affinity` + 0.25 x "close to a seam or to cavity" + 0.20 x (1 - `shade`)) x (1 - `footfall_gate`) x (1 - `crown_gate`) x (1 - `keepclear`) x (1 - `heap_gate`).
* `algae_site` = (0.5 x `dampness` + 0.2 x `shade` + 0.3 x "under a pipe outlet") x (1 - `keepclear`).
* `lichen_site` = 0 unless `habitat.lichen.enabled`; then (0.6 x north bias x `shade` + 0.4 x (1 - `dampness`)) x (1 - `footfall_gate`) on rough stone only.

Because the exclusions are factors, the fields are exactly 0 on the crown, in the lanes, near the fire and on the doorstep strips. That is the first half of pass line P6; the second half is a picture test.

### 6.4 The scale helper (`WK SCALE`) and the size of a plate dot

All marks are sized in plate dots through one helper. Its inputs are set by the runner for each picture from the settings' camera table: **Dot Angle** (radians per plate dot = 2 x tan(half vertical field of view) / plate height in dots, so a 540 x 960 test picture shows the same physical marks as the plate) and **Painter Widen** (0.5 / painter scale). From the Camera Data box it takes the distance. Its outputs:

* `Dot Across` (metres per plate dot across the view at this point) = distance x tan(Dot Angle) x Painter Widen.
* `Dot Along` = `Dot Across` / max(|surface normal . view direction|, 0.12): how long a dot is *along* the way the surface leans away (the road seen at a grazing angle, a wall seen from the side).
* **Mark width** (a small group): given a real width, a minimum in dots, `inflate_limit` and which direction, it returns the drawn width = max(real, minimum dots x dot size) and a `fade` that is 1 while the inflation is within the limit and falls to 0 by twice the limit. Beyond that the mark gives way to the layer's average tone.
* `Fade Near` = 1 minus smoothstep of the distance from `fade_start` to `fade_end`; `Far Blend` = smoothstep of the distance across the settings' `far_band_handover_m` (the pieces stop and the painted far band starts).

**What a plate dot is on the street's main camera** (vertical field of view 40 degrees, height 1.89 m, plate 2730 dots high, so the focal length is 3751 plate dots; the checker tests the helper against this table within 3 %):

| distance ahead | across the road or up a wall (mm) | along the road (mm) | along a house front (mm) | a 3-dot crack running ALONG the street is wide | a 3-dot crack running ACROSS the street is deep |
|---|---|---|---|---|---|
| 4 m | 1.1 | 2.5 | 1.5 | 3 mm | 8 mm |
| 6 m | 1.6 | 5.3 | 2.8 | 5 mm | 16 mm |
| 10 m | 2.7 | 14 | 7 | 8 mm | 43 mm |
| 15 m | 4.0 | 32 | 15 | 12 mm | 96 mm |
| 20 m | 5.3 | 56 | 26 | 16 mm | 170 mm |
| 30 m | 8.0 | 127 | 58 | 24 mm | 380 mm |
| 40 m | 10.7 | 226 | 103 | 32 mm | 680 mm |

So a crack across the street is believable only to about 10 to 12 m, one along it to about 25 m; vertical marks on walls and standing tufts keep full resolution (a 10 cm tuft is 9 dots wide even at 40 m); a mark lying along the wall at 20 m needs about 8 dots x 26 mm = 21 cm to survive. The lockout camera (1.70 m high, 44 degrees, focal length 3378 plate dots) and the notice camera (64.4 degrees) differ: the kit computes it from the camera table, never from this table.

### 6.5 What the earlier layers hand over

Wet Mask and Puddle Mask (from WETNESS, on the 15 materials that have it; 0 elsewhere) are read by kit layers through `wet_follow`. WETNESS's Streak Mask exists on a dry street too (it comes from the builder's typed window numbers); the kit does **not** use it: `drip` replaces it, made from the geometry. The road's joint picture is read through `tx_joint`. The rubbish mask arrives only as the `rubbish_heap` picture.

---

## 7. The layers: what each makes, and the design ideas to use

The dial tables (names, ranges, defaults for the kit, the sooty 1926 look and the courtyard look) are in **Appendix A**. Priority: MUST = needed for the street this round; SHOULD = build after the MUSTs of the same builder; COULD = only if time. Period rule numbers (G1 ...) are those of the period study; "P-L" is the painted-look study.

### 7.1 Walls (builder 1)

* **`soot`** (G1, G3, G6 in part; slot A; MUST). A two-way tonal pattern, not just darkening. The general film is `film_mult` everywhere (85 to 100 % of every wall carries soot); `Sheltered` pulls toward `sheltered_mult` (under sills, eaves, in reveals, behind pipes); rain-washed areas (`washed_share` of the wall, found from slow noise x exposure x (1 - shade)) go to `washed_mult`, the *light side* of the pattern; mortar hollows (`tx_cavity`) are darker (soot sits in hollows first); colour is pulled 30 % toward grey; mottling 0.3 to 2 m; the line between washed and sheltered is crisp under a sill. No dot goes below `floor_mult` of its clean colour. Chimney stacks `stack_mult`, roofs `roof_mult`. Reuse as ideas only: the brick GRIME soot-cloud numbers (cloud 1.8 times taller than wide, run streaks four times taller). Target: patches 15 dots or wider, contrast 0.06 (0.04 minimum).
* **`runoff`** (G2, S2 on the wall; slot A; MUST). Streaks from `Drip`, `Drip Distance` and `Drip Kind`. Width = max(real source width plus margin, `width_dots` x `Dot Along`) up to the inflate limit; length `drip_length` x `length_mult` x a per-source random; ragged sides by a downward-stretched noise; one edge soft, one crisp. On sooty walls the streak is a **paler washed stripe with dark tide-lines**, not a black stripe (`tone` -0.5); on pale plaster dark grey-green (`tone` +0.7). Sources of kind pipe joint or bracket tint toward rust (`iron_rust`); `leak_share` of downpipes carry a long heavy streak; a splash fan at every pipe foot. Reuse the WETNESS DRIP group's idea (centre, half width, top, length) but feed it from the picture, not from typed numbers. Target: 8 to 15 dots wide, contrast 0.04 to 0.05; **this is the element that suits the walls best** (vertical marks survive the slanted view).
* **`foot`** (G4, S5, C5; slot A; MUST). The splash band: `splash_height` tall, darkest at the ground line (x 0.45 to 0.60), a ragged top edge with fingers 5 to 15 cm tall, heavier at pipe feet (`pipe_foot_boost`), brown-grey. The damp tide-mark on `tide_share` of the house lengths (per-house random from the object seed, in runs of 3 to 8 m), ragged top, slightly greener and darker, with white salts along its top (`salt_bloom`). Eroded mortar and flaked bricks in the lowest 0.6 m (`tx_cavity` plus a Bump of 3 to 10 mm). Target: the band reads at 0.04 contrast over at least 15 dots tall at 6 to 13 m. The wet band from WETNESS is already 0.9 m tall on wet plates; the kit's dry splash must not stack into mush (budget in section 10).
* **`steps`** (S8, C4; slot A; MUST, flagged medium confidence). Found by `Step Top` and `Step Edge` at the surface's own world position (the steps are part of each trim mesh). Per door, `entry_rand` below `whitened_share` gives whitened (a 4 to 10 cm frame along nosing and riser, widened to `frame_dots` at distance), below `whitened_share` + `scrubbed_share` gives scrubbed pale, otherwise plain; boots grey the centre; a worn dish of `dish_depth` as a Bump faded with distance; a chipped nosing from `edge_dist`; polish on the worn centre. White goes grey when wet. The pale strip on the *flag* in front belongs to ground `dirt` (`scrub_strip`) and reads the same `entry_rand`.
* **`wallgrowth`** (M2, M4, M5, L1; slot C; SHOULD). Painted moss, algae and lichen on walls, trims, caps, plaster and roof tile, read from `moss_site`, `algae_site`, `lichen_site`, `drip` and `height`. Use the **method** of the slate MOSS layer (`recipes/slate_layers/layers/moss.py`; it cannot be used as it is, it reads a slate layout): flat painted steps in `tone_steps` olive tones, clumps stretched `clump_stretch` taller than wide with a fringe of down-pointing teeth, a lighter rim and a shadow under the upper edge, a Bump faded with distance; and its four rules (own seed, amount 0 means exactly nothing, no peeking at other layers, prove independence). Patches `patch_dots` wide or more, **lighter than the stone and above `brightness_floor`**, saturation 0.45 or more, hue 85 to 120 degrees (painted-look section 11). Algae is a thin dark green-black film at drips and shaded feet. Lichen: pale tan discs and rings in colonies, **off in the street** (`lichen_amount` 0: the 1926 smoke killed it), on in the courtyard. Moss follows the Wet Mask (darker, richer green when wet, never below plate 0.12).
* **`wallcracks`** (C5, C6, C7 in part; slot B; SHOULD). Stepped cracks at about 45 degrees through the mortar joints (`tx_cavity` cells) on the houses with `wk_stepped`; corner and opening-corner cracks from `corner` and `reveal`; chips at wall corners; plaster map cracks (courtyard); spalled patches near the foot. A crack is a dark line widened to at least `crack_dots` (3 dots needs contrast 0.11), a pale dust lip, a real slope of `slope_mm`, dull, faded by `near_only`. Reuse as ideas and numbers: the wood CRACKS layer (one crack per cell narrowing to a point, pale lip #9c7350, crack #120d0b) and DAMAGE's reach rule (chips where the distance to the edge is under "how far in" times a noise). A few, never a net: "many short cracks read as noise" (P-L).
* **`paint`** (G5, C7; slot A; COULD). Door and frame paint darkened to 0.70 to 0.85, flakes along the grain, scuffs kicked up the lowest `door_scuff` of every door to bare grey wood, a hand-grease patch at the latch, lost gloss.
* **Not built this round:** `lime` (S7: nothing in the street to put it on), bird lime (S9), the roof soot fan (G6: roofs are 1 % of the view), roof moss in the street.

### 7.2 Ground (builder 2)

* **`dirt`** (G, S1, S3, S6, S8 strip; slot A; MUST). (1) A broad soft film of soot and dust, 0.5 to 3 m patches, strongest in quiet places (not on the crown or trodden lanes), at most one third darker, on at most `film_max_share` of a surface, lowered by `film_near_walls` where RUBBISH works. (2) **Traffic polish**: worn lanes (high `footfall`) are lighter and smoother (the road and pavement have the brightness room for this; ground can go dark, walls cannot). (3) Dried puddle rings and tide lines in low spots. (4) Rust stain on the flag round the foot of iron posts and pipes (`vertical_foot`, 10 to 25 cm). (5) The rust bleed ring at the foot of the fire drum (the ash ring is RUBBISH's). (6) **Tar**: patches over lost setts (sited by wheel bands x seams x covers, scalloped irregular edges, never straight; a speckle of pale chippings; glossy new tar, matt weathered, near black wet), at most `tar_max_share` of the road; splashes at the kerb foot. (7) The pale scrubbed strip in front of whitened or scrubbed steps. No ash, coal dust, cinders, mud, straw, paper or leaves (RUBBISH).
* **`groundcracks`** (C1, C2, C3; slot B; MUST). Flags (from `tx_cell`, a random number per flag): fine cracks on 11 %, broken in two or three with a 2 to 6 mm gap on 3 %, tilted or sunk on 4 % (one edge 5 to 15 mm proud: a real Bump and a dark shadow line), a chipped corner on 7 %; sited near the kerb (`edge_dist`), the street ends and gaps between houses, covers (`cover_dist`) and wheel mounts. Kerbs (`edge_dist`, `piece_gap`): scalloped edge chips 2 to 8 cm long on 28 % of the length, 1 stone in 15 cracked, pale wheel scuffs, open dark joints. Setts (`tx_cell`, `tx_joint`, `seam_dist`, wheel bands): 4 % disturbed (tilted, sunken oval patches 0.4 to 1.2 m, missing setts as a dark rectangle with dust fill), 14 % of joints open and dark. Cracks drawn at least `crack_dots` wide, faded by `near_only` (15 m), dull. **Guard:** sett joints never exceed `max_contrast` 0.75 (a harsh black grid is a fault), and JOINTS' pass (section 10, P1) must hold.
* **`groundmoss`** (M1, M2, M3; slot C; MUST). Painted flat moss in joints and at edges away from traffic, from `moss_site` x `tx_joint`: a ribbon of `ribbon_m` (1 to 3 cm real, drawn at least `ribbon_dots` wide near the camera), broken into pieces of `broken_len`, covering `joint_share` of the joint length in the best gutter-side strip; algae fans under every downpipe outlet and gully (`algae_fan`); 0 to 2 liverwort patches (`liverwort`); and the **far band** (`far_band`, `Far Blend`): beyond the pieces distance, a slightly greener, darker strip along the gutter and the wall foot instead of single plants. Moss is mid-value green *lighter than the stone* (plate brightness `moss_value` about 0.36) but never covers more than the joint's own width plus its halo, so the joint grid still reads; the integrator checks P1 with and without moss dots.
* **`iron`** (S1, S2 on the iron itself, S3, S4; slot A; MUST; one layer for every iron object: pipes, lamp posts, fire drum, rails, gratings, wheel and headframe steel). Rust in the lowest `rust_height` of posts (20 to 40 % of the paint chipped back, vertical streaks 1 to 3 cm wide, a ring at the base flange), rings at pipe collars every `collar_spacing`, a dark wet streak at the pipe shoe; the fire drum: 60 to 80 % rust and old paint, heat-blued scale, soot rim and a halo above the vent holes; rust **lowers Metallic** by `metallic_drop`; paint kept black or dark green; object-space height from `wk_zmin` and `wk_zmax`. Iron is 4 % of the main view.

### 7.3 Growth (builder 3)

See section 8.

### 7.4 What is common to every layer (the builders' checklist)

Master dial `amount`; the six common dials; mask inputs by bus name; Bump relief faded with `Fade Near`; fine colour fading to the layer's *average tone* (a parameter `mean_effect` the layer supplies), never to clean; widths through the mark-width helper; wet behaviour through `wet_follow`; debug outputs `Mask` and named parts; per-object values read through Attribute nodes; no set names or numbers in code; ≤ 150 nodes; a recipe note in plain words in the builder's work folder.

---

## 8. The 3D pieces (builder 3: weeds and moss cushions)

**What.** Small separate 3D pieces scattered by Geometry Nodes (the way the rubbish pieces are; plate only, not in the glb): they catch light, throw a tiny shadow and stand up, so they keep their resolution where painted flat marks do not (a 10 cm tuft is about 9 plate dots wide at 40 m). The painted-look study: tufts of 5 plate dots or wider at contrast 0.08 come back as inked blobs; single blades are lost; hundreds of minimum-size marks read as noise. So: **a few clusters, not hundreds of tufts**, in the first `distance` (18 m) of the camera only.

**The piece library** (`growth/pieces.py`, sizes in `growth/species.json` as data; every piece 40 to 200 faces with ragged outlines, bent blades and a random lean; the first rubbish pieces "looked like gems and matchsticks" because they had too few facets):

| kind | size in May 1926 (period study W1 to W5) | share of weed pieces |
|---|---|---|
| meadow-grass tuft (some flowering heads 5 to 7 cm, some dead and straw-coloured) | 3 to 12 cm tall | 0.40 |
| pearlwort cushion | 2 to 6 cm across | 0.20 |
| dandelion rosette (a few in flower or seed-clock) | 8 to 20 cm across | 0.12 |
| greater plantain rosette | 6 to 15 cm | 0.08 |
| groundsel | 5 to 20 cm | 0.08 |
| chickweed mat | 10 to 30 cm | 0.08 |
| shepherd's purse rosette with spikes to 20 to 30 cm | 5 to 10 cm | 0.04 |
| ivy-leaved toadflax trail on damp mortar (0 to 2 clumps in the whole street) | 10 to 30 cm | by `toadflax_clumps` |
| **moss cushion** (domed, lumpy, 1 to 3 cm across, 0.5 to 1 cm high; strung 2 to 4 along a joint) | cushions share set by `cushions_amount` | - |
| liverwort lobe strips | flat, painted only (ground `groundmoss`) | - |

Left out (period study): buddleia, rosebay willowherb stands, pellitory-of-the-wall, any lichen, any flower box.

**Where and how many** (the period rules): sited by `weed_site` (weeds) and `moss_site` (cushions) multiplied by the hard `keepclear`; `weed_cover` 0.5 to 2 % green cover of the ground inside the pieces distance (default 1.0 %); 3 to 8 % of the gutter-side joint length with a visible tuft (`gutter_tuft_share`); 2 to 5 % of wall-foot length with a plant (`wall_foot_share`); none on the crown, in the wheel bands, on the walking line to each door, within 1 m of the fire, on the doorstep strip. Poisson-disk spacing `min_spacing` between pieces of one kind. Ceiling `max_pieces` 2,500 in one picture (drawing-time budget +10 %): when the estimate exceeds it, density is scaled down, never the zones.

**Next to the rubbish (decided).** Weeds grow at full density through rubbish thinner than `rubbish_thin_max` (0.45), thin out linearly, and stop at `rubbish_heap_min` (0.75); moss cushions stop between 0.30 and 0.60. Both read the `rubbish_heap` picture. The integrator checks that at most 3 % of weed pieces stand within 5 cm of a rubbish piece.

**Distance and size.** The scatter reads the **picture's camera position** (the runner sets it per picture) and lays pieces only within `distance`, with a `distance_fade` fall-off; pieces widen with distance by the mark-width rule up to the layer's `inflate_limit` (the growth builder should set a lower value than the common 6, about 3, in the look, because standing marks keep their resolution); beyond the distance the painted `far_band` carries the tone. Wet: a `WET` value on the piece materials (set by `kit.set_state`, like RUBBISH's pieces) makes leaves richer green (colour x `wet_dark`) and a little glossier, no coat. Colours: the table in Appendix A (low-saturation olive-green, plate brightness 0.17 to 0.33 survives the film curve; **moss and weed start values are lighter and stronger than the finished look**, hue 85 to 120 degrees, saturation 0.45 or more, because the painter weakens colour to 0.2 to 0.9 times).

**The engine is generic** (`growth/scatter.py`): a mask picture channel, a piece set, density per kind, target roles, zones, wet value, seed, a `realise_instances` option for sets with instanced surfaces. The courtyard's piece sets (moss cushions on stones, grass at the gravel edge, later leaves and pine needles) are data in a look or in `species.json`, not new code. **It must also run on a non-ground target** (a tilted box with a picture mask) so the courtyard's stones are not a surprise.

**Report.** `growth/report_growth.py` writes `pieces.json` (position, kind, size of every piece of a picture), used by the zone test (P6), the rubbish-proximity test and the count budget.

---

## 9. The test set and the harness (built by the foundation)

### 9.1 The pictures

| set | pictures | size and samples | notes |
|---|---|---|---|
| **Lighting set T22** (the earlier 22) | main: A dry, wet, heavy; C dry, wet; D dry, wet; E dry, wet, heavy (10). close_road: A dry, wet, heavy; C, D, E wet (6). lockout: B dry, wet, heavy; C, D, E wet (6) | 540 x 960 at 16 samples; close 640 x 480 at 24 | lights A to E are rig data in the settings (dusk lamps; brazier glare; low side light; flat overhead; light from behind). States: dry 0 / 0, wet 0.85 / 0.5, heavy 1.0 / 0.8 (Wetness / Puddles). |
| **Five close views** (new) | wall foot (`wall_close`), downpipe (`pipe_close`), doorstep (`doorstep_close`), gutter (`gutter_close`), cracked flag (`flag_close`, re-aimed at the ground-cracks layer's own strongest flag crack in the first 12 m) x lights A and E x dry, wet, heavy = 30 | 960 x 720 at 24 | `wall_lamp`, `left_gutter_close`, `drum_close` (lockout) are kept as extras |
| **Plates** | main A wet; lockout B wet (with props, and "behind" with the props hidden as in `painter_round_2/plate/no_props_hidden_objects.txt`); notice A wet; close_road plate | 1536 x 2730 at 48 (close 1920 x 1440) | EEVEE, ray tracing on, shadow rays 4, steps 16; states start with `today` |
| **Chart plate** (for the Paint step) | a grid of widths (2, 3, 5, 8, 12, 20 dots) and contrasts (0.03, 0.05, 0.08, 0.12) in grey, rust and green on the street's ground and wall surfaces | 1536 x 2730 | made by the integrator; free to draw; not sent |

Every picture is drawn in the looks `today` (the street as it is), `base` (WETNESS, JOINTS, RUBBISH: the baseline), `kit_all`, and `solo:<layer>` (base plus one kit layer) so a builder can see its own layer alone. About 22 x 2 + 30 x 2 + 13 solo series on the main wet picture is a few minutes on the rented machine.

### 9.2 The runner and the rented machine

* **Blender side** (`harness/runner.py`, run as `blender -b --disable-autoexec FILE --python runner.py -- JOBS.json OUT`): opens the scene file read-only (never saved), loads the settings, writes per-object values, applies the look named in each job, draws the list of jobs, one after another, so Blender loads once. A job: scene, camera, light (A to E), state, size, samples, look (`today`, `base`, `kit_all`, `kit:<layers>`, `solo:<layer>`), dial overrides, and a **view**: `beauty`, `layer:<key>` (that layer's own mask, raw, in plain light: used as the mask in the readability measure), `mask:<name>` (a bus mask in plain light), `class` (a flat colour per role, for surface masks), `puddles`, `plan:<name>` (a bus mask seen from above). It writes a PNG, then a JPG at quality 90, and the seconds. It skips a picture that already exists, so **the remote folder is cleared before a re-run** (a stale picture on the rented machine comes back otherwise).
* **Per picture** the runner sets the scale helper's Dot Angle from the camera and the plate size, the pieces' camera position, and the wet state for every part (`kit.set_state`).
* **Remote** (`harness/remote.py`): only `runpod/render_client_cached.py` (never the old `render_client.py`, never anything in `~/.runpod`). `upload` sends only changed files (the kit code, the settings, the mask packs, the pinned earlier layers, the maps; the machine already has `set_copy`, `tools` and `maps`, not `relief_and_rubbish` or the kit); `run` starts one Blender run that draws a whole batch; `download` brings back one tar of JPG and JSON, then the remote PNGs are deleted. A whole run of a few pictures takes 7 to 22 s on the card (the lockout file's first picture 14.7 s, then 2.6 s); the same picture here takes 75 to 85 s (plate size about 20 minutes), so **everything that is drawn is drawn there**. If a call fails with "no answer from the machine", run `status` once and try again; if "NO CARD FREE", draw here and say so. Do not stop or end machines.
* **Measuring** runs here on the downloaded JPG and JSON (plain Python with numpy and OpenCV); nothing needs Blender except the runner.
* **Disk**: work pictures as JPG; mask pictures as PNG only where a measure needs exactness; delete big scratch files at once; stop and report if free space falls under 0.9 GB.

### 9.3 The baseline

The foundation draws `base` for everything above **three times** (timing), keeps the JPG and JSON in `harness/baseline/`, and freezes `numbers.json`: the joint passes (21 of 22 expected), wet-to-dry ratios, puddle shares, class brightness shares, plate drawing times (best of three). **The three earlier layers are pinned**: the foundation copies their code (about 0.7 MB: `tools/wetness_layer.py`, `tools/apply_wetness_to_set.py`, the joint and rubbish `tools/`) into `integrate/legacy_pinned/` with file hashes in `legacy_pinned.json`, so the baseline cannot drift if the second painter round (which is fixing the rubbish pieces) changes the protected originals. If the second round has delivered newer rubbish by the time of integration, the integrator reports the difference and does not switch without being told.

### 9.4 The measuring scripts (each is a pass line's own test)

| script | measures | pass line |
|---|---|---|
| `measure_joints.py` | the earlier joint measure (contrast, delta, seen in the near and middle road bands) with the settings' `joint_pass`, three counts: puddle and rubbish dots left out (the official one), every dot counted, kit dots left out too; plus the dark-or-bright-lines measure | P1 |
| `measure_wet.py` | wet-to-dry ratios, puddle cover, highlight share, speckle share, each element's wet/dry | P2 |
| `measure_readable.py` (with `plate_detail_check.py` and `painter_survival_fit.json` copied in) | per element: width, contrast, surround brightness, GOOD / RISKY / LOST, crushed share; minimum counts | P3 |
| `coverage.py`, `measure_period.py` | shares of each surface covered by each element (from plan views of the layer masks and from the three cameras), the period caps, the hue check, forbidden classes | P4, D13 |
| `measure_mush.py` | area darkened by a third, share under 0.10, mean brightness drop, contrast spread, distance continuity | P5 |
| `measure_zones.py` | the habitat fields and the picture, in the crown, lanes, fire, doorstep strips | P6 |
| `measure_time.py` | seconds per picture (best of three), first picture, piece count | P7 |
| `selftests.py` | `dial_zero(layer)`, `isolation(layer)`, `determinism()`, `reuse_smoke(layer, set)` | P8, P9, P10 |
| `lint_no_set_names.py` | scans kit code (not `sets/`, `presets/`, `integrate/`, notes) for every object or material pattern or name in any settings file, for set words (street, cottage, colliery, pit village, courtyard, Japanese, lantern, shoji, Astra, doorway names), and for coordinates or sizes copied from a settings file. Generic element words (kerb, flag, sett, gutter, step, pipe, wall, iron) are allowed: a layer's dials are named after the thing they age | P9 |
| `sheets.py` | contact sheets, before/after pairs at 100 %, mask sheets (JPG under 400 KB) | reports |

---

## 10. Pass lines

All are measured on the rented machine's pictures, against `base`, in one batch. Each builder must meet P3, P5, P6, P7 (its own share) and P8 for **its own layers alone**; the integrator must meet all of them together. A failure is reported with its number, never hidden.

**P1 The sett joints still pass.** With the puddle dots and the rubbish dots left out (as before) and the kit's own dots **left in**: at least **21 of the 22** pictures pass, and every picture that passed in `base` still passes. With every dot counted (reported; not worse than the 18 of 22 before). With the kit's own dots left out as well: the count equals `base`'s. No picture's near-band joint contrast above 0.75 (no harsh black grid). The dark-or-bright-lines measure is reported too. Moss in joints may cover at most 15 % of the joint length.

**P2 The wet look is kept.** In every wet and heavy picture of the 22 on all three cameras: the wet-to-dry mean-brightness ratio of road, pavement and walls is within **0.05** of `base`'s (the wetness recipe's target for stone and brick is about 0.72 to 0.76); puddle cover within **2 points** of `base`'s at the same dial (the main camera's road: 8 %); the share of road dots that are specular highlights (above `base`'s 95th percentile of the wet road) within **85 to 115 %** of `base`'s; the speckle share (road dots at least four times the local median in lighting E wet) not above `base`'s plus **0.2 points**; every kit element's wet/dry brightness ratio at most 1.0 (nothing gets brighter when wet; whitening goes grey), moss between 0.55 and 0.85.

**P3 Each element is readable at the painter's size.** On the three plates (main, lockout, notice) for each element's own mask run `plate_detail_check.py` at painter scale 0.45 (0.40 reported). Inside the element's design zone: at least **60 %** of its marks GOOD, at most **15 %** LOST, at most **15 %** crushed (a dark mark on a surround under plate 0.12), and at least the minimum count of GOOD marks on the main plate (half on the lockout plate):

| element | design zone | smallest mark, smallest contrast (plate dots, plate brightness) | GOOD marks, main plate |
|---|---|---|---|
| soot and dust patches, walls | the whole wall | 15 wide, 0.06 (0.04 least) | 15 |
| run-off streaks | first 20 m | 8 to 15 wide, 0.04 to 0.05 | 10 |
| wall-foot band, tide-mark | first 30 m | 15 tall, 0.04 | visible along 60 % of the wall length in the zone |
| whitened or scrubbed steps | first 15 m | 8 frame, 0.08 | 4 steps |
| rust (post feet, pipe collars, drum) | first 20 m | 8 wide, 0.06 | 4 |
| cracks in flags, kerbs, setts | first 12 to 15 m | 3 wide at 0.11, 5 wide at 0.08 | 3 |
| tar patches | first 30 m | 15 wide, 0.06 | 1 |
| ground film, polish, water marks | the whole ground | 15 wide, 0.04 | 8 |
| weed tufts, moss cushions | first 15 m | 5 wide, 0.08 | 12 |
| moss ribbons, algae fans | first 15 to 20 m | patch 15 wide; dots 5 wide at 0.08 | 8 |

**P4 Nothing modern or wrong for 1926.** (a) By construction: the street look has no entry for graffiti, road lines or studs, yellow lines, wheelie bins, satellite dishes, modern litter, car oil, straight-edged trench patches, buddleia, flower boxes; `lichen_amount` is 0; the S7 and S9 layers do not exist. (b) By measurement, every element inside the period study's caps (a number outside its cap fails): soot on 85 to 100 % of wall area, washed 15 to 25 %, run-off streaks 3 to 6 % of wall area with a pair at 60 to 80 % of sills and a heavy leak at 10 to 20 % of downpipes, splash band on 70 to 90 % of wall length and 15 to 35 cm tall, whitened steps 40 to 70 %, flags (fine cracks 8 to 15 %, broken 2 to 4 %, tilted 3 to 6 %, chipped corner 5 to 10 %), kerb chips 20 to 35 % of length, setts disturbed 3 to 6 % with 10 to 20 % of joints open, tar 1 to 3 patches in the first 30 m and at most 4 % of the road, weed cover 0.5 to 2 % of the ground inside the pieces distance, moss on 5 to 15 % of the gutter-side joint length, **lichen exactly 0**, algae at all pipe outlets, liverwort 0 to 2 patches. (c) Hue check on the dots the kit changed: orange or yellow (hue 30 to 65 degrees, saturation 0.5 or more, value 0.5 or more) outside the rust and dandelion masks at most 0.05 % of dots; no bright green (saturation 0.6 and value 0.6 or more); nothing whiter than the whitened steps; whitewash at most 15 % of visible wall. (d) A fresh checker looks at eight 100 % crops and a sheet and finds nothing wrong for 1926.

**P5 The street is not turned into one dark mush.** Against `base`, per surface class (walls, trims, road, pavement, kerb and gutter, iron, roofs) on the main and lockout wet plates: **M1** at most **25 %** of the class's area darkened by a third or more (the painted-look budget: 25 % at a third reads as dirty but legible; 45 % at half brightness is mush); **M2** the share of the class under plate 0.10 rises by at most **8 points on road and pavement** and by at most **3 points on walls and trims** (they are already 60 to 90 % under 0.10 in the baseline, so almost nothing more may be crushed); **M3** the class's mean brightness drops by at most **12 %** (the legible example is 8.75 %, the mush example 22.5 %), the whole plate's by at most 8 %; **M4** the spread of brightness inside the class (90th over 10th percentile) stays at **85 % or more** of `base`'s (the street keeps its contrast, brick courses and joints stay); **M5** distance continuity: the kit/`base` brightness ratio of each class in the bands 5 to 10, 10 to 20 and 20 to 40 m stays between 0.80 and 1.00 and differs by at most 0.08 from band to band (no clean far wall).

**P6 No weeds or moss on the crown or the traffic lanes: zero.** `moss_site`, `weed_site`, `algae_site` and `lichen_site` are exactly 0.0 wherever `footfall` is 0.6 or more, `crown` 0.7 or more or `keepclear` 0.5 or more; **no piece** (from `pieces.json`) stands in those zones, within 1 m of the fire, or on a doorstep strip (count 0 of all pieces on all plates); painted green marks (the layers' `layer:` views) cover at most 0.2 % of the area of those zones; and at most 3 % of weed pieces stand within 5 cm of a rubbish piece.

**P7 The same drawing time within +30 %.** Plate pictures (1536 x 2730, 48 samples) on the main and lockout cameras, same card and same run as the baseline, best of three: all kit layers together at most **1.30 x** `base`'s time; shares walls +8 %, ground +8 %, growth +10 %, foundation overhead +4 %. The first picture after applying (shader build) at most 1.5 x `base`'s first picture and never over 40 s. At most 2,500 growth pieces in one picture.

**P8 Master dial 0 changes nothing.** For every layer: at `amount` 0 a float evaluation at 64 sample points is exactly the same (difference 0.0) and an EEVEE picture is identical (or at most one step of 255 on at most 1 % of dots); all layers at 0 equal `base`; a layer alone changes only the materials of its roles (isolation: the difference picture lies inside that role's class mask).

**P9 Reuse.** Zero hits from `lint_no_set_names.py` over `apply/`, `masks/`, `harness/`, `walls/`, `ground/`, `growth/`; both settings files validate; the foundation's reader and hook run on the courtyard scene (roles found for all 88 meshes, no object in two roles, hook on all 75 plain materials and the adapter on all 46 add-on materials, do-nothing picture identical); every builder's self-test also passes with the courtyard look on the courtyard scene (no crash, `amount` 0 identical).

**P10 Deterministic and the behind plate matches.** Two draws of the same plate are identical at the same samples; the lockout "behind" plate (props hidden) differs from the plate with props only where props are (at least 99 % of the other dots within 2 steps of 255).

**P11 Hygiene.** Nothing written in the film project or in `set_copy`, `street_wet/tools`, `relief_and_rubbish`, `painter_round_2`, `painter_test`, `japanese-courtyard` or the add-on folder (checked by hashes recorded at the start and at the end); the lockout file and the courtyard file never saved; no commit or push; no paid call; no machine stopped; each folder under its limit; free disk above 0.9 GB.

---

## 11. What each helper makes, and the briefs

### Common rules (every helper)

* Blender 5.2.2 at `/home/user/work/blender-app/blender-5.2.2-linux-x64/blender`, always `-b --disable-autoexec`. Draw every picture on the rented machine through `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py` after reading `HOW TO RENDER ON THE RENTED MACHINE - cached.md`; batch many pictures in one run; never print, copy, move or read anything in `~/.runpod`; do not stop or end machines; other jobs share it, that is fine.
* Never write in the film project (`/home/user/Music/austerity-explainer`), `street_wet/set_copy`, `street_wet/tools`, `street_wet/relief_and_rubbish`, `street_wet/painter_round_2`, `street_wet/painter_test`, `/home/user/Music/japanese-courtyard` or the add-on folder; read them freely (read the painter round 2 results if they exist). No commit, no push, no paid image call. Do not save the lockout or courtyard files.
* Disk is tight (about 1.9 GB shared by three jobs): JPG for work pictures, delete big scratch files, stop and report if free space falls under 0.9 GB.
* Code goes in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/<part>/` with **no set-specific names or numbers**; set-specific choices go in the settings files. Work pictures and notes go in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/<name>/`.
* Pictures worth showing go in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/` as JPG under 400 KB, names starting "25 " and saying what they show.
* Report in plain everyday words; say what you tested, what you did not, what you are unsure of and every failure. Explain an unavoidable technical word in one sentence.

### 11.1 Foundation (time-box about 4 hours; folder `grime_and_growth/foundation/` at most 150 MB)

**Read first:** this plan sections 3 to 6, 9 and 10; study 11 (sections 3 to 5, 9, 11); study 12b (sections 4, 8); the earlier tools `street_wet/tools/wetness_layer.py` and `apply_wetness_to_set.py`, `relief_and_rubbish/rubbish/tools/make_places_pictures.py`, `rubbish_runner.py`, `relief_and_rubbish/study/tools/b02_lighting_and_variants.py`, `b09_lighting_test_set.py`, `setts/tools/measure_grid_visibility.py`, `painted_look/tool/plate_detail_check.py`; the two settings files.

**Make, in this order** (if time runs out write what is missing in `masks/NOT_DONE.md`; the builders start from what exists):
1. **Core (`apply/`)**: `settings.py`, `roles.py`, `dials.py`, `seed.py`, `hook.py`, `adapters.py`, `chain.py`, `kit.py` and a **layer template** (`apply/layer_template.py`: a documented do-nothing layer that shows how to read bus masks by name, use `WK SCALE`, register a dial table with the master `amount`, and tag nodes). Tests: the hook works on all 41 street materials, all 85 lockout materials, and 75 plain plus 46 adapted courtyard materials; a do-nothing layer in slots A, B and C draws a picture identical to `base` (street 135 x 240 and 540 x 960 EEVEE; courtyard 1200 x 800); removing layers in any order or twice leaves the chain right; the earlier three layers register as stages from the pinned copies. Test first whether an Attribute node reads an object custom property in EEVEE and Cycles and write the result down (fallback in section 5.5).
2. **The where-pictures (`masks/`)**: everything in the table of section 6.2, per scene, as a pack with `manifest.json`: the ground plan (heights, slope, lowness, crown, wall and prop distance, catch points, steps, edges, piece gaps, seams, covers, water), the wall sheets and the ledge finder, shade (all modes), dampness, footfall, keep-clear, entry random, existing growth, the habitat fields, the texture-space pictures (cavity for the four photo materials; cells and joints for setts, reusing `sett_joints_clean.png`, and for flags, new), and `rubbish_heap` (the earlier runner's `plan` view of the RUBBISH mask on the pinned layers, for the street and the lockout). Make the pack for `street` and `lockout`; dry-run the reader on the courtyard.
3. **The bus and the scale helper**: `bus.py` (`WK MASKS`, attach per material, defaults), `scale.py` (`WK SCALE` and the mark-width helper), `debug.py`. Tests: the bus-consistency test (200 random points, at most 2/255); every acceptance check of the mask table; the dot-size table of section 6.4 within 3 %.
4. **The harness (`harness/`)**: cameras (from the settings, including `look_at` and `aim_at_feature`), lighting rigs A to E as data (draw A, C and E and compare with the earlier pictures: 99 % of dots within one step of 255), the T22 set, the five close views, plates, the chart plate, `jobs.py`, `runner.py`, `remote.py`, `class_pass.py`, `legacy_stack.py`, the measuring scripts for P1 to P7, `selftests.py`, `lint_no_set_names.py`, `sheets.py`.
5. **The baseline**: draw `base` three times, freeze `harness/baseline/numbers.json` and the pictures; record the pinned-code hashes.
6. **Reuse proof on the courtyard**: settings and roles on all 88 meshes, reader dry-run (ground height, year-sun shade, water edge, existing-growth density), hook and adapter on 121 materials, the do-nothing picture identical (EEVEE 1200 x 800 on the rented machine).
7. **Write** `masks/CONTRACT.md` (every bus name, meaning, default), `README.md` (one page), and the work-folder notes.

**Do not:** write in any other helper's folder; put a street or courtyard name, coordinate or size in kit code; use EEVEE's Ambient Occlusion, Bevel or Pointiness nodes; edit meshes or material slots; call the earlier scripts' own `remove()`.

**Pictures to save (names start "25 "):** the ground pictures of the street; one wall sheet of cottage 01; the habitat fields with the lanes; the same readers on the courtyard; the baseline close views of the five places; the T22 baseline contact sheet.

**Report:** the test results (a JSON next to the notes), which masks passed their checks and which did not, the baseline numbers, the Attribute-node result, timings, the size of each pack, what is in `NOT_DONE.md`.

### 11.2 Walls (builder; time-box about 2.5 hours; folder `grime_and_growth/walls/` at most 120 MB; code in `kits/weathering/walls/`)

**Your job.** Make the layers that dirty and age house walls and their trims in the 1926 pit village, as reusable layers that read only the kit's standard masks and work on any set. Read first: this plan (sections 0 to 2, 5, 6, 7.1, 9, 10, Appendix A walls tables and Appendix B); `foundation/` notes and `kits/weathering/masks/CONTRACT.md`; study 12 (sections 4 to 10); the period rules G1 to G6, S2, S5, S8, C4 to C7, M2, M4, M5, L1 (`study/reference_1926/tools/rules_data.py`); for ideas and numbers only `recipes/slate_layers/layers/moss.py` and `damage.py`, the wood CRACKS layer and the brick GRIME layer (they read a slate or tile layout and cannot be used as they are); the Scenario texturing skill in `/home/user/Music/.claude/skills/scenario-blender-texturing-shading` (read only: `grunge_group`, `audit_material`, `value_report`; its Bevel and AO edge masks do not work in EEVEE).

**Make, in this order, tuning each before starting the next** (node groups named `WK SOOT`, `WK RUNOFF` ...; dials exactly as in Appendix A, you may add finer ones in the same style): `soot`, `runoff`, `foot`, `steps` (MUST); `wallgrowth`, `wallcracks` (SHOULD); `paint` (COULD). Do **not** build limewash, bird lime or the roof soot fan. Slots: A for soot, runoff, foot, steps, paint; B for wallcracks; C for wallgrowth (section 5.1). Roles and which masks to read are in section 7.1 and the tables.

**The rules that decide whether it works:** (1) pale-first on dark surfaces: 80 to 90 % of wall and trim dots are under plate 0.13 and the film crushes them, so the pattern is washed stripes, salt, whitened steps, rust runs and moss lighter than the stone; dark soot never goes below `floor_mult` of the clean colour; do not use `base_lift` unless told. (2) Every width goes through the mark-width helper in plate dots (soot patches 15 or more, streaks 8 to 15, cracks 3 at contrast 0.11); fine detail fades to the layer's average tone, never to clean. (3) Amounts are shares of the wall in the world (period caps in P4), not values fitted on one camera; check main, lockout and notice. (4) Walls are slanted in the view: vertical marks survive, small horizontal detail does not. (5) Moss lighter than the stone, saturation 0.45 or more, hue 85 to 120 degrees; **lichen is 0 in the street** (the smoke killed it) but must work in the courtyard look. (6) Cracks only in slot B, dull, a few, never a net. (7) Never stack the dry splash band, WETNESS's 0.9 m wet band and the film into mush (P5).

**Deliver, for each layer:** the node-group builder file; an `apply_walls.py` with `apply(kit)`, `remove`, `set_dials`, `show_mask` that goes through the kit's hook and chain (never your own splice); a self-test that calls the foundation's `selftests.dial_zero`, `isolation` and `reuse_smoke` (the courtyard look on the courtyard scene) and saves `selftest_walls.json`; debug views (`layer:<key>` and named parts through `kit.show_mask`); a sheet (`sheet_walls.py`): before and after at 100 % on crops of the main plate, the close views wall foot, downpipe and doorstep, and the layers one at a time on one house; the measurements of P3 for your elements, P5 for walls and trims, P7 (your share +8 %), P8 and the wall part of P2; and a recipe note in plain words in `grime_and_growth/walls/` (what each layer does, its dials, what you tried and dropped, what failed). If you need a mask the foundation does not have, make a private one in `walls/local_masks.py` and say so; never edit `masks/`, `apply/`, `harness/`, `sets/` or `presets/`; if you want a look value changed, say which in your report (`REQUESTS.md`).

**Pictures to save (names start "25 ", JPG under 400 KB):** "25 Walls - soot, run-off streaks and wall foot at the main camera (before and after)", "25 Walls - doorsteps whitened and worn (close, before and after)", "25 Walls - the layers one at a time on one house", "25 Walls - the downpipe close (streaks, splash, tide-mark)", "25 Walls - the same layers on the courtyard plaster wall (reuse test)".

**Report:** per layer: done / partly / not started; every pass-line number you measured; every failure; what you did not test; what you are unsure of (how much, which colour, whether the painter keeps it).

### 11.3 Ground (builder; time-box about 2.5 hours; folder `grime_and_growth/ground/` at most 120 MB; code in `kits/weathering/ground/`)

**Your job.** Make the layers that dirty, crack and green the street's road, flags, kerbs and gutter stones, and all iron, as reusable layers that read only the kit's standard masks. Read first: this plan (sections 0 to 2, 5, 6, 7.2, 9, 10, Appendix A ground tables, Appendix B); `foundation/` notes and `masks/CONTRACT.md`; study 12 (sections 4 to 10); the period rules G (ground), C1 to C3, S1 to S4, S6, S8 (strip), W1, W2, W5, W6, M1 to M3; the earlier JOINTS recipe (`relief_and_rubbish/10 Recipe...md` part A: sections 2, 3, 7: why water washes narrow dark lines out) and RUBBISH (part B: so you do not repeat it); `recipes/slate_layers/layers/moss.py` (method and its four rules); the Scenario texturing skill (read only).

**Make, in this order** (`WK GROUND DIRT`, `WK GROUND CRACKS`, `WK GROUND MOSS`, `WK IRON`; dials as in Appendix A): `dirt` (slot A), `groundcracks` (slot B), `groundmoss` (slot C), `iron` (slot A; straight before the Principled BSDF on materials without WETNESS). Roles and masks in section 7.2.

**The rules that decide whether it works:** (1) **Do not repeat RUBBISH**: no ash, coal dust, cinders, mud, straw, paper, leaves; your film is broad and soft, plus traffic polish, water marks, rust halos, tar; keep `film_near_walls` honest. (2) The ground has headroom (wet road 0.195, pavement 0.20) so dark marks work here, but keep the darker side at plate 0.10 to 0.12 or more and the surround 0.18 or more; at most a quarter of a surface darkened by a third (P5). (3) **JOINTS must still pass** (P1): cracks come after WETNESS and JOINTS and make themselves dull; sett joints never exceed contrast 0.75; moss in joints covers at most 15 % of the joint length and the joint grid must still read; check P1 with the kit's own dots in and out. (4) Cracks at least 3 plate dots wide (contrast 0.11; 5 dots at 0.08), a few, only in the first 15 m (`near_only`), never across the road beyond about 12 m (a crack across the street is 43 mm deep at 10 m per 3 dots); draw them thicker than real. (5) Tar patches irregular and scalloped, never straight-edged, at most 3 % of the road. (6) **Never moss, algae or weed marks on the crown, in the lanes, near the fire, on the doorstep strips**: they come for free from `moss_site` and `keepclear`; test it (P6). (7) Rust lowers Metallic. (8) The far band (beyond the pieces distance) hands over with the growth pieces through `Far Blend`; agree with nothing but the settings' `far_band_handover_m`.

**Deliver, for each layer:** as for the walls brief: node-group builder files, `apply_ground.py` through the kit's hook and chain, a self-test (`dial_zero`, `isolation`, `reuse_smoke` with the courtyard look: gravel, earth and stones) saved as `selftest_ground.json`, debug views, a sheet, measurements (P1 with your layers, P3, P4 caps for your elements, P5 for road and pavement, P6 for your painted moss, P7 your +8 %, P8, P2 ground part), a plain-words recipe note. The `flag_close` camera is re-aimed at your strongest flag crack: write `feature_report.json` (`strongest_flag_crack` position) so the harness can find it.

**Pictures to save:** "25 Ground - cracks, kerb chips and tilted flags (close and plate crop)", "25 Ground - tar, rust halos, polish and water marks", "25 Ground - moss in the gutter joints and algae under the downpipe (close)", "25 Ground - the iron: lamp posts, downpipes, the fire drum", "25 Ground - the road middle stays clean (crown and lanes)".

**Report:** as for walls, plus the P1 table (the 22 pictures, with the kit dots in and out) and the share of joint length with moss.

### 11.4 Growth (builder; time-box about 2.5 hours; folder `grime_and_growth/growth/` at most 120 MB; code in `kits/weathering/growth/`)

**Your job.** Make the 3D weeds and moss cushions as scattered pieces (Geometry Nodes), plate only, sized and placed by the 1926 period rules, wet where the street is wet, never on the crown or in the traffic lanes, sensible next to the rubbish. Read first: this plan (sections 0 to 2, 5.5, 6, 8, 9, 10, Appendix A growth table and colours); the earlier pieces code `relief_and_rubbish/rubbish/tools/rubbish_pieces.py` and recipe part B5 (the Poisson-disk scatter, the wet value, the distance dial; the first pieces "looked like gems and matchsticks": too few facets) and the Scenario geometry-nodes skill (`/home/user/Music/.claude/skills/scenario-blender-geometry-nodes`, its scatter builder and counting checks; read only); the period rules W1 to W6, M1, M3; study 12 sections 4, 5, 9, 11 (marks 5 plate dots wide and contrast 0.08 come back as inked blobs; single blades are lost; hundreds of minimum marks read as noise).

**Make:** (1) `pieces.py` and `species.json`: the piece library of section 8 (grass tufts with bent blades and some dead, pearlwort cushion, dandelion and plantain rosettes, groundsel, shepherd's purse, chickweed mat, optional toadflax trail, moss cushions), 40 to 200 ragged faces each, sizes by the period rules, colours from Appendix A with a `WET` value. (2) `scatter.py`: the **generic** engine: mask picture channel (the bus's `weed_site`, `moss_site` read from the ground-plan picture by world x and y), piece set, density per kind from the share dials, Poisson-disk spacing, hard multiply by `keepclear`, the rubbish rule (full density below `rubbish_thin_max`, none above `rubbish_heap_min`), camera-distance cut-off and fade (the runner sets the picture's camera position), widening with distance up to a limit, a ceiling `max_pieces`, a seed, target roles from the settings, a `realise_instances` option; it must also work on a non-ground target (a tilted box with a picture mask) so the courtyard's stones are not a surprise. (3) `apply_growth.py` (`apply(kit)`, `remove`, `set_dials`, `set_state`, `pieces(visible)`), `report_growth.py` (`pieces.json`: position, kind, size of every piece), `selftest_growth.py`, `sheet_growth.py`, a plain-words recipe note.

**The rules that decide whether it works:** (1) A few clusters, not hundreds of tufts; at most 2,500 pieces in one picture (your drawing-time share is +10 %: measure it). (2) Zero pieces on the crown, in the wheel bands, on the walking line to each door, within 1 m of the fire, on doorstep strips (P6: count them from `pieces.json`); at most 3 % of weed pieces within 5 cm of a rubbish piece. (3) Weed cover 0.5 to 2 % of the ground in the first 18 m (default 1.0 %), 3 to 8 % of gutter-side joint length with a tuft, 2 to 5 % of wall-foot length with a plant. (4) May 1926: seedlings and small rosettes; no buddleia, no rosebay, no flower box, no lichen; a few dandelions in flower. (5) Colours lighter and stronger than the finished look (hue 85 to 120 degrees, saturation 0.45 or more, plate brightness 0.17 to 0.33 at least, never under 0.12 wet) because the painter weakens colour; wet pieces richer green and a little glossier, no coat. (6) Beware the EEVEE speckle on anything glossy (shadow rays 4, steps 16, 32 to 48 samples). (7) Pieces keep their resolution (a 10 cm tuft is 9 plate dots wide at 40 m), but the painter invents its own texture in the far third of the road, so stop at the pieces distance.

**Deliver:** the files above; `selftest_growth.json` (`amount` 0 gives zero pieces and an identical picture; isolation; the courtyard look on the courtyard scene gives a piece set on earth and stones without a crash); debug views (a plan of piece density; `mask:` views); measurements (P3 for tufts and cushions, P4 weed cover, P6 zones and rubbish, P7 your +10 % and the piece count, P8, P2 wet look of pieces); a sheet.

**Pictures to save:** "25 Growth - the pieces (weeds and moss cushions) in a close view, dry and wet", "25 Growth - where pieces stand (plan with crown, lanes and rubbish)", "25 Growth - weeds through thin rubbish, none on heaps", "25 Growth - the main plate crop at 100 %".

**Report:** as for walls, plus the piece counts per zone and the time cost per 1,000 pieces.

### 11.5 Integrator (time-box about 3 hours; folder `grime_and_growth/integrator/` at most 200 MB)

**Make:** (1) `integrate/legacy_adapters.py` and `street_run.py`: the full chain of section 5.4 on the street copy and the lockout file with the pinned earlier layers and the three builders' layers; (2) put each builder's dial values into `presets/sooty_1926.json` where they differ from the plan's (keeping a change log in `tune_log.md`); (3) draw T22, the five close views and the plates in `base`, `kit_all` and `solo:` looks; (4) run every measure; tune **at most four rounds** against P1 to P11 (the order of tuning: P5 mush first, then P3 readability, P1 joints, P2 wet look, P7 time); the legal tuning moves are dials in the look, never code in a builder's folder (a code fault goes back to that builder's folder as a note in `REQUESTS.md`; the integrator may fix a one-line fault and must say so); (5) the courtyard smoke test again with the final code; (6) `integrate/check_pack/`: eight 100 % crops, the contact sheet, the numbers and the plain-words list of every pass line with its value, for a fresh checker; (7) the hand-off to the Paint step: the plates (main, lockout with props, lockout behind, notice), the chart plate, the brief sentences of section 2, and a plain list of what the painter may do to moss (unknown) and to dark grime (unstable).

**Report:** every pass line with its number; every failure; what was tuned and what each tuning cost; what is still not good; the drawing times.

---

## 12. How the work fits together

### 12.1 Order and gates

`foundation` (about 4 h) - **gate G0** - `walls`, `ground`, `growth` in parallel (about 2.5 h each) - **gate G1** - `integrator` (about 3 h) - **gate G2** - a fresh checker (not part of this plan) reads `integrate/check_pack/` - the Paint step (paid, needs the person's go-ahead) - later, the courtyard job.

* **G0**: the foundation's selftests all pass (hook on all materials of three scenes, do-nothing identical in slots A, B and C, remove in any order, bus consistency, mask checks), `CONTRACT.md` and `NOT_DONE.md` are written, the baseline numbers are frozen. If a part is missing the builders are told in `NOT_DONE.md` and design around it.
* **G1**: each builder has its `selftest_*.json`, recipe note and report. A builder that ran out of time reports which layers are done, partly done or not started; the integrator works with what exists.
* **G2**: the check pack has the eight 100 % crops, the contact sheet, the numbers and the plain list of every pass line with its value.

### 12.2 Who owns which file, and how the parts touch

| shared thing | made by | read by | rule |
|---|---|---|---|
| the mask pack and the bus | foundation | every layer | read by name only; a builder never edits `masks/` |
| `moss_site` | foundation | walls `wallgrowth`, ground `groundmoss`, growth cushions | painted and 3D moss land in the same places; exclusions live inside the field |
| `weed_site` | foundation | growth | |
| `entry_rand` | foundation | walls `steps`, ground `dirt` (scrub strip) | the strip in front of a door agrees with the step |
| `drip` and `drip_kind` | foundation | walls `runoff`, ground `dirt` and `groundmoss` (algae fans), `iron` | one finder, one truth |
| `Far Blend` and `far_band_handover_m` | foundation (scale helper) | ground `groundmoss` (band), growth (cut-off) | the pieces fade out as the band fades in |
| `rubbish_heap` | foundation (from the earlier runner) | growth, `groundmoss`, `dirt` (`film_near_walls`) | the only way a kit layer learns about RUBBISH |
| dial values | builders propose, integrator edits `presets/` | | a builder never edits `presets/` |
| `pieces.json` | growth | harness (zones, proximity, count) | |
| `feature_report.json` | ground | harness (`flag_close` aim) | |

**Change requests.** A builder that needs a change in the foundation's code, the settings or the looks writes it in `REQUESTS.md` in its own work folder (what, why, the smallest change). The integrator decides and edits; it may fix a one-line fault in a builder's folder and must say so.

### 12.3 What the courtyard will need that the street cannot test

The street has no instanced roof, no shader-group stones, no add-on rebuilds, no water, no raked gravel and no existing growth. The kit supports all of them by design (sections 4 to 6) and the reuse proof (P9) covers only a smoke test: the reader on the courtyard scene, the hook and adapter on 121 materials, a do-nothing picture, each layer at `amount` 0 and at default without a crash. Untested until the courtyard job: scatter on realised roof instances and on displaced gravel; the kit's moss against the add-on's (extend or match: a choice for the person); the courtyard's own plate camera, lighting rigs and test set; its wet look (no wetness layer there); a litter piece set (leaves, needles); whether the painter keeps moss and streaks on light plaster.

---

## 13. What the plan does not settle, what I did not test, and what went wrong

**Questions for the person** (the plan has a default for each; the integrator's report will say what was assumed):
1. Which side of the street is the shaded, damp one? I declared the left row's fronts (`shade.toward_sun` from -x). Flip it in the settings if the film's orientation says otherwise.
2. Whitened or donkey-stoned doorsteps in a Durham pit row: 55 % in the look, medium confidence (documented for Lancashire and Yorkshire, no Durham source found). Keep, or lower to 0?
3. Sett and flag street versus tarmac: new East Durham villages had all roads tarmacadamed by about 1917 (Blackhall), so a sett street is the older-village look; tar patches (capped at 3 %) cover this either way. Keep?
4. Lockout air: pits idle may mean less fresh smoke; the plan draws a hard old crust with washed streaks, not fresh black dust. Say if you want fresher soot.
5. `base_lift`: if pale and coloured marks alone cannot make the dark walls read, may the integrator lift the walls' brightness a little (up to 0.3 on the dial)? Default: no, and it will say so.
6. Courtyard (next job): kept or neglected temple; north = +y and latitude 35 (assumptions, section 4); extend or match the add-on's moss.
7. The Paint step: a small paid repaint of the chart plate would settle moss and weed colour survival and the 0.4 plate size; wanted?

**What I did not test.** No weathering code exists, so no layer, mask or pass line was run. What I did run: one read-only Blender probe of the street copy (positions of pipes, posts, doorways, two lights, nothing saved), the generator that made the dial tables and look files, and a check that both settings files load, compile every regex, use the same keys and that the street's role patterns match the right counts (28 walls, 28 trims, 28 doorways, 28 downpipes, 5 posts, 112 paint objects). The plate-dot table of section 6.4 is my own arithmetic from the camera file. The habitat formulas, the dial values and the pass-line numbers are my judgement from the studies. The Attribute-node route for per-object values, EEVEE compile cost of 11 layers in 41 materials, the flag joint picture, the ledge finder on the other 27 cottages and every courtyard claim are untested. The two cameras `pipe_close` and `flag_close` are my coordinates and must be confirmed by drawing.

**What I am unsure of.** Every "how much" (the studies say so too); whether the painter keeps green moss green; whether a 3-dot crack at contrast 0.11 survives on wet ground; how the second painter round's rubbish changes the baseline (hence the pinned copy); whether the +30 % time budget is reachable with eleven layers and the pieces (the pieces are the main cost); whether the kit's compile time on 121 courtyard materials is acceptable (the street's rubbish layer on 4 materials cost about 2 s a plate).

**Conflicts between the studies, and how I settled them:** the unit of a mark (plate dot versus painter dot: D1); dark grime versus the film's crush (D2: pale-first, floor 0.30); "moss lighter than the stone" (painted-look) versus "moss in joints stays darker so the joints still show" (period study risks): moss is a mid-value green capped at 15 % of the joint length and measured with its dots in and out (P1); the pieces distance (13 m in the pipeline study, in painter dots, versus "10 to 15 m" in the painted-look study, in plate dots): 18 m with a 5 m fade and a far band; whether lichen belongs in a coal town (it does not).

**What went wrong while designing.** My first Blender probe crashed on a light attribute (fixed); the first draft of the street's file had no `looks` key (found by the check, fixed); the first dial tables named masks with a wall-sheet prefix that the unified bus does not use (renamed, tables regenerated). The report file of the period study was refused by the tool and is not a file; its content is in the study text and `rules_data.py`.

---

## Appendix A. The dials (generated from one list together with the look files)

Ranges are what makes sense; "kit" is the neutral default in code; "sooty 1926" and "courtyard (kept)" are the two look files (`presets/sooty_1926.json`, `presets/mossy_courtyard_kept.json`; `=` means the same as the kit default; the courtyard values are first guesses from study 12b section 9, not measured). Lengths in metres unless a dial says plate dots. A builder may add finer dials in the same style but may not rename or remove these.

**Dials every layer has** (the same names, ranges and defaults on every layer):

| dial | range | kit default | what it does |
|---|---|---|---|
| `amount` | 0 to 2 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |

#### `soot` (WK SOOT), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim, wall.industrial, chimney, roof.*. Reads masks: sheltered, drip, reveal, shade, tx_cavity, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `film_mult` | 0.3 to 1.0 | 0.8 | 0.62 | 0.97 | Colour multiplier of the general film on the clean surface (brick 0.50 to 0.65 in 1926). |
| `sheltered_mult` | 0.2 to 1.0 | 0.6 | 0.4 | 0.85 | Multiplier where rain cannot reach (under sills, eaves, in reveals). |
| `washed_mult` | 0.5 to 1.2 | 0.95 | 0.85 | 1 | Multiplier where rain washes (sill tops, the windward upper wall). |
| `washed_share` | 0 to 0.6 | 0.2 | 0.2 | 0.3 | Share of wall area that is rain-washed (15 to 25 % in 1926). |
| `floor_mult` | 0.2 to 0.8 | 0.4 | 0.3 | 0.6 | No dot may go below this multiple of its clean colour (keeps the film curve from crushing it). |
| `grey_pull` | 0 to 1 | 0.2 | 0.3 | 0.15 | How far colour is pulled toward grey (25 to 35 % in 1926). |
| `mortar_soot` | 0 to 1 | 0.3 | 0.5 | 0.1 | Extra darkening in mortar hollows (soot sits in hollows first). |
| `mottle_size` | 0.2 to 3 m | 1 | 0.9 | 1.2 | Size of the slow mottling. |
| `mottle_contrast` | 0 to 1 | 0.4 | 0.5 | 0.3 | How strong the mottling is. |
| `edge_sharp` | 0 to 1 | 0.5 | 0.6 | 0.4 | How crisp the line is between washed and sheltered (a clean line under a sill). |
| `stack_mult` | 0.2 to 1.0 | 0.6 | 0.35 | 1 | Multiplier on chimney stacks (blackest in a coal town). |
| `roof_mult` | 0.5 to 1.0 | 0.9 | 0.82 | 0.95 | Multiplier on roof surfaces. |
| `base_lift` | 0 to 0.5 | 0 | 0 | 0 | LAST-RESORT dial: lifts the whole wall colour so that a pattern has room above the film-black zone. Off unless the integrator proves it is needed and says so. |

#### `runoff` (WK RUNOFF), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim (iron-sourced streaks use iron objects as sources). Reads masks: drip, drip_dist, drip_kind, sheltered, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `strength` | 0 to 1 | 0.4 | 0.55 | 0.5 | Contrast of the streaks. |
| `tone` | -1 to 1 | 0 | -0.5 | 0.7 | -1 = pale washed stripe, +1 = dark stain. 1926 sooty walls: pale stripes with dark tide-lines. Courtyard plaster: dark grey-green streaks. |
| `edge_dark` | 0 to 1 | 0.3 | 0.5 | 0.2 | Dark tide-line along the streak edges. |
| `width_dots` | 4 to 24 | 8 | 10 | 10 | Smallest streak width in plate dots (the layer widens a streak with distance up to Inflate Limit). |
| `length_mult` | 0.3 to 3 | 1 | 1 | 1.2 | Length of every streak. |
| `ragged` | 0 to 1 | 0.5 | 0.6 | 0.5 | Ragged sides and a stretched-down shape. |
| `source_share` | 0 to 1 | 0.6 | 0.7 | 0.8 | Share of sills, ledges and cap edges that carry a streak pair (60 to 80 % in 1926). |
| `leak_share` | 0 to 0.5 | 0.1 | 0.15 | 0 | Share of downpipes that leak heavily and carry a long streak. |
| `leak_length` | 0.3 to 1.5 m | 0.8 | 0.9 | 0.8 | Length of a heavy leak streak. |
| `iron_rust` | 0 to 1 | 0.3 | 0.5 | 0 | How orange (rust) a streak is when its source is an iron joint or bracket. |
| `eave_streaks` | 0 to 1 | 0.3 | 0.5 | 0.7 | Streaks hanging from eave lines, gutter ends and cap overhangs. |

#### `foot` (WK FOOT), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim, wall.industrial. Reads masks: height, dampness, drip (pipe feet), tx_cavity, shade.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `splash_height` | 0.1 to 0.6 m | 0.25 | 0.28 | 0.3 | Height of the dirt splash band at the wall foot (15 to 35 cm in 1926). |
| `splash_strength` | 0 to 1 | 0.4 | 0.5 | 0.35 | How dark the band is at the ground line. |
| `splash_ragged` | 0 to 1 | 0.6 | 0.7 | 0.6 | Ragged top edge of splash dots and short upward fingers. |
| `finger_height` | 0 to 0.2 m | 0.08 | 0.1 | 0.1 | Height of the splash fingers above the band. |
| `pipe_foot_boost` | 0 to 2 | 1 | 1.4 | 0 | Extra heavy splash and damp where a downpipe ends. |
| `tide_share` | 0 to 1 | 0.3 | 0.45 | 0.15 | Share of house lengths that carry a damp tide-mark (older rows only). |
| `tide_height` | 0.3 to 1.3 m | 0.7 | 0.8 | 0.5 | Ragged top of the damp tide-mark. |
| `tide_strength` | 0 to 1 | 0.3 | 0.4 | 0.25 | Darkening inside the tide-mark. |
| `tide_green` | 0 to 1 | 0.2 | 0.3 | 0.4 | How green the damp zone is. |
| `salt_bloom` | 0 to 0.1 | 0.02 | 0.03 | 0.04 | Share of the band covered by white salts along its top. |
| `mortar_wear` | 0 to 1 | 0.4 | 0.5 | 0.2 | Recessed, eroded mortar in the lowest 0.6 m. |
| `spall_share` | 0 to 0.2 | 0.05 | 0.07 | 0.04 | Share of bricks or blocks with a flaked face near the foot. |
| `wear_height` | 0.2 to 0.9 m | 0.5 | 0.6 | 0.4 | How high mortar wear and spalls reach. |

#### `steps` (WK STEPS), owner: walls, priority: MUST
Acts on roles: wall.trim (the steps are found by the step masks, not by object). Reads masks: step_top, step_edge, entry_rand, edge_dist, footfall.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `whitened_share` | 0 to 1 | 0.5 | 0.55 | 0 | Share of doorsteps that are whitened or donkey-stoned (40 to 70 %; medium confidence for Durham). |
| `scrubbed_share` | 0 to 1 | 0.3 | 0.35 | 0 | Share that are only scrubbed pale. |
| `frame_m` | 0.03 to 0.12 m | 0.06 | 0.07 | 0.07 | Real width of the white frame along nosing and riser (4 to 10 cm). |
| `frame_dots` | 4 to 20 | 8 | 8 | 8 | Smallest frame width in plate dots (widened with distance up to Inflate Limit). |
| `boot_grey` | 0 to 1 | 0.3 | 0.3 | 0.3 | Boots grey the centre of the tread (30 %). |
| `dish_depth` | 0 to 0.012 m | 0.004 | 0.005 | 0.003 | Depth of the worn dish in the tread (relief, faded with distance). |
| `nosing_chips` | 0 to 1 | 0.3 | 0.3 | 0.2 | Share of steps with a chipped nosing or corner. |
| `wear_polish` | 0 to 1 | 0.4 | 0.5 | 0.2 | Polish of the worn centre. |

#### `wallgrowth` (WK WALL GROWTH), owner: walls, priority: SHOULD
Acts on roles: wall.masonry, wall.trim, wall.plaster, roof.tile (painted moss, algae, lichen). Reads masks: moss_site, algae_site, dampness, drip, lichen_site, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `moss_amount` | 0 to 2 | 0.5 | 0.4 | 1.2 | Painted moss at wall feet, drips, copings. |
| `algae_amount` | 0 to 2 | 0.8 | 1 | 1 | Green-black algae film at pipe outlets and shaded feet. |
| `lichen_amount` | 0 to 2 | 0 | 0 | 0.6 | Lichen. 1926 coal town: NONE (the smoke killed it). Courtyard: sparse colonies. |
| `moss_height` | 0.1 to 1 m | 0.3 | 0.35 | 0.5 | How high up a wall moss may reach from the foot. |
| `patch_dots` | 8 to 40 | 15 | 15 | 15 | Smallest moss patch width in plate dots (patches of 15 dots or more survive the painter). |
| `drip_moss` | 0 to 1 | 0.3 | 0.4 | 0.5 | Moss below run-off lines. |
| `cap_moss` | 0 to 1 | 0.3 | 0.3 | 0.6 | Moss along copings and wall caps. |
| `roof_moss` | 0 to 1 | 0 | 0 | 0.4 | Moss on roof surfaces (probably very little in 1926). |
| `tone_steps` | 3 to 6 | 5 | 5 | 4 | Number of flat painted tones in a moss patch. |
| `clump_stretch` | 1 to 3 | 1.8 | 1.8 | 1.5 | How much taller than wide a clump is (drip shape). |
| `relief` | 0 to 0.02 m | 0.005 | 0.006 | 0.008 | Height of moss relief (a bump on the incoming normal, faded with distance). |
| `lichen_dots` | 4 to 16 | 8 | 8 | 8 | Lichen disc size in plate dots. |
| `brightness_floor` | 0.12 to 0.4 | 0.25 | 0.25 | 0.25 | Lowest plate brightness of a moss patch (it must stay lighter than the stone and above the film-black zone). |

#### `wallcracks` (WK WALL CRACKS), owner: walls, priority: SHOULD
Acts on roles: wall.masonry, wall.trim, wall.plaster. Reads masks: corner, reveal, height, tx_cavity, house flag.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `crack_amount` | 0 to 2 | 0.3 | 0.3 | 0.5 | How many cracks (the master Amount scales it too). |
| `crack_dots` | 2 to 8 | 3.5 | 3.5 | 3.5 | Smallest crack width in plate dots (3 dots needs contrast 0.11). |
| `crack_contrast` | 0.04 to 0.2 | 0.11 | 0.11 | 0.11 | Smallest crack contrast against the surround. |
| `stepped_cracks` | 0 to 1 | 0 | 1 | 0 | Stepped mining cracks on the houses the set file flags (1 or 2 of 28). |
| `corner_chips` | 0 to 1 | 0.3 | 0.4 | 0.5 | Chips at wall corners and opening corners. |
| `chip_cm` | 2 to 12 | 5 | 5 | 6 | Chip size in centimetres (chips of about 5 cm and bigger read). |
| `plaster_cracks` | 0 to 1 | 0 | 0 | 0.5 | Map cracks and corner cracks in plaster. |
| `spall_patches` | 0 to 1 | 0.15 | 0.2 | 0.3 | Spalled patches near the foot. |
| `near_only` | 6 to 30 m | 15 | 15 | 12 | Cracks fade out beyond this distance (the painter invents its own texture there). |
| `slope_mm` | 0 to 5 | 1.5 | 1.5 | 1.5 | Real slope of a crack edge so a lamp lights one side. |
| `dull` | 0 to 1 | 1 | 1 | 1 | Cracks are dull: roughness back to 0.9, shine cut 35 %, water film cut 45 %. |

#### `paint` (WK PAINT), owner: walls, priority: COULD
Acts on roles: timber.paint (doors, window frames, fascia). Reads masks: height, footfall (door line), shade.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `paint_dark` | 0.5 to 1 | 0.85 | 0.78 | 0.9 | General darkening of paint (0.70 to 0.85 in 1926). |
| `flake_share` | 0 to 0.5 | 0.15 | 0.2 | 0 | Share of painted area that has lost flakes. |
| `door_scuff` | 0.1 to 0.5 m | 0.25 | 0.3 | 0.25 | Height of kicked scuffs at the foot of doors (bare grey wood). |
| `latch_grease` | 0 to 1 | 0.4 | 0.4 | 0.2 | Dark hand-grease patch at the latch. |
| `gloss_loss` | 0 to 1 | 0.4 | 0.5 | 0.3 | How much the paint has lost its gloss. |

#### `dirt` (WK GROUND DIRT), owner: ground, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (gravel and earth in other sets). Reads masks: footfall, keepclear, lowness, crown, wall_dist, shade, vertical_foot, prop_dist, seam_dist, entry_rand, step_foot.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `film` | 0 to 2 | 0.5 | 0.6 | 0.4 | Broad soft film of soot and dust, 0.5 to 3 m patches. NOT ash or coal dust (the rubbish layer has those). |
| `film_scale` | 0.5 to 4 m | 1.6 | 1.6 | 1.6 | Patch size of the film. |
| `film_darkness` | 0 to 0.6 | 0.25 | 0.3 | 0.2 | Darkening of the film (at most about one third). |
| `film_max_share` | 0 to 0.5 | 0.25 | 0.25 | 0.25 | Ceiling on the share of a surface the film may darken by a third or more. |
| `film_near_walls` | 0 to 1 | 1 | 0.5 | 1 | Keeps the film off the places the rubbish layer already dirties (wall foot, gutter strip). 1 = film everywhere; 0.5 = half strength there. |
| `polish` | 0 to 1 | 0.4 | 0.5 | 0 | Traffic polish: worn lanes are lighter and smoother. |
| `polish_lift` | 0 to 0.2 | 0.05 | 0.05 | 0.05 | Brightness added to polished lanes. |
| `polish_rough` | 0 to 1 | 0.3 | 0.3 | 0.3 | Roughness taken off polished lanes when dry. |
| `water_marks` | 0 to 1 | 0.3 | 0.4 | 0.3 | Dried puddle rings and tide lines in low spots. |
| `rust_halo` | 0 to 1 | 0.5 | 0.7 | 0 | Rust stain on the ground round the foot of iron posts and pipes (10 to 25 cm). |
| `rust_halo_m` | 0.05 to 0.4 m | 0.18 | 0.18 | 0.18 | Reach of the rust halo. |
| `drum_ring` | 0 to 1 | 0.5 | 0.5 | 0 | Rust bleed ring on the ground at the foot of the fire drum (the ash ring is already in the rubbish layer). |
| `tar_patches` | 0 to 1 | 0.3 | 0.5 | 0 | Tar patches over lost setts: scalloped edges, speckle of chippings. |
| `tar_max_share` | 0 to 0.06 | 0.03 | 0.03 | 0 | Ceiling on tar patches as a share of road area (2 to 4 %). |
| `tar_splash` | 0 to 1 | 0.3 | 0.3 | 0 | Splashes of tar at the kerb foot. |
| `tar_gloss` | 0 to 1 | 0.6 | 0.6 | 0.6 | How glossy new tar is (near black when wet). |
| `scrub_strip` | 0 to 1 | 0 | 0.6 | 0 | Pale scrubbed strip on the flags in front of a whitened or scrubbed doorstep (reads the same door random as the steps layer). |
| `scrub_strip_m` | 0.2 to 0.8 m | 0.4 | 0.4 | 0.4 | Reach of the scrubbed strip. |

#### `groundcracks` (WK GROUND CRACKS), owner: ground, priority: MUST
Acts on roles: ground.flag, ground.kerb, ground.sett (hard ground only). Reads masks: edge_dist, seam_dist, cover_dist, footfall, tx_cell (flags, setts), tx_cavity, crown.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `flag_cracks` | 0 to 2 | 1 | 1 | 0 | Amount of flag cracking. |
| `flag_fine_share` | 0.05 to 0.2 | 0.11 | 0.11 | 0 | Share of flags with a fine crack (8 to 15 %). |
| `flag_broken_share` | 0.01 to 0.06 | 0.03 | 0.03 | 0 | Share broken in two or three with a gap (2 to 4 %). |
| `flag_tilt_share` | 0.02 to 0.08 | 0.04 | 0.04 | 0 | Share tilted or sunk (3 to 6 %). |
| `tilt_lip` | 3 to 20 mm | 8 | 8 | 8 | Height of the raised edge of a tilted flag (throws a dark shadow line). |
| `corner_chip_share` | 0.03 to 0.15 | 0.07 | 0.07 | 0 | Share of flags with a chipped corner. |
| `kerb_chips` | 0 to 2 | 1 | 1 | 0 | Amount of kerb damage. |
| `kerb_chip_share` | 0.1 to 0.5 | 0.28 | 0.28 | 0 | Share of kerb length with edge chips (20 to 35 %). |
| `kerb_break_share` | 0 to 0.15 | 0.067 | 0.067 | 0 | Share of kerb stones cracked or broken (1 in 15). |
| `kerb_scuffs` | 0 to 1 | 0.3 | 0.3 | 0 | Pale wheel scuffs on kerb faces. |
| `kerb_joint_open` | 3 to 20 mm | 8 | 8 | 8 | Width of open, dark kerb joints. |
| `sett_disturb` | 0 to 2 | 0.7 | 0.7 | 0 | Amount of disturbed setts (tilted, sunk, missing, ash or tar filled). |
| `sett_disturbed_share` | 0.02 to 0.08 | 0.04 | 0.04 | 0 | Share of the sett field disturbed (3 to 6 %), gathered round seams, covers and wheel bands. |
| `open_joint_share` | 0.05 to 0.25 | 0.14 | 0.14 | 0 | Share of sett joints open and dark (10 to 20 %). |
| `missing_share` | 0 to 0.01 | 0.003 | 0.003 | 0 | Share of setts missing (dark rectangle). |
| `sunken_patch` | 0.3 to 1.5 m | 0.8 | 0.8 | 0.8 | Length of a sunken patch. |
| `crack_dots` | 2 to 8 | 3.5 | 3.5 | 3.5 | Smallest crack width in plate dots. |
| `crack_contrast` | 0.04 to 0.2 | 0.11 | 0.11 | 0.11 | Smallest crack contrast. |
| `near_only` | 8 to 30 m | 15 | 15 | 15 | Cracks fade out beyond this distance. |
| `max_contrast` | 0.4 to 0.9 | 0.75 | 0.75 | 0.75 | Guard: no harsh black grid. Sett joints may not exceed this contrast. |
| `dull` | 0 to 1 | 1 | 1 | 1 | Cracks are dull so the wet look cannot wash them out. |

#### `groundmoss` (WK GROUND MOSS), owner: ground, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (ground.earth, stone.natural in other sets). Reads masks: moss_site, algae_site, tx_cavity, tx_joint, shade, dampness, footfall, keepclear, existing_growth.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `joint_share` | 0.03 to 0.3 | 0.08 | 0.1 | 0.3 | Share of joint length carrying painted moss in the best (gutter-side) strip. |
| `shade_bias` | 0 to 1 | 0.6 | 0.6 | 0.6 | How much shade favours moss over sun. |
| `ribbon_dots` | 3 to 12 | 4 | 4 | 4 | Smallest moss ribbon width in plate dots (a 1 to 3 cm joint ribbon is drawn wider near the camera). |
| `ribbon_m` | 0.01 to 0.06 m | 0.02 | 0.02 | 0.02 | Real ribbon width. |
| `broken_len` | 0.1 to 0.8 m | 0.3 | 0.3 | 0.4 | Length of a broken ribbon piece. |
| `algae_fan` | 0 to 1 | 0.6 | 0.6 | 0.3 | Dark green-black algae fan under every downpipe outlet and gully. |
| `algae_radius` | 0.3 to 1 m | 0.55 | 0.55 | 0.55 | Reach of an algae fan. |
| `liverwort` | 0 to 1 | 0 | 0.1 | 0 | The one bright green: 0 to 2 patches of 10 to 40 cm in damp shade. |
| `far_band` | 0 to 1 | 0.5 | 0.5 | 0.3 | Beyond the pieces distance: a slightly greener, darker strip along gutter and wall foot instead of single plants. |
| `far_band_m` | 0.2 to 0.8 m | 0.45 | 0.45 | 0.45 | Width of the far band. |
| `moss_value` | 0.25 to 0.5 | 0.36 | 0.36 | 0.36 | Plate brightness of dry moss (lighter than the stone; painted values under 0.12 are black on the film). |

#### `iron` (WK IRON), owner: ground, priority: MUST
Acts on roles: iron, iron.post, iron.pipe, fire (cast iron, steel, drum, rails). Reads masks: height, object zmin and zmax, drip_kind, vertical_foot.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `rust_cover` | 0 to 1 | 0.3 | 0.35 | 0 | Share of the lower part of an iron object with paint chipped back to rust. |
| `rust_height` | 0.2 to 1.2 m | 0.55 | 0.55 | 0.55 | How high rust reaches from the foot of a post. |
| `chip_share` | 0.1 to 0.5 | 0.3 | 0.3 | 0.3 | Share of paint chipped in the rust zone. |
| `collar_spacing` | 1.2 to 2.5 m | 1.9 | 1.9 | 1.9 | Spacing of pipe collars and joints where rust rings sit. |
| `collar_rust` | 0 to 1 | 0.5 | 0.5 | 0 | Share of collars with rust. |
| `metallic_drop` | 0 to 1 | 0.6 | 0.6 | 0.6 | Rust lowers Metallic by up to this fraction (cast iron 0.6, steel 0.5, brass 0.9). |
| `heat_scale` | 0 to 1 | 0.3 | 0.3 | 0 | Heat-blued scale on the fire drum only. |
| `soot_halo` | 0 to 1 | 0.5 | 0.5 | 0 | Sooty halo above the drum vent holes and black rim. |
| `paint_keep` | 0 to 1 | 0.6 | 0.6 | 0.6 | Share of the original paint kept (black or dark green). |
| `rust_run` | 0.05 to 0.3 m | 0.12 | 0.12 | 0.12 | Length of rust runs below fixings. |

#### `growth` (WK GROWTH (3D pieces)), owner: growth, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (scatter targets; others by settings). Reads masks: weed_site, moss_site, keepclear, footfall, rubbish_heap, wall_dist, seam_dist, shade, dampness, existing_growth.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `weeds_amount` | 0 to 2 | 1 | 1 | 0.1 | Amount of weed pieces (grass tufts, rosettes). 0 = none. |
| `cushions_amount` | 0 to 2 | 1 | 1 | 1.5 | Amount of moss cushion pieces. 0 = none. |
| `distance` | 8 to 40 m | 18 | 18 | 25 | Pieces are laid only up to this far from the camera (the camera of the picture being drawn). |
| `distance_fade` | 2 to 10 m | 5 | 5 | 5 | Length of the fade-out at the pieces distance. |
| `piece_size` | 0.5 to 2 | 1 | 1 | 1 | Size of every piece (1 = as built to the period sizes). |
| `weed_cover` | 0 to 0.03 | 0.01 | 0.01 | 0.001 | Green cover of weeds as a share of ground area inside the pieces distance (0.5 to 2 % in 1926). |
| `gutter_tuft_share` | 0.02 to 0.1 | 0.05 | 0.05 | 0 | Share of gutter-side joint length with a visible tuft (3 to 8 %). |
| `wall_foot_share` | 0.01 to 0.08 | 0.035 | 0.035 | 0 | Share of wall-foot length with a plant (2 to 5 %). |
| `cushion_cover` | 0 to 0.03 | 0.008 | 0.008 | 0.02 | Moss cushion cover as a share of ground area inside the pieces distance. |
| `min_spacing` | 0.05 to 0.4 m | 0.15 | 0.15 | 0.15 | Nearest two pieces of one kind may be. |
| `toadflax_clumps` | 0 to 3 | 0 | 1 | 0 | Ivy-leaved toadflax trails on damp mortar: 0 to 2 clumps in the whole street. |
| `rubbish_thin_max` | 0.2 to 0.7 | 0.45 | 0.45 | 0.45 | Weeds grow at full density through rubbish thinner than this mask value. |
| `rubbish_heap_min` | 0.5 to 0.95 | 0.75 | 0.75 | 0.75 | No weeds (and no moss above 0.6) on rubbish heavier than this mask value; between the two it thins out linearly. |
| `dead_grass_share` | 0 to 0.5 | 0.15 | 0.15 | 0.15 | Share of grass tufts that are dead and straw-coloured. |
| `flower_share` | 0 to 0.3 | 0.08 | 0.08 | 0 | Share of dandelions in flower or seed-clock (a few only). |
| `max_pieces` | 500 to 6000 | 2500 | 2500 | 2500 | Hard ceiling on pieces in one picture (drawing time). |
| `wet_dark` | 0.4 to 1 | 0.7 | 0.7 | 0.7 | Colour multiple of wet pieces (richer green, darker). |
| `tilt_random` | 0 to 1 | 0.5 | 0.5 | 0.5 | How much each piece leans. |

**Colours** (plate sRGB 0 to 255 unless said; they are START values for the plate, to be tuned against the painter-size pictures; wet = dry x 0.76 to 0.88 for stone, brick, mortar, soot, wood; moss, algae and leaves darken more and get richer; whitening goes grey):

| layer | colour | sooty 1926 | courtyard | source |
|---|---|---|---|---|
| soot | soot tint | (77, 64, 56) | (92, 102, 77) grey-green dust and algae film | period G1; courtyard study 12b |
| runoff | washed pale stripe | wall colour x 1.10 to 1.25 (never below 0.18 plate brightness) | n/a | period G2, painted look 7 |
| runoff | rust streak | (120, 70, 45) dry, (80, 50, 36) wet | none | period S2 |
| foot | splash band | (62, 52, 45) dry, (45, 38, 33) wet | (95, 100, 85) dry grey-green | period G4 |
| foot | salt bloom | (215, 210, 200) | (225, 222, 212) | period S5 |
| steps | whitened stone | (228, 222, 208) dry, (170, 165, 150) wet | n/a | period S8 |
| steps | scrubbed sandstone | (195, 180, 155) dry, (145, 130, 108) wet | n/a | period S8 |
| wallgrowth / groundmoss | moss dry | HSV (98 deg, 0.45, 0.42) = (77, 107, 59) | the add-on moss tones (linear 0.035,0.075,0.022 / 0.085,0.15,0.04 / 0.15,0.22,0.065 / 0.055,0.105,0.03) | painted look 11; period M1; courtyard 12b |
| wallgrowth / groundmoss | moss wet | HSV (108 deg, 0.55, 0.30) = (43, 77, 34); never below plate 0.25 brightness for readability | brighter saturated green | painted look 11 |
| wallgrowth / groundmoss | algae film | dry (105, 112, 82), wet (48, 62, 42) | same | period M2 |
| groundmoss | liverwort | dry (95, 142, 65), wet (55, 110, 45) | n/a | period M3 |
| dirt | tar new / weathered / chippings | (24, 22, 20) glossy / (50, 48, 44) matt / (100, 98, 92) | n/a | period S6 |
| dirt | rust halo on stone | (160, 110, 80) | n/a | period S1 |
| iron | fresh rust / old rust | (150, 80, 45) / (90, 58, 42) | n/a | period S1, S3 |
| growth | weed leaf dry / wet | HSV (100 deg, 0.50, 0.40) = (68, 102, 51) / HSV (110 deg, 0.58, 0.30) = (40, 77, 32) | fresh green to yellow-green | painted look 11; period W1 |
| growth | dead grass / dandelion flower | (175, 152, 95) / (240, 195, 35) | straw | period W1 |

---

## Appendix B. Where each period rule goes

| rule | what | goes to | note |
|---|---|---|---|
| G1 | soot film on walls | `soot` | slot A, floor 0.30, pale-first |
| G2 | run-off streaks | `runoff` | pale stripes with dark tide-lines on sooty walls |
| G3 | soot under lintels, in reveals | `soot` (via `sheltered`, `reveal`) | |
| G4 | splash band at wall feet | `foot` | |
| G5 | door and glass grime | `paint` (COULD); glass is skipped | |
| G6 | soot on chimneys and roofs | `soot` (`stack_mult`, `roof_mult`) | the roof fan is not built |
| C1, C2, C3 | flag, kerb and sett cracks | `groundcracks` | slot B, dull |
| C4 | doorstep wear and chips | `steps` | |
| C5 | eroded mortar, spalled brick at the foot | `foot` (`mortar_wear`, `spall_share`) | |
| C6 | stepped mining cracks | `wallcracks` | two flagged houses; low confidence |
| C7 | peeling paint | `paint` | COULD |
| S1 | rust at lamp post foot | `iron`, `dirt` (rust halo on the flag) | |
| S2 | rust and damp streaks at downpipes | `iron` (collars), `runoff` (streaks on the wall), `foot` (pipe foot) | |
| S3 | fire drum rust, scale, soot | `iron`, `dirt` (`drum_ring`) | the ash ring is RUBBISH's |
| S4 | rust at railing feet, hinges, gratings | `iron` | |
| S5 | damp tide-mark, salt bloom | `foot` | |
| S6 | tar | `dirt` | capped, never straight-edged |
| S7 | limewash on yard walls | not built | nothing to put it on |
| S8 | whitened and scrubbed steps | `steps`, `dirt` (`scrub_strip`) | medium confidence |
| S9 | bird lime | not built | low value |
| W1, W2, W5 | weeds in setts, flags, gutter | `growth` (pieces), `groundmoss` (far band) | |
| W3 | plants at wall feet; toadflax | `growth` | |
| W4 | tufts in roof gutters | not built | |
| W6 | keep-clear zones | `keepclear` in the bus (inside every habitat field) | exactly zero |
| M1 | silver moss in joints | `groundmoss`, `growth` (cushions) | |
| M2 | algae film at drips and pipe outlets | `groundmoss` (ground), `wallgrowth` (walls) | |
| M3 | liverwort | `groundmoss` | 0 to 2 patches |
| M4 | moss and algae at wall feet | `wallgrowth` | |
| M5 | cushion moss on copings | `wallgrowth` (`cap_moss`); roofs off in the street | |
| L1 | lichen | `wallgrowth` (`lichen_amount` 0 in the street) | exactly zero |
| nothing modern | graffiti, lines, studs, bins, dishes, modern litter, oil, trench patches, flower boxes, buddleia | not built, not allowed | P4 |

