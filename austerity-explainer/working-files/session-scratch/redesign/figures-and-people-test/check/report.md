# Shot check: check

21 problems found in 28 checks, numbered worst first (the camera first, because it moves everything on screen).

How to read this: places are fractions of the frame (0 across is the left edge, 1 the right; 0 down is the top, 1 the bottom). Pixels are this frame's (1080 wide). Metres are metres in the street; "Blender x, y" is a spot on the street's map (x across the street, y up it). On marked.jpg each problem's place is boxed, with its number on a dark tag (red: a small place; orange: a large area). Dashed lines: the 0.90 and 0.95 limits of rule 12. Cyan arrows: from where a prop is to where the reference has it. Circles (main rule): purple, where the lines meet; white, the centre of the brightest parts; pink, the centre of the warm light; blue, the centre of the story props; green, the centre of the subject. A camera problem has no box: it changes the whole frame.

Words used: "where the lines meet" is the spot where the street's straight edges (kerbs, gutters, roof lines) run together in the distance. The subject is the thing the shot is about; story props are the props that tell the story; work props are the rest (the check file names them). Weight (rule 10) is how strongly a part of the picture pulls the eye, from its size, brightness and detail. The reference is the picture the shot is meant to match. The flat-colour picture shows each prop in one plain colour, as measured in Blender.

Made by check_shot.py version a8d2fe4a; a report made by another version may give other numbers.

## Fix first

Problem 1 (props rest where they should). Move man stooped off brazier and place it again from just above the pavement.

## Problems

1. **props rest where they should.** man stooped rests on brazier, not on the ground (at Blender x 2.85, y 22.04).
   - Fix: Move man stooped off brazier and place it again from just above the pavement.
2. **rule 3: one touching group.** Standing apart from the others: man arms folded, man leaning, man facing.
   - Fix: Move man arms folded about 0.32 m to the right so it overlaps brazier; move man leaning about 0.49 m to the left and about 2.17 m nearer to the camera so it overlaps man stooped; move man facing about 0.38 m to the right so it overlaps man arms folded.
3. **rule 6: lit from below.** The bottom of brazier is -0.54 warmer than its top, on a scale where 0 is the same colour and 1 is pure red against pure blue; it needs 0.10 (the reference measures about 0.17).
   - Fix: Give brazier's bottom more warm light than its top: add a warm light below it, aimed at its bottom edge; or dim or whiten the light from above (brazier_light, fire_glow_on_road, dusk_skylight). Then check again.
4. **rule 8: nothing big and dark where the eye enters.** The biggest dark shape where the eye enters (the bottom-left quarter) covers 8.5% of the frame (limit 1%): brightness 0.06 against 0.15 for the lit ground around it. It is not a prop: probably a shadow cast across the ground. (from 0.00 to 0.50 across, 0.71 to 1.00 down)
   - Fix: First give the tool the log Blender wrote while rendering the picture (--render-log, or RENDER_LOG=... with check-shot.sh): a render that ran out of shadow memory draws false hard shadows. If the log is clean, find what casts it: switch off each light's shadow one at a time (the warm lights first), see which one makes it vanish, and move that light or the thing in its way.
5. **rule 3: story props close together.** The story props fill a box 0.70 of the frame wide and 0.25 tall (limit 0.40 x 0.50). Its edges: man facing's left side (0.11 across), man leaning's right side (0.81), man hand on bar's top (0.44 down) and man arms folded's bottom (0.70).
   - Fix: Move man facing about 1.34 m to the right.
6. **rule 5: nothing in the story group as bright as brazier.** the brightest parts of man hand on bar reach 0.36, as bright as brazier (0.11); the brightest parts of man leaning reach 0.11, as bright as brazier (0.11).
   - Fix: Make man hand on bar darker (its own colour) or move it further from the light on it (brazier_light). Make man leaning darker (its own colour) or move it further from the light on it (brazier_light).
7. **rule 1: aim the street at the story.** The street's lines meet at 0.634 across, 0.440 down; the nearest edge of brazier is 0.209 of the frame width away (limit 0.03): 104 pixels to the left and 200 pixels below. (brazier spans 0.44 to 0.54 across, 0.54 to 0.66 down)
   - Fix: Turning the camera won't help: it moves where the lines meet and the props together. Lower the camera about 0.90 m (brazier then rises on screen while where the lines meet stays put); and move the camera about 0.47 m to the left, or move brazier about 0.47 m to the right.
8. **rule 5: brazier is the biggest bright thing.** Of the brightest parts (the brightest 3% of the frame), 0% lie on brazier (need 40%) and 36% in the story props' box (need 75%). The largest bright patch belongs to the set (no named prop).
   - Fix: Dim the set (no named prop) (the marked bright patch), or light brazier more.
9. **rule 5: brazier is bright.** brazier is 0.86 times as bright as the frame's average (need 1.8).
   - Fix: Light brazier more, or darken what is around it.
10. **rule 6: warm light from the people's own lights.** Warm light covers only 0.3% of the frame (aim for 1.5 to 3%); only 32% of it lies round the story props (need most of it). (warm: red clearly stronger than blue in a lit part (the same measure as measure_composition.py))
   - Fix: Let the fire and the lantern light more. 68% of the warm light is away from the story props; the largest patch is on lamp post at 0.59 across, 0.29 down (marked). The warm lights lighting it most: none found. Shorten how far their light reaches (Blender's "custom distance" for a light) rather than their strength, so the notice keeps its warm light from below.
11. **rule 4: overlap clearly or leave a clear gap.** man stooped and walker 3 almost touch: 7 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.52 across, 0.47 down; man stooped is nearer the camera)
   - Fix: Move man stooped about 0.07 m to the left and about 2.32 m further from the camera (but lamp post stands there) so it clearly overlaps walker 3, or move man stooped about 0.04 m to the right and about 0.85 m nearer to the camera to leave a clear gap.
12. **rule 10: nothing on the quiet side outshines the subject.** A light in the right half (at 0.59 across, 0.30 down) is 0.63 bright, as bright as brazier (0.12).
   - Fix: Dim that light (or move it further away), and move or shrink big props on that side.
13. **rule 10: the quiet side keeps the frame from tipping.** The right half (away from brazier) holds 54% of the weight (aim for 40 to 48%).
   - Fix: The right half is too busy: dim or remove some of its detail.
14. **rule 4: overlap clearly or leave a clear gap.** man hand on bar and walker 4 almost touch: 11 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.61 across, 0.47 down; man hand on bar is nearer the camera)
   - Fix: Move man hand on bar about 0.11 m to the right and about 4.03 m further from the camera so it clearly overlaps walker 4, or move man hand on bar about 0.04 m to the left and about 0.83 m nearer to the camera to leave a clear gap.
15. **rule 8: nothing big where the eye enters.** man facing fills 1.7% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man facing out of the bottom-left quarter.
16. **rule 8: nothing big where the eye enters.** man arms folded fills 1.6% of the frame in the bottom-left quarter, where the eye enters (limit 1%).
   - Fix: Move man arms folded out of the bottom-left quarter.
17. **rule 3: story props together in the street.** man hand on bar stands 0.38 m from the nearest other story prop (man leaning) in the street: the group should stand together.
   - Fix: Move man hand on bar about 0.25 m right (across the street) and 0.11 m down the street, toward man leaning.
18. **rule 3: story props together in the street.** man leaning stands 0.38 m from the nearest other story prop (man hand on bar) in the street: the group should stand together.
   - Fix: Move man leaning about 0.25 m left (across the street) and 0.11 m up the street, toward man hand on bar.
19. **rule 4: overlap clearly or leave a clear gap.** walker 1 only just overlaps walker 5: it reaches 9 pixels into it. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.44 across, 0.45 down; walker 1 is nearer the camera)
   - Fix: Move walker 1 about 0.22 m higher so it clearly overlaps walker 5, or move walker 1 about 0.73 m lower to leave a clear gap.
20. **rule 4: overlap clearly or leave a clear gap.** lamp post and walker 4 almost touch: 14 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.61 across, 0.45 down; lamp post is nearer the camera)
   - Fix: Move lamp post about 0.18 m to the right so it clearly overlaps walker 4, or move lamp post about 0.04 m to the left to leave a clear gap.
21. **rule 4: overlap clearly or leave a clear gap.** walker 4 and walker 6 almost touch: 16 pixels apart. Edges that just meet make near and far things look stuck together (a clear overlap is at least 15 pixels deep; a clear gap at least 18). (at 0.64 across, 0.47 down; walker 4 is nearer the camera)
   - Fix: Move walker 4 about 1.02 m to the right so it clearly overlaps walker 6, or move walker 4 about 0.15 m to the left to leave a clear gap.

## Passed

- rule 2: keep the camera level: The camera is level (tilt 0.0, lean 0.0 degrees).
- rule 2: stand at eye height: The camera's eye is 1.80 m above the pavement under it (a standing person: 1.50 to 1.90 m).
- props rest where they should: brazier, man arms folded, man hand on bar, man leaning, man facing, lamp post stand on the pavement or road (within 3 cm).
- rule 12: room for phone buttons: Everything to read is left of 0.90 across, and the story props left of 0.95 where the buttons are (brazier 0.56, man stooped 0.63, man arms folded 0.40, man hand on bar 0.61, man leaning 0.81, man facing 0.24).
- rule 5: keep the sky dim: The top third's brightness, left to right: 0.21, 0.23, 0.10 (limit 0.36).
- rule 5: no burnt-out colour: Nothing apart from tiny highlights is at its colour limit.
- main rule: every strong thing points at the same place: where the lines meet 0.63 across, 0.44 down; centre of the brightest parts 0.51 across, 0.39 down; centre of the warm light 0.49 across, 0.39 down; centre of the story props 0.43 across, 0.57 down; centre of brazier 0.49 across, 0.60 down. Together they span 0.20 of the frame wide and 0.21 tall (limit 0.40 x 0.50, holding brazier).

## Notes

- rule 4: overlap clearly or leave a clear gap: man hand on bar and walker 3 are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 4: overlap clearly or leave a clear gap: walker 2 and walker 5 are 20 pixels apart: they pass, but only just (the limit is 18); a small move of the camera could make them nearly touch.
- rule 12: titles in dim sky: Not checked: the check file has no "title_zone".
- rule 6: warm light from the people's own lights: Warm patches on the set (walls, road): at 0.73 across, 0.65 down (0.3% of the frame; lit most by brazier_light). Check each is lit by something you meant (a window, a lamp, the fire's glow on the road), not by a light meant for the notice that shines through or past it.

## Not checked by this tool

- rule 7 (story props stacked in upright columns, something in the top third): judge by eye.
- rule 9 beyond the lantern resting on the chair: that the chair stands right under the notice, its seat shows and the lantern is lit.
- rule 11 (the camera slides without turning): check where the lines meet in the first, middle and last frames of the film.
- whether a prop pokes into a wall or another prop in 3D: only what shows on screen is measured.
