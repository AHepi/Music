# Shot check: w1-working-k

10 problems found in 18 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (set-up: the finished picture matches the scene). Render a new finished picture of the scene as it is now, and check again.

## Problems

1. **set-up: the finished picture matches the scene.** The finished picture does not match the scene as measured: no-1 gate (62% of its outline lines up; 74% when slid 24 pixels left and 12 pixels up) stands somewhere else in it. It was probably made before the scene changed, so the light rules were not judged.
   - Fix: Render a new finished picture of the scene as it is now, and check again.
2. **rule 3: one touching group.** Standing apart from the others: brazier.
   - Fix: Move brazier about 0.36 m to the left so it overlaps diesel drum.
3. **rule 4: overlap clearly or leave a clear gap.** diesel drum and lunch tin almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.28 across, 0.56 down; diesel drum is nearer the camera)
   - Fix: Move diesel drum about 1.97 m further from the camera so it clearly overlaps lunch tin, or move diesel drum about 1.50 m nearer to the camera to leave a clear gap.
4. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.47 of the frame wide and 0.21 tall (limit 0.40 x 0.50). Its edges: lantern's left side (0.28 across), no-1 gate's right side (0.76), no-1 gate's top (0.43 down) and diesel drum's bottom (0.64).
   - Fix: Move lantern about 0.54 m to the right.
5. **rule 1: aim the street at the story.** The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.078 of the frame width away (limit 0.03): 84 pixels to the left and 0 pixels above. (no-1 gate spans 0.39 to 0.76 across, 0.43 to 0.63 down)
   - Fix: Turning the camera won't help: it moves where the lines meet and the props together. Move the camera about 0.66 m to the left, or move no-1 gate about 0.66 m to the right.
6. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps lunch tin: it reaches 7 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.07 m higher so it clearly overlaps lunch tin, or move lantern about 0.18 m lower to leave a clear gap.
7. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps diesel drum: it reaches 8 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.06 m lower so it clearly overlaps diesel drum, or move lantern about 0.18 m higher to leave a clear gap.
8. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps petrol drum: it reaches 13 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.29 across, 0.56 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.03 m lower so it clearly overlaps petrol drum, or move lantern about 0.22 m higher to leave a clear gap.
9. **rule 4: overlap clearly or leave a clear gap.** brazier and petrol drum almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.56 down; petrol drum is nearer the camera)
   - Fix: The move in problem 2 (bringing brazier into the group) fixes this too, if it ends in a clear overlap; check again after it.
10. **rule 12: titles in dim sky.** Only 39% of the title area is sky (need 85%). (39% of the title area is sky; its brightness 0.22)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: brazier, petrol drum, diesel drum stand on the pavement or road (within 3 cm).
- rule 3: story props together in the street: brazier, diesel drum stand in front of None and within 0.3 m of each other.
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.43, lantern 0.30, diesel drum 0.33, no-1 board 0.67).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- set-up: No object in the scene matches the group "man 1", so it was not measured (if the scene should have it, check the name patterns of "man 1" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 2", so it was not measured (if the scene should have it, check the name patterns of "man 2" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 3", so it was not measured (if the scene should have it, check the name patterns of "man 3" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 4", so it was not measured (if the scene should have it, check the name patterns of "man 4" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 5", so it was not measured (if the scene should have it, check the name patterns of "man 5" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 6", so it was not measured (if the scene should have it, check the name patterns of "man 6" in the check file against the objects' names in Blender).
- set-up: No object in the scene matches the group "man 7", so it was not measured (if the scene should have it, check the name patterns of "man 7" in the check file against the objects' names in Blender).

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
