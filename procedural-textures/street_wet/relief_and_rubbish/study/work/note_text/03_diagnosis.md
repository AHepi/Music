## 3. What flattens the joints (the diagnosis, one change at a time)

**Result in one line:** *the only thing that ever made the joints show, wet or dry, is the dark colour of the joints in the colour picture; the shine that water adds fills them in; the "relief" (normal map) never made them show at all.*

All the pictures below are the close view in lighting A (the film's dusk lamps), drawn from the same camera; each row changes ONE thing from "wet, round 2" (the problem). The picture is `pictures/diagnosis_close_A.jpg`.

[[TABLE:diagnosis_table]]

How to read it: the dry road has contrast 0.33 and 94 % of its joint dots are "seen". The wet road has 0.08 and 32 %. The pass line of section 6 asks for 0.25 and 70 % at the close camera.

**What the rows say, in plain words**

1. **Colour picture made flat (rows "colour picture made flat"): contrast 0.01 dry and -0.01 wet.** Without the dark joint colour, the joints are NOT there, in any condition. All the visible joint in today's road is paint: dark olive lines in the colour picture. *Example:* a flat grey road with a relief picture on it is, to the lamp, one grey road.
2. **Relief picture removed (rows "relief picture removed"): DRY contrast 0.35, the same as with it (0.33).** The relief picture adds nothing the eye can measure to the joints. The reason (my reading, and a number): a normal map only says which way each dot leans; the floor of a groove leans almost the same way as the top of a stone. In Poly Haven's picture the joint floors lean 9 degrees on average (stone faces 4, stone edges 8, measured in `work/joint_cores.png` against the normal picture); under a lamp that is a few per cent of brightness, in random directions, which averages out. The strong lean is only at the stone edge, about 2 to 4 mm wide, and at 540 x 960 one dot is 6 mm wide at 8 m (more, along the road).
3. **All shine taken off (colour darkening only): contrast 0.34, "seen" 98 %. The joints come back completely.** So the wet look washes the joints out through SHINE. Water makes a surface smooth; a smooth surface reflects the bright sky and lamps over the stone and over the joint alike, and the joint's dark colour is lost under a bright veil. *Example:* a black plate looks black until you tilt it to the window.
4. **Each part of the shine alone is not enough, all three together do it.** Roughness 0.9 (film and boost kept): 0.18. No water film and no extra shine (roughness 0.3 kept): 0.10. The round 2 layer has all three at once (wet roughness 0.3, film coat 0.3, specular boost 0.25).
5. **Stronger relief helps a little but does not cure it.** Relief strength 3: contrast 0.11, "seen" 42 %. Strength 6: contrast 0.13, 53 %. Relief not flattened (Relief Flatten 0, Grain Fill 0): 0.10 and 49 %. Their DELTA (the brightness difference) rises two to three times (0.016 to 0.034 / 0.052 / 0.045), but this is the white ticks on the stone corners, not the joints.
6. **Puddles are not the cause.** "No puddles" (dial 0): the same numbers as the wet road. The puddle layer flattens the relief inside puddles (round 2 did that on purpose), but outside puddles the shine does the damage, and the joints are hidden as much with no puddles as with them. (Section 3b has the share of joints under puddles.)
7. **"Stone tops stay drier" (Dry Tops 1.0): no change** (0.08, the same). The height picture is too flat to say where the tops are (stone 0.56, joint 0.51 on a 0 to 1 scale, measured against my joint mask).
8. **Poly Haven's own ambient occlusion picture** (the picture of how much light each dot would miss because of its neighbours; it is on Poly Haven for this road: `https://polyhaven.com/a/square_cobblestone`) **is no cure either:** joint 0.77, stone 0.85, so the joint is only 10 % darker than the stone. I downloaded it (CC0) only to measure it (work/polyhaven_download).

The main camera says the same (540 x 960, lighting A):

[[TABLE:diagnosis_main_table]]

**Why "missing shadow" is also true.** A real groove is dark because the stones on both sides block the light (a little "shadow" in the joint whatever the light). EEVEE draws no shadow from a picture, and a normal map only changes the lean of the surface, not its depth, so nothing in the road material makes the joint dark except its own colour. Real geometry does (section 5).

### 3b. Where each light puts the problem (baseline, round 2)

The same measure in all the pictures of the lighting test set (section 6 defines them). Dry rows are today's road; the wet and heavy rows are round 2.

[[TABLE:baseline_table]]

* **Every wet and heavy picture fails**, in every lighting and every camera: near contrast 0.01 to 0.12 against 0.18 to 0.33 dry.
* **The worst is light from behind into the glare (E):** near contrast 0.03 (main) and 0.01 (close), because the glare is a bright veil over the road. The brazier's glare in the lockout shot (B) is the same: 0.07.
* **Even the DRY road is weaker under the low side light (C): 0.18, and its middle band only 34 % seen.**
* [[PUDDLE_SENTENCE]]
