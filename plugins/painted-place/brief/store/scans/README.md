# Scans

What this folder is: real plants and branches photographed and measured into 3D models, free from Poly Haven (CC0, public
domain; authors in `manifest.json`), each in glTF with its pictures at 1K. The grass tool grows its turf, tussocks and herbs
from the grass, nettle and dandelion scans, and the litter tool lays its twigs from the branch scan, when they are here; without
them both fall back to plants and twigs made in code. `fetch_scans.py` downloads them again.

| Scan | What it is | Used by |
|---|---|---|
| `grass_medium_01/` | clumps of meadow grass, 17 shapes | grass: turf and tussocks |
| `grass_medium_02/` | clumps of longer meadow grass, 5 shapes | grass: turf and tussocks |
| `nettle_plant/` | stinging nettles, 6 plants | grass: herbs |
| `dandelion_01/` | dandelions, 5 plants | grass: herbs |
| `dry_branches_medium_01/` | dry fallen branches, 3 shapes | litter: twigs |

## Traps

- A scanned clump has thousands of points; the tools copy it (one shape, many copies), so a field costs memory only once,
  but a whole large ground of dense turf still makes a drawing slower. Give big grounds an area.
- Keep the folder whole: the models find their pictures in their own `textures/` folders.
