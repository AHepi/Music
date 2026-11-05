# The parts helper's report (barn additions to the store, 5 November 2026)

What this file is: the last message of the helper that turned the barn builders' things into store parts, saved by the session.

I made all eight parts, and the full parts test passes: 34 parts, including the eight new ones. I looked at every new part from all four sides and fixed what read wrong before drawing its final cards and saving it. I did not run the catalogue or touch the tools, tests, Store.md or Materials.blend.

**The parts.** Sizes are at the default options.

1. **plank_door**: 1.06 × 0.10 × 2.0 m.
   - Options: width (1.0), height (2.0), angle (0 means shut; a positive angle swings it out towards the front, the way barn doors open), hinges ('left' or 'right', seen from the front).
   - Origin: the middle of the doorway at the foot, not the hinge edge suggested. The parts test wants a part's default build centred on its origin, and the doorway's middle is just as handy for a builder. The card's trap says so.
   - Fixed from the builder's door: each plank is its own piece of wood with its own shade, a few rotted at the foot, small gaps between them. The braces sit on the ledges and rise from the hinge side. Real strap hinges hang on pins, with bolt heads, plus a thumb latch, nail heads and rust run down under the straps. The builder's right-hand door was a flipped copy, which turns a photographed surface inside out; nothing is flipped now.
2. **ladder**: 0.51 × 1.06 × 3.47 m.
   - Options: length (3.6).
   - How it stands: it leans back about 15 degrees. Its origin is the foot of the wall its top rests on, so its top touches the wall at any length; the card and trap say so.
   - Fixed: square boxes became rough, slightly bowed rails narrowing upwards, round rungs driven through them, and iron tie rods.
   - Test note: like the teapot sign, its card marks that its origin is not its middle (foot_z 0.0). Because of that the parts test skips its "centred on the origin" check, as it does for the sign.
3. **fork**: 0.18 × 0.43 × 1.61 m.
   - Options: kind ('pitch' or 'root'), pose ('leaning' or 'lying'), tines (0 gives each kind its usual number: 3 on a pitch fork, 4 on a root fork).
   - How it stands: a pitch fork leans with its tines up; a root fork stands on its tines with its D handle up.
   - Fixed: straight sticks became a shaped shaft, an iron socket strapped and riveted on, curved tapering tines (broad and flat on the root fork), a bent D handle, and a shaft rubbed pale where hands hold it.
4. **skep**: 0.58 × 0.58 × 0.48 m.
   - Options: filled (True).
   - Fixed: twenty finer woven rows instead of ten thick bands, a rope-like border, twisted handles, a woven base, and a pale rim kept from the builder's version.
   - Roots: the roots lie across the basket, because end-on they read as round fruit.
5. **mangold_heap**: 1.94 × 1.30 × 0.70 m.
   - Options: width (1.8), depth (0.9), height (0.65), loose (5 roots rolled out in front).
   - How it sits: its back is flat for a wall; the trap says where.
   - Fixed: the "peaches" problem. Roots are now long, slim and tapering, dull orange to red, each its own colour, with soil on their tails. Half the tails are broken short, because whole tails stuck out like spikes. There is dark earth between the roots.
6. **hay**: 3.10 × 2.65 × 2.57 m as a bay.
   - Options: kind ('bay' or 'heap'), width (3.0), depth (2.0), height (2.4). A heap uses its own sizes, 1.6 × 1.4 × 0.9, unless given others.
   - Fixed: the plain glowing block became a bulging, softly layered face with a sagging top and straggling edges. Thousands of stalks lie over a dark fibrous mass, and loose hay lies in side-by-side clumps at the foot, never spread out like stars.
   - Trap: light it from one side, and keep haze out of the barn, or it reads as fog.
7. **bare_tree**: 10.5 × 8.7 × 12.0 m.
   - Options: height (12).
   - Fixed: the builder's tree was straight cones forking at the same angles. Branches now curve and taper and spring all along each limb, the trunk has a flared foot, and fine twigs make the crown's edge. Its top lands exactly at the height asked.
8. **corrugated_sheet**: 0.76 × 0.03 × 1.83 m.
   - Options: width (0.76), height (1.83), rust (0.7), warp (0.3), lying (False).
   - How it sits: upright, its back on a wall at +Y; or lying flat with its top edge towards +Y. The card says which is which.
   - Fixed: real corrugations, nails on the crests with washers, and a rust setting that runs from grey zinc to rusted all over (eaten through along the bottom edge at full rust). The builder's nail heads floated off the sheet; these sit on it.

**What still doesn't read perfectly:**
- From the side and back, the hay bay looks greyish under the card's blue fill light. Those faces are meant to sit against walls.
- The tree's twigs bunch a little at the ends of the branches.
- Close up, the mangolds still look somewhat like big carrots, though no longer like peaches.
- The heap's back is a flat dark face, meant for the wall.

**Mistakes made and fixed along the way:**
- Adding a number layer to a mesh after making its points broke those points; the layers are now made first.
- The parts test reads an option's default only up to a semicolon, so "(default 0.76: …)" couldn't be read; it is now "(default 0.76; …)".
- An apostrophe in a choice option's text ("the bay's posts") was read by the test as a choice; reworded.
- On wide doors the braces stuck out past the edges until their ends were fitted inside.

**Files created** (nothing existing was changed), in `plugins/painted-place/brief/store/`: `parts/src/` _shapes_barn.py, plank_door.py, ladder.py, fork.py, skep.py, mangold_heap.py, hay.py, bare_tree.py, corrugated_sheet.py; `parts/` one saved part file per part (8 files); `cards/parts/` 32 card pictures.
