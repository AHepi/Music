# Materials by role

What this file is: which role word gives which proven material, and how to name objects so `apply_by_role.py` dresses them without being told anything else. The materials come from the street bundle "Rain on the Old Curve" (`Materials.blend`, 45 materials, their six sandstone pictures packed inside; see `Material inventory.txt`).

## Name your objects with role words

Build plain shapes and put the role in the name: `left terrace 03 wall`, `window lit`, `window dark`, `door wood`, `kerb stone`, `lamp post iron`, `lamp glass`, `puddle water`, `roof slate`, `chimney smoke`, `tea urn brass`, `teapot china`. Or set the property `obj['place_role'] = 'wall'` in your build script, or give a roles file `{"object name": "role"}`. Pairs of words beat single words (`window surround` is trim, not a window; `lamp post` is iron, not a lamp).

| Role | Material | Words that mean it |
|---|---|---|
| wall | one of the 12 `Hand-painted sandstone • shade NN` (a different shade per object) | wall, brick, stone, masonry, facade, chimney; and, after every other word: terrace, house, tenement, building, shop, tower |
| plaster | `PLASTER • mineral flakes and scars` | plaster, render, limewash; and, after every other word: ceiling |
| trim | `STONE • worn honey-grey architectural dressings` | kerb, curb, sill, lintel, quoin, cornice, surround, dressing, trim, plinth, arch, cap; `window surround`, `door surround`, `chimney pot`; and, after every other word: trough |
| mortar | `MORTAR • dark eroded joints` | mortar, joint |
| road | `COBBLES • wet basalt / broken amber-blue reflections` | road, cobble, sett, street, lane, carriageway |
| pavement | `PAVEMENT • damp sandstone slabs` | pavement, flag, flagstone, footpath, slab, step; `door step`; and, after every other word: floor, quay |
| earth | `ROAD BED • damp grit` | earth, ground, yard, mud, soil, grit, track |
| roof | `SLATE • soot-dark irregular roofs` | roof, slate, tile, ridge |
| wood | three looks, chosen by name (see below): weathered boards, bark, or `WOOD • peeling dark painted doors` | door, shutter, frame, sash, beam, plank, board, cart, crate, barrel, timber, wood, wooden, fence; and, after every other word: trunk, bark, log, driftwood, deck, decking, jetty, pier, wharf, boardwalk, stilt, weatherboard, cladding, hull, canoe, boat, floorboard, table, chair, bench, stool, counter, shelf, cupboard, cabinet, dresser, butt, palm, tree, coconut |
| iron | `IRON • soot-black lamp posts` | iron, rail, pipe, bracket, gate, drain, metal, steel, wheel, chain, wire; `lamp post`, `lamp cap`, `down pipe`, `cart wheel`; and, after every other word: post, tank |
| rust | `RUST • rain-aged iron` | rust, rusty |
| window lit | `GLASS • warm occupied interiors` (glows, and the look stage puts a real light behind it) | `window lit`, `lit window`, `window warm` |
| window dim | `GLASS • dim amber rooms` (a faint glow) | `window dim`, fanlight |
| window dark | `GLASS • sleeping navy interiors` | window, pane, glass (alone) |
| lamp glass | `Lantern • glowing imperfect amber glass` (glows; the look stage adds the gas mantle and its pavement wash) | `lamp glass`, `lamp head`, `lamp pane`, lantern |
| flame | `LAMP • honey flame glow` | mantle, flame, fire, glow |
| water | `PUDDLE • shallow transparent reflective film`; water bigger than 6 m² is still water and gets its banks dressed (see below) | puddle, water, gutter; and, after every other word: pond, pool, river, canal, lake, stream, creek |
| rock | `STONE • unique sandstone / damp soot` (natural stone: never built up into ashlar) | boulder, rock; `reef stone`, `cliff stone`, `crag stone`, `outcrop stone`, `headland stone`, `shore stone`, `field stone`; and, after every other word: reef, cliff, headland, crag, outcrop |
| sand | `ROLE • damp sand`: a photographed damp sand (made in code if the scans are missing; dark, so a fire nearby does not turn it to snow) | sand; and, after every other word: beach, dune |
| sea | `ROLE • dark sea with small waves` (made in code); its edges get foam, a wet band, a wrack line and driftwood (see below) | `sea water`, `ocean water`, `lagoon water`, `harbour water`, `harbor water`, `salt water`; and, after every other word: sea, ocean, lagoon, harbour, harbor |
| moss | `MOSS • subdued olive crevices` | moss, algae, lichen |
| grime | `GRIME • dark damp organic residue` | grime, soot, stain, dirt; `wall foot` |
| recess | `RECESSES • near-black blue` | recess, void, inside, interior, dark, shadow |
| smoke | `Chimney smoke • organic soft wisps` (a volume: give it a box above the chimney) | smoke, haze |
| weed | `Weed • rain olive` | weed, grass, ivy; and, after every other word: frond, foliage, canopy, bush, shrub, hedge, fern, reed |
| leaf | `Fallen leaf • ochre` | leaf, leaves, litter |
| paper | `PAPER • aged torn fragments` | paper, poster, notice |
| brass | `ROLE • old brass` (made in code): polished where handled, tarnished in patches and in every hollow, each object its own patches | brass, bronze, gilt, gilded, gold; and, after every other word: urn, samovar |
| copper | `ROLE • old copper` (made in code): as brass, warmer, with blue-green verdigris deep in the hollows | copper, verdigris; and, after every other word: kettle |
| china | `ROLE • glazed china` (made in code): a glossy glaze over cream, pale blue-white or a teapot's dark brown, chosen per object | china, porcelain, ceramic, crockery, earthenware, stoneware, pottery; `tea pot`, `coffee pot`; and, after every other word: teapot, teacup, cup, saucer, mug, jug, vase, bowl |

About one in five windows lit and one in five dim reads like the references; the rest dark.

Words that name a thing rather than what it is made of are read after every other word, so the material word wins: `boat hull rust` is rust, `paopao hull timber` is wood, `river bank earth` is earth, `jetty deck` is wood, `harbour wall stone` is a wall, `beach hut timber` is wood. In that order, last of all: urn, samovar (brass); kettle (copper); teapot, teacup, cup, saucer, mug, jug, vase, bowl (china); trunk, bark, log, driftwood, deck, jetty, pier, wharf, boardwalk, stilt, weatherboard, cladding, hull, canoe, boat, floorboard, table, chair, bench, stool, counter, shelf, cupboard, cabinet, dresser (wood); frond, foliage, canopy, bush, shrub, hedge, fern, reed (weed); palm, tree, coconut (wood, with bark); floor, quay (pavement); ceiling (plaster); trough (trim); post, tank (iron); pond, pool, river, canal, lake, stream, creek (water); sea, ocean, lagoon, harbour, harbor (sea); beach, dune (sand); reef, cliff, headland, crag, outcrop (rock); terrace, house, tenement, building, shop, tower (wall).

The metal and china words come before every other word, so they beat even `door` and `pipe`: `brass door handle` is brass, `copper pipe` copper, `china jug` china (and a `china cabinet` is china: call it `cabinet wood`).

Three more rules: a plural counts as its singular (`floor flags` is a pavement, `sea rocks` is rock); natural stone named with `stone` stays rock (`reef stone`, `cliff stone`, `shore stone`, `field stone`); and a container of water is not water (`water tank` is iron, `water butt` wood, `water trough` trim). `sea water`, `harbour water`, `salt water` are the sea.

## Timber's three looks

A wood-role object gets one of three looks, by the words in its name (`lay_timber.timber_kind` decides):

| Look | Which objects | What it is |
|---|---|---|
| painted | names with door, shutter, sash, frame, casing, window, surround, jamb, architrave | the street's `WOOD • peeling dark painted doors` |
| bark | names with trunk, bark, palm, tree, coconut, branch, bough (a mast, a flagpole or a column is not a tree) | `SCAN • wet palm bark` (palm, coconut) or `SCAN • wet furrowed bark`, from photographs; without the scans, `TIMBER • wet ringed bark` (made in code) |
| boards | every other wood thing: walls, decks, piles, posts, planks, fences, boats | `SCAN • weathered boards, peeling paint`: a photographed weathered wood, each board its own patch and shade, rain streaks, one faded paint per building left in cracked, peeling patches; a deck or floor that is one flat slab gets `SCAN • weathered deck planks`. Without the scans, `TIMBER • weathered boards, peeling paint` (made in code) |

A plain timber wall (one flat slab, thin, taller than 1 m) is laid as overlapping boards with casings round its windows and doors, a sash with glazing bars in each window, corner boards, and nail lines that bleed rust. Timber built from many separate boards gets a shade per board instead.

## Windows in plaster walls

A window standing in front of a `plaster` wall the camera faces gets the joinery it has there: a painted timber casing round the opening, a sill with the dark line of its drip under it, and a sash whose glazing bars cut the glass into panes about 0.45 m wide and 0.5 m tall, with a meeting rail when the window has a sash window's shape (taller than about 0.9 m, no wider than 1.6 m). A shop or tea-room front of big panes reads as many small ones, and draws less glare. Whatever you built yourself is kept and not doubled: bars over the glass (your own sash), a frame bigger than the glass all round (your own surround), a thin piece just under the glass (your own sill, or the beam a timber frame sets the window on). The plaster itself is left as it is.

## Water's edges

The dressing looks straight down over what the camera sees to find where water meets ground, so a sloping beach, a flat one, a river bank and a garden pond all work, whatever the ground is called. `sea` (salt water) gets a wet, glossy band of ground along the waterline, foam lace and a wandering swash line, broken surf lines further out, a wrack line of seaweed, sticks, husk fibre, shells, coral and a few modern scraps, and driftwood. `water` bigger than 6 m² (a pond, a river) gets a narrow wet bank, moss along it, and leaves washed against it and floating near it: no foam. Rocks, posts, walls and hulls standing in either are dark and wet up to the high-water line, with a slime band where the water stands.

## Scanned surfaces

The timber, bark, sand and driftwood come from free photographed scans (Poly Haven, CC0) kept in `materials/textures/` (see `Textures.md` there), and the street's stone materials (wall shades, dressings, flags, rocks) are given a real sandstone's grain over their own colours. `--no-scans` dresses without them.

## What the materials bring with them

The stone, cobble, pavement and slate materials are built in world space: weathering, soot runnels, low moss and grime follow real height above the ground (0 to about 2.8 m), so a wall's foot is damp and its upper courses clean without any painting. The stone image is one unique patch projected once over the whole place (`apply_by_role.py` stretches it to the place's size), so no two blocks repeat. Wetness is a coat on the road and pavement; the puddle film mirrors lamps when the look stage's lights are on.

## Traps

- Lay the place along Y, the long way, as the street is laid: the wall materials project their picture along Y and up Z. A place laid along X gets the picture smeared across its long walls (the procedural parts still work).
- The ground must be near Z = 0: the damp foot, moss and soot bands count metres above zero.
- An object with its own material and no role word keeps its material; the report's `unassigned` list says which.
- A merged mesh with several material slots gets one material in every slot. Build one object per role.
- `window` alone is a dark window. Say `window lit` for the ones that should glow.
- A name with `window` in it is a window, so your own sash bars named `window sash` would glow or darken like glass: call them `sash bars wood` (and a surround `window surround stone`, which is trim).
- `stone` means a built stone wall, and a built wall is laid up in ashlar courses. A boulder, a rock or a reef is `rock`: name it so.
- The glass materials glow but do not light the street by themselves; that is the look stage's job (it finds every glowing pane and puts a real light outside it).
- A tree's living leaves are `frond`, `foliage` or `canopy` (the weed material); `leaves` is the fallen-leaf material. `palm` or `tree` alone gives bark: build the trunk and the leaves as two objects.
- Water that is cut level with the ground leaves no edge to find: slope the sand or bank down under the water, or leave a gap where the water shows. A straight cut still gets a wandering swash line, but it reads straighter than a shaped beach.
- `pond` and `river` are still water only when bigger than 6 m²; smaller water is a puddle. Water standing taller than it is wide (a waterfall, a tank of water) gets no edges.
- Only ground with a role counts as a shore (sand, earth, rock, grass, moss, a pavement or road), and only up to 1.5 m above the water: a quay top, a deck, a moored boat or a palm top gets no tide line, foam or driftwood.
- The edges are dressed where the camera sees them, nearer than about 70 m. Move the camera and dress again.
