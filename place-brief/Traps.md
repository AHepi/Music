# Traps

What this file is: the faults every builder working from this brief has run into so far (four builders, four places, 3 November 2026), so the next one loses no time on them. Nothing here says how to build; it says what has gone wrong.

- **A lamp whose glass or casing surrounds its light gives no light.** Every builder's first lamps lit nothing. Put the light outside the glass, or let the glass pass light.
- **Haze that looks right from inside the scene is far too thick in the picture.** First pictures came out as brown or milky fog. Start thin; thin it with height; make it bluer than you think.
- **Puddles turn into black holes or sheets of pale paper.** Causes found: a sky too bright in the reflections; puddle shapes facing down; water as one big flood. A long puddle that mirrors one light reads better than many small ones.
- **Pale ground reads as snow, plaster or hammered tin.** Dusk ground is dark, damp and brown-grey; judge it next to the brightest light it will have.
- **Smoke made of blobs reads as balloons; smoke painted on afterwards is not lit by the lamps.** A soft ribbon facing the camera, with see-through edges, has worked. If you cannot make it read, leave it out.
- **Colour gradients with stops outside 0 to 1 silently go flat** in Blender's colour ramps; rescale the input first.
- **A volume's density measured from the world's centre comes out empty** when the box stands elsewhere; measure from the object's own coordinates.
- **The tall 9:16 frame is narrow near the camera:** about 3 m wide at 9 m with a 32 mm lens. A building placed near the camera fills a third of the picture; things 10 m to the side are out of frame. Check the frame before dressing.
- **Light makes visible shafts only where it comes through a small gap** (a few clear panes, a door ajar). A whole wall of lit glass makes a glow, not shafts.
- **Lit glass is counted by its area, not by how many windows glow.** Big panes lit all over draw far too bright whatever the exposure; light one or two and leave the rest dim or dark.
- **A dark hero against a dark background disappears** (a black urn, a gun barrel). Give it a light of its own or a lighter ground behind it.
- **Words, people and hands break the look.** House numbers, signs with letters, figures: none.
- **The period is fixed by the look page unless the request says otherwise:** "a suburban townhouse" came out as a Victorian terrace. If another era is wanted, it must be in the request.
- **The clock, not a fixed number of rounds, decides when to stop.** Measure every picture, look at every picture at full size, and keep fixing while time allows; a builder who stopped after one fix pass with an hour left handed in a picture it knew was broken.
- **With the `bpy` module, `import bpy` must come before `import bmesh`.**
