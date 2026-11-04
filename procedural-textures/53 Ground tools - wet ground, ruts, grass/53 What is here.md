# What is here

What this folder is: the pictures from plan 53, the ground tools (log 53 in the project story, 4 November 2026). Each was
drawn by a worked example in the plugin's store (`plugins/painted-place/brief/store/examples/`), which anyone can run again.

| Picture | What it shows |
|---|---|
| `53 Deep ruts in a wet field - grey day - final.png` | Your picture's kind of track (decision 71): a heavy tyre's deep ruts in a soaked field, water in them with leaves, grass between and beside them, weeds, twigs; Poly Haven's scanned grass, photographed churned mud with real lumps near the eye, its normal pictures, and a photographed rain sky. 960 x 720, finished. |
| `53 Deep ruts in a wet field - evening - final.png` | The same field in the series' dusk look. |
| `53 Cart track after rain - final.png` | A horse and cart's lane at dusk (decision 72): narrow iron-tyred ruts with water, potholes at the gate, hoof prints between the ruts, an older car's softened ruts, a footpath, footprints to a hut, grassy verges. 540 x 960, finished. |
| `53 Ground at four wetnesses.png` | The ground tool alone: dry, damp, after rain, just rained (water finds the low places first). |
| `53 Cart track - first try, smooth like sand.png` | The first full drawing, before the grass, the clods and the photographs: the fault the later work fixed. |
| `53 First heavy ruts, before the photographs - small.png` | The heavy ruts with home-made grass and lumps, before Poly Haven's scans. |

How they were made: `python3 "ground - deep ruts in a wet field.py" 960 720 64 OUT.png day` (or without `day` for the
evening) and `python3 "ground - a cart track after rain.py" 540 960 64 OUT.png`, from the store's examples folder.

## Traps

- The pictures depend on the store's photographs and scans being in place (`brief/surfaces/`, `brief/store/scans/`,
  `brief/store/skies/`); a copy of the store without them draws home-made grass and a plain sky instead.
- Full size takes about ten minutes a picture on this machine's two processors; the examples' small sizes are for trying.
