57. **A camera that never stops reads as restless on a phone.** Most pages crept or drifted for their
    whole length (page 1: one slow push for 20 seconds; pages 3 and 8 never held still). The camera
    rule is now built into the engine: `kit.stillShot` holds still and allows only named moves from
    the viewer's grammar, at most three per shot, and refuses a fourth. A checker measures every shot
    of the film in seconds (`--camera` then `camera_audit.py`).
58. **Measure camera moves against the thing in focus, not the aim point.** In a painted room the
    camera aims at a point 30 units away, so a real one-unit move looked tiny to the first checker.
    Using the focus distance fixed it.
59. **Plain card boxes look poor beside detailed paintings.** The old factory was about 2,000
    triangles with printed brick; the new one, built in Blender by script, is about 22,000 with real
    window openings, sills, copings, gutters, a sawtooth roof with lit glass and a chimney with bands.
    It is still light enough for the software renderer.
60. **Blender's MCP servers are a way to send it Python.** Where an agent can run code, `pip install
    bpy` gives the same Blender, headless. Blender's renderer is far too slow to film with here
    (35 to 90 seconds a frame), so it builds models and the stage films them.
61. **Baking corner shading: keep it local and small.** Blender's default reach (10 units) darkened
    whole walls, and 2048 pixels at 48 samples took 12 minutes on a busy machine. A reach of 0.6,
    1024 pixels and 32 samples took 2 minutes and looks right. A part left out of the bake must not
    share a material with a baked part, or it turns dark brown (the kerb did).
62. **Blender adds ".glb" to any file name that doesn't end in it** ("factory-a.glb.new" became
    "factory-a.glb.new.glb", and the rename after it failed).
63. **Frame with numbers before rendering.** `frame_check.py` says where each thing lands in the tall
    frame for a camera position, in a second. It found price boards off the edge and cut-outs too
    wide for the frame before any still was made.
64. **A tall frame needs things stacked in depth, not side by side.** Three cut-outs in a row were 2.4
    units wide and fell off both edges; staggered front to back, they fit large. Soft barrels, crates
    and a cart in the near corners fill the bottom third.
65. **Corner checks miss a flat card's middle.** The clearance check now samples points across every
    face, and the overlap check ignores hidden parts (both found by the reviewer).
66. **Words over a busy set need a soft dark band** (chimneys, papers on a desk), as the street
    already had.
