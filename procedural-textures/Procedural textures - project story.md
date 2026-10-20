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
- **Running now:** slate in separate layers (layout, colour and fade, damage, moss, outline and shadow) with your picture as a guide only.
- **Honest gaps the checker found:** nobody has yet followed the checklist on a brand-new surface from scratch (every transfer reused an existing generator); there is no
  starting template for writing a new generator; the tool guides mostly teach shader nodes while most generators here are "painters" of flat shapes written in Python;
  the same-kind tool needs a reference picture to score a new surface.
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
| `recipes/slate_layers/` | Slate made of separate layers inside one recipe (in progress) | Guides (05) when done |
| `cookbook/` | Tool guides (06), start-here page, new-surface checklist (in progress) | The finished cookbook |

## Word list

- **Tile:** one square picture that repeats without a seam. **Dot:** one pixel.
- **Description:** the short file of numbers a recipe reads. **Size classes:** S up to 8 KB, M up to 64 KB, L up to 512 KB.
- **Same-kind score:** how much two pictures look like the same kind of surface (0 to 1). **Dot-for-dot levels:** none, layout, close, exact.
- **Height map:** brighter is higher. **Normal map:** a picture telling Blender which way each dot of the surface faces. **Derivation ceiling:** how well the height and normal
  can be made from the colour picture alone, the best any recipe can do that way.
- **Layer:** one part of a recipe with its own settings, seed and mask (for example the moss).
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

## Next step

Finish the slate in layers (being combined and checked now), then send it and save it here. After that, the most useful test of the method is to follow the checklist on a brand-new surface from scratch.
