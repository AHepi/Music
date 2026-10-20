# 09 Recipe - wetness layer and specular map for the street - how it is made

What this file is: the plain-words record of the "wet street" test of the pit village set (the street view test, log 29 of the project story): one reusable **wetness layer** for Blender, the
materials it was put on, the **maps** (flat pictures, among them a **specularity map**) baked from it for the `.glb` file, the pictures drawn, how the `.glb` behaves in the three.js stage,
and everything that went wrong. It follows "09 Research - wet surfaces for the street set.md" (in `study/`). It has been through two rounds: round 1 built everything; a checker looked at it
and found eight problems; **round 2** (section 2) fixed what could be fixed. Sections 3 to 12 describe the state after round 2.
Nothing in the film project's own folder was changed: all work is on copies in `street_wet/` (the street copy is `set_copy/street.blend`; the film's shot file `lockout.blend` was opened
read-only, never saved). I did not run git.

Words used (one word for each thing, explained once):
* **set**: the 3D street built in Blender. **plate**: the one picture drawn from the set's camera, which the painter repaints. **painter**: the image model (Flux). **stage**: the film program (three.js) that shows the painting shone back on the set.
* **glb**: the single file that carries the set from Blender to the stage. **map**: a flat picture that holds one number for every dot instead of a colour (roughness map, specularity map ...).
* **roughness**: how blurry reflections are. 0 is a mirror, 1 is chalk. Example: wet glass is near 0.05, dry brick near 0.9.
* **specular** (the "shine"): how strongly a surface reflects light that hits it head-on. Blender calls the dial "Specular IOR Level": 0.5 is normal (about 4 %), 0.75 is a wet surface (about 6 %), 0 is none. A **specularity map** holds that strength for every dot.
* **clear coat** ("coat"): a thin clear layer on top, like varnish on a table or a film of water on stone; it reflects on its own whatever is underneath.
* **node group**: a small packaged recipe made of Blender's node boxes, which can be dropped into any material. The **wetness layer** is one.
* **porosity**: how much a material soaks water up (brick and sandstone soak a lot, glazed tile and iron do not). **puddle dial**: the layer's "Puddles" setting.
* **Cycles**: Blender's exact, slow renderer. **EEVEE**: its fast renderer, which the film's plates are drawn with. **UV2**: a second set of texture coordinates on a mesh, so a map can be laid on it a different way from the photo (here: once over the whole street, nothing repeats).
* **sample**: one pass of EEVEE or Cycles over the picture; the picture is the average of many samples, so more samples = smoother picture and a longer wait.
* **grain** (my measure of speckle): for a kind of surface, the average difference between a dot and the average of its four neighbours, on a 0 to 1 brightness scale. A dry road is 0.002 to 0.003; a road that looks covered in white grit is 0.026.
* **ray tracing** (an EEVEE setting): EEVEE follows rays to find what a glossy surface reflects; without it a puddle only shows the flat colour of the sky. **soft shadow**: the blurred edge of a shadow made by a lamp that has a size (the gas lamps are 12 cm across, the window lights 50 cm).

---

## 1. The short answer (after round 2)

1. **A wetness layer exists and works.** One node group, `WETNESS`, in `tools/wetness_layer.py` (plain Blender nodes, no add-on, 35 controls, 11 outputs). It sits between any material's dry look and its Principled BSDF and gives back the wet look: darker, smoother, shinier, with puddles in the low spots, a wet foot and rain streaks on walls. `sheets/wetness_layer_five_surfaces.jpg` (round 1) shows it on five different surfaces.
2. **It is on the street** (`tools/apply_wetness_to_set.py`): road setts, pavement flags, gutter and kerb stones, brick and stone cottage walls (wet foot, streaks under every sill and the eaves), colliery brick, two dressed stones, slate roofs, the yard. Nothing was replaced by a texture recipe (the plan: only the road setts could be, only if a painter test asks for it; no painter test was run).
3. **The white grit the checker found on the wet road in EEVEE is cured, and it was NOT what we thought.** It is noise in EEVEE's soft shadows, seen in the sheen of a wet surface, not the stones' fine relief picture (section 2, problem 1). The cure is two EEVEE settings for the plate (shadow rays 4, shadow steps 16) plus 32 to 48 samples: grain on the left third of the road falls from 0.026 to 0.008 at 48 samples.
4. **The walls are now darker wet, with a wet foot** (they were lighter): in the close view the lower wall is 0.66 of its dry brightness and the whole wall 0.88; in the main view the whole wall is 0.84 and the lowest eighth of it 0.66 (section 2, problem 2).
5. **The wet road is 1.50 times today's road in EEVEE** (aim 1.5; round 1 measured 2.0 in Cycles; in EEVEE with its default shadows it was 1.67, because the soft-shadow noise also leaks light).
6. **A full-size EEVEE wet plate with the lockout props was drawn** (section 2, problem 4): `work/r35/main_wet_plate.png` (1536 x 2730, the film's own lockout shot file with its props, opened read-only; EEVEE, ray tracing on, shadow rays 4 / steps 16, 32 samples; wet 0.85 / puddles 0.5; it took 20 min 27 s). It reads as a street after rain at dusk, with no white speckle at full size. Two things to know: the brazier's reflection on the road is blown out (4.5 % of the lower third of the plate is over 0.97, 1.6 % of the whole plate) and the props stand dry on the wet road (section 2, problem 4).
7. **The maps and the wet `.glb` were baked again** with the round 2 layer (`maps/`, `glb/street-wet.glb`). **They are insurance, not the wet look of the film.** The stage as it is today throws away the glb's roughness, coat and specular and shows the PAINTING almost everywhere, so what the audience sees as wet is whatever the painter paints from the plate (section 2, problem 3). **The specularity map by itself changes the picture very little; the roughness map is what makes a road look wet.** I do not claim the specularity map makes the film wet.
8. **Not done, and why:** the painter (Flux) was not asked to repaint the wet plate: it costs about 10 US cents a painting and needs your go-ahead. The plate is ready for it (section 2, problem 4).

---

## 2. Round 2: what the checker found, what I did, what came out

The checker re-drew my pictures (they matched exactly), measured them in EEVEE, and listed eight problems. In order of how much they matter:

### Problem 1: white grit on the wet road in EEVEE (the plate renderer)

*What the checker saw:* in an EEVEE picture the left third of the wet road had grain 0.029 (Cycles wet 0.007, dry 0.0035). The cure I had written for the pavement (flatter relief, rougher) left the road at 0.029.
*What I believed:* the stones' fine relief picture (the normal map) throws a glint at every dot. *That was wrong.* It took five runs to find out. In the order I tried them (left third of the road, 540 x 960 main-camera picture, EEVEE with ray tracing on, grain; dry is 0.0025):

| what I changed | left-third grain | what it tells |
|---|---|---|
| round 1 look (sharp relief, flatten 0.35, rougher 0.3) | 0.0265 | the problem, reproduced |
| relief picture blurred 2 dots wide (4 mm), road flattened 0.6, pavement 1.0 (the first round 2 setting) | 0.0261 | not the relief |
| relief taken away altogether | 0.0197 | a little, not the cause |
| no relief-height picture / no roughness picture / no colour picture | 0.0254 / 0.0261 / 0.0246 | not these |
| ray tracing at full size, best quality, rougher surfaces allowed | 0.0260 | not the ray tracing |
| ray tracing off | 0.0234 | not the ray tracing |
| brightness clamps, bigger shadow memory, EEVEE's cheap bounce light off | 0.0261 / 0.0261 / 0.0260 | not these |
| window lights made 0.1 m across instead of 0.5 m; shadow maps twice as fine | 0.0260 / 0.0261 | not the light size, not the shadow map size |
| wet road rougher (0.5 instead of 0.3) | 0.0179 | helps a third, not the cause |
| **shadows switched off** | **0.0080** | **it is the shadows** |
| **shadow rays 4 and steps 16** (EEVEE's maxima; its defaults are 1 and 6) | **0.0119** | the cure |
| the same with 48 samples | 0.0078 (pavement 0.0071) | under the checker's aim of 0.008 |

*What it is:* EEVEE blurs the edge of a lamp's shadow by sending a few rays through the shadow map, and with the defaults (1 ray, 6 steps) the answer for each dot is a little random. On a dry road the shine is weak so nobody sees it. On a wet road the shine is strong, so the randomness shows as white speckle. It also **leaks light**: with correct shadows the wet road is 10 % darker (0.220 to 0.192). `sheets/eevee_grit_cause_and_cure.jpg` shows dry, the speckle, shadows off (a diagnosis only: lights shine through walls, so it is much too bright), and the cure.
*Why Cycles never showed it:* Cycles works shadows out by tracing rays, not with shadow maps, and round 1's Cycles pictures were also cleaned by a noise filter.
*What I did:* nothing in the material needed to change for this. It is a PLATE SETTING (section 7): `shadow_ray_count 4`, `shadow_step_count 16`, 32 to 48 samples. The film's own plate script (`set_dressing.py`, `render()`) does not set them; two lines would. I did not touch it.
*Cost:* a 540 x 960 picture: 56 s with the defaults, 92 s with rays 4 / steps 16 at 16 samples, 357 s at 48 samples (machine shared with other work).
*Still open:* at 16 samples the left third still shows grain 0.0115 and the left pavement 0.011; at 48 samples 0.008 and 0.007. The full-size plate has more dots, so each dot's speckle is the same but looks finer after the painter shrinks the picture; I measured the plate: on its left road patch, shrunk to 540 x 960 so that it can be compared, grain is 0.0059 against 0.0046 for the dry lockout picture and 0.0062 for the 16-sample wet one; the middle road patch 0.0068 (16-sample wet 0.0046, dry 0.0090: the dry road there is textured by the brazier's light). Below 0.008 everywhere I looked, at full size 0.0049 with no dot-scale speckle. (The lockout camera sees less of the speckle-prone left side than the street's main camera does.)

### Problem 2: walls lighter wet than dry, no wet foot

*What the checker saw:* walls 1.16 times brighter wet (close view), 1.30 times (main view, Cycles), only 6 % of wall dots darker.
*What I found:* two causes. (a) The wet band at the foot was measured from the pavement, but each cottage's floor stands 0.15 to 0.46 m above the pavement and a dressed-stone plinth covers everything below the floor, so the band was hidden. (b) The shine added by wetness (roughness 0.45, clear coat 0.3, extra specular) outweighed the darkening; my reading, not separately proved, is that the gas lamp a metre from the wall lights the lower wall at a slant and a smoother surface throws more of that light at the camera. I also tried roughness 0.75 and found the lamp-lit base of the wall still came out brighter (1.04); at 0.9 (the same as dry) the wall only gets darker.
*What I did:* the band is measured from the cottage floor in the cottage's own coordinates (slope 0, offset 0) and is 0.9 m tall with a wavering top; the walls get no extra shine (Specular Boost 0, no coat, wet roughness 0.9); the darkening is stronger (porosity 1.0, darkest 0.2); the streaks under the sills and eaves are stronger (0.9 of the wet value instead of 0.7).
*Result* (`tools/24_wall_ratio.py`, EEVEE, wet over dry brightness; `sheets/wall_foot_round1_vs_round2.jpg`):

| | round 1 settings | first round 2 try (roughness 0.75) | wall roughness 0.9, plinth unchanged | **final** (also darker plinths and dressed stones) |
|---|---|---|---|---|
| close view, whole wall | 1.12 | 1.06 (0.96 with no coat) | 0.93 | **0.88** |
| close view, lower wall right of the lamp | 1.15 | 0.77 | 0.68 | **0.66** (89 % of its dots under 0.75) |
| close view, strip just above the plinth | - | 1.04 | 1.04 | **0.85** |
| main view, whole wall | 1.03 | 0.88 | - | **0.84** |
| main view, lowest eighth of the wall | - | 0.77 | - | **0.66** |

The checker's aim was a clear blue band at the foot, at least a quarter darker, and a wall mean under 1.0. The wall means, the lower wall (0.66) and the lowest eighth in the main view (0.66) meet it. The thin strip just above the plinth was 1.04 until I gave the plinth and the other dressed stones a splash band from the pavement (porosity 0.8, darkest 0.3, 0.6 m): the strip's mask also catches the plinth's lit edge, and it now reads 0.85, which is not a quarter darker. The picture `sheets/wall_wet_over_dry_final.jpg` shows the whole thing: a blue-purple wet foot and lower wall, grey upper wall. The final numbers come from a re-draw (`work/r36`) made after the last settings change.
Streaks under the sills: visible in the masks (`work/r30/wall_masks_both.jpg`); in the close lit view I could not pick them out from the darker foot band, and I did not measure them separately.

### Problem 3: the glb maps do not reach the film

*What the checker found (and I had said):* the maps are in the glb and three.js reads them, but the stage replaces every material with a matte copy and shows the painting at its painted brightness, so only about 2 % of a moved view wears the glb's own surface; matte on or off differs by 0.002. The specularity map alone does almost nothing.
*What I did:* re-baked everything with the round 2 layer and re-ran the stage check (section 9). Nothing in the stage was changed, as that is the film's code.
*Plainly:* the glb's roughness, coat and specularity pictures are **insurance** for a later stage change, for the plate (they are what the layer writes into the plate through the live materials), and for surfaces the painting does not cover. **If live reflections ever matter** (a reflection that moves as the camera moves), the way is a later stage change: matte OFF for the ground only, and the stage's match tint re-tuned from about 1.6 to 2.5 down to about 0.29 (measured in round 1: with matte off the uncovered surfaces come out 4.7 times brighter). I did not do it. A painted reflection stays stuck on the road when the camera moves (my estimate from round 1: about 0.9 m of drift at 12 m for a 1.4 m forward move; not tested).

### Problem 4: the painter was not tried, and the plate had two weak spots

*What the checker said:* ask for a go-ahead on one repaint of the EEVEE wet plate; give the puddles a bright reflection so they read as water; round the puddle edges; trim the road to about 1.5 times today's.
*What I did:* the road is 1.50 times today's in EEVEE (Specular Boost 0.25 and Film Coat 0.3 stayed; the drop came from the correct shadows). Puddle depth now leans 40 % on Lowness (was 25 %), 40 % on a slow wobble, 20 % on the relief (was 25 %); the puddle edge is softer (0.10 against 0.06) and the wobble smoother (2 octaves, not 3). The dial was fitted again (section 9). I did not add an artificial reflection: puddles show what is there (dark houses, the lit windows, the lamps, in the lockout shot the brazier). In the EEVEE pictures the large gutter puddles show the house fronts and a warm window or lamp patch; there are only two or three tiny puddles on the crown at heavy rain, and I saw no isolated mid-road island in the heavy picture (`work/r31/heavy_lower_2x.jpg`).
*Not done:* **the repaint.** It costs about 10 US cents a painting and needs your go-ahead. The painter's brief has to change first: it says "matte painted finish" and, in its never-add list, "puddles or reflections" (a painted wet ground was repainted dry once, Decisions item 25). The brief should say: keep the wet sheen, the lamp reflections and the puddles exactly where image 1 has them. Whether the painter keeps them, or reads the puddles as dark stains, is unknown.
*The full-size plate* (`work/r35/main_wet_plate.png`, half-size look `work/r35/plate_wet_half.jpg`, 100 % crop `work/r35/plate_wet_crop_lowerleft_100pct.jpg`, today-against-wet at 540 x 960 `sheets/lockout_today_wet_eevee.jpg`): wet setts reflect the handcart and the sacks softly, the gutters and the right pavement shine, the brazier lights a reflective pool. **Weak spots I can see:** (a) that pool is blown out (4.5 % of the lower third of the plate is over 0.97, none in the dry picture): if the painter turns it into a glare patch, lower the road's Film Coat and Specular Boost (0.3 and 0.25) first; not tried; (b) the props stand dry on the wet road, with no wet contact; (c) the puddles at dial 0.5 are small in this view (8 % of the road): the wet look here is mostly sheen. The lower third of the plate is only 1.18 times as bright as the dry one, because the brazier already lights it dry.

### Problem 5: pavement flags read as dry

*What I did:* flags: wet roughness 0.35 (round 1 had 0.45 and the EEVEE cure had 0.6), Relief Flatten 1.0, the smoothed relief picture. With correct shadows the flags are 1.12 times today's brightness (the road 1.50): they catch the lamp glow where it falls (right pavement) and are plain wet slabs elsewhere. I did not push them brighter. `sheets/street_dry_wet_eevee.jpg`.

### Problem 6: rows of gold pin-prick glints on the setts in the middle distance

*What I did:* the road's wet relief picture is blurred 4 dots wide and Relief Flatten is 0.7 (was 0.35). *Result:* the glints are still there in the 16-sample pictures as short white ticks on sett corners in the middle distance (`sheets/street_dry_wet_eevee.jpg`, `sheets/road_closeup_round2.jpg`); I did not measure them. The painter will probably drop them. Open.

### Problem 7: heavy-rain puddles (isolated cyan island, puddles on the crown)

*What I did:* Lowness weighs 40 % in the puddle depth. In the EEVEE heavy picture the puddles are in the gutters, round-edged; I found no isolated island in it. I did not change the puddle tint (reflections are what the world gives: the dusk sky is teal). **Pavements get 35 % puddle at the heavy setting (0.8) in the main view, against 30 % for the road**, because Puddle Bias is a shift and the pavement's depth rises quickly; use a larger Puddle Bias (0.3) on pavements for heavy rain. Open.

### Problem 8: stand-in numbers in the glb too bright (dressed stone 1.41, roofs 1.23, colliery brick 1.70 times live)

*What I did:* the flat numbers for the materials without maps now follow each material's own settings (coat = its Film Coat times wetness, specular = 0.5 + its Specular Boost times wetness, roughness = its soaked value) and the colour ratios were measured again with the round 2 settings. *Result* (`tools/31_compare_baked_live.py`: the baked street, which wears only the maps and flat numbers that go into the glb, drawn in EEVEE against the live layer, main camera): dressed stone 1.12 times live (round 1: 1.41), roofs 1.03 (1.23), colliery brick 1.13 (1.70). The first bake gave 1.21, 1.04 and 1.24; I then multiplied the flat colour numbers of dressed stone, slate and colliery brick by live / baked (they are now fitted to the main camera, not measured: see the note in `06_bake_maps_and_export.py`) and rebuilt the glb in seconds with `--reuse`. Still a little too bright: a flat surface that is "wet all over" shines more than a surface wet in places.

### Runs, and what it cost

18 Blender runs in round 2 (budget: about 10; one of them a two-second look at EEVEE's settings). Five were the search for the cause of problem 1 (the part-picture test, the whole-picture test, and three more that took things away one at a time) and one more tested the road and pavement settings; then: two wall runs, the quick calibration run (puddle sweep, colour ratios and wall masks in one go), two sets of final pictures (the second after the last settings change), a lockout check, the bake (8.5 minutes), two baked pictures, the lockout pictures with the full-size plate, and a glb rebuild. Times are in section 10.

---

## 3. What wetness does to a material, and why (example first)

**Example.** A dry cobbled road at dusk: dark grey-brown, chalky (roughness 0.9), no reflections. After rain the same road is **darker**, **smooth** (lamp light streaks across it), has a thin **shiny film**, **flat mirror puddles** in the low spots, and the stone tops, which drain first, stay a little drier than the joints. The cottage walls next to it are **darker at the foot** where rain splashes and rising damp collect, and have **streaks** running down from the sills and the eaves; they do not turn glossy.

The layer makes those changes, each from a rule you can switch off alone:

| change | why it happens in life | what the layer does | switch |
|---|---|---|---|
| darker, richer colour | water in the pores and on the surface traps light | colour x a darkening that grows with porosity and wetness; a little more colour | Colour Effect |
| smoother | water fills the pores | roughness slides to Wet Roughness (0.3 for the road; 0.9 = no change for walls); puddles go to Puddle Roughness | Roughness Effect |
| a shiny film | water (index 1.33) reflects about 2 % head-on and nearly everything at grazing angles | Specular IOR Level 0.5 up to 0.5 + Specular Boost, and a coat of weight Film Coat x wet (up to 1 in puddles) | Specular Effect, Coat Effect |
| puddles | water gathers in low spots | a "depth" from slow wobble (40 %), the caller's Lowness (40 %) and the relief's low parts (20 %), cut by a soft threshold the dial moves | Puddles dial |
| flat water | thick water hides the relief; water fills the finest grain first | the relief slides first to a smoothed copy (Grain Fill), then toward the plain surface normal (fully in puddles, Relief Flatten x wet elsewhere) | Normal Effect, Relief Flatten, Grain Fill |
| wet walls | splash and rising damp at the foot, rain running from sills and eaves | a band at the foot (wavering top edge), a general damp, general streaks, and streaks hanging from every window sill and the eaves | Wall Band, Wall Wetness, Streaks, Drip Mask |

Measured on the main camera: colour alone is nearly invisible at dusk, smoothness is the big change, the film adds the lamp pools, puddles add the mirrors. **A specularity map alone, without lower roughness, would not look wet.**

---

## 4. The layer: every control (`tools/wetness_layer.py`)

Plug the dry look in and plug the outputs into the Principled BSDF (Colour to Base Color, Roughness to Roughness, Specular IOR Level to Specular IOR Level, Coat Weight to Coat Weight, Coat Roughness to Coat Roughness, Normal to Normal), and set Coat IOR to 1.33. `add_wetness_to_material(material, ...)` does all of that for a photo-textured material.

**The dry look (plug in)**

| input | what it is |
|---|---|
| Colour | the dry colour picture |
| Roughness | the dry roughness: a number or a roughness picture |
| Height | the dry relief height, 0..1 (0.5 = flat); lets stone tops stay drier and water gather in joints |
| Normal | the dry normal (bumpy look from a normal map); the plain surface normal if there is none |
| **Wet Normal** (new) | the same normal but made from a SMOOTHED copy of the relief picture (finest grain blurred away; make it with `tools/20_make_smoothed_pictures.py`). With none given, `add_wetness_to_material` plugs the dry normal in again, so Grain Fill does nothing. |

**Where am I**

| input (default) | what changing it does |
|---|---|
| Use World Geometry (1) | 1: the layer reads the object's world position and surface direction itself. 0: it uses Position and Surface Up. Use 0 for walls (measure in the wall's OWN coordinates, so every copy of a shared wall mesh gets the same wet pattern, which a baked map needs) and for flat texture tiles. |
| Position, Surface Up | used only when Use World Geometry is 0 |

**How wet**

| input (default) | what changing it does |
|---|---|
| Wetness (0.8) | 0 = bone dry, the layer gives the dry look back unchanged; 1 = soaked |
| Puddles (0.5) | 0 = none. Calibrated (round 2): the main camera's road is 2.9 / 8.1 / 14.9 / 30.1 % puddle at 0.3 / 0.5 / 0.65 / 0.8 (section 9) |
| Seed (0) | any number; moves the puddles and streaks |

**The material**

| input (default) | what changing it does |
|---|---|
| Porosity (0.6) | how much it darkens: walls 1.0 (round 2), brick 0.7, stone 0.6, slate 0.3, painted wood 0.2, metal 0 |
| Darkest (0.45) | how dark a fully porous, soaked surface gets as a share of dry. Walls use 0.2 (a fully wet foot ends at about a third of its dry colour), setts 0.45 (colour ends at about 0.72 of dry) |
| Wet Roughness (0.3) | roughness of a soaked surface: 0.3 for the road, 0.35 for flags and kerbs, 0.9 for walls (= dry: walls only darken). EEVEE's ray tracing setting `trace_max_roughness` is 0.5 by default (my reading: rougher surfaces are not traced; not tested) |
| Puddle Roughness (0.08) | 0.03 is a perfect mirror and goes black wherever it reflects only dark houses; 0.08 reads as water without going black |
| Specular Boost (0.25) | how far the shine rises when wet (0.5 to 0.5 + this). 0 for walls, 0.05 slate |
| **Film Coat** (new, 0.3) | strength of the thin water film outside puddles (a coat weight of 0.3 x how wet it is). Round 1 had this fixed at 0.3 for everything, which made walls and roofs too bright. 0 for walls |
| Relief Flatten (0.35) | how much of the relief water smooths away on wet ground (after Grain Fill); the road uses 0.7, flags 1.0 |
| **Grain Fill** (new, 1) | how much of the relief's finest grain water fills when wet: 0 = the sharp relief always, 1 = the smoothed Wet Normal when wet |
| Puddle Darkness (0.9) | colour under standing water as a share of the wet colour; kept high so puddles do not go black |
| Puddle Bias (0) | moves the puddle threshold for one material: plus = fewer puddles. Pavements use 0.22 (about 2.5 % of the pavement is puddle at dial 0.5, main camera) |

**Where the water goes**

| input (default) | what changing it does |
|---|---|
| Lowness (0.5) | how low this spot is, given by whoever puts the layer on. The road: 0 on the crown, 1 at the gutter; the pavement: 1 at the kerb to 0 at the houses; the gutter: always 1 |
| Dry Tops (0.5) | how much the high parts of the relief (stone tops) stay drier |
| Water Level (0.65) | how high puddles reach on the Height scale |
| Ground Slope (0.0699), Ground Offset (0) | the ground rises this many metres per metre along +y (the street: tan 4 degrees). The layer measures height above the ground as z - y x slope - offset. **For the cottage walls in their own coordinates: slope 0, offset 0** (round 2: local z = 0 is the cottage floor); stone and dressed stone measured in the world use the street slope and offset 0.13 |
| Wall Band (0.45) | metres the wet band at the foot reaches: walls 0.9, dressed stone 0.6 |
| Wall Wetness (0.35) | how wet the whole wall face is |
| Streaks (0.5) | strength of the general vertical rain streaks |
| Drip Mask (0) | rain running from sources the caller knows; made by the sub-group `WETNESS DRIP` |

**Switches** (0..1, default 1): Colour Effect, Roughness Effect, Specular Effect, Coat Effect, Normal Effect. 0 gives that part's dry value back (for tests, or to turn one part off).

**Outputs**: Colour, Roughness, Specular IOR Level, Coat Weight, Coat Roughness, Normal, Height (after water fills the puddles), Wet Mask, Puddle Mask, Streak Mask, Puddle Depth (the number the puddle threshold is cut from; the calibration reads it).

**Fixed numbers inside** (at the top of the file, named): the dial's threshold = 0.79 - 0.52 x dial^1.25; puddle depth shares 40 / 40 / 20 %; puddle edge softness 0.10.

**The sub-group `WETNESS DRIP`** (inputs Position, Centre, Half Width, Top, Length, Seed; output Mask): one rain streak hanging from one source: ragged sides, lines stretched downward, strength fading with distance below the source. `drip_chain()` makes one per source and joins them. For the street cottages the sources come from the street builder's own numbers (`FACADE_LAYOUTS`, `GROUND_WINDOW`, `UPPER_WINDOW`, `EAVES_HEIGHT`): one under each window sill and two wide ones under the eaves. Picture: the green in `work/r30/wall_masks_both.jpg` (red = wet, green = streaks; the foot band is red up to about a metre).

---

## 5. The street: which materials got what (`tools/apply_wetness_to_set.py`, table `MATERIALS`)

| material | share of main view | Poly Haven maps added | porosity (darkest) | wet roughness | other |
|---|---|---|---|---|---|
| street_setts (road) | 33 % | roughness, height, relief smoothed 4 dots | 0.6 (0.45) | 0.3 | Lowness crown 0 to gutter 1; Relief Flatten 0.7; Film Coat 0.3; boost 0.25 |
| pavement_flags | 2.4 % | roughness, height, relief smoothed 2 dots | 0.55 (0.45) | 0.35 | Relief Flatten 1.0; Puddle Bias 0.22; Lowness 1 at kerb |
| channel_stones (gutter) | 1.2 % | none | 0.5 (0.45) | 0.3 | always wetter: Wetness x 1.15, Lowness 1 |
| kerb_stone | 1.2 % | none | 0.5 (0.45) | 0.35 | Wetness x 1.05, Lowness 0.3 |
| cottage_brick (left walls), cottage_stone (right walls) | 5.7 %, 5.6 % | roughness, height | **1.0 (0.2)** | **0.9** | measured in the cottage's own coordinates, band 0.9 m from the floor; one material copy per facade layout carrying its own sill and eaves streaks; boost 0, coat 0 |
| colliery_brick | 5 % | none | 0.7 (0.45) | 0.5 | boost 0, coat 0.05 |
| dressed_stone, dark_dressed_stone (plinths, sills) | 4.4 %, 1.4 % | none | **0.8 (0.3)** | 0.6 | measured from the pavement (offset 0.13), band 0.6 m; boost 0, coat 0 |
| roof_slate | 1.0 % | none | 0.3 (0.45) | 0.4 | boost 0.05, coat 0.05 |
| colliery_yard | 0.4 % | none | 0.7 (0.45) | 0.4 | - |

Not touched: metals, paints, windows, lamp glass, the sky dome, props (later or never for this view). Colour ratios measured with no lighting (wet 0.85 / puddles 0.5, wet colour as a share of dry; `tools/04b_colour_ratios.py`, `work/r30/colour/`): setts 0.72, pavement 0.78, kerb 0.76, gutter 0.69, brick walls 0.70, stone walls 0.72 (main view; 0.59 to 0.65 in the close view where more of the wall is foot), colliery brick 0.86, dressed stone 0.88 / 0.82, slate 0.90, yard 0.56.

---

## 6. The maps and what each is for (`tools/06_bake_maps_and_export.py`)

How they are made: a camera looks straight at the flat surface (orthographic, 8 light samples a dot, no lighting at all) and draws one output of the layer as plain light, so every dot holds exactly one number. This is the trick `lib/bake_harness.py` uses for the texture recipes. The ground is photographed from above as ONE picture of the whole street (x -4.4 to 4.4 m, y -12 to 72 m, 48 dots a metre = 2.1 cm a dot, 422 x 4032 dots); the four cottage fronts square-on (200 dots a metre = 0.5 cm, 900 x 1380 dots each, one picture serves every cottage of that kind).

| map (file) | what it holds | goes into (glTF slot, verified in the exported file in round 1) | for |
|---|---|---|---|
| wet colour (`ground_colour.jpg`, `wall_*_colour.jpg`) | the dry colour darkened and enriched where wet | base colour | the wet look in the glb |
| **roughness** (`*_roughness.png`) | 0.9 dry, 0.3 film, 0.08 puddle | green channel of the metal-roughness picture | the glossy road |
| **clear coat** (`*_coat.png`) | 0 dry up to 1 in puddles (walls: 0 everywhere in round 2) | red channel of the clear coat picture | the water film |
| clear coat roughness (`*_coat_roughness.png`) | 0.2 film, 0.08 puddle | green channel of the same picture (the exporter packs the two into one) | sharpness of the film's reflection |
| **specularity** (`*_specularity.png`) | reflection strength as a share of its biggest value: 1 = the wet shine (Specular IOR Level 0.75), 0.67 = a dry surface's normal shine (0.5). Walls: 0.67 everywhere (round 2 gives them no extra shine) | alpha channel of the specular picture; with a colour factor of 1.5 so the map's 1 means 1.5 times normal | tells the stage where the surface shines more |
| wet normal (`ground_normal.png`) | the layer's normal in the street's slope frame | not used (2 cm dots wash out the joints between setts); the glb wears the SMOOTHED photo relief picture on the first coordinates instead | checking |
| puddle mask, wet mask (`*_puddles.png`, `*_wet.png`) | where puddles and wet are | not exported | checking and compositing |

All of it is on the second texture coordinates (UV2). Everything not baked (kerbs, roofs, stone dressings, colliery brick, yard, chimneys) gets one flat set of wet numbers in the glb: its colour x its measured wet share (round 2 table above), its soaked roughness, coat = its Film Coat x wetness, specular = 0.5 + its Specular Boost x wetness.

**How a specularity map travels** (found by reading the exporter in round 1, checked in the file). The exporter puts a picture wired into "Specular IOR Level" into the ALPHA channel of the glTF specular picture, and only reads a grey picture's alpha unless a Separate Color node is in the path. So the baked material wires: picture, Separate Color (Red), Math multiply by 0.75, Specular IOR Level; the exporter then writes the specular picture and a colour factor of 1.5. In glTF a picture alone can only LOWER the normal reflection per dot; the factor 1.5 is what lets the map's 1.0 mean "wet shine". At grazing angles three.js uses the map value for the strongest reflection too (dry dots 0.67 instead of 1): slightly less grazing shine on dry dots than Blender has. Not measured.

Sizes after round 2: `maps/` 9.8 MB (8 ground maps, 24 wall maps); `glb/street-wet.glb` 23.7 MB, 45 materials, 56 pictures, 135 meshes, 7 of them (3 ground, 4 wall) with a second set of texture coordinates. The bake took 8.5 minutes this time (round 1: 13 minutes).

---

## 7. Plate settings: what to change in the film's plate drawing for a wet street

The film draws its plates with EEVEE at 1536 x 2730, 48 samples, ray tracing OFF (saved in the three shot files). For a wet street these have to change (all of it is in `set_dressing.py`'s `render()` and in `build_street.py`'s `picture_settings()`, which I did not touch):

| setting | today | for a wet plate | why |
|---|---|---|---|
| ray tracing (`scene.eevee.use_raytracing`) | off | **on** | with it off, puddles are pale flat patches of the world's blue; with it on they mirror the houses, windows and lamps |
| `scene.eevee.shadow_ray_count` | 1 (default) | **4** | the white speckle (problem 1) |
| `scene.eevee.shadow_step_count` | 6 (default) | **16** | same |
| samples | 48 | 48 (measured: 16 samples 0.0119, 48 samples 0.0078 on the road's left third; 32 was used for the lockout plate: see section 9) | less speckle |
| shadow memory / scale for wide pictures | `shadow_pool_size '1024'`, scale 1080 / width | keep | the film's own fix for "Shadow buffer full" |

Cost: about 1.6 times longer for rays 4 / steps 16 at the same samples. A full-size plate of the lockout shot (1536 x 2730, 32 samples, rays 4 / steps 16, ray tracing on) took 20 min 27 s; the same shot at 540 x 960 and 16 samples took 3 min 40 s (the dry one 3 min 47 s), so the lockout file with its props and lights costs about three times what the bare street does. About 50 minutes would be expected at 48 samples (not run). The EEVEE wet road comes out cold blue-grey with warm patches only where a lamp or window lights it, because a glossy surface reflects the dusk sky and the dark blue world (the dry road is warmer). The checker saw "no warm lamp pool": in EEVEE the lamp pools are on the pavement and in the gutter puddles; my reading (not tested) is that Cycles' long lamp streaks on the road came from reflecting the glowing lamp glass, which EEVEE at roughness 0.3 smears into almost nothing. I did not add anything to fake it.

---

## 8. How to put the layer on another set

1. Copy `tools/wetness_layer.py` into your set's tools. Inside Blender: `import wetness_layer as wl`.
2. For a photo material (colour picture, optional normal map, Principled BSDF): `wl.add_wetness_to_material(material, wetness=..., puddles=..., rough_image=..., height_image=..., smooth_normal_image=..., porosity=..., wet_roughness=..., film_coat=..., specular_boost=..., lowness=...)`. For a material made of one of the texture recipes, make a `WETNESS` node yourself and plug the recipe's Colour, Roughness and Height outputs into it, then its outputs into the Principled BSDF (not tested live; tested on the recipes' finished maps, `tools/01_five_card_test.py`).
3. **Smoothed relief picture**: `python3 -I tools/20_make_smoothed_pictures.py NAME SIGMA` writes a blurred copy of `NAME_normal.jpg` (and the height). SIGMA is the blur width in dots: about 8 mm of the real surface is a good start (4 dots of a 1024-dot-per-2-metre picture).
4. **Lowness**: give the layer a 0..1 socket that says where water gathers (for a road: from |x| across the street; for a tile: its own low parts). Without one every spot says "no opinion" (0.5).
5. **Walls**: measure in the wall's own coordinates (`position=` Texture Coordinate "Object"), with Ground Slope 0 and Ground Offset 0 when the object's z = 0 is the floor, and add `wl.drip_chain(...)` with the wall's window sills. One copy of the wall material per facade layout. Give walls NO shine (boost 0, coat 0, wet roughness = dry roughness): wet brick and stone are darker, not glossier.
6. **Calibrate with your camera**: `tools/23_calibration_driver.py` (one Blender run, a few seconds each: puddle sweep, colour ratios, wall masks), then `tools/23b_puddle_fit.py` (the puddle dial against the share of road under water) and `tools/04b_colour_ratios.py`. Then look.
7. **Draw plates in EEVEE with the settings of section 7**, and measure with `tools/22b_numbers.py` (brightness, grain, black holes per surface) and `tools/24_wall_ratio.py` (wet over dry on the walls).
8. **For the glb**: `tools/06_bake_maps_and_export.py` (photograph, build plain materials, export, save a baked .blend) and `tools/07_inspect_glb.py` to read what the file carries. Use `--reuse` to rebuild the materials and file from existing pictures in seconds.

---

## 9. Results (round 2)

**Pictures** (all EEVEE, ray tracing on, shadow rays 4 / steps 16, 16 samples at 540 x 960, 24 samples at 640 x 480):

* `sheets/street_dry_wet_eevee.jpg`: A today | C wet (0.85 / 0.5) | D wet, heavier rain (1.0 / 0.8), main camera.
* `sheets/wall_foot_round1_vs_round2.jpg`: the wall foot, dry, round 1 settings, round 2 settings.
* `sheets/road_closeup_round2.jpg`: the setts, dry and wet.
* `sheets/eevee_grit_cause_and_cure.jpg`: the speckle, its cause and its cure.
* `sheets/maps_sheet.jpg`: the baked maps. `sheets/stage_maps_ablation_round2.jpg`, `sheets/stage_projection_round2.jpg`: the stage check. `sheets/street_dry_wet.jpg`, `wet_closeups.jpg`, `wetness_layer_five_surfaces.jpg`: round 1's Cycles sheets (Cycles pictures were not redrawn in round 2: the plate renderer is EEVEE).
* `sheets/lockout_today_wet_eevee.jpg`: the lockout shot (with props) today and wet, 540 x 960. `work/r35/main_wet_plate.png`: the full-size wet plate (1536 x 2730, 4.9 MB), `work/r35/plate_wet_half.jpg`, `work/r35/plate_wet_crop_lowerleft_100pct.jpg`. `sheets/wall_wet_over_dry_final.jpg`: the wall's wet-over-dry picture.

**Main camera numbers** (EEVEE, `tools/22b_numbers.py`, finished 8-bit pictures, so brightness as shown, not light energy; today is drawn with the same settings; final settings, `work/r36/numbers.json`):

| surface | A today | dry new | C wet | D heavy | C / today | black-hole share today, C | grain C (left / middle / right thirds for the road and pavement) |
|---|---|---|---|---|---|---|---|
| road setts | 0.130 | 0.115 | 0.195 | 0.186 | **1.50** | 0 %, 0 % | 0.0053 (0.0115 / 0.0025 / 0.0020) |
| pavement flags | 0.179 | 0.183 | 0.200 | 0.159 | 1.12 | 0 %, 0 % | 0.0067 (0.0113 / 0.0060 / 0.0032) |
| kerb + gutter stones | 0.110 | 0.110 | 0.151 | 0.140 | 1.37 | 6 %, 0 % | 0.0091 |
| cottage walls | 0.091 | 0.090 | 0.076 | 0.074 | **0.84** | 26 %, 52 % (the walls are dark at dusk, and now darker) | 0.0039 |
| dressed stone | 0.100 | 0.100 | 0.094 | 0.092 | 0.94 | 19 %, 24 % | 0.0048 |
| roofs | 0.128 | 0.130 | 0.150 | 0.150 | 1.17 | 0 %, 0 % | 0.0046 |
| colliery brick | 0.100 | 0.100 | 0.106 | 0.106 | 1.06 | 3 %, 5 % | 0.0040 |

(16 samples; the left-third numbers are above the aim of 0.008 at 16 samples and meet it at 48.) Nothing is clipped in the main camera view (no surface has dots over 0.97 in C); the lockout plate does clip at the brazier's reflection (section 2, problem 4). Grain of a dry EEVEE road: 0.0025. The first EEVEE picture of round 2, drawn with EEVEE's default shadows, had the road at 1.67, roofs 1.31, walls 1.03; the table above is after the shadow cure and the wall and roof changes.

**Puddle dial** (`work/r30/puddle_dial_round2.json`; share of the surface that is puddle, per cent; threshold = 0.79 - 0.52 x dial^1.25, fitted on the main camera's road to hit 3 / 8 / 15 / 30 %):

| dial | road, main camera | road, lockout plate camera | road, notice-corner plate camera | road, whole street from above | pavements, main camera (bias 0.22) | pavements, whole street |
|---|---|---|---|---|---|---|
| 0.3 | 2.9 | 2.1 | 15.3 | 5.8 | 0 | 0 |
| 0.5 | 8.1 | 8.4 | 32.4 | 18.9 | 2.5 | 0.7 |
| 0.65 | 14.9 | 22.3 | 48.2 | 30.7 | 14.8 | 5.0 |
| 0.8 | 30.1 | 41.9 | 61.7 | 43.9 | 35.1 | 14.5 |

The two other plate cameras were placed on the prop-free copy of the street, so their numbers are for an emptier road than the real shots; the notice-corner camera stands on the right pavement and sees mostly the gutter half, so use about 0.3 for that shot.

**Live against baked** (`tools/31_compare_baked_live.py`, EEVEE, main camera, 16 samples: Blender working the layer out at every dot, against the same street wearing only the baked maps and flat numbers that went into the glb; correlation 1 = the same pattern):

| surface | baked / live brightness | mean difference | correlation |
|---|---|---|---|
| road setts | 1.01 | 0.006 | 0.983 |
| pavement flags | 1.00 | 0.004 | 0.996 |
| kerb + gutter | 1.02 | 0.007 | 0.961 |
| cottage walls | 1.00 | 0.003 | 0.993 |
| dressed stone (flat numbers) | 1.12 | 0.013 | 0.950 |
| roofs (flat numbers) | 1.03 | 0.012 | 0.945 |
| colliery brick (flat numbers) | 1.13 | 0.017 | 0.910 |

The plan's target (difference under 0.04, correlation over 0.9) is met for everything. Everything with maps is within 2 % of live. The three flat stand-ins are 3 to 13 % too bright (round 1: 23 to 70 %). Whether the baked picture shows the glints on the sett corners the way the live one does, I did not check.

**Stage check** (`stage_test/`, `sheets/stage_*_round2.jpg`, `work/s06/stage_numbers.json`): the same copy of the film kit's stage files (three.js 0.169, the kit's own `projected-set.js`) and the same hidden Chromium with software graphics as in round 1, with the re-baked wet glb, and the round 2 EEVEE wet picture as the stand-in painting.
* **The maps arrive.** three.js reports for `street_setts_wet`, `pavement_flags_wet`, `channel_stones_wet` and the four wall materials: `roughnessMap`, `clearcoatMap`, `clearcoatRoughnessMap`, `specularIntensityMap` (all on texture channel 1 = UV2), `specularColor` 1.5, and the normal map on channel 0 (now the smoothed photo relief picture). I also read the exported file itself (`tools/07_inspect_glb.py`): `KHR_materials_clearcoat`, `KHR_materials_specular`, `KHR_materials_emissive_strength`; 45 materials, 56 pictures, 135 meshes, 7 of them with a second set of texture coordinates.
* **They change the picture, and the roughness map does the work.** In my own stand-in dusk (a bright sky and bright lamp patches to reflect: much brighter than the stage's own dusk, so only the steps mean anything), road mean brightness: 0.220 today's glb; 0.178 wet glb with all maps off; 0.461 with the roughness map (mean change 0.28); 0.491 with the clear coat maps added (0.03); 0.485 with the specularity map added (0.006, and it lowers the road a little). **The specularity map changes the picture least; it does not make anything wet by itself.**
* **They do not reach the film today.** Through the film's real projection code: from the projector's own camera the stage shows the painting (mean difference 0.0036 on the road); in a moved view (1.4 m forward, 0.3 m right) 1.97 % of the picture wears the glb's own surface; today's glb against the wet glb differs by 0.0004 and matte on against off by 0.0024 (0.0011 on the road). Same as round 1 within small differences. The wet look the audience sees is whatever the painter paints.
* Timing in the software renderer: a still 7 to 8 s; a projected still 12 to 20 s (the machine was busy with a Blender run at the same time).

---

## 10. Timings and machine

Four processor cores shared with up to three other helpers (load average 2 to 6), 2 threads for Blender. EEVEE (xvfb-run, ray tracing on) at 540 x 960: 38 to 80 s for the street as it is (default shadows 38 s, rays 4 / steps 16 80 s); wet with the defaults 56 s; wet with rays 4 / steps 16: 85 to 108 s at 16 samples, 357 s at 48 samples. Close views 640 x 480, 24 samples: 78 to 170 s. The lockout file takes about a minute just to load and set up, even for a 270 x 480 picture at 4 samples (56 to 68 s). Calibration run (puddle sweep, colour ratios, wall masks, one Blender run): about 2 minutes. Bake: 8.5 minutes (32 maps, glb export). Full-size lockout plate (1536 x 2730, 32 samples, rays 4 / steps 16): 20 min 27 s, using about 7 GB of memory; the lockout shot at 540 x 960, 16 samples: 220 to 227 s. Glb rebuild with `--reuse`: 7 s of work, about 30 s with loading.

---

## 11. What went wrong, and what I am unsure of (all of it)

**Failures and slips in round 2, recorded**
* **I looked for the grit in the wrong place for five runs.** My first test drew only the lower-left part of the picture (a "border" render, which is quick) and found no speckle in ANY variant, including round 1's: border renders did not show the speckle (I do not know why; probably EEVEE does less shadow work when only a part is drawn), so that test said nothing. The second test, the whole picture, showed the speckle and showed it did not depend on the relief picture. Four more runs took pictures and EEVEE settings away one at a time until the shadows were left.
* The first guess for the cure (the checker's: flatter relief, rougher wet) lowered the speckle by a third at best.
* My first wall test with wet roughness 0.75 and no coat still came out lighter at the lamp-lit base of the wall (1.04): the shine from a lamp a metre away. Only roughness 0.9 (no change from dry) removed it.
* The "foot strip" of the close wall view read 1.04 after the first fix because my measuring mask catches the lit edge of the plinth; it reads 0.85 after the plinth was darkened (see problem 2). The numbers I give for "lower wall" are measured on a region I chose by looking at the picture (rows 100 to 170, columns 260 to 470 of 640 x 480), not on a wall-height scale.
* More Blender runs than the budget (18 against about 10), because of the search for problem 1 and the extra check of the final settings.
* The first set of final pictures (`work/r31`) was drawn before I set the walls' roughness to 0.9 and darkened the plinths and dressed stones; the numbers in this note are from the re-draw (`work/r36`). The road close-up pictures (`work/r31/close_road_*`) were not redrawn: the road did not change after them.

**Not tested**
* **The painter (Flux) on a wet plate**: needs your go-ahead. Whether it keeps the lamp pools, the mirror puddles, the streaks and the wet foot is unknown.
* Cycles pictures with the round 2 settings (round 2 drew everything in EEVEE; the round 1 Cycles sheets still stand for round 1 settings).
* The shots with props other than the one lockout plate (the notice corner), and the wet look of the props themselves (they are dry and stand on a wet road; metals and props are not touched).
* A road made from a texture recipe (second step of the plan); a live recipe node group plugged into the layer (only the recipes' finished maps were); our slate or mud recipes on the street.
* Animation (rain starting and stopping): the dial can be keyframed, not tried.
* A stage change (matte off for the ground) to let the glb's maps reach the film.
* Whether the 2 m repeat of the cobblestone picture is visible along the street.
* How much the glints on the sett corners are reduced (section 2, problem 6).
* The streaks under the sills and eaves as a measurement; I only looked at the masks and the close picture.

**Unsure**
* Whether 2.1 cm a dot is fine enough for the ground maps near the camera; I judged by the sheet.
* The puddle dial is calibrated on one seed and three camera views.
* The black-hole count is a plain "brightness under 0.06"; some of those dots are real shadow, not puddle or wet wall.
* The speckle numbers depend on the 540 x 960 picture size; the full-size plate has smaller dots.
* The numbers say the wet road is 1.50 times today's; whether that is the right amount of "wet" for the painter is a matter of taste.

---

## 12. Dead ends

* Colour darkening alone: nearly invisible at dusk; kept, but it is not what makes a road look wet.
* A baked wet normal map for the glb: washes out the setts' joints; baked for the sheet only.
* Walls at wet roughness 0.3 (glassy), 0.45 (too bright), 0.75 (still brighter at the lamp-lit base; 0.55 was only used in a first set-up and gave 1.06): walls now keep the dry roughness.
* Puddle roughness 0.03: black holes; 0.08 and Puddle Darkness 0.9 kept.
* Wall band 0.75 m measured from the pavement (round 1): hidden by the plinth; measured from the floor now.
* **A smoothed or flattened relief picture as the cure for the EEVEE speckle**: no effect on the speckle (it is still in the layer, as Grain Fill, because it is what water does and it softens the sett-corner glints a little).
* Ray tracing quality or size, brightness clamps, shadow memory, lamp size, shadow map size: none touched the speckle.

---

## 13. Files

* `tools/wetness_layer.py` the layer (and `WETNESS DRIP`); `tools/apply_wetness_to_set.py` the street's materials, cameras and render settings; `tools/06_bake_maps_and_export.py` maps, plain materials, glb, baked .blend; `tools/07_inspect_glb.py` what a glb carries; `tools/round1/` the round 1 versions of the three main scripts.
* Round 2 tools: `20_make_smoothed_pictures.py` (blurred relief pictures), `21_eevee_grit_diagnosis.py` + `21b_grain_numbers.py` (the first, border-render test and the grain measure), `22_render_eevee.py` (any camera, any state, EEVEE; opens a shot file read-only), `22b_numbers.py` (the numbers table), `23_calibration_driver.py` + `23b_puddle_fit.py` (calibration in one run), `24_wall_ratio.py` (wet over dry on the walls), `25_eevee_noise_variants.py` (the search for the speckle's cause: every variant of runs 2 to 5), `26_wall_variants.py`, `27_road_variants.py`, `29_pictures_round2.py` (the final pictures and the plate), `31_compare_baked_live.py`, `run_round2_tune.sh`, `run_round2_bake_and_plate.sh`. Each file begins with a plain note and its run line.
* Round 1 tools still used: `01_five_card_test.py`, `02_puddle_sweep.py`, `03_wall_masks.py`, `04_colour_ratios.py` + `04b_colour_ratios.py`, `05_render_views.py` (Cycles), `08_maps_sheet.py`, `09_make_sheets.py`, `10_numbers.py`, `11_compare_live_baked.py`, `13_stage_numbers.py`.
* `stage_test/`: a copy of the film kit's stage files plus my test page, the runner `run_stage_test.mjs` and the job files. The big glb files are linked, not copied.
* `set_copy/`: the street copy, its textures, Poly Haven's roughness and height pictures, the smoothed copies, the baked .blend. `maps/`, `glb/`, `sheets/`, `work/` (renders, numbers, logs: `r21` to `r27` the speckle search, `r28` to `r32` walls and road, `r30` calibration, `r31` final pictures, `r33` bake log, `r34` baked picture, `r35` plate; `s06` stage pictures).
* `build_result_round_1.json`, `build_result_round_2.json`: the structured results.
