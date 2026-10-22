# 30 Plan - Japanese garden - all the advice (21 October)

What this is: one plan for improving the Japanese courtyard (the one built on 18 October with your Astra add-on) and then drawing it on a rented graphics card on RunPod, paying per second. It is built from four reading-and-testing studies: the add-on's own advice, our own advice (street work, weathering kit, scanned surfaces, Cycles vs EEVEE, the seven Scenario skills), a hard look at the scene itself, and how real Japanese gardens look. Nothing was drawn at full size and nothing was paid for while making this plan.

All paths below start with `scratchpad/` unless they start with `/home/user`. Short name used below: `PW` = that scratchpad plus `proc-work/`, so `PW/garden/shapes/` means the folder `.../scratchpad/proc-work/garden/shapes/`.

---

## 1. The short version

The garden today has the right ingredients but reads as a quick sketch: one flat orange sky, flat cut-out hills, a blotchy "camouflage" ground, maple leaves that are paper confetti, crystal-looking rocks, dark pink-brown "gravel", a see-through-nothing pond, and a lantern whose cap floats above the lamp. About 57 percent of the picture (ground, gravel, stones, planks, plaster, roof) can be improved with real photographed surfaces plus our weathering kit; about a third (sky, hills, maple, pine) needs new modelling or a new backdrop.

The plan, in the order a viewer would notice it:

1. **Light, sky and hills** (about 22 percent of the picture, and the orange wash that colours everything). Graded sky, hills that go all the way round and fade by colour, cooler shadows, one saturated colour kept for the maple, vignette, light on separate layers.
2. **Ground** (about 16 percent). Photographed forest-floor/moss surface in a few broad passages instead of red-green noise, smooth shading, real 3D moss and tufts.
3. **Maple** (about 10 percent, the most saturated thing). Leaves a third of today's size, seven-lobed, mixed colours, crown in layers with gaps.
4. **Rocks** (about 9 percent). More, unequal flat planes, half-buried, real stone surfaces, moss at their feet.
5. **Gravel court** (about 7 percent). Pale grey-white granite, finer and crisper rake lines, a proper edge, moss collars round the rocks.
6. **Pond and bridge** (about 12 percent together). Pond water you can see into with a bed; bridge boards in silver-grey with their own wear, and the bridge actually carried by its piers.
7. **Roof** (about 5 percent). Real tile surface, not crushed black, moss and stains only where water and shade put them.
8. **Lantern** (small but it is the focal point). Carved six-sided lantern with a real opening, no gaps, a dim warm glow.
9. **Walls and hall plaster** (about 4 percent). Slightly battered clay wall with a real overhanging tile cap, stains, damp foot.
10. **Small things**: pine as dark flat pads, bamboo, fallen leaves, stepping stones, water basin set, shore.

Then draw it with **Cycles on a RunPod graphics card** (the renderer your rule asks for where lights are on; this scene has glowing screens and a lantern), at least the original golden-hour view, plus a second view from the veranda. The pictures are drawn with each light on its own layer, so the glow can be turned up or down afterwards for free instead of paying for a second drawing.

Work is split into **four builders who work side by side** (each in their own folder, each only touching their own objects) and **one final step** that puts it together, checks it, draws it on RunPod and reports.

---

## 2. What the four studies read, and how sure they are

| Study | Read | Could not / did not | How sure |
|---|---|---|---|
| Add-on (0.2.1 unpacked, read-only) | Every guidance file, all 83 lessons in full, 16 of 83 recipes in full (rest checked by machine: they repeat the lessons), tool code; ran the unused tools on Blender 5.2.2 | The 236 evidence records (read only the Japanese and feedback ones); the add-on's own evidence reports are not in the upload, so its claims about its earlier scenes cannot be re-checked | Reading high; tool limits and 5.2 breakages high (each reproduced); picture judgments medium |
| Our advice | Cookbook front, weathering kit and its recipe, courtyard set file, painted-look study, EEVEE/Cycles study, RunPod notes, five Scenario skills; wrote and tested three kit fixes headless | uv-baking and export skills; no after-picture of the kit fixes (a small EEVEE picture takes over 3 minutes on this shared computer); scans picked by thumbnails, not by drawing them | Kit fixes high (structure proven, street unchanged); scan picks and kit dial values medium or guesses; time and cost low |
| The scene | The whole build script, the saved file, the photo at full size, the add-on delivery check, six close-ups | Did not draw in Cycles (rule); every fix untested | Facts and measurements exact; ranking of weak spots is judgment plus measured area, not a viewer test |
| Real gardens | Conder 1893 in full, a 2015 Kyoto gravel survey in full, JAANUS and Wikipedia pages, practitioner lists | najga.org blocked; almost nothing on roof moss on Japanese tiles; no measured rake spacing; no CG-specific source | Gravel colour, grain, stone setting, wall shape, maple and pine facts strong; rake pitch, lantern lichen, roof moss weak |

---

## 3. Ranked improvements (what a viewer would notice most)

Shares are how much of the golden-hour picture each thing fills, measured on a flat colour map from the same camera (from the scene study). The ranking is share multiplied by how wrong it looks, which is judgment. "Who" is the builder number in section 7.

| # | What is wrong now | Share | What fixes it | Advice behind it | Who |
|---|---|---|---|---|---|
| 1 | Sky is one flat orange (varies by 0.4 of 255 over 392,000 dots); hills are flat cut-outs in five colours and exist only behind the hall; the world is one constant orange from the ground up to 30 degrees, so every shadow is washed orange; sky is the second brightest big area; edge as bright as centre | 22 | Graded sky; ridges all the way round, darker and cooler when near, paler and bluer far, soft top edges made by colour, not blur; sun lamp and sky sun pointing the same way; vignette about 0.8; lift roof band; one saturated hue (maple) | add-on: depth by colour and selective edge loss, no veil that erases the hall; scene: world and hills; ours: brightness study, vignette, light groups | 4 |
| 2 | Ground is a red-green noise carpet with flat 25 cm facets; the add-on's real moss barely shows | 16 | Scanned moss/forest-floor surface in broad unequal passages (damp dark, mossy green, dry earth) with quiet middles; smooth shading; 3D moss where dark damp meets pale stone; tufts; no moss on raked gravel | add-on: broad few irregular groups, not camouflage islands; moss reads by contrast not size; real gardens: fine mottled carpet | 3 and 2 |
| 3 | Maple leaves: 7,500 flat five-point stars, 20 to 34 cm wide, one orange | 10 | Real size (5 to 12 cm), seven lobes with serrated edge and a bend, colour from deep red through orange to a few yellow-green and brown, crown as separate layers with windows, backlit glow | scene, real gardens; add-on: designed crown lobes and visible woody scaffold, not just more small pieces | 2 |
| 4 | Rocks: 43 stones of 50 to 72 flat faces, all one grey-green, the standing rock reads as a crystal; sunk only 22 percent | 9 | More unequal planes with worn edges (or softly weathered, see the one choice), buried a third, grouped in threes, real rock surfaces with per-stone variation, moss at the feet | add-on: stone has short mineral marks, no long streaks; real gardens: half-buried, grouped 3/5; ours: scanned rocks | 1, 3, 2 |
| 5 | Gravel court: dark pink-brown (brightness 0.115 to 0.25, lowest contrast of any big area), reads as a rug; bare cut-off edge | 7 | Pale grey-white granite with black flecks (start near 0.45 to 0.6 and judge by value study); rake lines straight, about 12 cm apart, about 1.5 cm high, rings round the three rocks; stone or pebble edge; moss collar round each rock | real gardens (Kyoto survey); scene | 3, 1, 2 |
| 6 | Pond: opaque dark teal, no depth, odd white reflections of the screens; bridge: identical smooth pink boards, four piers touch nothing, boards separate and floating, corner boards poke out | 12 | See-through water with a bed and shore detail but crisp reflections; silver-grey boards with per-board tone and wear; piers lifted to the boards, stringers under each run, corner boards trimmed | add-on: thin water sheet, keep crisp reflections, support must be real; real gardens: plank bridge on short piles | 2, 3, 1 |
| 7 | Roof: crushed black (5th percentile 1 of 255), too uniform, the kit cannot reach its materials | 5 | Scan colour and roughness on the add-on's own tiles (keep the real geometry); moss only on shaded lower rows and ridge gaps; pale marks only (dark marks vanish on 0.14 brightness) | ours: kit fix 1; real gardens | 3 and 4 |
| 8 | Lantern: cap and finial float 14 cm, 7 mm gap at the post, glow box buried in the stone (flat white cut-out, "hourglass"), stack of boulders | 1 (focal) | Carved six-sided lantern, hollow firebox with an opening, curled-corner roof, no gaps, dim warm reddish light, patina and moss, half hidden by shrubs | real gardens; delivery check | 1, 4, 3, 2 |
| 9 | Walls and plaster: clean cream, thin cap floating 6.5 cm above the wall, wall just ends | 4 | Clay wall slightly wider at the base, overhanging tile cap seated on the wall, stains, rain streaks, damp foot (kit sheets on all four walls now) | real gardens; ours: kit fix 2 | 1 and 3 |
| 10 | Finish: no vignette, hard sky, no bloom | whole picture | Value study at thumbnail size, vignette, mild bloom only on screens and lantern, compare side by side with the original | ours; add-on: whole-image comparison first | 4 |
| 11 | Small: lime grape-ball pine; orange-chip fallen leaves; one-colour bamboo; near-straight stepping stones at even spacing; basin is a bare stone; moss runs straight to the water; two inside-out bamboo pieces | about 4 together | Dark flat needle pads on bare limbs; few small mixed leaves; used-looking bamboo; zigzag irregular stepping stones 3 to 6 cm high; basin with front, candle and bucket stones, spout, ladle; shore stones and pebble edge; fix the two bamboo pieces | real gardens; add-on: chiselled form rule for round parts | 1 and 2 |
| (must-do, cheap, not seen at hero distance) | Floating and gap faults: bridge piers, veranda step 23 cm in the air, wall caps 6.5 cm up, lantern, deck planks and plinth top in the same plane (77 faces fight), plaster/post overlap, roof 22 cm off the posts | tiny | Reseat everything; run the delivery check again | add-on: support is not clearance; delivery check | 1 |

---

## 4. Where the add-on's advice and ours disagree, and which I would follow

| Topic | Add-on says | Our studies / real gardens say | I would follow | Why |
|---|---|---|---|---|
| Overall look | Painted: broad brushed colour passages, chiselled flat planes, no photo look; technical passes are not art acceptance, the person decides | Street work used photo-scanned surfaces and you said the scanned bricks "look incredible"; real gardens are realistic | Both, as a switch (see section 5). Default if you say nothing: realistic | It is your choice; the plan makes both so you can pick by eye |
| Pigment tool vs scans | Pigment tool paints broad wood and plaster colour passages (colour only, timber and plaster only, one material per object) | Put scanned surfaces down first, then the kit on top | Scans plus kit for the realistic look; the pigment tool only for the painted look. They cannot be mixed on the same object (pigment needs a noise colour feeding Base Color) | Different jobs for the same objects |
| Rock shape | "No rounded smooth curves. Just edges and flat surfaces that approximate a curve" (your recorded words from 17 October); no subdivision or smoothing | Scene and real gardens: 50-72 flat faces look like crystals; stones are weathered, rounded, half-buried | Painted look keeps flat planes but makes them many, unequal and worn; realistic look softens and weathers them, keeping sharp creases only on big edges | Decided by your answer in section 5 |
| Smoothing | Smoothing and subdivision are the rejected look for forms | Scene: ground and pebbles are flat-shaded; shade them smooth | Smooth-shade the ground and pebbles (they are terrain, not designed forms); do not smooth architecture or lantern | Avoids the rejected look where it matters |
| Rake depth | (no figure; the 1.6 cm relief is our own) | Scene: deepen to 2.5 to 3 cm for contrast. Real gardens: low, crisp, about 1 cm, tines only 5 cm long | Keep about 1.5 cm, change the spacing to about 12 cm | The golden-hour sun is 9 degrees above the horizon, so 1 cm already throws a 6 cm shadow; 2.5 to 3 cm looks ploughed |
| Rebuilding the ground | Refine the grid rather than weaken the masks (38 percent of squares frozen, relief 0.158 m not 0.20 m) | Scene: ground is a noise carpet; stones were seated on today's heights | Do not rebuild the terrain; smooth-shade it, put the scan on it and add 3D moss | Rebuilding re-seats every stone; the gain is small next to the surface |
| Moss | The add-on's moss ignores shade (rank match 0.15); live scatter has stable records, keep-clear width for the path | Kit moss follows shade and damp | Both: 3D moss and tufts from the add-on scatter at rock feet and damp edges; kit moss as texture where shade says; never double on a scan that already carries moss | They fill different gaps |
| Atmosphere | Haze that erases the hall is rejected; depth is colour and selective edge loss, not blur | Mist idea for later; hills fade into haze | Colour-stepped ridges, no veil over the hall; mist only as a limited volume in a later variant | The earlier thin golden haze was already tried and dropped |
| Light test method | One change at a time on a fixed camera, lights alone first, then air | Light groups: draw once, rebalance after | Both: fixed camera and one-change tests for the main lighting, light groups for the final rebalancing | Cheap and complementary |
| Lantern | Part of the add-on's stone family; a "real reflection" is not automatically good | Real gardens: carved lantern, seldom lit, dim glow; scene: glow buried | Carved lantern built by hand (the add-on's stone tool cannot make a carved, hollow lantern); dim warm glow; the pond reflection checked in the picture | The add-on does not cover this part |
| Renderer | Cycles for light behaviour and material response | Cycles where lights are on (your rule); EEVEE cuts lamp reach unless its light threshold is lowered | Cycles for every final | Your rule; this scene has glowing screens and a lamp |
| Installed texturing skill | (not the add-on) | Its default says "EEVEE finals" | Override with your rule | Predates the rule |
| Evidence | Record engine, samples, seed, view transform, file hashes; keep failed attempts | (nothing) | Do it; it is cheap | Matches how the street was done |
| Where they agree | Fix support faults; stone identity (short marks); selective edges; connected glow, not a dark spotlit garden; moss readable by contrast | Same | Same | |

---

## 5. The one choice only you can make about the look

**Which look should be the garden's main one: the add-on's painted look, or realistic like the street?**

* **A. Keep the add-on's painted look.** Rocks and forms stay chiselled (flat planes of unequal size, your own 17 October rule). Colour is laid in a few broad brushed passages (the add-on's pigment tool on hall wood and plaster, broad hand-made passages on ground, stone and gravel), no photo surfaces, no weathering kit. It reads as a painted illustration and follows the add-on's rulebook; it gives up the "looks real" quality you liked in the street.
* **B. Go realistic like the street.** Photographed surfaces from Poly Haven (free to use, no credit needed), the weathering kit on top, rocks softly weathered and half-buried, Cycles light. It reads as a photograph and matches the street; it gives up the faceted painted identity of the add-on (the add-on still builds the roof, planks, ground and moss).

Because drawing is paid by the second and the shapes are shared, the plan **builds and draws both** hero pictures and lets you choose by eye. The only things that differ are the rocks' form and the surface stack (builders 1 and 3). **If you say nothing, the realistic one leads**, because you praised the scans, all four studies point that way, and the painted one is still delivered next to it.

(One small thing to confirm if you care: the weathering kit assumes north is the +y direction and a latitude of 35 degrees for its shade logic. The scene's sun is fixed by the sun lamp, so the plan makes the kit follow the lamp instead.)

---

## 6. Rendering: Cycles on RunPod, per second

**Engine.** Cycles for every final (renderer rule: Cycles where lights are on; they are: four glowing screens with area lights, a lantern, a pond mirroring the screens). EEVEE only for quick looks. If you consider golden hour plain daylight, EEVEE would draw this in about a second on a rented card; that is a one-line change.

**Settings for the finals.**
* 2400 x 1600 like the original; Cycles on the graphics card (OptiX, else CUDA). The saved scene says CPU, and the choice lives in Blender's settings, not in the file, so the render job switches it and proves it with one tiny Cycles picture first (an earlier community machine could not use the card for Cycles; two stores worked).
* About 384 to 512 samples, adaptive, with a denoiser (the original used 180 samples, 13 minutes on the shared computer). Caustics off. AgX with the "Punchy" look and exposure +0.5 as in the original, unless the value study says otherwise.
* **Light groups**: sun, sky/world, cool fill, hall glow (screens and their lights), lantern. Saved as a multi-layer EXR beside the PNG, so the glow can be rebalanced and the picture re-graded after drawing, for free. Check that the groups add up to the normal picture. Light groups are Cycles-only.
* Record engine, samples, seed, view transform and file hashes for every picture and keep failed attempts (add-on advice).
* The add-on needs Blender 5.2.2 pinned, the add-on 0.2.1 plus the small loader, and, for live scatter, a three-line patch kept outside the add-on. Only the saved final scene file has to travel (it is self-contained); the kit, scans and stage files travel as one bundle.

**Pictures.**
1. The original golden-hour view, 2400 x 1600, realistic look.
2. The same view in the painted look.
3. A second view from the veranda looking out over the pond (camera about (3.6, 5.3, 1.55) looking at about (-2.5, 0.8, 0.55), 24 mm), realistic look. This is the story's own next idea; it needs the all-round backdrop and the repairs, so it also tests them.
4. Stretch, if the lantern opening works: the blue evening view with the lantern lit (needs Cycles; sun off, deep blue graded world, screens and lantern glowing, lantern light dim). Skipped on purpose: morning mist (hides the weak hills instead of fixing them), fish (water must first be see-through and the plan makes it so, but fish are optional), tea house, bamboo spout beyond the basin set.

**Time and cost (estimates only, not measured on this scene).** Two scalings give 26 to 47 seconds (from street pictures) and about 3 minutes (from the 12-second Cycles test) for one 2400 x 1600 picture on an RTX 4090 at modest samples; at 512 samples this scene could take several minutes. A card costs roughly US$0.3 to 0.9 an hour (4000 Ada about 0.28, 4090 about 0.89 on the cached store), so one picture is cents. A whole session (start-up about 25 to 150 seconds, proof picture, two preview rounds at 1200 x 800, four finals) is probably 30 to 60 minutes of machine time, so roughly US$0.3 to 1 to a few dollars at the upper end. Ask the live price before starting and log seconds used.

**Paying only for seconds used.** Your RunPod set-up note says a machine ends itself after 30 minutes with no request, which would bill up to half an hour after the last picture; a newer pay-per-second endpoint (task 77) is "being set up now" and I did not read it. The final step must use whatever that endpoint's instructions say, and in either case **end the machine right after the last picture** and note the seconds. Nothing is rented until the final step.

---

## 7. How the work is split (shared rules for all four builders)

**One starting file.** `astra-work/out/courtyard_final.blend` (read-only, never save over it). It matches the golden-hour photo exactly (same fingerprint `04d47e70071f8e32ccd0ccd1` as the later preview files, checked dot for dot against the photo), it is self-contained (no add-on, no pictures needed), and opens in a second. The scene can be rebuilt from `/home/user/Music/japanese-courtyard/build_courtyard.py` in about 10 seconds (it draws at the end, so do not run it without cutting that out; the saved file is simpler).

**Stage files, not edits.** Nobody edits the build script, the saved scene or each other's files. Each builder delivers `stage_<name>.py` in their own folder with one function `apply(options)` that works on the already-open starting scene and prints a short report listing objects created, changed and deleted. The final step runs them one after another: shapes, then life, then surfaces, then weathering, then light. So each builder tests alone: open the starting file, run their stage, save a small test file in their own folder (compressed, under 20 MB), check, and write pictures.

**Switches.** `options["look"]` is `"real"` or `"painted"`. It changes only builder 1's rock treatment and builder 3's surfaces. Everything else is shared.

**Who owns what (existing objects).**

| Builder | Folder | Owns |
|---|---|---|
| 1 Shapes | `PW/garden/shapes/` | Geometry (and where parts sit) of: all `Astra / varied planks*` runs, `Bridge pier 0-3`, `Veranda step`, `Veranda step, lower`, `Stone plinth`, `Hall posts`, `Hall beams`, `Hall plaster`, `Eave soffit`, `Hall roof` (only hidden carrying parts), the three wall objects and their caps, `Rock 0-4`, `Gravel rock 0-2`, `Pond edge stone 0-14`, `Stepping stone 0-7`, the seven lantern parts (`Lantern base/post/gallery/firebox/cap/finial/window glow`), `Water basin`, `Basin water`, `Raked gravel court`; plus anything new that is stone, timber or architecture (kerbs, stringers, shore stones, basin stones, cap tiles) |
| 2 Life | `PW/garden/life/` | Geometry and materials of: `Maple *` (leaves, inner mass, trunk, branches), `Pine *`, `Bamboo stalks/leaves/fence`, `Fallen leaves`, `Lily pads`, `Lotus blossoms`, `Pond water`, `Astra / moss grouped bodies` and its four `moss tone` materials; the shading and any added scatter on `Astra / Courtyard receiving ground` and `Astra / pebbles grouped bodies`; everything new that grows (tufts, shrubs, iris, moss collars, leaf litter, pond bed, pebble fringe) |
| 3 Surfaces and weathering | `PW/garden/surfaces/` | Materials only, no geometry: `Moss and earth`, `Raked gravel`, `Plaster wall`, `Dark timber`, `Beam timber`, `Plinth stone`, `Wall cap tile`, `Bark`, the 43 stone materials, the roof materials (inside the roof's geometry nodes), the 56 plank tone materials, the four `pebbles tone` materials; the weathering kit and its courtyard set file |
| 4 Light and render | `PW/garden/light/` | World, all lights, emission materials (`Shoji paper glow`, `Lantern flame`, `Open room, dim`, hill haze materials, `Far hill`), `Hills, far/middle/near`, `Dark plain`, camera and `Focus`, render settings, view-layer light groups, compositor, the render job script |
| 5 Final | `PW/garden/final/` | Puts it together; owns nothing else |

**Names and labels (so the stages do not collide).**
* Nobody renames or deletes an object they do not own. The kit's set file finds things by name patterns (`^Rock \d+$`, `^Stepping stone \d+$`, `^Pond edge stone \d+$`, `^Lantern (base|post|gallery|firebox|cap)$`, `^Hall posts$`, the wall names, `^Astra / varied planks`), so owners keep today's names and new objects follow the same style.
* Every new object gets two custom properties: `garden_owner` (shapes, life, surfaces, light) and `garden_role` (one of `stone.natural`, `stone.dressed`, `timber.deck`, `timber.frame`, `roof.tile`, `wall.plaster`, `wall.cap`, `ground.earth`, `ground.gravel`, `growth`, `water`, `glow`, `leaf`, `bark`). Builder 3's stage reads these so it covers objects made by builders 1 and 2 without knowing their names. New objects go in a collection named `G1 shapes`, `G2 life`, `G4 light`.
* A mesh keeps its material slots when it is reshaped; a new object gets one placeholder material named `GARDEN placeholder <role>` for builder 3 to replace.
* The glow box keeps the name `Lantern window glow` and the material `Lantern flame`; builder 4 sets how bright it is.

**Frozen things.** Hall, pond outline, bridge route, lantern spot, basin spot, camera and sun direction stay where they are (the original view must still compose the same). Builder 1 may nudge rocks and pond-edge stones up to 0.5 m and change their yaw and size by up to 15 percent, and may re-lay the stepping stones inside the same corridor. Builder 2 reads positions from the open scene, so it sees builder 1's changes.

**Using the add-on.** It is needed only when a stage calls it (stone tool, plank tool, live scatter). Load it through `/home/user/Music/japanese-courtyard/astra_loader.py` from the 0.2.1 unpack at `astra-upload-021/` (read-only; set `PYTHONDONTWRITEBYTECODE=1` so nothing is written next to it). For live scatter, copy the add-on (4.3 MB) into your folder and apply `PW/garden/addon/tests/native_scatter_blender_5_2.patch` to the copy; never to the upload.

**Limits for everyone.** Read-only everywhere except your own folder (60 MB limit; delete scratch; disk has under 1 GB free) and the pictures folder `PW/29 Japanese garden - pictures/` (JPG under 400 KB, names start `29 `, e.g. `29 Shapes - ...`). Blender 5.2.2 headless (`-b --disable-autoexec`, `xvfb-run -a` if anything is drawn). No rendering bigger than a small preview (Workbench or EEVEE, under 2 minutes; hide the leaf and moss objects for previews because the hooked scene takes over 3 minutes per EEVEE picture here). No paid calls, nothing from `~/.runpod`, your name and email never in any outside request. Read the matching Scenario skill in `/home/user/Music/.claude/skills/` first (and use Cycles, not the skill's old "EEVEE finals" default, for anything about final look).

**Every builder:** keep the work in priority order so that stopping early still leaves a coherent result; run the Scenario delivery check on your own objects before handing over (method and wrapper in `PW/garden/scene/scripts/run_gate_courtyard.py` and `PW/garden/ours/work/delivery_check.py`); say plainly what you saw and what you only measured; hand over `stage_<name>.py`, a short test report in `out/`, and one or two small pictures.

---

## 8. Builder 1: shapes (repairs, lantern, rocks, gravel, walls, details)

Folder `PW/garden/shapes/`. Skills: scenario-blender-expert (delivery check), geometry-nodes if needed.

In this order:

1. **Repairs (must, cheap).** Re-measure first (the studies disagree slightly): raise the four bridge piers to the deck underside (gaps 2.2, 2.5, 5.0, 4.4 cm; the middle piers up to 7 cm); two stringers under each bridge run; trim the corner boards to the run width; seat the veranda step on the ground and the lower step on the ground, the upper on it, touching the deck (it floats 23 cm); wall caps down 6.5 cm onto the walls; plinth top 1 cm down (or deck planks 1 cm up) so 77 faces stop fighting; 2 to 5 mm inset where hall plaster meets posts; hidden ridge beam or rafters so the roof is carried (22 cm gap now); check the shoji bars and paper for shared faces; run the delivery check again. Expected afterwards: no floating parts except the loose leaf, moss, pebble and pad scatters, which are floating by design.
2. **Lantern.** Rebuild as one carved type (six-sided, thick post with ring, hollow firebox with one or two openings, roof with curled corners, finial), same spot and about the same height, part names unchanged, no gaps, glow box 3 cm proud of the opening so it reads as a lit window, not a buried cut-out. By hand (the add-on's stone tool cannot make a carved lantern); keep it clean enough for the weathering kit.
3. **Rocks.** Keep the add-on's rocks as the starting shape and give them more unequal planes (split, then displace with a rock noise; keep creases on big edges). `look="painted"`: keep flat planes, many, unequal, worn along real edges, no smoothing. `look="real"`: soften and weather them (bevel and a little smoothing between planes, veins as ridges). Both: bury about a third (today 22 percent), group in threes with different heights (small nudges only), keep no stone wider at the top than at the base, never in a row. Include the lantern base, basin and pond-edge stones.
4. **Gravel court.** Rake lines straight and parallel about 12 cm apart, about 1.5 cm high with crisp crests and a few millimetres of wobble, curved rings following the outline round the three rocks with short cross-lines at the ends. A line pattern needs at least four mesh squares per line, so use a 2.5 cm mesh over the court (about 100,000 faces; today it is 4.5 cm); if the lines turn wavy at the hero camera, widen to 14 cm. Edge: low stone kerb or pebble strip on the pond and path side, low timber or wall foot on the fence side. Do not flatten the lines for anyone else (the kit's set file says so too).
5. **Stepping stones.** Re-lay in a zigzag with uneven spacing, tops 3 to 6 cm above the ground, at least 10 cm gaps, one larger stone where the path turns; same corridor and the same names.
6. **Walls.** Keep names and a flat garden-facing front (the kit's wall sheets need it). Clay wall slightly wider at the base (3 to 4 degrees), real overhanging tile cap seated on the wall with a row of half-round tiles; no gap.
7. **Basin set.** Front stone, candle stone on the right, bucket stone on the left, a pebble drain, bamboo spout and ladle (basin at about (4.4, 4.0)).
8. **Shore.** A few shore-stone groups set partly into the water.

Not yours: materials (builder 3), moss and pebbles (builder 2), lights (builder 4). Report each repair as before and after numbers.

---

## 9. Builder 2: life (maple, ground cover, pond, pine, bamboo)

Folder `PW/garden/life/`. Skills: scenario-blender-geometry-nodes, scenario-blender-texturing-shading.

In this order:

1. **Maple.** Leaves 5 to 12 cm wide (today 20 to 34), seven lobes with a serrated edge and a slight bend, three to six leaf shapes instanced with geometry nodes (about 60,000 or more leaves; instances are cheap in Cycles), colours from deep red through orange to a few yellow-green and brown, a few stems. Crown as separate horizontal layers with windows through them so you can see the trunk and the woody scaffold and so the low sun shines through (leaf material with some translucency); keep the dark inner mass but shape it as layers. Keep one saturated hue as the picture's focus. Add-on rule: a designed crown with real divisions, not just more small pieces.
2. **Ground cover.** Smooth-shade the ground and pebbles. With the add-on's live scatter (patched copy): moss at the feet of rocks and stepping stones and where dark damp meets pale stone (on the lower sides of rocks, sloping up to the stone; round the three gravel rocks as a collar slightly above the gravel), a third plant kind (tufts), a pebble fringe along the gravel edge and the pond; keep-clear width round the stepping-stone path of half the path width; stable ids; source shapes with bottoms near z 0 and no parent; never moss on the raked area. Make moss mottled yellow-green to deep green to brown rather than one lime colour; check it reads by contrast against the ground, not by size. Do not rebuild the terrain. After builder 1's changes the positions are read live from the scene.
3. **Pond.** Water you can see into near the shore (transmission, IOR 1.33, a little dark teal absorption), a dark bed with pebbles and lily stems about 0.3 m down, a thin sheet near the bank height, reflections still crisp (do not make it matte, do not paint cyan); a few iris or sweet-flag clumps near the bridge; lily pads in uneven shapes. The white screen reflections are real: leave them for builder 4 to balance by brightness.
4. **Pine.** A few separate flat layered pads (unequal flat planes, not smooth blobs) in dark blue-green on bare curved limbs with open space between; keep the trunk and limbs.
5. **Planting.** A few clipped round shrubs between rocks and beside the lantern (loose groups of two, three or five), placed so the lantern's opening is still visible from the hero camera (check with a ray from the camera).
6. **Bamboo and litter.** Fix the two inside-out bamboo pieces; fence with slightly different culm colours and tone; fewer, smaller, mixed-colour fallen leaves clustered under the maple and along the moss edge, none on the gravel.

Not yours: stone, timber and plaster materials, bark (builder 3), the light (builder 4). Check scatter counts against density times area, and say the total face count (keep the whole scene under about 3 million faces).

---

## 10. Builder 3: surfaces and weathering (realistic stack first, painted stack second)

Folder `PW/garden/surfaces/`. Skills: scenario-blender-texturing-shading, scenario-blender-uv-baking (only for box projection and no-UV advice).

**Part A: realistic stack (`look="real"`).**
* Download Poly Haven 1k maps (Diffuse, Rough, OpenGL normal, Displacement) from the list in `PW/garden/ours/polyhaven_shortlist_CC0.json` (all CC0, no credit needed; ask with a generic agent name, never your name or email); about 1.5 MB per surface, keep what you use, delete the rest, pack the images in the test file (folder limit 60 MB). Pick by drawing a small test plate of each, not by thumbnail.
* Surface by surface, biggest first: ground (forest-floor/moss scan, broad unequal passages with quiet middles and a macro variation so tiling is not seen; box projection because nothing has UVs); gravel (pale grey granite with black flecks, start near 0.45 to 0.6, the scan's height only as a bump so the rake stays real); rocks and lantern (Rock Boulder Dry, Rock 08, Lichen Rock on shaded sides, per-stone variation using the object's random value; box projection with height as bump, never normal map plus bump together); roof (Grey Roof Tiles colour and roughness on the add-on's tiles by replacing the shader inside the three roof materials, world-position mapping because the tiles are instances, mean brightness well above today's 0.14); veranda boards (Weathered Planks, rotated to run along y, silver-brown to dark amber, not salmon); bridge boards (Wood Planks Grey, silver-grey); per-board variation through the 56 plank tone materials (give each its own tint and mapping offset); hall posts, beams, shoji bars (Hinoki aged, or Dark Planks); hall plaster (White Stucco dulled to grey-cream); garden walls (Worn Plaster Wall, Worn Cracked Plaster at the foot; do not add kit moss on a scan that already carries moss); plinth (Japanese Stone Wall); bark (Trident Maple Bark, Pine Bark); pebbles (Clean Pebbles).
* Colour is sRGB; roughness and displacement are Non-Color; use the roughness map. Replacing the 43 stone materials also removes the need for the kit's special stone adapter.

**Part B: weathering kit on top.**
* Copy `PW/garden/ours/kit_patched/` (it has the three blocker fixes plus the extra dial `moss_vs_stone`: roof materials inside geometry nodes now found; each wall gets an explicit front so all four sheets face the garden; every layer honours per-material dials). Do not touch the film's kit or `kit_orig`. Verify the patches apply and that the street still reads the same.
* Look: the "kept" look as base. On: dust-and-algae film, runoff under caps and eaves, damp foot at wall, post and stone feet, plaster hairlines and stone chips, wall growth (the main layer), dirt on gravel, earth and stones, patch moss on earth and stones. Off: steps, paint, ground cracks, iron, puddles and wetness, joints, rubbish. Weeds near zero, 3D growth layer off (builder 2 owns plants). Wet means darker, greener, glossier, no puddles.
* Per-material first guesses to tune by eye: lichen about off on plaster and wood and strong on natural stone; moss weaker on plaster, stronger on stone and roof; `moss_vs_stone` about 0.9 to 1.0 on grey stone; on dark surfaces (roof, dark timber) pale marks only; keep dark grime to about a quarter of a surface.
* Fix the remaining kit faults in your copy: role `bark` must also match curves; `roof.deck` matches no object; `never` patterns that match nothing; the apply step needs the kit's `integrate` folder even with no earlier layers, so send the whole kit folder or remove the dependency; make the set follow the sun lamp's real direction.
* Stage reads `garden_role` properties so new objects from builders 1 and 2 are covered.
* A local picture of the weathered scene is too slow here; prove structure instead (role map counts, node-group sizes, which materials and walls got which layers, role dials landing on the right objects) and write a preview request list for the final step (hero and close crops of roof edge, long wall, gravel, rocks, bridge).

**Part C: painted stack (`look="painted"`), time-boxed to about a third of the effort.** No scans, no kit. The add-on's pigment tool on hall posts, beams, shoji bars and plaster (palette mean at today's colour, strength about 0.5 to 0.75, grain axis set per object; it needs direct Principled materials with a noise colour feeding Base Color and colours one slot only); broad hand-made passages for ground, stone and gravel (four to six unequal directional groups, quiet middles, firm and lost edges, warm lit against cool shadow, no round camouflage islands, no giant clean polygon bands); stone with short mineral marks and chalky fields, never long streaks; planks with interrupted wear running along each board. Check material overrides after pigment (it creates per-object bindings).

Not yours: any geometry; leaf, water and moss-tone materials (builder 2); light and glow strengths (builder 4).

---

## 11. Builder 4: light, backdrop, camera and render job

Folder `PW/garden/light/`. Skills: scenario-blender-lighting-rendering (value studies, light groups, compositor in Blender 5.x).

In this order:

1. **World and hills.** Replace the hard-wired orange with a graded sky (warm horizon band, blue above); put the sky's sun and the sun lamp on the same direction; rebuild the hills as four or five ridges that go all the way round (today only about 190 degrees behind the hall), nearer ones darker and cooler, far ones paler and bluer, soft tops by colour gradient, plain and ground continued to the horizon; the south and the veranda view must not show empty sky and a dark slab. Keep them real geometry so parallax stays.
2. **Light.** Cool the ambient and the shadows (the uniform orange wash goes away), keep the low warm sun raking across the gravel (9 degrees: every rake ridge casts a thin shadow), back-light the maple, one rim on the sun side of the maple and hall edge, keep a broad connected glow from screens and lantern with a few dark interruptions (not a dark garden with spotlights). The lantern light stays dim in the golden-hour view. Test lighting as you go: fixed camera, one change at a time, a value study at thumbnail size side by side with the original photo, and targets from our brightness study: sky well below the screens in brightness, edge-to-centre about 0.8, roof band lifted (5 percent of it is near black today). Check the pond's reflected screens by actual pixels; light fields like transmission and volume factor did nothing in 5.1.2 Cycles, so use object ray visibility if you need to separate things.
3. **Light groups and finish.** Sun, sky/world, cool fill, hall glow, lantern; multi-layer EXR beside PNG; compositor recombine check (groups add up), vignette, mild bloom only above 1.0 (screens, lantern); no blur. Caustics off.
4. **Cameras.** Rename the hero camera to `photo` (the kit's set file calls it that; today it is `Camera`), unchanged lens and position; add `veranda` (about (3.6, 5.3, 1.55) looking at about (-2.5, 0.8, 0.55), 24 mm); check the sun is not a problem in that view.
5. **Evening variant** (function `apply_evening()` applied after the main stage): sun off, deep blue graded world, cooler dimmer fill, screens kept, lantern light 1800 to 2200 K and dim with the window about 3 to 6 stops above its surroundings, pond reflection of the lantern checked.
6. **Render job script** `render_job.py`: inputs blend path, camera, size, samples, output; switches Cycles to the graphics card (OptiX, else CUDA), prints and checks the device, sets light groups, writes EXR and PNG, logs seconds, engine, samples, seed, view transform and file hashes. Test locally with a dry run and a Workbench-size picture only (no paid call, no big render).

Not yours: geometry of anything but hills and plain, materials other than emission, hills and sky.

---

## 12. Step 5: integrate, render, check (after all four)

Folder `PW/garden/final/`. This step gets its RunPod instructions separately.

1. **Chain and conflict check.** Open the starting file, run the stages in the order shapes, life, surfaces (with `look`), weathering, light; save `garden_real.blend` and `garden_painted.blend` (compressed, images packed). Confirm each stage only touched its own objects (compare object and material lists before and after by `garden_owner`), the names the kit relies on still exist, and no object lost its materials. If one stage breaks the scene, run the others and report which; each stage is built to be skipped.
2. **Delivery check** again on groups (buildings, stones, roof realised, each scatter alone), plus the wall sheets (all four facing the garden) and a quick look for objects that now overlap.
3. **Preview round on RunPod** (small, cheap): one tiny Cycles picture to prove the graphics card, then 1200 x 800 previews of the hero in both looks and the veranda, plus 100 percent crops of: maple, ground, gravel and rock feet, lantern, bridge, roof edge, long wall. Judge as the add-on says: thumbnail first against the original, then crops. Fix, preview again once or twice (cheap).
4. **Final pictures** (section 6): 1, 2, 3, and 4 if it works. Multi-layer EXR with light groups beside each PNG; regrade from the groups if the glow needs it, instead of drawing again.
5. **Checks on the pictures.** Maple reads as leaves not confetti; ground is not camouflage; gravel is pale with visible lines; nothing hovers; roof is not black; lantern has a lit opening; sky is not one flat colour; screens still glow; hall not erased by haze.
6. **End the machine** right after the last picture and report seconds and cost.
7. **Report in plain words**: original beside new for each picture, what was done, what was only measured and not seen, what was skipped, the two looks and which one leads, and where everything is saved. The add-on advice is to treat all checks as a checklist and not as proof of quality: your eyes decide.

---

## 13. Risks and what is not known

* **No picture exists yet of the kit fixes or most fixes**; the local computer is too slow. The first look comes on RunPod, so the plan has a cheap preview round and every stage can be skipped on its own.
* **Stages stacking** can interact in ways nobody has seen (rocks reshaped after materials chosen, wall shape vs wall sheets, new objects without materials). The naming rules, the `garden_role` labels and the conflict check are there for that.
* **Look choice unanswered**: both looks are built and drawn; the painted stack is the smaller and lower-priority job.
* **Poly Haven** might be unreachable or slow, and disk is tight (under 1 GB free). 1k maps only; if scans cannot be fetched, fall back to the procedural recipes in the cookbook.
* **Scans at garden distance**: they looked incredible close up on the street; on a 16 percent ground area, tiling is the danger (macro variation needed).
* **Add-on on Blender 5.2**: it declares 5.1 only; live scatter needs the patch kept outside the add-on; the pigment tool refuses the add-on's own planks, stones and roof (modifiers); it colours one slot per object.
* **Estimates** of render time and cost are scaled from other tests, not measured on this scene; the graphics card may not run Cycles on some hosts; prove it with one tiny picture.
* **Light-group passes are noisy** unless drawn with enough samples or denoised separately; check the sum against the normal picture.
* **Rake lines** at a 12 cm period may wave at the hero camera; the fallback is 14 cm; actual temple spacing was not found.
* **Weak sources**: roof moss on Japanese tiles, lantern lichen, exact rake pitch, and the "one third buried" figure are single or reasoned sources; the add-on's own evidence reports are not in the upload.
* **Scope**: four builders plus a final step is a lot; each brief is in priority order so a stop leaves something usable.
