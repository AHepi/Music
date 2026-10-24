# Shot check: w3-quiet-light

36 problems found in 52 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (props rest where they should). Move man 2 off brazier and place it again from just above the pavement.

## Problems

1. **props rest where they should.** man 2 rests on brazier, not on the ground (at Blender x -5.42, y 21.14).
   - Fix: Move man 2 off brazier and place it again from just above the pavement.
2. **rule 5: nothing in the story group as bright as two gates and the wall between.** the brightest parts of gate boards reach 0.40, as bright as two gates and the wall between (0.05); the brightest parts of brazier reach 0.81, as bright as two gates and the wall between (0.05); the brightest parts of no-2 crates reach 0.70, as bright as two gates and the wall between (0.05); the brightest parts of man 1 reach 0.13, as bright as two gates and the wall between (0.05); the brightest parts of man 2 reach 0.33, as bright as two gates and the wall between (0.05); the brightest parts of man 3 reach 0.08, as bright as two gates and the wall between (0.05); the brightest parts of man 4 reach 0.06, as bright as two gates and the wall between (0.05); the brightest parts of man 5 reach 0.05, as bright as two gates and the wall between (0.05); the brightest parts of man 6 reach 0.06, as bright as two gates and the wall between (0.05); the brightest parts of man 7 reach 0.05, as bright as two gates and the wall between (0.05).
   - Fix: Make gate boards darker (its own colour) or move it further from the light on it (no-2-gateway-spill). Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Make no-2 crates darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 1 darker (its own colour) or move it further from the light on it (brazier_light). Make man 2 darker (its own colour) or move it further from the light on it (brazier_light). Make man 3 darker (its own colour) or move it further from the light on it (lantern_light). Make man 4 darker (its own colour) or move it further from the light on it (brazier_light). Make man 5 darker (its own colour) or move it further from the light on it (brazier_light). Make man 6 darker (its own colour) or move it further from the light on it (no-2-gateway-beam). Make man 7 darker (its own colour) or move it further from the light on it (no-2-gateway-beam).
3. **rule 3: one touching group.** Standing apart from the others: gate boards, no-2 crates.
   - Fix: Move gate boards about 2.52 m lower so it overlaps no-2 crates; move no-2 crates about 63.81 m further from the camera so it overlaps gate boards.
4. **rule 3: story props together in the street.** no-2 crates stands 1.92 m from the nearest other story prop (gate boards) in the street: the group should stand together.
   - Fix: Move no-2 crates about 1.52 m left (across the street) and 1.01 m down the street, toward gate boards.
5. **rule 5: two gates and the wall between is bright.** two gates and the wall between is 0.28 times as bright as the frame's average (need 1.8).
   - Fix: Light two gates and the wall between more, or darken what is around it.
6. **rule 3: story props close together.** The story props fill a box 0.56 of the frame wide and 0.21 tall (limit 0.40 x 0.50). Its edges: man 2's left side (0.19 across), two gates and the wall between's right side (0.75), two gates and the wall between's top (0.50 down) and man 7's bottom (0.71).
   - Fix: Move man 2 about 3.05 m to the right.
7. **rule 5: two gates and the wall between is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 1% lie on two gates and the wall between (need 40%) and 49% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light two gates and the wall between more.
8. **rule 4: overlap clearly or leave a clear gap.** two gates and the wall between and no-2 drums almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.75 across, 0.65 down; no-2 drums is nearer the camera)
   - Fix: Move no-2 drums about 0.33 m to the left so it clearly overlaps two gates and the wall between, or move no-2 drums about 0.35 m to the right to leave a clear gap.
9. **rule 4: overlap clearly or leave a clear gap.** no-2 crates only just overlaps two gates and the wall between: it reaches 1 pixel into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.74 across, 0.64 down; no-2 crates is nearer the camera)
   - Fix: The move in problem 3 (bringing no-2 crates into the group) fixes this too, if it ends in a clear overlap; check again after it.
10. **rule 4: overlap clearly or leave a clear gap.** man 7 only just overlaps man 1: it reaches 2 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.66 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.16 m to the right and about 0.90 m further from the camera (but man 6 stands there) so it clearly overlaps man 1, or move man 7 about 0.23 m to the left and about 1.21 m nearer to the camera to leave a clear gap.
11. **rule 10: the quiet side keeps the frame from tipping.** The right half (away from two gates and the wall between) holds 57% of the weight (aim for 40 to 48%).
   - Fix: The right half is too busy: dim or remove some of its detail.
12. **rule 4: overlap clearly or leave a clear gap.** man 2 only just overlaps brazier: it reaches 3 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.23 across, 0.64 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.23 m to the right and about 0.88 m further from the camera so it clearly overlaps brazier, or move man 2 about 0.36 m to the left and about 1.29 m nearer to the camera to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps two gates and the wall between: it reaches 3 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.33 across, 0.64 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 1.51 m further from the camera (but man 5 stands there) so it clearly overlaps two gates and the wall between, or move man 6 about 2.10 m nearer to the camera to leave a clear gap.
14. **rule 4: overlap clearly or leave a clear gap.** man 5 only just overlaps man 1: it reaches 4 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.65 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 0.12 m to the right and about 1.04 m further from the camera (but man 4 stands there) so it clearly overlaps man 1, or move man 5 about 0.23 m to the left and about 1.76 m nearer to the camera (but man 7 stands there) to leave a clear gap.
15. **rule 4: overlap clearly or leave a clear gap.** two gates and the wall between and no-1 drums almost touch: 6 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.64 down; no-1 drums is nearer the camera)
   - Fix: Move no-1 drums about 0.29 m to the right and about 1.94 m further from the camera so it clearly overlaps two gates and the wall between, or move no-1 drums about 0.19 m to the left and about 1.14 m nearer to the camera to leave a clear gap.
16. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 1: it reaches 5 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.66 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.12 m to the right and about 0.90 m further from the camera (but man 5 stands there) so it clearly overlaps man 1, or move man 6 about 0.24 m to the left and about 1.64 m nearer to the camera to leave a clear gap.
17. **rule 4: overlap clearly or leave a clear gap.** man 5 only just overlaps two gates and the wall between: it reaches 5 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.33 across, 0.63 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 1.33 m further from the camera (but man 4 stands there) so it clearly overlaps two gates and the wall between, or move man 5 about 2.43 m nearer to the camera (but man 7 stands there) to leave a clear gap.
18. **rule 4: overlap clearly or leave a clear gap.** man 3 and no-1 drums almost touch: 8 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.65 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.45 m to the left so it clearly overlaps no-1 drums, or move man 3 about 0.22 m to the right to leave a clear gap.
19. **rule 4: overlap clearly or leave a clear gap.** two gates and the wall between and man 7 almost touch: 9 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.64 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 2.64 m further from the camera so it clearly overlaps two gates and the wall between, or move man 7 about 1.01 m nearer to the camera to leave a clear gap.
20. **rule 10: nothing on the quiet side outshines the subject.** A light in the right half (at 0.62 across, 0.48 down) is 0.78 bright, as bright as two gates and the wall between (0.07).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
21. **rule 4: overlap clearly or leave a clear gap.** no-1 drums only just overlaps brazier: it reaches 10 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.25 across, 0.65 down; no-1 drums is nearer the camera)
   - Fix: Move no-1 drums about 0.14 m to the left so it clearly overlaps brazier, or move no-1 drums about 0.54 m to the right to leave a clear gap.
22. **rule 4: overlap clearly or leave a clear gap.** man 3 only just overlaps man 1: it reaches 10 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.64 down; man 3 is nearer the camera)
   - Fix: Move man 3 about 0.08 m to the right and about 0.70 m further from the camera so it clearly overlaps man 1, or move man 3 about 0.31 m to the left and about 2.47 m nearer to the camera (but man 5 stands there) to leave a clear gap.
23. **rule 3: story props together in the street.** man 3 stands 0.48 m from the nearest other story prop (man 4) in the street: the group should stand together.
   - Fix: Move man 3 about 0.02 m right (across the street) and 0.38 m down the street, toward man 4.
24. **rule 3: story props together in the street.** man 4 stands 0.48 m from the nearest other story prop (man 5) in the street: the group should stand together.
   - Fix: Move man 4 about 0.02 m right (across the street) and 0.38 m down the street, toward man 5.
25. **rule 3: story props together in the street.** man 5 stands 0.48 m from the nearest other story prop (man 4) in the street: the group should stand together.
   - Fix: Move man 5 about 0.02 m left (across the street) and 0.38 m up the street, toward man 4.
26. **rule 3: story props together in the street.** man 6 stands 0.45 m from the nearest other story prop (man 7) in the street: the group should stand together.
   - Fix: Move man 6 about 0.02 m right (across the street) and 0.35 m down the street, toward man 7.
27. **rule 3: story props together in the street.** man 7 stands 0.45 m from the nearest other story prop (man 6) in the street: the group should stand together.
   - Fix: Move man 7 about 0.02 m left (across the street) and 0.35 m up the street, toward man 6.
28. **rule 4: overlap clearly or leave a clear gap.** man 4 only just overlaps man 1: it reaches 12 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.64 down; man 4 is nearer the camera)
   - Fix: Move man 4 about 0.05 m to the right and about 0.55 m further from the camera so it clearly overlaps man 1, or move man 4 about 0.28 m to the left and about 2.54 m nearer to the camera (but man 6 stands there) to leave a clear gap.
29. **rule 4: overlap clearly or leave a clear gap.** man 7 only just overlaps man 3: it reaches 12 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.33 across, 0.66 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.49 m further from the camera so it clearly overlaps man 3, or move man 7 about 2.25 m nearer to the camera to leave a clear gap.
30. **rule 4: overlap clearly or leave a clear gap.** man 1 and no-1 drums almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.32 across, 0.66 down; no-1 drums is nearer the camera)
   - Fix: Move no-1 drums about 0.58 m to the right so it clearly overlaps man 1, or move no-1 drums about 0.09 m to the left to leave a clear gap.
31. **rule 4: overlap clearly or leave a clear gap.** man 5 only just overlaps man 3: it reaches 13 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.64 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 0.46 m further from the camera so it clearly overlaps man 3, or move man 5 about 2.85 m nearer to the camera to leave a clear gap.
32. **rule 4: overlap clearly or leave a clear gap.** two gates and the wall between and man 2 almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.24 across, 0.63 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.60 m to the right so it clearly overlaps two gates and the wall between, or move man 2 about 0.08 m to the left to leave a clear gap.
33. **rule 4: overlap clearly or leave a clear gap.** man 2 and no-1 drums almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.25 across, 0.64 down; man 2 is nearer the camera)
   - Fix: Move man 2 about 0.56 m to the right and about 1.34 m nearer to the camera so it clearly overlaps no-1 drums, or move man 2 about 0.08 m to the left and about 0.19 m further from the camera to leave a clear gap.
34. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 3: it reaches 14 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.65 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.02 m to the right and about 0.32 m further from the camera so it clearly overlaps man 3, or move man 6 about 0.16 m to the left and about 2.62 m nearer to the camera to leave a clear gap.
35. **rule 4: overlap clearly or leave a clear gap.** two gates and the wall between and man 1 almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.63 down; man 1 is nearer the camera)
   - Fix: Move man 1 about 0.63 m to the left so it clearly overlaps two gates and the wall between, or move man 1 about 0.07 m to the right to leave a clear gap.
36. **rule 4: overlap clearly or leave a clear gap.** man 6 only just overlaps man 4: it reaches 15 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.34 across, 0.65 down; man 6 is nearer the camera)
   - Fix: Move man 6 about 0.25 m further from the camera so it clearly overlaps man 4, or move man 6 about 0.16 m to the left and about 2.62 m nearer to the camera to leave a clear gap.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 0.91 m above the pavement under it (a standing person: 0.80 to 7.00 m).
- props rest where they should: brazier, no-1 drums, no-2 drums, no-2 crates, handcart, man 1, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of two gates and the wall between is 0.002 of the frame width away (limit 0.03).
- rule 3: nothing hides the words: 0% of gate boards's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 1% of bank sign's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (gate boards 0.72, brazier 0.26, no-2 crates 0.74, man 1 0.37, man 2 0.23, man 3 0.35, man 4 0.35, man 5 0.35, man 6 0.35, man 7 0.34, bank sign 0.21).
- rule 12: titles in dim sky: The title area (0.06 to 0.90 across, 0.05 to 0.22 down) is dim, empty sky.
- rule 8: nothing big where the eye enters: No prop fills more than 1% of the frame in the bottom-left quarter.
- rule 8: nothing big and dark where the eye enters: The biggest dark shape where the eye enters (the bottom-left quarter) covers 0.8% of the frame (limit 1%): brightness 0.11 against 0.21 for the lit ground around it. It is not a prop: probably a shadow cast across the ground.
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.31, 0.29, 0.28 (limit 0.36).
- rule 6: warm light from the people's own lights: Warm light covers 1.9% of the frame, 77% of it round the story props.
- rule 6: lit from below: The bottom of two gates and the wall between is 0.20 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.60 across, 0.53 down; centre of the warm light 0.59 across, 0.54 down; centre of the story props 0.47 across, 0.60 down; centre of two gates and the wall between 0.49 across, 0.59 down. Together they span 0.13 of the frame wide and 0.10 tall (limit 0.40 x 0.50, holding two gates and the wall between).

## Notes

- rule 4: overlap clearly or leave a clear gap: no-2 drums overlaps no-2 crates by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 4 by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 5 by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps man 6 by 17 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 7 overlaps no-1 drums by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.62 across, 0.69 down (0.4% of the frame; lit most by gas_lamp_1_light); at 0.65 across, 0.60 down (0.3% of the frame; lit most by gas_lamp_1_light); at 0.54 across, 0.49 down (0.2% of the frame). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
