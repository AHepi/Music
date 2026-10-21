## 9. What I tested, what I did not, what I am unsure of, and what went wrong

**Tested (run, and looked at):** the measure and its masks; the diagnosis (14 pictures in the close view, 9 in the main view, each with one thing changed); the joint picture (8 settings), the real geometry (3 kinds), the hybrid, the texture filter; the whole lighting test set on the road as it is and on the road with the joint picture mild1, in the street file and in the film's lockout shot file; the rubbish mask and a prototype of the muck layer and of the scattered pieces (two tries), with and without the joint picture; the test set's own one-command script (section 6.2) on the quick set ([[QUICK_SCRIPT_SENTENCE]]).

**Not tested:**
* **The painter** on any of these pictures (paid; asked nobody). Whether it keeps the joints and the rubbish is unknown; the painter test (`painter_test/`) says it kept thin dark joint lines and the wet shine in its one try.
* **The film's stage and the glb** with the joint picture or the rubbish. The stage shows the painting on its own road; the glb's maps would need the joint layer in the bake (A5).
* **Pavement flags, gutter and kerb stones, the walls' mortar lines.** The same method should work; each needs its own picture.
* **The full-size plate** (1536 x 2730): I drew 1080 x 1920 once (section 5.3) and 1280 x 960 of the close view.
* **Cycles.** All pictures are EEVEE.
* **Other puddle layouts** (the seed) and **other roads**.
* **Parallax nodes and add-ons**, **Cycles adaptive subdivision**, **modelled stones**, **Line Art or Freestyle outlines**.
* **Rubbish on the walls, in the lockout shot's props' contact shadows, in motion.**
* **The geometry route with the camera moving.**

**Unsure:**
* **My joint mask comes from the colour picture, and the joint picture is made from the same mask.** So the measure is friendly to the joint picture: it knows exactly where the joints are. This is not cheating (the joints are real, and the picture is what the road would have), but a different road picture with different joints would need its own mask and its own check by eye.
* **The pass line is mine**, chosen by looking at about 60 pictures (section 6.3). It is a first line.
* **Light C is artificial** (house shadows off); **light E is invented** (a strong low light at the street's far end); I chose their strengths so that the dry road is about as bright as in A. The film may never light the street like C or E; they are there to find where the joints break.
* **16 samples** leave grain on the wet road (section 2 of the recipe: 0.008 at 48 samples); the measure averages over thousands of dots so the grain hardly moves it, but I did not measure that.
* **The puddle share** is calibrated for the main camera; the lockout camera sees much more puddle (42 % of the road at the heavy dial in the recipe's table), which is why section 6 leaves puddle dots out.
* **The sources for 1926 rubbish are thin** (section 7).

**What went wrong (all of it, in order):**
1. **My first joint mask came from the height picture and was broken** (patchy joints: the picture shows the joint only 0.05 lower than the stone). I found it by looking at the check sheet; the second mask comes from the colour picture.
2. **Light E first stood under the road** (z 1.8 while the street rises 4 degrees: the road is at 4.7 m there), so it lit nothing; moved to z 5.9. **Light C first was six times too bright** (strength 6, then 1.0).
3. **The lockout baseline was measured against the street's mask by mistake** (both cameras were called "main", so the mask file was reused); the numbers came out as nonsense (contrast 0.00), I noticed because the number of joint dots was identical to the street's. I made the lockout camera's own mask and measured those pictures again from their JPEGs.
4. **The real-geometry modifier crashed the first run** (I used a shader node type that does not exist in a geometry node tree). I lost one run's worth of time and fixed it.
5. **The first joint pictures were far too strong** (black ragged net, contrast 0.85 to 0.96) and the second try (soft1 to soft3) was still twice the dry road's. It took four rounds to reach mild1.
6. **My first texture filter test did nothing** (I gave the setting the wrong name; the log said so) and had to be run again.
7. **The first run of the rubbish prototype stopped at once** (a missing folder in Python's path); fixed.
8. **The first measure of the road lumped puddle and non-puddle dots together**, and the lockout in heavy rain "failed" because 42 % of its road is a puddle; I added the puddle mask and left those dots out (section 6), and I report both ways.
9. **The disk was tight** (1.4 GB free against a 1.2 GB floor) all through; I kept pictures as JPEG, deleted my PNGs after measuring, and stopped runs from starting below 1.25 GB.
