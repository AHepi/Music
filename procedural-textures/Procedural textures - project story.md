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
- **Running now:** the generated-mask test on the slate (fal, under US$1); the wetness layer and specular map for the pit village street set. Helpers run on
  Sonnet 5.5 at extra-high effort.
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

## Next step

Let the two running jobs finish (the generated-mask test, the wet street) and send them with their checks. Open, waiting for your go: the wood's stone-wall look (longer
boards by joining two strips inside a crack, fewer and more ragged joints) and the slate's straight-edged facets.
