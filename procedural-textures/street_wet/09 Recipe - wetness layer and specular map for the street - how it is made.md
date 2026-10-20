# 09 Recipe - wetness layer and specular map for the street - how it is made

What this file is: the plain-words record of what was built for the "wet street" test of the pit village set (the street view test, log 29 of the project story): one reusable
**wetness layer** for Blender, the materials it was put on, the **maps** (flat pictures, among them a **specularity map**) baked from it for the `.glb` file, the pictures drawn, how the
`.glb` behaves in the three.js stage, and everything that went wrong. It follows "09 Research - wet surfaces for the street set.md" (in `study/`), which is the plan this round carried out.
Nothing in the film project's own folder was changed: all work is on copies in `street_wet/` (the street copy is `set_copy/street.blend`). I did not run git.

Words used (one word for each thing, explained once):
* **set**: the 3D street built in Blender. **plate**: the one picture drawn from the set's main camera, which the painter repaints. **painter**: the image model (Flux). **stage**: the film program (three.js) that shows the painting shone back on the set.
* **glb**: the single file that carries the set from Blender to the stage. **map**: a flat picture that holds one number for every dot instead of a colour (roughness map, specularity map ...).
* **roughness**: how blurry reflections are. 0 is a mirror, 1 is chalk. Example: wet glass is near 0.05, dry brick near 0.9.
* **specular** (the "shine"): how strongly a surface reflects light that hits it head-on. Blender calls the dial "Specular IOR Level": 0.5 is normal (about 4 %), 0.75 is a wet surface (about 6 %), 0 is none. A **specularity map** holds that strength for every dot.
* **clear coat** ("coat"): a thin clear layer on top, like varnish on a table or a film of water on stone; it reflects on its own whatever is underneath.
* **node group**: a small packaged recipe made of Blender's node boxes, which can be dropped into any material. The **wetness layer** is one.
* **porosity**: how much a material soaks water up (brick and sandstone soak a lot, glazed tile and iron do not). **puddle dial**: the layer's "Puddles" setting.
* **Cycles**: Blender's exact, slow renderer. **EEVEE**: its fast renderer, which the film's plates are drawn with. **UV2**: a second set of texture coordinates on a mesh, so a map can be laid on it a different way from the photo (here: once over the whole street, nothing repeats).

---

## 1. The short answer

1. **A wetness layer exists and works.** One node group, `WETNESS`, in `tools/wetness_layer.py` (445 lines, plain Blender nodes, no add-on). It sits between any material's dry look (colour, roughness, relief height, normal) and its Principled BSDF and gives back the wet look. Picture `sheets/wetness_layer_five_surfaces.jpg` shows the same layer, unchanged, on five different surfaces (street photo brick and cobblestone, our finished slate, mud and wood recipe tiles): every one goes darker, smoother and shinier.
2. **It is on the street.** `tools/apply_wetness_to_set.py` puts it on 11 materials of a COPY of the street: road setts, pavement flags, gutter stones, kerbs, brick and stone cottage walls (with rain streaks under every window sill and the eaves), colliery brick, two dressed stones, slate roofs and the yard. Poly Haven's own roughness and height pictures (free, CC0) were added for the road, pavement, brick walls and stone walls.
3. **Nothing was replaced by a texture recipe.** The plan says: first wet plate with the photos; only the road setts could become a recipe, as a second step, and only if the painter's result shows the problem. I could not run that painter test (it costs money and needs your go-ahead), so no replacement was made.
4. **Pictures** (Cycles, main camera, 540 x 960): A = street as it is today, B = new materials dry, C = wet, D = wet with heavier rain: `sheets/street_dry_wet.jpg`. Close-ups of the setts and of a wall foot beside the first gas lamp, dry and wet: `sheets/wet_closeups.jpg`.
5. **Maps baked for the glb** (`maps/`, one sheet `sheets/maps_sheet.jpg`): for the whole street seen from above (road, gutter, kerb tops, both pavements: one picture, 48 dots a metre) and for the four shared cottage fronts (200 dots a metre): wet colour, **roughness**, **clear coat**, clear coat roughness, **specularity**, and for the ground also a wet normal map and the puddle and wet masks. The wet `.glb` is `glb/street-wet.glb` (25.5 MB; the dry one is 16.9 MB).
6. **The maps survive the export and three.js reads them.** I read the exported file (`tools/07_inspect_glb.py`): `KHR_materials_clearcoat` with the coat picture and the coat-roughness picture packed in one image, `KHR_materials_specular` with the specularity map as its picture AND a colour factor of 1.5 (so a map plus a boost works), the roughness map in the metal-roughness slot, all on the second texture coordinates. three.js 0.169 (the film kit's version) loaded all of it (`roughnessMap`, `clearcoatMap`, `clearcoatRoughnessMap`, `specularIntensityMap`, `specularColor` 1.5). With the maps switched on one at a time in a three.js page, the road changes: roughness map +0.31 mean brightness on the road, clear coat maps +0.035, specularity map +0.006 (section 7).
7. **But as the stage is today they do not reach the film.** With the film's own projection code (`projectPaintingOnto`), only 1.97 % of a moved view wears the glb's own surface (mostly outlines and edges; the weights view shows the rest orange, the painting, or background), and drawing the set with matte on or off changes the moved picture by 0.002 (mean difference on a 0..1 scale). So the wet look the audience sees is what the painter paints from the plate. This confirms the study; the maps are insurance for the plate (live in Blender), unseen surfaces and a changed stage.
8. **Where the result falls short of the plan** (details in section 9): the wet road is 2.0 times as bright as today's road (plan aim 1.3 to 1.6; not clipped: 0.4 % of road dots above 0.97); the wet foot of the walls is hardly visible at dusk; the stand-in flat numbers for roofs, dressed stone and colliery brick are 1.2 to 1.7 times too bright in the baked render; the painter was not tried; EEVEE still sparkles on the pavement unless the cure in section 6 is used (tested in one picture only).

---

## 2. What wetness does to a material, and why (example first)

**Example.** A dry cobbled road at dusk: dark grey-brown, chalky (roughness 0.9), no reflections. After rain the same road is **darker**, **smooth** (lamp light streaks across it), has a thin **shiny film**, **flat mirror puddles** in the low spots, and the stone tops, which drain first, stay a little drier than the joints.

The layer makes exactly those six changes, each from a rule you can switch off alone:

| change | why it happens in life | what the layer does | switch |
|---|---|---|---|
| darker, richer colour | water in the pores and on the surface traps light | colour x a darkening that grows with porosity and wetness; a little more colour | Colour Effect |
| smoother | water fills the pores | roughness slides to Wet Roughness (0.3 for ground); puddles go to Puddle Roughness | Roughness Effect |
| a shiny film | water (index 1.33) reflects about 2 % head-on and nearly everything at grazing angles | Specular IOR Level 0.5 up to 0.75, and a coat of weight 0.3 x wet (up to 1 in puddles) | Specular Effect, Coat Effect |
| puddles | water gathers in low spots | a "depth" from slow wobble (50 %), the caller's Lowness (25 %) and the relief's low parts (25 %), cut by a soft threshold the dial moves | Puddles dial |
| flat water | thick water hides the relief | the normal slides to the plain surface normal (fully in puddles, 35 % of Wetness elsewhere) | Normal Effect, Relief Flatten |
| wet walls | splash and rising damp at the foot, rain running from sills and eaves | a band at the foot (wavering top edge), a general damp, general streaks, and streaks hanging from every window sill and the eaves | Wall Band, Wall Wetness, Streaks, Drip Mask |

Measured on the main camera (picture 04 of the study and my own colour table, section 8): colour alone is nearly invisible at dusk, smoothness is the big change, the film adds the lamp pools, puddles add the mirrors. **A specularity map alone, without lower roughness, would not look wet.**

---

## 3. The layer: every control (`tools/wetness_layer.py`)

Plug the dry look in and plug the outputs into the Principled BSDF (Colour to Base Color, Roughness to Roughness, Specular IOR Level to Specular IOR Level, Coat Weight to Coat Weight, Coat Roughness to Coat Roughness, Normal to Normal), and set Coat IOR to 1.33. `add_wetness_to_material(material, ...)` does all of that for a photo-textured material.

**The dry look (plug in)**

| input | what it is |
|---|---|
| Colour | the dry colour picture |
| Roughness | the dry roughness: a number or a roughness picture |
| Height | the dry relief height, 0..1 (0.5 = flat); lets stone tops stay drier and water gather in joints |
| Normal | the dry normal (bumpy look); the plain surface normal if there is none |

**Where am I**

| input (default) | what changing it does |
|---|---|
| Use World Geometry (1) | 1: the layer reads the object's world position and surface direction itself. 0: it uses Position and Surface Up. Use 0 for walls (measure in the wall's OWN coordinates, so every copy of a shared wall mesh gets the same wet pattern, which a baked map needs) and for flat texture tiles. |
| Position, Surface Up | used only when Use World Geometry is 0 |

**How wet**

| input (default) | what changing it does |
|---|---|
| Wetness (0.8) | 0 = bone dry, the layer gives the dry look back unchanged; 1 = soaked |
| Puddles (0.5) | 0 = none; the dial is calibrated: on the main camera's road 0.3 gives 3.0 %, 0.5 gives 7.8 %, 0.65 gives 16 %, 0.8 gives 30 % of the road as puddle (section 8) |
| Seed (0) | any number; moves the puddles and streaks |

**The material**

| input (default) | what changing it does |
|---|---|
| Porosity (0.6) | how much it darkens: brick 0.7, stone 0.6, slate 0.3, painted wood 0.2, metal 0 |
| Darkest (0.45) | how dark a fully porous, soaked surface gets as a share of dry. With porosity 0.6 and Wetness 0.85 the colour ends at about 0.72 of dry |
| Wet Roughness (0.3) | roughness of a soaked surface: 0.3 for ground, about 0.45 for walls (lower and the walls look like glass), 0.6 for flagstones in EEVEE |
| Puddle Roughness (0.08) | 0.03 is a perfect mirror and goes black wherever it reflects only dark houses; 0.08 reads as water without going black |
| Specular Boost (0.25) | how far the shine rises when wet (0.5 to 0.5 + this) |
| Relief Flatten (0.35) | how much of the normal map's relief water smooths away on wet ground; 1.0 for sparkly flagstones |
| Puddle Darkness (0.9) | colour under standing water as a share of the wet colour; kept high so puddles do not go black |
| Puddle Bias (0) | moves the puddle threshold for one material: plus = fewer puddles. The pavement uses 0.21 so it holds a fraction of the road's puddles |

**Where the water goes**

| input (default) | what changing it does |
|---|---|
| Lowness (0.5) | how low this spot is, given by whoever puts the layer on. The road: 0 on the crown, 1 at the gutter; the pavement: 1 at the kerb to 0 at the houses; the gutter: always 1 |
| Dry Tops (0.5) | how much the high parts of the relief (stone tops) stay drier |
| Water Level (0.65) | how high puddles reach on the Height scale |
| Ground Slope (0.0699), Ground Offset (0) | the ground rises this many metres per metre along +y (the street: tan 4 degrees). The layer measures height above the ground as z - y x slope - offset. For the cottage walls in their own coordinates: slope +-0.0699 and offset -0.307 |
| Wall Band (0.45) | metres the wet band at the foot reaches |
| Wall Wetness (0.35) | how wet the whole wall face is |
| Streaks (0.5) | strength of the general vertical rain streaks |
| Drip Mask (0) | rain running from sources the caller knows; made by the sub-group `WETNESS DRIP` |

**Switches** (0..1, default 1): Colour Effect, Roughness Effect, Specular Effect, Coat Effect, Normal Effect. 0 gives that part's dry value back (for tests, or to turn one part off).

**Outputs**: Colour, Roughness, Specular IOR Level, Coat Weight, Coat Roughness, Normal, Height (after water fills the puddles), Wet Mask, Puddle Mask, Streak Mask, Puddle Depth (the number the puddle threshold is cut from; the calibration reads it).

**The sub-group `WETNESS DRIP`** (inputs Position, Centre, Half Width, Top, Length, Seed; output Mask): one rain streak hanging from one source: ragged sides from a slow wobble, lines from noise stretched downward, a strength that fades with distance below the source. `drip_chain()` makes one per source and joins them. For the street cottages the sources are made from the street builder's own numbers (`FACADE_LAYOUTS`, `GROUND_WINDOW`, `UPPER_WINDOW`, `EAVES_HEIGHT`): one under each window sill (0.7 m long below the ground-floor sill, 1.0 m below upper sills) and two wide ones under the eaves (1.3 m). Picture: the green in `work/r03/both.jpg` (streak masks of one stone and one brick cottage front).

---

## 4. The street: which materials got what (`tools/apply_wetness_to_set.py`)

| material | share of main view | Poly Haven maps added | porosity | wet roughness | other |
|---|---|---|---|---|---|
| street_setts (road) | 33 % | roughness, height | 0.6 | 0.3 | Lowness from the crown to the gutters |
| pavement_flags | 2.4 % | roughness, height | 0.55 | 0.45 | Lowness 1 at the kerb; Relief Flatten 0.6; Puddle Bias 0.21 |
| channel_stones (gutter) | 1.2 % | none | 0.5 | 0.3 | always wetter: Wetness x 1.15, Lowness 1 |
| kerb_stone | 1.2 % | none | 0.5 | 0.35 | Wetness x 1.05, Lowness 0.3 |
| cottage_brick (left walls) | 5.7 % | roughness, height | 0.7 | 0.45 | measured in the wall's own coordinates; a copy of the material for each of the two facade layouts, each with its own sill streaks; the plain material stays on the chimneys |
| cottage_stone (right walls) | 5.6 % | roughness, height | 0.6 | 0.45 | same |
| colliery_brick, dressed_stone, dark_dressed_stone, colliery_yard | 5 %, 4.4 %, 1.4 % | none | 0.7, 0.5, 0.5, 0.7 | 0.45, 0.4, 0.4, 0.4 | measured in the world; stone gets the foot band from the pavement level |
| roof_slate | 1.0 % | none | 0.3 | 0.25 | a sheen |

Not touched: metals, paints, windows, lamp glass, the sky dome, props (the plan: later or never for this view).

**Pavement in EEVEE.** In EEVEE the flagstones still sparkled with the values above (grain 0.0129 against 0.007 dry). Setting Relief Flatten to 1.0 and Wet Roughness to 0.6 brought it to 0.0065 in one test picture (`work/r12/eevee_wet_pavement_fix.png`). `PAVEMENT_FOR_EEVEE` in `apply_wetness_to_set.py` holds those two numbers. The pictures and maps in this round were made BEFORE that test, with the table's values.

---

## 5. The maps and what each is for (`tools/06_bake_maps_and_export.py`)

How they are made: a camera looks straight at the flat surface (orthographic, 8 light samples a dot, no lighting at all) and draws one output of the layer as plain light, so every dot holds exactly one number. This is the same trick `lib/bake_harness.py` uses for the texture recipes. The ground is photographed from above as ONE picture of the whole street (x -4.4 to 4.4 m, y -12 to 72 m, 48 dots a metre = 2.1 cm a dot, 422 x 4032 dots); the four cottage fronts square-on (200 dots a metre = 0.5 cm, 900 x 1380 dots each, one picture serves every cottage of that kind).

| map (file) | what it holds | goes into (glTF slot, verified in the exported file) | for |
|---|---|---|---|
| wet colour (`ground_colour.jpg`, `wall_*_colour.jpg`) | the dry colour darkened and enriched where wet | base colour | the wet look in the glb |
| **roughness** (`*_roughness.png`) | 0.9 dry, 0.3 film, 0.08 puddle | green channel of the metal-roughness picture | the glossy road |
| **clear coat** (`*_coat.png`) | 0 dry up to 1 in puddles | red channel of the clear coat picture | the water film |
| clear coat roughness (`*_coat_roughness.png`) | 0.2 film, 0.08 puddle | green channel of the same picture (the exporter packs the two into one) | sharpness of the film's reflection |
| **specularity** (`*_specularity.png`) | reflection strength as a share of its biggest value: 1 = the wet shine (Specular IOR Level 0.75), 0.67 = a dry surface's normal shine (0.5) | alpha channel of the specular picture; with a colour factor of 1.5 so the map's 1 means 1.5 times normal | tells the stage where the surface shines more |
| wet normal (`ground_normal.png`) | the layer's normal in the street's slope frame | not used (see below) | checking |
| puddle mask, wet mask (`*_puddles.png`, `*_wet.png`) | where puddles and wet are | not exported | checking and compositing |

All of it is on the second texture coordinates (UV2). The photo's own tiled normal map stays on the first coordinates: the wet normal map made at 2.1 cm a dot washes out the 1 cm joints between setts (the study's test 6 found the same), so it was baked for the sheet and left out of the glb. Everything not baked (kerbs, roofs, stone dressings, colliery brick, yard, chimneys) gets one flat set of wet numbers in the glb: its colour x its measured wet share, roughness, coat 0.3 x wetness, coat roughness 0.2, specular 0.5 + 0.25 x wetness.

**How a specularity map travels (found by reading the exporter, then checked in the file).** The exporter puts a picture wired into "Specular IOR Level" into the ALPHA channel of the glTF specular picture, and it only reads a grey picture's alpha unless a Separate Color node is in the path (otherwise it would copy the picture's own alpha, which is 1 everywhere, and the map would be lost). So the baked material wires: picture, Separate Color (Red), Math multiply by 0.75, Specular IOR Level. The exporter then writes the picture as the specular picture and 0.75 x 2 = 1.5 as the specular colour factor. In glTF a picture alone can only LOWER the normal reflection per dot; the colour factor of 1.5 is what lets the map's 1.0 mean "wet shine". At grazing angles three.js uses the map value for the strongest reflection too (dry dots 0.67 instead of 1): slightly less grazing shine on dry dots than Blender has. Not measured.

Sizes: `maps/` 12 MB (8 ground maps, 24 wall maps); `glb/street-wet.glb` 25.5 MB, 45 materials, 56 pictures, 135 meshes, 7 of them (3 ground, 4 wall) with a second set of texture coordinates.

---

## 6. How to put the layer on another set

1. Copy `tools/wetness_layer.py` into your set's tools. Inside Blender: `import wetness_layer as wl`.
2. For a photo material (colour picture, optional normal map, Principled BSDF): `wl.add_wetness_to_material(material, wetness=..., puddles=..., rough_image=..., height_image=..., porosity=..., wet_roughness=..., lowness=...)`. For a material made of one of the texture recipes, make a `WETNESS` node yourself and plug the recipe's Colour, Roughness and Height outputs into it, then its outputs into the Principled BSDF (not tested live; tested on the recipes' finished maps, `tools/01_five_card_test.py`).
3. **Lowness**: give the layer a 0..1 socket that says where water gathers (for a road: from |x| across the street; for a tile: its own low parts). Without one every spot says "no opinion" (0.5).
4. **Walls**: measure in the wall's own coordinates (`position=` Texture Coordinate "Object"), set Ground Slope and Ground Offset for that wall, and add `wl.drip_chain(...)` with the wall's window sills. Make one copy of the wall material per facade layout.
5. **Calibrate with your camera**: `tools/02_puddle_sweep.py` and `02b_puddle_fit.py` (the puddle dial against share of road), `tools/04_colour_ratios.py` and `04b_colour_ratios.py` (how much darker each material gets). Both take seconds. Then look: `tools/03_wall_masks.py` shows the wall masks as plain pictures.
6. **For the glb**: `tools/06_bake_maps_and_export.py` (photograph, build plain materials, export, save a baked .blend) and `tools/07_inspect_glb.py` to read what the file carries. Use `--reuse` to rebuild the materials and file from existing pictures in seconds.
7. **Plates in EEVEE**: ray tracing must be ON (off: puddles are pale flat patches); use the pavement cure from section 4; draw a dry plate the same way for comparison.

---

## 7. Results

**Pictures** (all Cycles on the processor, 2 threads, OpenImageDenoise, 32 samples at 540 x 960, 40 at 640 x 480 for close-ups, same lights in every picture):

* `sheets/street_dry_wet.jpg`: A today | B new materials, dry | C wet (wetness 0.85, puddles 0.5) | D wet, heavier rain (1.0, 0.8).
* `sheets/wet_closeups.jpg`: setts and a wall foot beside the first gas lamp, dry and wet.
* `sheets/wetness_layer_five_surfaces.jpg`: five surfaces, dry, damp, soaked.
* `sheets/maps_sheet.jpg`: the baked maps. `sheets/stage_maps_ablation.jpg`, `sheets/stage_projection.jpg`: the stage check.

**Main camera numbers** (`tools/10_numbers.py`, finished 8-bit pictures, so brightness as shown, not light energy; surfaces found with a material-number picture of the same camera):

| surface | A today | B dry new | C wet | D heavy | C / B | black-hole share (dots under 0.06) B, C, D |
|---|---|---|---|---|---|---|
| road setts | 0.188 | 0.155 | 0.379 | 0.347 | 2.44 | 0.2 %, 1.2 %, 2.5 % |
| pavement flags | 0.195 | 0.201 | 0.271 | 0.248 | 1.35 | 1.3 %, 1.3 %, 3.1 % |
| kerb + gutter stones | 0.140 | 0.140 | 0.298 | 0.286 | 2.12 | 5.4 %, 1.5 %, 3.1 % |
| cottage walls | 0.093 | 0.092 | 0.119 | 0.124 | 1.30 | 41 %, 33 %, 32 % (the walls are dark at dusk anyway) |
| roofs | 0.047 | 0.047 | 0.046 | 0.047 | 0.98 | 66 %, 69 %, 68 % (dark slate) |
| whole picture | 0.191 | 0.181 | 0.266 | 0.256 | - | - |

Reading: B is slightly darker than A on the road (0.83 times) because Poly Haven's real roughness is 0.9, not the 0.75 the street guessed. The wet road is 2.0 times today's (C / A) and 2.4 times B; the plan aimed at 1.3 to 1.6. Not clipped: 0.4 % of road dots above 0.97 in C, 0.7 % in D (brightest 1 % of road dots: 0.24 in A, 0.76 in C, 0.91 in D). Pavement grain (sparkle) in Cycles: 0.0055 today, 0.0070 dry, 0.0050 wet: no gritty flags in Cycles. Gutter and kerb grain rises from 0.006 to 0.021 (lamp highlights along the gutter, which is what a wet gutter does).

**Puddle dial** (`work/r02/puddle_fit.json`; share of the road that is puddle, per cent; the layer's dial is threshold = 0.79 - 0.39 x dial^0.80, fitted to hit 3 / 8 / 15 / 30 % at 0.3 / 0.5 / 0.65 / 0.8 on the main camera):

| dial | main camera | lockout plate camera | notice-corner plate camera | whole street from above (area) | pavements, main camera / area |
|---|---|---|---|---|---|
| 0.3 | 3.0 | 2.5 | 15.9 | 5.6 | 0 / 0 |
| 0.5 | 7.8 | 10.6 | 27.7 | 15.4 | 1.6 / 0.4 |
| 0.65 | 16.1 | 24.8 | 39.6 | 26.0 | 5.9 / 1.9 |
| 0.8 | 29.6 | 39.6 | 51.8 | 37.1 | 12.8 / 4.6 |

(The study's draft dial gave 0.9 / 3.8 / 15.8 / 44.9 % on the main camera and 24 % of the pavement at 0.5.) The other two cameras were placed on the prop-free copy of the street, so their numbers are for an emptier road than the real shots. The notice-corner camera stands on the right-hand pavement (x 3.0 m, y 16.4 m, 3.2 m up) and looks up the street, so its view of the road is mostly the gutter half, where Lowness is high (I did not check this with a picture); the same dial gives far more puddle there, so use about 0.3 for that shot.

**Colour ratios** (`tools/04b_colour_ratios.py`, no lighting, wet 0.85 / puddles 0.5, wet colour as a share of dry): setts 0.72, pavement 0.78, kerb 0.75, gutter 0.66, brick walls 0.86, stone walls 0.90 (whole facade; the foot and streaks are darker), colliery brick 0.86, dressed stone 0.88 and 0.82, slate 0.90. Aim from the plan: stone, brick, setts, flags 0.7 to 0.8; slate about 0.85. Setts and flags are on target; the walls are lighter because only part of a wall is wet.

**Live against baked** (`tools/11_compare_live_baked.py`: the same camera and lights, Blender working the layer out at every dot against the street wearing only the baked maps and flat numbers that went into the glb; difference on the 0..1 scale of the finished pictures):

| surface | baked / live brightness | mean difference | correlation (1 = same pattern) |
|---|---|---|---|
| road setts | 1.02 | 0.018 | 0.977 |
| pavement flags | 1.02 | 0.008 | 0.997 |
| kerb + gutter | 1.04 | 0.028 | 0.946 |
| cottage walls | 1.01 | 0.006 | 0.995 |
| dressed stone (flat numbers) | 1.41 | 0.052 | 0.867 |
| roofs (flat numbers) | 1.23 | 0.015 | 0.922 |
| colliery brick (flat numbers) | 1.70 | 0.060 | 0.914 |

The plan's target (difference under 0.04, correlation over 0.9) is met for everything that has maps. The flat stand-ins for dressed stone, roofs and colliery brick come out too bright (they are "wet all over", the layer is only wet in places): they need a lower coat and specular, not tried.

**Stage check** (`stage_test/`, `sheets/stage_*.jpg`, `work/s05/stage_numbers.json`): a copy of the film kit's stage files (three.js 0.169, the kit's renderer and its real `projected-set.js`), Chromium with software graphics, the same way the film kit renders.
* The glb loads with all maps (table in section 1, item 6). Switching the road's maps on one at a time in a dusk setting made of my own stand-in (a sky gradient with bright lamp and window patches to reflect, five warm lamp lights): road mean brightness 0.225 (today's glb), 0.181 (wet glb, maps off), 0.492 (+ roughness map: mean change 0.31), 0.526 (+ clear coat maps: 0.035), 0.520 (+ specularity map: 0.006). So the roughness map makes the big change; the clear coat adds the flat bright puddles; **the specularity map changes the picture least, as the study predicted**. The road is bright in this stand-in dusk; only the changes between steps mean anything, not the level.
* Through the real projection with the wet Cycles picture C as a stand-in painting: from the projector's own camera the stage shows the painting (mean difference 0.002 on the road, after the film's own colour step is added); in a moved view (1.4 m forward, 0.3 m right, as the lockout clip's move) 1.97 % of the picture wears the glb's own surface; today's glb against the wet glb differs by 0.0004 and matte on against off by 0.0019 (0.0007 on the road). **The glb's roughness, specular and coat maps do not reach the film today.** Turning matte off makes the surfaces the painting does not cover about 4.7 times brighter in the stage's own calibration (0.064 matte on, 0.298 matte off), so the stage's match tint changes from about 1.6 to 2.5 down to 0.29: the stage would need re-tuning before it used the maps.
* Timing in the software renderer: a still of the street 7 to 13 s; a projected still 16 to 30 s.

---

## 8. Timings and machine

Four processor cores shared with up to three other helpers (load average 5 to 7 during all of this), 2 threads for Blender. Cycles pictures of the main camera 540 x 960, 32 samples: 235 s (A), 237 s (B), 262 s (C), 253 s (D), baked street 253 s; close-ups 640 x 480, 40 samples: 129 to 198 s; five-card test (1300 x 800, 40 samples) 83 to 106 s; puddle sweep and wall masks 1.3 s a picture (one sample); colour ratios a few seconds. **The bake took 13 minutes 20 s** (photographing 791 s for 32 maps: the ground maps 8 to 20 s each, the cottage-front maps 6 to 42 s each; glb export 6.5 s), over the 9-minute guide; it ran in the background. Rebuilding the materials and glb from the existing pictures (`--reuse`) takes 8 s. EEVEE (xvfb-run, 16 samples, 540 x 960): 200 s with ray tracing on, 126 s off, 79 s with ray tracing on and the pavement cure (the machine may have been less busy). Blender runs in all: about 28 (7 of them under a minute).

---

## 9. What went wrong, and what I am unsure of (all of it)

**Failures and slips, recorded**
* First five-card lamp was a point light and missed the right-hand cards; a big strong strip light then blew the dry cards out (the dry row came out orange-white); a weaker strip (650 W) was right. Three renders instead of one.
* First puddle dial used with the study's pavement scaling gave 24 % puddle on the pavement at 0.5; the "Puddle Bias" input was added to fix that.
* **A bug that reached the glb**: the photographing wired the engine house's door material (`interior_dark`) to a black emission and left it that way; the first glb carried it as an empty white metal, and the engine house door showed as a light grey slab in the stage. Only the stage test showed it. Fixed (the layer's script now puts the shader back) and the glb rebuilt.
* **A bug in the first live-against-baked comparison**: the baked .blend was saved with the photographing's settings (no sky light, no film look), so the baked picture came out 3 to 4 times too dark and the numbers (baked / live 0.29) meant nothing. Fixed (settings restored before saving), the street re-drawn; the table above is the second try. Not counted as a result: the first.
* Stage test: the first stills were washed out because I set the wrong property for how strongly shiny surfaces reflect their surroundings (three.js 0.169 reads `scene.environmentIntensity` when the environment is set on the scene, not the material's); the first projected stills came out dark because the film's projection writes the painting AFTER the colour encoding step and relies on the film's finishing pass; the runner now encodes them afterwards.
* The wall's wet band at the foot is mostly hidden: each cottage floor stands 0.15 m (uphill end) to 0.46 m (downhill end) above the pavement, and a dressed-stone plinth covers the wall below the floor. A band 0.45 m above the pavement therefore reaches only the foot of the plinth. I tried 0.75 m (`work/r13/band_compare.jpg`): the close-up hardly changed at dusk. The stone walls are dark and only slightly darker wet (0.90). Left at 0.45.
* The plan's brightness aim for the wet road (1.3 to 1.6 times) was not reached (2.0 times today). I did not lower the film's shine to get there; it is a setting (Specular Boost, coat weight) to turn down if the plate needs it.
* More than the "about 20" Blender runs (about 28), because of the two bugs above and the extra checks.

**Not tested**
* The painter (Flux) on a wet plate: costs money, needs your go-ahead. Whether it keeps the lamp pools and mirror puddles is unknown.
* A full-size plate (1536 x 2730) and the EEVEE plate with props; the shots with props (lockout, notice corner) themselves: I only placed their two cameras on the prop-free street copy.
* A road made from a texture recipe (second step of the plan), a live recipe node group plugged into the layer (only the recipes' finished maps were), our slate or mud recipes on the street.
* Streaks under the sills and eaves are in the masks, the wet renders and the maps, but in the one close-up I looked at I could not pick them out, and nobody has seen whether the painter would keep them.
* Animation (rain starting and stopping): the dial can be keyframed, not tried.
* Maps for the kerb stones, and the D (heavy rain) state baked.
* Whether the 2 m repeat of the cobblestone picture is visible along the street; the grid is regular in the pictures but I did not measure the repeat.
* How the roughness map behaves in the real stage with the film's grey room instead of a dusk (the real stage discards it anyway, matte on).

**Unsure**
* Whether 2.1 cm a dot is fine enough for the ground maps near the camera (the roughness and coat maps are smooth, the colour map loses the 1 cm joints); I judged by the sheet, not by a close three.js view.
* The stage stand-in environment and lamp strengths are mine, chosen to show the maps; the stage's own dusk setting is a different one.
* The calibration of the puddle dial is on one seed and the three camera views; another seed gives other patches with a similar share.
* The black-hole count is a plain "brightness under 0.06"; some of those dots are real shadow, not puddle.

---

## 10. Dead ends

* Colour darkening alone (picture 04 of the study): nearly invisible at dusk; kept, but it is not what makes a road look wet.
* A baked wet normal map for the glb: washes out the setts' joints; kept for the sheet only.
* Walls at wet roughness 0.3: glassy (the study); 0.45 chosen.
* Puddle roughness 0.03: black holes; 0.08 and Puddle Darkness 0.9 chosen by eye from three pictures (`work/r05b/variants.jpg`: 0.03 / 0.8, 0.08 / 0.9, 0.15 / 1.0).
* Wall band 0.75 m: no visible gain (above).

---

## 11. Files

* `tools/wetness_layer.py` the layer (and `WETNESS DRIP`); `tools/apply_wetness_to_set.py` the street's materials, cameras and render settings; `tools/06_bake_maps_and_export.py` maps, plain materials, glb, baked .blend; `tools/07_inspect_glb.py` what a glb carries.
* Tests: `01_five_card_test.py`, `02_puddle_sweep.py` + `02b_puddle_fit.py`, `03_wall_masks.py`, `04_colour_ratios.py` + `04b_colour_ratios.py`, `05_render_views.py` (any camera, any state), `run_main_renders.sh` and `run_closeups.sh`, `08_maps_sheet.py`, `09_make_sheets.py`, `10_numbers.py`, `11_compare_live_baked.py`, `12_eevee_check.py`, `12b_eevee_noise.py`, `13_eevee_pavement_fix.py`, `13_stage_numbers.py`. Each file begins with a plain note and its run line.
* `stage_test/`: a copy of the film kit's stage files plus `street-wet-test.js` and `street-wet-test.html` (mine), the runner `run_stage_test.mjs` and the job files. The big glb files are linked, not copied.
* `set_copy/`: the street copy, its textures, Poly Haven's roughness and height pictures, the baked .blend. `maps/`, `glb/`, `sheets/`, `work/` (renders, numbers, logs; `work/r07` A to D, `work/r08` close-ups, `work/r10` baked street, `work/r12` EEVEE, `work/s05` stage pictures).
* `build_result_round_1.json`: the structured result of this round.
