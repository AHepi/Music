# Shot check: facts

22 problems found in 35 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version 3ad3cd77; a report made by another version may give other numbers.

## Fix first

Problem 1 (rule 5: nothing in the story group as bright as no-1 gate). Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Dim lantern's glass or glow, so only its flame is as bright as no-1 gate. Make diesel drum darker (its own colour) or move it further from the light on it (lantern_light). Make pop-up crates darker (its own colour) or move it further from the light on it (no-1-gateway-beam).

## Problems

1. **rule 5: nothing in the story group as bright as no-1 gate.** the brightest parts of brazier reach 0.26, as bright as no-1 gate (0.11); the brightest parts of lantern reach 0.98, as bright as no-1 gate (0.11): 97% of it, where a lamp's flame alone is about 6%; the brightest parts of diesel drum reach 0.15, as bright as no-1 gate (0.11); the brightest parts of pop-up crates reach 0.55, as bright as no-1 gate (0.11).
   - Fix: Make brazier darker (its own colour) or move it further from the light on it (brazier_light). Dim lantern's glass or glow, so only its flame is as bright as no-1 gate. Make diesel drum darker (its own colour) or move it further from the light on it (lantern_light). Make pop-up crates darker (its own colour) or move it further from the light on it (no-1-gateway-beam).
2. **rule 3: story props close together.** The story props (leaving out no-1 board) fill a box 0.61 of the frame wide and 0.43 tall (limit 0.40 x 0.50). Its edges: lantern's left side (0.19 across), brazier's right side (0.79), no-1 gate's top (0.41 down) and diesel drum's bottom (0.84).
   - Fix: Move lantern about 0.81 m to the right.
3. **rule 1: aim the street at the story.** The street's lines meet at 0.500 across, 0.500 down; the nearest edge of no-1 gate is 0.157 of the frame width away (limit 0.03): 170 pixels to the left and 0 pixels above. (no-1 gate spans 0.29 to 0.78 across, 0.41 to 0.65 down)
   - Fix: Turning the camera won't help: it moves where the lines meet and the props together. Move the camera about 1.02 m to the left, or move no-1 gate about 1.02 m to the right.
4. **rule 5: no-1 gate is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on no-1 gate (need 40%) and 52% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light no-1 gate more.
5. **rule 5: no-1 gate is bright.** no-1 gate is 0.72 times as bright as the frame's average (need 1.8).
   - Fix: Light no-1 gate more, or darken what is around it.
6. **rule 6: lit from below.** The bottom of no-1 gate is -0.06 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give no-1 gate's bottom more warm light than its top: dim or whiten the light from above (dusk_skylight, no-1-gate-lamp-light); or bring the warm light below it closer under its bottom edge, or aim it there (brazier_light). Then check again.
7. **rule 3: one touching group.** Standing apart from the others: lantern.
   - Fix: Move lantern about 0.27 m to the right and about 0.27 m lower so it overlaps diesel drum.
8. **rule 8: nothing big where the eye enters.** diesel drum fills 3.7% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move diesel drum out of the bottom-left quarter.
9. **rule 3: story props together in the street.** diesel drum stands 0.95 m from the nearest other story prop (lantern) in the street: the group should stand together.
   - Fix: Move diesel drum about 0.43 m left (across the street) and 0.73 m up the street, toward lantern.
10. **rule 6: warm light from the people's own lights.** Warm light covers 5.0% of the frame, 1.7 times the most allowed (3%). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Most of it is round the story props: shorten how far the fire's and the lantern's light reaches, or lower the lantern's strength a little (the fire's light also lights the notice from below). 39% of the warm light is away from the story props; the largest patch is on the house walls at 0.41 across, 0.31 down (marked). The warm lights lighting it most: none found. Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
11. **rule 4: overlap clearly or leave a clear gap.** brazier and pop-up crates almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.69 across, 0.66 down; brazier is nearer the camera)
   - Fix: Move brazier about 0.10 m to the left so it clearly overlaps pop-up crates, or move brazier about 0.10 m to the right to leave a clear gap.
12. **rule 4: overlap clearly or leave a clear gap.** lantern and lunch tin almost touch: 1 pixel apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.19 across, 0.61 down; lantern is nearer the camera)
   - Fix: The move in problem 7 (bringing lantern into the group) fixes this too, if it ends in a clear overlap; check again after it.
13. **rule 3: story props together in the street.** brazier stands 0.84 m from the nearest other story prop (pop-up crates) in the street: the group should stand together.
   - Fix: Move brazier about 0.41 m left (across the street) and 0.62 m up the street, toward pop-up crates.
14. **rule 3: story props together in the street.** pop-up crates stands 0.84 m from the nearest other story prop (brazier) in the street: the group should stand together.
   - Fix: Move pop-up crates about 0.41 m right (across the street) and 0.62 m down the street, toward brazier.
15. **rule 4: overlap clearly or leave a clear gap.** diesel drum and petrol drum almost touch: 7 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.26 across, 0.65 down; diesel drum is nearer the camera)
   - Fix: Move diesel drum about 0.07 m to the left so it clearly overlaps petrol drum, or move diesel drum about 0.04 m to the right to leave a clear gap.
16. **rule 4: overlap clearly or leave a clear gap.** gate lamp only just overlaps no-1 gate: it reaches 6 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.33 across, 0.43 down; gate lamp is nearer the camera)
   - Fix: Move gate lamp about 0.02 m to the left and about 0.06 m lower so it clearly overlaps no-1 gate, or move gate lamp about 0.05 m to the right and about 0.13 m higher to leave a clear gap.
17. **rule 8: nothing big where the eye enters.** petrol drum fills 2.0% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move petrol drum out of the bottom-left quarter.
18. **rule 10: nothing on the quiet side outshines the subject.** A light in the left half (at 0.44 across, 0.31 down) is 0.73 bright, as bright as no-1 gate (0.14); petrol drum cover more than 2% of the frame there.
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
19. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 1.8% of the frame (limit 1%): brightness 0.03 against 0.19 for the lit ground around it. Most of it is petrol drum. (from 0.10 to 0.27 across, 0.61 to 0.75 down)
   - Fix: Move petrol drum out of the bottom-left quarter, or light it.
20. **rule 10: the quiet side keeps the frame from tipping.** The left half (away from no-1 gate) holds 51% of the weight (aim for 40 to 48%).
   - Fix: The left half is too busy: dim or remove some of its detail.
21. **rule 12: titles in dim sky.** Only 27% of the title area is sky (need 85%). (27% of the title area is sky; its brightness 0.20)
   - Fix: Move the title area into darker, emptier sky, or move what is in it.
22. **rule 4: overlap clearly or leave a clear gap.** lunch tin's edge runs right along petrol drum's edge for 88 pixels, without clearly passing behind it. Edges that just meet make near and far things look stuck together. (from 0.61 to 0.62 down, around 0.16 across; petrol drum is nearer the camera)
   - Fix: Move lunch tin about 0.07 m lower so lunch tin clearly passes behind petrol drum, or move lunch tin about 0.08 m higher to leave a clear gap.

## Passed

- set-up: the finished picture rendered cleanly: The render's log shows no shadow-memory faults.
- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.70 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: brazier, petrol drum, diesel drum, pop-up crates stand on the pavement or road (within 3 cm).
- rule 7: the story reaches the frame's lower part: The lowest story thing that shows is diesel drum, reaching 0.84 down the frame (the check file asks for at least 0.78).
- rule 3: nothing hides the words: 0% of no-1 board's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 3% of petrol drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of diesel drum's words are hidden (its bottom fifth, the signature, may be covered).
- rule 3: nothing hides the words: 0% of pop-up crates's words are hidden (its bottom fifth, the signature, may be covered).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.79, lantern 0.22, diesel drum 0.47, pop-up crates 0.69, petrol drum 0.27, no-1 board 0.66).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.18, 0.25, 0.22 (limit 0.36).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- main rule: every strong thing points at the same place: where the lines meet 0.50 across, 0.50 down; centre of the brightest parts 0.53 across, 0.38 down; centre of the warm light 0.52 across, 0.40 down; centre of the story props 0.48 across, 0.66 down; centre of no-1 gate 0.50 across, 0.53 down. Together they span 0.05 of the frame wide and 0.27 tall (limit 0.40 x 0.50, holding no-1 gate).

## Notes

- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.46 across, 0.47 down (1.5% of the frame); at 0.67 across, 0.49 down (0.9% of the frame); at 0.55 across, 0.34 down (0.9% of the frame). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye; only how far down the frame the story reaches is measured, and only when the check file gives "story_reaches_down".
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
