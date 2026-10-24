# Shot check: w2-plate-facts

8 problems found in 16 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

No finished picture was given, so marked.jpg is drawn on the flat-colour picture and the light rules (5, 6, 10, the main rule, and the dark shape in rule 8) are not checked.

## Fix first

Problem 1 (rule 3: story props together in the street). Move hand truck about 0.42 m right (across the street) and 2.90 m down the street, toward petrol drum.

## Problems

1. **rule 3: story props together in the street.** hand truck stands 3.04 m from the nearest other story prop (petrol drum) in the street: the group should stand together.
   - Fix: Move hand truck about 0.42 m right (across the street) and 2.90 m down the street, toward petrol drum.
2. **rule 3: one touching group.** Standing apart from the others: petrol drum.
   - Fix: Move petrol drum about 0.34 m to the left so it overlaps hand truck.
3. **rule 4: overlap clearly or leave a clear gap.** no-2 gateway and man 2 almost touch: 5 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.47 across, 0.58 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.18 m to the right so it clearly overlaps no-2 gateway, or move man 2 about 0.12 m to the left to leave a clear gap.
4. **rule 4: overlap clearly or leave a clear gap.** no-2 gateway's edge runs right along petrol drum's edge for 64 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.57 to 0.59 down, around 0.63 across; petrol drum is nearer the camera)
   - Fix: The move in problem 2 (bringing petrol drum into the group) fixes this too, if it ends in a clear overlap; check again after it.
5. **rule 3: story props close together.** The story props (leaving out no-2 board) fill a box 0.42 of the frame wide and 0.27 tall (limit 0.40 x 0.50). Its edges: man 8's left side (0.28 across), petrol drum's right side (0.70), no-2 gateway's top (0.44 down) and man 8's bottom (0.71).
   - Fix: Move man 8 about 0.12 m to the right.
6. **rule 8: nothing big where the eye enters.** man 8 fills 1.3% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 8 out of the bottom-left quarter.
7. **rule 4: overlap clearly or leave a clear gap.** man 6's edge runs right along man 7's edge for 29 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.53 to 0.54 down, around 0.37 across; man 7 is nearer the camera)
   - Fix: Move man 6 about 0.10 m to the right so man 6 clearly passes behind man 7, or move man 6 about 0.12 m to the left to leave a clear gap.
8. **rule 12: titles in dim sky.** Only 59% of the title area is sky (need 85%). (59% of the title area is sky)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: petrol drum, diesel drum, hand truck, man 1, man 2, man 3, man 4, man 5, man 6, man 7, man 8 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-2 gateway is 0.017 of the frame width away (limit 0.03).
- rule 3: nothing hides the words: 0% of no-2 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of petrol drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of diesel drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (petrol drum 0.70, diesel drum 0.60, hand truck 0.61, man 1 0.50, man 2 0.47, man 3 0.46, man 4 0.44, man 5 0.44, man 6 0.41, man 7 0.40, man 8 0.38, no-2 board 0.56).

## Notes

- rule 4: overlap clearly or leave a clear gap: man 1 overlaps no-2 gateway by 18 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: no-2 gateway and man 3 are 21 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
