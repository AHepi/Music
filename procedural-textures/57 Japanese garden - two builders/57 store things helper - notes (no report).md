# Garden things helper - notes (build 57 garden)

Started 22:42 (machine clock). Finish by 00:35.
My parts: stone_lantern, water_basin, jar, clogs, hanging_lantern, wooden_bucket, bamboo_broom
Shared module: _shapes_garden.py. Test: tests/test_store_garden_things.py

## Log
- 22:42 started, made scratch folder.
- 22:48 read Store.md, Traps, Before you build, Photographed.md, the board (07 lantern + basin, 06 lanterns), both builders' code
  (stone lantern, basin+spout+ladle, jar material, clog(), hanging_lantern(), broom(), bucket). Parts test: foot at card foot_z
  within 6 cm, size within 25%, every option's other values built, nothing floating, 4 cards, part file.
- Plan: shared _shapes_garden.py (Shape with pp_piece per piece; granite = SURFACE dark_rock_02 copy -> weathering.stone
  streaks -> moss.add; bamboo culm made in code with 'culm' vector attr; paper lit/unlit; still water; falling water).
  Wood: SURFACE rough_wood (grain along object Z on sides; geta built in a local frame with Z along its length).
  hanging_lantern: origin at the hook, foot_z fixed (all kinds same drop) because the parts test cannot move the foot.
- 22:52 look sl1: kasuga lit, 300px 10 samples
- 22:54 look wb1: water_basin round, 300px 10 samples
- 22:56 look jar1
- 22:59 look cl1 (clogs) + jar2 close
- 23:01 look hl1 (hanging box, round) + clogs2
- 23:02 hanging lantern was drawn under the card's ground (origin at the hook, all below z=0): moved origin to its foot, hook 0.8 m up. look hl2
- 23:03 look wk1 (bucket)
- 23:04 look bb1 (broom)
- 23:05 broom fan too sparse (120 twigs): 230 twigs, thicker, 2-4 side twigs each
- 23:06 wrote tests/test_store_garden_things.py: all 7 PASS first run (20 s)
- 23:07 look mix2: kasuga lit, yukimi, jar3 close, broom2 close
- 23:08 jar flowers read as plain circles: five deep petals (|cos 2.5 theta|), thicker stems
- 23:09 jar flowers were circles because the voronoi Position is already in metres (I divided it by the scale again): 2D voronoi, distance measured myself
- 23:10 look mix3: square basin, broom3, clogs scattered
- 23:10 moss cushions read as yellow leaves (store's green-gold moss): own dark fuzzy moss material
- 23:14 store cards: stone_lantern drawn (2m37s); the other six running in the background
- 23:16 card sizes corrected (hanging_lantern 0.36 wide, wooden_bucket 0.46 deep); removed a dangling node in tinted()
- Status at 23:16: all 7 parts built and saved (.blend), own test passes, stone_lantern cards drawn and looked at
  (lotus base, banded post, fire box windows, curled cap, moss). Remaining: other six cards (background), look at each,
  run test_store_parts.py and test_store_rules.py after the cards, report.
- 23:16 basin cards: moss cushions read as pale grey discs (sheen): sheen off, darker green; basin cards to redraw after the batch
- 23:19 jar cards looked at: five-petal flowers on stems, lotus panels, collar, neck band, lid; reads as blue-and-white. stone_lantern given sunk back panels (cards to redraw)
- 23:22 clogs cards: reads as geta, but the foot marks hardly show: darker, fully mixed from 0.6, a little polished; clogs cards to redraw
- 23:24 hanging_lantern cards looked at: chain, flared copper roof, lattice over glowing paper, tray: reads
- 23:26 wooden_bucket cards looked at: staves each their own part of the wood photo, copper hoops, handle bar, dipper: reads
- 23:28 redrawing stone_lantern, water_basin, clogs cards (background)
- 23:29 test: lantern height now printed as measured
- 23:30 report draft points (in case of restart):
  made 7 parts + _shapes_garden.py + tests/test_store_garden_things.py; calls in each CARD.
  photographed: lantern+basin stone (dark_rock_02, each stone pp_piece, rain streaks, moss), clogs wood (rough_wood, grain along
  the board) + thongs (rough_linen tinted), lantern frame + bucket staves (rough_wood, each stave pp_piece). In code: bamboo,
  paper, porcelain painting, water, moss cushions (no such photographs on the shelf).
  mistakes fixed: hanging lantern under the card ground (origin moved to foot); jar flowers circles (voronoi position scaled
  twice); lantern curls too big; moss cushions yellow then pale (own moss, no sheen); bamboo like plastic pipe; broom sparse;
  clog foot marks faint; foot stones glare.
  test_store_rules: PASS rules, catalogue check fails (expected until catalogue.py).
- 23:31 stone_lantern redrawn: sunk back panels show in the side view
- 23:33 water_basin redrawn: moss cushions now dark green mounds
