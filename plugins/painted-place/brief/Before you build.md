# Before you build

What this file is: what builders of places for films and games do before they build, and what they do while they build, written so a builder here can do the same in its first twenty minutes (from `procedural-textures/49 Research - ...`, 3 November 2026). It says what to look at and write down; it does not say how to model.

## 1. Look at the board, then write the material list

The folder `boards/<the request>/` holds real photographs of the kind of place asked for. Look at them before building anything. Then write, as your first deliverable, `materials.md` in your work folder: every surface and thing that will be in the picture, one line each:

> **what** · **made of** · **how it has aged** · **where the wear sits**
> e.g. hut wall · sawn boards, creosoted · greyed, splitting, paint gone at the bottom · damp line at the foot, rot at the corners, bright wear beside the door where hands and shoulders rub

Use `surfaces/` for the photographed surfaces you will lay on; say which set each line uses, or "made in code".

## 2. Decide who uses this place

Write three lines at the top of `materials.md`: who is here (they are not in the picture), what they do all day, what they left behind when they stepped out of frame. Every prop you place afterwards should be one of those things, in the place that person would have put it down. A prop with no owner is clutter.

## 3. Wear follows a few physical rules

- Convex edges and corners rub bright: paint chips there, metal shows, timber corners round off.
- Hollows, joints and the foot of anything fill with dirt, dust and damp; the darkest grime is where rain cannot reach to wash it.
- Water runs down: streaks start under a sill, a nail, a pipe joint, a bolt, and fade out; rust begins where water sits or is trapped (fittings, drains, seams, rivets) and runs from there.
- Hands and feet polish: thresholds, door edges, rails, the middle of a path.
- The setting decides the rest: in rain, mud climbs up the lower boards; in a desert, dust sits on every upward face and nothing rusts far.
- Restraint: not every edge, not every panel. The guides warn against it as often as they ask for wear.

## 4. Three sizes of shape

Before the last picture, squint at it. The big shapes should be the place (huts, road, tower). Close one eye and look again: medium shapes should give each thing its character (a gun's wheels and shield, a hut's windows and stove pipe, a tent's ropes). Then the small ones: nails, stains, sacks, a cup on a crate, the things people left. If any size is missing, add it; if the small ones are everywhere, take some away.

## 5. Photographed surfaces wherever they can carry the detail

The owner's words to every builder (decision 84): "Please remind the builders to use PBR wherever possible. It save in space and compute." And later (decision 91): "That should be the standard for textures." PBR here means the photographed surface sets: their colour, roughness, normal and height pictures used together, as on the shelf (`surfaces/`) and in the store's `SURFACE`, `BRICK` and `ASHLAR` materials. Let the pictures carry fine relief, grain, cracks and wear; build a shape only where its outline or its shadow must show (a step, a lip, a sett's edge, a beam's end).

## Traps

- The photographs on the board are daylight and grey; take the materials and the use from them, never the light or the colour.
- A surface from the shelf stretched over a surface with no texture layout reads at once; project it from three sides or use the object's own coordinates.
- The material list is written before the build and kept true during it: a surface that changes in the scene changes on the list.
