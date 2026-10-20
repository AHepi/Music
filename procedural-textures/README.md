# Procedural textures

What this is: Blender 5.2 recipes, research and guides for making the user's six painted surfaces (brick, slate, wood, rusted metal, mud, gravel)
procedurally, with tools that measure how close each result is to the reference. Start with `Procedural textures - project story.md`; when the cookbook is
finished, `cookbook/06 Cookbook - start here.md` is the front page.

- `research/` - research guides (02) and checks of three extra tools (03), with their experiment scripts.
- `recipes/<surface>/` - each surface's analysis, descriptions, generator, scores, new tiles, transfer to another surface, and its two guides (04).
  `builder_answer.json` and `verifier_answer.json` are the builder's full report and the independent checker's findings.
- `recipes/slate_layers/` - slate made of separate layers inside one recipe (work in progress).
- `cookbook/` - tool guides (06) and the start-here page (work in progress).
- `lib/` - the shared tools: comparison (same kind, dot for dot), baking, seamless noise, setting sweeps, description checker; `lib/contrib/` the researchers' helpers.
- `PROCEDURAL_NOTES.md`, `SLATE LAYERS BRIEF ...md` - the briefs the helpers worked from; the `NEXT PHASE` and `LATER` notes record requests not yet started.

Not saved here: the user's uploaded pictures and maps (put them in `reference/<surface>/` as described in `PROCEDURAL_NOTES.md` to re-run anything), the downloaded
third-party programs, and the large baked maps (re-make them by running a recipe). Paths inside scripts refer to the working folder `proc-work` (this folder).
Pictures here are shrunk copies. Plain Blender only: no film plugin, no add-ons.
