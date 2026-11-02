# Materials by role

What this file is: which role word gives which proven material, and how to name objects so `apply_by_role.py` dresses them without being told anything else. The materials come from the street bundle "Rain on the Old Curve" (`Materials.blend`, 45 materials, their six sandstone pictures packed inside; see `Material inventory.txt`).

## Name your objects with role words

Build plain shapes and put the role in the name: `left terrace 03 wall`, `window lit`, `window dark`, `door wood`, `kerb stone`, `lamp post iron`, `lamp glass`, `puddle water`, `roof slate`, `chimney smoke`. Or set the property `obj['place_role'] = 'wall'` in your build script, or give a roles file `{"object name": "role"}`. Pairs of words beat single words (`window surround` is trim, not a window; `lamp post` is iron, not a lamp).

| Role | Material | Words that mean it |
|---|---|---|
| wall | one of the 12 `Hand-painted sandstone • shade NN` (a different shade per object) | wall, brick, stone, masonry, facade, terrace, house, chimney, tenement, building, shop, tower |
| plaster | `PLASTER • mineral flakes and scars` | plaster, render, limewash |
| trim | `STONE • worn honey-grey architectural dressings` | kerb, curb, sill, lintel, quoin, cornice, surround, dressing, trim, plinth, arch, cap; `window surround`, `door surround`, `chimney pot` |
| mortar | `MORTAR • dark eroded joints` | mortar, joint |
| road | `COBBLES • wet basalt / broken amber-blue reflections` | road, cobble, sett, street, lane, carriageway |
| pavement | `PAVEMENT • damp sandstone slabs` | pavement, flag, footpath, slab, step; `door step` |
| earth | `ROAD BED • damp grit` | earth, ground, yard, mud, soil, grit, track |
| roof | `SLATE • soot-dark irregular roofs` | roof, slate, tile, ridge |
| wood | `WOOD • peeling dark painted doors` | door, shutter, frame, sash, beam, plank, board, cart, crate, barrel, timber, wood, fence |
| iron | `IRON • soot-black lamp posts` | iron, post, rail, pipe, bracket, gate, drain, metal, steel, wheel, chain, wire; `lamp post`, `lamp cap`, `down pipe`, `cart wheel` |
| rust | `RUST • rain-aged iron` | rust, rusty |
| window lit | `GLASS • warm occupied interiors` (glows, and the look stage puts a real light behind it) | `window lit`, `lit window`, `window warm` |
| window dim | `GLASS • dim amber rooms` (a faint glow) | `window dim`, fanlight |
| window dark | `GLASS • sleeping navy interiors` | window, pane, glass (alone) |
| lamp glass | `Lantern • glowing imperfect amber glass` (glows; the look stage adds the gas mantle and its pavement wash) | `lamp glass`, `lamp head`, `lamp pane`, lantern |
| flame | `LAMP • honey flame glow` | mantle, flame, fire, glow |
| water | `PUDDLE • shallow transparent reflective film` | puddle, water, gutter |
| rock | `STONE • unique sandstone / damp soot` (natural stone: never built up into ashlar) | boulder, rock, reef, cliff, headland, crag, outcrop |
| sand | `ROLE • dry sand with wind grain` (made in code: the street bundle has no sand) | sand, dune, beach |
| sea | `ROLE • dark sea with small waves` (made in code) | sea, ocean, lagoon, harbour |
| moss | `MOSS • subdued olive crevices` | moss, algae, lichen |
| grime | `GRIME • dark damp organic residue` | grime, soot, stain, dirt; `wall foot` |
| recess | `RECESSES • near-black blue` | recess, void, inside, interior, dark, shadow |
| smoke | `Chimney smoke • organic soft wisps` (a volume: give it a box above the chimney) | smoke, haze |
| weed | `Weed • rain olive` | weed, grass, ivy |
| leaf | `Fallen leaf • ochre` | leaf, leaves, litter |
| paper | `PAPER • aged torn fragments` | paper, poster, notice |

About one in five windows lit and one in five dim reads like the references; the rest dark.

## What the materials bring with them

The stone, cobble, pavement and slate materials are built in world space: weathering, soot runnels, low moss and grime follow real height above the ground (0 to about 2.8 m), so a wall's foot is damp and its upper courses clean without any painting. The stone image is one unique patch projected once over the whole place (`apply_by_role.py` stretches it to the place's size), so no two blocks repeat. Wetness is a coat on the road and pavement; the puddle film mirrors lamps when the look stage's lights are on.

## Traps

- Lay the place along Y, the long way, as the street is laid: the wall materials project their picture along Y and up Z. A place laid along X gets the picture smeared across its long walls (the procedural parts still work).
- The ground must be near Z = 0: the damp foot, moss and soot bands count metres above zero.
- An object with its own material and no role word keeps its material; the report's `unassigned` list says which.
- A merged mesh with several material slots gets one material in every slot. Build one object per role.
- `window` alone is a dark window. Say `window lit` for the ones that should glow.
- `stone` means a built stone wall, and a built wall is laid up in ashlar courses. A boulder, a rock or a reef is `rock`: name it so.
- The glass materials glow but do not light the street by themselves; that is the look stage's job (it finds every glowing pane and puts a real light outside it).
