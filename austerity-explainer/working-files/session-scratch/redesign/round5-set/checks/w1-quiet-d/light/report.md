# Shot check: facts

23 problems found in 38 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 5: nothing in the story group as bright as no-1 gate). Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Dim lantern's glass or glow, so only its flame is as bright as no-1 gate. Make diesel drum darker (its own colour) or move it further from the light on it (lantern_light). Make man 1 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 2 darker (its own colour) or move it further from the light on it (brazier_light). Make man 3 darker (its own colour) or move it further from the light on it (brazier_light). Make man 4 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 5 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 6 darker (its own colour) or move it further from the light on it (brazier_light). Make man 7 darker (its own colour) or move it further from the light on it (brazier_light).

## Problems

1. **rule 5: nothing in the story group as bright as no-1 gate.** the brightest parts of brazier reach 0.24, as bright as no-1 gate (0.11); the brightest parts of lantern reach 0.98, as bright as no-1 gate (0.11): 99% of it, where a lamp's flame alone is about 6%; the brightest parts of diesel drum reach 0.26, as bright as no-1 gate (0.11); the brightest parts of man 1 reach 0.13, as bright as no-1 gate (0.11); the brightest parts of man 2 reach 0.15, as bright as no-1 gate (0.11); the brightest parts of man 3 reach 0.23, as bright as no-1 gate (0.11); the brightest parts of man 4 reach 0.12, as bright as no-1 gate (0.11); the brightest parts of man 5 reach 0.16, as bright as no-1 gate (0.11); the brightest parts of man 6 reach 0.21, as bright as no-1 gate (0.11); the brightest parts of man 7 reach 0.16, as bright as no-1 gate (0.11).
   - Fix: Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Dim lantern's glass or glow, so only its flame is as bright as no-1 gate. Make diesel drum darker (its own colour) or move it further from the light on it (lantern_light). Make man 1 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 2 darker (its own colour) or move it further from the light on it (brazier_light). Make man 3 darker (its own colour) or move it further from the light on it (brazier_light). Make man 4 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 5 darker (its own colour) or move it further from the light on it (no-1-men-rim-yard). Make man 6 darker (its own colour) or move it further from the light on it (brazier_light). Make man 7 darker (its own colour) or move it further from the light on it (brazier_light).
2. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.64 of the frame wide and 0.33 tall (limit 0.40 x 0.50). Its edges: man 4's left side (0.15 across), brazier's right side (0.79), no-1 gate's top (0.40 down) and diesel drum's bottom (0.72).
   - Fix: Move man 4 about 1.34 m to the right.
3. **rule 5: no-1 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 8% lie on no-1 gate (need 40%) and 43% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-1 gate more.
4. **rule 5: no-1 gate is bright.** no-1 gate is 0.87 times as bright as the frame's average (need 1.8).
   - Fix: Light no-1 gate more, or darken what is around it.
5. **rule 6: warm light from the people's own lights.** Warm light covers only 0.2% of the frame (aim for 1.5 to 3%); only 27% of it lies round the story props (need most of it). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Let the fire and the lantern light more. 73% of the warm light is away from the story props; the largest patch is on gate lamp at 0.37 across, 0.35 down (marked). The warm lights lighting it most: none found. Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
6. **rule 5: no burnt-out colour.** Colour at its limit (pure white, or one colour at full strength), where all detail is lost: brazier (4% of it).
   - Fix: Dim the light on it, or darken its own colour or glow, until nothing but a lamp's flame reaches the limit.
7. **rule 4: overlap clearly or leave a clear gap.** man 4 and man 5 almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.27 across, 0.67 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 0.09 m to the left so it clearly overlaps man 4, or move man 5 about 0.09 m to the right to leave a clear gap.
8. **rule 4: overlap clearly or leave a clear gap.** lantern and man 5 almost touch: 3 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.60 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.08 m to the left so it clearly overlaps man 5, or move lantern about 0.07 m to the right to leave a clear gap.
9. **rule 4: overlap clearly or leave a clear gap.** man 4 and lunch tin almost touch: 3 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.16 across, 0.60 down; lunch tin is nearer the camera)
   - Fix: Move lunch tin about 0.09 m to the right so it clearly overlaps man 4, or move lunch tin about 0.08 m to the left to leave a clear gap.
10. **rule 4: overlap clearly or leave a clear gap.** man 3's edge runs right along man 6's edge for 68 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.54 to 0.56 down, around 0.51 across; man 6 is nearer the camera)
   - Fix: Move man 3 about 0.09 m to the left so man 3 clearly passes behind man 6, or move man 3 about 0.11 m to the right to leave a clear gap.
11. **rule 10: nothing on the quiet side outshines the subject.** A light in the left half (at 0.38 across, 0.35 down) is 0.57 bright, as bright as no-1 gate (0.13).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
12. **rule 4: overlap clearly or leave a clear gap.** man 5 and petrol drum almost touch: 10 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.23 across, 0.69 down; petrol drum is nearer the camera)
   - Fix: Move petrol drum about 0.12 m to the right so it clearly overlaps man 5, or move petrol drum about 0.05 m to the left to leave a clear gap.
13. **rule 4: overlap clearly or leave a clear gap.** lantern and man 6 almost touch: 12 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.38 across, 0.57 down; lantern is nearer the camera)
   - Fix: Move lantern about 0.11 m to the right and about 0.05 m higher so it clearly overlaps man 6, or move lantern about 0.03 m to the left and about 0.01 m lower to leave a clear gap.
14. **rule 8: nothing big where the eye enters.** diesel drum fills 1.6% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move diesel drum out of the bottom-left quarter.
15. **rule 8: nothing big where the eye enters.** man 6 fills 1.5% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 6 out of the bottom-left quarter.
16. **rule 8: nothing big where the eye enters.** petrol drum fills 1.4% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move petrol drum out of the bottom-left quarter.
17. **rule 4: overlap clearly or leave a clear gap.** man 5 only just overlaps man 1: it reaches 12 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.35 across, 0.55 down; man 5 is nearer the camera)
   - Fix: Move man 5 about 0.01 m to the right and about 0.43 m further from the camera so it clearly overlaps man 1, or move man 5 about 0.06 m to the left and about 1.76 m nearer to the camera to leave a clear gap.
18. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 1.2% of the frame (limit 1%): brightness 0.04 against 0.18 for the lit ground around it. Most of it is petrol drum. (from 0.10 to 0.23 across, 0.59 to 0.71 down)
   - Fix: Move petrol drum out of the bottom-left quarter, or light it.
19. **rule 4: overlap clearly or leave a clear gap.** brazier and man 7 almost touch: 17 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.68 across, 0.69 down; man 7 is nearer the camera)
   - Fix: Move man 7 about 0.08 m to the right and about 0.69 m further from the camera (but man 3 stands there) so it clearly overlaps brazier, or move man 7 about 0.01 m to the left and about 0.06 m nearer to the camera to leave a clear gap.
20. **rule 4: overlap clearly or leave a clear gap.** man 1's edge runs right along man 6's edge for 29 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.50 to 0.51 down, around 0.43 across; man 6 is nearer the camera)
   - Fix: Move man 1 about 0.09 m to the right so man 1 clearly passes behind man 6, or move man 1 about 0.11 m to the left to leave a clear gap.
21. **rule 8: nothing big where the eye enters.** man 5 fills 1.0% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man 5 out of the bottom-left quarter.
22. **rule 12: titles in dim sky.** Only 27% of the title area is sky (need 85%). (27% of the title area is sky; its brightness 0.19)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.
23. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from no-1 gate) holds 49% of the weight (aim for 40 to 48%).
   - Fix: The left half is too busy: dim or remove some of its detail.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: brazier, petrol drum, diesel drum, man 1, man 2, man 3, man 4, man 5, man 6, man 7 stand on the pavement or road (within 3 cm).
- rule 1: aim the street at the story: The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.001 of the frame width away (limit 0.03).
- rule 3: story props together in the street: brazier, diesel drum, man 1, man 2, man 3, man 4, man 5, man 6, man 7 stand in front of None and within 0.3 m of each other.
- rule 3: one touching group: Every story prop that shows touches or overlaps another.
- rule 7: the story reaches the frame's lower part: The lowest story thing that shows is diesel drum, reaching 0.72 down the frame (the check file asks for at least 0.70).
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 3% of petrol drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 2% of diesel drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.79, lantern 0.38, diesel drum 0.44, man 1 0.45, man 2 0.74, man 3 0.60, man 4 0.25, man 5 0.36, man 6 0.51, man 7 0.67, petrol drum 0.23, no-1 board 0.66).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.16, 0.18, 0.18 (limit 0.36).
- rule 6: lit from below: The bottom of no-1 gate is 0.25 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.60 across, 0.42 down; centre of the warm light 0.43 across, 0.42 down; centre of the story props 0.48 across, 0.59 down; centre of no-1 gate 0.56 across, 0.47 down. Together they span 0.16 of the frame wide and 0.18 tall (limit 0.40 x 0.50, holding no-1 gate).

## Notes

- rule 4: overlap clearly or leave a clear gap: lantern overlaps diesel drum by 19 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 4: overlap clearly or leave a clear gap: man 6 and man 7 are 19 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: lunch tin overlaps petrol drum by 16 pixels: it passes, but only just (the limit is 15); a small move of the camera could make the overlap too shallow.
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.78 across, 0.71 down (0.7% of the frame; lit most by brazier_light); at 0.55 across, 0.71 down (0.2% of the frame; lit most by brazier_light). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
