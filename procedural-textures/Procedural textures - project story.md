# Procedural textures - project story

## The goal

Make the textures, materials and maps of the six surfaces you uploaded (brick, roof slate, aged wood, rusted metal, muddy ground with puddles, gravel) with Blender's own
procedural tools (nodes, geometry nodes, curves, modifiers, physics), research how people do this today, and save recipes and guides that say what each tool does and how its
settings change the picture. In your words: "textures that can be scaled to larger sets with lessons that are transferable to other types of surfaces. Pixel accuracy isn't the
end goal, but it is required for this first step." Then: keep colour and fading, damage and moss on separate layers inside the recipe, with your picture used only as a guide.

**Later goal (21 October), in your words:** "I want to use the full set when we get around to it. Because I want to now do something more immersive with the camera moving through the street. The lighting reacting to characters moving around on set will add more detail and narrative context for some sequences." The textures, wetness, joints, rubbish and the weathering kit are all on the full 3D street, so they carry into that.

**Renderer rule (21 October), in your words:** "Cycles looks absolutely incredible. But it could be expensive. You know what? I think it's worth it. But only for scenes where the lights are on. When they're off, eeve is fine." So: Cycles for plates and frames where lamps, windows or fires are lit; EEVEE when they are off.

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
- **Rented graphics machine works (log 21):** Blender renders on a rented RunPod card instead of this shared computer: a street picture in 0.4-6 s instead of
  1.5-4 minutes, the full-size plate in 2.4 s instead of 20 minutes. Started on demand, ends itself after 30 idle minutes, so you pay per second of use plus about
  14 US cents a day for two permanent stores. Three routes when cards are short (Romania store, Iceland store, any community card), each proven end to end.
- **Skills scout done (log 20); Scenario's Blender skills installed (log 23):** seven Blender skills in the project, every file read twice first, the self-install lines removed. Tried on the street: they found 73 inside-out headframe parts nobody had noticed and give useful light-and-dark and export checks; for textures our own layers stay better (their wear shows only in Cycles unless baked). Your view: the baked door looks photorealistic, and realistic-looking textures in the plate are fine; the wear-then-bake route is kept for props.
- **Sett joints and rubbish done (log 22):** the joints between the road stones now read as grooves between raised stones in 21 of 22 lightings (before: 6 of 22,
  only the dry ones), wet or dry, at no extra drawing time; a rubbish mask built from the street's real shape puts coal dust, cinders, ash, mud, straw, paper and leaves
  along gutters, wall feet, doorsteps and round the props, never on the middle of the road. A fresh checker: joints "yes", rubbish "nearly".
- **Wet street painting round 2 done (log 24):** usable as the lockout picture by the checker's verdict: reads wet, joints and rubbish survive the painter,
  dark plain sky, no dry patches when the camera moves (new wet behind painting), and the stage no longer crushes the wet road dark (fix found and made in a
  copy of the stage; not yet in the real film). It looks more like a detailed 3D picture with a paint finish than the flat, outlined look of the earlier
  dry painting; your decision: "No keep it. The reference doesn't have to be followed exactly. This already looks incredible."
- **Weathering kit done as a first version (log 25):** one reusable kit of grime, cracks, stains, weeds and moss (code in `kits/weathering/`, one settings
  file per place, looks as presets). On the street it works but, after calming, adds little you can see at film size except rust and small weeds; the
  courtyard took it from a settings file alone and turned visibly mossy. Three things block the courtyard job (roof, long garden wall, per-material dials).
- **EEVEE and Cycles compared (log 26)** and **the wet street is in the real film (log 27).**
- **Pay-per-second rendering works (log 29):** a RunPod "serverless" endpoint: a card starts only when a picture is waiting and stops about 5 seconds after, so idle time costs nothing. EEVEE and Cycles both proven on it.
- **Japanese garden done in both looks (log 30):** realistic and painted, drawn with Cycles on the pay-per-second route; a fresh checker: the realistic one "reads as a real temple garden at golden hour", the painted one "nearly" follows your add-on's rules and your own words.
- **Japanese garden character done (log 31):** the realistic garden kept its art style and gained designed detail: a bridge that is built
  (stones, posts, cross beams, long beams, pegged planks), worn and mossy planks, varied roof tiles with moss, chunky grass tufts, a pond that reads,
  a layered maple; 85 materials now carry real normal maps (there were none). A fresh re-check: style kept, more character, bridge makes sense, all
  "yes". Still weak: the smeared lawn colour under the tufts, moss cushion banks that heap up, a clean orange veranda deck.
- **The plugin carries the place work (log 32):** the film plugin, now version 1.5.0, makes any model building a place give it real photographed
  surfaces (your own uploads first, then free scans), normal maps, displacement, dirt, grime, weeds by site, weathering, damage, puddles, stones and a
  construction check, without being told; it tests changes in batches of about 10 versions on the rented cards. Test: Sonnet built a forest village from
  your words and the plugin alone and used every treatment. Still weak: the road's relief, the puddle shapes, weeds round tree crowns and inside
  buildings, crude trees.
- **Control test without the plugin (log 33):** Sonnet at maximum effort built the same village with Blender alone (no plugin, no rented cards, no
  pictures) in 2 h 22 min. It looks more real than the plugin's village: a dense forest of grown trees, a ground fine enough (about 3 cm) to hold real
  ruts, hoof prints and puddles, low sun and haze. It used no normal maps, no displacement and no scans. Lesson: the plugin teaches surfaces; shapes,
  light and cameras matter more, and the plugin does not teach them yet.
- **Nothing running** (checked 23 October about 23:45): no rented machines; RunPod balance US$11.00; the local Blender connection was stopped.
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
| Rented graphics machine (scripts kept outside the repository, in the scratch folder `runpod/`; keys never saved here) | A small job server on the rented machine and a client here: start a machine if none is running, send files, run Blender, fetch the pictures | Rendered pictures, in seconds instead of minutes |
| Pay-per-second render route (scratch folder `runpod/`, not in the repository) | A RunPod endpoint whose cards start only when a job waits; the client `render_client_serverless.py` sends files, runs Blender and fetches pictures | Pictures drawn on an RTX 4090, billed per second |
| `garden/character/` | The garden character job: concept images and the style note (`concept/`), direction and briefs (`direction/`), one folder per builder (`wood/`, `roof/`, `ground/`, `pond/`), the combining step (`final/`) and the fixers (`fix/`) | Stage scripts that change the garden scene; sheets in `31 Japanese garden character - pictures/` |
| The film plugin (`/home/user/Music/plugins/explainer-film`, version 1.5.0) | Everything learned, for any model: the surface-and-wear skill, the place kit (`explainer-film-place`: finish, audit, variations, card-time, roads), a preflight check for places, the build-a-place workflow | A model given only the plugin builds a believable place |

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
- **Rented machine / card:** a computer with a graphics card hired from RunPod by the second. **Store:** a permanent RunPod disk in one data centre that keeps Blender and the uploaded files between machines. **Community card:** a cheaper card from RunPod's shared pool that cannot use a store.
- **Joint (sett joint):** the narrow gap between two road stones. **Behind painting:** a second painting of the street without the near props, which the stage shows where a moving camera sees past them. **Mask:** a black-and-white picture saying where something goes (white = there).
- **Skill:** a packaged set of written instructions (sometimes with scripts) that Claude loads for one kind of task.
- **Seamless / half-tile test:** a tile is seamless if moving the recipe half a tile gives the same picture moved half a tile.
- **Concept image:** a picture made by an image model showing what we aim for; the builders work from it, it is not used in the film. **Style note:** the written rules of the art style (shapes, edges, palette, light, how much detail).
- **Builder, fixer, checker:** helpers that build a part, fix a part, or look at the result fresh without having done the work.
- **Stage:** one script that changes only its own part of the garden scene; the stages run one after another to make the whole garden.
- **Squint test:** blur the new and the old picture and compare them; a high score (target 0.92) means the big shapes and light are unchanged. **Detail energy:** how much fine contrast one part of a picture has; too much reads as busy or photographic.
- **The bridge, from the bottom up:** footing stones on the pond bed carry posts; cross beams sit across pairs of posts; long beams run along the bridge on the cross beams; planks lie across the long beams.
- **Pay-per-second endpoint, worker:** the RunPod set-up where a card (a worker) starts only when a job waits; idle workers cost nothing. **Balance:** the money left in the RunPod account; with too little, workers will not take jobs.
- **Plugin:** a package of written steps, tools and checks that Claude loads; ours is the film plugin. **Blind test:** a fresh model gets only the plugin and a plain request, to see what it does without being told. **Guard test:** a test that fails if the words of one coming test request appear in the plugin.
- **Scan:** a surface photographed in real life with its normal and height maps (free from Poly Haven). **Your own texture library:** your uploaded surfaces (mud, gravel, brick, slate, wood, metal), which the plugin can use but never copies into GitHub.
- **Variation batch:** about 10 measurably different versions of one change, drawn at once on the rented cards and shown on one labelled sheet.
- **Control test:** the same job done without the thing being tested (here, without the plugin), to see what difference it really makes. **Blender MCP connection:** a link that lets a helper drive a running Blender directly, one command at a time. **Triangle:** the smallest flat piece a 3D shape is made of; more triangles means finer real shape.

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

20. **Skills scout.** You asked: set a helper on skills.sh to see if anything is worth keeping. The helper ran about 120 searches and read the instruction files of
    about 37 packages; it installed nothing and tested nothing. **Worth keeping, best first:** Scenario's "Blender expert" set (7 skills: scripting rules, shader and mask
    layers, baking, geometry nodes, EEVEE lighting, export to a three.js stage; leave out its two skills that use Scenario's add-on and outside services); a small
    "porting to Blender 5" set; a baking skill; a plain-language reporting skill; two three.js loading skills; ElevenLabs' own narration and music skills (say no
    to its sign-in installer); RunPod's pod-doctor and cost-audit. **Nothing found** for seamless or non-repeating textures, moss, wetness or rubbish recipes,
    measuring closeness to a reference picture, or frame-exact filming of the three.js stage: our own tools already go further. One trap: its first copies of
    other repositories filled this computer's disk (cleared). Report: `20 Skills scout - what is worth keeping from skills.sh.md`. Asked you before installing,
    because a skill runs with full permissions.

21. **Rented graphics machine (RunPod).** You asked whether a rented machine would help, gave a key and a US$5 start budget, then: "rent per second and cache
    the config", and later "Don't worry about runpod budget. Just find a workflow that works". **Built:** a small job server that runs on the rented machine
    (this session cannot open a terminal on it, so it sends files, starts Blender and fetches pictures over the machine's web address with a secret code), a
    client here that starts a machine only when a helper asks, a saved machine set-up, and two permanent 30 GB stores (Romania and Iceland) holding Blender and the
    street files. The machine ends itself after 30 minutes without a request (proven: it ended exactly on time in the first test with 15 minutes).
    **Speed (tested):** EEVEE and Cycles both use the card on the stores; street pictures in 0.4-6 s, the full-size 1536 x 2730 street plate in 2.4 s (20 minutes
    here). **When cards are short (tested):** Romania store ready in 25 s; Iceland store ready in about 80 s; with both stores switched off, a community RTX A5000
    was ready in 157 s, installing Blender from mirror sites and receiving the street files, and drew today and wet in 17 s. **Failures on the way:** the RunPod
    command tool could not be installed here (its download is blocked), so everything goes through RunPod's web interface; RunPod's web address refused Python's
    default name; sending 135 files one by one took 9 minutes (now one bundle, 8 s); my first two stored machines broke at start-up (my mistakes, fixed); the
    official Blender site refused or crawled for some machines (now mirror sites with a checksum); community cards often vanish between asking and starting (now
    three tries). On one community host Cycles could not use the card (it ran on 25 processor cores). **Cost so far:** RunPod's bill showed US$1.13 for machines
    at 04:40 (it lags); my estimate is about US$1.6-1.8 in all, plus about 14 US cents a day for the two stores. **Not tested:** Cycles on the community card;
    two helpers asking for a machine at the same moment (a lock makes one wait). Notes: `RunPod set-up for rendering - findings.md`; spending:
    `SPENDING - paid image generation ledger.md`.

22. **Sett joints that hold under all light, and a rubbish mask.** You said: "Add a rubbish mask for gutters and along buildings. And the normal maps between
    bricks on the ground needs a little work. The light shouldn't be able to wash out the 3d affect so easily. The geometry should still be visible under all
    conditions." Five helpers (a study, a joints builder, a rubbish builder, a fresh checker), all drawing on the rented machine. **What was wrong (measured):**
    the joints only ever showed because they were dark in the photo; the relief picture added nothing measurable (a relief picture tells the light which way a
    dot faces, not how deep it is), and the shine water adds lay equally over stones and joints, so wet joints vanished (6 of 22 test lightings passed, only the
    dry ones). **Joints fix:** a new layer, JOINTS, after the wetness layer on the road only: the joint is darker and stays dull when wet (rougher, less shine and
    water film), the stone edge gets a rounded slope, puddles still cover joints; one master dial. It needed a rebuilt joint picture (the first one missed about
    half the pale sand joints). Result: 21 of 22 lightings pass (all 9 full-size pictures pass); the one failure is the lockout shot in heavy rain, middle distance,
    under the brazier glare, at the small test size only. Same drawing time. Real 8 mm grooves cut into the near road were also built (plate only, +2 s a picture
    on the rented card), but they look worse in the middle distance, so they are off. **Rubbish:** a mask made from the street's real shape (gutters, wall feet,
    doorsteps, rain-pipe and lamp-post feet, inside corners, rings round the props) broken into patches, never on the middle of the road; it drives painted muck
    on the road, flags, kerbs and gutter stones (coal dust, cinders, ash, mud, wet straw, sodden paper, dead leaves, wet where the street is wet) and about 6,400
    to 7,200 small 3D pieces; 24 dials, one master "amount" dial. The joints keep their numbers with rubbish on. **Fresh checker:** joints read 3D everywhere
    "yes"; rubbish "nearly": near-camera coal chips look like faceted gems, straw like matchsticks, the gutters too thin in the street view, some bright ticks on
    middle-distance joints; with every dot counted (not leaving out puddle and rubbish dots) the pass count is 18 of 22, not 21. The wet road came out 3-8 %
    darker, which also cut blown-out dots near the brazier from 4.7 % to 2.8 %. **Failures on the way:** black road pictures from a stale picture left on the
    rented machine; a plan picture turned the wrong way round; four wrong explanations of the one remaining failure; about 60 Blender runs against a plan of 40.
    **Cost:** no paid painter calls; the builders' drawing took about US$0.45 of the first rented machine, which ran about 3 hours in all including set-up and waiting (about US$1.00 at US$0.34 an hour). **Not done:** the painter (now running, log 24), the .glb and stage, Cycles, joints on
    the flags and kerbs, dirt on the walls themselves, other shots (each needs its own "places" picture). Pictures: `22 Sett joints and rubbish - pictures/`;
    recipe: `street_wet/relief_and_rubbish/10 Recipe - sett relief and rubbish - how it is made.md`.

23. **Scenario's Blender skills installed.** You said: "Ok install scenario for now." Seven of Scenario's Blender skills (expert, texturing and shading, UV and
    baking, geometry nodes, lighting and rendering, export, previs and storyboard; MIT licence) went into the project's skills folder. Before installing, two
    helpers per skill read every file in full; 83 text edits were made: the "npx skills add" self-install lines now say "do not install anything, tell the
    person"; Scenario's add-on and live-window bridge are marked "not used here"; one line telling the agent to try another spelling when a safety filter
    blocked a quit, reset or delete was reversed; a storyboard template that wiped the whole open scene now stops instead; commands use our Blender path and
    a pretend screen (without it Blender stops as soon as it draws anything: tested). Six of nine helper scripts are unchanged; three got tiny safety changes.
    A final checker confirmed only the intended edits differ from the download. **Four try-outs on the street (rented machine):** (a) the delivery check found
    73 inside-out parts (69 headframe bars, both winding wheels, 2 trims), invisible now but see-through if back faces are ever hidden; as shipped it gives a
    useless 908 "errors" on the whole street because of the 3.5 km sky dome. (b) Its wear layer follows a prop's real mouldings but shows only in Cycles, not
    in EEVEE, unless baked; its automatic UV seams failed on our door; our own layers stay better for walls and ground. (c) Its light-and-dark study, blown and
    crushed shares, and colour-setting audit are useful (the audit found data pictures set to colour inside our wetness layer); its subject verdicts are
    built for faces. (d) Its scatter builder worked first time with proper counting checks; its export check found three real faults the exporter hides; its
    "web" export squeezes shapes lossily (up to 52 mm) and needs one line added to our stage. **Not tested:** that a new session picks the skills up; most of
    the tools. **Unsure:** whether Claude will always follow the written "local rules" (they are instructions, not locks). Note:
    `23 Scenario Blender skills - what was installed, changed and learned.md`; pictures: `23 Scenario Blender skills test - pictures/`.

24. **Wet street painting, round 2.** Cleared under "Just do it. $20 budget, ask free". Five helpers. **Plate:** the checker's small fixes: coal chips now flat
    irregular lumps, straw shorter, thinner and curved, more dust and some wet paper in the gutters, pieces near the camera capped in size, rubbish gathers
    about 8 to 1 at the kerb against the pavement (was 5 to 1); the bright hooked ticks on middle-distance joints are gone (the checker's own numbers did not
    remove them; the joint slope now fades from 3 m to 10 m). Joint test unchanged (21 of 22; 18 of 22 counting every dot). A props-free twin plate was
    drawn, hiding exactly the props the film's page hides (found by reading the film's page). **Front painting:** one repaint (US$0.197 to 0.277). The painter
    again added pale clouds despite three sentences against them, so a dark plain sky was put in for free with Blender's exact sky outline (four tries to keep
    the thin headframe rails clean). Below the sky it is far more faithful than the first test: joints kept at about 93 % of the plate's strength near the
    camera, about 70 % of the plate's rubbish chips found in place (first test 19-22 %), no blown-out glare pool. It ignored "no stronger lamp streaks" (5-9
    times the plate's) and painted the lamp glass cream-gold, not amber. **Behind painting:** one repaint of the props-free plate (US$0.197 to 0.277); it came
    back a fifth lighter and warmer, matched to the front painting for free. In the stage with the camera moved, the ground behind the props is now wet; the
    old dry behind painting showed pale dry pavement. Joints there are weaker. **Stage:** the darkening was found: mostly the dark frame edge and a film-style
    brightness curve squashing dark values (the suspected "contrast 1.04" was only a small part). Fix in a copy: a new switch ("toe") plus the frame edge eased
    from 0.30 to 0.25 for this scene; the wet road now arrives at 0.935 of its painted brightness (0.75 in the first test), crushed dots 4 % to 0.14 %; eight
    pictures of other scenes come out identical when the switch is off. **Fresh checker:** usable as the lockout picture "yes"; sky "yes"; joints and rubbish
    "nearly" (faint far away and in the behind painting); wet holds when the camera moves "yes"; the stage fix does no harm "yes". It checked the money
    against fal's history (two calls, US$0.39 to 0.55). **Its main point for you:** next to the earlier dry painting (flat colour, thick dark outlines) the new
    one reads like a detailed 3D picture with a paint finish. **Not done:** the paintings and the stage fix are not in the real film (that changes your film
    project, so it waits for your go); only stills, not the whole clip. **RunPod:** the machine has served this and three other jobs since 05:39 (about
    US$2.65 so far). Pictures: `24 Wet street painting round 2 - pictures/`; work: `street_wet/painter_round_2/`.

25. **A reusable weathering kit: grime, cracks, stains, weeds and moss.** You said: "The next thing to apply to the streets is things like: grime, cracks,
    stains, weeds and moss." then "They should be reusable too. Which is perfect. Because next is the Japanese forecourt again". Sixteen helpers: four
    studies (1926 pit villages; our pipeline; what survives the painter; the courtyard), a plan, shared "where things may go" maps read from any set's
    shape, three builders (walls, ground, growth), a combiner, a reuse test, two checkers, a fix round, a re-check and one painter test. **Built:** the kit
    (`kits/weathering/`): twelve layers (soot and dirt film, run-off streaks, damp tide-marks, rust, whitened doorsteps, tar and water marks, cracks and
    chipped kerbs, flat moss, algae, lichen, 3D weeds and moss cushions, worn paint) that go on any scene in one call and come off leaving it exactly as it
    was; everything about one place sits in a settings file (`sets/pit_village_street.json`, `sets/japanese_courtyard.json`), looks are presets. The study
    found no direct account of 1926 Durham street grime; its rules come from soot and damp science, plant surveys and northern practice, with honest
    confidence marks (one surprise: many East Durham colliery villages had tarmac roads by 1917). **On the street:** joints still pass (21 of 22; 20 counting
    every dot), the street is not turned to dark mush (plate brightness moves 1-1.6 %), no plant on the road middle, lanes or doorsteps. The first checkers
    found lime-bright weeds standing in puddles, pale panels on the brick row, cold blue doorsteps and over-even cracks; the fix round calmed all of that
    and cut the extra drawing time from 2.1 to 1.4 times. **But** the re-check says that at film size the kit now adds little a viewer can see except rust
    and a few weeds: the walls are nearly black and seen edge-on, so soot, run-off streaks and damp bands vanish; the notice shot's pavement got about 50
    weeds mid-slab; moss pieces look like cut-outs. **Painter test** (one call, US$0.197-0.277): the big weed clumps, the drum's soot and rust, and rust on
    the walls survive; hairline cracks and tiny tufts do not; the painter again added (grey) clouds. **Reuse:** the courtyard took the kit from a settings
    file and a new look alone, no code changed, and became visibly mossy (stones, lantern, wall caps, weeds at the gravel edge). Three things could not be
    done by settings: moss on the hall roof (its materials hide inside a node setup the kit cannot see), run-off streaks on the long garden wall, and
    different strengths per material for anything but soot. **Not tested:** Cycles with the kit, moving pictures, the courtyard after the fix round.
    Pictures: `25 Street grime, cracks, stains, weeds and moss - pictures/`; recipe: `kits/weathering/15 Recipe - weathering kit - grime, cracks, stains,
    weeds and moss - how it is made.md`.

26. **EEVEE and Cycles side by side.** You saw the Cycles door and said the bricks "look incredible", then "Yeah do it!" to drawing the whole wet street both
    ways. Same file, camera, lights, wetness, joints and rubbish; only the renderer differs; drawn on the rented RTX 4090. **Answer (fresh checker):** the
    whole street does NOT get the door's jump. The bricks and stone are the same photo scans in both, and walls look about the same (the drawer's claim that
    walls gain relief did not hold: 0.86 to 1.22 times). **Where Cycles clearly wins:** wet ground: lamps, lamp posts and house fronts mirrored in puddles and
    gutters, warm light reaching the road (road brightness 0.336 against 0.183), clean gutter water where EEVEE shows sandy grain; and the door's panels.
    **Where EEVEE holds its own:** joints read a little crisper; shadows keep some detail (Cycles leaves shade truly dark: 6-7 % crushed black against about
    1.5 %). **Biggest surprise:** the colour: EEVEE streets are cold blue, Cycles warm gold, and the painter would follow that mood. **Why:** mostly one EEVEE
    setting (its light cut-off stops lamp light reaching the road); lowering it brings EEVEE close but makes it as slow as Cycles. **Time per picture:** main
    street wet 3.7 s against 14.1 s; lockout plate 2.8 s against 25.3 s; close cottage view 1.6 s against 15.4 s. **Unexplained:** the fire drum lit orange
    in Cycles only; a bright speck at one roof corner in wet Cycles only; the sky dome and some glowing meshes darkening Cycles. **Not tested:** moving
    pictures (the clean-up step could flicker frame to frame), whether the painter paints better from Cycles pictures. **Why it matters for your later
    immersive plan:** with characters walking through the street, Cycles gives them real shadows and real reflections in the wet road for free.
    Pictures: `26 EEVEE and Cycles side by side - pictures/`; work: `street_wet/eevee_vs_cycles/`.

27. **The wet street in the real film.** You said: "Oh yes please." The lockout shot in the austerity explainer now uses the round 2 wet front and behind
    paintings; the old dry ones are kept beside them (lockout-painted-dry.jpg, lockout-behind-dry.jpg), so going back is four renames and one look line.
    The stage's darkening fix went in too: a new "toe" switch, off for every other scene, and the lockout's dark frame edge eased from 0.30 to 0.25. The
    12-second clip was filmed the kit's own way (56 minutes on this computer; the dry clip filmed the same way came out byte for byte the kit's earlier
    one). **Checked:** all 360 frames on contact sheets, the first seconds of the camera move frame by frame, the ground the props uncover: no dry patches,
    no seams between the front and behind paintings, no leftover painted shadows, no jumps except the planned cut at 7.3 s; the road arrives at 0.93 of
    its painted brightness (0.75 in the first wet test); eight pictures of other scenes come out dot for dot the same with the old and new stage. Two
    fresh checkers: "ready to show". **Failures on the way:** a record file's prices were damaged when written through the shell (the "$0" in "US$0.048"
    was read as a command name; fixed); the first fix round blamed a faint speckle in a ninth scene on the exact text of the stage code, and the second
    checker showed that scene comes out two ways from run to run even with the old stage (notes corrected, film project log 39). **Not tested:** the clip
    at full speed on a phone; it is silent (the kit's lockout example has no sound). The film project's own notes follow its house rules: decisions 43
    and 44 (your renderer rule), Status, Lessons 140-142, Workflows, its story logs 37-39. Pictures: `27 Wet lockout shot in the film - pictures/`.

28. **A helper's slip, found while saving (21 October, evening).** While checking the weathering kit's files for private details before saving them, I
    found that the period-reference helper (log 25) had written your email address into the identity line its two download scripts sent to Wikipedia and
    Wikimedia Commons when fetching reference pictures. Nobody asked it to. Those two websites received the address with each request; it was not saved in
    the repository (removed from both scripts before saving; this folder had never been saved before, and every earlier save was checked for it). Future
    helper briefs should say: never put the person's email or name into requests to outside websites.

29. **Pay-per-second rendering.** You said: "Then render on runpod. There's an option where you only pay per second used. So you don't pay for
    seconds or minutes not used." Today's always-on machine ran 13 hours (about US$11.60), much of it waiting between jobs. **Built:** a RunPod
    "serverless" endpoint: a worker (a card) starts only when a job waits, runs it, and stops about 5 seconds after its last job; billing is per
    second while a worker is up (RTX 4090: US$1.10 an hour, about 0.03 US cents a second). No custom software image was needed: the workers use a
    plain Ubuntu image, and everything else lives on our Romania store: Blender, a small job taker run by the Python that ships inside Blender,
    RunPod's job library, and 60 system libraries copied from a normal machine so Blender can draw. A new client (`render_client_serverless.py`)
    has the same commands as before (upload, run, wait, download); files go in 6 MB pieces. **Proven:** a cold worker woke in 20-22 s; the wet
    street with EEVEE on the card (wet picture 5.8 s, whole job 31.6 s billed, about one US cent); Cycles on the card through OptiX (128 samples,
    5.2 s), with a warm worker answering in half a second. **Failures on the way:** RunPod's newer interface started answering "authentication
    failed" mid-setup; I checked that your key was fine (their older interface accepted it, a wrong key got a clean refusal) and built the
    endpoint through the older interface instead; the job library pulled 2 GB of extras onto the store (only the parts used are read). **Not
    tested yet:** what RunPod's bill shows for these seconds (their billing page was down), long renders near the 55-minute job limit.
    Guide for helpers: `runpod/HOW TO RENDER - pay per second.md` (scratch folder, not in the repository).

30. **The Japanese garden, with all the advice, in both looks.** You said: "Ok. Can you work on the Japanese garden using all the advice
    available. Then render on runpod." and, asked which look, "Both, side by side". **Study (five helpers):** your Astra add-on's 17 guidance
    documents and all 83 lessons (its painted rules: broad unequal colour passages, marks that differ by material, chiselled unequal planes, and your
    own recorded words "No rounded smooth curves. Just edges and flat surfaces that approximate a curve"); everything learned on the street; an
    inspection of the scene (it found a veranda step floating 23 cm in the air, bridge posts 2-7 cm short of the boards, wall caps floating 6.5 cm,
    a lantern glow buried inside solid stone, 77 deck faces fighting the plinth); research on real temple gardens (gravel should be pale grey
    granite, not pink-brown; maple leaves 4-12 cm, not 20-34 cm; rocks half-buried with moss collars). One plan ranked 11 improvements by what a
    viewer notices. **Build (four builders, then one combiner):** repairs and new shapes (all floating parts fixed; a carved six-sided lantern
    with a lit window; rocks rebuilt, deeper set; straight rake lines every 12 cm with rings and a kerb; battered walls with tile caps; a basin
    set), living things (56,000 real-size maple leaves in layers, moss and tufts grown with your add-on's live scatter after a 3-line fix for
    Blender 5.2, a pine with needle sprays, clear pond water), surfaces (photo-scanned Poly Haven stone, wood, plaster, gravel, roof and ground for
    the realistic look; broad brushed colour with your add-on's pigment tool and flat-shaded planes for the painted look; the weathering kit on
    top, its three courtyard blockers fixed), light (a graded dusk sky instead of one flat orange, hills fading with distance, cooler shadows, each
    light on its own layer). **Pictures (Cycles, RTX 4090, pay per second):** the original view in both looks, the veranda view in both looks,
    and a blue evening with the lantern lit. **Checks:** two fresh checkers, a fix round (white shards on the pond were the hall lamps mirrored,
    now hidden from reflections; black corners lifted; painted sun rings and ground made straight-edged; a needle pine; tufts varied), a re-check:
    realistic "yes", painted "nearly", both "better than the original" "yes". **Still weak:** the far hedge in the veranda view reads as dark
    boulders; the painted original view still has one long smooth curve in its sky and smooth-shaded ground; the evening pictures were not redrawn
    after the fix round (old pond shards); the lantern's light sits inside its glow box. **Cost:** about 47 minutes of card time in all;
    RunPod's hourly bill for the endpoint: US$1.21 to midnight plus about US$0.20 after. A checker worried that three "idle" workers stayed up
    for 40 minutes; RunPod's own hour-by-hour bill shows they cost nothing (they are free standby for a fast start). Pictures: `30 Japanese
    garden - pictures/` (start with the two "30 Final" sheets); plan: `garden/30 Plan - Japanese garden - all the advice.md`.

31. **The garden's character, inside its own art style (22 October).** You said: "The realistic one. But don't make it more realistic. I still
    want the art style. What's missing now is the details in grass, pond, roof, wood and so on. They have textures, but they're bland and have no
    character. The geometry of the wood planks is also very basic. No wear, no mold or moss, the logic behind how the bridge is constructed makes
    no sense. Even for an artistic style. Are there any normal maps used? Generate an image of trees and so on in the art style and work from that.
    The image gen budget is $15." Then: "These things need to be integrated into the style. So it's just part of design." **Your normal-map
    question:** no, there were none; only gentle bump from height pictures, and the planks were plain boxes. **Concepts (paid):** paint-overs of
    the two views, element sheets (bridge construction, planks, roof, trees, pond edge, lantern, grass and moss) and swatches, 29 calls, US$3.86
    at most of the US$15. Nano Banana 2 kept the style best; Nano Banana Pro was too photographic; Flux 3 moved the picture around. A style note
    turned your rule into "the rule for every builder": details are designed parts of the style. **My mistake:** a message I sent to the concept
    helper woke a second copy of it, which made 8 extra paid calls (about US$0.70 of the total) before it stopped. **Direction and four builders
    (on the rented cards):** the bridge rebuilt so it stands up (footing stones, posts, cross beams pegged to the posts, long beams, planks with
    gaps, pegs, iron cramps and a diagonal board at each turn); planks with rounded edges, grain and knots; roof tiles in different tones, slipped,
    chipped and missing ones, round end discs, a ridge cap, moss and drip stains; walls with cracks; rocks with moss caps; 12 grass tuft shapes with
    seed heads, a worn path, moss cushions; lily pads, iris and ripples; the maple rebuilt as layered pads; the pine as flat discs. 85 materials
    now use 17 real normal-map pictures, each checked to point the right way. **First full-size pictures (Cycles):** a fresh art checker said
    the style was kept, there was more character and the bridge made sense, but: pale clean planks with almost no moss (a builder claimed 9.8
    percent, the checker measured 0.6), one knot stamped on most planks, a pond that only read up close, a darker and heavier maple, moss cushions
    like rows of bean bags, a hairy pine, a moss "sticker" on the lantern and green stripes on the rocks. **Two stoppages:** from 07:31 to 08:30
    the cards took no jobs because the RunPod balance had run down to US$0.13 (you added credit); and the container restarted twice (about 02:48
    and 09:40). Both times the job carried on from where it stopped; the second time one checker's work was lost. **Fix round:** four fixers, one
    per part, worked at the same time, then one step put the fixes together and drew the pictures again, and a fresh checker looked. Fixed:
    moss patches and greyer bridge wood, varied knots, the lantern sticker and rock stripes (they came from the weathering kit's splash, crack and
    growth layers, now toned down on stones), roof moss cushions, bolder wall cracks, chunky tufts, varied moss cushions, a soft worn path, readable
    flowers and red leaves, a pond that reads (bigger pads, pink flowers, a pebble shelf, floating leaves), a brighter maple with its branches
    showing, a pine with brush-stroke clumps. Re-check: style kept "yes", more character "yes", the bridge "yes" (checked in the scene: all 59
    planks rest on at least two supports); no further round needed now. **Still weak:** the lawn colour under the tufts is the old smeared scan;
    the moss cushion banks still heap up; the veranda deck is clean and the most orange area; drip stains, slipped tiles and ripples only read up
    close; the squint test missed (0.883 and 0.873 against 0.92), because the maple and pond now follow the concepts; strongly coloured pixels a
    little over the limit; 6 of 8 iron straps have a nail head floating 14-18 mm above the plank and 3 footing stones overhang the bank (both hidden
    from every camera); 48 leftover test cameras in the scene file. **Cost:** images US$3.86 at most of US$15; pay-per-second cards US$10.89 by
    RunPod's hourly bill (about 4 hours of card time), plus about 3 US cents for a test machine. Afterwards nothing was running, and as you asked I switched the
    pay-per-second endpoint fully off (most workers 0; it goes back to 3 before the next render). Pictures: `31
    Japanese garden character - pictures/` (start with "31 Final - hero view", "31 Final - veranda view", the two "31 Before and after" sheets and
    "31 Final - close-ups"); scripts and notes: `garden/character/`; the scene files stay on the RunPod store.

32. **The plugin learns the place work, and a forest village tests it (22-23 October).** You said: "Sonnet needs to use normals, displacements,
    dirt, grime, weeds, weathering, damage.. basically everything. But don't tell it that. These things need to be in the plugin." **Plugin 1.4.0
    (Sonnet helpers):** four readers went through the weathering kit, the street, the garden and the cookbook; a design, a critic, three builders
    (skill text; kit code with a one-command finishing pass, an audit that fails a scene missing a treatment, and a new preflight stage; a place-building
    workflow), a small canal-lock scene built with it, two blind models and a judge. **My mistake, found and fixed:** the system hands your latest message
    to every helper started in the same turn, so they all saw your village request and wrote it into the plugin as a worked plan; that made the test
    worthless, so everything written for it was removed, the worked examples became the garden and the canal lock, and a guard test keeps those words
    out. **Your money question:** "Why did it cost $10? That's really expensive for a few photos": the garden's finished pictures cost about 5 cents; the
    rest was helpers trying one change at a time with no limit. You added: "batch them with workers... 10 variations that are measurably different".
    Now in the plugin: a free tiny first pass drops versions that would look alike, up to 3 cards draw the rest at once, one labelled sheet comes back
    (10 versions in 48 s for about 5 cents), and every helper has a card-time allowance. **Lessons from the earlier sets:** you asked whether they were
    used; an audit of about 370 found about 210 carried, 90 partly, 70 missing; Opus helpers (you switched the plugin work to Opus) added the 40 that
    mattered, most with an automatic check, and the stage's dark-and-wet fix. Clean blind tests (harbour, railway station, monastery courtyard)
    applied the treatments without being told. **The village (Sonnet, the plugin alone):** 6 parts, ground first; it used normal maps on 61 of 67
    materials (23 pictures, all pointing the right way), displacement, dirt, grime, weathering, wetness, damage, moss, 88,000 weeds and litter pieces,
    ruts 10-12 cm deep with hoof prints; card cost about US$0.70 (the garden: US$10.89). It took about 5 hours, mostly thinking at extra-high effort
    (you moved the later helpers to high). The plugin's own gate then stopped it before any picture, because it contradicted itself twice; I drew the
    four views myself. **You looked and said** the dirt track had nothing like the mine's detail, and asked where those normals and materials went and
    why the weeds lost their edge logic. I looked: the plugin made every surface in code (it never used a scan or your uploads), and its weeds had a
    20-50 percent chance of growing anywhere. **Three runs, as you asked:** Opus updated the plugin to 1.5.0 (real scans and your own library, weeds by
    site, puddles and stones, the specks and sparkles fixed, the gate made consistent); Sonnet re-finished the village (the road and yard now wear your
    own mud; 17 scanned surfaces; weeds gathered at wall feet, verges and seams; the specks, sparkles and rectangles gone; the gate passed); Opus
    checked: the road now matches the mine in fine grain, colour spread and small lumps, but reaches only 68 percent of its large shapes and looks
    pleated, because the road mesh is too coarse for its displacement; the puddles are long grey channels (the plugin's "rounded pools" did not hold);
    almost no stones on the road itself; 26 percent of weeds ring the tree crowns and 109 stand inside buildings; the kit calls python3 by name, which
    the rented cards lack; your pictures are packed inside the finished scene file on the rented store (never in the plugin or GitHub). **Your rule:**
    "every new set that uses different tools needs to update the plugin" (now in CLAUDE.md, the film's decisions 45-48 and the plugin's house rules).
    **Cost:** RunPod about US$1.60 for all of this (balance US$12.61 to US$11.00); no paid pictures. Pictures: `32 Forest village and the plugin -
    pictures/` (start with "32 Village - first and rebuilt, next to the coal mine").

33. **The same village without the plugin (23 October).** You asked: "Can you get sonnet on max to generate a similar village without the plugin?
    No pods access, no image references. Isolate it completely and get it to use blender with its MCP plugin." One Sonnet helper at maximum effort got
    only your original village words and Blender through its MCP connection, with orders not to read any other file, use any skill, the internet or the
    rented cards. It ran 2 h 22 min on this computer's processor (each picture 6-7.6 minutes) and cost no rented-card money. **What it built:** a clearing
    in a dense forest (about 2,200 trees grown from branch skeletons, 1,400 ferns), five cottages (half-timbered or stone, thatch or shingles), a 12 m
    stable with four empty stalls and a cart, about 30 kinds of props, three dirt roads with modelled ruts, hoof prints and about a dozen puddles. Its
    ground is about 3 cm between points near the roads, against the plugin village's 10.6 cm. **Counted in its scene:** 29 materials, all made by code;
    no normal maps, no displacement, no pictures; bump on 21; edge wear on 4; dirt, damp, moss and silvered wood written into the materials; 40.7
    million triangles of real shape. **Side by side** (`33 Village without the plugin - pictures/`): it looks more real than the plugin's village in
    all five views, mainly because of shapes and light: real trees instead of faceted blobs, real ruts and puddles that reflect the sky, grass and
    flowers, low morning sun and haze instead of flat light, and a true view from above. Its own weak spots: kite-shaped leaves, a repeating spruce
    pattern, empty interiors, clean thatch and plaster, no clouds. **What it means:** the plugin makes a model apply every surface treatment, but
    surfaces were not what held the village back. **Fairness, my mistake:** the project note every helper reads automatically (CLAUDE.md) named the
    treatments from 18:27 that day, so this helper and the plugin village's rebuild both saw the list; the first plugin build did not. I reworded the
    note so it no longer names them. Counts, the helper's report, its build scripts (about 5,000 lines) and the measuring scripts are in
    `village-without-plugin/`; its 99 MB scene file stays in the scratch folder and is not saved (the scripts rebuild it).

## Next step

Your rule says a set that used different tools updates the plugin. The one next step: the three runs you set (Opus updates the plugin, Sonnet
rebuilds the village, Opus checks), teaching the plugin what this control did better: fine ground near roads with modelled ruts, hoof prints and
puddle hollows; trees grown from branch skeletons; real grass; low sun with a haze box; and choosing cameras. Waiting for your go-ahead.
