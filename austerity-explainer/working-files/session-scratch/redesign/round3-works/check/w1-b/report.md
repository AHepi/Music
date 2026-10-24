# Shot check: w1-b

15 problems found in 23 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move man 2 off brazier and place it again from just above the pavement.

## Problems

1. **props rest where they should.** man 2 rests on brazier, not on the ground (at Blender x -4.48, y 21.24).
   - Fix: Move man 2 off brazier and place it again from just above the pavement.
2. **rule 3: story props in the frame.** man 1 is in the frame but hidden behind man 7.
   - Fix: Move man 1 out from behind man 7, or in front of it.
3. **rule 3: story props in the frame.** man 3 is in the frame but hidden behind man 7.
   - Fix: Move man 3 out from behind man 7, or in front of it.
4. **rule 4: overlap clearly or leave a clear gap.** diesel drum only just overlaps man 2: it reaches 1 pixel into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.42 across, 0.60 down; diesel drum is nearer the camera)
   - Fix: Move diesel drum about 0.09 m to the right and about 0.39 m further from the camera (but petrol drum stands there) so it clearly overlaps man 2, or move diesel drum about 0.11 m to the left and about 0.47 m nearer to the camera to leave a clear gap.
5. **rule 4: overlap clearly or leave a clear gap.** petrol drum only just overlaps man 2: it reaches 2 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.42 across, 0.60 down; petrol drum is nearer the camera)
   - Fix: Move petrol drum about 0.09 m to the right so it clearly overlaps man 2, or move petrol drum about 0.13 m to the left to leave a clear gap.
6. **rule 4: overlap clearly or leave a clear gap.** lantern and man 2 almost touch: 6 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.39 across, 0.55 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.12 m to the right and about 0.07 m higher so it clearly overlaps man 2, or move lantern about 0.07 m to the left and about 0.04 m lower to leave a clear gap.
7. **rule 4: overlap clearly or leave a clear gap.** no-1 gate and lantern almost touch: 6 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.39 across, 0.55 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.14 m to the right so it clearly overlaps no-1 gate, or move lantern about 0.08 m to the left to leave a clear gap.
8. **rule 3: story props together in the street.** man 1 stands 0.69 m from the nearest other story prop (man 2) in the street: the group should stand together.
   - Fix: Move man 1 about 0.54 m left (across the street) and 0.25 m down the street, toward man 2.
9. **rule 4: overlap clearly or leave a clear gap.** lantern only just overlaps diesel drum: it reaches 8 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.38 across, 0.57 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.06 m lower so it clearly overlaps diesel drum, or move lantern about 0.16 m higher to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** man 2 only just overlaps brazier: it reaches 9 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.43 across, 0.60 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.03 m to the left and about 0.42 m nearer to the camera (but petrol drum stands there) so it clearly overlaps brazier, or move man 2 about 0.09 m to the right and about 1.84 m further from the camera to leave a clear gap.
11. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.43 of the frame wide and 0.30 tall (limit 0.40 x 0.50). Its edges: diesel drum's left side (0.33 across), no-1 gate's right side (0.76), no-1 gate's top (0.42 down) and man 7's bottom (0.73).
   - Fix: Move diesel drum about 0.21 m to the right.
12. **rule 4: overlap clearly or leave a clear gap.** man 7 only just overlaps no-1 gate: it reaches 10 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.60 across, 0.56 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.02 m to the left and about 0.39 m further from the camera so it clearly overlaps no-1 gate, or move man 7 about 0.07 m to the right and about 1.13 m nearer to the camera to leave a clear gap.
13. **rule 3: story props together in the street.** man 7 stands 0.36 m from the nearest other story prop (man 6) in the street: the group should stand together.
   - Fix: Move man 7 about 0.02 m right (across the street) and 0.26 m up the street, toward man 6.
14. **rule 3: story props together in the street.** man 6 stands 0.34 m from the nearest other story prop (man 5) in the street: the group should stand together.
   - Fix: Move man 6 about 0.03 m right (across the street) and 0.24 m up the street, toward man 5.
15. **rule 12: titles in dim sky.** Only 39% of the title area is sky (need 85%). (39% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: brazier, petrol drum, diesel drum, man 1, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.002 of the frame width away (limit 0.03).
- rule 3: one touching group: Every story prop that shows touches or overlaps another. Not showing at all: man 1 (problem 2), man 3 (problem 3).
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.43, lantern 0.39, diesel drum 0.42, man 2 0.50, man 4 0.71, man 5 0.71, man 6 0.72, man 7 0.73, no-1 board 0.67).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- rule 4: overlap clearly or leave a clear gap: lantern overlaps petrol drum by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
