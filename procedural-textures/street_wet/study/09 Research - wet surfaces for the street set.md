# 09 Research - wet surfaces for the street set

What this file is: the study that comes before building a "wet" look for the pit village street (the street view test, log 29 of the project story). It says how the
street is built, how it reaches the film, how people make wet surfaces, what I tested, and then a BUILD PLAN for one reusable "wetness layer" that can sit on any
material. Written for a person who is not a programmer. Every picture in it was made by a test I ran; where I did not test something, the text says so.
Nothing in the film project's repository was changed: I only read it. All my files are in this folder (`street_wet/study/`).

Words used (one word for each thing, explained once here):
* **set**: the 3D street built in Blender. **plate**: the one picture drawn from the set's main camera, which the painter repaints. **painter**: the image model (Flux)
  that repaints the plate. **painting**: what the painter returns. **stage**: the film program (three.js) that shines the painting back onto the set and films it.
* **glb**: the single file that carries the set from Blender to the stage.
* **picture**: a photograph-like colour image. **map**: a flat grey or coloured image that holds a number for every dot instead of a colour (a roughness map, a normal map).
* **roughness**: how blurry a surface's reflections are. 0 is a mirror, 1 is chalk. Example: wet glass is near 0.05, dry brick near 0.9.
* **specular**: how strongly a surface reflects light that hits it head-on (the "shine"). A **specularity map** is a map of that strength for every dot.
* **clear coat**: a thin clear layer lying on top of a surface, like varnish on a table or a film of water on a stone. It reflects on its own, whatever is under it.
* **normal map**: a map that tells the lighting which way each tiny patch of the surface faces, so a flat picture looks bumpy. **height map**: how high each dot is.
* **node group**: a small packaged recipe made of Blender's node boxes, which can be dropped into any material. The **wetness layer** is such a group.
* **Cycles**: Blender's slow, exact renderer (it follows light rays, so mirrors really mirror). **EEVEE**: Blender's fast renderer, which the plates are drawn with.
  **ray tracing** (in EEVEE): a setting that makes it follow rays too, so mirrors and puddles can reflect things.
* **porosity**: how much a material soaks water up (brick and sandstone soak a lot, glazed tile and iron do not).

---

## 1. The short answer (read this if you read nothing else)

1. **The street's main view is mostly road and sky.** From the main camera the cobbled road fills **33 %** of the frame and the sky **30 %**. Walls (brick and rubble
   stone) are 16 %, pavements, kerbs and gutter stones 5 %, dressed stone (sills, steps) 5 %, metal 7 %, roofs only **1 %**. (Picture 01.) So wetness has to be
   right on the road first, then pavements and walls. Roofs and the colliery yard hardly matter for this view.
2. **Today nothing can look wet**: every material has one fixed roughness (the road 0.75, walls 0.85), the colour pictures are dry photographs, and the plate is drawn
   with EEVEE with ray tracing **off**, so a shiny road would only reflect the flat dark blue of the world, not the windows or lamps (tested, picture 06). The painter is also told, in words, to make a "matte painted finish" and
   "never add puddles or reflections".
3. **Where a "specularity map" matters, and where it does not.** As the stage is today, the wet look reaches the film in one way only: **the plate** (drawn in Blender) carries it to the painter,
   and the painter's painting is what the stage shows. The stage shows the painting "at its painted brightness" and it turns the glb's materials into plain matte ones
   (it throws away roughness, specular and clear coat). So the maps matter most for the **plate**, where Blender uses them live. Baking them into the glb is useful
   insurance and for anything the painting does not cover, but it does not by itself change the film.
4. **What makes a surface look wet, in order of how much it matters (tested, picture 04):** (a) making it smoother (lower roughness) - by far the biggest;
   (b) a thin water film on top (clear coat plus a little more specular), which brings the broad lamp reflections; (c) puddles in the low spots that go flat and mirror
   the sky and lamps; (d) darker, richer colour - real but small on its own at dusk. A specularity map alone (without lower roughness) would not look wet.
5. **A draft wetness layer works.** I built a first draft node group and put it on the road, pavements, kerbs, walls, stone and roofs of the real street, with Poly Haven's own
   roughness and height pictures added. It made the street look wet in both Cycles and EEVEE-with-ray-tracing (pictures 03, 06, 07). Puddles, wet bands at wall bottoms
   and rain streaks are in the draft.
6. **Which materials get what.** All the rain-touched materials get the wetness layer on top of their photo textures (road, pavement, kerb, gutter, brick, rubble stone,
   dressed stone, roof). **Only one replacement is worth considering: the road setts**, as a second step after the first wet plate has been repainted
   (section 6). Slate roofs, brick and mud keep their photos for this view because they cannot change what the camera sees.
7. **Three things need the person's decision before the wet street can be filmed**: the painter's brief must stop saying "matte" and "never add puddles or reflections"
   (a paid test: about 10 US cents a painting; the log says five Flux repaints cost about 50 US cents); the plate must be drawn with ray tracing on (about 40 minutes a plate at full size, see section 5); and a painted reflection stays
   stuck on the road when the camera moves (section 3, last part).

---

## 2. How the street is built (build_street.py)

**A concrete example first.** The road you see in the middle of the frame is ONE object called `street_setts`: a flat grid of 16 squares across and 84 along, 1,344 faces,
cambered (8 cm higher in the middle than at the gutters) and rising 4 degrees uphill. It wears ONE photograph, Poly Haven's `square_cobblestone`, repeated every 2.0 metres,
multiplied by a grey tint (0.62, 0.62, 0.64). Its roughness is one number, 0.75. That is all the road has: no roughness map, no height map, no second layer.
(Pictures 01 and 02.)

**The parts** (all by script, units are metres, Blender z is up, the glb is y-up):
* the carriageway (above); two dished **channels** (gutters) of stone blocks beside the kerbs; **kerbs** made of separate jointed stones about 0.9 m long; two narrow **pavements**
  of flagstones with a 3 cm fall towards the kerb;
* 28 two-storey **cottages** in rows (8 then 6, either side), red brick on the left and rubble sandstone on the right, each with a slate roof, ridge tiles, chimney stack and pots,
  door, steps, sash windows with stone sills and lintels, fascia board, cast-iron gutter and downpipe. Cottages of the same kind share one mesh (linked copies), so a wall
  looks the same on every cottage unless the material itself varies by position;
* five gas lamps, and at the top of the street the colliery (headframe, two winding wheels, engine house, chimney, spoil heap, moor) and a sky dome with a dusk picture.

**Materials, texture sizes and tile sizes** (`tile_metres` is how many metres one copy of the picture covers; colour pictures are JPEG, normal maps are always 1024 dots):

| material | picture (Poly Haven, free CC0) | colour dots | metres per copy | dots per metre | roughness | normal strength | what wears it |
|---|---|---|---|---|---|---|---|
| street_setts | square_cobblestone | 2048 | 2.0 | 1024 | 0.75 | 1.4 | the road (1 object) |
| channel_stones | large_sandstone_blocks | 1024 | 1.5 | 683 | 0.7 | 1 | the two gutters |
| kerb_stone | large_sandstone_blocks | 1024 | 3.0 | 341 | 0.85 | 1 | the kerbs |
| pavement_flags | large_grey_tiles | 1024 | 3.0 | 341 | 0.85 | 1 | the pavements |
| cottage_brick | red_brick | 2048 | 1.4 | 1463 | 0.85 | 1 | left-hand walls (30 objects) |
| cottage_stone | stone_brick_wall_001 | 2048 | 2.5 | 819 | 0.85 | 1 | right-hand walls (30 objects) |
| colliery_brick | castle_brick_02_red | 1024 | 1.5 | 683 | 0.85 | 1 | engine house, chimney |
| dressed_stone / dark_dressed_stone | rock_surface | 1024 | 2.0 | 512 | 0.9 | 1 | sills, lintels, steps, plinth (64 and 29 objects) |
| roof_slate | roof_slates_03 | 2048 | 3.0 | 683 | 0.5 | 1.2 | roofs (31 objects) |
| colliery_yard, moor | muddy_tracks | 1024 | 2.25 and 12 | 455 and 85 | 0.8 and 0.95 | 1 | ground at the top |
| spoil_heap | rocks_ground_02 | 1024 | 2.0 | 512 | 0.75 | 1 | the heap |
| cast_iron, headframe_steel, wheel_iron, brass, wire_rope | rusty_metal_02 | 1024 | 0.3 to 1.0 | - | 0.3 to 0.6 | 0.3 to 1 | lamps, gutters, headframe (metallic 0.5 to 0.9) |
| paint_* (6 colours), ridge_clay, chimney pots, plaster_dark, interior_dark | grey_plaster_02 | 1024 | 0.8 to 1.0 | - | 0.45 to 1.0 | 0.4 | doors, frames, pots |
| boarded_green / boarded_blue / fascia_board | plank pictures | 1024 | 1.0 to 1.6 | - | 0.7 | 1 | doors, fascia |
| window_lit_glow_0..2, window_dark_0..2, lamp_glass_glow, engine_window_glow | made by the script (lace curtains etc.) | 384 x 640 | once per part | - | 0.08 to 0.15 | - | windows (the lit ones glow: emission 1.6 to 8) |
| sky_dome_glow | dusk_sky.jpg | 1024 x 512 | - | - | - | - | the dome (glows) |

Everything in that table is also what the glb carries: **41 materials, 38 pictures, 135 meshes**, the file is 16.9 MB. In the glb the only glTF extension used is
`KHR_materials_emissive_strength` (for the glowing windows and lamps). The road's roughness is exported as the plain number 0.75. The two shot files that add props
(`lockout-set.glb`, `notice-corner-set.glb`) also use `KHR_materials_specular` (only to switch the shine OFF on the brazier coals, soot, shut doors and lantern flame) and
`KHR_materials_transmission` (the lantern glass); about 3 in 10 of their materials (22 of 76 and 25 of 82, all props) carry a roughness picture from Poly Haven.

**What the main camera sees** (a quick false-colour picture: every material painted one flat colour, then the dots counted; I ran it for three cameras):
the main camera of `street.blend` (1.6 m up, 6.5 degrees looking up, 40 degrees lens), the lockout plate camera (the 12-second test clip) and the notice-corner plate camera.
Share of the frame, in per cent (picture 01):

| kind of surface | main camera | lockout plate | notice-corner plate |
|---|---|---|---|
| **road setts** | **33.0** | 24.2 | 21.0 |
| sky dome | 30.4 | 33.7 | 19.4 |
| walls: brick, rubble stone, plaster | 16.4 | 13.4 | 17.4 |
| metal: lamp posts, gutters, headframe, wheels | 6.7 | 5.9 | 5.9 |
| pavement flags, kerbs, gutter stones | 4.8 | 2.9 | **19.8** |
| dressed stone (sills, steps, lintels) | 4.8 | 4.6 | 4.7 |
| ground at the top (yard, heap, moor) | 1.4 | 1.1 | 0.4 |
| windows, doors, paint, fascia | 1.5 | 1.9 | 1.3 |
| roofs (slate, ridge, pots) | 1.0 | 1.2 | 1.5 |
| props and signs (all other materials) | 0 | 11.2 | 8.6 |

How to read it: in the main view, one material (the setts) is a third of the picture; the walls are a sixth; roofs are a hundredth. In the notice-corner shot the camera is higher
and wider (64 degree lens), so the pavement becomes a fifth of the frame. **The most important wet surfaces are therefore the road, then the pavement flags and gutter,
then the walls.**

![False colour: what fills the frame](pictures/01%20Street%20false%20colour%20-%20what%20fills%20the%20frame.jpg)

(Failure, recorded: my first false-colour run counted wrongly. The street file keeps an exposure of +0.6, which multiplied every material number, and Blender adds a trace of
noise to 8-bit pictures, which turned some dots into a neighbouring number. I discarded those numbers, switched both off and counted again outside Blender.)

![The photo textures the street wears](pictures/02%20The%20photo%20textures%20the%20street%20wears.jpg)

What the pictures show, which matters for wetness: the cobblestone is a regular grid of small square setts (roughly 11 cm, counted from the picture) with straight joints; its normal map is very faint, so
there is little relief to flatten in a puddle. The sandstone block picture used for kerbs and gutters has a stripe of moulding at its top and bottom. The yard picture is plain brown
with ruts. Poly Haven also offers a **roughness map and a height ("displacement") map for each of these**; the street never downloaded them. I did (1 k size, about 2 MB, nothing in the
repository was touched). Their real values: the cobblestone is rough **0.90 on average** (so the street's 0.75 was already a guess), brick 0.92, and the cobblestone height map runs 0.2 (joints)
to 0.9 (sett tops), which is just what a "wet joints, dry tops" rule needs.

---

## 3. How the set is exported and shown

**Step by step, with what each step actually uses:**

1. **Blender builds the set** (`build_street.py`, then `assemble_lockout.py` or `assemble_notice_corner.py` add props and lights). The scene has 473 objects, 41 materials and
   33 lights: two "sun" lights (a cool dusk skylight 0.35 and a warm afterglow 0.25), five gas lamps (260 W points), 24 lit-window lights (45 W) and two engine-house lights.
   The world is one flat dark blue. The sky dome is a mesh that glows.
2. **The plate is drawn** by `set_dressing.render()`: **EEVEE** (the fast renderer), 48 samples, 1536 x 2730 dots, "AgX" colour with a +0.6 exposure, **ray tracing OFF**
   (`use_raytracing = False` is saved in street.blend, lockout.blend and notice-corner.blend; I checked all three). With ray tracing off, EEVEE can show a lamp's bright highlight on a glossy surface, but it cannot show a mirror image of a house or
   of a lit window in a puddle. (I drew the wet draft both ways, picture 06: with ray tracing off the puddles are pale flat patches of the world's blue with nothing mirrored in them;
   with it on they mirror the lit windows and the lamp posts.) The plate uses the .blend, not the glb.
3. **The painter repaints the plate.** The brief (`notice-corner-paintings.json`) says, in words I quote: "matte painted finish", "Nothing should look like a 3D render or a photograph
   any more", "The road, pavement and walls are cool blue-grey dusk", and in the list of things never to add: "**puddles or reflections**". It is shown a style picture too.
   The history behind it: in chapter 1 a painted wet ground got no reflections of the 3D coins and notes, the person objected, and the street was "repainted dry" (Decisions, item 25).
4. **The glb is written** (`bpy.ops.export_scene.gltf`, Blender 5.2.2's exporter). It keeps, for each material: the base colour picture and a colour factor (the tint), the normal map, the
   roughness and metal numbers, emission, and the two UV sets it was given. The exporter (I read its source) can also write `KHR_materials_clearcoat` (from "Coat Weight" and "Coat Roughness",
   pictures allowed), `KHR_materials_specular` (from "Specular IOR Level" with one limit, see below), `KHR_materials_ior`, and it packs a roughness picture into the green channel of one
   image. The street.glb uses none of these today.

   What the glb keeps today, one line each: **base colour** yes (the picture and the tint as a colour factor); **normal map** yes (1024 dots, with its strength); **metallic-roughness** only as two
   plain numbers per material (no picture) in street.glb, and a picture for about 3 in 10 prop materials in the shot files; **KHR_materials_specular** only `specularFactor 0` on four prop
   materials of the notice corner and one of the lockout; **clear coat** none; **emissive** yes (colour picture as the emissive picture, with `KHR_materials_emissive_strength` 1.6 to 8);
   **transmission** the lantern glass; **IOR** none.
5. **The stage loads the glb and shines the painting on it** (`projected-set.js`, three.js version 0.169). For every dot of every surface the projector saw, the stage shows the painting
   **"at its painted brightness: no stage lamp, shadow or haze is added to it"** (file comment, and the last line of the shader). Only surfaces the projector never saw (backs,
   ground behind a house, what a camera move uncovers) show the glb's own material, **and by default (`matte: true`) the stage first swaps every realistic material for a plain matte
   (Lambert) copy that keeps only the colour picture, normal map, glow and baked occlusion**. The code of that swap (`matteCopy`) does not copy roughness, metalness, specular, clear
   coat or any reflection setting. Those unseen surfaces are then darkened to 0.75 and tinted toward the painting's average colour.
   The stage's reflections come from one shared "RoomEnvironment" (a soft grey room) at strength 0.2 to 0.3, not from a dusk sky with lamps.
   A material that has a clear coat also switches off the stage's "skip the lamps where the painting covers fully" shortcut (a comment in the file), so clear-coated surfaces would
   make filming slower; the file itself says realistic materials cost about twice a matte one in the software renderer, and the project's own measurement for a mirror-wet ground
   was +0.375 seconds a frame (`26 Research - fully 3D scenes and cheap effects.md`).

**What follows from this, plainly:**
* The wetness the audience sees will be **what the painter paints**. The painter sees only the plate. So the plate must carry the wet look in a form a painter keeps: dark glossy
  road, lamp pools, mirrored windows in puddles. That means ray tracing on, a changed brief, and a test.
* The glb's roughness, specular and clear coat maps would be thrown away by the stage as it is today. They only matter if the stage is changed (matte off for the road and pavements,
  plus a dusk reflection environment), or for unseen surfaces. This makes the baked maps **cheap insurance, not the main route**.
* **A painted reflection is stuck to the road.** When the camera moves, a real reflection of a lamp slides along the water; a painted one stays where it was painted. My own
  estimate (a calculation, not a test): lamp 4 m high, puddle 12 m away, camera 1.9 m up and moving 1.4 m forward (the lockout clip's move): the true reflection shifts about **0.9 m**
  along the road against the painted one. That is a gentle error for a puddle 1 to 2 m long, and larger for puddles close to the camera. Keep puddles away from the near road in
  moving shots, or keep the moves small, or add the stage's own mirror ground later.

---

## 4. How people make wet surfaces today (Blender 4.x / 5.x and three.js / glTF)

**A concrete example first.** A dry grey cobblestone and the same cobblestone after rain, photographed on the same street at the same time of day: the wet one is **darker**, its
colours are **a little richer**, the stones' tops and sides pick up **soft streaks of the lamps** (it has become smoother), and in the low places there are **flat dark patches
that mirror the houses and the sky**. Every method below makes one of those four things.

| # | what it does | how in Blender 4.x / 5.x | how in three.js / glTF | tested here? | sources |
|---|---|---|---|---|---|
| 1 | **Darker, richer colour.** Water in the pores and a film on top trap light, so the colour is darker, most for mid-brightness, rough, porous materials; shiny non-porous ones barely change. Game rule (Lagarde): multiply the colour by 1 (no pores) down to 0.2 (full pores) times the wetness. Wet asphalt in a driving simulator: colour x0.1 to 0.3. A model's ratio: a dry albedo of 0.12 becomes about 0.08. | Mix node (Multiply) by a grey from porosity and wetness, then Hue/Saturation node a little above 1. | The colour map and `baseColorFactor` carry it; in the glb it has to be baked into the base colour (no layers). | **Yes, picture 04 step 2.** By itself it is nearly invisible at dusk (the road was already dark). | [Lagarde 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/), [fxguide Part C](https://www.fxguide.com/?p=43362), [Lekner and Dorf 1988](https://www.wgtn.ac.nz/scps/staff/pdf/darkerwhenwet.pdf) |
| 2 | **Lower roughness.** Water fills the pores, so the surface behaves as if it were polished. Game rule: blend the gloss toward smooth by half the wetness. Standing water: near 0.02 to 0.1. | Roughness socket: Mix or Map Range from the wet mask; photo roughness maps (Poly Haven offers them) as the dry value. | `roughnessFactor` or the green channel of `metallicRoughnessTexture`. | **Yes, picture 04 step 3: the biggest single change.** | [Lagarde 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/), [Cinema 4D layered wetness](https://novedge.com/blogs/design-news/cinema-4d-tip-layered-wetness-workflow-for-realistic-puddles-in-cinema-4d-and-redshift) (seen as a search summary only) |
| 3 | **A clear water film: more specular, a coat.** Water has index 1.33, reflects about 2 % head-on and nearly everything at grazing angles (the Fresnel effect), so wet roads show long bright lamp streaks. | Principled BSDF "Coat" (Weight, Roughness 0.02 to 0.2, **IOR 1.33**) and "Specular IOR Level" (0.5 is normal, 1.0 doubles the head-on reflection, 0 removes it). | `MeshPhysicalMaterial.clearcoat` (its own docs name "wet surfaces"); glTF `KHR_materials_clearcoat`, `clearcoatTexture` (red) and `clearcoatRoughnessTexture` (green). glTF's `KHR_materials_specular` picture (its alpha channel) multiplies a factor of at most 1, so **per dot it can only keep or LOWER the normal 4 % reflection**; a boost above normal exists only as one constant for the whole material (the exporter writes it into `specularColorFactor` when a constant level is above 0.5; I read this in its code, I did not test a boost together with a picture). So in glTF the wet film is the clear coat, and a specularity map is for turning reflection DOWN on dry spots. | **Yes, picture 04 step 4** (broad lamp pools appear). The coat's own separate normal map: not tested. | [Blender 5.2 manual, Principled BSDF](https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html), [three.js MeshPhysicalMaterial](https://threejs.org/docs/pages/MeshPhysicalMaterial.html), [KHR_materials_specular](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_materials_specular/README.md), Blender exporter source (read) |
| 4 | **Puddles in the low spots.** Water collects first in holes, cracks and low curves. A "low-ness" field (from the height map, blurred noise, or a distance to the gutter) goes through a threshold; the edge is soft. Slope limit: only flat enough surfaces hold water. | Noise or height as a Math / Map Range threshold; add-ons do the same (RealPuddle Pro takes colour, roughness, normal and height in, with displacement scale and midlevel). | The same mask baked into roughness, clear coat and normal maps. | **Yes** (pictures 03, 05: coverage 0.8 % / 5.9 % / 45 % of the road at amounts 0.3 / 0.55 / 0.8). | [Lagarde 2012 "Observe rainy world"](https://seblagarde.wordpress.com/2012/12/10/observe-rainy-world/), [RealPuddle Pro docs](https://superhivemarket.com/products/realpuddle-pro/docs) (read), a Blender Artists thread [Cycles puddle material](https://blenderartists.org/t/cycles-puddle-material-shader-now-with-example/544715) (link only, not read) |
| 5 | **Puddles go flat** (the relief of the stones disappears under thick water). Blend the normal map toward the plain surface normal as the water gets deeper; keep a little ripple on thin films. Colour a little darker, roughness near 0. | Mix (Vector) between the normal map and the Geometry normal by the puddle mask; or lower Bump strength inside it. | Baked into the normal map (flat inside puddles). | **Yes** (pictures 04 step 5, 07). | [Lagarde 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/) (as the water gets deeper the normal moves step by step from the normal map to the flat surface normal, so thick puddles give a clean mirror), an Unreal answer [How to make puddle water transparent?](https://answers.unrealengine.com/questions/498324/view.html) (search summary only: albedo x0.5, roughness near 0, normal flat) |
| 6 | **Puddles mirror the sky and the lamps.** Needs something to reflect. | **Cycles**: automatic (rays). **EEVEE**: turn on **ray tracing** (screen trace method; it can only mirror what is on screen, then falls back to light probes). Lamp points show only as highlights, lit glass and windows mirror. | Needs an environment map (three.js `scene.environment`, a PMREM) or a planar mirror (`Reflector`), because glTF has no reflection data. The stage's environment is a grey room today. | **Yes in Cycles and EEVEE** (pictures 03, 06, 07). In three.js: not tested. | [Blender 5.2 manual, ray tracing](https://docs.blender.org/manual/en/latest/render/eevee/render_settings/raytracing.html) (seen as a search summary), the project's own mirror-wet ground measurement |
| 7 | **Wet bands at wall bottoms and streaks under sills and eaves.** A mask of "height above the ground" with a wavering top edge (splash and rising damp); long vertical streaks from vertical-stretched noise, starting at a source (a sill, a gutter) and fading downward; roughness and colour change together. | Math on world height minus the ground height (the street rises: `z - y * 0.0699`); Noise stretched along z for streaks. | Baked into the wall's colour, roughness and clear-coat maps (the walls' meshes are shared, so a bake is the same on every cottage). | **Partly.** Band, general damp and untied streaks: yes (picture 07). Streaks that start under each sill and eave: **not tested** (planned). | [ComfyUI "Surface Streak Mask"](https://comfy.icu/node/x1SurfaceStreakMask) and a [Tripo blog on streaks](https://www.tripo3d.ai/blog/explore/hd-model-water-streaks-and-drip-marks-realism) (both search summaries only; they describe the logic, not Blender settings) |
| 8 | **Wet setts with dry tops.** The raised tops of stones drain into the joints and dry first; the joints and dips stay dark and shiny; puddles dry last. | The height map goes through a smoothstep: high = drier, scaled down as wetness rises. | Baked. | **Yes, included in every wet picture**, but I did not switch it off alone to see its own effect, so I cannot say how much it adds. It is my own reasoning, backed by Lagarde's remark that water collects first in low spots and that puddles dry slower than the rest. | [Lagarde 2012](https://seblagarde.wordpress.com/2012/12/10/observe-rainy-world/), [Lagarde 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/) |
| 9 | **One "wetness" dial that wets and dries.** Do not store wet and dry separately: change the dry values toward the wet ones with one number, so rain can start and stop. Specular fades faster than the darkening when drying. | A group input; keyframe it. | Two glbs, or a baked pack per state. | The dial itself: yes (the draft group has Wetness and Puddles inputs). Drying over time: not needed for a still plate, not tested. | [Lagarde 3b](https://seblagarde.wordpress.com/2013/04/14/water-drop-3b-physically-based-wet-surfaces/) |
| 10 | **Take the dry roughness and height from the photograph's own maps.** Free from Poly Haven. | Image nodes (Non-Color) beside the colour picture. | Same files go into the glb. | **Yes** (used for road, pavement, brick and rubble stone). | [Poly Haven API](https://api.polyhaven.com/files/square_cobblestone) (read: lists Rough, Displacement, AO for all of them) |

Honest note on sources: items marked "search summary only" I did not open (two sites refused my fetch with errors 403 and 429); I only saw the search tool's summary. Lagarde's
articles (3a, 3b and "Observe rainy world"), the fxguide piece, the three.js and RealPuddle pages I fetched, but through a tool that returns a summary of the page rather than its raw text, so the
numbers I quote from them (0.2, 0.1 to 0.3, 5 to 10, 0.68) are as that summary gave them. The Poly Haven API data, the Blender exporter's code and three.js's loader code I read directly.

**Why no single method is enough.** In picture 04 the second step (darker, richer colour alone) looks almost like the dry road; step 3 (smoother) is what the eye reads as wet; step 4
adds the lamps' broad pools; step 5 adds mirror puddles. So a "specularity map" on its own, without lowering the roughness underneath it, would not make the road look wet.

---

## 5. What I tested (pictures, numbers, failures)

I built a first draft of the wetness layer (`tools/wetness_group.py`, about 300 lines, plain Blender nodes: no add-on, no Voronoi, no ambient-occlusion node) and put it on the street's real
materials through `tools/03_wet_street_test.py`. Nothing was saved back into the repository. The draft is a test, not the final tool; the final one is the plan in section 7.

**What the draft does** (inputs: dry colour, roughness, height, normal, a wetness amount, a puddle amount, a seed, plus how porous the material is, how low the spot is, how high
the wall band reaches and so on; outputs: wet colour, roughness, specular level, clear-coat strength and roughness, the changed normal and height, and three masks):
* it works out what the surface faces from its true normal: **ground-like** (flat enough to hold water), **wall-like** (upright), **roof-like** (between);
* puddles: a "low-ness" field made of a slow wobble across the ground, the caller's own "how low is this spot" (for the road: low beside the gutter, high on the crown) and the height
  map's low parts; a soft threshold turns it into puddles; the amount slides the threshold;
* ground gets a patchy damp film; **the high parts of the relief stay drier**;
* walls get a wet band at the foot (its top edge wavering), a general damp, and vertical rain streaks;
* the wet look: colour x (1 down to 0.2 by porosity) and a little more colour; roughness slides to a "wet roughness" and to 0.03 in puddles; specular level 0.5 to 0.75; clear coat
  up to 1 in puddles (water, index 1.33); the normal slides toward the plain surface normal inside puddles.

**Test 1 - main camera, dry and wet in Cycles** (picture 03; 540 x 960, 32 samples, wetness 0.85, puddles 0.6). Road brightness (average of the dots that are road) went from
0.188 to 0.370 (x1.97) because the wet road mirrors the bright sky and lamps (its brightest 1 % rose from 0.24 to 0.77). Pavement, kerb and gutter x1.53, walls x1.45, dressed stone x1.46, roofs x1.02.
Puddles covered **9.6 %** of the road (13 % with thin water). *Reading:* the whole frame brightens, so the plate will need its exposure watched; and walls at wet roughness 0.3 are too glossy
(use about 0.45 for walls).

![Main camera: dry, wet and the masks](pictures/03%20Main%20camera%20-%20dry%2C%20wet%20and%20the%20masks%20%28Cycles%29.jpg)

**Test 2 - what each part adds** (picture 04; a low close view of the setts, Cycles, 480 x 360, 48 samples): dry; darker and richer colour only; plus smoother; plus the water film
(specular and clear coat); plus puddles. *Reading:* step 2 is nearly invisible; step 3 makes it wet; step 4 brings the lamp pools; step 5 adds flat mirror patches. This is the picture
to show anyone who asks why lowering roughness matters more than a specularity map.

![Close look at the setts, dry then wet in four steps](pictures/04%20Close%20look%20at%20the%20setts%20-%20dry%20then%20wet%20in%20four%20steps.jpg)

**Test 3 - puddle amounts** (picture 05; 1-light-sample mask renders, two seconds each): the amount is steep. 0.3 gives 0.8 % of the road, 0.55 gives 5.9 %, 0.8 gives 45 % (a flood).
The first draft was worse: 1.5 % at 0.55 and the puddles lay in two straight stripes along the gutters. I added contrast to the "low-ness" wobble and lessened the gutter's weight; the patches
are now irregular but still gather beside the gutters, as water would. For the real tool the amount should be mapped so that the dial moves coverage smoothly (target: 3, 8, 15, 30 %).

![Puddle masks at four amounts](pictures/05%20Puddle%20masks%20at%20four%20amounts.jpg)

**Test 4 - wall foot, pavement, kerb and puddles from a low view** (picture 07; Cycles): wet flags and kerb, a darker wet band and streaks at the wall's foot, puddles mirroring the sky
and a lit window. Problems seen in it: puddles that reflect only dark houses read as **black holes** (in picture 03 the ones on the left pavement, bottom left; in this picture the nearest ones are dark mirror patches too); and the pavement got too many puddles
(21 % of the pavement dots) because its default "low-ness" is the same as the road's.

![Wall foot, kerb and puddles](pictures/07%20Wall%20foot%2C%20kerb%20and%20puddles%20-%20dry%20then%20wet.jpg)

**Test 5 - the plate renderer, EEVEE** (picture 06; 540 x 960): EEVEE runs on this machine only with a virtual screen (`xvfb-run`). Three pictures: (1) dry, as the plate is made today (ray
tracing off): 106 s at 16 samples; (2) the wet draft with ray tracing **off**: 117 s; (3) the wet draft with ray tracing **on**: 158 s at 16 samples and **398 s at 64 samples**.
*Reading:* with ray tracing off the road is glossy but the puddles are pale flat patches that show only the world's flat blue; with it on they are dark mirrors with the lit window and the lamp
posts in them. So **the plate must be drawn with ray tracing on** for puddles to read as water. Problems: (1) the pavement flags look **gritty** (glints from the photo's fine normal map under a
smooth surface). It is the texture, not the sampling or the ray tracing: my noise measure on the pavement was 0.0100 dry, 0.0165 wet with ray tracing off, 0.0196 on at 16 samples and 0.0172 on at 64
samples. A fix is needed (calmer normal when wet, a higher wet roughness for flags; not yet tried). (2) Turning ray tracing on also changes the whole image's ambient light (the engine house is
brighter), so a dry picture for comparison must be drawn the same way. (3) Scaled up, one full-size plate (1536 x 2730, 48 samples) will take roughly 40 minutes on this busy machine (my
estimate from the 64-sample time and the pixel count; not measured).

![EEVEE, the plate renderer, dry then wet](pictures/06%20EEVEE%20-%20the%20plate%20renderer%2C%20dry%20then%20wet.jpg)

**Test 6 - baking the maps for the glb** (picture 08; the road from y = 8 m to y = 40 m, one dot per centimetre). I "photographed" the draft's outputs from straight above (the same trick
`lib/bake_harness.py` uses for texture recipes): wet colour, roughness, clear coat, clear-coat roughness, normal and puddle mask, 440 x 3200 dots each, 20 seconds for all six. I gave the road a
second set of texture coordinates (across the road and along it, once), built a plain material that wears only those pictures, and exported the road alone. Results:
* **The exporter wrote exactly what was planned**: `KHR_materials_clearcoat` with a clear-coat picture and a clear-coat roughness picture **packed into one image** (red and green channels),
  a base-colour picture, a normal map, and the roughness picture in the green channel of the metal-roughness slot; every picture uses the second texture coordinates; the mesh carries both
  sets. No `KHR_materials_specular` was written, because I left the specular level at the normal 0.5. The road alone was 6.5 MB.
* **Live against baked, inside the baked stretch**: average brightness ratio 0.95, average difference 0.032 (on a 0 to 1 scale), correlation 0.96. By eye the lamp pools and the puddles sit in
  the same places; the baked joints look slightly softer (the sharpness measure did not show it: 0.0118 baked, 0.0100 live, so I do not trust that measure here).
* **A mistake of mine, recorded**: the bottom third of the baked picture is smeared stripes, because the close camera looks at road from 6 m but I baked from 8 m. That part was never baked,
  and I excluded it from the numbers (the unbaked band: ratio 0.78, correlation 0.56, which means nothing).
* One dot per centimetre cannot hold the 1 cm joints between setts crisply: the normal map is the part that suffers. The plan therefore keeps the photo's own tiled normal map (first texture
  coordinates) and uses the baked pictures only for roughness, clear coat and colour; glTF lets each picture choose its own texture coordinates.

![Baking test: live against baked road](pictures/08%20Baking%20test%20-%20live%20against%20baked%20road.jpg)

**Timing and machine, for planning**: Cycles dry 207 s and wet 304 to 380 s at 540 x 960 and 32 samples, small close views 140 to 275 s each at 48 samples (a fixed set-up cost of about 2 minutes
per picture), mask renders 2 s, a bake of six maps 20 s. Three other helpers were using the machine, which slowed everything; read these as "slow day" times.

**Failures and slips, all recorded**: the false-colour exposure and noise (section 2); first puddle settings far too small and in stripes (test 3); no wall wetness at first (the walls' average wet
mask was 0.05, so walls hardly changed; I added a "wall wetness" input and it became 0.31); the first EEVEE run started and ended instantly because the `time` program is not installed (my command,
not Blender); the bake window mistake (test 6); black-hole puddles and over-glossy walls (tests 1 and 4); web pages that refused (Lagarde 3a at one address returned 404, I found the right address from his
series page; two other sites returned 403 and 429).

**What I did NOT test**: a painter repaint of a wet plate (it costs money and needs the person's go-ahead); the stage with a wet glb (matte off, an environment map, a mirror ground); a full-size plate;
the lockout and notice-corner shots with their props; streaks that start under each sill and eave; the sett layout made from our recipes; our slate or mud recipes under the wetness layer; how visible the
2 m repeat of the cobblestone picture is along the street; whether Flux keeps a lamp pool and a mirror puddle when told to; animation (rain starting and stopping).

---

## 6. Which materials get the wetness layer, which could be replaced, which keep their photos

Rule used: **what matters is what the camera sees, and the painter repaints it**. The painter flattens the fine detail of a photograph into brushwork; what it needs from the plate is
readable structure (rows of setts, courses of brick) and the cues of wetness (dark glossy road, lamp pools, mirrored windows). So a better texture recipe does not change the painting;
the wetness layer does.

| material | share of main frame | wetness layer? | replace with our recipe? | settings to start from |
|---|---|---|---|---|
| street_setts (road) | 33 % (24 % and 21 % in the shots) | **Yes, first** | **Second step only** (see below) | Poly Haven roughness and height; porosity 0.6; wet roughness 0.3; puddles by gutter and dips; dry tops 0.5 |
| pavement_flags | 2.4 % (20 % in the notice corner) | **Yes** | No | Poly Haven roughness and height; porosity 0.55; wet roughness 0.4 to 0.45 (gritty at 0.3); fewer puddles (low-ness 0.2) |
| kerb_stone, channel_stones | 1.2 and 1.25 % | **Yes** (the gutter should always be wet: wetness 1, low-ness 1) | No | porosity 0.5; wet roughness 0.3 |
| cottage_brick, cottage_stone (walls) | 5.7 and 5.6 % (16 % with colliery brick, plaster) | **Yes**: general damp 0.35, foot band 0.45 m, streaks | **No** (a brick recipe exists but cannot change the wet look; photo brick is what the painter sees) | porosity 0.7 brick, 0.6 stone; wet roughness about 0.45 (not 0.3) |
| colliery_brick | 5 % (the engine house, far away) | Yes, same as the walls | No | as walls |
| dressed_stone, dark_dressed_stone | 4.4 % | **Yes**: sills and steps are flat tops that hold water; streaks below each sill | No | porosity 0.5 |
| roof_slate | **1.0 %** (1.2 and 1.5 % in the shots) | Yes, cheap (the same group; a sheen) | **No, not for this street**: the slate layers cannot change what 1 % of the frame shows | porosity 0.3; wet roughness 0.25 |
| colliery_yard, moor, spoil_heap | 1.4 % together (0.4 % in the notice corner) | Only if a shot looks at them | **Later, if a shot looks at the yard**: our mud recipe, whose ruts and clods are exactly where yard puddles go | - |
| cast iron, headframe steel, wheels, brass (metals) | 6.7 % | Not at first. Later with porosity 0 (metals do not darken) for a thin film | No | - |
| paints, doors, windows, lamp glass, sky dome | 1.5 % + sky 30 % | No (glass is already glossy; the lit windows glow and are mirrored in the road by themselves) | No | - |
| props (barrel, sacks, cart, pail, board) | 11 % and 8.6 % in the two shots | Later: the same function can wrap any prop material (wood porosity 0.4, hessian 0.8, iron 0) | No | - |

**The one real decision: the road setts.** The photo is a regular grid of equal squares in straight rows, repeated every 2 m along 84 m of street. The tool shelf could make something better
(setts laid in staggered courses, each with a domed top and a sunk joint, so the wet joints, dry tops and puddle fill come from a true height), but the project's own earlier cobble trial
(the brick recipe re-coloured) gave "straight courses in running bond, rounded rectangles of one shape" and a height that was "physically wrong for setts" (the joints came out brighter
than the stones), and the stone tools make rounded irregular stones (cobbles), not rectangular setts. A proper sett layout is the slate layout run with sett settings plus a dome-and-joint height. My advice: **do the first wet plate with the photo
(cheap, done in a few runs)**, send it to the painter, and look. **Build the sett layout only if** the painted result shows the grid as too regular or the 2 m repeat, or if puddles do
not read on the photo's height. If you want it anyway, it is about 4 Blender runs (bake the tile, check it, make a 2 x 2 area, compare plates) and the wetness layer sits on it unchanged.

---

## 7. THE BUILD PLAN - one wetness layer that sits on any material

### 7.1 What the layer is

One Blender node group named WETNESS, written by a Python file (`wetness_layer.py`, beside the other tools; it must not be put into `lib/` by accident). It takes the dry look of any
material and gives back the wet look. The draft I tested is its first version; the build turns the draft into this.

**Inputs** (name: what it is: default)
* **Colour** (dry colour), **Roughness** (dry roughness: a number or a map), **Height** (0 to 1, 0.5 is flat; from a map or a recipe), **Normal** (the dry normal): plugged from whatever the
  material already has (a photo, or one of our recipe groups, whose outputs are already called Colour, Roughness, Height).
* **Wetness** 0 to 1 (0.8): how wet everything is. **Puddles** 0 to 1 (0.5): how much standing water. **Seed**: any number that moves the puddles and streaks.
* **Porosity** 0 to 1 (0.6): how much the colour darkens. **Wet Roughness** (0.3 ground; 0.45 walls): the roughness of a soaked surface. **Puddle Roughness** (0.03).
* **Position** and **Surface Up** (new: the draft reads them inside; the build makes them inputs): for the set, plug in the world position and the geometry normal; for baking a flat texture
  tile, plug in the tile coordinates and the up direction (0, 0, 1) with a seamless noise so the tile repeats without a seam. This is what lets one layer serve both the set and the recipes.
* **Lowness** 0 to 1 (0.5): how low the spot is, given by the caller (the road: 1 at the gutter, 0 on the crown; the pavement: 0.2; a recipe tile: from its own height).
* **Dry Tops** (0.5), **Water Level** (0.65 on the height scale), **Ground Slope** (0.0699, the street's rise per metre) and **Ground Offset** (0.13 for walls above the pavement),
  **Wall Band** (0.45 m), **Wall Wetness** (0.35), **Streaks** (0.5), and **Drip Mask** (new: a 0-to-1 field of "water is running down from here", see rule 5 below).
* **Effect strengths** for colour, roughness, specular, coat and normal (each 0 to 1): switches for tests and for turning one part off.

**Rules inside** (all tested in the draft except the ones marked new)
1. Work out the surface's kind from its up direction: ground-like, wall-like, roof-like.
2. **Puddles in low spots**: low-ness = 50 % slow wobble + 25 % caller's low-ness + 25 % the height map's low parts; a soft threshold; only on ground-like surfaces. Map the dial so the road coverage
   is about 3 %, 8 %, 15 %, 30 % at 0.3, 0.5, 0.65, 0.8 (the draft's steep curve gave 0.8 %, 5.9 %, 45 % at 0.3, 0.55, 0.8).
3. **Dry tops of setts**: the high part of the height map keeps less of the wet, scaled down as the wetness rises toward soaked.
4. **Wet band at wall bottoms**: height above the local ground (world height minus ground slope times distance along the street, minus the offset), a top edge made to waver by noise.
5. **Streaks under sills and eaves** (new): a small sub-group that makes a vertical streak from a source rectangle (centre, half-width, height) down a given length with ragged edges; the
   cottage wall material chains one per opening using the same layout numbers as the build script (`FACADE_LAYOUTS`, `GROUND_WINDOW`, `UPPER_WINDOW`) in the wall's own coordinates, so every
   cottage shares them; the eaves use one wide source with gaps. Its result goes in as the Drip Mask. The draft's general vertical streaks stay as a weak background.
6. **The wet look**: colour x (porosity-weighted darkening) with a little more colour; roughness toward the wet roughness (puddles to 0.03); specular level 0.5 to 0.75; clear coat (index 1.33) up
   to 1 in puddles; normal slides to the plain normal inside puddles and a little on wet ground (**this is also the cure for the pavement's gritty glints**); a black-hole guard for
   puddles (water colour only 20 % darker, and a faint sky lift) (new).

**Outputs**: Colour, Roughness, Specular IOR Level, Coat Weight, Coat Roughness, Normal, Height, and three masks (Wet, Puddle, Streak). The material then plugs them into its Principled BSDF and
sets Coat IOR 1.33.

### 7.2 The maps to bake for the glb (roughness and a specularity map at least)

Per baked surface, one small pack (picture 08 shows the six I baked):

| map | what it holds | glTF slot it goes to (verified in the test) | resolution | notes |
|---|---|---|---|---|
| wet colour | the dry colour darkened and enriched where wet | base colour | 1 cm a dot near the camera (0 to 40 m), 2 cm to 80 m | JPEG is enough |
| **roughness** | 0.9 dry, 0.3 film, 0.03 puddle | green channel of the metal-roughness picture | same | grey, 8-bit |
| **clear coat** (the "wetness shine") | 0 dry up to 1 in puddles | `clearcoatTexture` (red) | same | this is what carries the wet film in glTF |
| clear-coat roughness | 0.2 film, 0.03 puddle | `clearcoatRoughnessTexture` (green) | same | packs with the clear coat into ONE image (the exporter did this) |
| **specularity map** | reflection strength; per dot only LOWER than normal is possible in glTF (a constant boost for the whole material is possible) | `specularTexture` (alpha) | same | use it to turn reflection down on dry sett tops; the wet shine itself is the clear coat. I did not bake this one; run 14 tests a constant boost together with the map |
| normal | puddles flattened | `normalTexture` | keep the photo's tiled normal map on the first coordinates | a 1 cm baked normal loses the joints (test 6) |
| puddle mask, wet mask | for checking and compositing | not exported | same | grey |

Where they go: the road and pavements (flat: photographed from above in tiles, test 6), the gutter and kerbs, and the four wall meshes (baked on a second unwrap with Blender's Bake, since
the cottages share them). One glb per state ("street-dry.glb" is the one that exists; a new "street-wet.glb"), so the stage can choose. Expect the wet glb to be well under 60 MB with JPEG maps.

### 7.3 Order of work, about 20 Blender runs (each under 9 minutes; one at a time, 2 threads; the long plate in the background)

| run | what | what to look at afterwards |
|---|---|---|
| **A. The layer** | | |
| 1 | Finish `wetness_layer.py` (Position and Surface Up as inputs, effect switches); a test scene of five cards: photo brick, photo cobble, our slate tile, our mud tile, plain painted wood, each at wetness 0, 0.5, 1 | every card goes darker and smoother; the group needs no change per material |
| 2 | Fast mask sweep (1 sample, 2 s a picture) on the three cameras: puddle dial against coverage; wall and pavement targets | a table: coverage at 0.3, 0.5, 0.65, 0.8 meets the targets |
| 3 | The sill and eave streak sub-group and its masks on one cottage | streaks start under each sill; none float |
| 4 | Colour calibration in flat white light (no reflections): wet/dry ratio per material against the targets (brick, setts, flags about 0.7 to 0.8; slate about 0.85) | a table |
| 5 | Gloss calibration: wet roughness 0.25 to 0.55 on road, pavement, brick; the gritty pavement fix | pictures; choose the values |
| 6 | Puddle look: water colour, a faint sky lift, no black holes | close pictures of three variants |
| **B. On the street** | | |
| 7 | `apply_wetness_to_set.py`: opens a COPY of street.blend, swaps the layer onto the materials in section 6 (adding Poly Haven's roughness and height pictures as new files), saves a copy | masks and a small EEVEE-with-ray-tracing picture |
| 8 | the same on the lockout copy (props included, metals left alone) | same |
| 9 | the same on the notice-corner copy | same |
| 10 | **Plate**: one shot, dry and wet, EEVEE with ray tracing at the full size (about 40 minutes each; background) | the two plates side by side; exposure; no sparkle |
| 11 | (optional) the same wet plate in Cycles as the reference | does EEVEE keep the mirror puddles? |
| **C. Maps for the glb** | | |
| 12 | Photograph the flat surfaces from above in tiles: road (0 to 80 m), pavements, gutter, kerbs, yard | the packs of 7.2; 1 cm to 4 cm a dot |
| 13 | Bake the four wall meshes on a second unwrap | maps per wall mesh |
| 14 | Build `street-wet.glb` (maps only materials), export, inspect with `paper-film/blender/inspect_glb.py` | extensions, picture count, size |
| 15 | Live against baked on the three cameras (the numbers of test 6: difference under 0.04, correlation over 0.9 inside the baked area) | a table |
| **D. Checks** | | |
| 16 | Main camera dry and wet in Cycles, 64 samples | the reference sheet |
| 17 | Close looks: setts, wall foot, a lamp pool (three cameras in one run) | pictures |
| 18 | The numbers run: coverage, brightness ratios, noise, for the three shots | one table |
| 19 | The "props removed" wet plate for the behind painting (the stage needs both) | the pair |
| 20 | A clean re-run of everything from the scripts in a new folder | it all re-runs |

Not Blender, in parallel: **(P1)** change the painter's brief (see 7.4) and try it on the wet plate once (about 10 US cents; the person decides); **(P2)** a stage test page in a copy of the
kit that loads the wet glb with `matte: false` for the road and pavements and a dusk environment, and films stills at the plate camera to compare with Blender (if the stage is to show the
maps at all).

### 7.4 How to check it

* **In Blender** (runs 16 to 18): the main camera dry and wet from the same lights; a close look at the setts; the wall foot; the lamp pool. Numbers: road brightness ratio (the draft gave
  1.97; aim for about 1.3 to 1.6 so the plate is not blown out), puddle coverage of the road (aim 8 to 15 %), puddles on the pavement (aim under 5 %), noise on the pavement, black-hole count
  (puddle dots that are almost black), and the wet-colour ratio per material.
* **Painter brief** (needs the person's go-ahead): remove "matte painted finish" for the road and "puddles or reflections" from the never-add list, and say what to keep: "The road, pavement and walls are
  wet after rain: keep the dark glossy sheen on the setts, the long warm reflections of the gas lamps and lit windows on the road, and the flat dark puddles beside the gutters, exactly where they
  are in image 1; do not add puddles or reflections that image 1 does not have." Then look at: did the painter keep the pools and the mirror patches in place? did it add its own?
* **In the stage**, if the maps are to count (P2): the stage's own helper `showWeights(true)` shows which dots wear the painting (orange) and which wear the glb (blue): wetness shows only on
  blue, so check how much blue there is in the plate view (very little, near the projector). Then, in the moved view, whether the unseen road looks wet and the same as the painted road.
* **For a camera move**: film the lockout clip's move with the wet painting and look at the reflections drifting (about 0.9 m by my estimate).

### 7.5 What could go wrong (and the way out)
* The painter may flatten the wet look to dry brushwork. Way out: a stronger brief; a wet style picture (earlier chapters already have painted wet streets, `04 Painting prompts.md`).
* The painter may invent puddles where the plate has none, and they will not match the 3D. Way out: the brief says "only where image 1 has them" (the third critique of the notice corner
  already asked for "no puddles" for this reason).
* Painted reflections stay stuck when the camera moves (section 3). Way out: puddles away from the near road in moving shots, or the stage's mirror ground later.
* A full plate takes about 40 minutes with ray tracing on this machine. Way out: background run; check at half size first.
* Ray tracing changes the whole picture's ambient light, so compare dry and wet plates drawn the same way and re-check the exposure.
* Pavement grit (test 5) and black-hole puddles (test 4): the fixes are in runs 5 and 6.

---

## 8. What I am unsure of
* Whether the painter will keep the wet cues. Everything in this study is about making the plate wet; I did not spend money on a repaint.
* The 40-minute plate time (an estimate from a smaller picture on a busy machine).
* How far a specularity map can go in glTF: per dot it can only lower reflection (the standard's text and the exporter agree); a whole-material boost together with a map is untested (run 14). I tested only the exporter and read three.js's loader.
* The strength of the dry-tops rule (not tested alone).
* How obvious the 2 m repeat of the cobblestone picture is along the street (not measured).
* The exact wording of Lagarde's, fxguide's, three.js's and RealPuddle's pages (I saw tool summaries, not the raw text), and the Unreal, Cinema 4D, ArtStation, ComfyUI and Tripo pages (search summaries only; two refused my fetch).

## 9. Files (all in `street_wet/study/`)
* `tools/` - `00_eevee_check.py` (does EEVEE run here), `01_material_map.py`, `01b_count_materials.py`, `01c_false_colour_picture.py` (the shares), `02_inspect_street_blend.py`, `02b_render_settings.py`,
  `wetness_group.py` (the draft layer), `03_wet_street_test.py` (dry/wet/masks/ablation/EEVEE), `04_puddle_coverage.py`, `05_bake_and_export_road.py` (the bake test).
* `pictures/` - the eight pictures used above (JPEG).
* To save disk I deleted the large baked maps and the 6.5 MB test glb after reading them; `work/baked_road/road_wet_test_glb_json.json` keeps the glb's description (its extensions, materials and pictures), and picture 08 shows the maps.
* `work/` - the renders, masks and numbers behind every claim (`work/ids/*_shares.json`, `work/group_shares.json`, `work/cycles_main_final/main_numbers_final.json`,
  `work/puddle_masks_sheet.json`, `work/baked_road/live_vs_baked.json` and `bake_report.json`), logs (`work/0*.log`), and 8 small Poly Haven maps (`work/polyhaven_maps/`, CC0).
