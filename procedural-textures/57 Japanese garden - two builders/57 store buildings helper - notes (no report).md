# Buildings helper - notes (garden 57)

Tools: lay_tile_roof, lay_shoji, lay_veranda. Finish by 00:35.

## Log
- 22:42 started; scratch folder made.
- 23:08 read Store.md, Traps, Before you build, Board.md, owner's picture, builder 1 roof() (one slope, rolls as tubes,
  front only). Plan: lay_tile_roof builds each slope from a height function (concave profile, corner lift), pan tiles as
  stepped quads (one pp_piece each), rolls as half tubes per course, round end discs, ridge stacks + onigawara,
  fascia, boarding, rafters, wall-top beams, gable triangles (plaster + timber), bargeboards. Writes box['tile_roof_under']
  so lay_veranda can set its beam under the eave. Materials: tiles = copy of SURFACE dark_rock_02 (wet, finer),
  timber = SURFACE old_planks_02 (turned copies via lay_stone.turned_along), plaster = SURFACE worn_plaster_wall.
- 22:58 first roof pictures: reads as irimoya; tiles brown -> cool grey copy; timber darker copy; gable bigger (GABLE_AT 0.34)
- 23:04 fixed small gable (its front row was at a wrong u), Darken is a multiplier (lower = darker): timber 0.5, tiles 0.8; fascia set 7 cm in under the tile ends; end discs 4 cm out
- 23:12 lay_shoji first picture reads as shoji (panels, lattice, kick boards); lit paper too cream-white -> warmer orange, strength 1.7
- 23:24 lay_veranda first picture reads (posts, beam under eave, floor, short posts, step). Stones were plain boxes -> rough_stone (rounded uneven outline, worn edge, tipped top)
- 23:17 tests/test_store_garden_buildings.py all PASS (fixed: stale object in test; long boards near the step all worn -> boards cut at the step; step check caught post stones)
- 23:27 card script scripts/cards.py; first roof card looks/card_roof_1.png reads (irimoya, lifted corners, small front gable a little weak)
- 23:22 first cards copied into the store (roof 1, shoji 1, veranda 2); shoji lit paper deeper/warmer (strength 1.15, base darker); veranda card camera raised to show the floor's wear
- 23:26 tests/test_store_tools.py PASS (exit 0); rules test passes all but the catalogue check (expected until the session runs catalogue.py). Pan tiles now dished; gables' plaster a paler copy; front_gable refused when the ridge runs front to back
- 23:28 roof card 4 (whole roof in frame, 24 samples) copied into the store
- 23:30 shoji card 3 copied (lit paper colour (1.0,0.36,0.09) strength 1.5)
- 23:32 veranda card 3 copied
