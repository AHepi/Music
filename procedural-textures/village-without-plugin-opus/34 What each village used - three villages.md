# 34 What each village used - three villages

What this file is: a side-by-side count of the three forest villages built from the same plain request: Sonnet with the plugin, Sonnet without it,
and Opus without it. Pictures: `../34 Village by Opus without the plugin - pictures/` (start with the three-way sheet).

How the numbers were measured: the same script, `../village-without-plugin/measuring/count_surface_treatments.py`, opened each no-plugin scene in
Blender and counted every material's parts, every modifier and every copied object; the wear lines come from reading each helper's scripts. The
plugin village's numbers come from its own audit and the checker's report (story log 32).

| | With the plugin (Sonnet) | No plugin: Sonnet, maximum effort | No plugin: Opus, maximum effort |
|---|---|---|---|
| Time | about 5 hours, then a rebuild | 2 h 22 min, 296 tool calls | 3 h 20 min, 299 tool calls |
| Rented card cost | about US$1.60 (with the plugin work) | nothing | nothing |
| Picture drawing | on rented cards (about 7 minutes of card time for the whole rebuild) | 6-7.6 min each, this computer | 6-7.5 min each, this computer |
| Materials in use | 67 | 29 | 38 |
| Normal maps | on 61 materials (23 pictures) | none | none |
| Displacement in materials | yes | none | none |
| Bump (light trick for small relief) | yes | on 21 | on 30 |
| Photographed surfaces | 17 scans plus your own mud | none | none |
| Ground near the road | about 10.6 cm between points | about 3 cm | about 2.5-3 cm (a separate road mesh) |
| How it makes many plants and trees | the kit's scatter, capped at 1.2 million triangles | every piece a separate object (3,900 objects) | copies of a few models (439,906 copies, made by 105 geometry-node set-ups) |
| Real geometry | not measured | 40.7 million triangles | 8.6 million triangles of models; 1.1 billion counting every copy |
| Trees | simple faceted shapes | about 2,200 grown from branch skeletons | 15 tree models, about 5,900 copies |
| Grass, weeds, flowers | 88,000 weeds and litter pieces | grass tufts, 1,400 ferns, wildflowers | about 368,000 clumps of grass, flowers and weeds |
| Ruts and hoof prints | ruts 10-12 cm deep with hoof prints | modelled ruts and hoof prints | modelled ruts that wander, split and crumble; about 5,700 hoof prints; curved turning ruts at forks |
| Puddles | long grey channels | about a dozen, in the ruts | 46, each filling only its own hollow |
| Wear and weather | dirt, grime, weathering, damage, moss | dirt at wall feet, damp on plaster, moss on thatch, stone and bark, silvered wood, edge wear on 4 | moss on the stable roof and thatch, dirt, cracks and damp in the road, a broken wheel, mud pushed up beside ruts, edge wear on 1, bevelled edges on 54 objects |
| Light and sky | flat, pale sky, a painted hill band | low morning sun, haze, no clouds | morning sun, a sky with soft clouds, a hidden light inside the stable |
| Its own weak spots | road pleated, puddles as channels, few stones, weeds ringing tree crowns and inside buildings | kite-shaped leaves, repeating spruce pattern, empty interiors, clean thatch and plaster, no clouds | hidden fill light in the stable, simple trees up close, blocky stone walls on one cottage, dry shallow ruts in the eye-level foreground, fine grit is a surface trick |

Both no-plugin helpers read the project's standing note (`CLAUDE.md`) automatically. Sonnet's copy still named the surface treatments; Opus's
copy did not (it was reworded between the two runs).
