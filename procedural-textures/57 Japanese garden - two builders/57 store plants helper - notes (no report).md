# Bridge and plants helper - notes

Started 22:42 (machine clock). Finish by 00:35.
Parts: arched_bridge, maple_tree, garden_pine, fern, bamboo_clump.

## 22:50 plan
- Read Store.md, Traps.md, Before you build.md, Board.md (photo 03 = the arched bridge), both builders' code
  (first pass render_final.py: bridge line 1110, maple leaf outlines 1345-1381, fern 1468, bamboo 1500, maple crowns
  on bare_tree 1530, pine 1599). Second builder made none of my parts.
- Shared module _shapes_garden_plants.py: leaf outlines (maple 7 lobes, toothed), leaf/needle/culm/sheath materials,
  red paint over the photographed planks (SURFACE old_planks_02 copy, paint mask inserted before Weather), bark copies
  of bark_willow_02, a helper to tag pp_piece per piece and point numbers.
- Bridge: foot_z = -0.5 (posts stand on the pond bed 0.5 m under the water); origin = water level.
- Look pictures go to plants/look/ with card.py --out (never the store's cards until final).
- 22:52 maple1 look (look/maple1): read as a tree with red leaves, but upright and narrow like a sapling, leaves sparse,
  pale pink-white sheen on the leaves (coat 0.25 mirrors the light), bare stem tips at the top.
- 22:54 maple2 look: crown spread wider (stems reach 0.55-0.85 of the half width, rise less), more branch pairs and
  twigs, a spray at each stem's end, coat 0.06, specular 0.3: reads as a layered Japanese maple; right side still a
  little pink-grey (the blue fill on red leaves). Then leaf 9 -> 10 cm, specular 0.15. 344k points, 3 s to build.
- 22:57 bridge1 look (look/bridge1, three and side): reads as a red Japanese arched bridge: stringers, deck boards
  stepping up, kerb/middle/hand rails, posts, capped end posts, frames with cap beams and ties, stone sills. Paint
  flaked too much (big grey patches on posts and stringers): peel 0.42 -> 0.385. 4288 points, 0.9 s.
- 22:59 pine1 look: reads as a niwaki, but the pads were smooth pale domes with a needle fringe only at the rim, white
  sheen spots (needle coat 0.35). Fixed: pad heart near-black and matte, tufts denser (6 cm apart), longer and wider
  spread needles, needle coat 0.1; trunk thicker (r 0.12). pine2 (23:00): pads read as dense bristly needle cushions.
  Foot ring dipped to -0.076 (tilted first ring): clamped to -0.03 (pine and maple).
- 23:01 fern1 look: reads as a fern but spread flat like a palm, pinnae thin and sparse, sheen spots. Fixed: fronds more
  upright (42-80 degrees, arching 62-112), 22-27 pinna pairs, wider pinnae, coat 0.05. fern2: a full shuttlecock clump.
- 23:03 bamboo1 look: reads as bamboo, foliage far too sparse, culms yellow-tan (too many old). Fixed: age biased young,
  branch zone from a third up, three fans a branch and two twigs with fans, thicker culms. bamboo2 (23:04): fuller;
  culm green made cooler.
- 23:05 next: tests/test_store_garden_plants.py, then the store cards and part files.
- 23:05 wrote tests/test_store_garden_plants.py (the parts test's checks for my five, plus each part's own claims).
- 23:06 measured every part and every option build; sizes written into the CARDs (maple 6.15 x 5.96 x 4.53,
  bridge 4.60 x 1.64 x 2.43, pine 2.84 x 2.51 x 3.53, fern 1.07 x 1.14 x 0.43, bamboo 3.14 x 3.43 x 5.98).
  Bamboo branches now carry their culm's age (they were 0, a false extra culm in the count).
- 23:07 drawing the store's four cards of arched_bridge (in the background: took over 2 minutes).
- 23:07-23:19 drew the store cards (four views each) of all five; looked at each: bridge, maple, pine, fern read well.
  Bamboo culms read tan-yellow: the waxy band blended over the whole upper half of each internode (no ring at its
  start) and the coat mirrored the amber key. Fixed: a band-start ring 7 cm under each node, coat 0.25, fewer yellow
  leaves (3.5 per cent withering). bamboo3 look: culms green with their node bands. Part files saved (23:19).
- 23:21 running tests/test_store_garden_plants.py
- 23:22 test FAIL: the bridge's along-Y frame was a mirror (scale -1): made it a turn; bridge file saved again.
- 23:22 bridge caps: 'MADE • old copper' read pink copper; made an old bronze material (dark brown metal, verdigris in
  streaks and hollows). bridge2 look: dull bronze caps.
- 23:23 maple green/orange looks: orange reads well; green had many red/yellow leaves (spray shading pushed tones into
  the turning stops) and pale leaves on the right. Fixed tones (4 per cent odd leaves only). Lowered see-through
  (0.3 -> 0.15 maple, 0.2 fern and bamboo) and sheen; the pale leaves on the right (rim light) are less but remain:
  the card's strong rim light through and on the leaves, washed pale by AgX.
- 23:24 redrawing the store cards of bridge, bamboo, maple and fern.
- 23:33 sizes final, part files saved again, plants test all PASS (exit 0). Running test_store_rules and test_store_parts (background, log in look/).
- 23:28-23:32 redrew the store cards of bridge, bamboo, maple, fern; looked at all 20 cards at full size: all read.
- 23:33 sizes final (bamboo 3.35 x 3.67 x 5.99, maple 6.08 x 5.99 x 4.53), part files saved, plants test PASS.
- 23:34 test_store_rules: the code check passes (107 files); the catalogue check fails as expected (session runs it).
- 23:35 removed my .blend1 backups; maple trap notes its 6,000 leaves / 340,000 points; unused imports dropped.
- 23:36 built every part at the edges of its options (bridge span 1.5-8, rise 0.15-1.25, width 0.6-2.5; maple
  fullness 0.1, height 2.5-7; pine pads 2-16; fern 3-25 fronds; bamboo 1-25 culms): all build, foot right.
- test_store_parts.py running in the background (log look/test_parts.log).
