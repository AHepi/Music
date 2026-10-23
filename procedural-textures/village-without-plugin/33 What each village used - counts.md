# 33 What each village used - counts

What this file is: a side-by-side count of what the two forest villages were built with, so the plugin can be judged against a model working on its own.
Both were built by Sonnet from the same plain request. Pictures: `../33 Village without the plugin - pictures/`.

How the no-plugin numbers were measured: `measuring/count_surface_treatments.py` opened the finished scene in Blender and counted every material's
parts (results in `measuring/surface_treatment_counts.json`); the moss, grime and weathering lines come from reading `scripts/materials.py`.
The plugin village's numbers come from its own audit and the checker's report (story log 32).

| | With the plugin | No plugin |
|---|---|---|
| Who and how | Sonnet, plugin 1.4.0 then 1.5.0, rented graphics cards | Sonnet at maximum effort, Blender through its MCP connection only, this computer's processor |
| Time | about 5 hours, then a rebuild (about 7 minutes of card time) | 2 hours 22 minutes |
| Rented card cost | about US$1.60 (with the plugin work) | nothing |
| Materials in use | 67 | 29 |
| Normal maps (pictures of surface relief) | on 61 materials (23 pictures) | none |
| Displacement (surface really pushed in and out) | yes | none in materials; ruts, hoof prints and puddle hollows are modelled as real shapes instead |
| Bump (light trick for small relief) | yes | on 21 of 29 materials |
| Photographed surfaces | 17 scans plus your own mud on the road (rebuild) | none; every surface is made by code |
| Ground mesh near the road | about 10.6 cm between points (too coarse, looks pleated) | about 3 cm between points |
| Total real geometry | scatter capped at 1.2 million triangles by the plugin's rule | 40.7 million triangles |
| Trees | simple faceted shapes | about 2,200 trees grown from branch skeletons, plus spruce cards |
| Weeds, grass, flowers | 88,000 weeds and litter pieces, by site (rebuild) | grass tufts, 1,400 ferns, wildflowers, a grassy middle strip in the road |
| Dirt and grime | yes | dirt at wall feet, damp and algae low on plaster, splashed mud |
| Moss | yes | on thatch near the eaves, on stone, on bark, on the forest floor |
| Weathering and wear | yes | silvered grey patches on wood; edge wear on 4 materials (planks, shingles, stone, timber) |
| Damage | yes | a few broken fence rails; no broken boards or cracked plaster |
| Puddles | long grey channels | about a dozen, in the ruts, reflecting the sky |
| Light | flat, pale sky, a painted hill band behind | low morning sun, a haze box for distance, Cycles |
| Its own weak spots | road pleated, puddles as channels, few stones on the road, weeds ringing tree crowns and inside buildings | kite-shaped leaves, repeating spruce pattern, finest road detail only bump, empty interiors, clean thatch and plaster, no clouds |

**What it means:** the plugin made Sonnet apply every surface treatment, but the no-plugin village looks more real anyway. Its strength is in
shapes and light, not surface tricks: a ground fine enough to hold real ruts, real trees, real grass, low sun and haze, and better cameras.

**One caution about fairness:** the project's standing note (`CLAUDE.md`, which every helper reads automatically) named the treatments from
18:27 on 23 October. The no-plugin helper and the plugin village's rebuild both saw that list; the plugin village's first build did not. The note
was reworded on 23 October so it no longer names them.
