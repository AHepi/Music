# What is here (log 54)

What this folder is: the record of "A barn on a farm" (decision 74), built by two fresh builders from the painted-place plugin alone, then drawn by day (decision 76), and what the build added to the plugin (0.8.0).

| File | What it is |
|---|---|
| `54 Barn - first pass - final.png` | The first builder's picture (540 x 960): a weatherboarded barn at dusk after rain, doors open on lit hay and a cart, cart ruts full of water, a dry-stone wall and gate, a limewashed cow house |
| `54 Barn - second pass - final.png` | The second builder's dressing of it: a heap of mangolds, a willow basket and a fork on the near verge, moss on the wall, a tin patch on the barn |
| `54 Barn - second pass - full size.jpg` | The dressed picture redrawn at 1080 x 1920, 64 samples (31 minutes) |
| `54 Barn - by day - final.png` | The dressed farmyard by day: a photographed sunny sky whose sun rakes from the right, lanterns unlit, daylight let in through the door |
| `54 Barn - by day - first try, black doorway.png` | The first day picture, whose open barn read as a black hole (lesson 224) |
| `54 Barn - first pass, second pass, by day.jpg` | The three side by side |
| `54 barn first pass - builder text.md`, `54 barn second pass - builder text.md` | The words each builder was given, and nothing else |
| `54 barn first pass - builder's report.md`, `54 barn second pass - builder's report.md` | Their reports, word for word |
| `54 barn first pass - materials.md`, `54 barn second pass - materials.md` | Their material lists |
| `54 barn first pass - render_final.py`, `54 barn second pass - render_final.py` | Their scripts (they read the store from the builders' copy of the kit, `/home/claude/build-54-barn/kit`, which exists only on this machine) |
| `54 barn by day - render_day.py` | The session's day copy of the second builder's script (reads the plugin itself, which has the sunny sky) |
| `54 store parts helper - report.md`, `54 store tools helper - report.md` | The two helpers' reports on what went into the store |

The board of photographs made for the builders is in the plugin: `plugins/painted-place/brief/boards/barn on a farm/`.

## Traps

- The scripts here do not run from this folder: they need the builders' kit copy or the plugin at the paths written at their top.
- The day picture is drawn only at 540 x 960; its script draws full size with `python3 "54 barn by day - render_day.py" 1080 1920 64 OUT.png` (about 30 minutes on this machine).
