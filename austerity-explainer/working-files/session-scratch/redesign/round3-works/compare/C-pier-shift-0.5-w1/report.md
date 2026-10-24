# Shot check: C-pier-shift-0.5-w1

15 problems found in 21 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (props rest where they should). Move brazier off man 2 and place it again from just above the pavement.

## Problems

1. **props rest where they should.** brazier rests on man 2, not on the ground (at Blender x -4.88, y 21.52).
   - Fix: Move brazier off man 2 and place it again from just above the pavement.
2. **props rest where they should.** man 2 rests on brazier, not on the ground (at Blender x -4.64, y 21.27).
   - Fix: Move man 2 off brazier and place it again from just above the pavement.
3. **rule 3: story props in the frame.** lantern is in the frame but hidden behind the set (a wall or a house).
   - Fix: Move lantern out from behind the set (a wall or a house), or in front of it.
4. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.60 of the frame wide and 0.31 tall (limit 0.40 x 0.50). Its edges: diesel drum's left side (0.36 across), man 7's right side (0.96), no-1 gate's top (0.42 down) and man 7's bottom (0.74).
   - Fix: This follows from problem 8: once man 7 is moved in from the right edge, the box narrows.
5. **rule 3: one touching group.** Standing apart from the others: diesel drum. Not showing at all: lantern (problem 3).
   - Fix: Move diesel drum about 0.32 m to the right so it overlaps brazier.
6. **rule 4: overlap clearly or leave a clear gap.** man 4's edge runs right along man 6's edge for 58 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.58 to 0.60 down, around 0.73 across; man 6 is nearer the camera)
   - Fix: Move man 4 about 0.10 m to the right so man 4 clearly passes behind man 6, or move man 4 about 0.12 m to the left to leave a clear gap.
7. **rule 3: story props together in the street.** man 1 stands 0.55 m from the nearest other story prop (man 2) in the street: the group should stand together.
   - Fix: Move man 1 about 0.40 m left (across the street) and 0.19 m down the street, toward man 2.
8. **rule 12: room for phone buttons.** man 7 reaches 0.96 across (limit 0.95). Video apps put their buttons down the right edge, from a little above the middle to near the bottom.
   - Fix: Move man 7 about 0.07 m to the left.
9. **rule 4: overlap clearly or leave a clear gap.** man 4's edge runs right along man 5's edge for 38 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.63 to 0.64 down, around 0.73 across; man 5 is nearer the camera)
   - Fix: Move man 4 about 0.10 m to the right so man 4 clearly passes behind man 5, or move man 4 about 0.12 m to the left to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** man 6's edge runs right along man 7's edge for 38 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.63 to 0.65 down, around 0.84 across; man 7 is nearer the camera)
   - Fix: Move man 6 about 0.08 m to the right so man 6 clearly passes behind man 7, or move man 6 about 0.10 m to the left to leave a clear gap.
11. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 4's edge for 35 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.61 to 0.62 down, around 0.66 across; man 4 is nearer the camera)
   - Fix: Move man 3 about 0.11 m to the right so man 3 clearly passes behind man 4, or move man 3 about 0.13 m to the left to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** man 5 and man 7 almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.84 across, 0.68 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.06 m to the left and about 0.58 m nearer to the camera so it clearly overlaps man 5, or move man 7 about 0.01 m to the right and about 0.08 m further from the camera to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** brazier and petrol drum almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.39 across, 0.58 down; petrol drum is nearer the camera)
   - Fix: Move petrol drum about 0.24 m to the right so it clearly overlaps brazier, or move petrol drum about 0.03 m to the left to leave a clear gap.
14. **rule 4: overlap clearly or leave a clear gap.** man 5's edge runs right along man 6's edge for 30 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.67 to 0.68 down, around 0.80 across; man 6 is nearer the camera)
   - Fix: Move man 5 about 0.09 m to the left so man 5 clearly passes behind man 6, or move man 5 about 0.11 m to the right to leave a clear gap.
15. **rule 12: titles in dim sky.** Only 34% of the title area is sky (need 85%). (34% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, man 1, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.006 of the frame width away (limit 0.03).
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.

## Notes

- rule 4: overlap clearly or leave a clear gap: no-1 gate and brazier are 23 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
