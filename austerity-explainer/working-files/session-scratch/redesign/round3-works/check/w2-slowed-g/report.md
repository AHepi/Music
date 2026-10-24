# Shot check: w2-slowed-g

12 problems found in 19 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move crates off no-2 gate and place it again from just above the pavement.

## Problems

1. **props rest where they should.** crates rests on no-2 gate, not on the ground (at Blender x 3.40, y 23.33).
   - Fix: Move crates off no-2 gate and place it again from just above the pavement.
2. **rule 3: story props in the frame.** crates is in the frame but hidden behind man 5. (it is also not resting where it should: problem 1)
   - Fix: Move crates out from behind man 5, or in front of it.
3. **rule 3: one touching group.** Standing apart from the others: no-2 board. Not showing at all: crates (problem 2).
   - Fix: Move no-2 board about 3.22 m lower so it overlaps petrol drum.
4. **rule 3: story props together in the street.** crates stands 0.92 m from the nearest other story prop (no-2 board) in the street: the group should stand together.
   - Fix: Move crates about 0.06 m right (across the street) and 0.82 m down the street, toward no-2 board.
5. **rule 8: nothing big where the eye enters.** man 8 fills 2.2% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 8 out of the bottom-left quarter.
6. **rule 12: titles in dim sky.** Only 46% of the title area is sky (need 85%). (46% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.
7. **rule 4: overlap clearly or leave a clear gap.** hand truck and man 1 almost touch: 3 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.52 across, 0.61 down; man 1 is nearer the camera)
   - Fix: Move man 1 about 0.14 m to the right so it clearly overlaps hand truck, or move man 1 about 0.12 m to the left to leave a clear gap.
8. **rule 4: overlap clearly or leave a clear gap.** man 7's edge runs right along man 8's edge for 63 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.50 to 0.52 down, around 0.29 across; man 8 is nearer the camera)
   - Fix: Move man 7 about 0.07 m to the left so man 7 clearly passes behind man 8, or move man 7 about 0.09 m to the right to leave a clear gap.
9. **rule 4: overlap clearly or leave a clear gap.** hand truck and man 2 almost touch: 12 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.51 across, 0.61 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.17 m to the right and about 0.70 m nearer to the camera (but man 3 stands there) so it clearly overlaps hand truck, or move man 2 about 0.05 m to the left and about 0.21 m further from the camera to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 4's edge for 40 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.50 to 0.52 down, around 0.44 across; man 4 is nearer the camera)
   - Fix: Move man 3 about 0.11 m to the right so man 3 clearly passes behind man 4, or move man 3 about 0.12 m to the left to leave a clear gap.
11. **rule 4: overlap clearly or leave a clear gap.** man 5's edge runs right along man 6's edge for 37 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.64 to 0.65 down, around 0.41 across; man 6 is nearer the camera)
   - Fix: Move man 5 about 0.09 m to the left so man 5 clearly passes behind man 6, or move man 5 about 0.10 m to the right to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** man 4's edge runs right along man 5's edge for 30 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.63 to 0.63 down, around 0.44 across; man 5 is nearer the camera)
   - Fix: Move man 4 about 0.10 m to the left so man 4 clearly passes behind man 5, or move man 4 about 0.11 m to the right to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, hand truck, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gate is 0.003 of the frame width away (limit 0.03).
- rule 3: story props close together: The story props (leaving out no-2 board) fill a box 0.40 of the frame wide and 0.21 tall (limit 0.40 x 0.50). Its edges: no-2 gate's left side (0.24 across), diesel drum's right side (0.64), no-2 gate's top (0.43 down) and diesel drum's bottom (0.64).
- rule 3: nothing hides the words: 0% of no-2 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (no-2 board 0.52, petrol drum 0.63, diesel drum 0.64).

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
