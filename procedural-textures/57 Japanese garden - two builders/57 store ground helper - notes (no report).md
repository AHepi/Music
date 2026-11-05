# Ground and water helper - notes (garden 57)

Started 22:42 (machine clock). Finish by 00:35.

Job: lay_slab_path, bamboo_fence, water_lilies, far_hills (new tools); maple kind in litter.py;
stronger mirror + pale-ring fix in puddle.py; tests/test_store_garden_ground.py; cards.

## Log
- 22:42 started; reading Store.md, Traps.md, Before you build.md.
- 22:46 read Store.md, Traps, Before you build, Board.md, both builders' reports and their slab/fence/lily/hill/leaf code,
  _lines.py, lay_kerb.py, litter.py, puddle.py. Puddle water: IOR 1.333, spec 0.5 (reads black from above).
  Plan: slab path first (owner's second picture), then litter maple, puddle mirror/ring, fence, lilies, hills, tests, cards.
  Slab path idea: each slab = outline (corners knocked off, edges wander inward) + rings to its middle; top relief +
  1-2 hollows; water = flat sheet at a level below the stone round its inner ring, so the stone's own relief cuts its edge.
- 22:50 slab_01/02 (420, 16 samples): slabs read; rows too regular -> skewed row joints, bows and bites in outlines.
  Joints rust-orange -> Darken x0.5 and greener moss. Stone like crinkled foil -> no extra normal/bump, gentler relief.
- 22:53 water bug: the 'lowest' point was on the worn edges, so hardly any slab held water; fixed (inner rings only).
  The 'water' number also wrongly counted the worn edges; fixed. Wet slabs now chosen by share (quota), not chance.
- 22:55 slab_close_03: puddles show but read as round black holes (card world is dark) -> two dips per puddle,
  ragged hollow, grain at the water's edge, wider clear shore (11 mm).
- 22:59 maple_01: maple leaves on the slab path + swept heap read as maple leaves (seven toothed lobes). Some leaves
  pale lilac (mirroring the blue fill and rim light) -> specular 0.22 -> 0.14, coat 0.06 -> 0.03, rougher.
  Puddles still black on the card stage (dark world): the card camera must catch the rim light in a puddle.
- 23:02 fence_01: lattice (yotsume-gaki) and close (misu-gaki, new canes) both read as bamboo fences.
- 23:03 fence_close_01: joints invisible -> ridge 13% proud, dark ring with a pale waxy band beside it. Ties read as
  small dark knots (fine at film size).
- 23:05 lilies_01: pads drew red (faces looked down, the underside colour showed) -> every face turned up. lilies_02 good.
- 23:08 hills_01..04: layers read; near ridge was all haze-grey (glow too strong) -> haze 400 m, glow 0.7, peaks
  (60, 220), mist rising from each ridge's foot to its crest: dark crests over misty bands.
- 23:11 PROOF: prove_same.py builds litter (default, seeds 0 and 3, all three old kinds) and puddles (flat, on ground,
  level, no film) with the old copies and the new tools: 262 arrays (points, every number, shapes, meshes, materials)
  identical. (First run showed material differences: my check used Python's per-run random hash; fixed with crc32.)
- 23:14 puddles_01 (135 s, too slow: 8 m ground): left as before (dark), right mirror 0.7 + no_ring: mirrors sky and
  the card's rim light strongly. Could NOT make the pale ring appear in my test picture, so no_ring is checked only by
  its numbers (matte film copy, narrow rim), not against the builders' failing picture.
- 23:16-23:19 tests/test_store_garden_ground.py: fixes on the way: test read object places before Blender updated them
  (test bug); slab on ground test hit a water hollow (test now water=0); maple leaves landed on slab sides and
  undersides (the stone tool's surface flips down-facing faces up) -> slab sides get their own points and the
  underside is left out. ALL PASS 23:19.
- 23:20-23:26 CARDS drawn into brief/store/cards/tools/: lay_slab_path.png (high view: two puddles mirror the card's
  back light, the rest read dark: there is no sky on the card stage; tried a dusk sky and looking back at the key:
  neither better), bamboo_fence.png, water_lilies.png (first try: shiny pads flared white like paper and too many
  yellow -> waxy pads, fewer yellow, closer camera), far_hills.png (the store's dusk sky as world, card lights kept).
- 23:28 slab water was the store's puddle water (opaque dark mirror) -> black holes wherever nothing bright is
  mirrored. Made clear_water(): a copy made clear (transmission), the stone seen through a little darker, the mirror
  raised. Now the slab path's default. Card redrawn 23:30: no black holes; two puddles mirror the back light.
- 23:30 test_store_garden_ground ALL PASS again; test_store_tools PASS; test_store_rules: rule check PASS, catalogue
  check fails as expected (the session runs catalogue.py).
