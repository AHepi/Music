# OUTLINE AND SHADOW - the controls (generated from layers/outline_and_shadow.py; every control is also a setting named `outline_and_shadow.<name>`)

Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.0064 = 8 dots). The "in dots" column shows the same size at 1254 dots per tile.

| setting | socket in Blender | what it does | lowest | highest | default | default in dots (1254 per tile) |
|---|---|---|---|---|---|---|
| `outline_and_shadow.seed` | Seed | the layer's own random seed: change it and ONLY this layer's pattern changes | 0.0 | 1000.0 | 41.0 |  |
| `outline_and_shadow.amount` | Amount | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) | 0.0 | 1.0 | 1.0 |  |
| `outline_and_shadow.joint_width` | Joint Width | how far the painted black spills out of the gap BETWEEN SLATES OF A ROW into each slate, in tile units (0.0008 = 1 dot); the gap itself is the layout's Joint Width | 0.0 | 0.006 | 0.0008 | 1.0 |
| `outline_and_shadow.band_width` | Band Width | how far the painted black spills out of the band BETWEEN ROWS into the slates above and below, in tile units (0.0004 = 0.5 dot); the band itself is the layout's Row Gap | 0.0 | 0.008 | 0.0004 | 0.5 |
| `outline_and_shadow.joint_colour` | Joint Colour | the near-black of the joints |  |  | #0e0f11 |  |
| `outline_and_shadow.side_outline_width` | Side Outline Width | width of the thin dark line just inside every slate edge, in tile units (0.0020 = 2.5 dots) | 0.0 | 0.008 | 0.002 | 2.5 |
| `outline_and_shadow.side_outline_darkness` | Side Outline Darkness | how strongly the outline colour covers the slate paint (0 = invisible, 1 = solid) | 0.0 | 1.0 | 0.6 |  |
| `outline_and_shadow.outline_colour` | Outline Colour | the dark blue-black of the thin outline (a little lighter than the joint black) |  |  | #14161a |  |
| `outline_and_shadow.shadow_width` | Shadow Width | how far the shadow of the slate above reaches down the slate below, in tile units (0.030 = 38 dots; the reference band is about 21 dots of dark plus a soft tail to 40 dots) | 0.0 | 0.06 | 0.03 | 37.6 |
| `outline_and_shadow.shadow_darkness` | Shadow Darkness | how strongly the shadow colour covers the slate paint right under the joint (0 = no shadow, 1 = solid black); it is weaker lower down | 0.0 | 1.0 | 0.7 |  |
| `outline_and_shadow.shadow_tiers` | Shadow Tiers | how many flat painted steps the shadow is cut into (0 = a smooth blur; 4 = four flat tones; 1 = one flat band) | 0.0 | 8.0 | 4.0 |  |
| `outline_and_shadow.shadow_drip` | Shadow Drip | how ragged the lower border of the shadow is, as a share of Shadow Width (0 = a straight line; 0.5 = teeth pointing down like drips; 1 = very ragged) | 0.0 | 1.0 | 0.5 |  |
| `outline_and_shadow.black_drips` | Black Drips | how far black drips hang down from the black band into the shadow, in tile units (0.009 = 11 dots at most; they are teeth of different length, most places have none; 0 = no drips) | 0.0 | 0.03 | 0.009 | 11.3 |
| `outline_and_shadow.shadow_colour` | Shadow Colour | the colour of the shadow: very dark blue-grey that is laid over the slate paint |  |  | #0f1114 |  |
| `outline_and_shadow.lip_offset` | Lip Offset | how far inside the slate edge the pale lip starts, in tile units (0.0026 = 3.3 dots: between the black joint and the lip is a thin dark rim, as in the reference) | 0.0 | 0.02 | 0.0026 | 3.3 |
| `outline_and_shadow.lip_width` | Lip Width | width of the pale lip along the lower edge of a slate, in tile units (0.0030 = 3.8 dots), measured from the slate edge, after Lip Offset | 0.0 | 0.02 | 0.003 | 3.8 |
| `outline_and_shadow.lip_brightness` | Lip Brightness | how strongly the pale colour covers the slate paint on the lip (0 = no lip, 1 = solid pale) | 0.0 | 1.0 | 0.25 |  |
| `outline_and_shadow.lip_breakup` | Lip Breakup | how broken the lip is (0 = one unbroken line, 1 = only short pale pieces) | 0.0 | 1.0 | 0.4 |  |
| `outline_and_shadow.lip_colour` | Lip Colour | the pale grey of the lip (the reference lip and chips measure about #6d6c67 to #7a7975 on top of the paint) |  |  | #8c8e8b |  |
| `outline_and_shadow.edge_darkening` | Edge Darkening | how strongly the slate is darkened right next to its edges (0 = not at all) | 0.0 | 1.0 | 0.3 |  |
| `outline_and_shadow.edge_darkening_width` | Edge Darkening Width | how far from an edge the darkening reaches, in tile units (0.0045 = 5.6 dots) | 0.0 | 0.03 | 0.0045 | 5.6 |
| `outline_and_shadow.wobble` | Wobble | how hand-drawn the lines are: every outline and joint edge gets wider and narrower by this share (0 = ruler-straight lines, 0.5 = plus or minus half) | 0.0 | 1.0 | 0.5 |  |
| `outline_and_shadow.wobble_scale` | Wobble Scale | how many wobbles fit across one base tile: 90 = a wobble about 14 dots long; more = finer | 10.0 | 400.0 | 90.0 |  |
| `outline_and_shadow.slate_variation` | Slate Variation | how different the slates are from each other in shadow depth, shadow reach and lip (0 = every slate drawn the same) | 0.0 | 1.0 | 0.5 |  |
| `outline_and_shadow.shadow_height` | Shadow Height | how far the slate surface is pushed down at the top edge under the joint (a slope that rises over the Shadow Width); height scale 0..1 | 0.0 | 0.5 | 0.12 |  |
| `outline_and_shadow.lip_height` | Lip Height | how much the lip is raised (height scale 0..1) | 0.0 | 0.3 | 0.04 |  |
| `outline_and_shadow.outline_height` | Outline Height | how deep the thin outline groove is (height scale 0..1) | 0.0 | 0.3 | 0.05 |  |
| `outline_and_shadow.joint_roughness` | Joint Roughness | how much rougher than a bare slate the black joints are (added to roughness) | -1.0 | 1.0 | 0.12 |  |
| `outline_and_shadow.shadow_roughness` | Shadow Roughness | how much rougher the shadow band is (dirt gathers there) | -1.0 | 1.0 | 0.06 |  |
| `outline_and_shadow.lip_roughness` | Lip Roughness | how much smoother the lip is (an edge worn smooth catches the light); minus = smoother | -1.0 | 1.0 | -0.15 |  |
