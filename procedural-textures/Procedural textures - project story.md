# Procedural textures - project story

## The goal

Make the textures, materials and maps of the six surfaces you uploaded (brick, roof slate, aged wood, rusted metal, muddy ground with puddles, gravel) with Blender's own
procedural tools (nodes, geometry nodes, curves, modifiers, physics), research how people do this today, and save recipes and guides that say what each tool does and how its
settings change the picture. In your words: "textures that can be scaled to larger sets with lessons that are transferable to other types of surfaces. Pixel accuracy isn't the
end goal, but it is required for this first step." Then: keep colour and fading, damage and moss on separate layers inside the recipe, with your picture used only as a guide.

## Where things stand

- **Done:** research (five tested guides), a check of the three extra tools you found, and all six surfaces rebuilt from Blender recipes, each scored dot for dot against your
  picture, each re-checked by an independent checker (every number reproduced exactly; no recipe reads your pictures).
- **Closest results:** slate and metal reach "close"; wood, mud, brick and gravel reach "layout". The closest versions are big descriptions (400-500 KB) that store your picture's
  paint patches one by one, which is closer to tracing than to procedural making. The small settings-only versions (2-8 KB) get the structure right and make new tiles.
- **Cookbook done and checked:** start at `cookbook/06 Cookbook - start here.md`. Eight tool guides (pattern makers, shapers, seamless tiles, relief, geometry, painted look,
  baking and checking, descriptions), a new-surface checklist, all twelve surface guides (brick and gravel now written, the checkers' corrections applied), an overview picture.
  An independent checker followed every link (320, none broken) and re-read 55 numbers against the files (all match after 9 fixes).
- **Slate in layers done and checked:** one Blender recipe made of six named parts (layout, colour and fade, damage, moss, outline and shadow, combine), driven by
  49 hand-set settings (1.7 KB), never fitted to your picture. It reads as the same material (same-kind colour score 0.70 on the default tile, 0.70-0.77 over five
  sets of random seeds; the aim was 0.8 and was not reached). Each layer can be switched off or re-seeded and only that layer changes (proven). It tiles, makes bigger
  areas of new slates, gives the same picture at three sizes, and its colour, damage, moss and outline parts ran unchanged on a brick layout. Two independent checks:
  the claims hold; an art director would still see a different hand (see log 12). Pictures: `12 Slate in layers - pictures/`.
- **Honest gaps the checker found:** nobody has yet followed the checklist on a brand-new surface from scratch (every transfer reused an existing generator); there is no
  starting template for writing a new generator; the tool guides mostly teach shader nodes while most generators here are "painters" of flat shapes written in Python;
  the same-kind tool needs a reference picture to score a new surface.
- **Reuse answered (log 14):** `cookbook/07 Reuse - which tools work on which surfaces.md`. The paint machinery carries over (55-87% of each recipe's nodes are shared,
  unchanged); the shapes do not (four of five surfaces needed their own layout, and one to three new layers each). Brick, wood, metal and gravel read as the surface; mud only partly.
- **Slate fixes done (log 15):** colour score 0.81 over five seed sets (aim 0.8), checker says "nearly" the same hand; one new fault (straight-edged flat facets on about
  14 slates) needs a small code fix in the colour and fade layer - not started, as you asked to move on.
- **Wood from your maps done (log 16):** the material reads as your wood (score 0.84, the highest of any surface so far) and big areas no longer repeat, but the
  arrangement reads as stacked stone or ledgestone, not long planks - boards are too short and regular. Not fixed (the job allowed two rounds).
- **Generated-mask test done (log 17):** fal shapes plug into the slate's moss and damage layers and the tile stays seamless, but they did not look better than the
  node-made shapes (US$0.35 spent of US$1.00).
- **Wet street done (log 18):** a wetness layer that sits on any material; the street reads wet at dusk in the plate (road sheen, lamp reflections, mirror puddles in the
  gutter, darker wet wall feet). The specularity map is made and travels in the .glb, but it changes the picture very little and does not reach the film as the stage works
  today: what the audience will see as wet is what the painter paints from the wet plate. The painter has not been tried (about 10 US cents; needs your go and a changed brief).
- **Painter test done (log 19):** with a changed brief the painter keeps the wet look (road sheen, reflections in the same places, gutter puddles with mirrored
  windows); the checker says it reads as wet. Not yet usable as the lockout picture: the painter added heavy white clouds, the film's old DRY behind painting shows
  next to the wet road once the camera moves, and the stage's finishing curve darkens the wet road. Cost about 20-28 US cents (more than the 10 I estimated).
- **Nothing running now.**
- **Waiting (not started, as you asked):** realistic moss and damage over the painted colour and weathering.
- **Not tested:** the recipes have not yet been put back into the coal-mine scene.

## How the pieces fit

| Piece | What it does | What it hands on |
|---|---|---|
| `reference/` (not saved here: your uploads) | Your six colour pictures and their maps, with the normal maps flipped to Blender's convention | What everything is compared with |
| `lib/texture_compare.py` | "Same kind of surface?" score from 0 to 1 (a shuffled copy of your picture scores 0.99, another surface about 0.1) | Scores and side-by-side sheets |
| `lib/pixel_compare.py` | "Same picture, dot for dot?" measures and four levels: none, layout, close, exact | Scores and difference sheets |
| `lib/description_audit.py` | Makes sure a recipe's description is a list of numbers, not a hidden picture | Pass or fail |
| `lib/bake_harness.py`, `lib/recipe_tools.py`, `lib/sweep_tools.py`, `lib/contrib/` | Turn a recipe into flat pictures; seamless noise; "what this setting does" strips; the researchers' helpers | Baked maps and strips |
| `research/` | Five research guides (02) and three tool checks (03) | Facts the builders used |
| `recipes/<surface>/` | Each surface: analysis, description, generator, scores, new tiles, bigger area, three resolutions, one surface you did not give, guides (04), builder and checker reports | The recipes and lessons |
| `recipes/slate_layers/` | Slate made of separate layers inside one recipe: `recipe/` (the recipe, settings, controls table), `layers/` (one file per layer), tests, variations, areas, brick reuse | Baked maps; guides (05) |
| `cookbook/` | Tool guides (06), start-here page, new-surface checklist (in progress) | The finished cookbook |

## Word list

- **Tile:** one square picture that repeats without a seam. **Dot:** one pixel.
- **Description:** the short file of numbers a recipe reads. **Size classes:** S up to 8 KB, M up to 64 KB, L up to 512 KB.
- **Same-kind score:** how much two pictures look like the same kind of surface (0 to 1). **Dot-for-dot levels:** none, layout, close, exact.
- **Height map:** brighter is higher. **Normal map:** a picture telling Blender which way each dot of the surface faces. **Derivation ceiling:** how well the height and normal
  can be made from the colour picture alone, the best any recipe can do that way.
- **Layer:** one part of a recipe with its own settings, seed and mask (for example the moss).
- **Layout bundle:** the eleven numbers the layout layer hands to every other layer for each dot (which slate it is on, how far from its edge, whether it is in a joint...).
- **Seed:** the number that picks one random pattern; a new seed gives a new pattern with the same character.
- **Debug view:** a picture of one layer alone (its mask or its colour), baked from the same recipe.
- **Declared link:** an allowed connection between two layers, written in the settings (here: moss avoids fresh damage).
- **Roughness / specularity map:** pictures saying how shiny each dot is. Roughness: low = glossy (wet), high = matt (dry). Specularity: how strong the reflection is.
- **Plate:** the picture drawn once from the 3D street that the image model repaints in the series' style; the film shows that painting shone back onto the 3D set.
- **Stamp sheet:** one generated picture of many separate shapes (moss clumps, chips) that a recipe places one by one.
- **Seamless / half-tile test:** a tile is seamless if moving the recipe half a tile gives the same picture moved half a tile.

## Log (added to, never rewritten)

1. **Set up.** Copied your six surfaces into a reference folder (and the golden-puddle mud, colour only). Built the "same kind" measuring tool and tested it: a shuffled copy of your
   brick scores 0.99, a blurred copy 0.17, another surface 0.09. Built the baking tool (photographs a flat square from straight above, one map at a time; 22 seconds per set), seamless
   noise and cell groups (Blender's own noise does not tile), and the setting-sweep tools.
2. **Research (five helpers, all claims tested in Blender 5.2).** Main findings: Blender's noise, cells and waves do not tile even at whole-number sizes (a shop page claims they do);
   your normal maps are the slope of your height maps with whole-number strengths (brick 6, slate 7, wood 8, metal 5, mud 9, gravel 10) and your height maps follow the brightness
   of the colour, so the colour picture is the real problem; your textures are measurably "painted" (flat patches 21-51 dots, dark outlines 5-12 dots, 8 colours reproduce each
   to a colour error of 3-4.5); photographing and Blender's Bake button give the same pixels; several colour-setting traps. Your own tiles have a mild seam.
3. **Mistake of mine, fixed:** the measuring tool was far too harsh on height (early attempts scored 0 even when the numbers looked alike). Loosened, re-tested.
4. **Your clarification (pixel accuracy first):** added the dot-for-dot tool with levels and difference sheets, and the description checker; changed the method to Analyse ->
   Describe -> Generate -> Compare. A fault in my picture-saving code (grey pictures went into the red channel only) was found by a researcher and fixed.
5. **Your three tools checked:** Ucupaint and Material Maker are real and free and run here with workarounds, but neither got closer than Blender nodes (borrow ideas only);
   MCP Blender Agent is small, cannot set node settings, has no password (skip). "Mixar" is a separate AI version of Blender, not a texture-layer editor.
6. **Six surfaces built and checked.** Closest result per surface: slate close (similarity 0.84), metal close (0.76), wood layout (0.73), mud layout (0.70), brick layout (0.67),
   gravel layout (0.67). New tiles from the small descriptions score as the same kind of surface at 0.74 (slate), 0.71 (brick), 0.63 (wood), 0.57 (metal), 0.40-0.46 (gravel),
   0.38 (mud). Each was moved to a surface you did not give: cedar shingles and fish-scale tiles, cobblestones, deck boards, hull plates, a snowy track and the golden mud,
   pebbles on sand. The checkers reproduced every number exactly and found: brick and gravel never wrote their guides; a refuted claim in metal; golden mud's "close" level is
   inflated (only colour could be measured); the same-kind score barely separates new mud tiles from other surfaces; several wrong numbers in guides.
7. **You said the slate match is close enough;** asked for colour and fading, damage and moss on separate layers inside the recipe, not fitted, picture as a guide only.
   Started (slate first). You also asked to remember realistic moss and damage over the painted layers for later (not started).
8. **Disk nearly full** (1.1 GB left): deleted only re-makeable things (downloaded programs, the checkers' duplicate copies of big pictures). Now 3.2 GB free.
9. **Cookbook started**, and this snapshot saved to the repository (guides, code, reports, scores, descriptions; only the pictures the guides use, shrunk; your pictures and the big
   baked maps left out).

10. **Cookbook written and checked.** Nine helpers: the missing brick and gravel guides (with the checkers' corrections), corrections to slate, wood, mud and metal guides, eight tool
    guides with setting-sweep pictures, the start-here page, one merged new-surface checklist and the overview picture (each surface: yours, best traced copy, small settings-only
    version, a new tile, the surface it was moved to). The independent checker found and fixed 9 wrong numbers (for example mud's "+0.03 SSIM for +50 KB" is really +0.009),
    made words consistent ("seam number" everywhere), and listed the gaps above. Space on the machine stayed above 3 GB.

11. **The machine restarted** while the slate layers were being combined (the four layers were built; the combining was half done, the guides not written). A second helper
    took over: checked every item on disk, re-made only what was missing or cut short (the largest size, the brick reuse views, two steps of the "what each layer adds"
    picture, the 4 x 4 area), tried one more tuning round, wrote the guides and the final report, and trimmed the folder from 436 MB to under the 400 MB limit. Nothing done
    before the restart was lost.
12. **Slate in layers - results.** Six layers inside one recipe, 176 controls in total (49 set for the default tile, the rest at their starting values), every size a share
    of the tile. What each layer adds to the same-kind colour score: joints and flat slates 0.32, + colour and fade 0.48, + moss 0.64, + damage 0.70; without the outline
    and shadow it drops to 0.57. Proven: switching a layer off or changing its seed changes nothing outside that layer (0.0%), except the one declared link (moss avoids
    damage: 0.9-1.6% of the tile, all inside the damage). Same picture at 512, 1254 and 2508 dots; 2 x 2 and 4 x 4 areas of new slates with no visible seam or repeat. On a
    brick layout the colour, damage, moss and outline layers ran with no code change (a 40-node brick layout and 53 settings); it looks like painted brick but is not a match
    to your brick. Eight variations: new seeds 0.77, more moss 0.76, heavily damaged 0.73, big slates 0.75; faded 0.55, dark and wet 0.55, pale old 0.54, fresh and clean 0.46.
    **Failures and limits:** the 0.8 aim was not reached; a 14th tuning round reached 0.80 on the default seeds but only +0.005 to +0.011 on other seeds, so it was not kept.
    About 70% of the height still follows the paint brightness, as in your maps. **The look checker** (judging by eye, measuring, testing fixes) found: paint inside each slate
    is narrow wavy "flame" tongues instead of broad flat bands; too much flat khaki moss (10.8% of the tile against 6.6%) with rows of sharp teeth; chips collect into big
    tan L-shapes at lower corners; near-square corners and ruler-straight rows; under a low light the relief looks like rippled plastic; drippy shadow under each row; a few
    pale outlier slates; one hair-like crack; round lichen dots; "dark and wet" reads as noise and "fresh and clean" loses the painted look. It tested one combined set of
    settings changes on colour-only tiles that moves every measure toward your picture (moss 6.0%, chips 0.8%, less stripy); the relief changes are untested.
    **The honesty checker** reproduced the numbers and found reporting errors, now noted: the like-for-like default score is 0.695 (0.705 in another file), "outline worth the
    most" is wrong for the colour score, the normal-map credit was reversed, "identical" was overstated (1-2 step differences from dither), 176 controls not 49.
    Pictures: `12 Slate in layers - pictures/`: ![](<12 Slate in layers - pictures/12 Slate in layers - your picture, the default tile, the checker suggested fix.jpg>)
    ![](<12 Slate in layers - pictures/12 Slate in layers - what each layer adds.jpg>) ![](<12 Slate in layers - pictures/12 Slate in layers - each layer on its own.jpg>)
    ![](<12 Slate in layers - pictures/12 Slate in layers - eight variations.jpg>) ![](<12 Slate in layers - pictures/12 Slate in layers - same layers on a brick wall.jpg>)
    ![](<12 Slate in layers - pictures/12 Slate in layers - bigger area of new slates.jpg>)

13. **Slate fixes round 1, the tool list, brick from the shared layers; helpers switched to Sonnet 5.5.** You said: apply the checker's fixes and re-bake; and asked how much of
    the tools can be used on the other textures.
    *Slate, round 1* (only settings changed, 49 to 65 entries, no code): same-kind overall 0.705 to 0.730, colour group 0.701 to 0.755 - but almost all of that gain is one
    jumpy measure (feature size); without it the colour group is flat (0.767 to 0.764). Moss 10.4% to 5.7% of the tile (yours 6.4%), tan chips 1.9% to 0.9% (yours 1.0%).
    A fresh checker judged the 11 problems: 4 fixed (L-shaped chips, drippy shadows, hair-like crack, lichen dots), 4 better (paint now flat crisp patches, moss amount
    right with no teeth, rounder corners, relief), 3 unchanged (pale outlier slates, the variations, moss cut straight at side joints), none worse. New problems it found: the
    moss now looks like small crisp khaki flakes (like peeling paint), chips and lip are thin, the relief is flatter than before with faint contour lines, the fine paint grain
    is gone, plain slates stand out. Verdict: "nearly" the same hand; it tested settings for the outlier slates and the grain; a second round is running with them.
    *Tool list* (one helper, reading plus small checks): every measuring and baking tool and the four paint layers, COMBINE and the layer interface run on all five other
    surfaces with no code change; what changes per surface is the layout plus one or two small new layers (brick: grime; wood: cracks and a quarter turn so the paint runs
    along the grain; metal: rivets, moss reused as rust, damage as chipped paint; mud: clods, ruts, stones; gravel: a stone layout). Its own count: 33-34 of 52 tools usable
    as they are or by settings on each surface. It also found that three settings remove the slate "tongues" on brick, correcting a claim in the 05 Lessons guide.
    *Brick from the shared layers*: no shared layer's code changed; new: a grime layer (161 nodes), a brick layout (118 nodes, optional - slate's own layout with brick settings
    scored almost the same) and a small height step (13 nodes) because COMBINE's colour-to-height rule only suits slate. 84% of the nodes are shared. Same-kind 0.654 on
    the best of three random patterns (mean 0.615) against 0.725 for the earlier brick-only recipe, scored the same way; the first quick layered brick was 0.194. Weak points:
    soot as flecks instead of long smudges, pale chip bands along lower edges (a slate habit), cut-paper patch edges, no right-hand shadow. To be ruled on by the checker:
    its height step uses two numbers taken once from your brick's height map.
    *Switch:* you asked for Sonnet 5.5 helpers at extra-high effort from then on. The wood and metal helpers (earlier model) were stopped part-way; nothing was lost, and the
    new helpers continue from their folders. Also found: Blender is not on the helpers' search path (each lost one try); the full path is now in their instructions.
    All of this was put in one download: `13 Finished results so far.zip`.

14. **Reuse of the shared slate layers on five surfaces - results, independently checked.** Brick (log 13), then wood, rusted metal, mud and gravel, each built by one
    helper from the frozen shared layers plus its own layout and new layers, then one checker re-ran every score, re-baked each tile (bit for bit the same), recounted the
    nodes and re-ran the seam test. Same-kind score, layered (mean of three random patterns) against each surface's own earlier recipe, measured the same way:
    brick 0.615 vs 0.725 (behind), wood 0.667 vs 0.606, metal 0.648 vs 0.579, mud 0.507 vs 0.391, gravel 0.622 vs 0.380. Share of the recipe from shared parts:
    wood 87%, brick 84%, metal 78%, gravel 56%, mud 55%. Reads as the surface by eye: brick, wood, metal yes; gravel at a glance (ragged up close); mud partly.
    What carried over: the colour and fade layer, the stacking, the layer interface, baking and scoring; damage, outline and moss on three or four surfaces, sometimes with
    a new meaning (moss as rust on metal, as puddle water on mud). What did not: the layout (only wood could use slate's own, with a 5-node quarter turn) and COMBINE's
    colour-to-height rule, which only suits slate. New layers made: grime (brick), cracks, knots and grain (wood), rivets and edge light (metal), ruts and stones (mud),
    soil and facets (gravel). Every tile is cleaner and flatter than yours up close. **Caveats from the checker:** the first random pattern was the one tuned on (others score
    0.04-0.08 lower); brick, metal and gravel use a height curve measured once from your height maps (2, 24 and 4 numbers), which lifts brick by 0.116 and metal by 0.083 -
    within the "measure once" rule by the letter, but quote those scores beside the plain ones (brick 0.538, metal 0.578, gravel 0.643); the score separates mud and gravel
    from other surfaces least sharply. Missing to make the toolkit general, ranked: recipe wiring and tests not tied to slate, a layout per kind of piece, a settable height
    rule, a light direction in the outline and shadow layer. Pictures: `14 Reuse trials - pictures/` (`14 Reuse - all five surfaces, checked.jpg`).
15. **Slate fixes, round 2, re-bake and checks.** A second tuner used the fresh checker's tested settings plus six new controls in the moss and outline-and-shadow
    layers (code changed in two layer files; independence re-tested: 0.0% change outside each layer's own part). Settings 49 to 73 entries. Colour group 0.822 on the default
    tile and 0.810 over five seed sets (0.740 before), so the 0.8 aim is met on paper - but about three quarters of the gain is the jumpy feature-size measure, and the
    normal group moves about 0.07 up or down depending on how the normal map is made. What each layer adds now: joints 0.41, + colour and fade 0.73, + moss 0.79,
    + damage 0.82; without outline and shadow 0.68. Look checker, round 2: 5 problems fixed (corner L-chips, row shadow, lone crack, lichen dots, moss cut at side joints),
    5 better (paint ripple, moss, slate shape, relief, odd slates), the variations then re-made by the re-baker (v4 "faded" still only reads as a lighter tile).
    **New fault it found:** about 14 slates carry flat straight-edged polygons (a cut-glass look), caused by the broader paint cells - "now the first thing an art director
    would point at"; it needs a code fix in the colour and fade layer (the job allowed only two rounds, so it is not fixed). Also: the lower rim looks frayed with a pink
    fringe, moss is a little pale, relief still weaker than yours. Seamless and non-repeating (half-tile and 2 x 2 tests). Honesty check: claims hold; 11 wording and number
    errors corrected in the guides. Pictures: `15 Slate fixes round 2 - pictures/`.

16. **Wood from your displacement and colour maps.** You said the wood was not good and asked to use the displacement map, then "and the material map", and to make
    bigger surfaces that do not repeat. For wood only, your two maps became the source: a researcher measured them once (five rows of boards, the map does not repeat at its
    own edges, colour brightness predicts height at 0.98, your normal map is the slope of your height at strength 8) and tested methods; the builder made one Blender recipe
    that lays out new rows of boards and gives each board its own random strip of BOTH maps (same place, so colour and relief always match), with flips, small zoom and
    tone changes, painted-out landmarks (knots and other recognisable places shown only now and then), stain stamps and soft masks. One switch gives an exactly repeating tile
    or a big area of new boards. Two rounds, each with a fresh look checker and an honesty checker. Results: same-kind 0.839 with your colour map (0.760 with colour made from
    height; the earlier pure-node wood 0.665 - not like for like, because the new one is made of your own dots). The tile repeats without a seam. In a 4 x 4 area the look
    checker found no repeated knot, crack, stain or board (twin test: 0-2% of pieces have a twin, against 14-18% in round 1 and 100% for a plain repeat). Your colour map is
    worth keeping: colour made from height is flatter and loses the blue-grey and orange. **Still wrong (look checker, round 2, "nearly"):** the layout reads as stacked stone
    or brick, not long boards (boards about 2.5 times longer than high, straight full-height joints, even rows; a source row is only one tile long, so boards cannot be longer);
    a soft blurry dark dash keeps coming back inside boards; a few hard-edged round tone patches where landmarks were painted out; joints too regular. Round 1 also had a false
    claim ("never the same strip as its neighbour": really 19%), fixed in round 2 (1.1%). Six guide errors from the last honesty check corrected by me. Pictures:
    `16 Wood from your maps - pictures/`. Guides: `recipes/wood_from_displacement/08 Recipe ...md` and `08 Lessons ...md`.

17. **Generated masks as layers (your idea), tested on the slate.** fal (flux/dev) made six stamp sheets for US$0.354 by the price list (limit US$1.00; the checker
    confirmed exactly six calls). Asked for white shapes on black, it gave black backgrounds four times out of six, a cream background once, round fluffy balls and square
    paper pieces when asked for drips and thin strips, and once a brown rod and a red scribble; two sheets were usable after cleaning (16 hanging-moss "curtains", and long
    ragged chip strips cut into 20 pieces). A copy of the slate recipe got a stamp mode in its moss and damage layers: per slate, from the layer's seed, a few stamps are placed
    by the layer's own rules (moss from the upper edge and along joints, chips along the lower edge), with random choice, turn, size and mirror. The layer still makes its
    own colour and relief. It is seamless (half-tile test re-run by the checker) and the original slate was never touched. **Result: not better.** Scores within noise
    (0.778 node-made, 0.783 moss stamps, 0.770 chip stamps, 0.775 both). By eye the stamp moss is a hazy see-through wash with a hard flat top, rubber-stamped on every
    second slate; the stamp chips are a tidy continuous "frosting" band; the reference has opaque ragged blotches and lumpy cream islands. Why: the generator gave generic
    silhouettes without the reference's torn brush edge, and the node shapes had many tuning rounds against one hour for the stamps. Worth trying next (not started):
    generate the shapes FROM a crop of your picture; the multiplied mode (node mask times stamp) looked best for moss by eye but was not calibrated. Pictures:
    `17 Generated masks test - pictures/`; notes: `mask_test/notes - generated mask stamps test.md`; spending: `mask_test/spending.md`.
18. **The street view set: wetness layer and specularity map.** You asked to move on to the street test, which needs a specularity map for wetness. A study of the pit
    village street (473 objects, 41 materials, all Poly Haven photo surfaces with one fixed shininess each): the road is a third of the main view, walls a sixth, roofs 1%.
    Built: one WETNESS node group (35 controls) that sits between any material's dry look and its shader - photo surfaces or our recipes (tested on five). Rules: water
    in low spots (from the road's camber to the gutter) becomes puddles that flatten the stones and mirror the sky and lamps; wet stone gets darker and glossier with drier
    tops; walls get a darker wet foot and streaks under sills; dials for wetness and puddles. Put on 11 materials of a COPY of the street (your film project was not changed).
    Baked the maps for the .glb (colour, roughness, specularity, clear coat), checked them in a copy of the film's three.js stage. Round 2 fixed the checker's findings:
    white grit on the road in EEVEE (the film's renderer; cause found: its soft-shadow noise; cured by plate settings), walls had got LIGHTER when wet (now 0.84 of dry, foot
    0.66), road too bright (now 1.5 times today). A full-size wet plate of the lockout shot was drawn (1536 x 2730, 20 minutes). **Key finding:** the specularity map changes
    the road by only 0.006; the roughness map is what makes it wet (0.28). And none of the .glb maps reach the film as the stage works today (the projected painting covers
    98% of a moved view): the wet look the audience sees is whatever the painter paints from the wet plate. **Open (checker, "nearly"):** walls barely read wet at plate
    size; the brazier-lit foreground reads as polished tile with a blown-out glare pool; props stand dry and the sacks look as if they hover; a stepped hard edge on one close
    road puddle. **Not tried:** the painter (about 10 US cents) - its brief must first drop "matte painted finish" and "no puddles or reflections" (a wet ground was once
    repainted dry). Pictures: `18 Wet street - pictures/`; guide: `street_wet/09 Recipe - wetness layer and specular map for the street - how it is made.md`.

19. **Painter test of the wet street.** You said: do it (with Sonnet 5.5 helpers). The painter brief (the notice-corner one; the lockout painting's own brief was not
    saved) was changed as little as possible: "matte painted finish" and the ban on puddles and reflections removed; one paragraph added asking to keep the wet sheen, lamp
    and window reflections, gutter puddles with mirrored houses, wet joint lines and darker wall feet exactly where the wet plate has them, painted in the series' hand.
    ONE repaint with Flux 3 edit on fal (same settings as before), finished first time. **Cost:** between US$0.197 and US$0.277 by the price list (fal does not show the
    exact charge) - more than the "about 10 US cents" I told you, because the painter's price per megapixel has doubled since the plan; under the US$0.30 limit. The checker
    confirmed exactly one call. **Result:** the wet look survived. Road 0.72 times as bright as the dry painting and glossy; bright reflections in the same places as the
    plate (overlap 0.60-0.63, the dry painting 0.04-0.10, chance 0.05); gutter puddles with mirrored lamps and windows; the blown-out glare pool of the plate tamed into a
    warm painted pool. Nothing was moved, removed or added to the street (line-up needed no correction). Checker: reads as wet "yes", fits the series' style "nearly".
    **Problems:** the painter added heavy pale-white brush-stroke clouds that look like another painter's hand (it ignored the ban on bright clouds); lamp glass pale
    instead of amber; walls do not read wet and the sacks and cart look as if they hover (from the plate). **In the film stage** (a copy; the film project was not changed):
    the wet look holds in the plate view and when the camera moves, but once it moves the film's old DRY behind painting shows on 56-71% of the near road and pavement (dry
    ghosts beside the drum), and the stage's finishing curve darkens the wet road to about 0.7 of its painted brightness (dry 0.89). Pictures: `19 Wet street painting -
    pictures/`; notes: `street_wet/painter_test/notes - wet street painter test.md`; briefs old and new: `street_wet/painter_test/briefs/`.

## Next step

The checker's free first step: swap the old dry painting's sky into the wet painting (a copy, cut with Blender's exact sky mask), redraw the stage stills and look
again (no cost, about an hour). After that, still waiting for your go: a wet behind painting (one more repaint, about 20-28 US cents), the wood's stone-wall look, and
the slate's straight-edged facets.
