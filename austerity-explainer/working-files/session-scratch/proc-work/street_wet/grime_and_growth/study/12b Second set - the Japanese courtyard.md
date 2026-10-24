# 12b Second set - the Japanese courtyard

What this file is: the study that makes the weathering kit (grime, cracks, stains, weeds and moss) ready for its SECOND set, the Japanese courtyard, before any kit code is written. It says which saved courtyard scene to use, what the courtyard is made of (family by family, material by material), where a kit layer can be put into those materials (and a test that proves it), what real Japanese temple and garden courtyards look like when they age, what the courtyard's own shapes say about where shade and damp are, and what the kit has to handle so that ONE set of layers serves both this courtyard and the sooty 1926 coal-town street. It was written on 21 October 2026. It follows on from `11 Pipeline - where new layers hook into the street.md` (section 12 of that file was a 20-minute look at the courtyard; this is the real study).

What I did and did not do: I opened the courtyard's newest saved scene in Blender with nothing saved (the file's time stamp is unchanged), listed every object and material, read the build script and the add-on's code, measured the scene with rays (what the camera sees, sky openness, year-round sun), ran small test pictures here and on the rented machine, and searched the web for how real courtyards weather. I did NOT build any weathering layer (none exists yet), did not ask the painter for anything, spent nothing on paid image calls, wrote nothing in the courtyard folder, the add-on folder, the street copy, the film project or the other jobs' folders, and did not commit or push.

Words used (one word for each thing, explained once):
* **set**: a 3D scene built in Blender (the street, the courtyard). **plate**: the one picture drawn from the set's camera, which the painter repaints. **painter**: the image model (Flux 3 edit on fal). **stage**: the film's three.js program that shines the painting back on the 3D set.
* **layer**: a small packaged recipe of Blender node boxes (a "node group") dropped into a material. **Principled BSDF**: the all-purpose surface box most materials end in. **plug** (Blender says "socket"): one input of a box, such as Base Color or Roughness. **hook** (or **splice**): putting a layer into the wire between whatever feeds a plug and the plug itself. **adapter**: a small step that first turns an odd material into a Principled box so a hook can be made.
* **mask**: a grey number for every dot of a surface, 0 = nowhere, 1 = fully. **geometry reader**: the kit's own tool that measures the set's real shapes and writes masks as small flat pictures. **role**: the kind of surface (plaster wall, stone, planks, roof tile ...) that the set's settings file says an object or material is.
* **instance**: a copy of one object that Blender draws many times without storing each copy as separate faces (the courtyard roof is 688 copies of one tile). **add-on**: the person's Astra Painted Workbench, which built the roof, stones, planks, moss and pebbles. **Cycles / EEVEE**: Blender's slow exact renderer and its fast one (the film's plates are drawn with EEVEE).
* **painter dot**: one dot of the plate as the painter sees it (the painter is given the plate at about 0.4 to 0.5 of its size). **brightness**: the finished 8-bit picture's brightness from 0 (black) to 1 (white), as in the street study.
* Marks used in the research part: **[S]** = a web source says it (link given); **[M]** = my own reading or general knowledge, not found in a source I opened. **GUESS** = a starting number I have not measured.

---

## 1. The short answer

1. **The scene to use is `astra-work/out/courtyard_final.blend`** (saved 18 October 22:13). Its own picture `courtyard_final.png` is pixel for pixel the same as the project's "01 Japanese courtyard - golden hour photo.png" (difference 0 on all 3.84 million dots), so it IS the final photo's scene. The other saved files are test runs, "hide one thing" debugging and two small previews made later for the add-on version comparison. Section 2.
2. **The courtyard is a different kind of set from the street in almost every way**, and that is what the kit has to cover: wood, plaster, roof tiles and natural stone instead of brick, setts and flags; raked gravel and soft earth instead of a road; a pond instead of puddles; footfall paths instead of cart lanes; a dry, bright plate instead of a dark wet one. Section 8.
3. **Surface families and the share of the final photo each covers** (one ray per dot of a 240 x 160 grid, about 0.25 points): sky 10.5, hills 11.5 and leaf masses 11.6 (never weathered), then the weatherable ones: soft ground 15.4, raked gravel 7.4, wood 10.3 (bridge planks 6.2, hall posts and beams 3.1, veranda deck 1.0), roof tiles 5.3, plaster walls 5.1, add-on stones 9.7 (pond-edge stones 4.4, rocks 4.0, lantern, steps and others 1.3), plinth 1.8, pebbles 0.7. **About 57 % of the picture can be weathered**; the pond is another 5.9. Section 3 and the picture `25 Japanese courtyard - surface families and what the kit would treat.jpg`.
4. **How the 134 materials are built:** 68 are a Principled box with every plug a plain number (all the planks, moss and pebble tones), 14 are a Principled box with a noise-made colour or a vertex colour (ground, gravel, plaster, timber, plinth, bark, bamboo, leaves), **46 are the add-on's own shader groups with no Principled box on the surface** (43 stones, 2 ceramic roof materials, 1 timber roof deck) and 6 are glow-only. Section 4.
5. **One generic hook covers all of them, and I tested it.** A do-nothing group was put in front of every weatherable material: "wire or plain number" splice for the 75 plain ones, an **adapter** for the 46 add-on groups (it rebuilds one Principled box from the group's own Albedo, Roughness and Normal outputs), and the glow and leaf materials left alone on purpose. Result in Cycles with full floating-point pictures: **identical, largest difference 0.0 on all 153,600 dots**. A deliberate 2 % darkening through the same hook changed 114,583 dots (75 %), so the test can see a change and the hook really sits in the path of every weatherable surface. In EEVEE at 1200 x 800 the hooked picture matched the plain one to within one step of 255 on 0.8 % of dots and exactly elsewhere. It works on the roof's 688 instanced tiles. Section 4.
6. **Three things in this set break the street's habits:** (a) the roof tiles are instances, so a layer must read the surface in the shader (or work on a realised copy), not the object; (b) 43 stones have 43 separate materials, each a different copy of the same add-on group; (c) the water is one big plane under the ground, so the shore line must be found where the ground crosses the water level, not from the water object. Section 3.
7. **The add-on has already grown moss and pebbles as real geometry** (32,365 and 5,654 faces) from seven hand-placed patches, and in my test its moss does NOT follow shade (rank match +0.15 with year-round sun on land, where 0 means none): 11.2 % of its moss points are in the shadiest tenth of the land and the shadiest tenth holds 11.0 % of the land. The kit must read where that moss is and not double it. Section 6.
8. **Shade is a weak signal here and needs a second driver.** With the sun path of Kyoto (35 degrees north, north taken as +y: see the assumption in section 6), only 8.7 % of the land gets under 35 % of an open spot's year of sun; the pond's bank ring 20 %; the north faces of the walls get 0.06 of it against 0.36 to 0.48 for the other faces. So moss and algae need **shade x damp x undisturbed** (damp = near the water line, low ground, under drip lines, at wall feet), not shade alone. Section 6.
9. **Dark marks work here where they could not in the street.** In the courtyard picture plaster is 0.64 bright, gravel 0.41, add-on stones 0.37, soft ground 0.27, wood 0.31 on average (15 % of its dots under 0.13): only the **roof tiles (mean 0.14, 47 % of dots under 0.13)** sit in the zone the stage crushes. So on plaster, gravel, stone and ground dark stains read, and on the roof and the darkest timber only pale moss, lichen and silver weathering will. The kit must choose dark or pale marks from the plate's measured brightness per role, not from a typed rule. Section 7.
10. **The courtyard is coarser at painter size than the street's near ground:** with the existing camera (69 degrees wide, 3 m up) one painter dot is 6 to 21 mm at the courtyard's distances (5 to 18 m) if the painter gets a wide 1229-dot picture, and 11 to 37 mm if it gets a 691-dot-wide picture, against 1.7 to 2.9 mm across the street (3 to 9 mm along it) at 3 to 5 m. Hairline cracks are gone; moss clumps (28 cm across), stains and streaks, plank-end rot and 10 to 30 cm lichen colonies read. Section 7.
11. **EEVEE draws the courtyard** (the film's plate renderer): 1200 x 800 at 48 samples took 1.2 s on the rented card (0.6 s for the next picture), it looks like the Cycles photo with softer pond reflections and slightly warmer stones (mean difference 7.7 of 255), so the same plate pipeline can serve both sets. Section 4.
12. **What to carry over and what not.** Carry over the chain, the hook, the masks' method, the four rules (own seed, amount 0 = nothing, declared inputs only, prove independence), the painter-size rules and the moss/lichen method. **Do not carry over** coal soot as the default dirt, coal and cinder litter, cast-iron rust streaks, sett joints, kerb and gutter logic, the road crown, cart lanes, the 4 degree slope and every street name and number. Sections 8 to 10.
13. **A first draft of the courtyard's settings file** (roles, never-weather list, water, footfall paths, drip sources, light, scale, cameras, palette, measured brightness) is in `out/c1/japanese_courtyard.draft.json`. Its key names are a proposal; every number is from the scene or marked GUESS. Section 11.

---

## 2. Which saved scene, and why

All files are in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work/out/`.

| file | saved | what it is |
|---|---|---|
| **`courtyard_final.blend`** (7.99 MB) and `courtyard_final.png` | 18 Oct 22:13 (scene), 22:27 (picture) | the final scene and the 2400 x 1600 photo drawn from it at 180 samples in 13 min 21 s (`final.log`). **Chosen.** |
| `test1` to `test11`, `test10h` | 21:44 to 22:12 | first tries (first picture washed out, pond hidden, slow leaves, popcorn maple, sun blocked ...), see the project story log |
| `dbg1` to `dbg3`, `hide_*` (planks, bridge pier, lily), `hide_sheet.png` | 22:08 to 22:13 | "hide one group at a time" debugging of the white shapes beside the bridge (they were the pond's mirror image of the glowing screens) |
| `cmp_v020`, `cmp_v021` (+ fingerprints, 720 x 480 pictures) | 22:53 to 22:54 | small previews made later to compare add-on version 0.2.0 with 0.2.1 (same scene: 89 meshes, 214,689 corner points, 236,044 faces, zero different dots) |

Why `courtyard_final.blend`: (1) its own picture is identical dot for dot to the project's photo (I compared all 3,840,000 values: largest difference 0); (2) it was saved at 22:13 and the 13-minute picture ends at 22:27, so the scene is what was photographed; (3) the later `cmp_*` files are quick-preview builds for a different question (and the build script in the project folder was edited at 22:57, after the final photo, to add the fingerprint code; I did not rebuild anything). Opened headless (`blender -b --disable-autoexec`), listed only; the file's time stamp is still 22:13:47 on 18 October.

What the scene holds (my count): 88 mesh objects and 10 curve objects, 10 empties, 7 lights, 1 camera, 134 materials, 14 collections. Render settings saved in it: Cycles, 2400 x 1600, AgX "Punchy", exposure 0.5. Units are metres, z up; x is across, y runs away from the camera. The camera is at (-5.2, -5.6, 3.0), horizontal field of view 69.4 degrees, looking at (1.0, 3.9, 1.0). Lights: a golden-hour sun (energy 8, toward the sun (-0.944, -0.244, +0.223), so low and from the left), a 120 W lantern point light, four hall-glow area lights, a cool sky fill. No object has an open add-on "surface transaction" (the add-on's undo handle), and its pigment, detail and textile tools were never used (checked: `out/c1/addon_marks.json`).

---

## 3. The courtyard, family by family

Numbers are mine: object and face counts from my listing (`out/c1/survey.json`, evaluated geometry, so the add-on's modifiers are included), shares from camera rays (`out/c1/family_shares.json`), painter-dot sizes from the camera's maths for the median distance of each family (`out/c1/hits_by_object.json`). "Wide" = the painter gets a 1229-dot-wide picture (a 2730-wide landscape plate at 0.45); "narrow" = 691 dots wide (a 1536-wide plate at 0.45). The film's plates are tall (1536 x 2730), so a real courtyard plate will have its own camera and its own numbers: the kit must calculate them from the settings' camera list (section 8).

| family | objects (names in the file) | faces / size | how the material is built | share of photo | one painter dot (wide / narrow) | where a layer hooks in |
|---|---|---|---|---|---|---|
| **soft ground** (earth, moss colour, banks, pond bed) | `Astra / Courtyard receiving ground` (1 object; a hidden copy `Courtyard ground source` sits under it and must be skipped) | 7,392 faces, 22 x 21 m, height from -0.58 (pond bed) to +0.95 (hill) | `Moss and earth`: Principled with a noise colour ramp (dark brown to green) and a noise bump | 15.4 % | 8 / 14 mm across, grazing view so about 2.3 times longer along | in front of the Principled box (wire or number hook). Already carries painted moss colour: weathering must be a different tone from it |
| **add-on moss and pebbles** (real geometry) | `Astra / moss grouped bodies` (4 tone materials), `Astra / pebbles grouped bodies` (4) | 32,365 and 5,654 faces; moss clumps 0.14 m radius, 5 cm high | 8 plain Principled materials (numbers only: moss tones linear (0.035,0.075,0.022) to (0.15,0.22,0.065)) | 0.1 and 0.7 % | - | do not weather; read as a density picture so kit growth does not double them |
| **raked gravel court** | `Raked gravel court` | 31,486 faces, 8.2 x 7.8 m; rake lines and rings are real 1.6 cm relief every 17 cm | `Raked gravel`: Principled, noise grain colour (linear 0.115..0.25), a wave-pattern bump and a fine grain bump | 7.4 % | 11 / 20 mm, grazing about 3.3 times | in front of the Principled box; layers must not flatten the rake lines (15 painter dots wide at the wide setting) |
| **pond and basin water** | `Pond water` (one 8.2 x 6.2 m plane at z -0.12), `Basin water` (a 0.22 m disc) | 26 faces | `Pond water`: Principled, rough 0.06, a noise ripple bump | 5.9 % | - | **leave alone**; later its own water layer (duckweed, leaf film). The shore line comes from where the ground crosses z -0.12 |
| **veranda deck planks** | `Astra / varied planks`, `.001`, `.002` (3 runs, planks run along y) | 1,974 faces, planks about 0.26 m wide, gap 1.2 cm, bevelled | one plain Principled material per tone (21 of them), no grain in the material | 1.0 % | 9 / 16 mm | wire-or-number hook on each tone material; **grain direction has to come from the mesh** (the planks' long axis) |
| **bridge planks and landings** | `Astra / varied planks.003` to `.007` (3 segments, 2 square landings) | 3,337 faces, planks 0.15 m wide, 1.05 m long, deck top z 0.20 to 0.23 | same (34 tone materials) | 6.2 % | 8 / 14 mm | same. Wet-line and algae rules apply (the pond is right under it) |
| **posts, beams, soffit, shoji lattice** | `Hall posts`, `Hall beams`, `Eave soffit`, `Shoji bars` | 678 faces; posts 17 cm square, lattice bars 2.8 cm | `Dark timber`, `Beam timber`: Principled, noise colour stretched along the grain (very dark brown, linear 0.05 to 0.13), noise bump | 3.1 % | 15 to 16 / 26 to 29 mm | in front of the Principled box. Dark on dark: only pale marks read |
| **shoji paper and open room** | `Shoji paper`, `Open room back` | 48 faces | emission only (glow) | 2.4 % | - | **never** (glow; the street rule "skip emission above 0") |
| **plaster walls** | `Hall plaster`, `Back wall, left`, `Back wall, right`, `Right wall behind hall` | boxes of 6 faces; garden walls 0.3 m thick, 2.1 to 2.2 m tall; hall walls 2.4 m | `Plaster wall`: Principled, noise colour from linear 0.62 to 0.80 (a light cream), noise bump | 5.1 % | 17 to 21 / 30 to 37 mm; walls seen at a slant | in front of the Principled box. **Light surface: dark stains read well** |
| **wall cap tiles** | `Back wall, left cap`, `Back wall, right cap`, `Right wall behind hall cap` | 72 faces; 0.5 m wide, 0.1 m overhang on each side of the 0.3 m wall | `Wall cap tile`: Principled, plain numbers, near black (linear 0.032) | 0.5 % | - | the run-off source for the wall faces; moss and lichen on top |
| **roof tiles** | `Hall roof` (geometry nodes) and a hidden `CT / Ceramic pan prototype` | the object's own mesh has 42 faces (timber deck and ridge); the tiles are **688 instances** of one 12-face tile 0.30 x 0.66 x 0.22 m; roof 11.9 x 5.8 m, eave z 3.2, ridge z 4.68 | `CT / Ceramic painterly surface` (tiles), `CT / Ceramic ridge host-local surface`, `CT / Timber painterly surface` (deck): add-on shader groups, no Principled on the surface; tiles very dark blue-black (linear 0.013) | 5.3 % (4.5 of it hits the tile copies) | 14.5 / 26 mm | **adapter**, then the hook. Mean brightness 0.14: moss, lichen and pale stains only |
| **plain stone** | `Stone plinth`, `Lantern finial` | 18 faces; the plinth is a 10.9 x 5.6 m slab 0.6 m high | `Plinth stone`: Principled, noise colour, strong bump | 1.8 % | 14 / 25 mm | in front of the Principled box |
| **add-on stones** (43 objects) | `Stepping stone 0-7`, `Veranda step`, `Veranda step, lower`, `Pond edge stone 0-14`, `Rock 0-4`, `Gravel rock 0-2`, `Lantern base/post/gallery/firebox/cap`, `Water basin`, `Bridge pier 0-3` | 16 faces each before the add-on's modifiers (a geometry-nodes shaping, a bevel, a support plane), 61 to 72 after; typical 0.75 x 0.86 x 0.59 m, tall rocks to 1.46 x 1.0 x 1.9 m, stepping stones 0.64 x 0.59 x 0.25 m | 43 separate materials `CT / Stone painterly surface.NNN`, each a copy of the add-on group `FOUNDRY / Wet Stone` (see below) | 9.7 % (pond-edge stones 4.4, rocks 4.0, lantern 0.5, stepping stones 0.4, steps 0.3, basin and piers 0.1) | 6 to 11 / 11 to 19 mm | **adapter**, then the hook; the group's own `Wear Mask` can feed the kit's edge channel |
| **bamboo** | `Bamboo fence`, `Bamboo stalks`, `Bamboo leaves` | 6,657 faces | `Bamboo stalk` (noise), `Bamboo leaf colour` (vertex colour, see-through mix) | 0.5 % | - | leave alone in round one |
| **trees: bark** | 10 curve objects (`Maple trunk/branch`, `Pine trunk/limb`) | 410 faces | `Bark`: noise colour and strong bump | 0.4 % | - | leave alone in round one |
| **leaf masses and litter** | `Maple leaves` (75,000 faces), `Maple inner mass`, `Pine pads` (56,000), `Fallen leaves` (156), `Lily pads`, `Lotus blossoms` | 135,000 + 440 faces | vertex colour (some with a see-through Translucent mix) | 11.6 + 0.8 % | - | **never weathered** (vertex coloured, see-through) |
| **backdrop** | `Hills, far/middle/near`, `Dark plain` | 486 faces | emission haze | 11.5 % | - | never |

### Things to know about how the courtyard is built (they change how a layer must be written)

1. **The roof tiles are instances.** `Hall roof` has no faces of its own; a geometry-nodes modifier (`CT / Shared roof controls`) produces a 42-face base mesh and 688 copies of the hidden tile. A layer that looks at "the roof object's faces" sees almost nothing. Shader layers that read position and normal work on the copies (proved: the hook and the family map both reach the roof). Anything that needs real geometry (scattering moss clumps on the lower tile edges, finding the eave line for drip stains) must read the evaluated and realised roof (Blender lists every copy with its own matrix, I counted them: `out/c1/roof_instances.json`).
2. **The add-on's stone and roof materials are shader groups, not Principled boxes.** `FOUNDRY / Wet Stone` (stone, ceramic) and `FOUNDRY / Wood` (the roof's timber deck) have 14 inputs (Vector, Generated, Base, Shadow, Highlight, Seed, Scale, Variation, Roughness, Bump, Wear, Wetness, stroke length and width) and **six outputs: Shader, Albedo, Roughness, Height, Normal and Wear Mask**. Inside, one Principled box is fed exactly by Albedo, Roughness and Normal (so a Principled rebuilt from those three outputs plus the group's plain numbers is the same surface; the test proves it). The add-on's group already has a built-in wet film (`Wetness` 0.25 for stone, 0 for the roof) and an edge-wear mask made from the object's own bounding-box coordinates (`Wear` 0.12). Every stone has its own material copy carrying `ct_material_role` (stone, ceramic or timber), `ct_surface_seed`, `foundry_kind` and `ct_coordinates` as custom properties: the kit's settings can find these by that property instead of by name.
3. **The stones are low-poly** (61 to 72 faces each after the add-on's shaping). Vertex-based masks (vertex colours, vertex curvature) would be crude. The add-on gives each stone a point attribute `CT_rest` (its rest-pose coordinates) so its pigment stays attached when it moves. Masks for stones must come from the shader: world up-ness (normal z), height above where it meets the ground, and the group's own Wear Mask for edges and corners.
4. **The planks have no grain in the material.** The add-on makes tone variety with one plain Principled material per tone (7 tones per run, 56 in all); the plank edges are real bevelled geometry. There are no UV maps anywhere on the add-on's meshes. Grain direction has to come from the mesh's long axis (the add-on's own timber crack code does the same).
5. **The walls are plain boxes** (6 faces each), straight along x or y, with no turned copies or shared meshes, so wall pictures can be made in world coordinates. The garden walls have a 0.5 m cap on a 0.3 m wall (0.1 m overhang), which is the run-off source. There are no windows with sills; the openings are the shoji bays between posts.
6. **The pond is an invisible trick.** The water is one big plane just under the shore line (`WATER_Z = -0.12`); the ground hides it everywhere except the pond. So "distance to the water edge" must be made from the ground height picture and the water level, never from the water object's outline.
7. **Existing growth.** The add-on grew moss from seven hand-placed patches (front-left, hill, maple root, rocks, lantern, gravel islands, path edge) plus "contact" and "shelter" fields, and scattered pebbles on four shore patches. This is real geometry lying on the ground. The kit must treat it as "already grown here".
8. **Two hidden helper objects:** `Courtyard ground source` (the ground before the add-on rebuilt it; hidden in render) and `CT / Ceramic pan prototype` (the roof tile; hidden in render but its material is the visible tile). A layer hooks the material, but a measuring tool must skip the objects. My first camera-ray count lumped the tile prototype with "hidden things" and showed 4.4 % hidden: that was the roof, not nothing (see section 12).
9. **Cycles scene, EEVEE-able.** The scene is set for Cycles (AgX Punchy, sky texture world, sun disc off, leaf Translucent mix) but EEVEE draws it well (section 4).

---

## 4. How the materials are built, and where a layer hooks in

### 4.1 The materials (134, all counted by script: `out/c1/material_kinds.json`)

| how it is built | count | examples | what a kit hook has to do |
|---|---|---|---|
| Principled box, **every plug a plain number** | 68 | all 56 plank tones (7 tones in each of the 8 runs), 4 moss tones, 4 pebble tones, `Wall cap tile`, `Lily pad`, `Lotus blossom`, `Far hill` | make a Value or RGB box for each plug number, splice, done (no wire to find) |
| Principled box, colour and bump **made by noise nodes** (9) or **from a vertex colour** (3 + 2 with a see-through mix) | 14 | `Moss and earth`, `Raked gravel`, `Plaster wall`, `Dark timber`, `Beam timber`, `Plinth stone`, `Bamboo stalk`, `Bark`, `Pond water`; leaf and needle materials | splice into the existing wires (colour and normal are wired, the other plugs are numbers) |
| **the add-on's shader group, no Principled box on the surface** | 46 | 43 `CT / Stone painterly surface.NNN`, `CT / Ceramic painterly surface`, `CT / Ceramic ridge host-local surface`, `CT / Timber painterly surface` | **adapter** (rebuild one Principled box from the group's Albedo, Roughness, Normal and copy its plain numbers), then splice |
| **glow only** (emission, no Principled) | 6 | `Shoji paper glow`, `Shoji paper, softer`, `Open room, dim`, `Lantern flame`, three `... haze` hills | skip (never weathered) |

(The 6 glow-only materials plus `Far hill` are the 7 "glow and backdrop" materials skipped; the 6 leaf-type materials skipped are `Maple leaves`, `Maple inner mass`, `Pine needles`, `Fallen leaves`, `Lily pad`, `Lotus blossom`.)

The street's problem (its old hook wanted a wire on every plug and worked on 0 of 41 materials) is even bigger here: **68 of 134 materials have no wire at all** and 46 have no Principled box on the surface. The "wire or plain number" hook of study 11 is therefore the rule, plus the adapter.

### 4.2 The hook test (`scripts/c6_hook_test.py`, run on this computer in memory, nothing saved; `scripts/c9_eevee_courtyard.py` on the rented machine)

| test | result |
|---|---|
| materials handled | 134 = **75 plain Principled** (spliced) + **46 add-on groups** (adapter, then spliced) + 6 leaf-type left alone + 7 glow/backdrop left alone; no failures |
| Cycles, 480 x 320, 16 samples, no noise cleaning, same seed, full floating-point pictures | before and after **identical: largest difference 0.0, 0 of 153,600 dots differ at all** (an earlier run with 8-bit pictures also gave 0) |
| negative control: the same hook told to darken every colour by 2 % | 114,583 of 153,600 dots changed (75 %; includes light bounced from darkened surfaces), largest change 0.34: the comparison can see a change and the hook is really in the path of all weatherable surfaces. Checked by family with the flat family map: **100 % of the dots of the roof tiles (6,508 dots, the 688 instances), plaster, stones and gravel changed; sky 0 %; leaves only through bounced light (75 % of their dots, by 0.1 %)** |
| EEVEE, 1200 x 800, 48 samples, ray tracing on, shadow rays 4, steps 16 (the street plate settings), rented RTX 4090 | plain against hooked: 7,762 of 960,000 dots (0.8 %) differ by exactly 1 step of 255, none by 2 or more (the street's EEVEE test was exactly identical; here the add-on's heavy groups give a one-step rounding wobble) |
| EEVEE against the Cycles photo | looks the same; mean difference 7.7 of 255; EEVEE slightly brighter (86 against 82 mean), pond reflections softer and grey, stones a touch pinker |
| time on the rented machine | Cycles 1200 x 800 at 48 samples 12.1 s (first picture); EEVEE plain 1.2 s, then hooked 0.6 s; the whole Blender run for the three pictures 18.5 s |

Picture: `25 Japanese courtyard - Cycles photo against EEVEE plate-type picture.jpg`.

**What the test does not tell us:** how long a REAL layer (hundreds of boxes) takes to compile when it sits in 121 materials (the do-nothing group has 12 boxes). The street's rubbish layer (547 boxes) cost about 2 s a plate on 4 road materials; 43 separate stone materials with the same heavy layer will cost more. Not measured. A cure to try first: one shared layer group with per-material inputs (Blender still compiles each material, so measure).

### 4.3 Where each kind of layer sits (the same slots as study 11, section 3.4)

* **Slot A (before a water layer, on the dry colour): grime film, stains, algae tint, efflorescence, lichen tint.** In the courtyard nothing is wired to water yet: the only wet look is the add-on's own `Wetness` dial (0.25 on stone), so Slot A is simply "in front of the Principled box" for the plain materials and "after the adapter" for the add-on's.
* **Slot B (after water): cracks and chips**, dull and sloped so a wet look cannot wash them out (the JOINTS lesson). In the courtyard these are mostly plaster hairline and corner cracks, stone chips, plank-end checks.
* **Slot C (after cracks): growth** (moss, lichen, weeds). It reads the wet mask where one exists.
* **Litter** (fallen leaves, needles) is the last layer, as RUBBISH was on the street.
* **JOINTS** (sett joints) has no job here; the courtyard has no setts, flags or kerbs.
* If the kit later puts the street's WETNESS layer on the courtyard, the adapter makes that possible (it needs a Principled box); the add-on's group already has its own wetness dial, which the kit could drive instead.
* **Relief:** add the layer's height as a Bump on the incoming normal (the add-on's own normal is "fine bump only", so there is no clash), with the distance fade of study 11 (M8).

### 4.4 Things the add-on does that the kit must not disturb
* The add-on keeps an undo handle ("surface transaction") when its pigment, detail or textile tools are used: it then refuses to restore if the receiver's mesh or material bindings were changed. **The kit must change only node trees inside existing materials and add separate objects; never edit or replace the add-on's meshes or material slots.** In the saved scene no object has an open transaction.
* The add-on can rebuild a stone, roof or ground (`update_stone`, `update_roof`, `rebuild_landscape`), which may recreate meshes and materials (I did not run them). Kit changes must be **re-applied by a script from the settings file after any rebuild**, never assumed to survive.
* Its objects carry `astra_*` and `ct_*` custom properties and its materials `astra_runtime_owner` or `ct_material_role`: a safe way to recognise add-on things. Per-object variation in its stone group comes from Object Info "Random", which (I believe, not tested) depends on the object's name, and the courtyard has `.001`-style names: the kit should write its own explicit seed property on each object instead.

---

## 5. Research: how aged Japanese temple and garden courtyards look

Brief, as asked: seventeen web searches and eleven page fetches, today. The sources are thinner than I hoped: several fetches gave only abstracts, and most are not Japanese conservation reports. I mark what is sourced [S] and what is my own reading [M]. The links are at the end of this section.

**Moss (koke).**
* Where: moss wants cool, wet, shaded, undisturbed surfaces [S: Inspectapedia says "cool, wet, shaded"; Saihō-ji's moss "was not part of the original design" and came by itself when the garden was left untended [S: Wikipedia Japanese dry garden and Saihō-ji]; at Ryōan-ji the only plant is moss around the stones [S]]. In a kept garden it is on the ground and around stones, at the base of trees (a pale cushion moss, Leucobryum, collects under conifers where trunk-water is acid) [S: search summary of intosaihoji.com, not opened], on lanterns [S: "appears on stone lanterns, trees and garden paths", japanesegardens.jp]. [M] On this courtyard's parts: the up-facing planes and shaded, ground-touching sides of the pond-edge stones, the rocks and the stepping stones; the lantern's base, then the cap's top where water and dust settle; in the gaps and around the edges of the stepping stones; at wall-cap tops and wall feet; at the lower edges of roof tiles, and more on the shaded (north) slope than on the sunny one [S: roof moss is commonest on north slopes and shaded, damp places, patchy or clumpy on clay tile, helped by tree shade (jrcslate, buildingadvisor, search summaries)]; at plank ends and bridge piers near the water. Not on the raked gravel's middle (raking) and not on the worn tops of stepping stones.
* Look: [M] cushions 5 to 30 cm across that merge into carpets on the ground; thin soft-edged patches on stone, gathering in hollows and along joint lines; clumps on the lower edge of roof tiles. A few millimetres to a few centimetres thick, so mostly colour plus slight relief (the add-on's own clump is 5 cm high and 28 cm across).
* Colour dry and wet: [S] moss is dull brownish-green when dry and bright green within minutes of wetting (a reversible dormancy, university time-lapse and moss guides); [S] a "green bloom" after a night rain. [M] shade moss is darker and bluer, sun-exposed moss yellow-green, the pale cushion moss grey-green. The add-on's tones, in the scene, are linear (0.035,0.075,0.022), (0.085,0.15,0.04), (0.15,0.22,0.065), (0.055,0.105,0.03): sRGB about (0.21,0.30,0.16) to (0.42,0.51,0.28). Kit moss should use these tones so the two match.

**Lichen.**
* Where: [S] on rock, walls, bark, roofs and clay tile; first on rough, shaded, north faces and inside carved lettering; polished surfaces resist [S: Inspectapedia, Wikipedia]; shaded, damp faces are heavily colonised [S: study of statues]. A very old lantern "covered with lichen and moss" is prized; people used to keep a new one shaded and often wetted to grow white lichen [S: 1912 book on Japanese gardens]. [M] on this courtyard: tops and north faces of the big rocks and the lantern cap, wall-cap tops, roof tiles.
* Look: [S] crust-like discs lying flat like a layer of paint, leafy lobes or small tufts; usually green-grey, with yellow, orange and red where exposed and dry; they grow under a millimetre a year (crustose ones 1 to 2 mm of width a year) [S: Wikipedia Lichen]. So lichen is a mark of age: on a young courtyard almost none; on an old one, rings 5 to 20 cm across. Colours: pale grey-green, yellow-green, white, yellow-orange [S].
* Wet and dry: [S] wetting makes the top layer transparent so the green shows: bright green to olive grey when wet; grey to grey-green to brown when dry.

**Grime, dark water stains and rot at the foot of posts and under drips.**
* [S] Dark blotches on exterior wood are usually mildew and algae living on dirt, not rot; silver-grey is the normal sun-and-rain weathering of bare wood; moisture cycling cracks the surface, and end grain (the cut ends of posts and planks) checks most; rot is the worry close to the ground where moisture lingers in trapped or shaded places (Iowa State and other wood-weathering summaries).
* [S] Japanese eaves traditionally let rain fall to a strip of gravel or stones on the ground (amaochi) to stop mud splashing on the building (JAANUS). [M] So the hall's drip line (front eave at y 4.4, z 3.2) should show a darker, coarser, moss-free strip on the ground and a splash band on the plinth and the foot of the posts; stones under the drips get a dark stain but no moss (rain hammering stops it).
* [M] Planks: dark algae and mildew in the gaps and at the ends, worst on the bridge where the pond keeps it damp; the bridge's lowest points and piers wear a wet-line stain at the water level.
* [S] Posts in Japanese halls stand on base stones (soseki), some cut with a channel to shed water (mizukiri) [JAANUS]; the old weak point of buried posts was rot at soil level [S: JAANUS]. In this courtyard the posts stand on the veranda deck, so the rot stain is at the foot of the posts on the deck and at the deck edge, not in the soil. [M]

**Streaks on plaster (the earthen wall, dobei).**
* [S] Algae grows where rainwater dribbles down a stucco wall; a wall under a roof overhang stayed algae-free; an overhang or a flashing with a drip edge reduces it; shaded areas let algae and mildew flourish [S: Green Building Advisor; Inspectapedia]. [S] Efflorescence is a white fluffy deposit that brushes off, and it signals water getting into the wall; [M] at the wall foot and below the cap.
* [M] So: vertical streaks hanging from the cap tiles' lower edge and from the hall eave, wider and darker where the cap is chipped or at the ends; a splash band 20 to 40 cm up from the ground; a pale band above the damp line; green-grey algae and black mildew spots on shaded (north) faces; hairline map cracks, vertical corner cracks, and spalled patches near the foot that show the earth beneath. My searches found nothing specific on dobei streaking; this paragraph is mostly my reading.
* Colour: plaster is light (0.64 bright in the plate), so grey-green, brown (tannin) and dark mildew read well; a few white salt patches.

**Weeds and grass.**
* [S] Gravel itself does not feed weeds: seeds blown in with dust and leaf debris sprout, mostly along borders and at edges, and grass creeps in from the sides; keeping gravel clear of leaves and dirt is the cure [S: Gardeners' World, a gravel-path blog]. [S] A kept karesansui court is raked two to three times a month, and moss is the only plant; the gravel itself gets finer with weathering and is topped up [S: Wikipedia]. A kept stepping-stone garden keeps its open ground "firm, well weeded and swept, slightly damp" [S: 1912 book].
* [M] So the **default is almost none**: moss, not weeds. A neglected variant puts grass tufts (5 to 15 cm) along the gravel edge, at the foot of the rocks in the gravel and between stepping stones, rosettes in cracks of steps and the plinth, and small plants on the wall caps and roof edge ([S] "grass growing from the roof peak", a commenter on a shrine-roof blog). Leaf litter and pine needles are the real clutter.

**Cracks and chips in stone.**
* [S] A study of a stone lantern and its base in Korea (abstract only) found cracks, scaling, black, white and brown discolorations and lichens, mosses and herbaceous plants, with the cracks clustered on the north side and linked to freeze-thaw. [S] Lichen hyphae can grow millimetres into granite.
* [M] Chips at the corners and edges of the lantern cap, the steps and the stepping stones; hairline cracks across thin parts (the lantern post); orange-brown iron stains (none here, no iron); the add-on's own stones already carry a mild edge-wear mask. At painter size only chips of about 5 cm and larger read.

**Wet weather.**
* [S] Moss rehydrates and turns bright green; lichen turns greener and translucent; [M] stone and wood darken and lose contrast, plaster darkens from the foot up and the streaks grow, gravel darkens (raked lines hold), roof tiles go glossy black with sharp reflections, the drip line and the stepping stones show wet, the pond ripples. No puddles on a Japanese court: water collects only in hollows of stones and the pond. The kit's "wet" state for this set should mean "darker, greener, glossier", not "puddles".

**What the sources did not give:** colours and sizes of streaks on dobei; any Japanese conservation report on moss on kawara (roof tiles; the sources say moss on roofs is generally "thought to be detrimental" and metals like zinc are used against it [S: a commenter]); a source for wet versus dry moss colour in Kyoto in particular; iron staining on stone lanterns. For these my numbers are GUESS.

Sources: [Landscape Gardening in Japan 1912, patination of stone lanterns](https://www.gardenvisit.com/book/landscape_gardening_in_japan_1912/chapter_3_garden_lanterns/patination_of_stone_lanterns); [same book, stepping stones](https://www.gardenvisit.com/book/landscape_gardening_in_japan_1912/chapter_2_garden_stones/stepping_stones_tsutai-ishi); [Wikipedia, Japanese dry garden](https://en.wikipedia.org/wiki/Japanese_dry_garden); [Wikipedia, Saihō-ji](https://en.wikipedia.org/wiki/Saih%C5%8D-ji_(Kyoto)); [Into Saihoji, moss journal](https://intosaihoji.com/en/journal/goki002/) (search summary only); [Moss in the Japanese Garden, japanesegardens.jp](https://japanesegardens.jp/plant_tag/sphagnum/); [Wikipedia, Lichen](https://en.wikipedia.org/wiki/Lichen); [Inspectapedia, Lichens on Stone](https://inspectapedia.com/exterior/Lichens_on_Stone.htm); [Green Building Advisor, algae on stucco](https://greenbuildingadvisor.com/article/preventing-algae-on-stucco-with-flashing-or-overhangs); [Wikipedia, Efflorescence](https://en.wikipedia.org/wiki/Efflorescence); [JAANUS amaochi (eaves drip ground)](https://projects.mcah.columbia.edu/jaanus/node/5246); [JAANUS soseki (base stone)](https://aisf.or.jp/~jaanus/deta/s/soseki.htm); [study of a stone lantern's deterioration (Korea), abstract](https://www.earticle.net/Article/A360269); [Abodo, natural weathering of timber](https://www.abodo.co.nz/resources/articles/natural-weathering-of-timber-surface-checking); [moss on roofs, JRC Slate](https://www.jrcslate.co.uk/?p=2674); [Weeds in a gravel path](https://bifurcatedcarrots.eu/2011/09/weeds-in-a-gravel-path/); [Gardeners' World, weeding garden paths](https://www.gardenersworld.com/plants/weeding-garden-paths); [weathered shrine roof, regex.info](https://regex.info/blog/2008-07-12/867); [moss dormancy, Berkeley 3D Moss](https://3dmoss.berkeley.edu/community-outreach/media).

---

## 6. What the courtyard's own shapes say about where shade and damp are (tested)

Method (`scripts/c8_shade_maps.py`, 6 seconds on this computer): for each spot of a 0.2 m grid over the ground (11,550 spots), each wall face (1,016 spots) and each roof face (234 spots) it shoots **32 fixed sky directions** (openness: the share of sky the spot can see) and **48 sun directions** (both solstices and the equinox twice, every hour of daylight) at the real shapes: hall, walls, rocks, stones, lantern, bridge, bamboo; leaves block 60 %. "Year sun" is the share of an unshaded flat spot's year of direct sun, so 1.0 is full sun. **Assumption to confirm: latitude 35 degrees north (Kyoto) and north along +y**, i.e. the hall faces south, as a hall looking over a garden usually does, and the golden-hour sun low from the left (west, -x) agrees with that. I did not find a north in the scene; the sun lamp is a one-moment golden-hour lamp, not a sun path.

| spot | year sun (mean) | openness (mean) | spots |
|---|---|---|---|
| all land (not under the hall, not the pond bed) | 0.76 (shadiest tenth 0.36 and below) | 0.75 | 9,262 |
| ... of which under 20 % of open-spot sun / under 35 % | 6.0 % / 8.7 % | | |
| raked gravel court | 0.87 (3.9 % of it under 35 %) | 0.83 | 1,599 |
| the pond's bank ring (1.05 to 1.4 pond radii) | 0.68 (**20.5 % under 35 %**) | 0.60 | 561 |
| plaster walls facing north | **0.06** | 0.71 | 290 |
| plaster walls facing east / south / west | 0.48 / 0.36 / 0.37 | 0.61 / 0.27 / 0.32 | 218 / 290 / 218 |
| roof slope facing north / south | 0.68 / 1.13 (a south slope gets more than a flat spot) | 0.97 / 0.96 | 12 / 12 |

(Wall numbers are not on the same scale as the ground's: a wall can never get a flat spot's sun. Read them as "north face about a tenth of the others". The roof has only 12 + 12 face samples: the base mesh is coarse.)

**Does the add-on's own moss follow this shade?** I counted the add-on's moss mesh points per 0.5 m cell (199 of 1,515 land cells have any) against the cell's shade. Rank match with year sun **+0.15**, with openness +0.11 (0 = no link). The share of the add-on's moss points in cells under 35 % sun is 11.2 %, and those cells are 11.0 % of the land: no difference. The add-on places moss by hand-drawn patches, not by shade. So the kit's shade-driven growth will land in different places from the add-on's: either **extend** (fill shaded and damp places the add-on left bare) or **match** (grow where the add-on is), a choice for the preset and for the person.

Reading the picture `25 Japanese courtyard - where sun and shade fall and the add-on moss.jpg` (top-down: sun, openness, and the add-on's moss; north up; the camera is the magenta triangle): the shade is the hall's footprint (greyed), the sunken pond margin and the bank behind the pond (the rock group's north side), under the maple on the left, along the garden wall's foot, and small dark dots beside each stepping stone and the lantern. The big gravel court and the front lawn are bright. **So for this courtyard moss needs a second driver, dampness: near the water line (the pond bank ring, the basin), low ground, under the drip line of the eaves and the cap overhangs, and at wall feet.** That is the same idea as the street's "gutter" and "wall foot" damp zones, so one generic "dampness picture" made from the water level, the ground's low spots, the drip sources and the wall feet serves both sets.

---

## 7. What the painter will see in this set

### 7.1 Size of things (camera maths, section 3's column)
Median distance of each family from the camera: pond-edge stones 5.4 m, bridge 6.3 to 7.0 m, soft ground 6.9 m, rocks 9.4 to 9.7 m, gravel 10 m, plinth 12 m, roof tiles 13 m, beams 13 m, posts 14 m, hall plaster 15 m, garden wall 18 m. One painter dot: `2 x distance x tan(34.7 degrees) / dots across` = 1.13 mm per metre of distance if the painter gets 1229 dots across and 2.0 mm per metre if it gets 691. The ground is seen at a grazing angle (26 degrees at the soft ground, 17 degrees at the gravel), so a flat mark on it is squashed 2.3 and 3.3 times along the view.
What reads (rule of thumb of study 11, about 3 painter dots across to survive, and standing things keep the across-view size): **moss clumps (28 cm), lichen colonies of 10 cm and more, stain bands, streaks, plank-end dark staining (planks are 15 to 26 cm wide: 10 to 30 dots), leaf litter, weed tufts 5 to 15 cm tall (5 to 15 dots at 10 mm), rake lines (17 cm pitch)** all read; **hairline cracks (2 mm), single lichen discs of 1 to 3 cm and small chips** do not (at 6 to 20 mm a dot), and tile-edge moss reads only as a dark or pale line along each tile row. Fine detail has to fade to an average tone with distance, as in study 11 (M8).

### 7.2 Brightness: where dark grime can show (`out/c1/brightness_by_family.json`; EEVEE picture 1200 x 800, each family labelled with the flat family map)
| family | mean brightness | dots under 0.13 | under 0.17 | so |
|---|---|---|---|---|
| plaster walls | 0.64 | 0 % | 0 % | dark and coloured stains read |
| raked gravel | 0.41 | 0 % | 0 % | dark and light read |
| add-on stones | 0.37 | 0 % | 2 % | dark and light read |
| wood (planks, posts, beams) | 0.31 | 15 % | 20 % | planks fine; posts, beams and lattice are dark: pale marks |
| soft ground | 0.27 | 2 % | 8 % | dark film and moss tones read |
| plain stone (plinth) | 0.30 | 0 % | 0 % | fine |
| wall cap tiles | 0.27 | 4 % | 6 % | fine |
| pond water | 0.22 | 9 % | 44 % | (own layer later) |
| **roof tiles** | **0.14** | **47 %** | **67 %** | pale only: moss, lichen, pale stain |
In Cycles (the photo) the means are within 0.01 of these for ground, gravel, stones, wood and roof, and lower for plaster (0.56), water (0.15) and the plinth (0.26); the darkest tenth of the wood is 0.03 against 0.10. Compare the street: walls 0.07 to 0.09 and 80 to 90 % of their dots under 0.13. **The stage crushes darks (a painted 0.13 comes out 0.07), so a mark must differ from its surface by lightness or colour with room to move.** The kit should read this per role from the measured plate (the runner can measure it at the start) and pick the mark's direction itself: dark where the surface is brighter than about 0.25, pale or coloured (moss green, lichen cream, rust orange) where it is under about 0.13, either in between. Not typed per set.

### 7.3 Open questions about the painter (not tested)
Whether the painter keeps moss and streaks on a bright, soft, painterly courtyard picture or turns them into brush strokes is unknown: no courtyard has gone to the painter. The courtyard's add-on materials are already "painterly" (brush-dab pigment planes in the group), so the plate is closer to a painting than the street's photo textures were; weathering that mimics the same brush logic may survive better. Ask only after a plate shows the marks at 100 %.

---

## 8. What the kit must handle so ONE set of layers covers both sets

| topic | the street (study 11) | the courtyard (this study) | so the kit must |
|---|---|---|---|
| **surface kinds** | brick, stone brick, dressed stone, setts, flags, cast iron, slate, painted wood | plaster, timber (planks, posts, lattice), ceramic tile, natural stone (many separate), gravel, earth and moss | work from **roles** (`wall.masonry`, `wall.plaster`, `timber.frame`, `timber.deck`, `timber.paint`, `stone.dressed`, `stone.natural`, `ground.paving`, `ground.gravel`, `ground.earth`, `roof.slate`, `roof.tile`, `iron`, never-weather) listed in the set's settings, found by object name, collection, material name **or material custom property** (the add-on's `ct_material_role`) |
| **material hook** | all Principled, nine without a Normal wire; old hook failed on all | 68 with no wires, 14 noise or vertex colour, **46 add-on groups with no Principled on the surface**, 6 glow | one "wire or number" splice (proved on 41 + 85 + 121 materials) **plus the adapter** for shader-group materials (proved on 46 of 46); skip lists by role; works under instances and with a Mix Shader after the box; never edits meshes |
| **many material copies** | 4 shared wall meshes, 4 wall material copies | 43 stones with 43 material copies of one group; 56 plank tone materials | apply by family in one loop; the layer is one shared group with per-material inputs; one seed per object, written by the kit |
| **coordinates and frames** | wall pictures in each wall's own turned frame; ground in world | walls are straight boxes (world is fine); stones tilted with their own rest coordinates; roof tiles are instances | the geometry reader asks the settings for each role's frame (`object`, `world`, `rest`) and for instances reads the realised copies; masks on stones come from the shader (up-ness, height above contact, the add-on group's Wear Mask) because they have 61 to 72 faces |
| **ground** | hard setts, flags, channel, kerb; crown 8 cm; 4 degree slope; gutter at 2.35 m | loose raked gravel (real relief), soft earth with banks and a pond bed, no road | take ground height, slope and "lowness" from the ground picture (generic), never from \|x\| or a typed slope; crown, channel and kerb become optional inputs |
| **water** | none; wetness makes puddles | a pond, a basin, a shore found where ground crosses z -0.12; a wet line on stones, bridge piers and planks at the water level | a `water` entry in the settings (objects, level) and a "distance to the water line" and "height above water" picture; shore from the ground height, not the water object |
| **who walks where** | cart wheel lanes, road middle, pavement along the wall, door to kerb | stepping-stone path, bridge, veranda front; **raked gravel kept un-walked** | a list of `footfall` shapes (line or area, width, feather, traffic weight, kind), including zones of negative traffic (raked, kept clean); street lanes and courtyard paths are the same data |
| **shade** | no real sun path (dusk lamps); even dim canyon; openness 0.4 to 0.56 | real golden-hour sun; shade weak (8.7 % of land under 35 % year sun) | one generic "shade" input made from **year sun (declared latitude and north) and openness**, falling back to openness alone when the set declares nothing; plus a **dampness** picture (water line, low ground, drip lines, wall feet) as the second driver |
| **run-off sources** | sills, string courses, eaves, a downpipe: found from up-facing ledges | roof eave line, cap overhang, lantern cap, veranda edge, no sills, no pipes | the ledge finder takes "what counts as a source" from the settings (roles whose lower edge sheds water) and finds them from the geometry; drip lines on the ground under them (the Japanese amaochi) come from the same finder |
| **growth already there** | none | add-on moss and pebbles (real geometry), painted moss colour in the ground material, fallen leaves | the settings list `existing_growth` objects; the reader writes a density picture; kit growth avoids or extends it, never doubles it |
| **colour direction** | everything under 0.13 on walls: pale or coloured marks only | plaster 0.64, gravel 0.41, stone 0.37; only roof under 0.13 | choose dark or pale marks per role from the plate's measured brightness (study 7.2) |
| **size of marks** | 1.7 to 2.9 mm per painter dot across the street at 3 to 5 m ahead (3 to 9 mm along it), 5 to 8 mm at 9 to 13 m | 6 to 21 mm (wide) or 11 to 37 mm (narrow) per painter dot | give every mark size in painter dots and let the kit turn it into metres from the settings' camera list and each surface's measured distance and slant |
| **litter and scatter** | cinders, ash, coal, paper, straw, mud, rags, in gutters and wall feet | maple leaves, pine needles, twigs, petals, a few pebbles; wherever the maple and pine drop and wind carries them | one scatter engine (Poisson-disk, mask picture, seed), a **piece set per preset**; scatter on the evaluated and realised surface (gravel is displaced by 1.6 cm; the roof is instances) |
| **per-object seed** | Object Info Random (name based) | renamed objects (`.001` ...), the add-on's `ct_surface_seed` | an explicit seed property written by the reader on every object, so renaming or rebuilding does not reshuffle |
| **engine and camera** | EEVEE plates, cameras in a table typed in code | Cycles scene that EEVEE draws well; one camera now | cameras, plate size, engine and painter scale in the settings; the runner takes them from there; same states ("today" first) |
| **rebuilds** | none | the add-on can rebuild stones, roof, ground | applying the kit is a script run from the settings after every build; never rely on it surviving |

**Layers that need nothing but the generic inputs:** position (world, object or rest), normal, distance-to-wall and edge pictures, cavity or curvature (from the add-on's Wear Mask for its stones, from the photo height pictures for the street; the courtyard has no photo height pictures), shade, dampness, footfall, existing growth, wet masks only if a wetness layer is present. Nothing in the layers' code names a street or a courtyard object, coordinate or size.

**Layers that will not carry over as code** (they were street layers): JOINTS (sett joints), the street part of RUBBISH (places pictures of gutters, kerbs, doorsteps and pipe feet; coal pieces), the street part of WETNESS (puddle curve fitted on the main camera's road, crown, lowness from \|x\|). Their *methods* carry over (the masks method, the scatter engine, the chain).

---

## 9. The looks are presets of the same dials (first guesses, not measured)

Same layers, same code; two settings files. Everything in this table is **GUESS** to start from, except where it says measured.

| layer and dial | sooty 1926 coal-town street | mossy Japanese courtyard (kept temple) | neglected variant of the courtyard |
|---|---|---|---|
| soot / dark grime film | high; on walls, trim, roofs, iron; brown-black (study 11: stone and brick tones from the brick GRIME trial) | near 0 | 0 |
| dust and algae film (green-grey) | low | medium on plaster foot, wood, shaded stone | high on plaster, bridge, steps |
| run-off streaks | from sills, eaves, pipes; pale or coloured on dark walls | from cap overhang and eave; **dark grey-green, brown, on light plaster** | stronger, wider |
| rust (tide marks, streaks) | cast iron, pipes, gutters, lamp posts | none (no iron in the scene) | none |
| lime or salt, efflorescence | medium on brick and stone feet | a little white salt at plaster foot | more |
| cracks | stone steps, kerbs, setts; few | plaster hairline and corner cracks, stone chips, plank-end checks; few | more |
| moss (tones) | rare: gutters, wall foot, north steps; the slate recipe's five olive tones | **common: stones, ground, wall caps, tile edges, plank ends**; the add-on's four moss tones | very common |
| lichen | rare | on rocks, lantern cap, caps, tiles; slow: only on old surfaces | more |
| weeds | gutter and kerb joints; few | **almost none** (kept: only at the extreme edge of the gravel and in step cracks) | grass tufts along gravel edge and at rock feet, in step cracks |
| litter set | cinders, ash, coal lumps, paper, straw, mud | maple leaves, pine needles, a few twigs | many more |
| "wet" state | puddles, shiny setts | darker stone and wood, greener moss, glossier tiles, no puddles | same |
| mark direction | pale or coloured on walls (under 0.13), dark on road and pavement | dark on plaster, gravel, ground, stone; pale on roof tiles and the darkest timber | same |

---

## 10. What would be wrong to carry over from the street

* **Coal soot as the default dirt.** The courtyard is not a coal town; soot would turn the pale plaster grey-black and the stones sooty. Soot is one dial in one preset, at 0 here.
* **Coal-town litter** (cinders, ash, coal lumps, mud, straw, paper, rags): the RUBBISH layer's pieces and its colours are a *look preset*, not code. The courtyard's litter is leaves and needles.
* **Rust from cast iron** (gutter, downpipe, lamp post tide marks): there is no iron in this scene. Keep the layer, give it no role.
* **Sett joints, kerb edges, the gutter channel, the road crown, cart lanes, doorsteps and pipe feet**: street objects. The courtyard has footfall and a pond bank instead.
* **The 4 degree slope, the street's width, "x = 0 is the middle line", the gutter at 2.35 m, the places-picture grid (x -4.5 to 4.5, y -12 to 72), every name regular expression** (`*_cottage_NN_walls`, `street_setts`, `gas_lamp_N`): all go to the settings file.
* **The street's dials fitted on one camera** (puddle dial 0.5 = 8 % on the main camera's road): a "how much" dial must be tied to a share of a surface in a given view and re-checked on every camera.
* **The street's rule that "walls are dark so use pale marks".** Here the walls are light.
* **A shade rule from the sun lamp.** The street's lamps were no sun path; here the golden-hour lamp is a one-moment light. The courtyard's shade must come from a declared latitude and north, not from the lamp's direction.
* **"Moss is rare"** (street) and **"weeds are rare"** (kept temple) are preset values: do not bake either into code.
* **Weathering a kept temple like a neglected one.** A raked court is swept; weeds in the gravel's middle would be wrong for the "mossy courtyard" the person asked for. Moss on stone is the desirable sign of age there [S], so the preset's job is to make it look cared-for.

---

## 11. The settings file for this set (a draft)

`out/c1/japanese_courtyard.draft.json` (next to this study; the kit's own `sets/japanese_courtyard.json` should be made from it). It holds, with the numbers measured above: the scene file, the roles with name patterns and add-on custom-property rules (stone, dressed stone, deck and frame timber, roof tile and deck, plaster, caps, bamboo, bark, existing growth), the never-weather list and the "own water layer later" list, the ground objects and picture bounds, the walls' frame, the drip and ledge sources (eave line, cap overhang, lantern cap, veranda edge), the water (objects, level -0.12, shore note), the footfall shapes (stepping-stone path from the add-on's landscape spec, the zigzag bridge, the veranda front, the raked court at zero traffic), existing growth, the sun and shade model (latitude 35, north +y, assumption flagged), scale numbers (plank width, tile size, stone size, rake pitch and relief, floor, eave and ridge heights), the camera and plate, the hook rules (skip emission, add-on groups need the adapter) and the scene's own colour palette (add-on moss tones, ground, gravel, plaster, roof tile and stone ramps, plank tones) and the measured plate brightness per role.
What it does NOT hold yet: the street's equivalents (`sets/pit_village_street.json` is for the kit builder), a plate camera for the film (the saved camera is the photo's), and anything the person must decide: whether north is +y, whether the court is kept or neglected, and whether the kit moss extends or matches the add-on's.

---

## 12. What I tested, what I did not, what I am unsure of, and what went wrong

**Tested (by running it):**
* Which scene matches the final photo (pixel comparison, 3.84 million values, difference 0; file times).
* The list of every object and material of the saved scene, by family and by how it is built; the add-on's shader groups' inputs, outputs and inner boxes (stone, ceramic, ridge, timber); the roof's 688 instances; the add-on's bookkeeping properties.
* What the camera sees, by rays (two grids: 120 x 80 and 240 x 160) by family and by object; brightness by family in the EEVEE and Cycles pictures; painter-dot sizes from the camera maths.
* The generic hook and the adapter on all 134 materials in memory: identical in Cycles (full floating-point), a negative control that shows changes, within one step on 0.8 % of dots in EEVEE; EEVEE against Cycles; EEVEE timing on the rented RTX 4090 (three pictures in one run).
* Sky openness and year-round sun on the ground, the walls and the roof, and the add-on's moss against shade.
* Seventeen web searches and eleven page fetches.
**Left on the rented machine:** my scripts folder and one small output folder (`.../study/out/c1/rented`), under the same paths as here, plus the courtyard scene file I uploaded (8 MB). I did not touch `~/.runpod` and did not stop the machine.
**Read, not run:** the add-on's `materials.py`, `api.py` and README; the build script; the pipeline study 11 and the Scenario skills' names (no moss or lichen recipe is in them; the geometry-nodes skill's `scatter_tree` helper is the scatter helper that study 11 recommended).
**Not tested:**
* Any weathering layer (none exists).
* The painter on a courtyard plate (no courtyard has been sent).
* Cost of a real heavy layer in 121 materials (only the 12-box do-nothing group).
* A tall plate camera for the courtyard (only the photo's camera; the film's plate is a different shape).
* The "wet" look of the courtyard (the add-on's `Wetness` dial was not varied; no wetness layer on it).
* The explicit per-object seed idea (an Attribute node reading an object custom property): believed to work in EEVEE and Cycles, not run. That Object Info "Random" depends on the object's name: believed, not run.
* Scatter on the realised roof and on the displaced gravel.
* The rest of the 43 stone materials one by one (I dumped two stone, the ceramic, the ridge and the timber materials by hand; the adapter was then applied to all 46 and the Cycles picture came out identical, which shows they share the structure).
* Blender 5.1 and add-on 0.2.1 (the story says the 0.2.1 courtyard is identical).
**Unsure:**
* The orientation: **north = +y and latitude 35 degrees are my assumption** (a hall looking over a garden faces south; the golden-hour sun from the left fits). If the film places the courtyard otherwise, the shade picture changes.
* The openness and sun numbers use 32 and 48 fixed directions per spot (not smoothed, not compared with a picture); leaves block 60 % (a guess); bamboo stalks block fully (thin but many); the roof has few samples.
* My "share of the picture" values are from 38,400 rays (about 0.25 points).
* The research: thin, partly search summaries only; the marks in section 5 tagged [M] are my reading.
* The adapter copies the group's plain numbers from the Principled box inside the group; if the add-on changes its group the adapter may need a look (it was written against 0.2.0).
* Section 9's dial values are guesses.
**What went wrong (all of it):**
* **My first camera-ray count said 4.4 % of the picture was "hidden: ground source and prototypes".** It was actually the 688 roof tiles (their hidden prototype is what a ray hits), so my first table undercounted the roof by 4.5 points (0.8 instead of 5.3). Found by counting hits by exact object name; fixed in `family_shares.json`.
* **My first sun and shade numbers counted spots inside solid things** (under the hall, the pond bed) and so said 10 % of the ground gets no sun at all and 20 % is shaded; re-counted for land only: 8.7 % below 35 %.
* **The first EEVEE batch on the rented machine drew 480 x 320 pictures at 16 samples instead of 1200 x 800 at 48**: my script reused a variable name that the borrowed hook code overwrote. The second try crashed on a list that the borrowed code also overwrote. Third run was right. The comparison numbers in this study are from the third run.
* **My first shade script crashed at the very end** on a number type (it wrote a float32 into a JSON file); fixed and re-run (6 s).
* **The EEVEE hook was not exactly identical** (one step of 255 on 0.8 % of dots), unlike the street's exact zero. I report it as it is.
* **The study folder's size.** The folder `study/` is about 61 MB, of which 52 MB is another job's `painted_look/` folder; my own files (scripts about 0.2 MB, `out/c1` about 1.3 MB after I turned the big PNGs into JPGs and deleted the raw map) are far under 20 MB. I did not touch the other job's folder.
* The web tool returned search summaries more than page text for several pages; some fetches gave only an abstract (the Korean lantern study) or a teaser (japanesegardens.jp). I used them only for what they said and marked the rest [M].

---

## 13. What I would do next (for whoever builds the kit)

1. Make the chain and the hook the first code: one list per material, the six plugs (Base Color, Roughness, Metallic, Specular IOR Level, Coat Weight, Normal), "wire or number", the **adapter for shader groups**, skip lists by role, add, remove, move, rebuild. Its self-test is my test: a do-nothing group gives an identical picture on all materials of all four files (street, lockout, courtyard Cycles, courtyard EEVEE), plus a control that changes 2 %.
2. Ask the person two things before painting: **where is north** (and is it kept or neglected) and **does kit moss extend or match the add-on's moss**.
3. Make the geometry reader generic: ground picture (height, slope, lowness), shade (year sun and openness), dampness (water line, drip lines, wall feet, low ground), footfall, distance to wall and edge, existing growth density; wall pictures for ledges and drips; instances realised; per-object seeds written. Time: 6 s on the courtyard here for the shade part.
4. Start the courtyard with the layers that read best at painter size: **moss on stones, the pond bank and wall caps (pale-green, with the add-on's tones), grey-green algae streaks on the plaster below the cap and the eave, dark water staining at plank ends and the foot of the posts, and a dampness band on the plinth.** Draw 5 EEVEE pictures at 1200 x 800 (about 1 s each) before anything else. Lichen as a slow, sparse layer on old surfaces only. Hairline cracks last (below painter size).
5. Measure the visibility of marks per role with the street's line ("a mark reads if it differs by 12 % and twice the surface's grain"), per camera, and choose dark or pale from the measured brightness.
6. Time a real layer in all 121 materials before anyone promises a plate time.
7. Ask for a repaint only after a plate shows the marks at 100 %.

---

## 14. Files

All under `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/study/` (my part about 1.5 MB).
* This file: `12b Second set - the Japanese courtyard.md`.
* Scripts in `scripts/` (each starts with a plain note and its run line; none saves into the courtyard files): `c1_names.py` (object names), `c2_addon_groups.py` and `c5_wood_group.py` (the add-on's shader groups), `c3_survey.py`, `c3b_hidden_hits.py`, `c3c_family_shares.py` (families, camera rays), `c4_roof_and_instances.py` (roof copies and stone attributes), `c6_hook_test.py` (the hook and adapter test), `c7_family_map.py` and `c7b_family_sheet.py` (the colour map and sheet), `c8_shade_maps.py` and `c8b_make_maps.py` (openness, year sun, add-on moss), `c9_eevee_courtyard.py` (Cycles against EEVEE on the rented machine), `c10_brightness_by_family.py`, `c11_material_kinds.py`, `c12_addon_marks.py`.
* Results in `out/c1/`: `names.txt`, `survey.json`, `hits_by_object.json`, `family_shares.json`, `material_kinds.json`, `roof_instances.json`, `addon_groups.txt`, `wood_group.txt`, `addon_marks.json`, `brightness_by_family.json`, `shade_stats.json`, `shade_land_stats.json`, `shade_ground.npz`, `shade_moss_density.npz`, `hook/t_result.json` (the do-nothing test), `hook/control_result.json` (the 2 % control), `rented/` (the three 1200 x 800 pictures as JPG and their seconds), `pics/`, and **`japanese_courtyard.draft.json`** (the draft settings file).
* Pictures worth showing, in `/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/`: `25 Japanese courtyard - surface families and what the kit would treat.jpg`, `25 Japanese courtyard - where sun and shade fall and the add-on moss.jpg`, `25 Japanese courtyard - Cycles photo against EEVEE plate-type picture.jpg`.
