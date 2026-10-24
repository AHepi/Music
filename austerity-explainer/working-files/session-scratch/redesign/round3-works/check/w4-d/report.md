# Shot check: w4-d

9 problems found in 16 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move upturned crate off mug and wages and place it again from just above the pavement.

## Problems

1. **props rest where they should.** upturned crate rests on mug and wages, not on the ground (at Blender x 5.40, y 23.17).
   - Fix: Move upturned crate off mug and wages and place it again from just above the pavement.
2. **rule 3: story props in the frame.** mug and wages is in the frame but hidden behind upturned crate.
   - Fix: Move mug and wages out from behind upturned crate, or in front of it.
3. **rule 3: one touching group.** Standing apart from the others: jacket and cap, upturned crate. Not showing at all: mug and wages (problem 2).
   - Fix: Move jacket and cap about 0.56 m lower so it overlaps upturned crate; move upturned crate about 4.34 m further from the camera so it overlaps jacket and cap.
4. **rule 3: story props close together.** The story props fill a box 0.59 of the frame wide and 0.51 tall (limit 0.40 x 0.50). Its edges: jacket and cap's left side (0.26 across), no-2 gate's right side (0.84), no-2 gate's top (0.29 down) and upturned crate's bottom (0.81).
   - Fix: Move jacket and cap about 0.69 m to the right; move upturned crate about 0.28 m further from the camera.
5. **rule 8: nothing big where the eye enters.** upturned crate fills 2.1% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move upturned crate out of the bottom-left quarter.
6. **rule 4: overlap clearly or leave a clear gap.** no-2 gate's edge runs right along crates's edge for 59 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.68 to 0.70 down, around 0.83 across; crates is nearer the camera)
   - Fix: Move crates about 0.05 m to the right so no-2 gate clearly passes behind crates, or move crates about 0.06 m to the left to leave a clear gap.
7. **rule 8: nothing big where the eye enters.** jacket and cap fills 1.6% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move jacket and cap out of the bottom-left quarter.
8. **rule 12: titles in dim sky.** Only 27% of the title area is sky (need 85%). (27% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.
9. **rule 4: overlap clearly or leave a clear gap.** crates only just overlaps handcart: it reaches 7 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.67 across, 0.55 down; crates is nearer the camera)
   - Fix: Move crates about 0.01 m to the left and about 0.49 m further from the camera so it clearly overlaps handcart, or move crates about 0.04 m to the right and about 0.92 m nearer to the camera to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: crates, handcart, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- props rest where they should: mug and wages rests on upturned crate.
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gate is 0.005 of the frame width away (limit 0.03).
- rule 3: story props together in the street: upturned crate, man 1, man 2, man 3 stand in front of None and within 0.3 m of each other.
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (jacket and cap 0.48, upturned crate 0.46, man 1 0.78, man 2 0.76, man 3 0.77).

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
