# Examples

What this folder is: worked examples of the store's ground and street tools, each a script that builds a whole small place and
draws it, with the picture it draws beside it. Read a script to see the order the tools are used in; run it to draw it.

| Script | Picture | What it builds |
|---|---|---|
| `ground - a cart track after rain.py` | `ground - a cart track after rain.jpg` | A horse and cart's lane at dusk: iron-tyred ruts holding water, potholes at a gateway, hoof prints, an older car's softened ruts, a footpath, footprints to a hut, grassy verges, stones, leaves and twigs; parts stood on the uneven ground. 540 x 960. |
| `ground - deep ruts in a wet field.py` | `ground - deep ruts in a wet field - grey day.jpg`, `... - evening.jpg` | A heavy tyre's deep ruts in a soaked field, the floors ridged by the tread and holding water, grass between and beside them, weeds, leaves and twigs, rain on the water. 960 x 720; add `day` for a grey day under a photographed rain sky. |
| `street - a curved corner after rain.py` | `street - a curved corner after rain.jpg` | A wet street corner at dusk (decisions 80 and 81): a sett road that climbs and bends, kerbs and flagged pavements following both edges, a wall of flat planes along the bend filled by `lay_wall` (old red brick, dark brick in Flemish bond, stone blocks), a house front by `lay_stone` in photographed sandstone with timber door and window frames and two lit windows, a gas lamp and its puddle, an ash bin, a newspaper, joint weeds. 540 x 960. |

Run one from anywhere:

    python3 "ground - a cart track after rain.py" [WIDTH HEIGHT SAMPLES OUT.png]
    python3 "ground - deep ruts in a wet field.py" [WIDTH HEIGHT SAMPLES OUT.png [day]]
    python3 "street - a curved corner after rain.py" [WIDTH HEIGHT SAMPLES OUT.png]

The order every ground follows: `ground.make` and `ground.wet`; the tracks; `ground.detail` where the camera is near;
grass, stones and litter; then `ground.fill(yard, ground.spots(yard))` for the water. Parts go on the ground with
`ground.height_at`. A street follows one line: `lay_cobbles.lay_setts_along`, then `road_edges` for the kerbs, the pavements and the walls' line, then the walls, the buildings, the puddles (`top_at` for their level) and the weeds.

## Traps

- Each script writes its picture into the folder you run it from unless you give OUT; never run it from inside the brief
  folder, or the picture goes to every builder with the kit.
- Full size takes about ten minutes on two processors; try 270 480 16 (or 480 360 16) first.
