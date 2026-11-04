# Skies

What this folder is: whole skies photographed all round with no ground in them, free from Poly Haven (CC0; authors in
`manifest.json`), for `sky_and_haze.photo_sky(scene, name)`: the sky is the world's background and its light. `fetch_skies.py`
downloads them again.

| Sky | What it is |
|---|---|
| `mud_road_puresky` | a flat grey overcast sky, soft even daylight |
| `overcast_soil_puresky` | a heavy grey sky of rolling rain clouds, a paler band low down |

## Traps

- A photographed sky lights the whole place by itself; add lamps only for what the sky cannot give (a window's glow, a
  lantern). An extra big fill light makes the ground brighter than the sky, which reads wrong.
- The series' dusk look uses the store's own dusk sky (`sky_and_haze.sky`), not a photograph.
