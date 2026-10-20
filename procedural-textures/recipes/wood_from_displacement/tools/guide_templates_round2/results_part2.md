### 7.4 Joints and the lit look

![every joint of seed 1 at full size](sheets/joints_seed1.jpg)

`sheets/joints_seed1.jpg`, `joints_seed2.jpg` and `joints_seed3.jpg` hold one full-size crop (one dot = one dot, 300 x 300) of every joint. Round 1 found joints by looking for dark runs, which can miss faint joints; round 2 finds them **exactly** from the board numbers that the recipe writes (a joint is a place where the board number changes from one dot to the next one to the right, over at least 25 dots; the stepped parts of one joint share a crop): @@JOINT_PARTS@@ joint parts in the three tiles, on @@JOINT_CROPS@@ crops. I looked at every crop. What I see: every joint is a stepped joint or a straight joint with a ragged dark crack; no crop shows a plain wood-against-wood cut without some crack; the sideways part of a step reads as a crack along the grain. A few joints are faint (that is on purpose: `joints.darkness_variation`): there the cut shows as an abrupt change of grain with a thin dark hairline, and I did not count how many. Beside one joint of seed 3 (x 912, y 265) a darker block with a soft edge is a stain stamp that ends there. The vertical parts of some joints are still very straight over 60 to 90 dots.

![reference and new, lit by a low sun](sheets/lit.jpg)

The same raking light on the reference and on the new tile: @@LIT_READING@@

### 7.5 MAIN colour against COMPARISON colour

![three seeds, MAIN above, COMPARISON below](sheets/seeds.jpg)

Both versions use exactly the same arrangement, the same tone per board and the same patches. The COMPARISON colour is made from the height with three palettes (blue-grey, brown, orange; measured from the colour map itself, so only fair as a comparison) and two slow cloud patterns that choose where the orange and the blue-grey patches lie; the height alone cannot tell them apart. It differs from the colour map by Delta E @@CMP_DE@@ on average for seed 1 (@@CMP_DE95@@ at the 95th percent point; about 1 is just visible, 2 to 5 small, over 10 clearly another colour); round 1's single palette gave 4.7 and 11.0, so the new palettes are not closer dot for dot (the patches are random, not the map's own) but they bring back a good part of the orange and grey-brown variety (colour score of the same-kind tool @@CMP_COLOUR_NOW@@ against @@CMP_COLOUR_BEFORE@@ before). The blue-grey is still missing in one sense: in the table below no dot of COMPARISON is bluer than red, against 0.7 percent of the dots of MAIN (the uploaded map: 0.6 percent), because even the cool palette stays warm. In my eyes it is still plainer than MAIN: no crisp painted edges between colours, no small orange highlights.

@@COLOUR_TABLE@@

### 7.6 All maps of the default tile

![all maps](sheets/maps.jpg)

The roughness map shows the tone of every board as a faint block (roughness = a base + a part of the height + a small change per board; `roughness.board_variation`); there is no uploaded roughness map to compare with.
