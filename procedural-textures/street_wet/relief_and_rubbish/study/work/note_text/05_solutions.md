## 5. The solutions I built and measured

### 5.1 The joint picture (solution 1: free, works in every renderer, works in the glb)

**What it is, with an example.** A real joint between two stones is dark and dull whatever the weather: it is a narrow crevice, full of earth and moss, and the light barely reaches it. So: lay one more flat picture over the road, a **joint picture** (grey: white in the joints, black on the stone faces, a soft edge), through the road's own texture coordinates, and use it AFTER the wetness layer, so wetness has no say:

* **colour** is multiplied by a number below 1 in the joints (the joint is darker than the stone);
* **roughness** is pulled toward 0.9 in the joints (no smooth water film: dull);
* **specular** (the reflection strength) is multiplied by a number below 1 in the joints;
* **clear coat** (the water film's reflection) is multiplied by a number below 1 in the joints;
* **in a puddle** the dulling of roughness, specular and coat is cut by 0.8 times the puddle mask (a puddle's water covers the joint and mirrors the sky), but the dark colour stays (you see the dark joint through the water).

So the stone tops keep their wet shine and the joints stay dark and dull: the picture of wet cobbles with glistening tops and black cracks. It is the method D/E of section 4. It costs nothing at render time (77 s against 87 s for the same close picture, which is noise). Where it lives: the function `joint_picture(...)` in `tools/b02_lighting_and_variants.py` (about fifteen nodes); where it would live in the project: a small node group put after `WETNESS` on the road (section 8).

**How the joint picture is made** (`tools/b01_make_joint_mask.py`, `tools/b01b_make_soft_cavity.py`; both plain Python): from the road's colour picture, find the joints; close the gaps along the lines (45 dots, 4.5 cm, so that a lighter stretch of joint does not break the line into dashes); blur it about 4 mm; scale so that the middle of an ordinary joint is 1; add a faint 1 cm halo. The result is a 2048 x 2048 grey picture of 0.6 MB (it repeats every 2 m like the colour picture). **It must be made again for any other texture** (the flags, the setts of another street).

**The tries, in order** (close view, lighting A, wet, rows are in the order I did them; the full pictures are `pictures/solution_joint_picture_first_tries.jpg`, `pictures/solution_joint_picture_soft.jpg`):

[[TABLE:solutions_close_table]]

* **First tries "b" and "c"** (colour 0.45 or 0.30, the dulling at 0.25 or 0.05): contrast 0.85 and 0.96 against 0.33 for the dry road: the joints are jet black and ragged, like a black net. Too much. The picture itself was ragged because the colour picture's joint outlines are.
* **Colour alone (joint a):** contrast 0.12. The dark colour alone does almost nothing (the shine fills it in again). **The dulling is what works**: this is the proof of section 3 from the other side.
* **Softer picture, gentler numbers (soft1 to soft3):** contrast 0.47 to 0.58 in the middle band, 0.58 to 0.70 near: better, and the road finally reads as wet cobbles (`pictures/solution_joint_picture_soft.jpg`), but still about twice the dry road's 0.33.
* **Closed picture, milder numbers (mild1, mild2):** near contrast 0.60 / 0.54, "seen" 100 %. **mild1 is my recommended first setting**: colour 0.85, roughness 0.9, specular x0.65, coat x0.55, puddle clearing 0.8, the closed picture. Why mild1 and not the milder mild2: at the main camera in A wet mild1 gives near contrast 0.47 and mild2 0.41, and mild2 is not weaker than needed there; but I put only mild1 through the whole test set (section 6.4), so mild1 is the one that is proven, and mild2 is the first thing to try if the person finds mild1 too strong. **The strength is a dial in practice**: all four numbers can be moved together (1 = mild1, 0 = off) and the test set says where it stops passing.

**On the main camera** (540 x 960, lighting A, wet), with the other lighting conditions in section 6:

[[TABLE:solutions_main_table]]

**What the pictures show** (`pictures/solution_main_all_lights.jpg`): in dusk lamps (A), side light (C), overhead light (D), light from behind with the glare (E), heavy rain and dry, the road reads as setts; in the glare (E) the joints are black and the stone tops are bright; in heavy rain the big puddles (which cover the joints, correctly) still hide them and the dry parts show them.

### 5.2 Real geometry (solution 2: strong, view-dependent, but slow and near only)

**What I built** (`geometry(...)` in `tools/b02_lighting_and_variants.py`; a Geometry Nodes modifier on the road): it cuts out the part of the road between two distances (3 and 14 m along the street for the close view), cuts every face of it into 4096 small faces (`Subdivide Mesh`, level 6: about 8 mm squares; 1.4 million faces for 11 m of road), and pushes every corner DOWN by a depth times the groove picture along the surface normal. Real grooves between real stones, which catch the light, throw their own shadows (the lamps' shadow maps reach into them) and show at the edge of the picture.

* **Soft groove from the cavity picture, 2.5 cm deep:** the stones look swollen like cushions, the joints are wide shallow bowls: contrast near 0.14 (the picture's gradient is too gentle), middle 0.45.
* **Sharp groove from the "height" picture (1 for the joint, 0 on the stone, a 3 mm edge), 2 cm deep:** contrast near 0.50, middle 0.47, "seen" 93 % and 89 %. Real, hard shadows in the joints. It looks like a rough cobbled street, a little deep and ragged (the groove follows the colour picture's ragged joints).
* **Sharp geometry plus the joint picture:** 0.64 near, 0.63 middle, far 0.29.
* **What limits it:** it only exists where the road is cut (3 to 14 m here; the part beyond looked flat in the 4th panel of the picture, far contrast 0.05). It took **195 to 205 seconds against 80 for the same close picture** (and 241 against 75 for the main view with 15 m of geometry): about +120 to +165 seconds, mostly the one-time cutting and the shadow work, so for a long plate it should be a smaller share (not measured). It cannot go into the glb and the stage (the stage shows the painting on its own flat road; the painting carries the joints). It needs a high-resolution mesh near the camera, which is awkward when the camera moves along the street (a plate is one still, so for a plate it is fine).
* **The picture** is `pictures/solution_geometry_close.jpg`.

### 5.3 The hybrid, the texture filter, and the size the painter sees

[[SOL4_TEXT]]
