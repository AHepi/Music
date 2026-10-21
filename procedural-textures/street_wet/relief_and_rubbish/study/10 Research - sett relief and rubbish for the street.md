<!-- NOTE (plain words): this is the study for the person's last request on the wet street: "add a rubbish mask for gutters and along buildings" and "the normal maps between bricks on the ground need a little work: the light shouldn't be able to wash out the 3D effect so easily; the geometry should still be visible under all conditions". It was written on 20 and 21 October 2026 from runs on COPIES of the street (nothing in the film project's own folder was changed, no git). Every number in it comes from a file in `work/` (the tables are filled in by `tools/b13_write_note.py` from the measurement files); every picture is in `pictures/`. It says what was run and looked at, what was not, and what I am unsure of. Words are explained where they first appear. -->

# 10 Research - sett relief and rubbish for the street

**What this file is.** Two jobs, in this order. **(1) The setts** ("the bricks on the ground": the squared stones of the road): why the joints between them stop showing in the wet street under some lights, what keeps them showing, what I built and measured, and a fixed **lighting test set** with a number that says "visible under all conditions" or not. **(2) The rubbish**: where rubbish lay in a 1926 Durham pit village street, how a rubbish mask and small litter are made in Blender, a first prototype, and the plan to build it on top of the setts. It follows `09 Recipe - wetness layer and specular map for the street - how it is made.md` (two folders up, in `street_wet/`) and uses its round 2 settings.

**Words used** (one word for each thing, explained once).
* **set**: the 3D street in Blender. **plate**: the one picture drawn from the set's camera that the painter repaints. **painter**: the image model (Flux). **stage**: the film program that shines the painting back on the set. **wetness layer**: the node group `WETNESS` of the recipe note.
* **sett**: a squared stone laid in a road (the road here has about 12,000). **joint**: the thin gap between two setts. **stone face**: the flat top of a sett.
* **colour picture**: the photo of the road (Poly Haven's "square cobblestone", CC0, 2 m wide, one dot = 1 mm). **relief picture**: the picture that says, for every dot, which way the surface leans (Blender calls it a "normal map"). **height picture**: a grey picture of how high each dot is. **mask**: a picture that says where something is (0 nowhere, 1 fully).
* **shine**: reflection of lamps and sky. **roughness**: how blurry reflections are (0 mirror, 1 chalk). **specular**: how strongly a surface reflects light head-on. **clear coat** (or "film"): a thin clear layer on top, like water on stone.
* **joint picture**: my picture for the cure: white in the joints, black on the stone faces, a soft edge (the 3D programs call it a "cavity" picture). **contrast, delta, seen, near, middle, far**: my joint visibility measure (section 2).
* **lighting test set**, **pass line**: section 6. **rubbish mask** (or "plan picture"): a picture of the street seen from above that says where rubbish gathers (section 7). **muck layer**: dust, cinders and mud painted on the ground by a material. **pieces**: small separate bits of litter placed as little objects.
* **EEVEE**: Blender's fast renderer, which the plates are drawn with. **sample**: one pass of the renderer over the picture (more samples, less speckle, more time).

## 1. The short answer

**(1) Why the joints wash out.** Look at the pictures `pictures/baseline_A_dry_wet_heavy.jpg` and `pictures/diagnosis_close_A.jpg`. In today's dry road every stone has a dark line round it; in the wet road the stones melt into one sheet. I measured it (section 2) and changed the road's settings one at a time (section 3). Three findings, all measured:
* **All the visible joint is the dark colour of the joints in the colour picture.** With that picture made flat the joints are gone, wet or dry (contrast 0.01). The relief picture (normal map) adds nothing measurable: dry road with the relief taken out, contrast 0.35; with it, 0.33. A normal map says which way each dot leans, not how deep it is; a groove's floor leans about as the stone's top does.
* **What washes the joints out is the SHINE that water adds** (low roughness, the water film, the extra specular): it puts the same bright reflection over stone and joint. With the shine taken off and only the wet darkening kept, the joints come back completely (contrast 0.34, against 0.08 for the wet road). Stronger relief helps only a little (0.13 at strength 6, and mostly white ticks on the stone corners); puddles are not the cause.
* **Round 2's wet road fails in every light.** In the lighting test set (below) the joints in the wet and heavy pictures have near contrast 0.01 to 0.12 where today's dry road has 0.18 to 0.33. The worst is light from behind into the glare (0.03) and the brazier's glare in the lockout shot (0.07).

**(2) What fixes it (tested): a "joint picture", free at render time.** One flat picture of the joints, laid on the road after the wetness layer, makes the joints dark AND dull (no water shine) while the stone tops keep their wet shine: wet cobbles with glistening tops and dark cracks (`pictures/solution_main_all_lights.jpg`, `pictures/solution_plate_size_1080x1920.jpg`). My recommended first setting, **"mild1"**: colour x0.85, roughness 0.9, specular x0.65, clear coat x0.55 in the joints, and the dulling cut in puddles. On the main camera, wet, near contrast goes from 0.07 to 0.47 (98 % of joint dots "seen" against 14 %); in the glare from 0.03 to 0.56; in heavy rain from 0.07 to 0.37 (puddle dots left out). **It costs no render time** (75 s against 78 s). Stronger settings (colour 0.3 to 0.6, the dulling x0.05 to x0.35) made a black net with ragged edges and are too much. The setting is a dial: the test set says where it stops passing.

**(3) Real geometry works too but is not needed.** A Geometry Nodes modifier that cuts the near road into 8 mm faces and presses real grooves in it makes strong, view-dependent joints that cast shadows (near contrast 0.50 with a 2 cm sharp groove). It costs about +2 to +3 minutes per picture, covers only a part of the road, cannot go into the glb, and with a shallow groove under the joint picture it did NOT improve the main view (0.40 against 0.47) and looks lumpier. I would keep it for one hero close-up, and only after cleaning the groove picture.

**(4) The lighting test set** (section 6): five lightings (A dusk lamps, B the lockout brazier's glare, C low side light, D flat overhead, E light from behind into the glare), three cameras (main, lockout, close), three states (dry, wet 0.85 / 0.5, heavy 1.0 / 0.8); 22 pictures (full, about 40 minutes) or 9 (quick, about 20 minutes); one command, `bash tools/run_lighting_test_set.sh`; a **pass line** that says "visible under all conditions" in numbers (near and middle bands: contrast, brightness difference and share of joint dots seen; section 6.3), chosen so that today's dry road in the film's own light passes. **Round 2 fails 16 of its 16 wet and heavy pictures; the road with mild1 passes 20 of 22** (all 16 street pictures, and 4 of the 6 lockout ones); the two that fail are the lockout shot's wet and heavy pictures in the middle band, where the sacks' big shadow, the brazier's glare and the puddles dominate (section 6.4). The script itself was tested end to end: the one-command script ran from start to end on the quick set in 1,119 seconds (18.7 minutes): it drew 9 pictures and 4 puddle masks, measured them and printed 8 PASS and 1 FAIL (the lockout B wet picture, the same failure as in the full set); its numbers agree with the full set's to within 0.009 in contrast (an independent second drawing of the same pictures; section 6.4).

**(5) The rubbish** (section 7). The sources I could read are thin for exactly 1926 and a front street: ash and cinders from the fires (kept in ash pits and middens; the north-east's colliery housing, up to 1914), coal holes and the night cart in the back lanes, and, in the 1926 lockout, families searching the waste heaps and digging for coal, which drops coal dust and slack everywhere. I added what I infer (mud, wet straw, sodden paper, a few leaves, crockery, horse droppings) and marked it. **The rubbish mask is a plain picture of the street from above** (red dirt, green "pieces lie here", blue mud) that follows the places rubbish gathers: the gutter, the foot of the kerb, the foot of the house walls, doorsteps, the foot of rain pipes and lamp posts, and in the lockout shot the drum, the slack heap, the dustbins, the sacks and the cart. A prototype (muck layer plus 2,000 small pieces placed by Geometry Nodes) reads well in the lockout shot, faintly in the street's main view, costs 0 to 14 seconds on a street picture (and 8 to 29 on the 205-second lockout one), chains after the joint picture, and has weak spots (section 7.5).

**(6) The plan** (section 8): first the setts (a reusable `JOINTS` node group after `WETNESS`, the test set, the person's look, the glb bake, the plate), then the rubbish (agree the mask, a `RUBBISH` node group, the pieces, the wall foot, the test set again). **What I did not do:** ask the painter (paid; it needs your go-ahead, and one sentence added to its brief), touch the glb or the stage, or do the pavement flags, kerbs and walls. **What I need from you:** how strong the joints and the rubbish should be (two dials), whether the flags and kerbs matter, and the go-ahead for a repaint.

## 2. How I measured "the joints show" (the method, with an example)

**An example first.** Take the close road picture of today's dry road (`pictures/diagnosis_close_A.jpg`, top left). In it you can see every stone and the dark line round it. Now take the same picture with the road wet: the stones melt into one grey sheet and only a few bright ticks are left. I wanted a number that says "the first picture is good, the second is bad", that anybody can recompute, and that does not depend on my eye.

**The joint mask.** A *joint* is the thin gap between two stones; a *stone face* is the flat top of a stone. The road's picture (Poly Haven's "square cobblestone", 2 m wide, one dot = 1 mm) shows the joints as dark olive lines. `tools/b01_make_joint_mask.py` finds them (a standard trick, a "black top-hat", that keeps thin dark lines and drops wide dark smudges) and writes a picture that is white on joints and black on stone faces (`pictures/joint_mask_check.jpg`: colour picture, the joint picture, joints in red). I first tried the height picture, but its joints are patchy (the supplied height picture shows the joint only 0.05 lower than the stone, on a 0 to 1 scale); the colour picture's joints are clear, so the mask comes from the colour picture (failure recorded in section 9). Blender then draws the road through its own texture coordinates with this mask as the colour (`tools/b02_lighting_and_variants.py`, `make_mask_material`), so that every dot of every render is known as "joint", "stone face" or "not road". The mask render is made once for each camera.

**The measure** (`tools/b04_measure_joints.py`, my own, defined in the file's first lines). For every joint dot, take the brightness of the stone faces beside it (the average of the stone-face dots in a 17-dot square), and call:
* **contrast** = (stone beside it - the joint dot) / stone beside it. 1.0 means the joint is black, 0.25 means a quarter darker than the stone, 0 means no difference, negative means the joint is BRIGHTER (a glare fills it);
* **delta** = the same difference in plain brightness (0 black to 1 white, of the finished picture as shown). A joint that is 30 % darker than a stone of brightness 0.05 is only 0.015 darker, and nobody sees it, so delta says whether the contrast is big enough to see;
* **seen** = the share of the joint dots that are at least 15 % AND at least 0.015 darker than the stone beside them.

The road is split into three bands by picture row: **near** (the lowest third of the rows that hold road), **middle**, **far**. At 540 x 960 the far joints are narrower than one dot and the far band says little (it is reported, not judged). Brightness is the finished 8-bit picture as shown (the same as the painter sees); the tables of sections 3 and 5 were measured on the PNG pictures as drawn (the lockout baseline from its JPEGs), and the reports of section 6.4 on the JPEGs of quality 92 that the study keeps (they were measured again to leave puddle dots out); I compared PNG and JPEG on four pictures and the near contrast differed by 0.00 to 0.01 (the largest: today's dry main picture, 0.233 from the PNG and 0.225 from the JPEG).

**Pictures** are drawn the way the film's plates are (round 2 settings: EEVEE, ray tracing on, shadow rays 4, shadow steps 16, 16 samples at 540 x 960 and 24 samples at 640 x 480), with the round 2 wetness layer on every material, with the machine's two threads. Dry = Wetness 0 and Puddles 0; wet = 0.85 and 0.5; heavy = 1.0 and 0.8.

**Cameras.** *main*: the street file's own camera (540 x 960). *lockout*: the lockout plate camera in the film's own lockout shot file, which has the props, the brazier and its glare (540 x 960; the file is opened read-only and never saved). *close*: a low view down the road, from (0.5, 6.0, 1.0) at 38 degrees (640 x 480), which has about 1.4 times more joint dots per band than the main view and shows the problem best.

## 3. What flattens the joints (the diagnosis, one change at a time)

**Result in one line:** *the only thing that ever made the joints show, wet or dry, is the dark colour of the joints in the colour picture; the shine that water adds fills them in; the "relief" (normal map) never made them show at all.*

All the pictures below are the close view in lighting A (the film's dusk lamps), drawn from the same camera; each row changes ONE thing from "wet, round 2" (the problem). The picture is `pictures/diagnosis_close_A.jpg`.

| picture | road | near contrast | near delta | near seen | middle contrast | middle delta | middle seen |
|---|---:|---:|---:|---:|---:|---:|---:|
| dry, as the film has it | 0.114 | 0.33 | 0.038 | 0.94 | 0.28 | 0.033 | 0.91 |
| wet, round 2 (the problem) | 0.305 | 0.08 | 0.016 | 0.32 | 0.05 | 0.014 | 0.07 |
| wet, all shine taken off (colour darkening only) | 0.095 | 0.34 | 0.032 | 0.98 | 0.28 | 0.026 | 0.93 |
| wet, roughness 0.9 (film and boost kept) | 0.182 | 0.18 | 0.022 | 0.69 | 0.10 | 0.014 | 0.34 |
| wet, no water film and no extra shine (roughness 0.3 kept) | 0.281 | 0.10 | 0.019 | 0.40 | 0.07 | 0.019 | 0.16 |
| wet, relief strength 3 (was 1.4) | 0.303 | 0.11 | 0.034 | 0.42 | 0.06 | 0.023 | 0.19 |
| wet, relief strength 6 | 0.300 | 0.13 | 0.052 | 0.53 | 0.08 | 0.039 | 0.33 |
| wet, relief not flattened (Relief Flatten 0, Grain Fill 0) | 0.302 | 0.10 | 0.045 | 0.49 | 0.06 | 0.036 | 0.30 |
| wet, relief picture removed | 0.306 | 0.09 | 0.015 | 0.20 | 0.04 | 0.008 | 0.01 |
| wet, stone tops stay drier (Dry Tops 1.0) | 0.305 | 0.08 | 0.015 | 0.32 | 0.05 | 0.014 | 0.08 |
| wet, no puddles (dial 0) | 0.307 | 0.08 | 0.016 | 0.32 | 0.05 | 0.014 | 0.07 |
| wet, colour picture made flat | 0.305 | -0.01 | 0.001 | 0.10 | 0.01 | 0.005 | 0.04 |
| DRY, colour picture made flat | 0.116 | 0.01 | 0.001 | 0.03 | 0.02 | 0.002 | 0.01 |
| DRY, relief picture removed | 0.114 | 0.35 | 0.040 | 0.99 | 0.28 | 0.032 | 0.94 |

How to read it: the dry road has contrast 0.33 and 94 % of its joint dots are "seen". The wet road has 0.08 and 32 %. The pass line of section 6 asks for 0.25 and 70 % at the close camera.

**What the rows say, in plain words**

1. **Colour picture made flat (rows "colour picture made flat"): contrast 0.01 dry and -0.01 wet.** Without the dark joint colour, the joints are NOT there, in any condition. All the visible joint in today's road is paint: dark olive lines in the colour picture. *Example:* a flat grey road with a relief picture on it is, to the lamp, one grey road.
2. **Relief picture removed (rows "relief picture removed"): DRY contrast 0.35, the same as with it (0.33).** The relief picture adds nothing the eye can measure to the joints. The reason (my reading, and a number): a normal map only says which way each dot leans; the floor of a groove leans almost the same way as the top of a stone. In Poly Haven's picture the joint floors lean 9 degrees on average (stone faces 4, stone edges 8, measured in `work/joint_cores.png` against the normal picture); under a lamp that is a few per cent of brightness, in random directions, which averages out. The strong lean is only at the stone edge, about 2 to 4 mm wide, and at 540 x 960 one dot is 6 mm wide at 8 m (more, along the road).
3. **All shine taken off (colour darkening only): contrast 0.34, "seen" 98 %. The joints come back completely.** So the wet look washes the joints out through SHINE. Water makes a surface smooth; a smooth surface reflects the bright sky and lamps over the stone and over the joint alike, and the joint's dark colour is lost under a bright veil. *Example:* a black plate looks black until you tilt it to the window.
4. **Each part of the shine alone is not enough, all three together do it.** Roughness 0.9 (film and boost kept): 0.18. No water film and no extra shine (roughness 0.3 kept): 0.10. The round 2 layer has all three at once (wet roughness 0.3, film coat 0.3, specular boost 0.25).
5. **Stronger relief helps a little but does not cure it.** Relief strength 3: contrast 0.11, "seen" 42 %. Strength 6: contrast 0.13, 53 %. Relief not flattened (Relief Flatten 0, Grain Fill 0): 0.10 and 49 %. Their DELTA (the brightness difference) rises two to three times (0.016 to 0.034 / 0.052 / 0.045), but this is the white ticks on the stone corners, not the joints.
6. **Puddles are not the cause.** "No puddles" (dial 0): the same numbers as the wet road. The puddle layer flattens the relief inside puddles (round 2 did that on purpose), but outside puddles the shine does the damage, and the joints are hidden as much with no puddles as with them. (Section 3b has the share of joints under puddles.)
7. **"Stone tops stay drier" (Dry Tops 1.0): no change** (0.08, the same). The height picture is too flat to say where the tops are (stone 0.56, joint 0.51 on a 0 to 1 scale, measured against my joint mask).
8. **Poly Haven's own ambient occlusion picture** (the picture of how much light each dot would miss because of its neighbours; it is on Poly Haven for this road: `https://polyhaven.com/a/square_cobblestone`) **is no cure either:** joint 0.77, stone 0.85, so the joint is only 10 % darker than the stone. I downloaded it (CC0) only to measure it (work/polyhaven_download).

The main camera says the same (540 x 960, lighting A):

| picture | road | near contrast | near delta | near seen | middle contrast | middle delta | middle seen |
|---|---:|---:|---:|---:|---:|---:|---:|
| dry | 0.115 | 0.23 | 0.027 | 0.87 | 0.16 | 0.019 | 0.56 |
| wet (the problem) | 0.195 | 0.07 | 0.015 | 0.14 | 0.05 | 0.009 | 0.07 |
| wet, all shine taken off | 0.096 | 0.23 | 0.022 | 0.87 | 0.16 | 0.016 | 0.46 |
| wet, no film and no extra shine | 0.182 | 0.09 | 0.018 | 0.21 | 0.06 | 0.011 | 0.09 |
| wet, relief strength 3 | 0.197 | 0.07 | 0.019 | 0.24 | 0.05 | 0.010 | 0.12 |
| wet, relief not flattened | 0.199 | 0.06 | 0.019 | 0.28 | 0.05 | 0.009 | 0.13 |
| wet, relief picture removed | 0.195 | 0.06 | 0.011 | 0.03 | 0.04 | 0.007 | 0.04 |
| wet, colour picture made flat | 0.195 | 0.01 | 0.005 | 0.09 | 0.01 | 0.002 | 0.05 |
| DRY, colour picture made flat | 0.114 | 0.01 | 0.001 | 0.00 | 0.00 | 0.000 | 0.00 |

**Why "missing shadow" is also true.** A real groove is dark because the stones on both sides block the light (a little "shadow" in the joint whatever the light). EEVEE draws no shadow from a picture, and a normal map only changes the lean of the surface, not its depth, so nothing in the road material makes the joint dark except its own colour. Real geometry does (section 5).

### 3b. Where each light puts the problem (baseline, round 2)

The same measure in all the pictures of the lighting test set (section 6 defines them). Dry rows are today's road; the wet and heavy rows are round 2.

| picture | road | near contrast | near delta | near seen | middle contrast | middle delta | middle seen |
|---|---:|---:|---:|---:|---:|---:|---:|
| main A dry | 0.115 | 0.23 | 0.027 | 0.87 | 0.16 | 0.019 | 0.56 |
| main A wet | 0.195 | 0.07 | 0.015 | 0.14 | 0.05 | 0.009 | 0.07 |
| main A heavy | 0.186 | 0.07 | 0.013 | 0.13 | 0.05 | 0.008 | 0.07 |
| main C dry | 0.138 | 0.18 | 0.026 | 0.68 | 0.13 | 0.017 | 0.34 |
| main C wet | 0.322 | 0.06 | 0.018 | 0.09 | 0.05 | 0.016 | 0.07 |
| main D dry | 0.161 | 0.23 | 0.037 | 0.89 | 0.16 | 0.027 | 0.59 |
| main D wet | 0.212 | 0.09 | 0.021 | 0.20 | 0.07 | 0.013 | 0.09 |
| main E dry | 0.139 | 0.19 | 0.024 | 0.70 | 0.14 | 0.019 | 0.46 |
| main E wet | 0.502 | 0.03 | 0.010 | 0.09 | 0.02 | 0.006 | 0.03 |
| main E heavy | 0.481 | 0.05 | 0.014 | 0.14 | 0.03 | 0.008 | 0.08 |
| close A dry | 0.114 | 0.33 | 0.038 | 0.94 | 0.28 | 0.033 | 0.91 |
| close A wet | 0.305 | 0.08 | 0.016 | 0.32 | 0.05 | 0.014 | 0.07 |
| close A heavy | 0.303 | 0.07 | 0.011 | 0.25 | 0.04 | 0.010 | 0.06 |
| close C wet | 0.339 | 0.09 | 0.018 | 0.35 | 0.05 | 0.014 | 0.09 |
| close D wet | 0.320 | 0.11 | 0.023 | 0.41 | 0.07 | 0.018 | 0.11 |
| close E wet | 0.400 | 0.01 | -0.002 | 0.27 | 0.03 | 0.009 | 0.07 |
| lockout B dry | 0.267 | 0.19 | 0.039 | 0.66 | 0.09 | 0.034 | 0.16 |
| lockout B wet | 0.369 | 0.07 | 0.017 | 0.19 | 0.08 | 0.025 | 0.17 |
| lockout B heavy | 0.349 | 0.06 | 0.011 | 0.17 | 0.06 | 0.014 | 0.17 |
| lockout C wet | 0.178 | 0.10 | 0.016 | 0.27 | 0.06 | 0.011 | 0.13 |
| lockout D wet | 0.176 | 0.12 | 0.021 | 0.34 | 0.07 | 0.011 | 0.13 |
| lockout E wet | 0.534 | 0.06 | 0.015 | 0.20 | 0.05 | 0.018 | 0.15 |

* **Every wet and heavy picture fails**, in every lighting and every camera: near contrast 0.01 to 0.12 against 0.18 to 0.33 dry.
* **The worst is light from behind into the glare (E):** near contrast 0.03 (main) and 0.01 (close), because the glare is a bright veil over the road. The brazier's glare in the lockout shot (B) is the same: 0.07.
* **Even the DRY road is weaker under the low side light (C): 0.18, and its middle band only 34 % seen.**
* **Puddles cover the road, not specially the joints.** Share of the road under a puddle (and of the joint dots and the stone-face dots alone), from the road's puddle mask drawn as plain light (`tools/b12_puddles_over_joints.py`, `work/r10`, `work/r12`): main camera: wet dial 7.9 % of the road is puddle (joint dots 3.5 %, stone dots 6.3 %); heavy dial 29.8 % (29.6 %, 27.2 %); close camera: wet dial 2.9 % of the road is puddle (joint dots 0.4 %, stone dots 1.9 %); heavy dial 12.5 % (4.7 %, 10.2 %); lockout camera: wet dial 6.4 % of the road is puddle (joint dots 3.6 %, stone dots 5.3 %); heavy dial 42.2 % (47.1 %, 43.3 %). A joint dot is about as often under water as a stone dot (within 6 percentage points in every case), which fits the 'no puddles' row of the table above. The lockout camera sees a lot of puddle at the heavy dial (the recipe's calibration table says 42 %), and water at a grazing angle really does hide what lies under it, so **from here on the study leaves dots under a puddle out of the measure** and reports the puddle share beside each picture.

## 4. How people keep cobbles and setts in relief today, and what I could confirm

I searched the web for 2024 to 2026 practice in Blender 4.x and 5.x. **The search tool gave mostly forum threads, product pages and the manual; I cite what I read and say what I only saw in a search summary.** Nothing here is a recipe I copied: the three I judged most promising I built and measured (section 5).

| way | what sources say | did I test it | cost, as far as I know |
|---|---|---|---|
| **A. Real geometry: displacement on a finely cut road** | In EEVEE (Blender 4.2 and later, so 5.x too) displacement moves the mesh's own corners, so the road must be cut into many small faces first; the manual's text for EEVEE says "Displacement Only" is not supported and falls back to "Displacement and Bump", and that flat-shaded faces split when displaced ([manual page change, EEVEE-Next](https://projects.blender.org/blender/blender-manual/pulls/104816/commits/5acc07af9870e3f50e6baf18ca6de1990379d002), seen in a search summary; the related pull request page [#113979](https://projects.blender.org/blender/blender/pulls/113979) would not open for me). The fine cutting in Cycles can be automatic ("adaptive subdivision", experimental, Cycles only: general knowledge, not read here); in EEVEE it has to be done by hand. | **Yes**, as a Geometry Nodes modifier (Subdivide Mesh, then Set Position from a picture, section 5) | time: +120 to +165 seconds on a picture that takes 75 to 85 seconds (2.5 to 3 times at that small size; the extra is mostly the one-time cutting and shadow work, so at plate size it should be a smaller share: not measured); 1.4 million faces for 11 m of road |
| **B. Parallax mapping** (a flat surface that looks deep because each dot's picture is looked up a little to one side, by its height) | Blender has no built-in parallax node. Free and paid choices: a free parallax "node group" for EEVEE and Cycles that needs a separate copy of the group for each texture ([Gumroad listing](https://djpiercy.gumroad.com/l/ddzlrg)); one free set-up that only works with generated coordinates, not UV ([BlenderArtists](https://blenderartists.org/t/parallax-occlusion-mapping-test/1513622)); a Blender Extensions add-on, "Parallax Node": one node, a step count, custom UV layers, EEVEE and Cycles, version 1.1 needs Blender 5.0 ([listing](https://superhivemarket.com/products/parallax-node)); and an experimental EEVEE build that adds a "Parallax Occlusion" choice that is not in the main program ([devtalk thread](https://devtalk.blender.org/t/parallax-occlusion-mapping/15774/36)). None of the pages says it casts shadows or makes a joint darker. | **No** (it needs an add-on installed from outside; and my diagnosis says the missing thing is darkness in the joint, not depth) | one extra look-up per step: slow on large textures |
| **C. A stronger normal map** | The usual first advice: raise "Strength". | **Yes** (section 3, rows "relief strength 3 / 6") | free; raises the white ticks on stone corners, not the joints |
| **D. Ambient occlusion or cavity picture driving colour, roughness and specular ("specular occlusion")** | Search result summaries: use the AO or cavity map to darken and dull the crevices (the road shader documentation of [Studio 397](https://docs.studio-397.com/x/NQBDAg) has separate AO, specular and roughness settings for the blended areas); a wet-surface tutorial for Unreal Engine ([Axton, ArtStation](https://axton.artstation.com/projects/nYeAJe)) drives puddles from height and slope and says its specular use is "not perfectly PBR compliant" but needed for the look. For Blender's own nodes: the Ambient Occlusion node "Inside" switch, and the Bevel node and Pointiness for edges ([BlenderNation 2019](https://www.blendernation.com/2019/02/10/better-edge-and-cavity-masking-with-cycles/)); a bug report says the AO node is unreliable on bevelled models ([Blender bug 90134](https://developer.blender.org/T90134)), and a shader seller's page says Bevel and Pointiness only work in Cycles, so in EEVEE you would see only scratches (page for Blender 2.9 to 3.2: not checked for 5.2). | **Yes**, with a picture made from the road's own joints (the "joint picture"), not a live AO node | free at render time |
| **E. Wet joints stay dark and rough while stone tops shine** | The same idea as D, seen from the water side: water gathers in low spots and the joints hold dark, dull wet muck while the stone tops catch the light. I found no Blender tutorial that sets it up; it is what D does when the cavity picture cuts specular, coat and roughness in the joints. | **Yes**, inside D | free |
| **F. Painted style: dark joint lines that survive the repaint** | No Blender source. From our own painter test ([`painter_test/notes - wet street painter test.md`](../../painter_test/notes%20-%20wet%20street%20painter%20test.md)): the painter DID keep "the thin dark lines between setts" in the wet plate, and the film's stage curve then crushes dark values (painted 0.08 becomes 0.02, the wet road arrives at 0.75 of its painted brightness) and "loses the dark sett joints". So the lines must start with a real brightness difference (that is why the pass line has a DELTA), and the brief must say to keep them. A line-drawing pass (Freestyle or Line Art) needs real edges to draw, so it would only follow real geometry (A). | **Not as a drawing pass.** The first half (the plate has the lines) is what D does. The painter was not asked (paid) | the painter's price is about US$0.20 to 0.28 a repaint (painter test) |
| **G. Modelled stones** (a real model of every sett, or Geometry Nodes that lays stones along rows) | Search found no 2024 to 2026 tutorial for a whole street. | **No** | the road has about 12,000 setts (32 to the square metre, counted on a crop of the picture; 370 square metres of road): heavy for one plate, a possibility only for a hero close-up |

**Two more things I looked at because they came up:**
* **The texture filter.** Blender's "anisotropic filtering" keeps a texture sharp when it is seen at a grazing angle, which a road in a low camera is. A background Blender run has it at 2 (`FILTER_2`). I tried 16 in section 5.
* **Poly Haven's own other pictures** (ambient occlusion, a higher-quality 2k height picture, the "ARM" picture that packs AO, roughness and metal): downloaded and measured; the AO and height pictures show the joints too weakly to be the cure (section 3, row 8).

## 5. The solutions I built and measured

### 5.1 The joint picture (solution 1: free, works in every renderer, works in the glb)

**What it is, with an example.** A real joint between two stones is dark and dull whatever the weather: it is a narrow crevice, full of earth and moss, and the light barely reaches it. So: lay one more flat picture over the road, a **joint picture** (grey: white in the joints, black on the stone faces, a soft edge), through the road's own texture coordinates, and use it AFTER the wetness layer, so wetness has no say:

* **colour** is multiplied by a number below 1 in the joints (the joint is darker than the stone);
* **roughness** is pulled toward 0.9 in the joints (no smooth water film: dull);
* **specular** (the reflection strength) is multiplied by a number below 1 in the joints;
* **clear coat** (the water film's reflection) is multiplied by a number below 1 in the joints;
* **in a puddle** the dulling of roughness, specular and coat is cut by 0.8 times the puddle mask (a puddle's water covers the joint and mirrors the sky), but the dark colour stays (you see the dark joint through the water).

So the stone tops keep their wet shine and the joints stay dark and dull: the picture of wet cobbles with glistening tops and black cracks. It is the method D/E of section 4. It costs nothing at render time (77 s against 87 s for the same close picture, which is noise). Where it lives: the function `joint_picture(...)` in `tools/b02_lighting_and_variants.py` (about fifteen nodes); where it would live in the project: a small node group put after `WETNESS` on the road (section 8).

**How the joint picture is made** (`tools/b01_make_joint_mask.py`, `tools/b01b_make_soft_cavity.py`; both plain Python): from the road's colour picture, find the joints; close the gaps along the lines (45 dots, 4.5 cm, so that a lighter stretch of joint does not break the line into dashes); blur it about 4 mm; scale so that the middle of an ordinary joint is 1; add a faint 1 cm halo. The result is a 2048 x 2048 grey picture of 0.6 MB (it repeats every 2 m like the colour picture). **It must be made again for any other texture** (the flags, the setts of another street).

**The tries, in order** (close view, lighting A, wet, rows are in the order I did them; the full pictures are `pictures/solution_joint_picture_first_tries.jpg`, `pictures/solution_joint_picture_soft.jpg`):

| picture | road | near contrast | near delta | near seen | middle contrast | middle delta | middle seen | far contrast | far delta | far seen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| wet, round 2 (the problem) | 0.305 | 0.08 | 0.016 | 0.32 | 0.05 | 0.014 | 0.07 | 0.05 | 0.012 | 0.08 |
| dry, as the film has it | 0.114 | 0.33 | 0.038 | 0.94 | 0.28 | 0.033 | 0.91 | 0.15 | 0.019 | 0.55 |
| joint picture, colour only (0.45) | 0.303 | 0.12 | 0.022 | 0.47 | 0.08 | 0.019 | 0.18 | 0.07 | 0.017 | 0.09 |
| joint picture first try "b" (colour 0.45, dull, ragged picture) | 0.263 | 0.85 | 0.240 | 1.00 | 0.76 | 0.289 | 1.00 | 0.48 | 0.138 | 0.90 |
| joint picture first try "c" (strong) | 0.256 | 0.96 | 0.271 | 1.00 | 0.89 | 0.343 | 1.00 | 0.57 | 0.158 | 0.92 |
| soft picture soft3 (colour 0.8, spec x0.6, coat x0.5) | 0.289 | 0.58 | 0.183 | 0.99 | 0.47 | 0.192 | 0.98 | 0.24 | 0.070 | 0.68 |
| soft picture soft1 (0.7, x0.5, x0.35) | 0.287 | 0.63 | 0.199 | 0.99 | 0.52 | 0.213 | 0.99 | 0.26 | 0.074 | 0.71 |
| soft picture soft2 (0.6, x0.35, x0.25) | 0.284 | 0.70 | 0.217 | 1.00 | 0.58 | 0.237 | 0.99 | 0.30 | 0.086 | 0.77 |
| closed picture mild1 (0.85, x0.65, x0.55) | 0.280 | 0.60 | 0.186 | 1.00 | 0.52 | 0.204 | 1.00 | 0.33 | 0.097 | 0.82 |
| closed picture mild2 (0.9, x0.75, x0.7) | 0.284 | 0.54 | 0.167 | 1.00 | 0.46 | 0.179 | 1.00 | 0.28 | 0.085 | 0.76 |
| mild1 with texture filter 16 | 0.280 | 0.60 | 0.186 | 1.00 | 0.52 | 0.204 | 1.00 | 0.33 | 0.097 | 0.82 |
| real geometry, soft groove 2.5 cm | 0.242 | 0.14 | 0.028 | 0.53 | 0.45 | 0.144 | 0.91 | 0.24 | 0.092 | 0.80 |
| real geometry, sharp groove 2 cm | 0.270 | 0.50 | 0.150 | 0.93 | 0.47 | 0.234 | 0.89 | 0.05 | 0.051 | 0.66 |
| sharp geometry + soft2 picture | 0.262 | 0.64 | 0.179 | 0.97 | 0.63 | 0.273 | 0.95 | 0.29 | 0.105 | 0.78 |
| mild1 + shallow geometry 8 mm | 0.269 | 0.64 | 0.197 | 0.97 | 0.55 | 0.254 | 0.92 | 0.27 | 0.087 | 0.76 |

* **First tries "b" and "c"** (colour 0.45 or 0.30, the dulling at 0.25 or 0.05): contrast 0.85 and 0.96 against 0.33 for the dry road: the joints are jet black and ragged, like a black net. Too much. The picture itself was ragged because the colour picture's joint outlines are.
* **Colour alone (joint a):** contrast 0.12. The dark colour alone does almost nothing (the shine fills it in again). **The dulling is what works**: this is the proof of section 3 from the other side.
* **Softer picture, gentler numbers (soft1 to soft3):** contrast 0.47 to 0.58 in the middle band, 0.58 to 0.70 near: better, and the road finally reads as wet cobbles (`pictures/solution_joint_picture_soft.jpg`), but still about twice the dry road's 0.33.
* **Closed picture, milder numbers (mild1, mild2):** near contrast 0.60 / 0.54, "seen" 100 %. **mild1 is my recommended first setting**: colour 0.85, roughness 0.9, specular x0.65, coat x0.55, puddle clearing 0.8, the closed picture. Why mild1 and not the milder mild2: at the main camera in A wet mild1 gives near contrast 0.47 and mild2 0.41, and mild2 is not weaker than needed there; but I put only mild1 through the whole test set (section 6.4), so mild1 is the one that is proven, and mild2 is the first thing to try if the person finds mild1 too strong. **The strength is a dial in practice**: all four numbers can be moved together (1 = mild1, 0 = off) and the test set says where it stops passing.

**On the main camera** (540 x 960, lighting A, wet), with the other lighting conditions in section 6:

| picture | road | near contrast | near delta | near seen | middle contrast | middle delta | middle seen | far contrast | far delta | far seen |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| wet, round 2 (the problem) | 0.195 | 0.07 | 0.015 | 0.14 | 0.05 | 0.009 | 0.07 | 0.03 | 0.005 | 0.05 |
| dry, as the film has it | 0.115 | 0.23 | 0.027 | 0.87 | 0.16 | 0.019 | 0.56 | 0.06 | 0.007 | 0.02 |
| mild1 | 0.195 | 0.47 | 0.111 | 0.98 | 0.27 | 0.059 | 0.66 | 0.02 | 0.005 | 0.20 |
| mild2 | 0.196 | 0.41 | 0.099 | 0.94 | 0.22 | 0.049 | 0.54 | -0.00 | 0.001 | 0.17 |
| mild1 + shallow geometry 8 mm (y 3 to 18 m) | 0.199 | 0.40 | 0.102 | 0.85 | 0.18 | 0.045 | 0.68 | -0.00 | 0.002 | 0.31 |
| AT 1080 x 1920: wet, round 2 | 0.216 | 0.12 | 0.027 | 0.40 | 0.09 | 0.019 | 0.21 | 0.04 | 0.007 | 0.05 |
| AT 1080 x 1920: wet, mild1 | 0.173 | 0.53 | 0.096 | 1.00 | 0.35 | 0.068 | 0.79 | 0.14 | 0.030 | 0.42 |

**What the pictures show** (`pictures/solution_main_all_lights.jpg`): in dusk lamps (A), side light (C), overhead light (D), light from behind with the glare (E), heavy rain and dry, the road reads as setts; in the glare (E) the joints are black and the stone tops are bright; in heavy rain the big puddles (which cover the joints, correctly) still hide them and the dry parts show them.

### 5.2 Real geometry (solution 2: strong, view-dependent, but slow and near only)

**What I built** (`geometry(...)` in `tools/b02_lighting_and_variants.py`; a Geometry Nodes modifier on the road): it cuts out the part of the road between two distances (3 and 14 m along the street for the close view), cuts every face of it into 4096 small faces (`Subdivide Mesh`, level 6: about 8 mm squares; 1.4 million faces for 11 m of road), and pushes every corner DOWN by a depth times the groove picture along the surface normal. Real grooves between real stones, which catch the light, throw their own shadows (the lamps' shadow maps reach into them) and show at the edge of the picture.

* **Soft groove from the cavity picture, 2.5 cm deep:** the stones look swollen like cushions, the joints are wide shallow bowls: contrast near 0.14 (the picture's gradient is too gentle), middle 0.45.
* **Sharp groove from the "height" picture (1 for the joint, 0 on the stone, a 3 mm edge), 2 cm deep:** contrast near 0.50, middle 0.47, "seen" 93 % and 89 %. Real, hard shadows in the joints. It looks like a rough cobbled street, a little deep and ragged (the groove follows the colour picture's ragged joints).
* **Sharp geometry plus the joint picture:** 0.64 near, 0.63 middle, far 0.29.
* **What limits it:** it only exists where the road is cut (3 to 14 m here; the part beyond looked flat in the 4th panel of the picture, far contrast 0.05). It took **195 to 205 seconds against 80 for the same close picture** (and 241 against 75 for the main view with 15 m of geometry): about +120 to +165 seconds, mostly the one-time cutting and the shadow work, so for a long plate it should be a smaller share (not measured). It cannot go into the glb and the stage (the stage shows the painting on its own flat road; the painting carries the joints). It needs a high-resolution mesh near the camera, which is awkward when the camera moves along the street (a plate is one still, so for a plate it is fine).
* **The picture** is `pictures/solution_geometry_close.jpg`.

### 5.3 The hybrid, the texture filter, and the size the painter sees

* **The texture filter (anisotropic filtering 16 instead of the default 2): no change.** Near contrast 0.60 / middle 0.52 / far 0.33 against 0.60 / 0.52 / 0.33 with the default: the same to two decimals, and the same to the eye (`pictures/solution_close_hybrid_filter.jpg`, first two panels). Either the setting does not reach EEVEE in a background run, or the road was already as sharp as it gets; I cannot tell. It is not a cure.
* **The hybrid, mild1 plus an 8 mm real groove** (sharp profile; 11 m of road for the close view, 15 m for the main view): in the close view near contrast 0.64 and middle 0.55 (mild1 alone 0.60 and 0.52), so a little better; in the main view near 0.40 and middle 0.18 (mild1 alone 0.47 and 0.27), so WORSE, because the groove's edges catch the wet shine. To the eye it is lumpier and less clean than mild1 alone (third panel of `pictures/solution_close_hybrid_filter.jpg`: ragged bright rims along the joints, small lumps far away, from the picture being sampled at 8 mm). It costs +120 to +165 seconds. **So real geometry is not needed to pass; it is an option for one hero close-up, and it needs a cleaner groove picture first.**
* **At the size the painter sees (1080 x 1920, lighting A, wet, 16 samples):** round 2: near contrast 0.12 (40 % seen), middle 0.09 (21 %), far 0.04; with mild1: near 0.53 (100 %), middle 0.35 (79 %), far 0.14 (42 %). Round 2 looks a little better at this size than at 540 x 960 (more dots to show the joint) but is still far under the dry road and under the pass line. The lower road at 100 % is `pictures/solution_plate_size_1080x1920.jpg`. **One weak spot I can see in it:** at middle distance the joints that run across the road look like short dashes (they are foreshortened, and the joint picture has small gaps in them); and near the brazier's glare in the lockout shot the bright rim of a stone edge draws curly outlines that can look like scribbles. A cleaner joint picture drawn from a straight grid instead of the colour picture's ragged joints (step A1) would help both; not tried.

## 6. THE LIGHTING TEST SET (every later helper must draw this, and pass it)

**Why it exists.** "The geometry should still be visible under all conditions" is only true if somebody looks under all conditions. Today a helper tunes the road in the dusk lamps, sees good joints, and the first brazier glare or heavy rain ruins them. This set is a fixed list of pictures, a command that draws them, and a number that says PASS or FAIL.

**Example first.** Run the quick set on the road as it is today: all nine pictures fail (near contrast 0.01 to 0.09, where today's dry road has 0.19 to 0.33). Run it on the road with the joint picture: 8 of the nine pass (near contrast 0.30 to 0.62); the ones that fail: lockout_B_wet (middle contrast 0.041 < 0.07). That is the whole use.

### 6.1 The five lightings (letters A to E), how each is made, and how to switch

Every lighting is made by `set_lighting(letter)` in `tools/b02_lighting_and_variants.py` (a function inside Blender; it puts everything back first, so lightings never pile up). The suns and lights used are listed here so that anybody can rebuild them.

| letter | name | what it is | dry road brightness, main camera | why it is in the set |
|---|---|---|---|---|
| **A** | dusk lamps | the street exactly as the film lights it: five gas lamps (260 W each), the lit windows (45 W each), the two dim sky suns (0.3 and 0.2) | 0.115 | the film's own light: the plate lighting |
| **B** | brazier glare | the lockout shot file as the film lights it, with the brazier's light (900 W, orange) and its glare on the wet road. It is the same as A in the lockout file; B only names the picture | 0.267 (lockout camera) | the lockout plate: the glare is the worst case in the real film |
| **C** | low side light | all lamps off (the two sky suns stay); one low sun, 10 degrees above the horizon, from the right of the street and slightly from the camera side (strength 1.0, warm). **The houses' shadows are switched off for this one** (otherwise the houses block the low sun and the road is simply dark), so C is an artificial test of how the relief looks under raking light, not a picture of a real evening | 0.138 | a light that comes from the side, so the relief picture has its best chance. If the joints do not show here, they do not show |
| **D** | flat overhead light | all lamps off; one sun almost straight up (88 degrees, strength 0.4, slightly warm) | 0.161 | the opposite: almost no side light, so a relief picture has nothing to work with and only the joints' own darkness counts |
| **E** | light from behind into the glare | A as it is, plus one strong low light (30,000 W, orange, 0.35 m across) at the far end of the street (x 0, y 66, z 5.9, which is 1.2 m above the road there), shining toward the camera | 0.139 | a bright source low in front of the camera: every shiny surface reflects it. The worst case for "light washes out the joints" |

The sun strengths of C and D were chosen so that the DRY road is about as bright as in A (0.12 to 0.16, `work/cal`), so that a change in how well the joints show comes from the kind of light, not from how much. The first try of the back light (E) stood at z = 1.8, under the road (the street climbs 4 degrees), and did nothing; the first try of C was six times too strong. Both are recorded in section 9.

### 6.2 Cameras, sizes, states

| camera | file | size | samples | what it shows |
|---|---|---|---|---|
| **main** | the street copy `set_copy/street.blend` | 540 x 960 | 16 | the film's street camera |
| **lockout** | the film's lockout shot file (opened read-only, never saved), the lockout plate camera | 540 x 960 | 16 | the plate of the lockout shot, with the props |
| **close** | `set_copy/street.blend` | 640 x 480 | 24 | a low view down the road from (0.5, 6.0, 1.0): more joint dots |

States: **dry** (Wetness 0, Puddles 0), **wet** (0.85 / 0.5), **heavy** (1.0 / 0.8). Plate settings are the round 2 ones (EEVEE, ray tracing on, shadow rays 4, steps 16).

**The two sets** (`tools/b09_lighting_test_set.py`, `FULL` and `QUICK`):
* **quick, 9 pictures, about 20 minutes:** main A wet, A heavy, C wet, D wet, E wet; close A wet, E wet; lockout B wet, E wet. These are the conditions the baseline fails most.
* **full, 22 pictures, about 40 minutes:** main A dry / wet / heavy, C dry / wet, D dry / wet, E dry / wet / heavy; close A dry / wet / heavy, C wet, D wet, E wet; lockout B dry / wet / heavy, C wet, D wet, E wet.

**The command** (one, from any folder; it never saves a Blender file and never touches the film project):

```
bash tools/run_lighting_test_set.sh quick OUT_FOLDER
bash tools/run_lighting_test_set.sh full  OUT_FOLDER --variant NAME --args '{"...": ...}'
bash tools/run_lighting_test_set.sh quick OUT_FOLDER --after-apply my_solution.py
```
`--variant` names a change of the road material in `tools/b02_lighting_and_variants.py` (the study's solutions are there: `joint_picture`, `geometry`, `combo`); `--after-apply` is a Python file that is run once inside Blender after the wetness layer is on, for a new solution of your own. It stops if the free disk space is below 1.25 GB, skips pictures already drawn, and prints the PASS / FAIL table (`report.txt`). The measuring is `tools/b04_measure_joints.py`; the masks are drawn by the same run.

### 6.3 The pass line ("visible under all conditions", in numbers)

For every picture of the set, in the **near** and **middle** bands of the road (section 2 defines contrast, delta and seen):

| camera | band | contrast at least | delta at least | seen at least |
|---|---|---|---|---|
| main | near | 0.18 | 0.020 | 0.65 |
| main | middle | 0.12 | 0.015 | 0.30 |
| lockout | near | 0.15 | 0.020 | 0.50 |
| lockout | middle | 0.07 | 0.015 | 0.12 |
| close | near | 0.25 | 0.030 | 0.70 |
| close | middle | 0.20 | 0.025 | 0.60 |

and the other fault: **contrast at most 0.75 (main, lockout) or 0.80 (close)**, so that the cure is not a harsh black grid.

**How I chose it (by looking, then writing the numbers down).** I looked at today's DRY road in the film's own lights (A and D, the lockout B) and at the close view: those pictures show the setts clearly, and the person's own verdict on the street so far was that it "works really well". So the line is set just under what today's dry road has in every one of those pictures: they all pass it (section 6.4, baseline table: six of six). Then I looked at every wet and heavy picture of round 2: the joints are gone, and every one of them fails by a wide margin (near contrast 0.01 to 0.12; "seen" 9 to 41 %). The upper limit comes from the first try of the cure, which made the joints black and ragged (contrast 0.85 to 0.96, section 5): 0.75 is just under the strongest look I would keep. The delta column is there because the stage's brightness curve crushes dark values (painter test): a contrast on a very dark road means nothing if the brightness difference is under about 0.02.

*The line is a first line.* It was chosen by one person (me) looking at about 60 pictures; the person who owns the film should look at `pictures/solution_main_all_lights.jpg` and say if it is too lenient or too strict. If a later helper finds a picture that fails the line but looks fine, or passes and looks wrong, the line is what to change, not the picture.

### 6.4 What the set says: the road as it is today, and the road with the joint picture

**How to read the reports below.** `pud` is the share of the road that was left out because it lies under a puddle (the puddle plus a 2-dot margin; it is calibrated for the main camera, so it is a little higher than the shares in section 3b); `near` and `middle` give contrast, delta and seen; the last column is the output of `report` (PASS, or FAIL with the first three reasons). The nine pictures of the quick set are among the 22.

**The road as it is today (round 2), the full set** (`work/r01/measurements_nopuddle.json`, the pictures of `work/r01`):

```
picture                  road   pud    near c / delta / seen    middle c / delta / seen  verdict
main_A_dry              0.115     -        0.23  0.026  0.83          0.15  0.018  0.49  PASS
main_A_wet              0.202  0.10        0.07  0.015  0.14          0.05  0.009  0.06  FAIL  near contrast 0.068 < 0.18; near delta 0.015 < 0.02; near seen 0.145 < 0.65
main_A_heavy            0.194  0.34        0.07  0.012  0.05          0.04  0.008  0.03  FAIL  near contrast 0.068 < 0.18; near delta 0.012 < 0.02; near seen 0.048 < 0.65
main_C_dry              0.138     -        0.18  0.025  0.66          0.12  0.017  0.32  PASS
main_C_wet              0.334  0.10        0.06  0.018  0.09          0.04  0.012  0.04  FAIL  near contrast 0.063 < 0.18; near delta 0.018 < 0.02; near seen 0.090 < 0.65
main_D_dry              0.161     -        0.22  0.036  0.85          0.15  0.026  0.53  PASS
main_D_wet              0.221  0.10        0.09  0.021  0.19          0.06  0.013  0.07  FAIL  near contrast 0.087 < 0.18; near seen 0.187 < 0.65; middle contrast 0.063 < 0.12
main_E_dry              0.139     -        0.19  0.024  0.69          0.13  0.018  0.42  PASS
main_E_wet              0.531  0.10        0.03  0.010  0.09          0.02  0.007  0.01  FAIL  near contrast 0.031 < 0.18; near delta 0.010 < 0.02; near seen 0.085 < 0.65
main_E_heavy            0.595  0.34        0.03  0.008  0.06          0.02  0.008  0.02  FAIL  near contrast 0.028 < 0.18; near delta 0.008 < 0.02; near seen 0.059 < 0.65
close_A_dry             0.114     -        0.33  0.038  0.93          0.28  0.033  0.91  PASS
close_A_wet             0.312  0.04        0.08  0.016  0.32          0.05  0.013  0.07  FAIL  near contrast 0.082 < 0.25; near delta 0.016 < 0.03; near seen 0.320 < 0.7
close_A_heavy           0.333  0.15        0.07  0.011  0.26          0.04  0.011  0.05  FAIL  near contrast 0.071 < 0.25; near delta 0.011 < 0.03; near seen 0.255 < 0.7
close_C_wet             0.345  0.04        0.09  0.018  0.35          0.05  0.014  0.09  FAIL  near contrast 0.093 < 0.25; near delta 0.018 < 0.03; near seen 0.355 < 0.7
close_D_wet             0.327  0.04        0.11  0.023  0.41          0.06  0.018  0.11  FAIL  near contrast 0.107 < 0.25; near delta 0.023 < 0.03; near seen 0.411 < 0.7
close_E_wet             0.406  0.04        0.01 -0.002  0.27          0.03  0.009  0.07  FAIL  near contrast 0.007 < 0.25; near delta -0.002 < 0.03; near seen 0.265 < 0.7
lockout_B_dry           0.267     -        0.19  0.039  0.66          0.09  0.034  0.16  PASS
lockout_B_wet           0.381  0.09        0.07  0.017  0.19          0.08  0.027  0.15  FAIL  near contrast 0.068 < 0.15; near delta 0.017 < 0.02; near seen 0.187 < 0.5
lockout_B_heavy         0.473  0.46        0.04  0.011  0.11          0.06  0.023  0.08  FAIL  near contrast 0.038 < 0.15; near delta 0.011 < 0.02; near seen 0.110 < 0.5
lockout_C_wet           0.174  0.09        0.10  0.016  0.26          0.06  0.010  0.09  FAIL  near contrast 0.103 < 0.15; near delta 0.016 < 0.02; near seen 0.264 < 0.5
lockout_D_wet           0.175  0.09        0.12  0.021  0.33          0.07  0.014  0.12  FAIL  near contrast 0.123 < 0.15; near seen 0.334 < 0.5; middle delta 0.014 < 0.015
lockout_E_wet           0.551  0.09        0.06  0.015  0.20          0.05  0.018  0.12  FAIL  near contrast 0.057 < 0.15; near delta 0.015 < 0.02; near seen 0.203 < 0.5

missing pictures: none
RESULT: 16 picture(s) fail, 0 missing
```

**The road with the joint picture "mild1"** (colour x0.85 in the joints, roughness 0.9, specular x0.65, coat x0.55, the "closed" joint picture; section 5), the full set (`work/r07`):

```
picture                  road   pud    near c / delta / seen    middle c / delta / seen  verdict
main_A_dry              0.112     -        0.33  0.038  0.98          0.23  0.028  0.84  PASS
main_A_wet              0.200  0.10        0.46  0.111  0.97          0.29  0.064  0.70  PASS
main_A_heavy            0.198  0.34        0.37  0.073  0.96          0.25  0.055  0.65  PASS
main_C_dry              0.136     -        0.28  0.039  0.91          0.20  0.027  0.69  PASS
main_C_wet              0.328  0.10        0.42  0.177  0.97          0.29  0.133  0.72  PASS
main_D_dry              0.158     -        0.31  0.051  0.98          0.22  0.036  0.85  PASS
main_D_wet              0.226  0.10        0.36  0.097  0.89          0.18  0.045  0.55  PASS
main_E_dry              0.136     -        0.29  0.036  0.89          0.21  0.028  0.75  PASS
main_E_wet              0.517  0.10        0.56  0.277  0.97          0.35  0.203  0.84  PASS
main_E_heavy            0.576  0.34        0.52  0.275  0.97          0.37  0.237  0.88  PASS
close_A_dry             0.111     -        0.46  0.051  0.99          0.40  0.046  0.99  PASS
close_A_wet             0.286  0.04        0.60  0.185  1.00          0.52  0.203  1.00  PASS
close_A_heavy           0.305  0.15        0.59  0.182  1.00          0.50  0.201  1.00  PASS
close_C_wet             0.321  0.04        0.57  0.182  1.00          0.49  0.203  0.99  PASS
close_D_wet             0.306  0.04        0.53  0.179  1.00          0.45  0.192  0.98  PASS
close_E_wet             0.376  0.04        0.62  0.221  1.00          0.53  0.263  0.99  PASS
lockout_B_dry           0.263     -        0.28  0.058  0.87          0.14  0.055  0.34  PASS
lockout_B_wet           0.391  0.09        0.30  0.124  0.77          0.04 -0.000  0.31  FAIL  middle contrast 0.041 < 0.07; middle delta -0.000 < 0.015
lockout_B_heavy         0.486  0.46        0.18  0.131  0.59         -0.09 -0.048  0.06  FAIL  middle contrast -0.092 < 0.07; middle delta -0.048 < 0.015; middle seen 0.062 < 0.12
lockout_C_wet           0.183  0.09        0.40  0.080  0.96          0.30  0.064  0.72  PASS
lockout_D_wet           0.187  0.09        0.30  0.064  0.81          0.20  0.047  0.54  PASS
lockout_E_wet           0.555  0.09        0.34  0.171  0.78          0.11  0.064  0.47  PASS

missing pictures: none
RESULT: 2 picture(s) fail, 0 missing
```

**What fails, and why I think so.** Two pictures, both in the lockout shot's middle band: *B wet* (middle contrast 0.04 against the line's 0.07) and *B heavy* (middle contrast -0.09: there the joints are LIGHTER than the stones). The lockout camera's middle band (rows 712 to 836 of the 960) is the part of the road behind the sacks and beside the drum: the sacks' big shadow, the brazier's glare and, in heavy rain, 58 % puddle (42 % of the whole lockout road at the heavy dial) fill it, and what is left are few joint dots next to a mirror-like puddle that reflects dark houses, so a dull joint can come out lighter than a stone that mirrors something dark. By eye the joints in that band of the wet picture are visible where the road is lit (`pictures/solution_lockout_all_lights.jpg`), so I do not think the picture is wrong; I think the band is badly placed for this shot and the line is too strict for it. **I left the line as it is, and the two failures stand as an open item** (a later helper can move the lockout bands to the unoccluded road, or draw a plate without the sacks' shadow, and re-run). The near band, where the plate's foreground road is, passes in all six lockout pictures (0.18 to 0.40).

**The self-test of the one command** (`bash tools/run_lighting_test_set.sh quick work/r13 --variant joint_picture --args '{"colour_mult":0.85,"rough_to":0.9,"spec_keep":0.65,"coat_keep":0.55,"picture":"joint_cavity_closed.png"}'`, exactly as a later helper would type it). It took 1,119 seconds (18.7 minutes) and printed:

```
picture                  road   pud    near c / delta / seen    middle c / delta / seen  verdict
main_A_wet              0.201  0.10        0.47  0.111  0.98          0.30  0.065  0.72  PASS
main_A_heavy            0.198  0.34        0.38  0.074  0.97          0.26  0.057  0.68  PASS
main_C_wet              0.328  0.10        0.43  0.177  0.99          0.30  0.134  0.75  PASS
main_D_wet              0.226  0.10        0.37  0.098  0.90          0.19  0.047  0.56  PASS
main_E_wet              0.517  0.10        0.56  0.276  0.98          0.35  0.203  0.84  PASS
close_A_wet             0.286  0.04        0.60  0.186  1.00          0.52  0.204  1.00  PASS
close_E_wet             0.376  0.04        0.62  0.221  1.00          0.53  0.263  0.99  PASS
lockout_B_wet           0.391  0.09        0.31  0.126  0.78          0.04  0.001  0.32  FAIL  middle contrast 0.043 < 0.07; middle delta 0.001 < 0.015
lockout_E_wet           0.555  0.09        0.35  0.172  0.79          0.11  0.065  0.48  PASS

missing pictures: none
RESULT: 1 picture(s) fail, 0 missing
```

Its numbers agree with the full set's for the same pictures to within 0.009 in contrast (the pictures were drawn a second time, independently): so the measure is repeatable at the 0.01 level, and a change of 0.03 or more in a later helper's report is a real change.

## 7. Rubbish: what lay where in a 1926 Durham pit village street

**Plainly, first: the sources I could read are thin for exactly 1926 and exactly a front street.** I found no photograph or account that describes the rubbish of a 1926 Durham street in so many words. What I have is (a) the English north-east's colliery housing and its ash pits and middens, up to 1914; (b) captions from nearby colliery villages of about 1910 and the 1920s; (c) two 1926 Durham lockout sources that say how families got their coal; (d) a Lancashire description of ash collection in the 1930s; and (e) things I know in general and mark "my inference". The person who owns the film may know better, or may want to look at the Durham Record and Beamish photographs themselves (the Durham Record's pictures are "for personal use only").

### 7.1 What the sources say

| source (what I read) | what it says, short | for which rubbish |
|---|---|---|
| H. Diana Brown, "Colliery Cottages 1830-1915: the Great Northern Coalfield", *Archaeologia Aeliana*, 5th series (the file name says volume 23, pages 291-305: [PDF on the Archaeology Data Service](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-3433-1/dissemination/AAseries5/AA523new/archael523-000-000-PDFs/archael523-291-305-brown.pdf); I read its text layer) | Colliery rows stood 50 to 60 feet apart; "a privy shared between several houses and connected to either an ash pit or privy midden"; "although intended for dry ashes and excrement only the pits and middens filled with rain water and slop water"; in 1842 many rows had "merely dung heaps which tended to spread filth over back yards and on to paths between colliery rows"; "the quality of the external environment was so appalling that there was little point in trying to improve it"; by 1914 "the more progressive Local Authorities were improving the Back Streets" and the dung heap "had been replaced by the privy-midden and the worst of the privy-middens replaced by ash pits". | ash and cinders (from the fires, kept in ash pits and tipped); wet muck; dung (horses, pigs); it is about 1914 and earlier, so it says what the habit was, not what 1926 looked like |
| South Tyneside Libraries photograph captions, [Boldon c1910](https://southtynesidehistory.co.uk/view/619340-privy-middens) and [Whitburn c1920s](https://southtynesidehistory.co.uk/view/4157562-east-back-bowman-street-whitburn) (nearby colliery villages, Tyne and Wear, not County Durham) | Back-lane doors: lower doors to the "privy midden", upper doors to the "coal hole" where coal was delivered; before the 1930s many houses had only "a seat over a dry hole" and "scattered dry ash over" it; "the Corporation cart would come around the back lanes at night" to empty the middens through a low hatch and scatter lime; one midden often served several families. | ash everywhere in the back lane; coal delivered by hatch (coal dust and spilled coal at the wall foot); lime (white dust) |
| Bolton Revisited, ["Ashpits"](https://www.boltonrevisited.org.uk/s-ashpits.html) (Bolton, Lancashire, 1930s: not Durham) | "most households kept fires burning all day and raked them up at night" so "the ash tubs would be overflowing with ashes"; ashpit men with horse-drawn carts, then a man swept the street. | ash is the most common rubbish; the street was swept after collection |
| Tom Brown, "An excellent personal account of the 1926 miners' lockout in County Durham" (Birtley, written 1963, posted by the Kate Sharpley Library: [libcom.org](https://libcom.org/book/export/html/63512)) | Waste heaps "like young mountains"; families got coal by "searching the waste heaps" and, later, "prospecting for coal in the fields like gold diggers"; the heap is "loose stone"; a fir wood "was completely felled and sawn up"; "a rent strike was automatic" in company houses; schoolchildren had free breakfasts. | coal dust, slack, small coals, stone chips carried home and spilled; wood chips and bark; fewer bought goods |
| The Durham Record, [Byers Green, "strikers digging coal", 1926](https://dre.durham.gov.uk/Image/ByKeyword/Miners%27%20costume/DRE9872) (caption only; I could not look at the image) | "Striking miners dig coal for domestic use during the 1926 strike." | the same |
| The film's own notes (`project-notes`, `experiments/`) | The film is the lockout of May 1926; "a sooty street"; the drum is an oil drum used for a fire; the older lockout painting had "a soot-and-ash ring round the drum" that the wet painting lost; the lockout shot has the drum, the handcart, coal sacks, a slack heap, a pail, two dustbins, a ladder and the notice. | where the story props stand |
| Litter history (University of Exeter, ["In defence of litter"](https://blogs.exeter.ac.uk/ceah/?p=45): I could only see a search summary, the page itself would not load) | Litter as a worry is an early 20th century idea; popular concern after 1918 and the Anti-Litter Leagues of the 1920s; "littering" as we mean it (packaging) is later. | in 1926 the rubbish of a poor street is mostly ash, coal dust, mud, horse droppings, food scraps and paper, not packaging |

### 7.2 What I infer for the film's street (my reasoning, to be checked)

* **Ash, cinders and coal dust are the main rubbish, and in a lockout more of it is coal than ash.** Normally the "free coal" was delivered; in the lockout there was none, so families fetched it from heaps and outcrops in sacks and prams. That drops coal dust and slack along the way, in the gutters, at doorsteps and round the cart and sacks. Fires were smaller (less ash from the grate) but a street fire in a drum gives ash, half-burnt wood and cinders all round it.
* **Mud and wet muck gather in the gutter**, where the road's rain runs; a dry week leaves a grey crust, a wet one a black paste.
* **Wet straw and horse droppings** (the road still had horses: coal carts, milk, the rag-and-bone man's pony); straw also comes from packing crates and stable sweepings. Wet straw lies in short pale-brown strokes against the kerb.
* **Paper**, sodden into the ground: newspaper, grocery and fish-shop wrapping, a torn handbill. **Never readable print** (house rule), so only grey-brown scraps with, at most, a few dark lines.
* **Leaves.** The lockout began in May (the film says May 1926): few leaves, old brown ones lodged in corners and under rain pipes, a few fresh green ones from the hedges. I kept them small and few.
* **Broken bits:** a sherd of crockery, a bit of coal-tar-black slate, a stick, a rusty nail head. Few.
* **Nothing modern:** no plastic, no tins with printed labels, no cigarette packets with lettering (a bare crumpled packet shape could be made; I did not).

### 7.3 Where rubbish gathers in the street (the rules the mask follows)

Each rule is a physical reason that I believe holds for a straight terraced street; the sources above support the ash, the coal-hole and the back-lane parts, not the other parts.

| place | why | strength in my mask |
|---|---|---|
| the **gutter** (the channel stones) and the road's outer 0.5 m | rain and sweeping push everything down the camber into it; mud settles in the bottom | highest dirt, and mud in the very bottom |
| the **foot of the kerb**, pavement side | things dropped from the pavement and swept off it | medium |
| the **foot of the house walls** along the pavement, about 0.7 m wide, strongest at the wall | wind and sweeping push things against the wall; rain splashes mud up | high |
| **doorsteps** | ash tipped out, boots bringing mud, coal spilled where it is carried in | high, patch about 1 m long |
| the foot of each **rain pipe** | water carries grit, leaves and mud down and leaves them | high, with mud |
| the foot of each **gas lamp post** | things stop against a post | medium |
| round the **fire drum** (lockout shot only) | ash, cinders, burnt wood, soot | highest, about 0.8 m round it |
| the **coal slack heap**, the **dustbins** against the wall, the **coal sacks**, the **handcart** (lockout shot only) | spills: slack from the heap, ash and scraps from bins, coal dust from sacks, straw and bits from the cart | strong round their feet |
| every household's stretch | each cottage is a little dirtier or cleaner than its neighbour | a random factor of 0.6 to 1.3 for each 4.5 m of street |
| patches | nothing is a clean stripe | smooth noise of about 1.6 m scale |

### 7.4 How people make rubbish masks and litter in Blender today (research)

Again from searches; I say what I could read and what I only saw summarised.

| way | what I found | did I test it | my reading |
|---|---|---|---|
| **a mask picture from the street's plan** (a flat picture of where things lie, read by world position) | not a named technique in what I found; it is how the wetness layer's own bake works (one picture of the whole street, `tools/06_bake_maps_and_export.py`) | **Yes** (section 7.5) | the mask is a plain picture, so the person can paint it, the same picture can drive the muck layer, the scattered pieces and the glb's second texture coordinates |
| **masks from what the wetness layer already knows** | the layer has the gutter (the road's `Lowness`: 0 on the crown, 1 at the gutter), the pavement's kerb side, and the wall foot (`Wall Band`, measured from the cottage floor) | **No**, I used the plan picture instead | they sit inside the materials, so they cannot drive scattered pieces, nor be painted by hand, nor know doorsteps, rain pipes or props; but for a quick gutter-and-wall-foot dirt on ANY street they are free: plug `Lowness` and the wall band into a dirt colour |
| **distance to walls with Geometry Nodes** (the Geometry Proximity node) | the manual: it finds "the closest location on the target geometry" and gives its "Distance"; "the Map Range node is often helpful to use with the distance output to create a falloff with a maximum distance" ([manual](https://docs.blender.org/manual/en/4.2/modeling/geometry_nodes/geometry/sample/geometry_proximity.html)). Used on the ground's points with the walls as target it gives "near a wall" for any street | **No** | the right choice for a street that has no plan file; it needs a check that it ignores wall faces above head height |
| **ambient occlusion, bevel and pointiness nodes** for corners and edges | BlenderNation 2019 ([article](https://www.blendernation.com/2019/02/10/better-edge-and-cavity-masking-with-cycles/)): pointiness was the best procedural edge detector, the Bevel node later better, the AO node "much more convenient than baking"; a bug report says the AO node is close to unusable on bevelled models ([bug 90134](https://developer.blender.org/T90134)); a shader seller says Bevel and Pointiness only work in Cycles ([listing](https://blendermarket.com/products/principled-bsdf-wear-material), Blender 2.9 to 3.2, not checked for 5.2) | **No** | in the plate renderer (EEVEE) these would be screen-dependent and come and go with the camera; a world-position picture does not |
| **a painted muck layer in the ground material** (procedural dust, cinders, mud, driven by a mask) | everywhere; no single source | **Yes** | cheap; reads as a darker, duller strip; the first thing that makes the gutter look used |
| **small pieces scattered with Geometry Nodes** (Distribute Points on Faces, then Instance on Points) | the manual's "Scatter on Surface" page ([manual](https://docs.blender.org/manual/sr/latest/modeling/geometry_nodes/generate/scatter_on_surface.html), seen in a search summary): density per square metre or a fixed number, a **Distribution Mask** (near 1 scatter, near 0 none), a Selection; Poisson disk keeps the points apart; the points then take instances of a collection. Paid scatter packs exist ("Trash Scatter", "Scattercraft": not used) | **Yes** | the pieces are real small objects, so they catch the light and cast a shadow: they read as litter even when the muck layer is faint |
| **decals** (flat pictures of a stain laid on the ground) | common in games; no Blender source read | **No** | would suit the paper and leaf shapes at plate size; extra pictures to make |

### 7.5 The prototype: what I built, what it cost, what it looked like

**What it is** (`tools/b10_rubbish_plan_mask.py` makes the mask; `tools/b11_rubbish_prototype.py` has `add_muck()` and `build_pieces()` / `build_scatter()`; a first try, not a tool):

* **The mask** (section 7.3, `pictures/rubbish_plan_mask_lockout.jpg`): 450 x 4200 dots (2 cm), three channels. One for the street alone and one with the lockout shot's props. Each takes about a second to make.
* **The muck layer**, on the road, the pavements, the gutter and the kerb stones: the mask's red channel darkens the colour, puts cinder-coloured grit speckles (about 5 mm) on top, makes the surface duller (roughness toward 0.95, specular x0.45 to 1, coat x0.3 to 1) and adds a faint bump from the grit; the blue channel adds brown mud (roughness 0.4 again: wet mud shines a little). It chains after the joint picture: the code takes whatever feeds the Principled BSDF, so wetness, then joints, then rubbish.
* **The pieces:** eleven small objects built from simple shapes (cinder lumps, clinker, two coals, torn paper, sodden paper, a dead leaf, straw, a crock sherd, a stick; 1 to 10 cm), with plain materials (cinder grey-black, coal black, paper grey-brown, leaf brown, straw yellow-brown, china white, stick brown); **nothing printed on any of them**. Geometry Nodes places them: Distribute Points on Faces (Poisson disk, no two nearer than 6 cm) over the road, pavements, gutter and kerbs, the density being the mask's green channel times 140 (try 1) or 45 (try 2) a square metre, only up to 90 m (try 1) or 32 m (try 2) along the street; then Instance on Points with a random piece, a random turn and a random size of 0.7 to 1.5.

**What it cost** (this machine, two threads):

| | street, main camera 540 x 960, wet | close 640 x 480 | lockout shot 540 x 960 |
|---|---|---|---|
| no rubbish (joint picture only) | 74.9 s | 77.2 s | 205.1 s |
| try 1 (7,939 pieces street / 8,291 lockout, muck 1.0) | 88.8 s (with joints off: 71.8 s pieces only, 74.4 s muck only) | 89.0 s | 234.3 s |
| try 2 (1,990 / 2,180 pieces, muck 1.5) | 71.0 s | 90.8 s | 212.7 s |

So the layer costs 0 to 14 seconds on a street picture and 8 to 29 seconds on the lockout picture (+4 % in try 2, +14 % in try 1); the building of the nodes takes a fraction of a second. Memory was not measured.

**What it looks like** (`pictures/rubbish_try1_street.jpg`, `rubbish_try1_lockout.jpg`, `rubbish_try1_on_joint_picture.jpg`, `rubbish_try2_street.jpg`, `rubbish_try2_lockout.jpg`):
* **In the lockout shot it reads well** (try 2): cinders, coal bits and a few scraps lie round the drum's foot with a dark ash-and-soot stain, slack is spilled round the heap, there are scraps round the cart wheel and the sacks, and a ragged line of coal and grit lies along the right gutter and the foot of the right wall. Nothing looks modern and nothing is readable. At 540 x 960 the pieces are 1 to 6 dots wide.
* **In the street's main view it is faint:** try 1 shows dark flecks along the gutters and the wall foot; try 2 shows fewer; the muck layer's darkening is visible in the gutter and at the wall foot but easy to lose. **Both are dials** (density, amount): try 2 is the "faint" end, try 1 the "heavy" end; a good setting is between them, found by looking at a 100 % crop of a full-size plate (I did not).
* **It chains with the joint picture without trouble** (`rubbish_try1_on_joint_picture.jpg`): the joints still show beside the dirt.

**Weak spots I can see (not fixed):**
1. The mask's patches are blobby and the household factor makes seams every 4.5 m (visible in the picture of the mask): smooth the factor and use a finer noise.
2. The wall foot is dirtied only on the PAVEMENT; the walls' own foot (soot, mud splash up to 25 cm) is not done.
3. The pieces ignore wetness (dry colours; sodden paper is simply darker) and the props (a cinder could sit under a sack); I did not check for pieces inside props.
4. The straw (3 mm thick) is too thin to read at plate size; paper and leaf are the readable ones; a few larger shapes would help.
5. The muck layer has no joint awareness: dust sits in the joints and on the stones alike.
6. The rubbish is placed on the ground the camera sees: for another shot the y limit and the density need setting again.
7. The 1926 look of the colours (cinder, coal, ash, straw, paper) is my choice from section 7, not from a photograph.

## 8. The plan: first the setts, then the rubbish mask on top

**Order matters.** The rubbish dirties the ground, and a dirty gutter hides joints; so first make the joints survive every light (Part A), prove it with the test set, and only then put the rubbish over it (Part B), and prove the joints still show where there is no rubbish. Each step says what it costs, who does it and how you know it worked.

### Part A. The setts (do this first; it all happens in the street's materials)

| step | what | cost | proof it worked |
|---|---|---|---|
| **A1** | **Make the joint layer a reusable node group**, like `WETNESS`: `tools/joint_layer.py` with a node group `JOINTS` that sits after `WETNESS` on the road. Inputs: Colour, Roughness, Specular IOR Level, Coat Weight, Puddle Mask (all from `WETNESS`), the joint picture, and one dial **Joint Strength** (0 = off, 1 = mild1: colour x0.85, roughness 0.9, specular x0.65, coat x0.55, puddle clearing 0.8; every number moves with the dial). The code of `joint_picture()` in `tools/b02_lighting_and_variants.py` is the starting point (about 15 nodes). Put the joint picture (`work/joint_cavity_closed.png`, 0.6 MB) next to Poly Haven's pictures in `set_copy/polyhaven_maps/`. Add a `joints` entry to the road's line in `MATERIALS` in `apply_wetness_to_set.py`. | one helper, about 2 hours | the road looks as in `pictures/solution_main_all_lights.jpg`; with the dial at 0 it gives the round 2 road back exactly |
| **A2** | **Run the lighting test set** (`bash tools/run_lighting_test_set.sh quick OUT`, 20 minutes; then `full`, 40 minutes). Fix the dial until every picture passes. | 1 hour of waiting | the report says ALL PASS |
| **A3** | **Look, with the person.** Show `pictures/solution_main_all_lights.jpg` style sheets (dry, wet, heavy, glare). The person decides the dial (the test set only says the minimum and the harsh-grid maximum). | 15 minutes | the person says yes |
| **A4** | **The same for the pavement flags, the gutter and kerb stones** if the person wants them (they have joints too). Each needs its own joint picture from its own colour picture (`b01` and `b01b` make it; they are written for the setts' picture and need two numbers changed). **Not tested by me.** | 2 hours each | the same test set, with a mask for each |
| **A5** | **The glb.** The bake (`tools/06_bake_maps_and_export.py`) photographs the layer's outputs; it has to photograph them AFTER `JOINTS` so that the baked colour, roughness, coat and specularity maps carry the joint. **Not tested by me**; the stage mostly shows the painting, so this is insurance. | 1 hour, 10 minutes of baking | `31_compare_baked_live.py` correlation stays over 0.9 |
| **A6** | **The plate and the painter.** Draw the full-size lockout plate (1536 x 2730, the round 2 settings, 32 to 48 samples: 20 to 50 minutes) and look at a 100 % crop of the road; then, **only if the person says go (it is paid: about US$0.20 to 0.28 for one repaint with small pictures, painter test)**, repaint it, with one added sentence in the brief: "keep the thin dark lines between the setts and the flags where image 1 has them, even where the road shines". The painter kept such lines in the wet test, and the stage's brightness curve crushes dark values, so the lines must start with a real brightness difference: the pass line's delta. | 1 hour; US$0.20 to 0.28 if repainted | the 100 % crop shows the joint lines; the painting keeps them |
| **A7 (optional, only for close shots)** | **Shallow real geometry** under the joint picture: `geometry` with depth 0.008, y from 3 to 18 m (the "hybrid", section 5.3). It makes the nearest stones catch the light and cast a shadow. It costs about +2 to +3 minutes on a small picture (more for a plate: not measured) and covers a part of the road only. Not for the glb. | a few hours of helper time; plate time + a few minutes | the close view with the hybrid has near contrast 0.64; the main view, 0.40 (mild1 alone: 0.60 and 0.47): not better in the main view, so use it only if the person wants the stones to cast real shadows in a hero close-up |

**What not to do:** do not raise the relief strength or switch off Relief Flatten as the cure (section 3: it raises white ticks on stone corners, not the joints); do not make the joint colour much darker than 0.85 (the first tries, 0.30 to 0.45, were a black net); do not light the road "brighter" to show the joints (that is the veil).

### Part B. The rubbish mask, then the rubbish (do this after A2 passes)

| step | what | cost | proof it worked |
|---|---|---|---|
| **B1** | **Agree the mask picture with the person.** `work/rubbish_plan_mask.png` (the street) and `work/rubbish_plan_mask_lockout.png` (plus the lockout props) are plain pictures of the street from above (red = dirt, green = where pieces lie, blue = mud). The person can open them in any paint program and brush more or less; `tools/b10_rubbish_plan_mask.py` makes them again from `plan_street.json` and `plan_lockout.json` (from `b07_probe_street_plan.py`, which reads the doors, the wall line and the props out of the file). | 30 minutes | the person says "yes, there; no, not there" |
| **B2** | **Make the muck layer a node group** `RUBBISH` (as `add_muck()` in `tools/b11_rubbish_prototype.py`, which reads the mask by world position, adds dust, cinders, mud, takes shine off dust and puts a little back in mud) and put it AFTER `JOINTS` on the road, the flags, the gutter and the kerb. It takes whatever feeds the Principled BSDF, so layers chain: `WETNESS` then `JOINTS` then `RUBBISH`. One dial **Rubbish Amount**. | 2 to 3 hours | the main camera shows darker gutters and wall feet |
| **B3** | **The pieces.** Build the little pieces (`build_pieces()`: cinder lumps, clinker, coal, torn paper, sodden paper, a dead leaf, straw, a crock sherd, a stick; they are 1 to 10 cm), and scatter them with Geometry Nodes (`build_scatter()`: Distribute Points on Faces, Poisson disk 6 cm apart, density from the mask's green channel, Instance on Points with a random piece, turn and size). **Few and small:** the second prototype uses at most 45 a square metre, none beyond 32 m along the street, 1,990 pieces in the whole street file and 2,180 in the lockout shot file (the first try had 7,939 and 8,291, which is too many). Plate only (they are not in the glb). | 2 to 3 hours | the lockout shot shows ash and coal at the drum's foot, slack at the heap, scraps at the bins and along the gutter, nothing that looks like a modern thing, nothing readable |
| **B4** | **The wall foot.** The foot of the house walls (up to 25 cm: soot and mud splash) should be dirtied too (the walls' own materials). The prototype covers the PAVEMENT along the wall foot, not the wall itself. **Not tested.** | 1 hour | the wall foot is darker with a ragged top |
| **B5** | **Test.** Run the lighting test set again with the rubbish on. The joint measure skips dots where the dirt is above 0.3 (not done yet: add it to `b04_measure_joints.py` as a third mask: the dirt channel of the plan mask drawn through the same camera). The joints must still pass in the clean parts. Look at the lockout shot at 100 %. | 1 hour | ALL PASS, and the person likes the dirt |
| **B6** | **The painter.** Add to the brief: "keep the small rubbish (cinders, coal, paper scraps, straw) where image 1 has it; do not add any writing to it". | with A6 | the painting keeps the litter and adds no print |

**What the person decides:** how dirty (the two dials), whether the flags and kerb joints matter (A4), and whether to pay for a repaint (A6, B6). **What I could not decide for them:** the exact look of 1926 rubbish (section 7 says what the sources cover and do not).

## 9. What I tested, what I did not, what I am unsure of, and what went wrong

**Tested (run, and looked at):** the measure and its masks; the diagnosis (14 pictures in the close view, 9 in the main view, each with one thing changed); the joint picture (8 settings), the real geometry (3 kinds), the hybrid, the texture filter; the whole lighting test set on the road as it is and on the road with the joint picture mild1, in the street file and in the film's lockout shot file; the rubbish mask and a prototype of the muck layer and of the scattered pieces (two tries), with and without the joint picture; the test set's own one-command script (section 6.2) on the quick set (the one-command script ran from start to end on the quick set in 1,119 seconds (18.7 minutes): it drew 9 pictures and 4 puddle masks, measured them and printed 8 PASS and 1 FAIL (the lockout B wet picture, the same failure as in the full set); its numbers agree with the full set's to within 0.009 in contrast (an independent second drawing of the same pictures; section 6.4)).

**Not tested:**
* **The painter** on any of these pictures (paid; asked nobody). Whether it keeps the joints and the rubbish is unknown; the painter test (`painter_test/`) says it kept thin dark joint lines and the wet shine in its one try.
* **The film's stage and the glb** with the joint picture or the rubbish. The stage shows the painting on its own road; the glb's maps would need the joint layer in the bake (A5).
* **Pavement flags, gutter and kerb stones, the walls' mortar lines.** The same method should work; each needs its own picture.
* **The full-size plate** (1536 x 2730): I drew 1080 x 1920 once (section 5.3) and 1280 x 960 of the close view.
* **Cycles.** All pictures are EEVEE.
* **Other puddle layouts** (the seed) and **other roads**.
* **Parallax nodes and add-ons**, **Cycles adaptive subdivision**, **modelled stones**, **Line Art or Freestyle outlines**.
* **Rubbish on the walls, in the lockout shot's props' contact shadows, in motion.**
* **The geometry route with the camera moving.**

**Unsure:**
* **My joint mask comes from the colour picture, and the joint picture is made from the same mask.** So the measure is friendly to the joint picture: it knows exactly where the joints are. This is not cheating (the joints are real, and the picture is what the road would have), but a different road picture with different joints would need its own mask and its own check by eye.
* **The pass line is mine**, chosen by looking at about 60 pictures (section 6.3). It is a first line.
* **Light C is artificial** (house shadows off); **light E is invented** (a strong low light at the street's far end); I chose their strengths so that the dry road is about as bright as in A. The film may never light the street like C or E; they are there to find where the joints break.
* **16 samples** leave grain on the wet road (section 2 of the recipe: 0.008 at 48 samples); the measure averages over thousands of dots so the grain hardly moves it, but I did not measure that.
* **The puddle share** is calibrated for the main camera; the lockout camera sees much more puddle (42 % of the road at the heavy dial in the recipe's table), which is why section 6 leaves puddle dots out.
* **The sources for 1926 rubbish are thin** (section 7).

**What went wrong (all of it, in order):**
1. **My first joint mask came from the height picture and was broken** (patchy joints: the picture shows the joint only 0.05 lower than the stone). I found it by looking at the check sheet; the second mask comes from the colour picture.
2. **Light E first stood under the road** (z 1.8 while the street rises 4 degrees: the road is at 4.7 m there), so it lit nothing; moved to z 5.9. **Light C first was six times too bright** (strength 6, then 1.0).
3. **The lockout baseline was measured against the street's mask by mistake** (both cameras were called "main", so the mask file was reused); the numbers came out as nonsense (contrast 0.00), I noticed because the number of joint dots was identical to the street's. I made the lockout camera's own mask and measured those pictures again from their JPEGs.
4. **The real-geometry modifier crashed the first run** (I used a shader node type that does not exist in a geometry node tree). I lost one run's worth of time and fixed it.
5. **The first joint pictures were far too strong** (black ragged net, contrast 0.85 to 0.96) and the second try (soft1 to soft3) was still twice the dry road's. It took four rounds to reach mild1.
6. **My first texture filter test did nothing** (I gave the setting the wrong name; the log said so) and had to be run again.
7. **The first run of the rubbish prototype stopped at once** (a missing folder in Python's path); fixed.
8. **The first measure of the road lumped puddle and non-puddle dots together**, and the lockout in heavy rain "failed" because 42 % of its road is a puddle; I added the puddle mask and left those dots out (section 6), and I report both ways.
9. **The disk was tight** (1.4 GB free against a 1.2 GB floor) all through; I kept pictures as JPEG, deleted my PNGs after measuring, and stopped runs from starting below 1.25 GB.

## 10. Files

Everything is under `relief_and_rubbish/study/` (about 35 MB; the film project was not touched).

* **This note**: `10 Research - sett relief and rubbish for the street.md`. **Pictures**: `pictures/` (JPEG sheets: the diagnosis, the baseline in every light, the solutions, the rubbish).
* **The one command for the test set**: `tools/run_lighting_test_set.sh` (calls `tools/b09_lighting_test_set.py` for the lists, `tools/b03_render_jobs.py` for the drawing, `tools/b05_measure_folder.py` and `tools/b04_measure_joints.py` for the measuring). `tools/b02_lighting_and_variants.py` holds the five lightings and every variant of the road (the diagnosis changes, the joint picture, the geometry, the puddle mask view).
* **Making the pictures**: `tools/b01_make_joint_mask.py` (the joint masks from the colour picture), `tools/b01b_make_soft_cavity.py` (the soft and the "closed" joint pictures), `work/joint_cavity_closed.png` (the recommended joint picture, 0.6 MB), `work/joint_cores.png` (the measuring mask picture), `work/joint_height.png` (the sharp groove picture for geometry).
* **The rubbish**: `tools/b07_probe_street_plan.py` (reads doors, wall line, lamps, props out of a street file), `tools/b10_rubbish_plan_mask.py` (draws the mask), `tools/b11_rubbish_prototype.py` (the muck layer and the scattered pieces), `work/rubbish_plan_mask.png` and `work/rubbish_plan_mask_lockout.png` (the masks), `work/plan_street.json` and `work/plan_lockout.json` (the plan).
* **The runs**: job lists `work/jobs/*.json`; `tools/b06*_make_*jobs*.py` write them; `tools/run_study_chain_*.sh` are the chains of Blender runs in the order they were done; logs in `work/logs/`; measurement files `work/r01` (baseline and diagnosis) to `work/r13` (the self-test), each with `measurements.json`; the pictures themselves are JPEGs there.
* **The note's own builder**: `tools/b13_write_note.py` with `tools/b12b_tables.py` and the text parts in `work/note_text/`.
* **Downloaded** (CC0, only to measure): `work/polyhaven_download/` (the 2k ambient occlusion and height pictures of square_cobblestone).
