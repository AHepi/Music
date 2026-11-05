# Materials: a barn on a farm

What this file is: the material list for the place, written before building and kept true while building. One line per surface or thing: what · made of · how it has aged · where the wear sits · which surface it uses.

## Who uses this place

- **Who is here (not in the picture):** an old carter and a young woman farm hand, about 1915, on a small mixed farm in the south of England; the farmer's sons have gone to the war.
- **What they do all day:** milk the cows at dawn and dusk, muck out the cow house, cart roots and dung, fork hay down from the barn for the horses and cows, mend things in the barn's doorway.
- **What they left when they stepped out of frame:** the evening milk in two churns by the cow-house door, waiting for the morning cart to the station; a lit hurricane lantern hung on a nail by the barn door, because one of them has gone inside to fork hay down and will come back; the cart unhitched in the yard, shafts resting on the ground, an empty sack in it; a pitchfork leant against the barn wall by the door; a wheelbarrow of muck by the cow-house door, from mucking out; a besom and a bucket against the cow-house wall; forkfuls of hay dropped on the way from the barn to the cow house.

## The place

A farmyard after rain at dusk. A lane of trodden mud runs from the eye to the gable end of a big timber barn on a brick plinth, its tall cart doors open and lit from inside. On the left a dry-stone wall with a five-bar gate into a field; on the right a low limewashed stone cow house with a lean-to iron roof.

## Surfaces and things

| what | made of | how it has aged | where the wear sits | surface used |
|---|---|---|---|---|
| barn walls (gable end and sides) | sawn lapped weatherboards, tarred long ago | tar weathered off to grey, boards split and cupped, a few sprung | damp dark line and mud splash on the lowest boards; rust runs below the nails; boards round the door rubbed pale | store tool `lay_boards`, `MADE • weathered boards, peeling paint`, darkened copy |
| barn plinth | red brick in lime mortar, 0.5 m high | soft, mortar eroded from the joints | mud splashed up its foot; green damp at the ground; corners knocked by cart wheels at the doorway | `SURFACE • brick_wall_02` (Wet and Mud dials up) |
| barn roof | Welsh slate in courses on battens | wet sheen, some slates darker | darkest at the eaves where water runs off; the ridge pale against the sky | `MADE • slate roof` |
| barn eaves, barge boards, rafter tails | sawn softwood | greyed like the walls | ends of rafter tails darkest | `lay_boards` eaves |
| barn cart doors (two tall leaves, one swung open, one ajar) | vertical planks on ledges and braces, iron strap hinges | greyed, bottoms rotted ragged and darker | rust runs down from each strap hinge; pale rub at hand height by the meeting edge; mud on the lowest 30 cm | made in code, `SURFACE • old_planks_02`; hinges `RUST • rain-aged iron` |
| loft door above the cart doors | planks on ledges, shut | greyed | rust under its hinges | made in code, `SURFACE • old_planks_02` |
| barn inside | timber posts and a tie beam; hay stacked to the beams on both sides; loose hay on an earth floor | dusty, the hay gold where the lantern reaches it | hay trodden flat in the middle of the floor where the carts go | made in code: posts `SURFACE • rough_wood`, hay made in code (straw colour, stringy bump) |
| lantern at the door | tin and glass hurricane lantern, lit | sooted globe | hangs on a nail at the right of the door | store part `hurricane_lantern` |
| cow house walls | rubble stone, limewashed | limewash flaking off in patches to show the stones | wash mostly gone on the lowest 60 cm (muck splash, damp), brown stain at the foot; green damp at the corner | made in code: stones in relief, limewash mixed by noise |
| cow house roof | corrugated iron, lean-to | rusted | rust streaks running down to the eaves, darkest at the overlaps | store tool `lay_boards` lean-to, `SURFACE • rusty_corrugated_iron` |
| cow house door | stable door in two halves, planks, old dark paint | paint peeling, bottom rotted | top half open (dark byre inside); scuffed pale at the bottom by boots and the barrow | made in code, `WOOD • peeling dark painted doors` |
| cow house window | small square hole with a board shutter | shutter warped | open a crack | made in code, `WOOD • peeling dark painted doors` |
| dry-stone wall (left) | flat grey-brown stones piled without mortar, cope stones on edge | settled, some stones slipped | moss on the cope and the shaded face; darker and wet at the foot; two fallen stones at its foot | made in code: stones in relief, own stone material with moss on top faces |
| five-bar gate and posts | ash bars on oak posts, iron hinges | greyed, sagging on its hinges | top bar polished pale where hands lift it; hinge rust | made in code, `SURFACE • rough_wood` |
| yard ground | earth trodden to mud | wet after rain | cart ruts holding water down the lane, hoof prints between them, boot prints between the cow house and the barn; straw pressed in by the doors | store tools `ground`, `tracks`, `MADE • dirt, dark` |
| puddles | rain water in the ruts and hollows | standing since the rain | ragged edges, wet rim, faint ripple; the long one in a rut mirrors the barn door | store `ground.fill` (`MADE • puddle water`) |
| grass and weeds | grass, nettles | wet, dark, yellowed at the tips | along the foot of the walls and in the field, none in the ruts or the trodden middle | store tool `grass` |
| stones in the yard | pebbles and grit | wet, dark | gathered in the hollows and at the wall feet | store tool `stones` |
| dropped hay | dry straw and hay | gold, trodden dark into the mud at the edges | a trail of forkfuls from the barn door to the cow-house door | made in code |
| farm cart | timber cart, two spoked wheels with iron tyres | boards worn, paint mostly gone | mud on the wheels and tyres; an empty sack in it | store part `coal_cart` (empty, shafts down) |
| milk churns (two) | galvanised steel | dull, dented | rust at the foot ring | store part `milk_churn` |
| wheelbarrow with muck | timber barrow, iron-tyred wheel; dung and straw | boards greyed | muck heaped in it | store part `wheelbarrow` (empty) + muck made in code |
| pitchfork | ash shaft, iron tines | tines rusted | shaft polished pale where hands hold it | made in code |
| besom and bucket | birch twigs on an ash pole; zinc bucket | twigs worn short on one side | against the cow-house wall | store part `besom_and_bucket` |
| sky | dusk: amber low, teal-blue above, streaky cloud | | the glow low on the left over the field | store tool `sky_and_haze` |
| air | thin cool haze | | thinning with height | store tool `sky_and_haze.haze` |
| hedge beyond the field | hawthorn hedge | | a dark silhouette against the amber glow | made in code |

## Kept true while building

Changes made during the build, so the list matches the picture:

- **The cart is inside the barn, not in the yard.** In the yard it was a dark lump in front of the cow house; inside, its spoked wheel and sideboards stand dark against the lit hay. Store part `coal_cart`, empty, shafts resting on their props, turned side-on so the wheel faces the eye.
- **Added inside the barn:** a hay ladder leant on the hay mow (made in code, `SURFACE • rough_wood`); a wall of hay across the back of the bay and two loose heaps on the floor (made in code); a second hurricane lantern hung on a post (store part).
- **Added to the gable:** three narrow slits for air high up, each with a sill and head board (made in code, `RECESSES • near-black blue` and the door planks).
- **Added to the barn front:** mud splashed up the lowest boards above the plinth and a damp stain under the eaves on the left (store tool `stain`). They hardly show at the final size.
- **The pitchfork moved** from the barn wall (where it was too thin to see at 19 m) to lean on the cow-house wall by the window, behind the barrow. It is still hard to name at full size.
- **A second lit lantern** hangs on a nail by the cow-house door (store part `hurricane_lantern`, 35 W): it lights the churns, the barrow and the stable door. The light first put inside the cow house was shut inside its solid walls and lit nothing; it was taken out.
- **The cow house's open top half door and the window** show a near-black recess behind them (they showed pale plaster before).
- **The cow house's fascia** uses a darker copy of the boards (it read as a pale concrete slab).
- **The yard is wetter** (the ground's wetness 0.88, after rain): both ruts now hold water down the lane; the cart ruts are three passes deep, not five (five read as trenches).
- **Grass** also grows on the lane's sides and thinly in the strip between the ruts (store tool `grass`), none in the ruts or on the trodden path.
- **Dropped hay** is laid as trodden forkfuls (dense tangles, the outer strands pressed dark into the mud), not as single scattered strands (which read as asterisks): a big spread at the barn threshold, a trail to the cow-house door, a few by the barrow, one near the eye; straw on the muck in the barrow.
- **The muck in the barrow** is rougher and browner (it was glossy and read as grey).
- **The dry-stone wall** starts nearer the lane by the eye and runs out to the gate, so it comes into the frame lower down; its cope stones are chunkier and lean (thin ones read as a picket fence).
- **The five-bar gate** is hung on the far post and swung part open into the yard (swung into the field it hid behind the wall).
- **The hedge** is a ragged strip, not a row of round bumps (those read as balloons).
- **The haze** is two boxes: in front of the barn and far beyond it, none inside the barn (inside, it turned the hay into glowing fog).
- **The besom and bucket, and the sacks,** stand behind the barrow and churns and are mostly hidden from the eye.
